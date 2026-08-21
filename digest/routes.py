"""Blueprint. Mevcut hicbir route ile cakismaz.

GET yolunun sozlesmesi:
  - Kayit varsa dondurur.
  - Kayit yok ama snapshot varsa YALNIZ kural motoruyla uretir (AI yok).
  - Snapshot da yoksa not_ready doner; hicbir hesaplama baslatmaz.
  - DB dosyasi yoksa YARATMAZ.
"""

import hmac
import os
from datetime import date

from flask import Blueprint, jsonify, request

from . import batch, store
from .keys import DASHA_LORDS, LAYER_DASHA_LEVEL, build_key, normalize_lord, today_ist

digest_bp = Blueprint("digest", __name__)


def _rebuild_token():
    return os.getenv("DIGEST_REBUILD_TOKEN", "")


def _read(layer, natal_idx, lord, d):
    """Doner: (kayit, durum). kayit None ise durum 'not_ready'."""
    key = build_key(layer, d, natal_idx, lord)

    if store.exists():
        row = store.get(key)
        if row:
            return row, "hazir"

    row = batch.rule_only(layer, natal_idx, lord, d)
    if row:
        return row, "kural_ile_uretildi"
    return None, "not_ready"


@digest_bp.route("/api/pwa/digest", methods=["GET"])
def pwa_digest():
    try:
        natal_idx = int(request.args.get("moon_sign_index", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "moon_sign_index zorunlu, 0-11 tam sayi"}), 400
    if not 0 <= natal_idx <= 11:
        return jsonify({"error": "moon_sign_index 0-11 araliginda olmali"}), 400

    antara = normalize_lord(request.args.get("antara_lord", ""))
    pratyantar = normalize_lord(request.args.get("pratyantar_lord", ""))

    if antara is None or pratyantar is None:
        return jsonify({
            "error": "antara_lord ve pratyantar_lord zorunlu",
            "gecerli_degerler": DASHA_LORDS,
            "not": "haftalik pratyantar, aylik antara seviyesini kullanir",
        }), 400

    d = today_ist()
    try:
        daily, d_st = _read("daily", natal_idx, None, d)
        weekly, w_st = _read("weekly", natal_idx, pratyantar, d)
        monthly, m_st = _read("monthly", natal_idx, antara, d)
    except Exception as exc:
        store.log_error(None, None, "read", exc=exc,
                        fallback_nedeni="okuma_hatasi")
        return jsonify({"error": "digest okunamadi"}), 500

    hazir = all(x is not None for x in (daily, weekly, monthly))
    return jsonify({
        "tarih": d.isoformat(),
        "hazir": hazir,
        "generator": store.active_generator(),
        "dasha_seviyeleri": LAYER_DASHA_LEVEL,
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "durum": {"daily": d_st, "weekly": w_st, "monthly": m_st},
    }), (200 if hazir else 202)


@digest_bp.route("/api/pwa/digest/rebuild", methods=["POST"])
def pwa_digest_rebuild():
    token = request.headers.get("X-Digest-Token", "")
    beklenen = _rebuild_token()
    if not beklenen or not hmac.compare_digest(token, beklenen):
        return jsonify({"error": "yetkisiz"}), 403

    body = request.get_json(silent=True) or {}
    force = bool(body.get("force", False))
    d = date.fromisoformat(body["date"]) if body.get("date") else None
    layers = body.get("layers")
    allow_llm = body.get("llm")

    try:
        return jsonify(batch.run(d=d, layers=layers, force=force,
                                 allow_llm=allow_llm))
    except ValueError as exc:
        return jsonify({"error": "yol dogrulamasi: %s" % exc}), 400
    except Exception as exc:
        store.log_error(None, None, "rebuild", exc=exc,
                        fallback_nedeni="toplu_uretim_basarisiz")
        return jsonify({"error": "toplu uretim basarisiz: %s" % exc}), 500


@digest_bp.route("/api/pwa/digest/stats", methods=["GET"])
def pwa_digest_stats():
    """Salt okuma. DB dosyasi yoksa yaratmaz."""
    try:
        return jsonify(store.stats())
    except ValueError as exc:
        return jsonify({"error": "yol dogrulamasi: %s" % exc}), 400


@digest_bp.route("/api/pwa/digest/errors", methods=["GET"])
def pwa_digest_errors():
    token = request.headers.get("X-Digest-Token", "")
    beklenen = _rebuild_token()
    if not beklenen or not hmac.compare_digest(token, beklenen):
        return jsonify({"error": "yetkisiz"}), 403
    try:
        n = min(int(request.args.get("n", 50)), 200)
    except (TypeError, ValueError):
        n = 50
    return jsonify({"hatalar": store.recent_errors(n)})
