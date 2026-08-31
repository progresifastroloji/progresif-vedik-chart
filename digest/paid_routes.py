"""Giriş yapmış harita sahibi için güncel kişisel digest route'u.

app.py'de _beta_db / _beta_load_json / _account_deletion_user_id fonksiyonlarini
KULLANIR ama import etmez modul seviyesinde (dongusel import olur, cunku
app.py bu paketi register ediyor). Route fonksiyonu icinde gec (lazy)
import edilir — writer.py'nin vertex_bridge_client'i cagirma seklinin
aynisi.

Sozlesme: chart_id + profile_id + owner_user_id ile /api/v2/beta/chart/summary
ile BIREBIR ayni dogrulama/sahiplik kontrolu. beta_charts.chart_json zaten
tam v2 chart'i tutuyor; burada AYRICA hesap yapilmaz, yalniz okunur.

Saatlik gökyüzü + chart_id için tek Gemini çağrısı (paid_store ile önbellek).
Basarisizlikta ok:false + neden doner; 500 degil — caller (Next.js) bunu
güncel yorumun hazırlanamadığı sinyali olarak okur. Eski/sabit yorum yoktur.
"""

import hashlib
import json
import re
import time
from contextlib import closing

from flask import Blueprint, jsonify, request

from . import batch, paid_store, paid_writer, store
from .keys import current_hour_ist
from .situation import planet_signs_at, required_days
from .paid_situation import (
    HOMEPAGE_CONTEXT_VERSION,
    HOMEPAGE_METHODOLOGY_VERSION,
    build_homepage_context,
    build_paid_situation,
)

paid_digest_bp = Blueprint("paid_digest", __name__)


def _load_owned_chart(data):
    """api_v2_beta_chart_summary ile ayni dogrulama/sahiplik kontrolu.

    Doner: (chart_dict, chart_id, profile_id) veya (None, jsonify_response, http_status).
    """
    from app import _account_deletion_user_id, _beta_db, _beta_load_json

    owner_user_id = _account_deletion_user_id(data.get("owner_user_id"))
    profile_id = str(data.get("profile_id") or "").strip()
    chart_id = str(data.get("chart_id") or "").strip()
    if not profile_id or not re.fullmatch(r"[0-9A-Za-z._:-]{1,200}", chart_id):
        raise ValueError("Geçerli profil ve harita kimliği gerekli")

    with closing(_beta_db()) as conn:
        row = conn.execute(
            """
            SELECT c.chart_json, c.owner_user_id,
                   p.owner_user_id AS profile_owner_user_id
            FROM beta_charts c
            JOIN beta_profiles p ON p.id = c.profile_id
            WHERE c.id = ? AND c.profile_id = ?
            """,
            (chart_id, profile_id),
        ).fetchone()

    if not row:
        return None, ("chart_not_found", 404)
    if row["owner_user_id"] != owner_user_id or row["profile_owner_user_id"] != owner_user_id:
        return None, ("ownership_mismatch", 403)

    return (_beta_load_json(row["chart_json"]), chart_id, profile_id,
            owner_user_id), None


def _required_snapshot_days(d):
    return sorted(required_days("weekly", d))


def _load_current_snapshot(local_hour):
    """Aynı İstanbul saati için ortak gerçek gökyüzü snapshot'ı."""
    store.init()
    snapshot_key = "current:%s" % local_hour.strftime("%Y-%m-%dT%H")
    snap = store.get_snapshot(snapshot_key)
    if snap is not None:
        return snap, 0

    lock_key = "homepage:current-snapshot:%s" % snapshot_key
    sahibi = store.acquire_lock(lock_key)
    if sahibi is None:
        return None, 0
    t0 = time.time()
    try:
        snap = store.get_snapshot(snapshot_key)
        if snap is None:
            snap = planet_signs_at(local_hour)
            store.put_snapshot(snapshot_key, snap)
        return snap, int((time.time() - t0) * 1000)
    finally:
        store.release_lock(lock_key, sahibi)


def _load_weekly_snapshots(d):
    """Pazartesi-pazar günlük snapshot'larını ortak önbellekten oku."""
    store.init()
    gunler = _required_snapshot_days(d)
    snaps = store.get_snapshots(gunler)
    if snaps is not None:
        return snaps, 0

    lock_key = "homepage:weekly-snapshots:%s" % d.isoformat()
    sahibi = store.acquire_lock(lock_key)
    if sahibi is None:
        return None, 0
    t0 = time.time()
    try:
        # Baska istek kilidi beklerken tamamlamis olabilir; tekrar oku.
        snaps = store.get_snapshots(gunler)
        if snaps is None:
            batch.ensure_snapshots(gunler)
            snaps = store.get_snapshots(gunler)
        if snaps is None:
            return None, int((time.time() - t0) * 1000)
        return snaps, int((time.time() - t0) * 1000)
    finally:
        store.release_lock(lock_key, sahibi)


def _sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _julian_day(local_hour):
    """Saat dilimli datetime değerini Unix kökeninden Julian güne çevirir."""
    if local_hour.tzinfo is None or local_hour.utcoffset() is None:
        raise ValueError("Saat dilimli yerel zaman gerekli")
    return (local_hour.timestamp() / 86400.0) + 2440587.5


@paid_digest_bp.route("/api/v2/pwa/digest/personal", methods=["POST"])
def api_v2_pwa_digest_personal():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("Geçerli istek gövdesi gerekli")

        sonuc, hata = _load_owned_chart(data)
        if hata:
            kod, http_status = hata
            return jsonify({"ok": False, "status": kod, "error_code": "beta_chart_%s" % kod}), http_status
        chart, chart_id, profile_id, owner_user_id = sonuc

        local_hour = current_hour_ist()
        d = local_hour.date()
        current_snapshot, current_snapshot_ms = _load_current_snapshot(local_hour)
        weekly_snapshots, weekly_snapshot_ms = _load_weekly_snapshots(d)
        if current_snapshot is None or weekly_snapshots is None:
            return jsonify({
                "ok": False,
                "status": "generation_pending",
                "fallback_nedeni": "durum_paketi_hazir_degil",
                "chart_id": chart_id,
                "profile_id": profile_id,
            }), 200

        reference_jd = _julian_day(local_hour)
        paketler = {
            "daily": build_paid_situation(
                chart, "daily", [current_snapshot], reference_jd=reference_jd,
            ),
            "weekly": build_paid_situation(
                chart, "weekly", weekly_snapshots, reference_jd=reference_jd,
            ),
        }

        context = build_homepage_context(chart, d, paketler)
        chart_hash = _sha256(chart)
        context_hash = _sha256({
            "chart_hash": chart_hash,
            "context": context,
            "snapshot_hash": _sha256({
                "current": current_snapshot,
                "weekly": weekly_snapshots,
            }),
        })
        onbellek = paid_store.get_homepage(
            owner_user_id, chart_id, d, context_hash,
            generator_version=paid_store.GENERATOR_VERSION,
            methodology_version=HOMEPAGE_METHODOLOGY_VERSION,
        )
        if onbellek:
            return jsonify({
                "ok": True,
                "status": "ready",
                "kaynak": "onbellek",
                "chart_id": chart_id,
                "profile_id": profile_id,
                "digest": onbellek,
                "context_version": HOMEPAGE_CONTEXT_VERSION,
            })

        lock_key = "homepage:gemini:%s:%s:%s" % (owner_user_id, chart_id, context_hash)
        sahibi = paid_store.acquire_lock(lock_key)
        if sahibi is None:
            return jsonify({
                "ok": False,
                "status": "generation_pending",
                "fallback_nedeni": "ayni_istek_uretiliyor",
                "chart_id": chart_id,
                "profile_id": profile_id,
            }), 200

        try:
            # Kilit sonrasi ikinci okuma, paralel istegin bitmis olmasi durumunu kapatir.
            onbellek = paid_store.get_homepage(
                owner_user_id, chart_id, d, context_hash,
                generator_version=paid_store.GENERATOR_VERSION,
                methodology_version=HOMEPAGE_METHODOLOGY_VERSION,
            )
            if onbellek:
                return jsonify({
                    "ok": True,
                    "status": "ready",
                    "kaynak": "onbellek",
                    "chart_id": chart_id,
                    "profile_id": profile_id,
                    "digest": onbellek,
                    "context_version": HOMEPAGE_CONTEXT_VERSION,
                })

            sonuc_llm, hata_llm = paid_writer.generate(
                paketler["daily"], paketler["weekly"],
                context=context,
            )

            if sonuc_llm is None:
                return jsonify({
                    "ok": False,
                    "status": "generation_unavailable",
                    "fallback_nedeni": (hata_llm or {}).get("fallback_nedeni"),
                    "chart_id": chart_id,
                    "profile_id": profile_id,
                }), 200

            paid_store.set_homepage(
                owner_user_id, chart_id, sonuc_llm, d, context_hash,
                generator_version=paid_store.GENERATOR_VERSION,
                methodology_version=HOMEPAGE_METHODOLOGY_VERSION,
            )
        finally:
            paid_store.release_lock(lock_key, sahibi)

        return jsonify({
            "ok": True,
            "status": "ready",
            "kaynak": "yeni_uretim",
            "chart_id": chart_id,
            "profile_id": profile_id,
            "digest": sonuc_llm,
            "context_version": HOMEPAGE_CONTEXT_VERSION,
            "snapshot_ms": current_snapshot_ms + weekly_snapshot_ms,
        })

    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": "Geçersiz kişisel digest isteği: %s" % e}), 400
    except Exception:
        return jsonify({
            "ok": False,
            "status": "generation_unavailable",
            "fallback_nedeni": "beklenmeyen_sunucu_hatasi",
        }), 200
