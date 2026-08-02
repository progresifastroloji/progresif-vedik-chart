import json
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from app import app, _beta_db, _beta_json, _beta_now


PROFILE_ID = "33333333-3333-4333-8333-333333333333"
CHART_ID = "chart-methodology-test"


def _model_payload():
    analysis = {
        "summary": "Kariyer konusunda destek ve sınırlar birlikte görülüyor.",
        "supporting_evidence": [
            {"claim": "Destekleyici faktör var", "evidence_path": "evidence.topic_packet"},
        ],
        "challenging_evidence": [
            {"claim": "Zorlayıcı faktör var", "evidence_path": "evidence.topic_packet"},
        ],
        "missing_layers": [],
        "confidence": "medium",
        "limitations": ["Nihai metodoloji seçilmedi."],
    }
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(analysis)}]}}],
        "usageMetadata": {"totalTokenCount": 123},
        "modelVersion": "test-model",
    }


class BetaMethodologyCompareEndpointTest(unittest.TestCase):
    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_heavy_limit = app.config["BETA_DAILY_HEAVY_LIMIT"]
        self._tmp = tempfile.TemporaryDirectory()
        app.config["BETA_DB_PATH"] = f"{self._tmp.name}/beta.sqlite3"
        app.config["BETA_DAILY_HEAVY_LIMIT"] = 3
        self.client = app.test_client()
        chart = {
            "birth": {"person": {"id": PROFILE_ID}, "date": "2000-01-01"},
            "lagna": {"sign": "Aries", "degree_str": "10°"},
            "dashas": {"vimshottari": {"current_active": {"maha": "Saturn"}}},
            "topic_packets": {
                "career": {
                    "confidence": "medium",
                    "supporting_factors": [{"code": "career-support"}],
                    "challenging_factors": [{"code": "career-challenge"}],
                    "missing_factors": [],
                    "required_but_missing": [],
                },
            },
            "missing": [],
            "data_quality": {"status": "complete"},
        }
        with closing(_beta_db()) as conn:
            conn.execute(
                "INSERT INTO beta_charts (id, profile_id, chart_json, created_at) VALUES (?, ?, ?, ?)",
                (CHART_ID, PROFILE_ID, _beta_json(chart), _beta_now()),
            )
            conn.commit()

    def tearDown(self):
        app.config["BETA_DB_PATH"] = self._old_beta_db_path
        app.config["BETA_DAILY_HEAVY_LIMIT"] = self._old_heavy_limit
        self._tmp.cleanup()

    @patch("app.call_vertex_bridge")
    def test_endpoint_runs_three_candidates_and_replays_idempotently(self, bridge_call):
        bridge_call.side_effect = lambda request_id, _request: (request_id, _model_payload())
        payload = {
            "comparison_id": "methodology-compare-endpoint-1",
            "profile_id": PROFILE_ID,
            "chart_id": CHART_ID,
            "question": "Kariyer açısından güçlü ve zorlayıcı teknik kanıtlar nelerdir?",
        }

        first = self.client.post("/api/v2/beta/chat/compare", json=payload)
        second = self.client.post("/api/v2/beta/chat/compare", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        data = first.get_json()
        replay = second.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "comparison_ready")
        self.assertEqual(data["completed_count"], 3)
        self.assertEqual(len(data["methodology_results"]), 3)
        self.assertIsNone(data["selection"])
        self.assertFalse(data["replayed"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["usage"]["heavy"]["used"], 1)
        self.assertEqual(bridge_call.call_count, 3)
        usage = self.client.get(f"/api/v2/beta/usage?profile_id={PROFILE_ID}").get_json()
        self.assertEqual(usage["counts"]["methodology_comparisons"], 1)

    @patch("app.call_vertex_bridge")
    def test_endpoint_rejects_comparison_id_collision(self, bridge_call):
        bridge_call.side_effect = lambda request_id, _request: (request_id, _model_payload())
        base = {
            "comparison_id": "methodology-compare-endpoint-2",
            "profile_id": PROFILE_ID,
            "chart_id": CHART_ID,
            "question": "Kariyer kanıtları nelerdir?",
        }
        self.assertEqual(self.client.post("/api/v2/beta/chat/compare", json=base).status_code, 200)
        base["question"] = "Farklı soru"

        collision = self.client.post("/api/v2/beta/chat/compare", json=base)

        self.assertEqual(collision.status_code, 400)
        self.assertEqual(collision.get_json()["status"], "invalid_request")
        self.assertEqual(bridge_call.call_count, 3)

    @patch("app.call_vertex_bridge")
    def test_endpoint_blocks_before_model_when_heavy_limit_is_full(self, bridge_call):
        app.config["BETA_DAILY_HEAVY_LIMIT"] = 0

        response = self.client.post(
            "/api/v2/beta/chat/compare",
            json={
                "comparison_id": "methodology-compare-endpoint-3",
                "profile_id": PROFILE_ID,
                "chart_id": CHART_ID,
                "question": "Kariyer kanıtları nelerdir?",
            },
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.get_json()["status"], "heavy_limit_exceeded")
        bridge_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
