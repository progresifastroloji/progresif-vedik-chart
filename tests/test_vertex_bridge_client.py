import hashlib
import hmac
import io
import json
import os
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from app import app
from vertex_bridge_client import VertexBridgeClientError, call_vertex_bridge


TEST_SECRET = "a" * 64
TEST_URL = "https://vedic-bridge.example"


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.closed = False

    def read(self, _limit):
        return self._payload

    def close(self):
        self.closed = True


class VertexBridgeClientTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch.dict(
        os.environ,
        {
            "VEDIC_VERTEX_BRIDGE_URL": TEST_URL,
            "VEDIC_MACHINE_HMAC_SECRET": TEST_SECRET,
        },
        clear=False,
    )
    def test_client_signs_exact_body_and_returns_json(self):
        captured = {}
        response = _FakeResponse(b'{"candidates":[{"content":{"parts":[{"text":"TAMAM"}]}}]}')

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return response

        request_id, payload = call_vertex_bridge(
            "test-request-1",
            {"contents": [{"role": "user", "parts": [{"text": "TAMAM yaz"}]}]},
            opener=opener,
            now=lambda: 1_800_000_000,
            nonce=lambda: "018f47d2-4cf5-7a30-8a0f-8da7167d9101",
        )

        sent = captured["request"]
        raw_body = sent.data
        body_hash = hashlib.sha256(raw_body).hexdigest()
        canonical = (
            "1800000000\n018f47d2-4cf5-7a30-8a0f-8da7167d9101\n" + body_hash
        ).encode("utf-8")
        expected = "v1=" + hmac.new(
            TEST_SECRET.encode("utf-8"), canonical, hashlib.sha256
        ).hexdigest()

        self.assertEqual(request_id, "test-request-1")
        self.assertEqual(sent.full_url, f"{TEST_URL}/v1/generate")
        self.assertEqual(sent.method, "POST")
        self.assertEqual(sent.headers["X-vedic-timestamp"], "1800000000")
        self.assertEqual(
            sent.headers["X-vedic-nonce"],
            "018f47d2-4cf5-7a30-8a0f-8da7167d9101",
        )
        self.assertTrue(hmac.compare_digest(sent.headers["X-vedic-signature"], expected))
        self.assertEqual(json.loads(raw_body), {
            "request_id": "test-request-1",
            "request": {
                "contents": [{"role": "user", "parts": [{"text": "TAMAM yaz"}]}],
            },
        })
        self.assertEqual(payload["candidates"][0]["content"]["parts"][0]["text"], "TAMAM")
        self.assertTrue(response.closed)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_config_fails_closed(self):
        with self.assertRaises(VertexBridgeClientError) as raised:
            call_vertex_bridge("test-request", {"contents": [{}]})

        self.assertEqual(raised.exception.code, "vertex_bridge_unavailable")
        self.assertEqual(raised.exception.http_status, 503)

    @patch.dict(
        os.environ,
        {
            "VEDIC_VERTEX_BRIDGE_URL": TEST_URL,
            "VEDIC_MACHINE_HMAC_SECRET": TEST_SECRET,
        },
        clear=False,
    )
    def test_invalid_request_is_rejected_before_network(self):
        def opener(_request, _timeout):
            self.fail("Geçersiz istek ağ çağrısı yapmamalı")

        with self.assertRaises(VertexBridgeClientError) as raised:
            call_vertex_bridge(
                "bad request id",
                {"contents": []},
                opener=opener,
            )

        self.assertEqual(raised.exception.code, "vertex_request_id_invalid")
        self.assertEqual(raised.exception.http_status, 400)

    @patch.dict(
        os.environ,
        {
            "VEDIC_VERTEX_BRIDGE_URL": TEST_URL,
            "VEDIC_MACHINE_HMAC_SECRET": TEST_SECRET,
        },
        clear=False,
    )
    def test_provider_error_body_is_not_exposed(self):
        def opener(request, timeout):
            raise HTTPError(
                request.full_url,
                400,
                "Bad Request",
                {},
                io.BytesIO(b'{"secret_provider_detail":"must-not-leak"}'),
            )

        with self.assertRaises(VertexBridgeClientError) as raised:
            call_vertex_bridge(
                "test-request",
                {"contents": [{}]},
                opener=opener,
            )

        self.assertEqual(raised.exception.code, "vertex_bridge_rejected")
        self.assertNotIn("must-not-leak", str(raised.exception))

    @patch("app.call_vertex_bridge")
    def test_api_endpoint_returns_bridge_response(self, bridge_call):
        bridge_call.return_value = (
            "api-request-1",
            {"candidates": [{"content": {"parts": [{"text": "TAMAM"}]}}]},
        )

        response = self.client.post(
            "/api/v2/ai/generate",
            json={
                "request_id": "api-request-1",
                "request": {"contents": [{"parts": [{"text": "TAMAM yaz"}]}]},
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["request_id"], "api-request-1")
        self.assertEqual(data["response"]["candidates"][0]["content"]["parts"][0]["text"], "TAMAM")

    @patch("app.call_vertex_bridge")
    def test_api_endpoint_returns_safe_classified_error(self, bridge_call):
        bridge_call.side_effect = VertexBridgeClientError("vertex_bridge_rejected", 502)

        response = self.client.post(
            "/api/v2/ai/generate",
            json={"request_id": "api-request-2", "request": {"contents": [{}]}},
        )

        self.assertEqual(response.status_code, 502)
        data = response.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["status"], "model_unavailable")
        self.assertEqual(data["error_code"], "vertex_bridge_rejected")
        self.assertNotIn("provider", json.dumps(data))

    @patch("app.call_vertex_bridge")
    def test_api_endpoint_rejects_non_object_json(self, bridge_call):
        response = self.client.post("/api/v2/ai/generate", json=[])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_code"], "vertex_request_invalid")
        bridge_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
