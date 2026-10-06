import json
import unittest

from question_classifier import (
    ALLOWED_TOPICS,
    QuestionClassificationError,
    build_request,
    classify_question,
    detect_explicit_topic,
    enforce_explicit_time_scope,
    event_evidence_for_question,
    infer_question_intent,
    normalize_classification,
    route_diagnostics,
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
            "vedic_spine",
            "natal_emotional_core",
            "active_dasha",
            "transits",
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
    def test_explicit_calendar_day_is_preserved_in_all_normalization_paths(self):
        route = _classification(primary_topic="general", time_scope="none", timing_required=False, required_evidence=[])
        for normalize in (normalize_classification, enforce_explicit_time_scope):
            for question, expected in (
                ("06.10.2026 Salı günü için kişiselleştirilmiş derin analiz yapmanı istiyorum.", "2026-10-06"),
                ("07.10.2026 günü kariyerimde neye dikkat edeyim?", "2026-10-07"),
                ("2028-02-29 için günlük yorum istiyorum.", "2028-02-29"),
            ):
                with self.subTest(normalizer=normalize.__name__, question=question):
                    result = normalize(route, question, "2026-10-06T12:00:00+03:00")
                    self.assertEqual(result["time_scope"], "daily")
                    self.assertEqual((result["target_start"], result["target_end"]), (expected, expected))
                    self.assertIn("moon_and_panchanga", result["required_evidence"])
                    self.assertTrue(result["timing_required"])

    def test_calendar_day_does_not_replace_birth_date_or_explicit_range(self):
        route = _classification(primary_topic="general", time_scope="none", timing_required=False, required_evidence=[])
        self.assertEqual(normalize_classification(route, "01.01.2000 günü doğdum, karakterim nasıl?", "2026-10-06T12:00:00+03:00")["time_scope"], "none")
        result = normalize_classification(route, "06.10.2026 için önümüzdeki üç ayı yorumla.", "2026-10-06T12:00:00+03:00")
        self.assertEqual(result["time_scope"], "range")
        self.assertEqual(result["target_end"], "2027-01-05")
        with self.assertRaises(QuestionClassificationError) as caught:
            normalize_classification(route, "31.02.2026 günü için yorum istiyorum.", "2026-10-06T12:00:00+03:00")
        self.assertEqual(caught.exception.code, "question_classifier_explicit_date_invalid")

    def test_question_intent_covers_annual_guidance_current_and_forecast_questions(self):
        cases = {
            "Yıllık Varshaphala haritam bu yılı nasıl anlatıyor?": "annual_analysis",
            "Şu sıralar genel sağlığımda neye dikkat etmeliyim?": "current_state",
            "İlişkilerimde hangi tutuma dikkat etmem iyi olur?": "guidance",
            "Kariyer öngörümde önümüzdeki dönemde ne görünüyor?": "forecast",
            "Partnerimle uyumumuzu nasıl değerlendirebilirim?": "compatibility",
            "Doğum haritamda karakterimin ana teması nedir?": "natal_explanation",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(infer_question_intent(question), expected)

    def test_general_topic_normalization_applies_sensitivity_defaults(self):
        now = "2026-09-30T12:00:00+03:00"
        cases = {
            "Genel sağlık durumum hakkında ne görünüyor?": ("health", "medical"),
            "Maddi durumum ve gelir düzenim nasıl?": ("wealth", "financial"),
            "Hukuki sürecimde hangi göstergeler öne çıkıyor?": ("legal", "legal"),
            "Ruh halim neden bu kadar gergin?": ("wellbeing", "mental_wellbeing"),
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                result = normalize_classification(
                    _classification(
                        primary_topic="general",
                        time_scope="none",
                        timing_required=False,
                        sensitivity="standard",
                        required_evidence=[],
                    ),
                    question,
                    now,
                )
                self.assertEqual(
                    (result["primary_topic"], result["sensitivity"]),
                    expected,
                )

    def test_forecast_intent_requires_range_for_all_life_topics(self):
        result = normalize_classification(
            _classification(
                primary_topic="career",
                time_scope="none",
                timing_required=False,
                required_evidence=[],
            ),
            "Kariyer öngörümde önümüzdeki dönemde hangi fırsatlar öne çıkıyor?",
            "2026-09-30T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "career")
        self.assertEqual(result["time_scope"], "range")
        self.assertTrue(result["timing_required"])
        self.assertEqual(result["target_start"], "2026-09-30")
        self.assertEqual(result["target_end"], "2026-12-30")

    def test_route_diagnostics_reports_missing_route_obligations(self):
        route = _classification(
            primary_topic="health",
            time_scope="none",
            timing_required=False,
            sensitivity="standard",
            required_evidence=["natal_core"],
        )
        diagnostics = route_diagnostics(
            route,
            "Sağlık öngörümde önümüzdeki dönemde neye dikkat etmeliyim?",
            "2026-09-30T12:00:00+03:00",
        )

        self.assertEqual(diagnostics["status"], "repair_required")
        self.assertEqual(diagnostics["question_intent"], "forecast")
        self.assertIn("time_scope", diagnostics["repaired_fields"])
        self.assertIn("sensitivity", diagnostics["repaired_fields"])
        self.assertIn("required_evidence", diagnostics["repaired_fields"])
        self.assertIn("transits", diagnostics["missing_required_evidence"])

    def test_recent_and_current_wellbeing_phrases_require_bounded_timing_context(self):
        now = "2026-09-30T12:00:00+03:00"
        cases = {
            "Son günlerde niye bu kadar isteksizim?": ("range", "2026-09-30", "2026-10-06"),
            "Bu aralar çok isteksizim, neden?": ("range", "2026-09-30", "2026-10-06"),
            "Şu an niye bu kadar huzursuzum?": ("instant", None, None),
            "Bugün neden bu kadar isteksizim?": ("daily", "2026-09-30", "2026-09-30"),
        }
        for question, (scope, start, end) in cases.items():
            with self.subTest(question=question):
                result = normalize_classification(
                    _classification(
                        primary_topic="general",
                        time_scope="none",
                        timing_required=False,
                        required_evidence=[],
                    ),
                    question,
                    now,
                )
                self.assertEqual(result["primary_topic"], "wellbeing")
                self.assertEqual(result["time_scope"], scope)
                self.assertTrue(result["timing_required"])
                self.assertEqual(result["target_start"], start)
                self.assertEqual(result["target_end"], end)

    def test_topic_and_timing_contract_covers_requested_positive_and_negative_questions(self):
        now = "2026-09-30T12:00:00+03:00"
        positive = {
            "Beni genel olarak analiz et. Nasıl biriyim?": ("general", "none"),
            "Şu an yaptığım uygulama işi benim için doğru bir yön mü?": ("career", "instant"),
            "İlişkilerimde neden hep aynı sorunları yaşıyorum?": ("marriage", "none"),
            "Son günlerde ilişkiler konusunda neden bu kadar gerginim?": ("marriage", "range"),
        }
        negative = {
            "Nasıl biriyim?": ("general", "none"),
            "İlişkilerde genel yapım nasıl?": ("marriage", "none"),
            "Kariyer potansiyelim nedir?": ("career", "none"),
        }
        for question, expected in {**positive, **negative}.items():
            with self.subTest(question=question):
                result = normalize_classification(
                    _classification(
                        primary_topic="general",
                        time_scope="none",
                        timing_required=False,
                        required_evidence=[],
                    ),
                    question,
                    now,
                )
                self.assertEqual(
                    (result["primary_topic"], result["time_scope"]),
                    expected,
                )
    def test_api_subject_inventory_is_available_to_the_question_contract(self):
        self.assertEqual(
            ALLOWED_TOPICS,
            {
                "general", "character", "career", "marriage", "wealth",
                "health", "family", "education", "relocation", "legal",
                "spiritual", "wellbeing", "varshaphala",
            },
        )

    def test_current_question_detects_every_api_subject_without_raw_substrings(self):
        cases = {
            "Karakterimde öne çıkan güçlü yön nedir?": "character",
            "Kariyerimde hangi becerimi geliştirmeliyim?": "career",
            "Evlilik konusunda sınırlarımı nasıl kurarım?": "marriage",
            "Maddi güven ve birikim düzenimi nasıl ele almalıyım?": "wealth",
            "Sağlık ve enerji düzenimde neye dikkat etmeliyim?": "health",
            "Aile içinde sorumlulukları nasıl dengelemeliyim?": "family",
            "Eğitim ve uzmanlaşma yönüm nasıl görünüyor?": "education",
            "Öğrenme ve kişisel gelişimimde bu dönemi daha verimli kullanmak için nelere odaklanabilirim?": "education",
            "Yurtdışına taşınma kararını nasıl değerlendirmeliyim?": "relocation",
            "Hukuki sözleşme sürecinde neye dikkat etmeliyim?": "legal",
            "Ruhsal yönüm ve yaşam amacım hakkında ne görünüyor?": "spiritual",
            "Neden gergin ve mutsuz hissediyorum?": "wellbeing",
            "Yıllık haritam hangi alanları öne çıkarıyor?": "varshaphala",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(detect_explicit_topic(question), expected)

        self.assertEqual(
            detect_explicit_topic("Aile ve kariyer alanlarını birlikte değerlendir."),
            "general",
        )
        self.assertIsNone(detect_explicit_topic("Bu konuda ne görüyorsun?"))
        self.assertEqual(detect_explicit_topic("İyi hissetmiyorum."), "wellbeing")
        self.assertEqual(detect_explicit_topic("İşe girmek için uygun dönem var mı?"), "career")
        self.assertEqual(detect_explicit_topic("Yeni işe başlamak doğru mu?"), "career")
        self.assertEqual(
            detect_explicit_topic(
                "Mesleki yeteneklerim neler ve hangi meslekler bana uygun?"
            ),
            "career",
        )
        self.assertEqual(
            detect_explicit_topic(
                "When evaluating a new career opportunity, which indicators should I consider?"
            ),
            "career",
        )

    def test_healthy_relationship_language_is_not_routed_to_health(self):
        question = (
            "İlişkilerimde tekrar eden örüntü nedir ve bunu daha sağlıklı "
            "yönetmek için ne yapabilirim?"
        )

        self.assertEqual(detect_explicit_topic(question), "marriage")

    def test_explicit_six_month_request_keeps_the_full_requested_horizon(self):
        result = enforce_explicit_time_scope(
            _classification(
                primary_topic="career",
                time_scope="range",
                target_start="2026-09-25",
                target_end=None,
            ),
            "Önümüzdeki altı ayda kariyerime ne zaman odaklanmalıyım?",
            "2026-09-25T12:00:00+03:00",
        )

        self.assertEqual(result["target_start"], "2026-09-25")
        self.assertEqual(result["target_end"], "2027-03-24")

    def test_eclipse_question_forces_stored_event_layers_without_calculation(self):
        def model_call(request_id, _request):
            return request_id, _model_payload(_classification(
                primary_topic="general",
                time_scope="none",
                timing_required=False,
                target_start=None,
                target_end=None,
                target_datetime=None,
                required_evidence=["natal_core", "vedic_spine", "active_dasha", "transits"],
                sensitivity="standard",
            ))

        result = classify_question(
            "Ay tutulması beni nasıl etkileyebilir?",
            "route-test-eclipse",
            model_call,
            "2026-08-21T12:00:00+03:00",
        )

        self.assertEqual(result["time_scope"], "range")
        self.assertEqual(result["target_start"], "2026-08-21")
        self.assertEqual(result["target_end"], "2026-11-20")
        self.assertTrue({"eclipse_events", "eclipse_nakshatra", "eclipse_pada"}.issubset(
            set(result["required_evidence"])
        ))

    def test_rahu_ketu_event_requests_stored_natal_contact_layer(self):
        evidence = event_evidence_for_question(
            "Transit Rahu doğum haritamdaki Ketu ile kavuşuyor mu?"
        )
        self.assertIn("important_sky_events", evidence)
        self.assertIn("sky_event_natal_contacts", evidence)
        self.assertNotIn("eclipse_nakshatra", evidence)

    def test_natal_rahu_question_is_not_misclassified_as_sky_event(self):
        self.assertFalse(event_evidence_for_question("Rahu doğum haritamda ne anlatır?"))
        self.assertFalse(event_evidence_for_question("Rahu beni nasıl etkiliyor?"))

    def test_instant_wellbeing_contract_is_accepted(self):
        result = validate_classification(_classification())

        self.assertEqual(result["primary_topic"], "wellbeing")
        self.assertEqual(result["time_scope"], "instant")
        self.assertIn("current_transit_snapshot", result["required_evidence"])
        self.assertTrue({"vedic_spine", "transits"}.issubset(set(result["required_evidence"])))

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
        generation_config = calls[0][1]["generationConfig"]
        self.assertNotIn("temperature", generation_config)
        self.assertEqual(
            generation_config["thinkingConfig"]["thinkingLevel"],
            "LOW",
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
        self.assertEqual(result["time_scope"], "instant")
        self.assertEqual(result["sensitivity"], "mental_wellbeing")
        self.assertIn("natal_emotional_core", result["required_evidence"])
        self.assertIn("current_transit_snapshot", result["required_evidence"])

    def test_present_state_anger_uses_current_sky_without_explicit_now(self):
        def model_call(request_id, _request):
            incomplete = _classification(
                primary_topic="general",
                time_scope="none",
                timing_required=False,
                target_start=None,
                target_end=None,
                target_datetime=None,
                required_evidence=["natal_core", "vedic_spine", "active_dasha", "transits"],
                sensitivity="standard",
            )
            return request_id, _model_payload(incomplete)

        result = classify_question(
            "Neden sinirliyim?",
            "route-test-present-anger",
            model_call,
            "2026-08-27T12:00:00+03:00",
        )

        self.assertEqual(result["primary_topic"], "wellbeing")
        self.assertEqual(result["time_scope"], "instant")
        self.assertEqual(result["target_datetime"], "2026-08-27T12:00:00+03:00")
        self.assertTrue({
            "moon_and_panchanga",
            "current_transit_snapshot",
            "stored_transit_days",
            "transit_natal_contacts",
            "ashtakavarga",
        }.issubset(set(result["required_evidence"])))

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
                required_evidence=["natal_core", "vedic_spine", "active_dasha", "transits"],
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
