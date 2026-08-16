"""Server-only client for the separate Vedik Vertex Cloud Run bridge."""

import hashlib
import hmac
import json
import os
import re
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# The full-context mode sends the owned natal Markdown together with the
# three-month transit Markdown. Keep the same bounded 1 MiB contract as the
# methodology prompt builder; the old 256 KiB limit rejected valid full-mode
# requests before they could reach Vertex/Gemini.
MAX_REQUEST_BYTES = 1024 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_ID_PATTERN = re.compile(r"^[0-9a-z._:-]{1,200}$", re.IGNORECASE)


class VertexBridgeClientError(Exception):
    """A safe, classified bridge failure that contains no provider response body."""

    def __init__(self, code, http_status):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


def _bridge_config():
    bridge_url = os.environ.get("VEDIC_VERTEX_BRIDGE_URL", "").strip().rstrip("/")
    secret = os.environ.get("VEDIC_MACHINE_HMAC_SECRET", "")
    try:
        timeout_seconds = float(os.environ.get("VEDIC_VERTEX_BRIDGE_TIMEOUT_SECONDS", "45"))
    except ValueError as exc:
        raise VertexBridgeClientError("vertex_bridge_config_invalid", 503) from exc

    if not bridge_url.startswith("https://") or len(secret) < 32:
        raise VertexBridgeClientError("vertex_bridge_unavailable", 503)
    if not 1 <= timeout_seconds <= 120:
        raise VertexBridgeClientError("vertex_bridge_config_invalid", 503)
    return bridge_url, secret, timeout_seconds


def _request_body(request_id, vertex_request):
    normalized_request_id = str(request_id or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(normalized_request_id):
        raise VertexBridgeClientError("vertex_request_id_invalid", 400)
    if not isinstance(vertex_request, dict):
        raise VertexBridgeClientError("vertex_request_invalid", 400)
    contents = vertex_request.get("contents")
    if not isinstance(contents, list) or not contents:
        raise VertexBridgeClientError("vertex_contents_required", 400)

    raw_body = json.dumps(
        {"request_id": normalized_request_id, "request": vertex_request},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(raw_body) > MAX_REQUEST_BYTES:
        raise VertexBridgeClientError("vertex_request_too_large", 413)
    return normalized_request_id, raw_body


def _signature(secret, timestamp, nonce, raw_body):
    body_hash = hashlib.sha256(raw_body).hexdigest()
    canonical = f"{timestamp}\n{nonce}\n{body_hash}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def call_vertex_bridge(request_id, vertex_request, *, opener=None, now=None, nonce=None):
    """Sign one Vertex request and send it through the configured Vedik bridge."""

    bridge_url, secret, timeout_seconds = _bridge_config()
    normalized_request_id, raw_body = _request_body(request_id, vertex_request)
    timestamp = str(int((now or time.time)()))
    nonce_value = str((nonce or uuid.uuid4)())
    signature = _signature(secret, timestamp, nonce_value, raw_body)
    bridge_request = Request(
        f"{bridge_url}/v1/generate",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Vedic-Timestamp": timestamp,
            "X-Vedic-Nonce": nonce_value,
            "X-Vedic-Signature": signature,
        },
        method="POST",
    )

    response = None
    try:
        response = (opener or urlopen)(bridge_request, timeout=timeout_seconds)
        raw_response = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        exc.close()
        raise VertexBridgeClientError("vertex_bridge_rejected", 502) from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise VertexBridgeClientError("vertex_bridge_unreachable", 504) from exc
    finally:
        if response is not None:
            response.close()

    if len(raw_response) > MAX_RESPONSE_BYTES:
        raise VertexBridgeClientError("vertex_bridge_response_too_large", 502)
    try:
        payload = json.loads(raw_response.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VertexBridgeClientError("vertex_bridge_response_invalid", 502) from exc
    if not isinstance(payload, dict):
        raise VertexBridgeClientError("vertex_bridge_response_invalid", 502)
    return normalized_request_id, payload
