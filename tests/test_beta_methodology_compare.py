import json
import os
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from app import (
    PWA_NATAL_TOPIC_SECTION_IDS,
    TOPIC_PACKET_CONFIG,
    app,
    _beta_build_chat_draft,
    _beta_build_chart,
    _beta_db,
    _beta_detect_subject_topic,
    _beta_detect_topic,
    _beta_question_route,
    _beta_topic_packet,
    _beta_shadbala_strength_summary,
    _beta_json,
    _beta_load_json,
    _beta_now,
    _beta_options,
    _beta_public_methodology_response,
    _build_transit_pack_markdown,
    _beta_compact_transit_evidence,
    _normalize_important_sky_events,
)
from methodology_orchestrator import (
    MAX_PROMPT_BYTES,
    MethodologyOrchestrationError,
    _canonical_json,
    _model_request,
    compact_evidence,
    load_methodology_candidates,
)
from question_classifier import QuestionClassificationError


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
                "vedic_spine",
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


def _narrative_payload():
    opening_summary = (
        "Kariyeriniz, tek bir uzmanlık alanında derinleştiğinizde daha sağlam biçimde gelişebilir. "
        "En güçlü yanınız, karmaşık sorumlulukları düzenli ve güvenilir bir sonuca dönüştürmenizdir. "
        "İlerlemenizi hızlandıracak seçim, gereksiz yükleri azaltıp emeğinizi görünür kılmaktır."
    )
    answer = (
        "Kariyer alanında ilerleme potansiyeliniz var; bu potansiyel en iyi, dağılmadan belirli bir "
        "uzmanlık alanına odaklandığınızda çalışıyor. Haritanın ana cevabı hızlı sonuçtan çok güvenilir "
        "ve kalıcı bir mesleki yapı kurmaya yatkın olduğunuz yönündedir.\n\n"
        "Teknik değerlendirme destekleyici göstergelerle birlikte zorlayıcı koşulları da hesaba katıyor. "
        "Bu yüzden güçlü yanınız olan sorumluluk alma becerisi, sınırlarınız net olmadığında fazla yük "
        "üstlenmeye dönüşebilir. Öncelikleri sadeleştirmeniz, emeğinizin karşılığını daha görünür kılar.\n\n"
        "Pratik olarak tek bir ana hedef seçin, onu haftalık adımlara bölün ve tamamladığınız işleri düzenli "
        "olarak görünür hale getirin. Astrolojik göstergeler sonucu garanti etmez; fakat disiplin, doğru "
        "zamanlama ve seçici sorumluluk aldığınızda ilerleme alanınızın güçlendiğini gösterir. Bu yaklaşım "
        "hem mesleki güveninizi hem de dışarıdan algılanan yetkinliğinizi besleyebilir."
    )
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps({
            "opening_summary": opening_summary,
            "answer": answer,
        })}]}}],
        "usageMetadata": {"totalTokenCount": 321},
        "modelVersion": "test-model",
    }


def _analysis_or_narrative_payload(request_id):
    return _narrative_payload() if "-narrative" in request_id else _model_payload()


def _route_payload(topic, time_scope, *, sensitivity="standard"):
    required = ["natal_core", "vedic_spine", "active_dasha", "transits"]
    if topic == "wellbeing":
        required.append("natal_emotional_core")
    if time_scope != "none":
        required.extend([
            "stored_transit_days",
            "transit_natal_contacts",
            "ashtakavarga",
        ])
    if time_scope in {"daily", "instant"}:
        required.append("moon_and_panchanga")
    if time_scope == "instant":
        required.append("current_transit_snapshot")
    value = {
        "interpreted_question": "Soru doğru konu ve zaman kapsamıyla anlaşıldı.",
        "primary_topic": topic,
        "time_scope": time_scope,
        "timing_required": time_scope != "none",
        "target_start": "2026-08-15" if time_scope in {"daily", "range"} else None,
        "target_end": "2026-11-14" if time_scope == "range" else None,
        "target_datetime": "now" if time_scope == "instant" else None,
        "required_evidence": required,
        "sensitivity": sensitivity,
        "confidence": "high",
        "clarification_required": False,
        "clarification_question": None,
    }
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(value)}]}}],
    }


class BetaMethodologyCompareEndpointTest(unittest.TestCase):
    def test_public_evidence_drawer_keeps_all_path_free_support_and_counter_claims(self):
        comparison = {
            "methodology_results": [{
                "analysis": {
                    "supporting_evidence": [
                        {"claim": f"Destek {index}", "evidence_path": f"evidence.support.{index}"}
                        for index in range(1, 5)
                    ],
                    "challenging_evidence": [
                        {"claim": "Karşıt 1", "evidence_path": "evidence.counter.1"},
                        {"claim": "Karşıt 2", "evidence_path": "evidence.counter.2"},
                    ],
                    "missing_layers": [],
                    "limitations": [],
                },
            }],
        }

        public = _beta_public_methodology_response(comparison)
        analysis = public["methodology_results"][0]["analysis"]

        self.assertEqual(analysis["display_evidence"], ["Destek 1", "Destek 2", "Destek 3", "Destek 4"])
        self.assertEqual(analysis["display_counter_evidence"], ["Karşıt 1", "Karşıt 2"])
        self.assertNotIn("supporting_evidence", analysis)
        self.assertNotIn("challenging_evidence", analysis)
        self.assertNotIn("evidence.support.1", json.dumps(public))

    def test_source_only_eclipse_is_preserved_in_runtime_and_markdown(self):
        event = {
            "event_type": "lunar_eclipse",
            "label": "Ay tutulması",
            "date": "2026-08-28",
            "local_datetime": "2026-08-28T04:12:00+03:00",
            "utc_datetime": "2026-08-28T01:12:00Z",
            "timezone_id": "Europe/Istanbul",
            "sign_tr": "Kova",
            "degree": "4°12'",
            "nakshatra": "Dhanishta",
            "pada": 3,
            "natal_contacts": [{
                "transit_planet": "Moon",
                "natal_planet": "Ketu",
                "contact_type": "degree_orb",
                "orb": 1.2,
            }],
        }
        pack = {
            "period": {"type": "range", "range_start": "2026-08-28", "range_end": "2026-08-28", "day_count": 1, "important_sky_event_status": "available", "important_sky_event_count": 1},
            "meta": {"api_version": "v2", "engine_version": "test"},
            "person": {"name": "Test", "group": "PWA"},
            "natal": {"lagna_sign": "Oğlak", "moon_sign": "Oğlak"},
            "important_sky_events": [event],
            "days": [{"date": "2026-08-28", "important_sky_events": [event]}],
        }
        compact = _beta_compact_transit_evidence(pack)
        markdown = _build_transit_pack_markdown(pack)
        self.assertEqual(compact["event_data_status"], "available")
        self.assertEqual(compact["important_sky_events"][0]["nakshatra"], "Dhanishta")
        self.assertEqual(compact["important_sky_events"][0]["pada"], 3)
        self.assertIn("Önemli Gökyüzü Olayları", markdown)
        self.assertIn("Dhanishta", markdown)
        self.assertIn("Hesaplanmadı", _build_transit_pack_markdown({"period": {}, "person": {}, "meta": {}, "natal": {}, "days": []}))

    def test_event_normalizer_rejects_missing_source_date_and_keeps_pada(self):
        with self.assertRaises(ValueError):
            _normalize_important_sky_events([{"event_type": "lunar_eclipse"}])
        normalized = _normalize_important_sky_events([{
            "type": "Ay tutulması",
            "date": "2026-08-28",
            "event_nakshatra": "Dhanishta",
            "event_nakshatra_pada": 3,
        }])
        self.assertEqual(normalized[0]["event_type"], "lunar_eclipse")
        self.assertEqual(normalized[0]["nakshatra"], "Dhanishta")
        self.assertEqual(normalized[0]["pada"], 3)

    @patch("app._pwa_full_markdown_documents")
    def test_ordered_full_mode_loads_transit_for_non_timing_question(self, full_documents):
        full_documents.return_value = {
            "documents": [
                {
                    "filename": "natal-interpretation.md",
                    "byte_size": 12,
                    "sha256": "natal-sha",
                    "content": "# Natal\n",
                },
                {
                    "filename": "transit-three-month.md",
                    "byte_size": 15,
                    "sha256": "transit-sha",
                    "content": "# Transit\n",
                },
            ],
        }
        chart = {
            "birth": {"person": {"name": "Test"}},
            "lagna": {"sign": "Aries"},
            "dashas": {"vimshottari": {"current_active": {"path": ["Saturn"]}}},
            "topic_packets": {
                "career": {
                    "confidence": "medium",
                    "missing_factors": [],
                    "required_but_missing": [],
                    "evidence": {},
                },
            },
            "data_quality": {"status": "complete"},
        }
        with patch.dict(os.environ, {"VEDIC_GEMINI_MARKDOWN_MODE": "ordered_full"}, clear=True):
            draft = _beta_build_chat_draft(
                "Kariyerimde güçlü yönlerim neler?",
                chart,
                routing={
                    "selected": {
                        "contract_version": "test-route-v1",
                        "primary_topic": "career",
                        "time_scope": "none",
                        "timing_required": False,
                        "required_evidence": ["natal_core"],
                    },
                },
                owner_user_id="11111111-1111-4111-8111-111111111111",
                profile_id=PROFILE_ID,
                chart_id=CHART_ID,
                include_full_markdown_sources=True,
            )

        full_documents.assert_called_once_with(
            "11111111-1111-4111-8111-111111111111",
            CHART_ID,
            include_transit=True,
        )
        self.assertEqual(
            draft["context_trace"]["full_markdown_test"]["document_order"],
            ["natal-interpretation.md", "transit-three-month.md"],
        )

    @patch("app._pwa_full_markdown_test_document")
    def test_full_markdown_test_document_is_internal_to_compare_draft(self, full_document):
        full_document.return_value = {
            "filename": "natal-interpretation.md",
            "byte_size": 28,
            "sha256": "full-md-test-sha",
            "content": "# Tam natal test dosyası\n",
        }
        chart = {
            "birth": {"person": {"name": "Test"}},
            "lagna": {"sign": "Aries"},
            "dashas": {"vimshottari": {"current_active": {"path": ["Saturn"]}}},
            "topic_packets": {"career": {"confidence": "medium", "missing_factors": [], "required_but_missing": [], "evidence": {}}},
            "data_quality": {"status": "complete"},
        }
        with patch.dict(os.environ, {"VEDIC_GEMINI_FULL_MARKDOWN_TEST": "1"}, clear=False):
            draft = _beta_build_chat_draft(
                "Kariyerimde güçlü yönlerim neler?",
                chart,
                routing={
                    "selected": {
                        "contract_version": "test-route-v1",
                        "primary_topic": "career",
                        "time_scope": "none",
                        "timing_required": False,
                        "required_evidence": ["natal_core"],
                    },
                },
                owner_user_id="11111111-1111-4111-8111-111111111111",
                profile_id=PROFILE_ID,
                chart_id=CHART_ID,
                include_full_markdown_test=True,
            )

        self.assertIn("_full_markdown_test", draft)
        self.assertEqual(
            draft["context_trace"]["full_markdown_test"]["filename"],
            "natal-interpretation.md",
        )
        self.assertEqual(
            draft["context_trace"]["full_markdown_test"]["documents"][0]["filename"],
            "natal-interpretation.md",
        )
        # The route that returns/persists a normal draft does not set the
        # internal flag, so full content cannot leak into chat history.
        normal_draft = _beta_build_chat_draft(
            "Kariyerimde güçlü yönlerim neler?",
            chart,
            routing={
                "selected": {
                    "contract_version": "test-route-v1",
                    "primary_topic": "career",
                    "time_scope": "none",
                    "timing_required": False,
                    "required_evidence": ["natal_core"],
                },
            },
        )
        self.assertNotIn("_full_markdown_test", normal_draft)

    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_heavy_limit = app.config["BETA_DAILY_HEAVY_LIMIT"]
        self._old_router_mode = app.config["QUESTION_ROUTER_MODE"]
        self._old_router_users = app.config["QUESTION_ROUTER_ACTIVE_USER_IDS"]
        self._tmp = tempfile.TemporaryDirectory()
        app.config["BETA_DB_PATH"] = f"{self._tmp.name}/beta.sqlite3"
        app.config["BETA_DAILY_HEAVY_LIMIT"] = 3
        app.config["QUESTION_ROUTER_MODE"] = "off"
        app.config["QUESTION_ROUTER_ACTIVE_USER_IDS"] = set()
        self.client = app.test_client()
        chart = _beta_build_chart(
            {"id": PROFILE_ID, "name": "Test"},
            {
                "year": 2000,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "second": 0,
                "lat": 41.0082,
                "lon": 28.9784,
                "timezone_id": "Europe/Istanbul",
            },
            _beta_options({}),
        )
        with closing(_beta_db()) as conn:
            conn.execute(
                "INSERT INTO beta_charts (id, profile_id, chart_json, created_at) VALUES (?, ?, ?, ?)",
                (CHART_ID, PROFILE_ID, _beta_json(chart), _beta_now()),
            )
            conn.commit()

    def tearDown(self):
        app.config["BETA_DB_PATH"] = self._old_beta_db_path
        app.config["BETA_DAILY_HEAVY_LIMIT"] = self._old_heavy_limit
        app.config["QUESTION_ROUTER_MODE"] = self._old_router_mode
        app.config["QUESTION_ROUTER_ACTIVE_USER_IDS"] = self._old_router_users
        self._tmp.cleanup()

    def test_strict_chat_rebuilds_missing_spine_and_includes_transits_for_general(self):
        chart = _beta_build_chart(
            {"id": PROFILE_ID, "name": "Test"},
            {
                "year": 2000,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "second": 0,
                "lat": 41.0082,
                "lon": 28.9784,
                "timezone_id": "Europe/Istanbul",
            },
            _beta_options({}),
        )
        chart.pop("vedic_spine", None)
        question = "Genel haritam hakkında ne görüyorsun?"
        routing = _beta_question_route(question, chart, "general-mandatory-evidence", mode_override="bypass")

        draft = _beta_build_chat_draft(
            question,
            chart,
            routing=routing,
            require_mandatory_evidence=True,
        )
        evidence = compact_evidence(draft)

        self.assertEqual(draft["topic"], "general")
        self.assertTrue(evidence["vedic_spine"]["anchors"])
        self.assertEqual(evidence["vedic_spine"]["status"], "available")
        self.assertEqual(evidence["active_dasha"]["status"], "available")
        self.assertTrue(evidence["transits"]["contract_version"].startswith("vedic-compact-transit-evidence"))

    def test_strict_chat_stops_when_spine_refresh_inputs_are_invalid(self):
        chart = _beta_build_chart(
            {"id": PROFILE_ID, "name": "Test"},
            {
                "year": 2000,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "second": 0,
                "lat": 41.0082,
                "lon": 28.9784,
                "timezone_id": "Europe/Istanbul",
            },
            _beta_options({}),
        )
        chart["birth"]["date"] = "not-a-date"

        with self.assertRaises(MethodologyOrchestrationError) as raised:
            _beta_build_chat_draft(
                "Genel haritam hakkında ne görüyorsun?",
                chart,
                routing={"selected": _beta_question_route(
                    "Genel haritam hakkında ne görüyorsun?",
                    chart,
                    "general-invalid-birth",
                    mode_override="bypass",
                )["selected"]},
                require_mandatory_evidence=True,
            )

        self.assertEqual(raised.exception.code, "vedic_spine_refresh_required")

    @patch("app.call_vertex_bridge")
    def test_endpoint_runs_three_candidates_and_replays_idempotently(self, bridge_call):
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            _analysis_or_narrative_payload(request_id),
        )
        payload = {
            "comparison_id": "methodology-compare-endpoint-1",
            "profile_id": PROFILE_ID,
            "chart_id": CHART_ID,
            "question": "Kariyer açısından güçlü ve zorlayıcı teknik kanıtlar nelerdir?",
            "conversation_context": [
                {
                    "question": "Yarınki iş görüşmem nasıl geçer?",
                    "answer": "Görüşme 17 Ağustos için değerlendirildi.",
                },
                {
                    "question": "Ay etkisini de açıklar mısın?",
                    "answer": "Ay etkisi ayrıca açıklandı.",
                },
            ],
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
        self.assertEqual(data["context_trace"]["primary_topic"], "career")
        self.assertEqual(data["context_trace"]["time_scope"], "none")
        self.assertEqual(data["context_trace"]["conversation_turn_count"], 2)
        self.assertIsNotNone(data["context_trace"]["transit"])
        self.assertEqual(data["context_trace"]["transit"]["range_start"], "2026-09-02")
        self.assertEqual(data["context_trace"]["transit"]["range_end"], "2026-12-02")
        public_analysis = data["methodology_results"][0]["analysis"]
        self.assertEqual(public_analysis["opening_summary"], (
            "Kariyeriniz, tek bir uzmanlık alanında derinleştiğinizde daha sağlam biçimde gelişebilir. "
            "En güçlü yanınız, karmaşık sorumlulukları düzenli ve güvenilir bir sonuca dönüştürmenizdir. "
            "İlerlemenizi hızlandıracak seçim, gereksiz yükleri azaltıp emeğinizi görünür kılmaktır."
        ))
        self.assertEqual(public_analysis["display_evidence"], ["Destekleyici faktör var"])
        self.assertEqual(public_analysis["display_counter_evidence"], ["Zorlayıcı faktör var"])
        self.assertNotIn("supporting_evidence", public_analysis)
        self.assertNotIn("challenging_evidence", public_analysis)
        self.assertNotIn("methodology_coverage", public_analysis)
        self.assertNotIn("technical_summary", public_analysis)
        self.assertFalse(data["replayed"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["context_trace"], data["context_trace"])
        self.assertEqual(replay["usage"]["heavy"]["used"], 1)
        self.assertEqual(bridge_call.call_count, 2)
        technical_prompt = bridge_call.call_args_list[0].args[1]["contents"][0]["parts"][0]["text"]
        narrative_prompt = bridge_call.call_args_list[1].args[1]["contents"][0]["parts"][0]["text"]
        self.assertIn("Yarınki iş görüşmem nasıl geçer?", technical_prompt)
        self.assertIn("Ay etkisini de açıklar mısın?", narrative_prompt)
        with closing(_beta_db()) as conn:
            stored = _beta_load_json(conn.execute(
                "SELECT response_json FROM beta_methodology_comparisons WHERE id = ?",
                (payload["comparison_id"],),
            ).fetchone()["response_json"])
        stored_analysis = stored["methodology_results"][0]["analysis"]
        self.assertIn("challenging_evidence", stored_analysis)
        self.assertIn("methodology_coverage", stored_analysis)
        self.assertIn("technical_summary", stored_analysis)
        usage = self.client.get(f"/api/v2/beta/usage?profile_id={PROFILE_ID}").get_json()
        self.assertEqual(usage["counts"]["methodology_comparisons"], 1)

    @patch("app.call_vertex_bridge")
    def test_endpoint_rejects_comparison_id_collision(self, bridge_call):
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            _analysis_or_narrative_payload(request_id),
        )
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
        self.assertEqual(bridge_call.call_count, 2)

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

    @patch("app.call_vertex_bridge")
    def test_endpoint_exposes_single_methodology_failure_code(self, bridge_call):
        bridge_call.return_value = ("invalid-response", {"candidates": []})

        response = self.client.post(
            "/api/v2/beta/chat/compare",
            json={
                "comparison_id": "methodology-compare-endpoint-failure-code",
                "profile_id": PROFILE_ID,
                "chart_id": CHART_ID,
                "question": "Kariyer kanıtları nelerdir?",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.get_json()["error_code"],
            "methodology_model_response_invalid",
        )

    def test_three_month_career_question_uses_transit_with_career_subject(self):
        question = "Önümüzdeki üç ay kariyerimde hangi dönemler öne çıkıyor?"

        self.assertEqual(_beta_detect_topic(question), "transit")
        self.assertEqual(_beta_detect_subject_topic(question), "career")

    def test_future_specific_marriage_question_uses_transit_with_marriage_subject(self):
        question = "Çıktığım adamla evlenebilir miyim?"

        self.assertEqual(_beta_detect_topic(question), "transit")
        self.assertEqual(_beta_detect_subject_topic(question), "marriage")

    def test_marriage_context_includes_required_planets_lordships_and_networks(self):
        marriage = TOPIC_PACKET_CONFIG["marriage"]

        self.assertEqual(marriage["lordships"], ["7", "2"])
        self.assertTrue({"Venus", "Jupiter", "Moon", "Mars", "Sun"}.issubset(
            marriage["planets"]
        ))
        self.assertTrue({"doshas", "house_drishti", "planet_role_blocks"}.issubset(
            PWA_NATAL_TOPIC_SECTION_IDS["marriage"]
        ))

    @patch("app.call_vertex_bridge")
    def test_controlled_nine_question_shadow_comparison(self, bridge_call):
        cases = [
            ("İyi hissetmiyorum.", "wellbeing", "instant", "mental_wellbeing"),
            ("Neden sinirliyim?", "wellbeing", "instant", "mental_wellbeing"),
            ("Tam şu anda neden böyle hissediyorum?", "wellbeing", "instant", "mental_wellbeing"),
            ("Bugün kendimi neden gergin hissediyorum?", "wellbeing", "daily", "mental_wellbeing"),
            ("İşimde neden mutsuzum?", "career", "none", "standard"),
            ("Bugün işte neden gerginim?", "career", "daily", "standard"),
            ("Kariyerimde güçlü tarafım nedir?", "career", "none", "standard"),
            ("Önümüzdeki üç ay kariyerimde ne olur?", "career", "range", "standard"),
            ("Bugün sevgilimle neden gerginiz?", "marriage", "daily", "standard"),
        ]
        payloads = [_route_payload(topic, scope, sensitivity=sensitivity) for _, topic, scope, sensitivity in cases]
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            payloads.pop(0),
        )

        response = self.client.post(
            "/api/v2/beta/question-route/diagnostic",
            json={"questions": [question for question, *_ in cases]},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "shadow")
        self.assertEqual(data["count"], 9)
        for result, (_, topic, scope, sensitivity) in zip(data["results"], cases):
            self.assertEqual(result["model"]["primary_topic"], topic)
            self.assertEqual(result["model"]["time_scope"], scope)
            self.assertEqual(result["model"]["sensitivity"], sensitivity)
            self.assertEqual(result["selected"], result["legacy"])
        self.assertEqual(data["results"][0]["legacy"]["primary_topic"], "wellbeing")
        self.assertEqual(data["results"][0]["model"]["primary_topic"], "wellbeing")

        with closing(_beta_db()) as conn:
            stored = conn.execute(
                "SELECT COUNT(*) FROM beta_question_routes WHERE chart_id = ?",
                ("question-router-diagnostic",),
            ).fetchone()[0]
        self.assertEqual(stored, 9)

    @patch("app.call_vertex_bridge")
    def test_active_router_agrees_that_hissetmiyorum_is_not_career(self, bridge_call):
        app.config["QUESTION_ROUTER_MODE"] = "active"
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            _route_payload("wellbeing", "instant", sensitivity="mental_wellbeing"),
        )

        routing = _beta_question_route(
            "Tam şu anda neden böyle hissediyorum?",
            {"birth": {"timezone_id": "Europe/Istanbul"}},
            "active-route-test",
        )

        self.assertEqual(routing["legacy"]["primary_topic"], "wellbeing")
        self.assertEqual(routing["selected"]["primary_topic"], "wellbeing")
        self.assertEqual(routing["selected"]["time_scope"], "instant")
        self.assertNotIn("path", routing["selected"])

    @patch("app.call_vertex_bridge")
    def test_gemini_only_router_bypasses_keyword_and_server_overrides(self, bridge_call):
        app.config["QUESTION_ROUTER_MODE"] = "gemini_only"
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            _route_payload("general", "none"),
        )

        routing = _beta_question_route(
            "Kariyerimde neden mutsuzum?",
            {"birth": {"timezone_id": "Europe/Istanbul"}},
            "gemini-only-route-test",
        )

        self.assertEqual(routing["mode"], "gemini_only")
        self.assertEqual(routing["legacy"]["primary_topic"], "career")
        self.assertEqual(routing["selected"]["primary_topic"], "general")
        self.assertEqual(routing["status"], "model_selected")

    @patch("app._beta_question_now", return_value="2026-08-19T12:00:00+03:00")
    @patch("app.call_vertex_bridge")
    def test_gemini_only_router_keeps_topic_but_enforces_explicit_week(self, bridge_call, _now):
        app.config["QUESTION_ROUTER_MODE"] = "gemini_only"
        bridge_call.side_effect = lambda request_id, _request: (
            request_id,
            _route_payload("career", "none"),
        )

        routing = _beta_question_route(
            "Önümüzdeki haftanın olay konuları gün gün yorum istiyorum",
            {"birth": {"timezone_id": "Europe/Istanbul"}},
            "gemini-only-weekly-route-test",
        )

        selected = routing["selected"]
        self.assertEqual(selected["primary_topic"], "career")
        self.assertEqual(selected["time_scope"], "range")
        self.assertTrue(selected["timing_required"])
        self.assertEqual(selected["target_start"], "2026-08-24")
        self.assertEqual(selected["target_end"], "2026-08-30")
        self.assertIn("stored_transit_days", selected["required_evidence"])

    @patch("app.call_vertex_bridge")
    def test_gemini_only_router_never_silently_falls_back(self, bridge_call):
        app.config["QUESTION_ROUTER_MODE"] = "gemini_only"
        bridge_call.side_effect = RuntimeError("bridge unavailable")

        with self.assertRaises(QuestionClassificationError):
            _beta_question_route(
                "İyi hissetmiyorum.",
                {"birth": {"timezone_id": "Europe/Istanbul"}},
                "gemini-only-failure-test",
            )

    def test_bypass_router_preserves_three_month_transit_scope(self):
        routing = _beta_question_route(
            "Önümüzdeki 3 aylık süreçte beni neler bekliyor?",
            {"birth": {"timezone_id": "Europe/Istanbul"}},
            "bypass-three-month-route-test",
            mode_override="bypass",
        )

        self.assertEqual(routing["status"], "classifier_bypassed")
        self.assertEqual(routing["selected"]["primary_topic"], "general")
        self.assertEqual(routing["selected"]["time_scope"], "range")
        self.assertTrue(routing["selected"]["timing_required"])
        self.assertIn("stored_transit_days", routing["selected"]["required_evidence"])

    def test_bypass_router_covers_all_api_subjects_and_never_inherits_an_absent_topic(self):
        cases = {
            "Karakterimde öne çıkan güçlü yön nedir?": "character",
            "Kariyerimde hangi becerimi geliştirmeliyim?": "career",
            "Evlilik konusunda sınırlarımı nasıl kurarım?": "marriage",
            "Maddi güven ve birikim düzenimi nasıl ele almalıyım?": "wealth",
            "Sağlık ve enerji düzenimde neye dikkat etmeliyim?": "health",
            "Aile içinde sorumlulukları nasıl dengelemeliyim?": "family",
            "Eğitim ve uzmanlaşma yönüm nasıl görünüyor?": "education",
            "Yurtdışına taşınma kararını nasıl değerlendirmeliyim?": "relocation",
            "Hukuki sözleşme sürecinde neye dikkat etmeliyim?": "legal",
            "Ruhsal yönüm ve yaşam amacım hakkında ne görünüyor?": "spiritual",
            "İyi hissetmiyorum.": "wellbeing",
            "Yıllık haritam hangi alanları öne çıkarıyor?": "varshaphala",
        }
        for index, (question, expected) in enumerate(cases.items()):
            with self.subTest(question=question):
                routing = _beta_question_route(
                    question,
                    {"birth": {"timezone_id": "Europe/Istanbul"}},
                    f"bypass-all-topics-{index}",
                    conversation_context=[{
                        "question": "Kariyerimde ne olur?",
                        "answer": "Önceki cevap yalnız kariyer hakkındaydı.",
                    }],
                    mode_override="bypass",
                )
                self.assertEqual(routing["selected"]["primary_topic"], expected)

        neutral = _beta_question_route(
            "Bu konuda bana ne söyleyebilirsin?",
            {"birth": {"timezone_id": "Europe/Istanbul"}},
            "bypass-neutral-current-question",
            conversation_context=[{
                "question": "İlişkim nasıl ilerler?",
                "answer": "Önceki cevap ilişki hakkındaydı.",
            }],
            mode_override="bypass",
        )
        self.assertEqual(neutral["selected"]["primary_topic"], "general")

    def test_extended_api_subjects_receive_real_topic_packets(self):
        chart = {
            "houses": [],
            "lordships": {},
            "planets": [],
            "vargas": {},
            "dashas": {},
            "yogas": {},
            "missing": [],
            "analysis_modules": {
                "children_education": {"confidence": "medium", "missing_data": []},
                "property_legal": {"confidence": "medium", "missing_data": []},
                "spiritual_karma_dharma": {"confidence": "medium", "missing_data": []},
                "varshaphala": {"confidence": "medium", "missing_data": []},
            },
            "varshaphala": {"status": "available", "year": {"varsha_start_year": 2026}},
        }
        for topic in (
            "character", "wellbeing", "family", "education", "relocation",
            "legal", "spiritual", "varshaphala",
        ):
            with self.subTest(topic=topic):
                packet = _beta_topic_packet(chart, topic)
                self.assertEqual(packet["topic"], topic)
                self.assertEqual(packet["source"], "canonical_chart_topic_selection")
                self.assertIn("evidence", packet)

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

        compact = compact_evidence({
            "question": "Karakterimdeki en güçlü özellik nedir?",
            "topic": "character",
            "subject_topic": "character",
            "evidence": {"strength_summary": summary},
        })
        self.assertEqual(compact["strength_summary"]["strongest_planet"], "Sun")

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
            routing={
                "selected": {
                    "contract_version": "test-route-v1",
                    "primary_topic": "career",
                    "time_scope": "range",
                    "timing_required": True,
                    "target_start": "2026-08-01",
                    "target_end": "2026-08-02",
                    "required_evidence": ["stored_transit_days"],
                },
            },
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
