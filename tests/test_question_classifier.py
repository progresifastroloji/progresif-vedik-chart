import json
import unittest

from question_classifier import (
    QuestionClassificationError,
    build_request,
    classify_question,
    enforce_explicit_time_scope,
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
        self.assertEqual(result["time_scope"], "none")
        self.assertEqual(result["sensitivity"], "mental_wellbeing")
        self.assertIn("natal_emotional_core", result["required_evidence"])

    def test_classifier_can_bypass_server_topic_and_time_overrides(self):
        def model_call(request_id, _request):
            model_decision = _classification(
                interpreted_question="Kullanıcı arkadaşlıkta barışma olasılığını soruyor.",
                primary_topic="general",
                time_scope="none",
                timing_required=False,
                target_start=None,
                target_end=None,
                target_datetime=None,
                required_evidence=["natal_core", "active_dasha"],
                sensitivity="standard",
            )
            return request_id, _model_payload(model_decision)

        result = classify_question(
            "Arkadaşımla küstüm, barışır mıyım?",
            "route-test-gemini-only",
            model_call,
            "2026-08-16T12:00:00+03:00",
            apply_server_normalization=False,
        )

        self.assertEqual(result["primary_topic"], "general")
        self.assertEqual(result["time_scope"], "none")

    def test_gemini_only_repairs_explicit_weekly_scope_before_validation(self):
        def model_call(request_id, _request):
            incomplete = _classification(
                primary_topic="career",
                time_scope="none",
                timing_required=False,
                target_start=None,
                target_end=None,
                target_datetime=None,
                required_evidence=["natal_core", "active_dasha"],
                sensitivity="standard",
            )
            return request_id, _model_payload(incomplete)

        result = classify_question(
            "Önümüzdeki haftanın olay konuları gün gün yorum istiyorum",
            "route-test-gemini-only-weekly",
            model_call,
            "2026-08-19T12:00:00+03:00",
            apply_server_normalization=False,
        )

        self.assertEqual(result["primary_topic"], "career")
        self.assertEqual(result["time_scope"], "range")
        self.assertEqual(result["target_start"], "2026-08-24")
        self.assertEqual(result["target_end"], "2026-08-30")
        self.assertIn("stored_transit_days", result["required_evidence"])

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

    def test_explicit_next_week_preserves_topic_but_forces_weekly_range(self):
        model_value = _classification(
            primary_topic="career",
            time_scope="none",
            timing_required=False,
            target_datetime=None,
            required_evidence=["natal_core", "active_dasha"],
            sensitivity="standard",
        )

        result = enforce_explicit_time_scope(
            model_value,
            "Önümüzdeki haftanın olay konuları gün gün yorum istiyorum",
            "2026-08-19T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "career")
        self.assertEqual(result["time_scope"], "range")
        self.assertTrue(result["timing_required"])
        self.assertEqual(result["target_start"], "2026-08-24")
        self.assertEqual(result["target_end"], "2026-08-30")
        self.assertIn("stored_transit_days", result["required_evidence"])

    def test_future_marriage_question_uses_current_transit_horizon(self):
        def model_call(request_id, _request):
            incomplete = _classification(
                primary_topic="general",
                time_scope="none",
                timing_required=False,
                target_start=None,
                target_end=None,
                target_datetime=None,
                required_evidence=["natal_core", "active_dasha"],
                sensitivity="standard",
            )
            return request_id, _model_payload(incomplete)

        result = classify_question(
            "Çıktığım adamla evlenebilir miyim?",
            "route-test-future-marriage",
            model_call,
            "2026-08-15T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "marriage")
        self.assertEqual(result["time_scope"], "range")
        self.assertEqual(result["target_start"], "2026-08-15")
        self.assertEqual(result["target_end"], "2026-11-14")
        self.assertIn("stored_transit_days", result["required_evidence"])

    def test_prompt_explicitly_blocks_hissetmiyorum_career_substring_bug(self):
        request = build_request(
            "İyi hissetmiyorum.",
            "2026-08-15T12:00:00+03:00",
        )
        prompt = request["systemInstruction"]["parts"][0]["text"]

        self.assertIn("'hissetmiyorum' kariyer degildir", prompt)
        self.assertIn("wellbeing", prompt)

    def test_classifier_receives_the_full_active_conversation(self):
        context = [
            {
                "question": "Yarınki iş görüşmesinden nasıl bir yanıt alırım?",
                "answer": "Görüşme 17 Ağustos için değerlendirildi.",
            },
            {
                "question": "Ay etkisini de açıklar mısın?",
                "answer": "Ay etkisi ayrıca açıklandı.",
            },
        ]
        request = build_request(
            "Diğer transitlerle beraber yorum yap.",
            "2026-08-16T12:00:00+03:00",
            context,
        )
        payload = json.loads(request["contents"][0]["parts"][0]["text"])

        self.assertEqual(payload["active_conversation"], context)
        self.assertEqual(
            payload["current_question"],
            "Diğer transitlerle beraber yorum yap.",
        )
        self.assertIn("aynı açık sohbetin bağlamıdır", request["systemInstruction"]["parts"][0]["text"])


if __name__ == "__main__":
    unittest.main()
