import json
import tempfile
import unittest
from pathlib import Path

from methodology_orchestrator import (
    CANDIDATE_MANIFEST,
    MethodologyOrchestrationError,
    _model_request,
    load_methodology_candidates,
    run_methodology_comparison,
    validate_methodology_response,
)


def _draft():
    return {
        "status": "evidence_ready",
        "question": "Kariyer alanındaki güçlü ve zorlayıcı göstergeler nelerdir?",
        "topic": "career",
        "subject_topic": "career",
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
        "question_intent": {
            "interpreted_question": "Kariyer alanındaki ana güçler ve sınırlar",
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
        "summary": summary,
        "supporting_evidence": [
            {"claim": "Destek var", "evidence_path": "evidence.topic_packet"},
        ],
        "challenging_evidence": [
            {"claim": "Sınır var", "evidence_path": "evidence.topic_packet"},
        ],
        "missing_layers": [],
        "confidence": "medium",
        "limitations": ["Yalnız sağlanan kanıt kullanıldı."],
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
    def test_manifest_loads_single_active_system_methodology(self):
        candidates = load_methodology_candidates()

        self.assertEqual(
            [candidate["id"] for candidate in candidates],
            [candidate["id"] for candidate in CANDIDATE_MANIFEST],
        )
        self.assertEqual(len(candidates), 1)
        self.assertTrue(all(candidate["status"] == "active" for candidate in candidates))
        self.assertTrue(all(candidate["document"].startswith("---\n") for candidate in candidates))

    def test_analysis_runs_single_active_methodology_and_selects_it(self):
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
        self.assertEqual(result["completed_count"], 1)
        self.assertEqual(result["selection"], "vedic-system-methodology-v1")
        self.assertEqual(result["selection_status"], "system_methodology_active")
        self.assertEqual(len(calls), 1)
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

    def test_invalid_model_response_fails_closed_after_one_retry(self):
        def model_call(request_id, _request):
            return request_id, {"candidates": []}

        result = run_methodology_comparison(
            _draft(),
            "methodology-compare-test-2",
            model_call,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(
            [item["status"] for item in result["methodology_results"]],
            ["failed"],
        )

    def test_schema_invalid_response_is_retried_once_without_relaxing_validation(self):
        calls = []

        def model_call(request_id, _request):
            calls.append(request_id)
            if request_id.endswith("vedic-system-methodology-v1"):
                invalid = _payload()
                value = json.loads(invalid["candidates"][0]["content"]["parts"][0]["text"])
                value["supporting_evidence"][0]["evidence_path"] = "evidence.nonexistent.layer"
                invalid["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
                return request_id, invalid
            return request_id, _payload()

        result = run_methodology_comparison(
            _draft(),
            "methodology-compare-schema-retry",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["completed_count"], 1)
        self.assertEqual(len(calls), 2)
        system_result = result["methodology_results"][0]
        self.assertEqual(system_result["status"], "completed")
        self.assertEqual(system_result["attempt_count"], 2)
        self.assertTrue(system_result["request_id"].endswith("-retry-1"))

    def test_response_rejects_a_made_up_evidence_path(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0]["evidence_path"] = "evidence.nonexistent.layer"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, {
                "topic": "career",
                "subject_topic": "career",
                "topic_packet": {},
            })

        self.assertEqual(raised.exception.code, "methodology_model_evidence_invalid")

    def test_response_accepts_only_existing_list_index_paths(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0]["evidence_path"] = "evidence.topic_packet.supporting_factors.0.code"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "career",
            "subject_topic": "career",
            "topic_packet": {"supporting_factors": [{"code": "career-support"}]},
        }

        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(
            validated["supporting_evidence"][0]["evidence_path"],
            "evidence.topic_packet.supporting_factors.0.code",
        )

        value["supporting_evidence"][0]["evidence_path"] = "evidence.topic_packet.supporting_factors.1.code"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        with self.assertRaises(MethodologyOrchestrationError):
            validate_methodology_response(payload, evidence)

    def test_response_canonicalizes_topic_evidence_shorthand_only_when_it_exists(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0]["evidence_path"] = "evidence.topic_packet.houses.0.occupants"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "career",
            "subject_topic": "career",
            "topic_packet": {
                "evidence": {
                    "houses": [{"occupants": ["Moon"]}],
                },
            },
        }

        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(
            validated["supporting_evidence"][0]["evidence_path"],
            "evidence.topic_packet.evidence.houses.0.occupants",
        )

        value["supporting_evidence"][0]["evidence_path"] = "evidence.topic_packet.houses.1.occupants"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        with self.assertRaises(MethodologyOrchestrationError):
            validate_methodology_response(payload, evidence)

    def test_response_uses_router_topic_and_timing_as_authority(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["question_intent"]["primary_topic"] = "spiritual"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {"topic": "character", "subject_topic": "character", "topic_packet": {}}

        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(validated["question_intent"]["primary_topic"], "character")
        self.assertFalse(validated["question_intent"]["timing_required"])

        value["question_intent"]["primary_topic"] = "character"
        value["question_intent"]["timing_required"] = True
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(validated["question_intent"]["primary_topic"], "character")
        self.assertFalse(validated["question_intent"]["timing_required"])

    def test_timing_response_requires_real_transit_citation_and_real_date(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["summary"] = (
            "2026-08-15 tarihinde transit Ay ve Tithi birlikte bugünün temasını destekliyor."
        )
        value["supporting_evidence"][0] = {
            "claim": "2026-08-15 günü Ay kaydı ve Panchanga birlikte incelendi.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        value["challenging_evidence"][0] = {
            "claim": "Aynı günün transit kanıtı sınırlarla birlikte okundu.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "transit",
            "subject_topic": "wellbeing",
            "question_route": {"time_scope": "instant"},
            "transits": {
                "daily_records": [{
                    "date": "2026-08-15",
                    "panchanga": {"tithi": {"name": "Shukla Dvitiya"}},
                    "planets": [{"name": "Moon", "degree": "10° 00' 00\""}],
                }],
            },
        }

        validated = validate_methodology_response(payload, evidence)
        self.assertTrue(validated["question_intent"]["timing_required"])

        value["summary"] = "2026-09-30 tarihinde kesin bir olay oluşur."
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, evidence)
        self.assertEqual(
            raised.exception.code,
            "methodology_model_timing_evidence_invalid",
        )

    def test_wellbeing_response_rejects_clinical_reassurance(self):
        payload = _payload("Bu süreç klinik bir durum değil; geçici bir astrolojik etkidir.")
        evidence = {
            "topic": "character",
            "subject_topic": "wellbeing",
            "topic_packet": {},
        }

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, evidence)

        self.assertEqual(
            raised.exception.code,
            "methodology_model_wellbeing_safety_invalid",
        )

    def test_instant_wellbeing_requires_moon_and_panchanga_in_summary(self):
        payload = _payload("Bugünün transitleri duygusal yoğunluğu açıklıyor.")
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0] = {
            "claim": "Transit Ay kaydı incelendi.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        value["challenging_evidence"][0] = {
            "claim": "Günün transit sınırları dikkate alındı.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "transit",
            "subject_topic": "wellbeing",
            "question_route": {"time_scope": "instant"},
            "transits": {
                "daily_records": [{
                    "date": "2026-08-15",
                    "panchanga": {"tithi": {"name": "Shukla Dvitiya"}},
                    "planets": [{"name": "Moon", "degree": "10° 00' 00\""}],
                }],
            },
        }

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, evidence)

        self.assertEqual(
            raised.exception.code,
            "methodology_model_timing_evidence_invalid",
        )

    def test_timing_response_rejects_degree_not_present_in_evidence(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["summary"] = "Ay 27.5° derecede görünüyor."
        value["supporting_evidence"][0] = {
            "claim": "Transit Ay kaydı kullanıldı.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        value["challenging_evidence"][0] = {
            "claim": "Transit kaydının sınırları dikkate alındı.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "transit",
            "subject_topic": "wellbeing",
            "transits": {
                "daily_records": [{
                    "date": "2026-08-15",
                    "planets": [{"name": "Moon", "degree": "10° 00' 00\""}],
                }],
            },
        }

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            validate_methodology_response(payload, evidence)
        self.assertEqual(
            raised.exception.code,
            "methodology_model_timing_evidence_invalid",
        )

    def test_shadbala_claim_is_verified_and_bound_to_ratio_summary(self):
        payload = _payload()
        value = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        value["supporting_evidence"][0]["claim"] = "En yüksek Shadbala oranı Güneş'tedir."
        value["supporting_evidence"][0]["evidence_path"] = "evidence.strength_summary.planets.0"
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        evidence = {
            "topic": "career",
            "subject_topic": "career",
            "topic_packet": {},
            "strength_summary": {
                "strongest_planet": "Sun",
                "ranking": [
                    {
                        "planet": "Sun", "strength_ratio": 1.4391,
                        "total_rupa": 7.1957, "required_rupa": 5.0,
                        "legacy_raw_total": 175.55,
                    },
                    {
                        "planet": "Saturn", "strength_ratio": 1.2682,
                        "total_rupa": 6.341, "required_rupa": 5.0,
                        "legacy_raw_total": 210.56,
                    },
                ],
            },
        }

        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(
            validated["supporting_evidence"][0]["evidence_path"],
            "evidence.strength_summary",
        )

        value["supporting_evidence"][0]["claim"] = "Shadbala oranları teknik güç tablosunda gösterilir."
        payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
        validated = validate_methodology_response(payload, evidence)
        self.assertEqual(
            validated["supporting_evidence"][0]["evidence_path"],
            "evidence.strength_summary",
        )

    def test_model_request_includes_only_real_canonical_evidence_paths(self):
        candidate = load_methodology_candidates()[0]
        evidence = {
            "topic_packet": {
                "evidence": {
                    "houses": [{"occupants": ["Moon"]}],
                },
            },
        }

        request, _ = _model_request(candidate, evidence)
        prompt = request["contents"][0]["parts"][0]["text"]

        self.assertIn("evidence.topic_packet.evidence.houses.0.occupants", prompt)
        self.assertNotIn('"evidence.topic_packet.houses.0.occupants"', prompt)

    def test_long_time_series_catalog_is_bounded_and_keeps_array_root(self):
        candidate = load_methodology_candidates()[0]
        evidence = {
            "transits": {
                "daily_timing": [
                    {"date": f"2026-08-{(index % 28) + 1:02d}", "value": index}
                    for index in range(92)
                ],
            },
        }

        request, _ = _model_request(candidate, evidence)
        prompt = request["contents"][0]["parts"][0]["text"]

        self.assertIn("evidence.transits.daily_timing", prompt)
        self.assertIn("evidence.transits.daily_timing.0.date", prompt)
        self.assertNotIn("evidence.transits.daily_timing.91.date", prompt)

    def test_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = Path(__file__).resolve().parents[1] / "methodologies"
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
