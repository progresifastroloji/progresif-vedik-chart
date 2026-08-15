import json
import unittest

from question_classifier import (
    QuestionClassificationError,
    build_request,
    classify_question,
    validate_classification,
)


def _classification(**overrides):
    value = {
        "interpreted_question": "Kullanıcı şu anki ruh halinin nedenini soruyor.",
        "primary_topic": "wellbeing",
        "time_scope": "instant",
        "timing_required": True,
        "target_start": None,
        "target_end": None,
        "target_datetime": "now",
        "required_evidence": [
            "natal_core",
            "natal_emotional_core",
            "active_dasha",
            "stored_transit_days",
            "current_transit_snapshot",
            "moon_and_panchanga",
            "transit_natal_contacts",
            "ashtakavarga",
        ],
        "sensitivity": "mental_wellbeing",
        "confidence": "high",
        "clarification_required": False,
        "clarification_question": None,
    }
    value.update(overrides)
    return value


def _model_payload(value):
    return {
        "candidates": [{
            "content": {"parts": [{"text": json.dumps(value, ensure_ascii=False)}]},
        }],
    }


class QuestionClassifierTest(unittest.TestCase):
    def test_instant_wellbeing_contract_is_accepted(self):
        result = validate_classification(_classification())

        self.assertEqual(result["primary_topic"], "wellbeing")
        self.assertEqual(result["time_scope"], "instant")
        self.assertIn("current_transit_snapshot", result["required_evidence"])

    def test_model_cannot_select_user_or_file_identifiers(self):
        for forbidden in ("owner_user_id", "chart_id", "path", "filename"):
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(QuestionClassificationError):
                    validate_classification(_classification(**{forbidden: "secret"}))

    def test_instant_route_requires_all_server_evidence_layers(self):
        value = _classification(required_evidence=["natal_core", "active_dasha"])

        with self.assertRaises(QuestionClassificationError) as raised:
            validate_classification(value)

        self.assertEqual(raised.exception.code, "question_classifier_evidence_invalid")

    def test_classifier_uses_existing_bridge_contract(self):
        calls = []

        def model_call(request_id, request):
            calls.append((request_id, request))
            return request_id, _model_payload(_classification())

        result = classify_question(
            "Tam şu anda neden böyle hissediyorum?",
            "route-test-1",
            model_call,
            "2026-08-15T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "wellbeing")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "route-test-1")
        self.assertEqual(
            calls[0][1]["generationConfig"]["responseMimeType"],
            "application/json",
        )

    def test_classifier_repairs_bounded_evidence_omissions(self):
        def model_call(request_id, _request):
            incomplete = _classification(
                required_evidence=["natal_core", "active_dasha"],
                sensitivity="standard",
            )
            return request_id, _model_payload(incomplete)

        result = classify_question(
            "İyi hissetmiyorum.",
            "route-test-evidence",
            model_call,
            "2026-08-15T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "wellbeing")
        self.assertEqual(result["sensitivity"], "mental_wellbeing")
        self.assertIn("natal_emotional_core", result["required_evidence"])

    def test_explicit_daily_career_context_overrides_model_misroute(self):
        def model_call(request_id, _request):
            wrong = _classification(
                primary_topic="wellbeing",
                time_scope="instant",
                target_start=None,
                target_end=None,
                target_datetime="now",
            )
            return request_id, _model_payload(wrong)

        result = classify_question(
            "Bugün işte neden gerginim?",
            "route-test-daily-career",
            model_call,
            "2026-08-15T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "career")
        self.assertEqual(result["time_scope"], "daily")
        self.assertEqual(result["target_start"], "2026-08-15")
        self.assertEqual(result["target_end"], "2026-08-15")
        self.assertIsNone(result["target_datetime"])

    def test_none_scope_discards_model_supplied_dates(self):
        def model_call(request_id, _request):
            wrong = _classification(
                primary_topic="career",
                time_scope="none",
                timing_required=False,
                target_start="2026-08-15",
                target_end="2026-08-15",
                target_datetime=None,
                required_evidence=["natal_core", "active_dasha"],
                sensitivity="standard",
            )
            return request_id, _model_payload(wrong)

        result = classify_question(
            "İşimde neden mutsuzum?",
            "route-test-no-time",
            model_call,
            "2026-08-15T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "career")
        self.assertEqual(result["time_scope"], "none")
        self.assertIsNone(result["target_start"])
        self.assertIsNone(result["target_end"])

    def test_prompt_explicitly_blocks_hissetmiyorum_career_substring_bug(self):
        request = build_request(
            "İyi hissetmiyorum.",
            "2026-08-15T12:00:00+03:00",
        )
        prompt = request["systemInstruction"]["parts"][0]["text"]

        self.assertIn("'hissetmiyorum' kariyer degildir", prompt)
        self.assertIn("wellbeing", prompt)


if __name__ == "__main__":
    unittest.main()
