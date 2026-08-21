"""Toplu uretim.

Snapshot uretimi ile metin uretimi ayrilmistir:
  - snapshot: gunluk 1, haftalik 7, aylik ~30 gunluk calculate_chart
  - metin   : 12 gunluk + 108 haftalik + 108 aylik

Kilit yalnizca uretim turu basina alinir ve AI cagrisi boyunca
veritabani kilitli tutulmaz (SQLite baglantisi her islemde acilip kapanir).
"""

import time
from datetime import date, timedelta

from . import rules, store, writer
from .keys import (
    DASHA_LORDS,
    DASHA_SOURCE,
    LAYER_DASHA_LEVEL,
    build_key,
    month_start,
    rotation_seed,
    today_ist,
    week_start,
)
from .situation import build_situation, planet_signs, required_days

SNAPSHOT_RETENTION_DAYS = 60
ERROR_RETENTION_DAYS = 90


# ------------------------------------------------------------ snapshot

def ensure_snapshots(gunler):
    """Eksik gunlerin snapshot'ini uretir. Uretilen gun sayisini doner."""
    uretilen = 0
    for g in gunler:
        iso = g.isoformat()
        if store.get_snapshot(iso) is not None:
            continue
        try:
            snap = planet_signs(g)
        except Exception as exc:
            store.log_error(iso, "snapshot", "calculate_chart", exc=exc,
                            fallback_nedeni="snapshot_uretilemedi")
            raise
        store.put_snapshot(iso, snap)
        uretilen += 1
    return uretilen


def load_snapshots(layer, d):
    """Katmanin ihtiyac duydugu snapshot'lar tamsa liste, degilse None."""
    return store.get_snapshots(required_days(layer, d))


# ------------------------------------------------------------ metin

def produce(layer, snaps, natal_idx, lord, d, allow_llm=True):
    """Tek kayit uretir. Kayit zaten varsa dokunmaz.

    Doner: "llm" | "rule" | "mevcut"
    """
    key = build_key(layer, d, natal_idx, lord)
    if store.get(key) is not None:
        return "mevcut"

    level = LAYER_DASHA_LEVEL.get(layer)
    situation = build_situation(layer, snaps, natal_idx, lord, level)

    out = None
    kaynak = "rule"
    sure = None

    if allow_llm:
        out, hata = writer.generate(situation)
        if hata is not None:
            store.log_error(key, layer, hata["asama"], exc=hata.get("exc"),
                            fallback_nedeni=hata["fallback_nedeni"],
                            sure_ms=hata.get("sure_ms"))
        if out is not None:
            kaynak = "llm"
            sure = out.pop("sure_ms", None)

    if out is None:
        t0 = time.time()
        out = rules.generate(situation, rotation_seed(layer, d))
        sure = int((time.time() - t0) * 1000)

    yazildi = store.put(
        key, layer, out["cumle"], out["odak"], kaynak,
        dasha_lord=lord, dasha_level=level,
        dasha_source=DASHA_SOURCE if lord else None,
        uretim_ms=sure,
    )
    return kaynak if yazildi else "mevcut"


# ------------------------------------------------------------ orkestrasyon

def _layers_for(d, force):
    layers = ["daily"]
    if force or d == week_start(d):
        layers.append("weekly")
    if force or d == month_start(d):
        layers.append("monthly")
    return layers


def run(d=None, layers=None, force=False, allow_llm=None):
    """Toplu uretim. Kilit alinamazsa calismadan doner."""
    store.verify_path()
    store.init()

    d = d or today_ist()
    layers = layers if layers is not None else _layers_for(d, force)
    if allow_llm is None:
        allow_llm = writer.llm_enabled()

    kilit_adi = "rebuild:%s" % d.isoformat()
    sahip = store.acquire_lock(kilit_adi)
    if sahip is None:
        return {"tarih": d.isoformat(), "durum": "kilitli",
                "not": "ayni gun icin baska bir uretim suruyor"}

    rapor = {
        "tarih": d.isoformat(),
        "durum": "tamam",
        "generator": store.active_generator(),
        "llm": bool(allow_llm),
        "snapshot_uretilen": 0,
        "katmanlar": {},
        "hata": [],
    }

    try:
        # 1) Gerekli butun snapshot gunlerini topla
        gerekli = []
        for layer in layers:
            for g in required_days(layer, d):
                if g not in gerekli:
                    gerekli.append(g)
        rapor["snapshot_gun_sayisi"] = len(gerekli)
        rapor["snapshot_uretilen"] = ensure_snapshots(sorted(gerekli))

        # 2) Metinleri uret
        for layer in layers:
            snaps = load_snapshots(layer, d)
            if snaps is None:
                rapor["hata"].append("%s: snapshot eksik" % layer)
                continue
            sayac = {"llm": 0, "rule": 0, "mevcut": 0}
            lords = [None] if layer == "daily" else DASHA_LORDS
            for natal_idx in range(12):
                for lord in lords:
                    try:
                        kaynak = produce(layer, snaps, natal_idx, lord, d,
                                         allow_llm=allow_llm)
                        sayac[kaynak] += 1
                    except Exception as exc:
                        key = build_key(layer, d, natal_idx, lord)
                        store.log_error(key, layer, "produce", exc=exc,
                                        fallback_nedeni="uretim_istisnasi")
                        rapor["hata"].append("%s/%s/%s: %s"
                                             % (layer, natal_idx, lord, exc))
            rapor["katmanlar"][layer] = sayac

        # 3) Bakim
        rapor["silinen_snapshot"] = store.prune_snapshots(
            (d - timedelta(days=SNAPSHOT_RETENTION_DAYS)).isoformat())
    finally:
        store.release_lock(kilit_adi, sahip)

    return rapor


# ------------------------------------------------------------ okuma yolu

def rule_only(layer, natal_idx, lord, d):
    """Snapshot varsa yalniz kural motoruyla aninda uretir.

    AI cagrisi YAPILMAZ. Snapshot yoksa None doner ve hicbir hesaplama
    baslatilmaz.
    """
    if not store.exists():
        return None
    snaps = load_snapshots(layer, d)
    if snaps is None:
        return None
    key = build_key(layer, d, natal_idx, lord)
    produce(layer, snaps, natal_idx, lord, d, allow_llm=False)
    return store.get(key)
