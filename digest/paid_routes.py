"""Ucretli kisisel digest route'u. Mevcut hicbir route ile cakismaz.

app.py'de _beta_db / _beta_load_json / _account_deletion_user_id fonksiyonlarini
KULLANIR ama import etmez modul seviyesinde (dongusel import olur, cunku
app.py bu paketi register ediyor). Route fonksiyonu icinde gec (lazy)
import edilir — writer.py'nin vertex_bridge_client'i cagirma seklinin
aynisi.

Sozlesme: chart_id + profile_id + owner_user_id ile /api/v2/beta/chart/summary
ile BIREBIR ayni dogrulama/sahiplik kontrolu. beta_charts.chart_json zaten
tam v2 chart'i tutuyor; burada AYRICA hesap yapilmaz, yalniz okunur.

Gunde bir chart_id icin tek Gemini cagrisi (paid_store ile onbellek).
Basarisizlikta ok:false + neden doner; 500 degil — caller (Next.js) bunu
"mevcut statik digest'i goster" sinyali olarak okur.
"""

import hashlib
import json
import re
import time
from contextlib import closing

from flask import Blueprint, jsonify, request

from . import batch, paid_store, paid_writer, store
from .keys import today_ist
from .situation import required_days
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
    gunler = []
    for katman in ("daily", "weekly", "monthly"):
        for gun in required_days(katman, d):
            if gun not in gunler:
                gunler.append(gun)
    return sorted(gunler)


def _load_homepage_snapshots(d):
    """Ortak snapshot onbelleğini kullan; ayni gun icin tek hesap yap."""
    store.init()
    gunler = _required_snapshot_days(d)
    snaps = store.get_snapshots(gunler)
    if snaps is not None:
        return snaps, 0

    lock_key = "homepage:snapshots:%s" % d.isoformat()
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

        d = today_ist()
        snapshots, snapshot_ms = _load_homepage_snapshots(d)
        if snapshots is None:
            return jsonify({
                "ok": False,
                "status": "generation_pending",
                "fallback_nedeni": "durum_paketi_hazir_degil",
                "chart_id": chart_id,
                "profile_id": profile_id,
            }), 200

        required = _required_snapshot_days(d)
        snap_by_day = {g.isoformat(): snap for g, snap in zip(required, snapshots)}
        paketler = {}
        for katman in ("daily", "weekly", "monthly"):
            snaps = [snap_by_day[g.isoformat()] for g in required_days(katman, d)]
            paketler[katman] = build_paid_situation(chart, katman, snaps)

        context = build_homepage_context(chart, d, paketler)
        chart_hash = _sha256(chart)
        context_hash = _sha256({
            "chart_hash": chart_hash,
            "context": context,
            "snapshot_hash": _sha256(snapshots),
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

        lock_key = "homepage:gemini:%s:%s:%s" % (owner_user_id, chart_id, d.isoformat())
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
                paketler["daily"], paketler["weekly"], paketler["monthly"],
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
            "snapshot_ms": snapshot_ms,
        })

    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": "Geçersiz kişisel digest isteği: %s" % e}), 400
    except Exception:
        return jsonify({
            "ok": False,
            "status": "generation_unavailable",
            "fallback_nedeni": "beklenmeyen_sunucu_hatasi",
        }), 200
