"""Controlled comparison runner for the three Vedik methodology candidates."""

import hashlib
import json
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path


CONTRACT_VERSION = "vedic-system-analysis-v4"
MAX_METHODOLOGY_BYTES = 64 * 1024
# Full Markdown mode intentionally has room for both owned source documents
# plus the validated evidence package. The provider still receives one bounded
# request, so an unexpectedly huge artifact fails loudly instead of being cut.
MAX_PROMPT_BYTES = 1024 * 1024
FULL_MARKDOWN_MODE_ENV = "VEDIC_GEMINI_MARKDOWN_MODE"
FULL_MARKDOWN_TEST_ENV = "VEDIC_GEMINI_FULL_MARKDOWN_TEST"
# Explicit diagnostic mode: send the complete, owned source set in a fixed
# order. Keep this separate from the existing route-aware ``full`` mode so
# the production default and older test switch remain backward compatible.
ORDERED_FULL_MARKDOWN_MODES = {
    "ordered_full",
    "full_ordered",
    "ordered",
    "all_files",
}
FULL_SOURCE_CONTEXT_MODES = {
    "all_full",
    "full",
    "ordered_full",
    "full_ordered",
    "ordered",
    "all_files",
}
TECHNICAL_MAX_OUTPUT_TOKENS = 8192
NARRATIVE_MAX_OUTPUT_TOKENS = 8192
NARRATIVE_MIN_CHARS = 300
NARRATIVE_MIN_PARAGRAPHS = 1
CONFIDENCE_LEVELS = {"low", "medium", "high"}
COVERAGE_STATUSES = {"applied", "not_applicable", "missing"}
REQUIRED_METHODOLOGY_STEPS = (
    "question_and_scope",
    "topic_package",
    "data_gate",
    "d1_natal_promise",
    "bhava_lord_karaka",
    "dispositor_and_nakshatra",
    "strength_capacity_delivery",
    "relevant_varga",
    "dasha_access",
    "transit_trigger",
    "counter_evidence",
    "thematic_synthesis",
)
RETRYABLE_RESPONSE_ERRORS = {
    "methodology_model_json_invalid",
    "methodology_model_response_empty",
    "methodology_model_schema_invalid",
    "methodology_model_intent_invalid",
    "methodology_model_coverage_invalid",
    "methodology_model_summary_invalid",
    "methodology_model_evidence_invalid",
    "methodology_model_list_invalid",
    "methodology_model_strength_invalid",
    "methodology_model_timing_evidence_invalid",
}
RETRYABLE_NARRATIVE_ERRORS = {
    "methodology_narrative_json_invalid",
    "methodology_narrative_response_invalid",
    "methodology_narrative_response_empty",
    "methodology_narrative_schema_invalid",
    "methodology_narrative_opening_summary_invalid",
    "methodology_narrative_too_short",
    "methodology_narrative_timing_evidence_invalid",
    "methodology_narrative_technical_leak",
}
EVIDENCE_PATH_PATTERN = re.compile(r"^evidence(?:\.[a-zA-Z0-9_\-]+)+$")

CANDIDATE_MANIFEST = (
    {
        "id": "vedic-system-methodology-v1",
        "title": "Vedik Analiz Sistem Metodolojisi",
        "version": "1.5.0",
        "status": "active",
        "filename": "SYSTEM_METHODOLOGY.txt",
        "sha256": "192daafc4fd9de382814c56ed51c99ba5e242c1001e239b74a9d9306d29e5cad",
    },
)


class MethodologyOrchestrationError(Exception):
    """Safe orchestration failure with a stable public error code."""

    def __init__(self, code, http_status=500):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


def methodology_validation_mode():
    """Return the semantic model-validation mode for the current process.

    ``strict`` is the safe default. ``bypass`` is intentionally an explicit,
    reversible operations switch for diagnosing provider/output drift. It
    does not bypass JSON decoding or an entirely empty provider response.
    """

    value = os.environ.get("VEDIC_METHODOLOGY_VALIDATION_MODE", "strict")
    normalized = str(value or "strict").strip().lower()
    return "bypass" if normalized in {"bypass", "disabled", "off"} else "strict"


def full_markdown_test_mode():
    """Return whether full Markdown context is explicitly enabled.

    ``full`` is the durable setting; the older boolean test flag remains an
    alias so an already prepared diagnostic environment can be switched back
    without a code change. Compact mode remains the safe default until the
    Railway environment is deliberately changed.
    """

    mode = str(os.environ.get(FULL_MARKDOWN_MODE_ENV, "compact") or "compact").strip().lower()
    if mode in {"full", "all", "expanded", "on"} or mode in ORDERED_FULL_MARKDOWN_MODES:
        return True
    value = os.environ.get(FULL_MARKDOWN_TEST_ENV, "")
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "full"}


def ordered_full_markdown_mode():
    """Return whether all owned source files must be sent in fixed order.

    This is an explicit, reversible diagnostic switch. It bypasses compact
    document selection and the question's timing gate for source inclusion,
    but it does not bypass ownership, hash, size, JSON, or output validation.
    """

    mode = str(os.environ.get(FULL_MARKDOWN_MODE_ENV, "compact") or "compact").strip().lower()
    return mode in ORDERED_FULL_MARKDOWN_MODES


def full_source_context_mode():
    """Return whether normal chat must send the complete three-source context.

    The classifier is deliberately not part of this decision. ``all_full``
    is the production default; ``compact``/``selected`` are reversible
    rollback switches for operations, not question-routing behavior.
    """

    configured_mode = os.environ.get("VEDIC_GEMINI_SOURCE_CONTEXT_MODE")
    if configured_mode is None:
        # Keep the already-deployed ordered_full switch as the production
        # compatibility path. A local process with no provider setting stays
        # compact until its operator explicitly enables all_full.
        configured_mode = os.environ.get(FULL_MARKDOWN_MODE_ENV, "compact")
    mode = str(configured_mode or "compact").strip().lower()
    return mode in FULL_SOURCE_CONTEXT_MODES


def _sha256(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _frontmatter(document):
    if not document.startswith("---\n"):
        raise MethodologyOrchestrationError("methodology_frontmatter_missing")
    end = document.find("\n---\n", 4)
    if end < 0:
        raise MethodologyOrchestrationError("methodology_frontmatter_invalid")
    values = {}
    for line in document[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip('"\'')
    return values


def load_methodology_candidates(root=None):
    root_path = Path(root or Path(__file__).resolve().parent / "methodologies")
    candidates = []
    for expected in CANDIDATE_MANIFEST:
        path = root_path / expected["filename"]
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise MethodologyOrchestrationError("methodology_file_unavailable") from exc
        if not raw or len(raw) > MAX_METHODOLOGY_BYTES:
            raise MethodologyOrchestrationError("methodology_file_size_invalid")
        digest = _sha256(raw)
        if digest != expected["sha256"]:
            raise MethodologyOrchestrationError("methodology_checksum_mismatch")
        try:
            document = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MethodologyOrchestrationError("methodology_encoding_invalid") from exc
        metadata = _frontmatter(document)
        if metadata.get("document") != "SYSTEM_METHODOLOGY":
            raise MethodologyOrchestrationError("methodology_metadata_mismatch")
        if metadata.get("version") != expected["version"]:
            raise MethodologyOrchestrationError("methodology_metadata_mismatch")
        candidates.append({
            "id": expected["id"],
            "title": expected["title"],
            "version": expected["version"],
            "status": expected["status"],
            "sha256": digest,
            "document": document,
        })
    return candidates


def compact_evidence(draft):
    source = draft.get("evidence") or {}
    evidence = {
        "contract_version": "vedic-evidence-package-v1",
        "question": draft.get("question"),
        "topic": draft.get("topic"),
        "subject_topic": draft.get("subject_topic"),
        "question_route": draft.get("question_route"),
        "status": draft.get("status"),
        "confidence": draft.get("confidence"),
        "chart_summary": source.get("chart_summary"),
        "active_dasha": source.get("active_dasha"),
        "strength_summary": source.get("strength_summary"),
        "topic_packet": source.get("topic_packet"),
        "natal_sections": source.get("natal_sections") or [],
        "data_quality": source.get("data_quality"),
        "context_strategy": draft.get("context_strategy"),
        "missing": draft.get("missing") or [],
        "safety_notes": draft.get("safety_notes") or [],
    }
    if draft.get("topic") == "transit":
        evidence["transits"] = source.get("transits")
    # Normal PWA chat uses ``_full_markdown_sources``. The older
    # ``_full_markdown_test`` field remains supported only behind the explicit
    # diagnostic switch so existing callers do not silently change behavior.
    test_document = draft.get("_full_markdown_sources")
    if test_document is None and full_markdown_test_mode():
        test_document = draft.get("_full_markdown_test")
    if test_document:
        documents = test_document.get("documents") if isinstance(test_document, dict) else None
        if documents is None:
            documents = [test_document]
        if not isinstance(documents, list) or not documents:
            raise MethodologyOrchestrationError("full_markdown_test_document_invalid", 500)
        metadata = []
        content_parts = []
        for document in documents:
            if not isinstance(document, dict):
                raise MethodologyOrchestrationError("full_markdown_test_document_invalid", 500)
            content = document.get("content")
            if not isinstance(content, str) or not content:
                raise MethodologyOrchestrationError("full_markdown_test_document_empty", 500)
            filename = str(document.get("filename") or "unknown.md")
            metadata.append({
                "filename": filename,
                "byte_size": len(content.encode("utf-8")),
                "sha256": str(document.get("sha256") or ""),
                **({"source_path": str(document.get("source_path"))} if document.get("source_path") else {}),
            })
            content_parts.append(f"\n\n===== TAM DOSYA: {filename} =====\n\n{content}")
        evidence["full_markdown_sources"] = {
            "documents": metadata,
            "ordered": bool(draft.get("_full_markdown_sources")),
        }
        # Kept out of the canonical evidence JSON below; it is appended once
        # as a dedicated source section in both model prompts.
        evidence["_full_markdown_source_content"] = "".join(content_parts)
        # Compatibility aliases for existing instrumentation and fixtures.
        evidence["full_markdown_test"] = evidence["full_markdown_sources"]
        evidence["_full_markdown_test_content"] = evidence["_full_markdown_source_content"]
    return evidence


def _evidence_path_catalog(evidence):
    paths = []

    def walk(value, prefix):
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}"
                paths.append(path)
                walk(child, path)
        elif isinstance(value, list):
            # The array root remains a valid citation path. One representative
            # row documents shape without duplicating every table row in the
            # prompt path catalogue.
            children = value[:1]
            for index, child in enumerate(children):
                path = f"{prefix}.{index}"
                paths.append(path)
                walk(child, path)

    walk(evidence, "evidence")
    return sorted(paths)


def _model_request(candidate, evidence, conversation_context=None):
    full_markdown_content = evidence.get("_full_markdown_source_content")
    if full_markdown_content is None:
        full_markdown_content = evidence.get("_full_markdown_test_content")
    ordered_sources = bool(
        (evidence.get("full_markdown_sources") or {}).get("ordered")
    )
    prompt_evidence = {
        key: value
        for key, value in evidence.items()
        if key not in {"_full_markdown_source_content", "_full_markdown_test_content"}
    }
    evidence_json = _canonical_json(prompt_evidence)
    evidence_path_catalog_json = _canonical_json(_evidence_path_catalog(prompt_evidence))
    system_text = (
        "Yalnız aşağıdaki tek ve aktif Vedik/Jyotisha sistem metodolojisini uygula. "
        "Başka metodoloji, Batı/Tropical astroloji veya hesap uydurma kullanma. "
        "Sadece verilen kanıt paketindeki teknik gerçekleri yorumla. Eksik veri varsa açıkça sınırla. "
        "Metodolojide anılan fakat kanıt paketinde bulunmayan registry içeriğini uydurma. "
        "Önemli gökyüzü olayları veya tutulma istenirse evidence.transits.important_sky_events içindeki kaynak kayıtlarını kullan. "
        "Tarih, saat, derece, Rahu/Ketu-natal temas, tutulma nakshatra ya da pada hesaplama; kayıt yoksa missing_layers içine yaz ve analysis_status INCOMPLETE yap. "
        "Kanıt paketinde veya etkin tam Markdown kaynaklarında transit günleri/Panchanga varsa, "
        "sistemin tamamında bu verinin bulunmadığını söyleme; yalnız istenen tarih aralığı veya "
        "gönderilen kanıt kapsamı gerçekten dışındaysa sınır belirt. "
        "Sorunun sunucu tarafından doğrulanmış sınıflandırmasını evidence.question_route içinden oku; "
        "onu yeniden adlandırma veya başka konuya taşıma. Sonra doğru konu, veri kapısı ve zorunlu "
        "analiz sırasını uygula. "
        "SOHBET BAĞLAMI aynı açık sayfadaki önceki soru-cevaplarıdır; devam ifadelerini çözmek için "
        "kullan fakat astrolojik kanıt sayma. Geçmiş cevaptaki teknik iddiaları yalnız KANIT PAKETİ "
        "doğruluyorsa kullan. Yalnız güncel soruyu yanıtla. "
        "question_intent.primary_topic değeri kanıt paketindeki subject_topic ile birebir aynı olmalı; "
        "timing_required yalnız topic=transit ise true olmalı. "
        "Shadbala gezegen sıralamasında yalnız evidence.strength_summary içindeki strength_ratio kullanılır; "
        "legacy_raw_total gezegenler arası güç karşılaştırması değildir. "
        "mental_wellbeing veya wellbeing sorularında psikolojik/psikiyatrik teşhis, "
        "kişilik bozukluğu hükmü, klinik durum var/yok hükmü ya da kriz güvencesi üretme; yalnız sağlanan "
        "astrolojik örüntüyü teşhis dışı dille açıkla. "
        "Wellbeing konulu daily veya instant soruda ana summary içinde transit Ay'ı ve en az bir "
        "Panchanga bileşenini (Tithi, Vara, Nakshatra, Yoga veya Karana) değerlendir. Bunları birlikte "
        "adlandıran en az bir kanıt satırı gerçek daily_records veya instant_snapshot yolunu kullansın. "
        "Teknik analiz tamamlanmadan koçluk veya motivasyon ekleme. "
        "Yanıt yalnız geçerli JSON olsun.\n\n"
        f"METODOLOJİ KİMLİĞİ: {candidate['id']}@{candidate['version']}\n"
        f"METODOLOJİ SHA256: {candidate['sha256']}\n\n"
        f"METODOLOJİ BELGESİ:\n{candidate['document']}"
        + (
            "\n\nTAM KAYNAK BAĞLAMI ETKİN: Aşağıdaki tam Markdown dosyalarını ayrıntılı kaynak olarak kullan. "
            "İlgili teknik ayrıntıları özetine taşıyabilirsin; yalnız dosya ve kanıt paketinde bulunmayan bilgi ekleme."
            + (
                " Kaynak sırası sabittir: 1) bu metodoloji belgesi, 2) tam natal dosyası, "
                "3) tam üç aylık transit dosyası. Sıralamayı ve kapsamı daraltma."
                if ordered_full_markdown_mode() or ordered_sources
                else ""
            )
            if full_markdown_content is not None
            else ""
        )
    )
    full_markdown_section = ""
    if full_markdown_content is not None:
        full_markdown_section = (
            "\n\nTAM MARKDOWN KAYNAKLARI (ETKİN BAĞLAM MODU):\n"
            "Aşağıdaki içerikler kaynak Markdown dosyalarının eksiksiz metnidir. "
            "Soruyla ilgili ayrıntıları kullan; dosyalarda veya kanıt paketinde olmayan teknik veri üretme.\n"
            + (
                "Bu testte tam kaynak sırası: 1/3 metodoloji (systemInstruction içinde), "
                "2/3 natal, 3/3 üç aylık transit. Ara seçim/özetleme yapma.\n\n"
                if ordered_full_markdown_mode() or ordered_sources
                else "\n"
            )
            + f"{full_markdown_content}"
        )
    user_text = (
        "Aşağıdaki kanıt paketini metodolojiye göre eksiksiz incele. JSON alanları tam olarak şunlar olsun: "
        "question_intent (interpreted_question string, primary_topic string, timing_required boolean), "
        "analysis_status (COMPLETE|INCOMPLETE), methodology_coverage (array; her satır step, status ve note içerir), "
        "summary (Aşama 2 için ayrıntılı teknik hüküm; kullanıcıya gösterilecek nihai metin değil), "
        "supporting_evidence (claim ve evidence_path içeren array), "
        "challenging_evidence (claim ve evidence_path içeren array), missing_layers (string array), "
        "confidence (low|medium|high), limitations (string array). "
        "methodology_coverage şu adımların her birini tam bir kez ve bu sırada içermeli: "
        + ", ".join(REQUIRED_METHODOLOGY_STEPS)
        + ". status yalnız applied|not_applicable|missing olabilir. "
        "Zorunlu bir adım missing ise analysis_status INCOMPLETE olmalıdır. "
        "Her evidence_path evidence. ile başlamalı ve paketteki gerçek alana işaret etmelidir. "
        "Uzun zaman serilerindeki birden fazla satırı destekleyen iddia için dizinin kök yolunu "
        "(örneğin evidence.transits.daily_timing) kullan. "
        "Konu paketindeki houses, planets, lordships, yogas, vargas ve active_dasha alanları "
        "evidence.topic_packet.evidence altında bulunur; örneğin "
        "evidence.topic_packet.evidence.houses.0.occupants. "
        "Alan yolunu aşağıdaki geçerli yol kataloğundan eksiksiz kopyala; katalog dışında yol üretme.\n\n"
        f"GEÇERLİ EVIDENCE_PATH KATALOĞU:\n{evidence_path_catalog_json}\n\n"
        f"SOHBET BAĞLAMI (KANIT DEĞİLDİR):\n{_canonical_json(conversation_context or [])}\n\n"
        f"KANIT PAKETİ:\n{evidence_json}"
        f"{full_markdown_section}"
    )
    request = {
        "systemInstruction": {"parts": [{"text": system_text}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": TECHNICAL_MAX_OUTPUT_TOKENS,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }
    raw = _canonical_json(request).encode("utf-8")
    if len(raw) > MAX_PROMPT_BYTES:
        raise MethodologyOrchestrationError(
            "full_markdown_test_prompt_too_large" if full_markdown_content is not None else "methodology_prompt_too_large",
            413,
        )
    return request, _sha256(raw)


def _narrative_request(candidate, evidence, analysis, conversation_context=None):
    """Build the client-facing call from validated analysis and active sources."""

    full_markdown_content = evidence.get("_full_markdown_source_content")
    if full_markdown_content is None:
        full_markdown_content = evidence.get("_full_markdown_test_content")
    narrative_full_context = full_markdown_content
    ordered_sources = bool(
        (evidence.get("full_markdown_sources") or {}).get("ordered")
    )
    if (ordered_full_markdown_mode() or ordered_sources) and full_markdown_content is not None:
        # The technical call receives methodology in systemInstruction. The
        # client-facing call must also see all three verified source files.
        narrative_full_context = (
            "\n\n===== TAM DOSYA 1/3: SYSTEM_METHODOLOGY.txt =====\n\n"
            f"{candidate['document']}"
            f"{full_markdown_content}"
        )
    narrative_input = {
        "conversation_context": conversation_context or [],
        "question": evidence.get("question"),
        "question_route": evidence.get("question_route"),
        "analysis": analysis,
    }
    system_text = (
        "Sen Vedik AI'nin danışan anlatımı katmanısın. Astrolojik hesap veya yeni teknik analiz yapma. "
        "Sunucu tarafından doğrulanmış Aşama 1 JSON'unu ve etkin tam Markdown kaynaklarını doğal Türkiye Türkçesine çevir. "
        "Tam Markdown kaynakları verilmişse, soruyla ilgili teknik ayrıntıları, bağlantıları ve karşılaştırmaları açıklayabilirsin. "
        "Ancak kaynaklarda veya Aşama 1 kanıtında bulunmayan yeni teknik veri, olay, derece veya tarih üretme. "
        "conversation_context aynı açık sayfadaki önceki soru-cevaplarıdır; anlatımın devamlılığını "
        "korumak için kullan fakat oradan yeni astrolojik teknik iddia çıkarma. Yalnız güncel soruyu yanıtla. "
        "opening_summary alanında cevabın ana sonucunu kısa ve anlaşılır biçimde özetle; teknik terim kullanman "
        "gerekiyorsa kullan, fakat terimi danışanın anlayacağı cümleyle açıkla. answer alanında bu özeti aynen tekrarlamadan ayrıntılı "
        "yoruma geç. İlk paragrafta kullanıcının asıl sorusuna doğrudan ve koşullu cevap ver. Ardından sonucu oluşturan "
        "ana mekanizmaları, teknik bağlantıları, destekleyen ve zorlayan göstergeleri, güçlü tarafı, dikkat isteyen koşulu "
        "ve uygulanabilir rehberliği açıkla. "
        "timing_required true ise doğrulanmış zaman bulgusunu ve önümüzdeki süreci ayrı bir paragrafta açıkla; "
        "Önemli gökyüzü olayı veya tutulma istenmişse yalnız doğrulanmış transit kayıtlarındaki tarih, saat, derece, nakshatra, pada ve natal temasları anlat; "
        "bunlardan herhangi biri kaynakta yoksa hesaplama yapma ve eksik olduğunu açıkça söyle. "
        "false ise tarih veya gelecek garantisi üretme. Teknik kayıt listesini, evidence_path değerlerini, "
        "kaynakta transit günleri veya Panchanga varsa sistemde haftalık/günlük verinin hiç bulunmadığını "
        "iddia etme; yalnız gerçek tarih kapsamını ve varsa kapsanmayan günleri belirt. "
        "Wellbeing konulu daily veya instant yanıtta doğrulanmış transit Ay ve Panchanga bulgusunu doğal "
        "anlatı içinde açıkça değerlendir. "
        "Kanıt listesini veya evidence_path değerlerini ham biçimde dökme; karşıt bulguları sonucu dengeleyen koşullar "
        "olarak doğal cümlelere yansıt. Gerektiğinde başlıklar ve madde işaretleri kullan; bilgi kaybına yol açacak sabit "
        "paragraf, cümle veya karakter sınırı uygulama. "
        "Psikolojik ya da tıbbi teşhis koyma. Yalnız geçerli JSON döndür."
    )
    user_text = (
        "Aşağıdaki doğrulanmış teknik analiz ve etkin tam kaynaklardan kullanıcı cevabını üret. JSON yalnız "
        "opening_summary ve answer alanlarını içersin. opening_summary kısa bir sonuç özeti olsun; sabit cümle sayısı yoktur.\n\n"
        f"DOĞRULANMIŞ AŞAMA 1:\n{_canonical_json(narrative_input)}"
        + (
            "\n\nTAM KAYNAK SIRASI (3 DOSYANIN TAMAMI):\n"
            "1/3 metodoloji, 2/3 tam natal, 3/3 tam üç aylık transit. Ara seçim yapma.\n"
            f"{narrative_full_context}"
            if narrative_full_context is not None and (ordered_full_markdown_mode() or ordered_sources)
            else f"\n\nTAM MARKDOWN KAYNAKLARI:\n{narrative_full_context}"
            if narrative_full_context is not None
            else ""
        )
    )
    request = {
        "systemInstruction": {"parts": [{"text": system_text}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": NARRATIVE_MAX_OUTPUT_TOKENS,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }
    raw = _canonical_json(request).encode("utf-8")
    if len(raw) > MAX_PROMPT_BYTES:
        raise MethodologyOrchestrationError(
            "full_markdown_test_prompt_too_large" if full_markdown_content is not None else "methodology_narrative_prompt_too_large",
            413,
        )
    return request, _sha256(raw)


def _response_text(payload):
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MethodologyOrchestrationError("methodology_model_response_invalid", 502) from exc
    text = "".join(str(part.get("text") or "") for part in parts if isinstance(part, dict)).strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    if not text:
        raise MethodologyOrchestrationError("methodology_model_response_empty", 502)
    return text


def _decoded_response_object(payload):
    try:
        value = json.loads(_response_text(payload))
    except json.JSONDecodeError as exc:
        raise MethodologyOrchestrationError("methodology_model_json_invalid", 502) from exc
    if not isinstance(value, dict):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    return value


def _relaxed_evidence_rows(value):
    """Keep provider evidence shape without asserting paths in bypass mode."""

    if not isinstance(value, list):
        return []
    rows = []
    for item in value:
        if not isinstance(item, dict):
            continue
        rows.append({
            "claim": str(item.get("claim") or "").strip(),
            "evidence_path": str(item.get("evidence_path") or "").strip(),
        })
    return rows


def _relaxed_methodology_response(payload, evidence):
    """Normalize a parseable technical response while skipping semantic gates."""

    value = _decoded_response_object(payload)
    raw_intent = value.get("question_intent")
    intent = raw_intent if isinstance(raw_intent, dict) else {}
    subject_topic = str(evidence.get("subject_topic") or intent.get("primary_topic") or "unknown").strip()
    return {
        "question_intent": {
            "interpreted_question": str(
                intent.get("interpreted_question")
                or evidence.get("question")
                or ""
            ).strip(),
            "primary_topic": subject_topic,
            "timing_required": evidence.get("topic") == "transit",
        },
        "analysis_status": str(value.get("analysis_status") or "INCOMPLETE").strip().upper(),
        "methodology_coverage": value.get("methodology_coverage") if isinstance(value.get("methodology_coverage"), list) else [],
        "summary": str(value.get("summary") or "").strip(),
        "supporting_evidence": _relaxed_evidence_rows(value.get("supporting_evidence")),
        "challenging_evidence": _relaxed_evidence_rows(value.get("challenging_evidence")),
        "missing_layers": [str(item).strip() for item in value.get("missing_layers", []) if str(item).strip()]
        if isinstance(value.get("missing_layers"), list)
        else [],
        "confidence": str(value.get("confidence") or "medium").strip().lower(),
        "limitations": [str(item).strip() for item in value.get("limitations", []) if str(item).strip()]
        if isinstance(value.get("limitations"), list)
        else [],
        "validation_bypassed": True,
    }


def _relaxed_narrative_response(payload):
    """Keep a parseable narrative response without semantic/length gates."""

    value = _decoded_response_object(payload)
    answer = str(value.get("answer") or "").strip()
    if not answer:
        raise MethodologyOrchestrationError("methodology_narrative_response_empty", 502)
    return {
        "opening_summary": str(value.get("opening_summary") or "").strip(),
        "answer": answer,
        "validation_bypassed": True,
    }


def _evidence_path_exists(evidence, evidence_path):
    current = evidence
    for key in evidence_path.split(".")[1:]:
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        if isinstance(current, list) and key.isdigit():
            index = int(key)
            if index >= len(current):
                return False
            current = current[index]
            continue
        else:
            return False
    return True


def _canonical_evidence_path(evidence, evidence_path):
    if _evidence_path_exists(evidence, evidence_path):
        return evidence_path

    topic_prefix = "evidence.topic_packet."
    topic_evidence_prefix = "evidence.topic_packet.evidence."
    if evidence_path.startswith(topic_prefix) and not evidence_path.startswith(topic_evidence_prefix):
        suffix = evidence_path[len(topic_prefix):]
        candidate = f"{topic_evidence_prefix}{suffix}"
        if _evidence_path_exists(evidence, candidate):
            return candidate
    return None


def _evidence_rows(value, evidence):
    if not isinstance(value, list):
        raise MethodologyOrchestrationError("methodology_model_evidence_invalid", 502)
    rows = []
    for item in value:
        if not isinstance(item, dict):
            raise MethodologyOrchestrationError("methodology_model_evidence_invalid", 502)
        claim = str(item.get("claim") or "").strip()
        evidence_path = str(item.get("evidence_path") or "").strip()
        is_strength_claim = bool(
            re.search(r"\b(?:shadbala|strength_ratio)\b", claim, re.IGNORECASE)
        )
        strength_summary = evidence.get("strength_summary")
        if (
            is_strength_claim
            and isinstance(strength_summary, dict)
            and isinstance(strength_summary.get("ranking"), list)
            and strength_summary["ranking"]
        ):
            canonical_path = "evidence.strength_summary"
        else:
            canonical_path = (
                _canonical_evidence_path(evidence, evidence_path)
                if EVIDENCE_PATH_PATTERN.fullmatch(evidence_path)
                else None
            )
        if (
            not claim
            or not canonical_path
        ):
            raise MethodologyOrchestrationError("methodology_model_evidence_invalid", 502)
        rows.append({"claim": claim, "evidence_path": canonical_path})
    return rows


def _string_list(value):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise MethodologyOrchestrationError("methodology_model_list_invalid", 502)
    return [item.strip() for item in value if item.strip()]


def _validated_strength_claim(row, evidence):
    if not re.search(r"\b(?:shadbala|strength_ratio)\b", row["claim"], re.IGNORECASE):
        return row
    summary = evidence.get("strength_summary")
    ranking = summary.get("ranking") if isinstance(summary, dict) else None
    if not isinstance(ranking, list) or not ranking:
        raise MethodologyOrchestrationError("methodology_model_strength_invalid", 502)

    # The deterministic router supplies a ratio-sorted table. Models can pick
    # a nearby real path for a valid claim; bind it to the canonical table
    # instead of dropping the complete answer over citation formatting.
    return {**row, "evidence_path": "evidence.strength_summary"}


def _validate_timing_claim_tokens(summary, evidence_rows, evidence):
    """Reject explicit dates/degrees that do not exist in supplied evidence."""

    source_text = _canonical_json(evidence)
    answer_text = "\n".join([
        summary,
        *(row["claim"] for row in evidence_rows),
    ])
    source_dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", source_text))
    claimed_dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", answer_text))
    if not claimed_dates.issubset(source_dates):
        raise MethodologyOrchestrationError(
            "methodology_model_timing_evidence_invalid",
            502,
        )

    degree_pattern = r"(?<!\d)(\d{1,3}(?:[.,]\d{1,6})?)\s*°"
    source_degrees = {
        value.replace(",", ".").rstrip("0").rstrip(".")
        for value in re.findall(degree_pattern, source_text)
    }
    claimed_degrees = {
        value.replace(",", ".").rstrip("0").rstrip(".")
        for value in re.findall(degree_pattern, answer_text)
    }
    if not claimed_degrees.issubset(source_degrees):
        raise MethodologyOrchestrationError(
            "methodology_model_timing_evidence_invalid",
            502,
        )


def _validate_weekly_transit_evidence(evidence):
    """Require complete daily/Panchanga evidence for a short weekly window."""

    route = evidence.get("question_route") or {}
    if route.get("time_scope") != "range":
        return
    try:
        start = date.fromisoformat(str(route.get("target_start")))
        end = date.fromisoformat(str(route.get("target_end")))
    except (TypeError, ValueError):
        return
    day_count = (end - start).days + 1
    if not 1 <= day_count <= 7:
        return
    records = (evidence.get("transits") or {}).get("daily_records") or []
    if len(records) != day_count or any(not record.get("panchanga") for record in records):
        raise MethodologyOrchestrationError(
            "methodology_model_timing_evidence_invalid",
            502,
        )

def _validate_wellbeing_language(summary, evidence_rows, evidence):
    if evidence.get("subject_topic") != "wellbeing":
        return

    normalized_summary = summary.casefold()
    forbidden = (
        r"klinik\s+(?:bir\s+)?durum\s+değil",
        r"psikolojik\s+(?:bir\s+)?hastalık\s+değil",
        r"psikiyatrik\s+(?:bir\s+)?durum\s+değil",
        r"tedavi\s+gerektirmez",
    )
    if any(re.search(pattern, normalized_summary) for pattern in forbidden):
        raise MethodologyOrchestrationError(
            "methodology_model_wellbeing_safety_invalid",
            502,
        )

    question_route = evidence.get("question_route") or {}
    if question_route.get("time_scope") not in {"daily", "instant"}:
        return

    moon_pattern = re.compile(r"(?:\bay\b|\bay['’]|\bmoon\b)", re.IGNORECASE)
    panchanga_pattern = re.compile(
        r"\b(?:panchanga|tithi|vara|nakshatra|yoga|karana)\w*\b",
        re.IGNORECASE,
    )
    if not moon_pattern.search(summary) or not panchanga_pattern.search(summary):
        raise MethodologyOrchestrationError(
            "methodology_model_timing_evidence_invalid",
            502,
        )

    transit_rows = [
        row
        for row in evidence_rows
        if row["evidence_path"].startswith((
            "evidence.transits.daily_records",
            "evidence.transits.instant_snapshot",
        ))
    ]
    has_moon_citation = any(moon_pattern.search(row["claim"]) for row in transit_rows)
    has_panchanga_citation = any(
        panchanga_pattern.search(row["claim"])
        for row in transit_rows
    )
    if not has_moon_citation or not has_panchanga_citation:
        raise MethodologyOrchestrationError(
            "methodology_model_timing_evidence_invalid",
            502,
        )


def _validate_global_transit_absence_claim(text, evidence):
    """Reject a system-wide absence claim when transit evidence is present."""

    transits = evidence.get("transits") or {}
    if not (transits.get("daily_records") or transits.get("daily_timing")):
        return
    normalized = str(text or "").replace("İ", "i").casefold()
    patterns = (
        r"sistem(?:imizde)?[^.\n]{0,100}(?:haftalık|günlük|transit|panchanga)[^.\n]{0,50}(?:yok|bulunmuyor|mevcut değil|bulunmamaktadır)",
        r"(?:haftalık|günlük|transit|panchanga)[^.\n]{0,80}(?:sistem(?:imizde)?)[^.\n]{0,50}(?:yok|bulunmuyor|mevcut değil|bulunmamaktadır)",
    )
    if any(re.search(pattern, normalized) for pattern in patterns):
        raise MethodologyOrchestrationError(
            "methodology_narrative_timing_evidence_invalid",
            502,
        )


def _wellbeing_timing_fact(evidence):
    if evidence.get("subject_topic") != "wellbeing":
        return None
    question_route = evidence.get("question_route") or {}
    scope = question_route.get("time_scope")
    if scope not in {"daily", "instant"}:
        return None

    transits = evidence.get("transits") or {}
    if scope == "instant":
        record = transits.get("instant_snapshot") or {}
        evidence_path = "evidence.transits.instant_snapshot.panchanga"
        if not record:
            records = transits.get("daily_records") or []
            record = records[0] if records else {}
            evidence_path = "evidence.transits.daily_records.0.panchanga"
    else:
        records = transits.get("daily_records") or []
        record = records[0] if records else {}
        evidence_path = "evidence.transits.daily_records.0.panchanga"
    panchanga = record.get("panchanga") or {}
    planets = record.get("planets") or []
    moon = next(
        (
            planet for planet in planets
            if str(planet.get("name") or "").casefold() == "moon"
        ),
        {},
    )
    nakshatra = panchanga.get("moon_nakshatra") or {}
    tithi = panchanga.get("tithi") or {}
    vara = panchanga.get("vara") or {}
    moon_sign = moon.get("sign_tr") or moon.get("sign")
    nakshatra_name = nakshatra.get("name")
    tithi_name = tithi.get("name") or tithi.get("sanskrit")
    vara_name = vara.get("sanskrit") or vara.get("name")
    if not nakshatra_name or not (tithi_name or vara_name):
        return None

    location = f" {moon_sign} burcunda" if moon_sign else ""
    calendar_parts = [
        f"Tithi {tithi_name}" if tithi_name else None,
        f"Vara {vara_name}" if vara_name else None,
    ]
    calendar_text = ", ".join(item for item in calendar_parts if item)
    claim = (
        f"Transit Ay{location} {nakshatra_name} nakshatrasında; "
        f"Panchanga kaydında {calendar_text}."
    )
    return {"claim": claim, "evidence_path": evidence_path}


def _ensure_wellbeing_timing_evidence(summary, supporting_evidence, evidence):
    fact = _wellbeing_timing_fact(evidence)
    if not fact:
        return summary, supporting_evidence
    moon_pattern = re.compile(r"(?:\bay\b|\bay['’]|\bmoon\b)", re.IGNORECASE)
    panchanga_pattern = re.compile(
        r"\b(?:panchanga|tithi|vara|nakshatra|yoga|karana)\w*\b",
        re.IGNORECASE,
    )
    if not moon_pattern.search(summary) or not panchanga_pattern.search(summary):
        summary = f"{summary.rstrip()} {fact['claim']}"
    cited_claims = "\n".join(row["claim"] for row in supporting_evidence)
    if not moon_pattern.search(cited_claims) or not panchanga_pattern.search(cited_claims):
        supporting_evidence = [*supporting_evidence, fact]
    return summary, supporting_evidence


def validate_methodology_response(payload, evidence):
    try:
        value = json.loads(_response_text(payload))
    except json.JSONDecodeError as exc:
        raise MethodologyOrchestrationError("methodology_model_json_invalid", 502) from exc
    if not isinstance(value, dict):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    question_intent = value.get("question_intent")
    analysis_status = str(value.get("analysis_status") or "").strip().upper()
    coverage = value.get("methodology_coverage")
    if not isinstance(question_intent, dict):
        raise MethodologyOrchestrationError("methodology_model_intent_invalid", 502)
    interpreted_question = str(question_intent.get("interpreted_question") or "").strip()
    primary_topic = str(question_intent.get("primary_topic") or "").strip()
    timing_required = question_intent.get("timing_required")
    if not interpreted_question or not primary_topic or not isinstance(timing_required, bool):
        raise MethodologyOrchestrationError("methodology_model_intent_invalid", 502)
    expected_topic = str(evidence.get("subject_topic") or "").strip()
    expected_timing = evidence.get("topic") == "transit"
    if not expected_topic:
        raise MethodologyOrchestrationError("methodology_model_intent_invalid", 502)
    # Topic and timing are deterministic router decisions. The model still
    # explains its interpretation, but a synonymous or package-code label must
    # not override the server's selected subject or make a valid analysis fail.
    primary_topic = expected_topic
    timing_required = expected_timing
    if analysis_status not in {"COMPLETE", "INCOMPLETE"} or not isinstance(coverage, list):
        raise MethodologyOrchestrationError("methodology_model_coverage_invalid", 502)
    normalized_coverage = []
    for expected_step, row in zip(REQUIRED_METHODOLOGY_STEPS, coverage, strict=False):
        if not isinstance(row, dict):
            raise MethodologyOrchestrationError("methodology_model_coverage_invalid", 502)
        step = str(row.get("step") or "").strip()
        status = str(row.get("status") or "").strip()
        note = str(row.get("note") or "").strip()
        if step != expected_step or status not in COVERAGE_STATUSES or not note:
            raise MethodologyOrchestrationError("methodology_model_coverage_invalid", 502)
        normalized_coverage.append({"step": step, "status": status, "note": note})
    if len(coverage) != len(REQUIRED_METHODOLOGY_STEPS):
        raise MethodologyOrchestrationError("methodology_model_coverage_invalid", 502)
    if any(row["status"] == "missing" for row in normalized_coverage) and analysis_status != "INCOMPLETE":
        raise MethodologyOrchestrationError("methodology_model_coverage_invalid", 502)
    summary = str(value.get("summary") or "").strip()
    confidence = str(value.get("confidence") or "").strip().lower()
    if not summary or confidence not in CONFIDENCE_LEVELS:
        raise MethodologyOrchestrationError("methodology_model_summary_invalid", 502)
    supporting_evidence = _evidence_rows(value.get("supporting_evidence"), evidence)
    challenging_evidence = _evidence_rows(value.get("challenging_evidence"), evidence)
    supporting_evidence = [
        _validated_strength_claim(row, evidence) for row in supporting_evidence
    ]
    challenging_evidence = [
        _validated_strength_claim(row, evidence) for row in challenging_evidence
    ]
    summary, supporting_evidence = _ensure_wellbeing_timing_evidence(
        summary,
        supporting_evidence,
        evidence,
    )
    if expected_timing:
        _validate_weekly_transit_evidence(evidence)
        cited_paths = {
            row["evidence_path"]
            for row in [*supporting_evidence, *challenging_evidence]
        }
        if not any(path.startswith("evidence.transits") for path in cited_paths):
            raise MethodologyOrchestrationError("methodology_model_timing_evidence_invalid", 502)
        coverage_by_step = {row["step"]: row["status"] for row in normalized_coverage}
        if coverage_by_step.get("transit_trigger") != "applied":
            raise MethodologyOrchestrationError("methodology_model_timing_evidence_invalid", 502)
        _validate_timing_claim_tokens(
            summary,
            [*supporting_evidence, *challenging_evidence],
            evidence,
        )
    _validate_wellbeing_language(
        summary,
        [*supporting_evidence, *challenging_evidence],
        evidence,
    )
    return {
        "question_intent": {
            "interpreted_question": interpreted_question,
            "primary_topic": primary_topic,
            "timing_required": timing_required,
        },
        "analysis_status": analysis_status,
        "methodology_coverage": normalized_coverage,
        "summary": summary,
        "supporting_evidence": supporting_evidence,
        "challenging_evidence": challenging_evidence,
        "missing_layers": _string_list(value.get("missing_layers")),
        "confidence": confidence,
        "limitations": _string_list(value.get("limitations")),
    }


def validate_narrative_response(payload, analysis, evidence):
    try:
        response_text = _response_text(payload)
    except MethodologyOrchestrationError as exc:
        code = (
            "methodology_narrative_response_empty"
            if exc.code == "methodology_model_response_empty"
            else "methodology_narrative_response_invalid"
        )
        raise MethodologyOrchestrationError(code, 502) from exc
    try:
        value = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise MethodologyOrchestrationError("methodology_narrative_json_invalid", 502) from exc
    if not isinstance(value, dict) or set(value) != {"opening_summary", "answer"}:
        raise MethodologyOrchestrationError("methodology_narrative_schema_invalid", 502)
    opening_summary = str(value.get("opening_summary") or "").strip()
    answer = str(value.get("answer") or "").strip()
    if not opening_summary or not answer:
        raise MethodologyOrchestrationError("methodology_narrative_response_empty", 502)
    opening_sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", opening_summary)
        if item.strip()
    ]
    if (
        "\n" in opening_summary
        or len(opening_summary) < 20
        or len(opening_summary) > 1_500
        or not (1 <= len(opening_sentences) <= 5)
        or any(not re.search(r"[.!?]$", item) for item in opening_sentences)
    ):
        raise MethodologyOrchestrationError(
            "methodology_narrative_opening_summary_invalid",
            502,
        )
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", answer) if item.strip()]
    if len(answer) < NARRATIVE_MIN_CHARS or len(paragraphs) < NARRATIVE_MIN_PARAGRAPHS:
        raise MethodologyOrchestrationError("methodology_narrative_too_short", 502)

    combined_text = f"{opening_summary}\n{answer}"
    normalized_answer = combined_text.replace("İ", "i").casefold()
    forbidden_markers = (
        "vedik analiz sistem metodolojisi",
        "evidence.",
        "methodology_coverage",
        "supporting_evidence",
        "challenging_evidence",
        "rul-",
        "künye:",
    )
    if any(marker in normalized_answer for marker in forbidden_markers):
        raise MethodologyOrchestrationError(
            "methodology_narrative_technical_leak",
            502,
        )

    evidence_rows = [
        *(analysis.get("supporting_evidence") or []),
        *(analysis.get("challenging_evidence") or []),
    ]
    if (analysis.get("question_intent") or {}).get("timing_required"):
        try:
            _validate_timing_claim_tokens(combined_text, evidence_rows, evidence)
        except MethodologyOrchestrationError as exc:
            raise MethodologyOrchestrationError(
                "methodology_narrative_timing_evidence_invalid",
                502,
            ) from exc
    _validate_global_transit_absence_claim(combined_text, evidence)
    _validate_wellbeing_language(combined_text, evidence_rows, evidence)
    return {
        "opening_summary": opening_summary,
        "answer": answer,
    }


def _usage(payload):
    usage = payload.get("usageMetadata") or {}
    return {
        "prompt_tokens": usage.get("promptTokenCount"),
        "response_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
        "model_version": payload.get("modelVersion"),
    }


def _combined_usage(technical_payload, narrative_payload):
    technical = _usage(technical_payload)
    narrative = _usage(narrative_payload)

    def add(field):
        values = [technical.get(field), narrative.get(field)]
        numeric = [value for value in values if isinstance(value, (int, float))]
        return sum(numeric) if numeric else None

    return {
        "prompt_tokens": add("prompt_tokens"),
        "response_tokens": add("response_tokens"),
        "total_tokens": add("total_tokens"),
        "model_version": narrative.get("model_version") or technical.get("model_version"),
        "technical": technical,
        "narrative": narrative,
    }


def _run_candidate(
    candidate,
    comparison_id,
    evidence,
    evidence_sha256,
    model_call,
    clock,
    conversation_context=None,
):
    base_request_id = f"{comparison_id}-{candidate['id']}"
    validation_mode = methodology_validation_mode()
    request, technical_prompt_sha256 = _model_request(
        candidate,
        evidence,
        conversation_context,
    )
    started = clock()
    technical_payload = None
    technical_analysis = None
    technical_request_id = None
    technical_attempt_count = 0
    for attempt_index in range(2):
        request_id = (
            f"{base_request_id}-analysis"
            if attempt_index == 0
            else f"{base_request_id}-analysis-retry-{attempt_index}"
        )
        try:
            returned_request_id, payload = model_call(request_id, request)
            if returned_request_id != request_id or not isinstance(payload, dict):
                raise MethodologyOrchestrationError("methodology_model_response_invalid", 502)
            analysis = (
                _relaxed_methodology_response(payload, evidence)
                if validation_mode == "bypass"
                else validate_methodology_response(payload, evidence)
            )
            technical_payload = payload
            technical_analysis = analysis
            technical_request_id = request_id
            technical_attempt_count = attempt_index + 1
            break
        except Exception as exc:
            if not isinstance(exc, MethodologyOrchestrationError) and not hasattr(exc, "code"):
                raise
            code = (
                exc.code
                if isinstance(exc, MethodologyOrchestrationError)
                else getattr(exc, "code", "methodology_model_failed")
            )
            if attempt_index == 0 and code in RETRYABLE_RESPONSE_ERRORS:
                continue
            return {
                "status": "failed",
                "methodology": {key: candidate[key] for key in ("id", "title", "version", "status", "sha256")},
                "request_id": request_id,
                "attempt_count": attempt_index + 1,
                "evidence_sha256": evidence_sha256,
                "prompt_sha256": technical_prompt_sha256,
                "latency_ms": max(round((clock() - started) * 1000), 0),
                "validation_mode": validation_mode,
                "error": code if str(code).startswith(("methodology_", "vertex_")) else "methodology_model_failed",
            }

    narrative_request, narrative_prompt_sha256 = _narrative_request(
        candidate,
        evidence,
        technical_analysis,
        conversation_context,
    )
    for attempt_index in range(2):
        narrative_request_id = (
            f"{base_request_id}-narrative"
            if attempt_index == 0
            else f"{base_request_id}-narrative-retry-{attempt_index}"
        )
        try:
            returned_request_id, narrative_payload = model_call(
                narrative_request_id,
                narrative_request,
            )
            if returned_request_id != narrative_request_id or not isinstance(narrative_payload, dict):
                raise MethodologyOrchestrationError("methodology_narrative_response_invalid", 502)
            narrative = (
                _relaxed_narrative_response(narrative_payload)
                if validation_mode == "bypass"
                else validate_narrative_response(
                    narrative_payload,
                    technical_analysis,
                    evidence,
                )
            )
            analysis = {
                **technical_analysis,
                "technical_summary": technical_analysis["summary"],
                "opening_summary": narrative["opening_summary"],
                "summary": narrative["answer"],
            }
            return {
                "status": "completed",
                "methodology": {key: candidate[key] for key in ("id", "title", "version", "status", "sha256")},
                "request_id": narrative_request_id,
                "technical_request_id": technical_request_id,
                "narrative_request_id": narrative_request_id,
                "attempt_count": technical_attempt_count + attempt_index + 1,
                "technical_attempt_count": technical_attempt_count,
                "narrative_attempt_count": attempt_index + 1,
                "evidence_sha256": evidence_sha256,
                "prompt_sha256": narrative_prompt_sha256,
                "technical_prompt_sha256": technical_prompt_sha256,
                "narrative_prompt_sha256": narrative_prompt_sha256,
                "latency_ms": max(round((clock() - started) * 1000), 0),
                "usage": _combined_usage(technical_payload, narrative_payload),
                "analysis": analysis,
                "validation_mode": validation_mode,
            }
        except Exception as exc:
            if not isinstance(exc, MethodologyOrchestrationError) and not hasattr(exc, "code"):
                raise
            code = (
                exc.code
                if isinstance(exc, MethodologyOrchestrationError)
                else getattr(exc, "code", "methodology_narrative_failed")
            )
            if attempt_index == 0 and code in RETRYABLE_NARRATIVE_ERRORS:
                continue
            return {
                "status": "failed",
                "methodology": {key: candidate[key] for key in ("id", "title", "version", "status", "sha256")},
                "request_id": narrative_request_id,
                "technical_request_id": technical_request_id,
                "narrative_request_id": narrative_request_id,
                "attempt_count": technical_attempt_count + attempt_index + 1,
                "technical_attempt_count": technical_attempt_count,
                "narrative_attempt_count": attempt_index + 1,
                "evidence_sha256": evidence_sha256,
                "prompt_sha256": narrative_prompt_sha256,
                "technical_prompt_sha256": technical_prompt_sha256,
                "narrative_prompt_sha256": narrative_prompt_sha256,
                "latency_ms": max(round((clock() - started) * 1000), 0),
                "validation_mode": validation_mode,
                "error": code if str(code).startswith(("methodology_", "vertex_")) else "methodology_narrative_failed",
            }


def run_methodology_comparison(draft, comparison_id, model_call, *, candidates_root=None, clock=None):
    candidates = load_methodology_candidates(candidates_root)
    evidence = compact_evidence(draft)
    conversation_context = draft.get("conversation_context") or []
    evidence_json = _canonical_json(evidence)
    evidence_sha256 = _sha256(evidence_json)
    monotonic = clock or time.monotonic
    with ThreadPoolExecutor(max_workers=len(candidates), thread_name_prefix="vedic-methodology") as executor:
        results = list(executor.map(
            lambda candidate: _run_candidate(
                candidate,
                comparison_id,
                evidence,
                evidence_sha256,
                model_call,
                monotonic,
                conversation_context,
            ),
            candidates,
        ))

    completed = sum(result["status"] == "completed" for result in results)
    comparison_status = "comparison_ready" if completed == len(results) else "partial" if completed else "failed"
    return {
        "contract_version": CONTRACT_VERSION,
        "validation_mode": methodology_validation_mode(),
        "comparison_id": comparison_id,
        "status": comparison_status,
        "question": draft.get("question"),
        "topic": draft.get("topic"),
        "subject_topic": draft.get("subject_topic"),
        "question_route": draft.get("question_route"),
        "routing_comparison": draft.get("routing_comparison"),
        "context_trace": draft.get("context_trace"),
        "evidence_sha256": evidence_sha256,
        "methodology_order": [item["id"] for item in CANDIDATE_MANIFEST],
        "methodology_results": results,
        "selection": CANDIDATE_MANIFEST[0]["id"],
        "selection_status": "system_methodology_active",
        "completed_count": completed,
        "candidate_count": len(results),
    }


def new_comparison_id():
    return f"methodology-compare-{uuid.uuid4()}"
