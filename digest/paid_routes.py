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

import re
from contextlib import closing
from datetime import date

from flask import Blueprint, jsonify, request

from . import paid_store, paid_writer
from .situation import planet_signs, required_days
from .paid_situation import build_paid_situation

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

    return (_beta_load_json(row["chart_json"]), chart_id, profile_id), None


def _snaps_for(katman, d):
    gunler = required_days(katman, d)
    return [planet_signs(g) for g in gunler]


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
        chart, chart_id, profile_id = sonuc

        d = date.today()

        onbellek = paid_store.get(chart_id, d)
        if onbellek:
            return jsonify({
                "ok": True,
                "status": "ready",
                "kaynak": "onbellek",
                "chart_id": chart_id,
                "profile_id": profile_id,
                "digest": onbellek,
            })

        paketler = {}
        for katman in ("daily", "weekly", "monthly"):
            snaps = _snaps_for(katman, d)
            paketler[katman] = build_paid_situation(chart, katman, snaps)

        sonuc_llm, hata_llm = paid_writer.generate(
            paketler["daily"], paketler["weekly"], paketler["monthly"]
        )

        if sonuc_llm is None:
            return jsonify({
                "ok": False,
                "status": "generation_unavailable",
                "fallback_nedeni": (hata_llm or {}).get("fallback_nedeni"),
                "chart_id": chart_id,
                "profile_id": profile_id,
            }), 200

        paid_store.set(chart_id, sonuc_llm, d)

        return jsonify({
            "ok": True,
            "status": "ready",
            "kaynak": "yeni_uretim",
            "chart_id": chart_id,
            "profile_id": profile_id,
            "digest": sonuc_llm,
        })

    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": "Geçersiz kişisel digest isteği: %s" % e}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": "Kişisel digest hatası: %s" % e}), 500
