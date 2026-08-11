#!/usr/bin/env python3
"""
Standalone rectification API.

This service exposes only rectification routes on a separate local port so
heavy rectification scans do not need to share the main dashboard/API process.
"""

import hmac
import os
from ipaddress import ip_address

from flask import Flask, jsonify, request

from app import (
    app as main_app,
    _build_rectification_analysis,
    _build_rectification_report,
    _rectification_payload_from_save_data,
    _rectification_save_gate,
    _save_rectification_record,
)


ALLOWED_DASHBOARD_ORIGINS = {
    "http://127.0.0.1:5000",
    "http://localhost:5000",
}

rectification_app = Flask(__name__)
rectification_app.config["LOCAL_ACCESS_ONLY"] = main_app.config["LOCAL_ACCESS_ONLY"]
rectification_app.config["MAX_CONTENT_LENGTH"] = main_app.config["MAX_CONTENT_LENGTH"]
rectification_app.config["VAULT_ASTROLOGY_ROOT"] = main_app.config["VAULT_ASTROLOGY_ROOT"]
rectification_app.config["API_TOKEN"] = os.environ.get(
    "VEDIC_RECTIFICATION_API_TOKEN",
    "",
).strip()
rectification_app.config["ALLOWED_DASHBOARD_ORIGINS"] = ALLOWED_DASHBOARD_ORIGINS


@rectification_app.before_request
def _require_local_access():
    content_length = request.content_length
    max_content_length = rectification_app.config.get("MAX_CONTENT_LENGTH")
    if (
        content_length is not None
        and max_content_length is not None
        and content_length > max_content_length
    ):
        return jsonify({
            "ok": False,
            "error": "İstek güvenli boyut sınırını aşıyor.",
        }), 413

    if not rectification_app.config["LOCAL_ACCESS_ONLY"]:
        configured_token = rectification_app.config.get("API_TOKEN") or ""
        if not configured_token:
            return jsonify({
                "ok": False,
                "error": "Rektifikasyon servisi kimlik doğrulaması yapılandırılmamış.",
            }), 503
        authorization = request.headers.get("Authorization", "")
        supplied_token = (
            authorization[7:].strip()
            if authorization.lower().startswith("bearer ")
            else ""
        )
        if not supplied_token or not hmac.compare_digest(supplied_token, configured_token):
            return jsonify({
                "ok": False,
                "error": "Rektifikasyon servisi yetkilendirmesi geçersiz.",
            }), 401
        return None

    remote_addr = request.remote_addr
    try:
        is_local = bool(remote_addr) and ip_address(remote_addr).is_loopback
    except ValueError:
        is_local = False

    if not is_local:
        return jsonify({
            "ok": False,
            "error": "Bu API yalnızca yerel cihazdan kullanılabilir.",
        }), 403
    return None


@rectification_app.after_request
def _add_security_headers(response):
    origin = request.headers.get("Origin")
    if origin in rectification_app.config["ALLOWED_DASHBOARD_ORIGINS"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "600"
        response.headers["Vary"] = "Origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@rectification_app.errorhandler(413)
def _request_too_large(_error):
    return jsonify({
        "ok": False,
        "error": "İstek güvenli boyut sınırını aşıyor.",
    }), 413


@rectification_app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "status": "rectification_service_ready",
        "service": "progresif-vedic-rectification",
    })


@rectification_app.route("/api/v2/rectification/analyze", methods=["POST"])
def api_v2_rectification_analyze():
    try:
        data = request.get_json() or {}
        result = _build_rectification_analysis(data)
        return jsonify(result)

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Geçersiz veri: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Rektifikasyon hatası: {str(e)}"}), 500


@rectification_app.route("/api/v2/rectification/report", methods=["POST"])
def api_v2_rectification_report():
    try:
        data = request.get_json() or {}
        result = _build_rectification_report(data)
        return jsonify(result)

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Geçersiz rektifikasyon rapor verisi: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Rektifikasyon rapor hatası: {str(e)}"}), 500


@rectification_app.route("/api/v2/rectification/save", methods=["POST"])
def api_v2_rectification_save():
    try:
        data = request.get_json() or {}
        record = _rectification_payload_from_save_data(data)
        overwrite = bool(data.get("overwrite", False))
        result = {
            "person": record["person"],
            "birth_base": record["birth_base"],
            "birth_window": record["birth_window"],
            "source_docs": record["source_docs"],
            "search_window": record["search_window"],
            "events": record["events"],
            "event_count": len(record["events"]),
        }
        save_gate = _rectification_save_gate(record)
        if save_gate:
            http_status = save_gate.pop("_http_status", 400)
            result.update(save_gate)
            return jsonify(result), http_status
        save_result = _save_rectification_record(record, overwrite=overwrite)
        http_status = save_result.pop("_http_status", 200)
        result.update(save_result)
        return jsonify(result), http_status

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Geçersiz rektifikasyon kayıt verisi: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Rektifikasyon kayıt hatası: {str(e)}"}), 500


if __name__ == "__main__":
    host = os.environ.get("PROGRESIF_RECTIFICATION_HOST", "127.0.0.1")
    port = int(os.environ.get("PROGRESIF_RECTIFICATION_PORT", "5051"))
    rectification_app.run(debug=False, host=host, port=port)
