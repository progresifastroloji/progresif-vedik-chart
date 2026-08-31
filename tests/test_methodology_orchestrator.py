import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from methodology_orchestrator import (
    CANDIDATE_MANIFEST,
    GUIDANCE_MANIFEST,
    MethodologyOrchestrationError,
    _model_request,
    _narrative_request,
    compact_evidence,
    full_markdown_test_mode,
    load_guidance_methodology,
    load_methodology_candidates,
    ordered_full_markdown_mode,
    run_methodology_comparison,
    validate_methodology_response,
    validate_narrative_response,
)
from question_classifier import ALLOWED_TOPICS


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


def _narrative_payload(answer=None, opening_summary=None):
    opening_summary = opening_summary or (
        "Kariyerinizde kalıcı başarı, tek bir alanda derinleştiğinizde daha güçlü biçimde görünür olabilir. "
        "En belirgin üstünlüğünüz, sorumluluk alırken karmaşayı düzene çevirebilmenizdir. "
        "Önünüzü açacak temel seçim, enerjinizi dağıtan yükleri azaltıp emeğinizi görünür kılmaktır."
    )
    answer = answer or (
        "Kariyerinizde güçlü bir gelişim potansiyeli var; ancak bu potansiyel, sabırlı biçimde "
        "uzmanlaşmanız ve sorumluluk alanınızı netleştirmeniz koşuluyla daha görünür hale geliyor. "
        "Haritanın verdiği ana cevap, hızlı bir sıçramadan çok kalıcı bir yapı kurmaya yatkın olduğunuzdur.\n\n"
        "Teknik analizde mesleki yönü destekleyen göstergeler ile ilerlemeyi yavaşlatabilecek koşullar "
        "birlikte görülüyor. Bu nedenle yalnız güçlü yanlarınıza yaslanmak yerine, enerjinizi dağıtan işlere "
        "sınır koymanız ve belirli bir alanda derinleşmeniz daha verimli olur. Böyle yaptığınızda görünürlük "
        "ve güvenilirlik aynı anda büyüyebilir.\n\n"
        "Pratik olarak önümüzdeki dönemde tek bir ana hedef seçmeniz, onu haftalık küçük adımlara bölmeniz "
        "ve yaptığınız işi düzenli biçimde görünür kılmanız yararlı olur. Sonucu garanti eden tek bir gösterge "
        "yoktur; harita size en çok, disiplinli hazırlık ile doğru fırsatı buluşturduğunuzda ilerleme alanı açıldığını gösteriyor."
    )
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps({
            "opening_summary": opening_summary,
            "answer": answer,
        })}]}}],
        "usageMetadata": {
            "promptTokenCount": 40,
            "candidatesTokenCount": 180,
            "totalTokenCount": 220,
        },
        "modelVersion": "test-model",
    }


class MethodologyOrchestratorTest(unittest.TestCase):
    def test_full_markdown_test_mode_adds_complete_markdown_once_without_changing_default(self):
        document = "# FULL NATAL TEST\n\nBu metin yalnız test için gönderilir.\n"
        draft = _draft()
        draft["_full_markdown_test"] = {
            "filename": "natal-interpretation.md",
            "sha256": "test-sha256",
            "content": document,
        }
        candidate = load_methodology_candidates()[0]

        with patch.dict(os.environ, {"VEDIC_GEMINI_FULL_MARKDOWN_TEST": "1"}, clear=False):
            self.assertTrue(full_markdown_test_mode())
            evidence = compact_evidence(draft)
            request, _ = _model_request(candidate, evidence)
            prompt = request["contents"][0]["parts"][0]["text"]
            self.assertIn("TAM MARKDOWN KAYNAKLARI", prompt)
            self.assertEqual(prompt.count(document), 1)
            self.assertIn("natal-interpretation.md", prompt)
            self.assertIn("SYSTEM_METHODOLOGY", request["systemInstruction"]["parts"][0]["text"])

        with patch.dict(os.environ, {"VEDIC_GEMINI_FULL_MARKDOWN_TEST": "0"}, clear=False):
            self.assertFalse(full_markdown_test_mode())
            evidence = compact_evidence(draft)
            request, _ = _model_request(candidate, evidence)
            prompt = request["contents"][0]["parts"][0]["text"]
            self.assertNotIn("TAM MARKDOWN KAYNAKLARI", prompt)
            self.assertNotIn(document, prompt)

    def test_full_markdown_context_reaches_narrative_call(self):
        document = "# FULL NATAL NARRATIVE TEST\n\nAyrıntılı kaynak içeriği.\n"
        draft = _draft()
        draft["_full_markdown_test"] = {
            "documents": [{
                "filename": "natal-interpretation.md",
                "sha256": "test-sha256",
                "content": document,
            }],
        }
        candidate = load_methodology_candidates()[0]
        analysis = validate_methodology_response(_payload(), compact_evidence(draft))
        with patch.dict(os.environ, {"VEDIC_GEMINI_MARKDOWN_MODE": "full"}, clear=True):
            evidence = compact_evidence(draft)
            request, _ = _narrative_request(candidate, evidence, analysis)
        prompt = request["contents"][0]["parts"][0]["text"]
        self.assertIn("TAM MARKDOWN KAYNAKLARI", prompt)
        self.assertEqual(prompt.count(document), 1)
        self.assertEqual(request["generationConfig"]["maxOutputTokens"], 8192)

    def test_ordered_full_mode_sends_all_three_sources_in_fixed_order(self):
        natal = "# TAM NATAL\nNatal ayrıntısı.\n"
        transit = "# TAM ÜÇ AYLIK TRANSİT\nTransit ayrıntısı.\n"
        draft = _draft()
        draft["_full_markdown_test"] = {
            "documents": [
                {
                    "filename": "natal-interpretation.md",
                    "sha256": "natal-sha",
                    "content": natal,
                },
                {
                    "filename": "transit-three-month.md",
                    "sha256": "transit-sha",
                    "content": transit,
                },
            ],
        }
        candidate = load_methodology_candidates()[0]

        with patch.dict(os.environ, {"VEDIC_GEMINI_MARKDOWN_MODE": "ordered_full"}, clear=True):
            self.assertTrue(full_markdown_test_mode())
            self.assertTrue(ordered_full_markdown_mode())
            evidence = compact_evidence(draft)
            technical_request, _ = _model_request(candidate, evidence)
            technical_system = technical_request["systemInstruction"]["parts"][0]["text"]
            technical_user = technical_request["contents"][0]["parts"][0]["text"]
            self.assertIn("Kaynak sırası sabittir", technical_system)
            self.assertLess(technical_user.index("natal-interpretation.md"), technical_user.index("transit-three-month.md"))

            analysis = validate_methodology_response(_payload(), evidence)
            narrative_request, _ = _narrative_request(candidate, evidence, analysis)
            narrative_user = narrative_request["contents"][0]["parts"][0]["text"]
            methodology_marker = "===== TAM DOSYA 1/3: SYSTEM_METHODOLOGY.txt ====="
            self.assertIn(methodology_marker, narrative_user)
            self.assertIn(natal, narrative_user)
            self.assertIn(transit, narrative_user)
            self.assertLess(narrative_user.index(methodology_marker), narrative_user.index("natal-interpretation.md"))
            self.assertLess(narrative_user.index("natal-interpretation.md"), narrative_user.index("transit-three-month.md"))

    def test_normal_source_context_ignores_diagnostic_gate(self):
        draft = _draft()
        draft["_full_markdown_sources"] = {
            "documents": [
                {
                    "filename": "natal-interpretation.md",
                    "sha256": "natal-sha",
                    "content": "# TAM NATAL KAYNAĞI\n",
                },
                {
                    "filename": "transit-three-month.md",
                    "sha256": "transit-sha",
                    "content": "# TAM ÜÇ AYLIK TRANSİT KAYNAĞI\n",
                },
            ],
        }
        candidate = load_methodology_candidates()[0]

        with patch.dict(
            os.environ,
            {"VEDIC_GEMINI_MARKDOWN_MODE": "compact", "VEDIC_GEMINI_FULL_MARKDOWN_TEST": "0"},
            clear=False,
        ):
            evidence = compact_evidence(draft)
            request, _ = _model_request(candidate, evidence)
            prompt = request["contents"][0]["parts"][0]["text"]

        self.assertIn("# TAM NATAL KAYNAĞI", prompt)
        self.assertIn("# TAM ÜÇ AYLIK TRANSİT KAYNAĞI", prompt)
        self.assertIn("natal-interpretation.md", prompt)
        self.assertIn("transit-three-month.md", prompt)

    def test_manifest_loads_single_active_system_methodology(self):
        candidates = load_methodology_candidates()

        self.assertEqual(
            [candidate["id"] for candidate in candidates],
            [candidate["id"] for candidate in CANDIDATE_MANIFEST],
        )
        self.assertEqual(len(candidates), 1)
        self.assertTrue(all(candidate["status"] == "active" for candidate in candidates))
        self.assertTrue(all(candidate["document"].startswith("---\n") for candidate in candidates))

    def test_guidance_methodology_is_versioned_and_narrative_only(self):
        guidance = load_guidance_methodology()

        self.assertEqual(guidance["id"], "vedic-guidance-skill-v1")
        self.assertEqual(guidance["version"], "1.3.0")
        self.assertEqual(guidance["sha256"], GUIDANCE_MANIFEST["sha256"])
        self.assertIn("runtime_stage: narrative_only", guidance["document"])
        self.assertIn("en fazla tek kısa", guidance["document"])
        self.assertIn("bütün karşıt kanıtlar", guidance["document"])
        self.assertIn("yalnız kullanıcının açık sözlerinden", guidance["document"])
        self.assertIn("SAV/BAV", guidance["document"])
        self.assertIn("Uygulanabilir Rehberlik", guidance["document"])
        self.assertIn("başlık, alt başlık, numaralı liste", guidance["document"])

    def test_analysis_runs_single_active_methodology_and_selects_it(self):
        calls = []
        draft = _draft()
        draft["conversation_context"] = [
            {
                "question": "Yarınki iş görüşmem nasıl geçer?",
                "answer": "İlk değerlendirme bu soruya aittir.",
            },
            {
                "question": "Ay etkisini de açıklar mısın?",
                "answer": "İkinci cevap Ay etkisini açıklar.",
            },
        ]

        def model_call(request_id, request):
            calls.append((request_id, request))
            if "-narrative" in request_id:
                return request_id, _narrative_payload()
            return request_id, _payload(request_id)

        result = run_methodology_comparison(
            draft,
            "methodology-compare-test-1",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["completed_count"], 1)
        self.assertEqual(result["selection"], "vedic-system-methodology-v1")
        self.assertEqual(result["selection_status"], "system_methodology_active")
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            {item["evidence_sha256"] for item in result["methodology_results"]},
            {result["evidence_sha256"]},
        )
        technical_request = calls[0][1]
        system_text = technical_request["systemInstruction"]["parts"][0]["text"]
        self.assertIn("METODOLOJİ KİMLİĞİ: vedic-system-methodology-v1@1.7.0", system_text)
        self.assertNotIn("vedic-guidance-skill-v1", system_text)
        user_text = technical_request["contents"][0]["parts"][0]["text"]
        self.assertNotIn("must_not_be_sent_for_natal_topic", user_text)
        self.assertIn("Yarınki iş görüşmem nasıl geçer?", user_text)
        self.assertIn("Ay etkisini de açıklar mısın?", user_text)
        narrative_request = calls[1][1]
        narrative_text = narrative_request["contents"][0]["parts"][0]["text"]
        narrative_system = narrative_request["systemInstruction"]["parts"][0]["text"]
        self.assertIn("Yarınki iş görüşmem nasıl geçer?", narrative_text)
        self.assertIn("Ay etkisini de açıklar mısın?", narrative_text)
        self.assertIn("TEKNİK METODOLOJİ BELGESİ", narrative_system)
        self.assertIn("vedic-guidance-skill-v1@1.3.0", narrative_system)
        self.assertIn("en fazla tek kısa ve sade dayanak cümlesini", narrative_system)
        self.assertIn("SAV/BAV", narrative_system)
        self.assertIn("'Uygulanabilir Rehberlik' diye bir bölüm açma", narrative_system)
        self.assertEqual(
            narrative_request["generationConfig"]["maxOutputTokens"],
            8192,
        )
        self.assertEqual(
            technical_request["generationConfig"]["maxOutputTokens"],
            8192,
        )
        system_result = result["methodology_results"][0]
        self.assertEqual(result["guidance_methodology"]["id"], "vedic-guidance-skill-v1")
        self.assertEqual(system_result["guidance_methodology"]["sha256"], GUIDANCE_MANIFEST["sha256"])
        self.assertIn("technical_summary", system_result["analysis"])
        self.assertEqual(
            system_result["analysis"]["opening_summary"].count("."),
            3,
        )
        self.assertGreater(len(system_result["analysis"]["summary"]), 700)
        self.assertEqual(system_result["usage"]["total_tokens"], 370)

    def test_selected_english_language_reaches_both_model_prompts(self):
        calls = []
        draft = _draft()
        draft["response_language"] = "en"

        english_narrative = _narrative_payload(
            opening_summary=(
                "Your career direction can become clearer when responsibility and progress are measured together. "
                "A steady, practical choice is more useful than a certain promise."
            ),
            answer=(
                "The available evidence supports building expertise through consistent responsibility, while keeping "
                "your commitments clear and reviewable. This is a conditional interpretation rather than a guaranteed "
                "outcome.\n\n"
                "In practice, choose one priority, define a visible measure of progress, and review it regularly. "
                "If circumstances change, adjust the plan before making a larger commitment."
            ),
        )

        def model_call(request_id, request):
            calls.append((request_id, request))
            return request_id, english_narrative if "-narrative" in request_id else _payload(request_id)

        result = run_methodology_comparison(draft, "methodology-compare-en", model_call)
        self.assertEqual(result["response_language"], "en")
        self.assertEqual(result["status"], "comparison_ready")
        technical_text = calls[0][1]["systemInstruction"]["parts"][0]["text"]
        narrative_text = calls[1][1]["systemInstruction"]["parts"][0]["text"]
        self.assertIn("cevap dili EN", technical_text)
        self.assertIn("cevap dili EN", narrative_text)
        self.assertIn("English", narrative_text)

    def test_methodology_uses_customer_declaration_data_gate_without_event_file(self):
        document = load_methodology_candidates()[0]["document"]

        self.assertIn("Eminim** / `exact`", document)
        self.assertIn("Yaklaşık biliyorum** / `approximate`", document)
        self.assertIn("Hiç bilmiyorum** / `unknown`", document)
        self.assertNotIn("`rectified` (olay dosyası ile)", document)
        self.assertNotIn("Kayıtlı olay yoksa `data: medium`", document)
        self.assertIn("Ana müşteri analizinin veri güvenini", document)

    def test_methodology_matches_current_artifacts_and_runtime_schema(self):
        document = load_methodology_candidates()[0]["document"]

        self.assertIn("`natal-interpretation.md`", document)
        self.assertIn("`transit-three-month.md`", document)
        self.assertIn("`canonical-snapshot.json`", document)
        self.assertIn("`manifest.json`", document)
        self.assertIn("`topic_packet` fiziksel bir dosya değildir", document)
        self.assertIn("Aşama 2 `opening_summary` ve `answer` alanları", document)
        self.assertNotIn("Künye:", document)
        self.assertNotIn("FACT / ATOM", document)
        self.assertNotIn("RUL-*", document)
        self.assertNotIn("ACTIVE/PROVISIONAL", document)
        self.assertNotIn("448 kural ACTIVE", document)
        self.assertNotIn("## Danışman modu", document)
        self.assertNotIn("## Genel harita kompozisyonu", document)
        for topic in ALLOWED_TOPICS:
            self.assertIn(f"### `{topic}`", document)
        for stale_topic in ("P01-REL", "P01-MAR", "P02-BIZ", "P11-TIM"):
            self.assertNotIn(stale_topic, document)

    def test_narrative_rejects_methodology_or_evidence_leak(self):
        answer = (
            "VEDİK ANALİZ SİSTEM METODOLOJİSİ\n\n"
            + "Bu metin yeterince uzun bir danışan yanıtı gibi görünse de iç teknik başlığı sızdırıyor. " * 10
            + "\n\nBu nedenle kullanıcıya gösterilmemelidir."
        )
        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(answer),
                validate_methodology_response(
                    _payload(),
                    compact_evidence(_draft()),
                ),
                compact_evidence(_draft()),
            )
        self.assertEqual(context.exception.code, "methodology_narrative_technical_leak")

    def test_narrative_rejects_a_relationship_question_that_the_user_never_asked(self):
        opening = (
            "İlişki sorunuza karşılık sistemimizin kariyer odağına yönlenmesi nedeniyle "
            "profesyonel sorumluluklarınız öne çıkıyor."
        )
        answer = (
            "Mevcut koşulları acele etmeden gözden geçirmek ve karar ölçütlerini açık biçimde "
            "tanımlamak yararlı olabilir. Önceliklerinizi, sorumluluklarınızı ve değiştirebildiğiniz "
            "alanları ayrı ayrı değerlendirmeniz belirsizliği azaltır.\n\n"
            "Tek bir sonuca hızla bağlanmak yerine küçük bir deneme adımı seçin, sonucu gözlemleyin "
            "ve yeni bilgi geldikçe planınızı güncelleyin. Böylece kararınız varsayıma değil, gerçek "
            "koşullara ve açık geri bildirime dayanır.\n\n"
            "Geri dönüşü zor bir taahhüt vermeden önce seçenekleri karşılaştırın ve ihtiyaç varsa "
            "ilgili alandaki bağımsız bir uzmandan görüş alın."
        )
        evidence = compact_evidence(_draft())
        analysis = validate_methodology_response(_payload(), evidence)

        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(answer, opening),
                analysis,
                evidence,
            )

        self.assertEqual(context.exception.code, "methodology_narrative_topic_mismatch")

    def test_narrative_rejects_sav_graha_yuddha_drishti_and_guidance_heading(self):
        answer = (
            "Bazı dengeleyici unsurlar ilişki kararlarınızda daha dikkatli ilerlemeyi gerektiriyor.\n\n"
            "**Mars'ın Düşüş Konumu ve Düşük SAV Skoru:** 7. evdeki Mars düşüşte olduğu ve "
            "SAV puanı düşük kaldığı için hızlı başlangıçların ardından güç savaşı riski vardır. "
            "Venüs ile Jüpiter arasındaki Graha Yuddha ve Satürn drishti etkisi bu teknik hükmü destekler.\n\n"
            "**Uygulanabilir Rehberlik:** Karşınızdaki kişiyi tanımak için kendinize zaman tanıyın. "
            "Sosyal ortamlarda açık olun fakat acele bir karar vermeyin. Bu yaklaşım ilişkinin gerçekçi "
            "biçimde gelişip gelişmediğini görmenizi ve kendi sınırlarınızı daha iyi korumanızı sağlayabilir."
        )
        analysis = validate_methodology_response(_payload(), compact_evidence(_draft()))

        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(answer),
                analysis,
                compact_evidence(_draft()),
            )

        self.assertEqual(context.exception.code, "methodology_narrative_technical_leak")

    def test_narrative_allows_one_plain_astrological_anchor_after_the_answer(self):
        answer = (
            "İlişkilerde hızlı yakınlaşma isteğiniz ile güveni zamana yayma ihtiyacınız birlikte çalışabilir. "
            "Bunu destekleyen ana astrolojik işaret, Ay'ın duygusal güveni acele etmeden kurma ihtiyacını öne "
            "çıkarmasıdır.\n\n"
            "Bu nedenle ilk heyecanın yanında karşınızdaki kişinin davranışlarının zaman içindeki tutarlılığına da "
            "bakmanız daha dengeli olabilir. Yeni bir tanışmada hemen sonuç çıkarmak yerine birkaç görüşme boyunca "
            "sözler ile davranışların ne kadar örtüştüğünü gözlemlemeyi deneyebilirsiniz."
        )
        analysis = validate_methodology_response(_payload(), compact_evidence(_draft()))

        validated = validate_narrative_response(
            _narrative_payload(answer),
            analysis,
            compact_evidence(_draft()),
        )

        self.assertEqual(validated["answer"], answer)

    def test_narrative_rejects_more_than_one_visible_astrological_anchor_sentence(self):
        answer = (
            "İlişkilerde hızlı yakınlaşma isteğiniz ile güveni zamana yayma ihtiyacınız birlikte çalışabilir. "
            "Mars doğrudan davranma eğilimini güçlendirebilir. Ay'ın konumu ise güveni zamana yayma ihtiyacını "
            "öne çıkarabilir.\n\n"
            "Bu nedenle birkaç görüşme boyunca sözler ile davranışların ne kadar örtüştüğünü gözlemlemek daha "
            "dengeli bir seçim yapmanıza yardımcı olabilir."
        )
        analysis = validate_methodology_response(_payload(), compact_evidence(_draft()))

        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(answer),
                analysis,
                compact_evidence(_draft()),
            )

        self.assertEqual(
            context.exception.code,
            "methodology_narrative_evidence_density_invalid",
        )

    def test_narrative_rejects_astrological_anchor_in_opening_summary(self):
        analysis = validate_methodology_response(_payload(), compact_evidence(_draft()))

        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(
                    opening_summary=(
                        "Satürn kariyerinizde sabırlı ve kalıcı ilerlemenin ana dayanağıdır."
                    ),
                ),
                analysis,
                compact_evidence(_draft()),
            )

        self.assertEqual(
            context.exception.code,
            "methodology_narrative_evidence_density_invalid",
        )

    def test_narrative_rejects_guidance_heading_even_without_technical_terms(self):
        answer = (
            "İlişkilerde güveni zamana yaymanız, ilk izlenim ile kalıcı uyumu birbirinden ayırmanıza yardımcı olabilir. "
            "Karşınızdaki kişinin farklı koşullarda nasıl davrandığını görmek, kendi ihtiyaçlarınızı daha açık biçimde "
            "fark etmenizi ve acele bir sonuca bağlanmamanızı sağlayabilir.\n\n"
            "**Uygulanabilir Rehberlik:** Önümüzdeki tanışmalarda birkaç görüşme boyunca sözler ile davranışların "
            "ne kadar örtüştüğünü gözlemleyebilirsiniz. Bu küçük gözlem, seçiminizi korkudan veya ilk heyecandan değil, "
            "yaşanmış deneyimden yapmanıza yardımcı olabilir."
        )
        analysis = validate_methodology_response(_payload(), compact_evidence(_draft()))

        with self.assertRaises(MethodologyOrchestrationError) as context:
            validate_narrative_response(
                _narrative_payload(answer),
                analysis,
                compact_evidence(_draft()),
            )

        self.assertEqual(context.exception.code, "methodology_narrative_technical_leak")

    def test_narrative_allows_expanded_technical_opening_summary(self):
        analysis = validate_methodology_response(
            _payload(),
            compact_evidence(_draft()),
        )
        evidence = compact_evidence(_draft())

        validate_narrative_response(
            _narrative_payload(opening_summary="Bu yalnız iki cümledir. İkincisi de burada biter."),
            analysis,
            evidence,
        )

        technical = (
            "Kariyerinizde belirleyici bir rol üstleniyorsunuz. "
            "Altıncı ev çalışma düzeninizi öne çıkarıyor. "
            "Bu yerleşim hizmet alanında başarı sağlayabilir."
        )
        validate_narrative_response(
            _narrative_payload(opening_summary=technical),
            analysis,
            evidence,
        )

    def test_short_narrative_is_retried_without_rerunning_technical_analysis(self):
        calls = []

        def model_call(request_id, _request):
            calls.append(request_id)
            if request_id.endswith("-analysis"):
                return request_id, _payload()
            if request_id.endswith("-narrative"):
                short = {
                    "candidates": [{
                        "content": {"parts": [{"text": json.dumps({
                            "opening_summary": (
                                "Kariyerinizde kalıcı gelişim için alanınızı netleştirmeniz gerekir. "
                                "Sorumluluk alma gücünüz doğru sınırlarla daha görünür olabilir. "
                                "Önceliğiniz, emeğinizi dağıtmadan tek bir hedefe yöneltmek olmalıdır."
                            ),
                            "answer": "Kısa cevap.",
                        })}]},
                    }],
                }
                return request_id, short
            return request_id, _narrative_payload()

        result = run_methodology_comparison(
            _draft(),
            "methodology-narrative-retry",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        phases = [item.rsplit("vedic-system-methodology-v1", 1)[1] for item in calls]
        self.assertEqual(sum(item.startswith("-analysis") for item in phases), 1)
        self.assertEqual(sum(item.startswith("-narrative") for item in phases), 2)
        system_result = result["methodology_results"][0]
        self.assertEqual(system_result["technical_attempt_count"], 1)
        self.assertEqual(system_result["narrative_attempt_count"], 2)

    def test_technical_main_text_is_retried_without_rerunning_analysis(self):
        calls = []

        def model_call(request_id, _request):
            calls.append(request_id)
            if request_id.endswith("-analysis"):
                return request_id, _payload()
            if request_id.endswith("-narrative"):
                answer = (
                    "İlişki konusunda dikkatli ilerlemek önemlidir. "
                    "7. ev SAV puanı ve Graha Yuddha teknik olarak zorlayıcı bir tablo gösterir. "
                    "Bu nedenle ilk izlenimle karar vermek yerine davranışların zaman içindeki tutarlılığına bakmak gerekir.\n\n"
                    "**Uygulanabilir Rehberlik:** Birkaç görüşme boyunca sözler ile davranışların ne kadar örtüştüğünü "
                    "gözlemleyebilirsiniz. Bu küçük adım, acele bir sonuç yerine yaşanmış deneyime dayanarak seçim "
                    "yapmanıza ve kendi sınırlarınızı daha açık görmenize yardımcı olabilir."
                )
                return request_id, _narrative_payload(answer)
            return request_id, _narrative_payload()

        result = run_methodology_comparison(
            _draft(),
            "methodology-narrative-technical-retry",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        phases = [item.rsplit("vedic-system-methodology-v1", 1)[1] for item in calls]
        self.assertEqual(sum(item.startswith("-analysis") for item in phases), 1)
        self.assertEqual(sum(item.startswith("-narrative") for item in phases), 2)
        system_result = result["methodology_results"][0]
        self.assertEqual(system_result["technical_attempt_count"], 1)
        self.assertEqual(system_result["narrative_attempt_count"], 2)

    def test_strict_mode_uses_validated_plain_fallback_after_narrative_retries(self):
        def model_call(request_id, _request):
            if request_id.endswith("-analysis"):
                return request_id, _payload()
            return request_id, _narrative_payload(
                opening_summary="Mars ve düşük SAV teknik olarak belirleyicidir.",
                answer=(
                    "### Uygulanabilir Rehberlik\n\n"
                    "7. ev ve Graha Yuddha nedeniyle acele etmeyin. "
                    "Bu metin teknik görünürlüğü özellikle artırır. " * 8
                ),
            )

        with patch.dict(os.environ, {"VEDIC_METHODOLOGY_VALIDATION_MODE": "strict"}):
            result = run_methodology_comparison(
                _draft(),
                "methodology-compare-narrative-fallback",
                model_call,
            )

        self.assertEqual(result["status"], "comparison_ready")
        system_result = result["methodology_results"][0]
        self.assertTrue(system_result["narrative_fallback"])
        self.assertNotIn("SAV", system_result["analysis"]["summary"])
        self.assertNotIn("Graha Yuddha", system_result["analysis"]["summary"])
        self.assertNotIn("###", system_result["analysis"]["summary"])

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
            if request_id.endswith("-analysis"):
                invalid = _payload()
                value = json.loads(invalid["candidates"][0]["content"]["parts"][0]["text"])
                value["supporting_evidence"][0]["evidence_path"] = "evidence.nonexistent.layer"
                invalid["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
                return request_id, invalid
            if "-narrative" in request_id:
                return request_id, _narrative_payload()
            return request_id, _payload()

        result = run_methodology_comparison(
            _draft(),
            "methodology-compare-schema-retry",
            model_call,
        )

        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["completed_count"], 1)
        self.assertEqual(len(calls), 3)
        system_result = result["methodology_results"][0]
        self.assertEqual(system_result["status"], "completed")
        self.assertEqual(system_result["attempt_count"], 3)
        self.assertTrue(system_result["technical_request_id"].endswith("-analysis-retry-1"))
        self.assertTrue(system_result["narrative_request_id"].endswith("-narrative"))

    def test_validation_bypass_is_reversible_and_keeps_parseable_provider_output(self):
        calls = []

        def model_call(request_id, _request):
            calls.append(request_id)
            if request_id.endswith("-analysis"):
                invalid = _payload()
                value = json.loads(invalid["candidates"][0]["content"]["parts"][0]["text"])
                value["methodology_coverage"] = []
                value["supporting_evidence"][0]["evidence_path"] = "evidence.nonexistent.layer"
                invalid["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(value)
                return request_id, invalid
            return request_id, _narrative_payload(
                opening_summary="Bu özet iki cümlede kalır.",
                answer="Kısa ama okunabilir cevap.",
            )

        with patch.dict(os.environ, {"VEDIC_METHODOLOGY_VALIDATION_MODE": "bypass"}):
            result = run_methodology_comparison(
                _draft(),
                "methodology-compare-validation-bypass",
                model_call,
            )

        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["validation_mode"], "bypass")
        self.assertEqual(calls, [
            "methodology-compare-validation-bypass-vedic-system-methodology-v1-analysis",
            "methodology-compare-validation-bypass-vedic-system-methodology-v1-narrative",
        ])
        analysis = result["methodology_results"][0]["analysis"]
        self.assertTrue(analysis["validation_bypassed"])
        self.assertEqual(analysis["opening_summary"], "Bu özet iki cümlede kalır.")

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
            "2026-08-15 tarihinde transit Ay Uttara Phalguni nakshatrasında ilerliyor."
        )
        value["supporting_evidence"][0] = {
            "claim": "2026-08-15 günü transit Ay kaydı incelendi.",
            "evidence_path": "evidence.transits.daily_records.0",
        }
        value["challenging_evidence"][0] = {
            "claim": "Aynı günün Tithi ve Panchanga sınırları birlikte okundu.",
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
                    "panchanga": {
                        "tithi": {"name": "Shukla Dvitiya"},
                        "moon_nakshatra": {"name": "Uttara Phalguni"},
                    },
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

    def test_instant_wellbeing_adds_verified_moon_and_panchanga_fact(self):
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
                    "panchanga": {
                        "tithi": {"name": "Shukla Dvitiya"},
                        "moon_nakshatra": {"name": "Uttara Phalguni"},
                    },
                    "planets": [{"name": "Moon", "degree": "10° 00' 00\""}],
                }],
            },
        }

        validated = validate_methodology_response(payload, evidence)

        self.assertIn("Transit Ay", validated["summary"])
        self.assertIn("Panchanga", validated["summary"])
        self.assertTrue(any(
            row["evidence_path"].endswith(".panchanga")
            for row in validated["supporting_evidence"]
        ))

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

    def test_guidance_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = Path(__file__).resolve().parents[1] / "methodologies"
            path = root / GUIDANCE_MANIFEST["filename"]
            content = (source_root / GUIDANCE_MANIFEST["filename"]).read_text(encoding="utf-8")
            path.write_text(content + "\nchanged", encoding="utf-8")

            with self.assertRaises(MethodologyOrchestrationError) as raised:
                load_guidance_methodology(root)

        self.assertEqual(raised.exception.code, "guidance_methodology_checksum_mismatch")


if __name__ == "__main__":
    unittest.main()
