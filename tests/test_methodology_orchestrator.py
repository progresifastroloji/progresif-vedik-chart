import json
import tempfile
import unittest
from pathlib import Path

from methodology_orchestrator import (
    CANDIDATE_MANIFEST,
    MethodologyOrchestrationError,
    load_methodology_candidates,
    run_methodology_comparison,
    validate_methodology_response,
)


def _draft():
    return {
        "status": "evidence_ready",
        "question": "Kariyer alanındaki güçlü ve zorlayıcı göstergeler nelerdir?",
        "topic": "career",
        "confidence": "medium",
        "missing": [],
        "safety_notes": ["Kesin hüküm üretme."],
        "evidence": {
            "chart_summary": {"lagna": {"sign": "Aries"}},
            "active_dasha": {"status": "available", "maha": "Saturn"},
            "topic_packet": {
                "supporting_factors": [{"code": "career-support"}],
                "challenging_factors": [{"code": "career-challenge"}],
            },
            "data_quality": {"status": "complete"},
            "transits": {"must_not_be_sent_for_natal_topic": True},
        },
    }


def _payload(summary="Teknik özet"):
    analysis = {
        "summary": summary,
        "supporting_evidence": [
            {"claim": "Destek var", "evidence_path": "evidence.topic_packet"},
        ],
        "challenging_evidence": [
            {"claim": "Sınır var", "evidence_path": "evidence.topic_packet"},
        ],
        "missing_layers": [],
        "confidence": "medium",
        "limitations": ["Bu bir aday metodoloji çıktısıdır."],
    }
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(analysis)}]}}],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 50,
            "totalTokenCount": 150,
        },
        "modelVersion": "test-model",
    }


class MethodologyOrchestratorTest(unittest.TestCase):
    def test_manifest_loads_exact_three_candidate_documents(self):
        candidates = load_methodology_candidates()

        self.assertEqual(
            [candidate["id"] for candidate in candidates],
            [candidate["id"] for candidate in CANDIDATE_MANIFEST],
        )
        self.assertTrue(all(candidate["status"] == "candidate" for candidate in candidates))
        self.assertTrue(all(candidate["document"].startswith("---\n") for candidate in candidates))

    def test_comparison_runs_each_candidate_with_same_evidence_and_no_selection(self):
        calls = []

        def model_call(request_id, request):
            calls.append((request_id, request))
            return request_id, _payload(request_id)

        result = run_methodology_comparison(
            _draft(),
            "methodology-compare-test-1",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["completed_count"], 3)
        self.assertIsNone(result["selection"])
        self.assertEqual(result["selection_status"], "user_review_required")
        self.assertEqual(len(calls), 3)
        self.assertEqual(
            {item["evidence_sha256"] for item in result["methodology_results"]},
            {result["evidence_sha256"]},
        )
        for index, (_, request) in enumerate(calls):
            selected_id = CANDIDATE_MANIFEST[index]["id"]
            system_text = request["systemInstruction"]["parts"][0]["text"]
            self.assertIn(f"METODOLOJİ KİMLİĞİ: {selected_id}@1.0.0", system_text)
            for other in CANDIDATE_MANIFEST:
                if other["id"] != selected_id:
                    self.assertNotIn(f"METODOLOJİ KİMLİĞİ: {other['id']}@", system_text)
            user_text = request["contents"][0]["parts"][0]["text"]
            self.assertNotIn("must_not_be_sent_for_natal_topic", user_text)

    def test_one_invalid_model_response_is_isolated_without_selecting_winner(self):
        call_count = 0

        def model_call(request_id, _request):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return request_id, {"candidates": []}
            return request_id, _payload()

        result = run_methodology_comparison(
            _draft(),
            "methodology-compare-test-2",
            model_call,
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["completed_count"], 2)
        self.assertIsNone(result["selection"])
        self.assertEqual(
            [item["status"] for item in result["methodology_results"]],
            ["completed", "failed", "completed"],
        )

    def test_response_rejects_a_made_up_evidence_path(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0]["evidence_path"] = "evidence.nonexistent.layer"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, {"topic_packet": {}})

        self.assertEqual(raised.exception.code, "methodology_model_schema_invalid")

    def test_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = Path(__file__).resolve().parents[1] / "methodologies" / "candidates"
            for candidate in CANDIDATE_MANIFEST:
                content = (source_root / candidate["filename"]).read_text(encoding="utf-8")
                (root / candidate["filename"]).write_text(content, encoding="utf-8")
            path = root / CANDIDATE_MANIFEST[0]["filename"]
            path.write_text(path.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")

            with self.assertRaises(MethodologyOrchestrationError) as raised:
                load_methodology_candidates(root)

        self.assertEqual(raised.exception.code, "methodology_checksum_mismatch")


if __name__ == "__main__":
    unittest.main()
