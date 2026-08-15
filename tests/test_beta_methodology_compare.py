import json
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from app import (
    app,
    _beta_build_chat_draft,
    _beta_db,
    _beta_detect_subject_topic,
    _beta_detect_topic,
    _beta_shadbala_strength_summary,
    _beta_json,
    _beta_now,
)
from methodology_orchestrator import MAX_PROMPT_BYTES, _canonical_json, _model_request, compact_evidence, load_methodology_candidates


PROFILE_ID = "33333333-3333-4333-8333-333333333333"
CHART_ID = "chart-methodology-test"


def _model_payload():
    analysis = {
        "question_intent": {
            "interpreted_question": "Kariyer göstergelerini değerlendirmek",
            "primary_topic": "career",
            "timing_required": False,
        },
        "analysis_status": "COMPLETE",
        "methodology_coverage": [
            {"step": step, "status": "applied", "note": f"{step} uygulandı"}
            for step in (
                "question_and_scope", "topic_package", "data_gate",
                "d1_natal_promise", "bhava_lord_karaka",
                "dispositor_and_nakshatra", "strength_capacity_delivery",
                "relevant_varga", "dasha_access", "transit_trigger",
                "counter_evidence", "thematic_synthesis",
            )
        ],
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
        self.assertEqual(data["completed_count"], 1)
        self.assertEqual(len(data["methodology_results"]), 1)
        self.assertEqual(data["selection"], "vedic-system-methodology-v1")
        self.assertFalse(data["replayed"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["usage"]["heavy"]["used"], 1)
        self.assertEqual(bridge_call.call_count, 1)
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
        self.assertEqual(bridge_call.call_count, 1)

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

    def test_three_month_career_question_uses_transit_with_career_subject(self):
        question = "Önümüzdeki üç ay kariyerimde hangi dönemler öne çıkıyor?"

        self.assertEqual(_beta_detect_topic(question), "transit")
        self.assertEqual(_beta_detect_subject_topic(question), "career")

    def test_character_router_and_shadbala_ranking_use_ratio(self):
        self.assertEqual(
            _beta_detect_topic("Haritamdaki en güçlü karakter özelliğim nedir?"),
            "character",
        )
        summary = _beta_shadbala_strength_summary({
            "shadbala": {
                "planets": [
                    {
                        "planet": "Sun",
                        "total_score": 175.55,
                        "professional_total": {"strength_ratio": 1.4391, "total_rupa": 7.1957, "required_rupa": 5.0},
                    },
                    {
                        "planet": "Saturn",
                        "total_score": 210.56,
                        "professional_total": {"strength_ratio": 1.2682, "total_rupa": 6.341, "required_rupa": 5.0},
                    },
                ],
            },
        })
        self.assertEqual(summary["comparison_basis"], "strength_ratio_only")
        self.assertEqual(summary["strongest_planet"], "Sun")
        self.assertEqual(
            [row["planet"] for row in summary["ranking"]],
            ["Sun", "Saturn"],
        )

    @patch("app._pwa_transit_pack")
    def test_transit_draft_keeps_subject_packet_and_bounded_daily_evidence(self, transit_pack):
        transit_pack.return_value = {
            "period": {
                "type": "three_month",
                "range_start": "2026-08-01",
                "range_end": "2026-08-02",
                "day_count": 2,
            },
            "natal": {"lagna_sign": "Aries", "moon_sign": "Taurus"},
            "days": [
                {
                    "date": f"2026-08-0{day}",
                    "active_dasha_path": ["Saturn", "Venus", "Jupiter"],
                    "planets": [
                        {"name": "Moon", "sign": "Aries", "nakshatra": "Ashwini", "nakshatra_pada": 1, "house_from_lagna": 1, "house_from_moon": 12},
                        {"name": "Saturn", "sign": "Pisces", "degree_str": "10°", "house_from_lagna": 12, "house_from_moon": 11, "retrograde": True, "ashtakavarga": {"sav": 30, "bav": 4}},
                    ],
                    "natal_contacts": [
                        {"transit_planet": "Saturn", "natal_planet": "Moon", "contact_type": "degree_orb", "orb": 0.5 + day, "sign": "Pisces", "house_from_lagna": 12, "house_from_moon": 11},
                    ],
                }
                for day in (1, 2)
            ],
        }
        chart = {
            "birth": {"person": {"name": "Test"}},
            "lagna": {"sign": "Aries"},
            "dashas": {"vimshottari": {"current_active": {"path": ["Saturn", "Venus", "Jupiter"]}}},
            "topic_packets": {"career": {"confidence": "medium", "missing_factors": [], "required_but_missing": [], "evidence": {"active_dasha": {"path": ["Rahu", "Rahu"]}}}},
            "missing": [],
            "data_quality": {"status": "complete"},
        }

        draft = _beta_build_chat_draft(
            "Önümüzdeki üç ay kariyerimde hangi dönemler öne çıkıyor?",
            chart,
        )
        evidence = compact_evidence(draft)
        request, _ = _model_request(load_methodology_candidates()[0], evidence)

        self.assertEqual(draft["topic"], "transit")
        self.assertEqual(draft["subject_topic"], "career")
        self.assertIsNot(draft["evidence"]["topic_packet"], chart["topic_packets"]["career"])
        self.assertEqual(
            draft["evidence"]["topic_packet"]["evidence"]["active_dasha"]["path"],
            ["Saturn", "Venus", "Jupiter"],
        )
        self.assertEqual(len(evidence["transits"]["daily_timing"]), 2)
        self.assertLess(len(_canonical_json(request).encode("utf-8")), MAX_PROMPT_BYTES)


if __name__ == "__main__":
    unittest.main()
