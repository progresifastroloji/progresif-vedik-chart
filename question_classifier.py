"""Gemini-backed, schema-limited question classification for Vedik AI.

The classifier never reads chart files and never makes astrological claims. It
only converts the user's natural-language question into a small allow-listed
routing decision. The application server remains responsible for ownership,
artifact access, evidence selection, calculations, and methodology execution.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta


CONTRACT_VERSION = "vedic-question-route-v1"
ALLOWED_TOPICS = {
    "general",
    "character",
    "career",
    "marriage",
    "wealth",
    "health",
    "spiritual",
    "wellbeing",
}
ALLOWED_TIME_SCOPES = {"none", "instant", "daily", "range"}
ALLOWED_EVIDENCE = {
    "natal_core",
    "natal_emotional_core",
    "topic_packet",
    "active_dasha",
    "stored_transit_days",
    "current_transit_snapshot",
    "moon_and_panchanga",
    "transit_natal_contacts",
    "ashtakavarga",
    "relevant_vargas",
    "important_sky_events",
    "eclipse_events",
    "eclipse_nakshatra",
    "eclipse_pada",
    "sky_event_natal_contacts",
}
ALLOWED_SENSITIVITY = {
    "standard",
    "mental_wellbeing",
    "medical",
    "financial",
    "legal",
    "crisis",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

IMPORTANT_SKY_EVENT_PHRASES = (
    "ay tutulması", "ay tutulmasi", "güneş tutulması", "gunes tutulmasi",
    "tutulma", "eclipse", "gökyüzündeki önemli",
    "gokyuzundeki onemli", "önemli gökyüzü", "onemli gokyuzu",
)
ECLIPSE_PHRASES = (
    "ay tutulması", "ay tutulmasi", "güneş tutulması", "gunes tutulmasi",
    "tutulma", "eclipse",
)
NODE_EVENT_MARKERS = (
    "transit", "kavuşum", "kavusum", "temas", "geçiş", "gecis",
    "retro", "gökyüzü", "gokyuzu", "yaklaş", "yaklas",
)


def _question_text(question):
    return str(question or "").replace("İ", "i").casefold()


def event_evidence_for_question(question):
    """Return evidence labels for a named sky event; never calculate it."""

    text = _question_text(question)
    named_event = any(phrase in text for phrase in IMPORTANT_SKY_EVENT_PHRASES)
    node_event = (
        ("rahu" in text or "ketu" in text)
        and any(marker in text for marker in NODE_EVENT_MARKERS)
    )
    if not named_event and not node_event:
        return set()
    evidence = {"important_sky_events", "sky_event_natal_contacts"}
    if any(phrase in text for phrase in ECLIPSE_PHRASES):
        evidence.update({"eclipse_events", "eclipse_nakshatra", "eclipse_pada"})
    return evidence


def _explicit_weekly_range(question, now_iso):
    """Return the calendar week explicitly requested by the user, if any.

    Gemini remains the semantic topic classifier. This helper is only a
    server-side safety invariant for unambiguous calendar phrases, so a model
    omission cannot silently remove the transit evidence required by the
    question.
    """

    text = _question_text(question)
    weekly_next = any(
        phrase in text
        for phrase in (
            "önümüzdeki hafta",
            "gelecek hafta",
            "önümüzdeki haftanın",
            "gelecek haftanın",
        )
    )
    weekly_current = any(
        phrase in text
        for phrase in ("bu hafta", "bu haftanın")
    )
    seven_days = any(
        phrase in text
        for phrase in ("önümüzdeki 7 gün", "önümüzdeki yedi gün", "gün gün")
    )
    if not (weekly_next or weekly_current or seven_days):
        return None

    current_day = datetime.fromisoformat(str(now_iso).replace("Z", "+00:00")).date()
    if seven_days and not weekly_next and not weekly_current:
        start = current_day
        end = current_day + timedelta(days=6)
    else:
        monday = current_day - timedelta(days=current_day.weekday())
        start = monday + timedelta(days=7 if weekly_next else 0)
        end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def enforce_explicit_time_scope(value, question, now_iso):
    """Enforce only explicit calendar timing; never change the topic choice."""

    if not isinstance(value, dict):
        return value
    weekly_range = _explicit_weekly_range(question, now_iso)
    if not weekly_range:
        return value
    normalized = dict(value)
    start, end = weekly_range
    normalized["time_scope"] = "range"
    normalized["timing_required"] = True
    normalized["target_start"] = start
    normalized["target_end"] = end
    normalized["target_datetime"] = None
    primary_topic = str(normalized.get("primary_topic") or "").strip()
    evidence = normalized.get("required_evidence")
    if isinstance(evidence, list) and primary_topic in ALLOWED_TOPICS:
        normalized["required_evidence"] = sorted(
            set(evidence) | _required_evidence_for(primary_topic, "range")
        )
    return normalized


def _required_evidence_for(primary_topic, time_scope):
    required = {"natal_core", "active_dasha"}
    if primary_topic == "wellbeing":
        required.add("natal_emotional_core")
    if time_scope != "none":
        required.update({
            "stored_transit_days",
            "transit_natal_contacts",
            "ashtakavarga",
        })
    if time_scope in {"daily", "instant"}:
        required.add("moon_and_panchanga")
    if time_scope == "instant":
        required.add("current_transit_snapshot")
    return required


def normalize_classification(value, question, now_iso):
    """Repair bounded model omissions without granting file or chart authority.

    Gemini remains the semantic classifier. The server only enforces explicit
    time phrases, explicit career/relationship context, required evidence
    minima, and internally supplied current time.
    """

    if not isinstance(value, dict):
        return value
    normalized = dict(value)
    # Turkish capital dotted-I casefolds to ``i`` plus a combining dot, which
    # would split words such as "İşimde" during tokenization.
    question_text = _question_text(question)
    tokens = set(re.findall(r"\w+", question_text, flags=re.UNICODE))
    event_evidence = event_evidence_for_question(question)

    career_context = any(
        token in {
            "iş", "işim", "işimde", "işte",
            "meslek", "mesleğim", "mesleğimde",
        }
        or token.startswith("kariyer")
        for token in tokens
    )
    relationship_context = any(
        token in {
            "eş", "eşim", "eşimle", "sevgili", "sevgilim", "sevgilimle",
            "partner", "partnerim", "ilişki", "evlilik", "flört", "flörtüm",
            "çıktığım", "ciktigim", "adamla", "kadınla", "kadinla",
        }
        or token.startswith("ilişki")
        or token.startswith("evlili")
        or token.startswith("evlen")
        for token in tokens
    )
    emotional_context = any(
        token.startswith(("hisset", "gergin", "mutsuz", "kayg", "endiş", "motivasyon"))
        for token in tokens
    )

    if career_context:
        normalized["primary_topic"] = "career"
    elif relationship_context:
        normalized["primary_topic"] = "marriage"
    elif emotional_context:
        normalized["primary_topic"] = "wellbeing"

    explicit_instant = (
        any(
            phrase in question_text
            for phrase in ("şu anda", "su anda", "tam şimdi")
        )
        or "şimdi" in tokens
    )
    explicit_daily = "bugün" in tokens or "bugun" in tokens
    future_modal = bool(re.search(
        r"\b(?:evlenebilir|gerçekleşir|gerceklesir|etkileyecek|etkiler|olacak\s+mı|olacak\s+mi|ne\s+zaman)\b",
        question_text,
    ))
    if explicit_instant:
        normalized["time_scope"] = "instant"
    elif explicit_daily:
        normalized["time_scope"] = "daily"
    elif future_modal and normalized.get("time_scope") == "none":
        normalized["time_scope"] = "range"
    elif event_evidence and normalized.get("time_scope") == "none":
        # A named sky event is a timing request even without an exact date.
        # The stored transit horizon is used; absent event records fail closed.
        normalized["time_scope"] = "range"
    elif emotional_context and normalized.get("time_scope") == "instant":
        # A present-tense feeling is not automatically an hour-specific
        # transit question. Instant mode requires an explicit "now" signal.
        normalized["time_scope"] = "none"

    time_scope = str(normalized.get("time_scope") or "").strip()
    primary_topic = str(normalized.get("primary_topic") or "").strip()
    normalized["timing_required"] = time_scope != "none"
    if time_scope == "none":
        normalized["target_start"] = None
        normalized["target_end"] = None
        normalized["target_datetime"] = None
    elif time_scope == "daily":
        current_day = (
            datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
            .date()
            .isoformat()
        )
        normalized["target_start"] = current_day
        normalized["target_end"] = current_day
        normalized["target_datetime"] = None
    elif time_scope == "instant":
        normalized["target_start"] = None
        normalized["target_end"] = None
        normalized["target_datetime"] = str(now_iso)
    elif time_scope == "range":
        current_day = (
            datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
            .date()
        )
        range_start = normalized.get("target_start") or current_day.isoformat()
        normalized["target_start"] = range_start
        normalized["target_end"] = normalized.get("target_end") or (
            date.fromisoformat(str(range_start)) + timedelta(days=91)
        ).isoformat()
        normalized["target_datetime"] = None

    evidence = normalized.get("required_evidence")
    if isinstance(evidence, list):
        evidence_set = set(evidence)
        evidence_set.update(_required_evidence_for(primary_topic, time_scope))
        evidence_set.update(event_evidence)
        normalized["required_evidence"] = sorted(evidence_set)

    if (
        primary_topic == "wellbeing"
        and normalized.get("sensitivity") in {None, "", "standard", "medical"}
    ):
        normalized["sensitivity"] = "mental_wellbeing"
    return enforce_explicit_time_scope(normalized, question, now_iso)


class QuestionClassificationError(Exception):
    """Stable, non-provider-specific classification failure."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _response_text(payload):
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise QuestionClassificationError("question_classifier_response_invalid") from exc
    text = "".join(
        str(part.get("text") or "")
        for part in parts
        if isinstance(part, dict)
    ).strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    if not text:
        raise QuestionClassificationError("question_classifier_response_empty")
    return text


def _iso_date(value, field, *, required=False):
    text = str(value or "").strip()
    if not text:
        if required:
            raise QuestionClassificationError(f"question_classifier_{field}_required")
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise QuestionClassificationError(f"question_classifier_{field}_invalid") from exc


def _iso_datetime(value, *, required=False):
    text = str(value or "").strip()
    if not text:
        if required:
            raise QuestionClassificationError("question_classifier_target_datetime_required")
        return None
    if text.casefold() == "now":
        return "now"
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
    except ValueError as exc:
        raise QuestionClassificationError("question_classifier_target_datetime_invalid") from exc


def validate_classification(value):
    if not isinstance(value, dict):
        raise QuestionClassificationError("question_classifier_schema_invalid")

    allowed_keys = {
        "interpreted_question", "primary_topic", "time_scope", "timing_required",
        "target_start", "target_end", "target_datetime", "required_evidence",
        "sensitivity", "confidence", "clarification_required",
        "clarification_question",
    }
    if set(value) - allowed_keys:
        raise QuestionClassificationError("question_classifier_schema_invalid")

    interpreted_question = str(value.get("interpreted_question") or "").strip()
    primary_topic = str(value.get("primary_topic") or "").strip()
    time_scope = str(value.get("time_scope") or "").strip()
    timing_required = value.get("timing_required")
    required_evidence = value.get("required_evidence")
    sensitivity = str(value.get("sensitivity") or "").strip()
    confidence = str(value.get("confidence") or "").strip()
    clarification_required = value.get("clarification_required")
    clarification_question = str(value.get("clarification_question") or "").strip() or None

    if not interpreted_question:
        raise QuestionClassificationError("question_classifier_interpretation_invalid")
    if primary_topic not in ALLOWED_TOPICS:
        raise QuestionClassificationError("question_classifier_topic_invalid")
    if time_scope not in ALLOWED_TIME_SCOPES:
        raise QuestionClassificationError("question_classifier_time_scope_invalid")
    if not isinstance(timing_required, bool) or timing_required != (time_scope != "none"):
        raise QuestionClassificationError("question_classifier_timing_invalid")
    if (
        not isinstance(required_evidence, list)
        or not required_evidence
        or any(item not in ALLOWED_EVIDENCE for item in required_evidence)
        or len(set(required_evidence)) != len(required_evidence)
    ):
        raise QuestionClassificationError("question_classifier_evidence_invalid")
    required_layers = _required_evidence_for(primary_topic, time_scope)
    if not required_layers.issubset(set(required_evidence)):
        raise QuestionClassificationError("question_classifier_evidence_invalid")
    if sensitivity not in ALLOWED_SENSITIVITY:
        raise QuestionClassificationError("question_classifier_sensitivity_invalid")
    if confidence not in ALLOWED_CONFIDENCE:
        raise QuestionClassificationError("question_classifier_confidence_invalid")
    if not isinstance(clarification_required, bool):
        raise QuestionClassificationError("question_classifier_clarification_invalid")
    if clarification_required and not clarification_question:
        raise QuestionClassificationError("question_classifier_clarification_invalid")

    target_start = _iso_date(
        value.get("target_start"),
        "target_start",
        required=time_scope in {"daily", "range"},
    )
    target_end = _iso_date(
        value.get("target_end"),
        "target_end",
        required=time_scope == "range",
    )
    target_datetime = _iso_datetime(
        value.get("target_datetime"),
        required=time_scope == "instant",
    )
    if time_scope == "daily":
        target_end = target_start
    if time_scope == "range":
        start = date.fromisoformat(target_start)
        end = date.fromisoformat(target_end)
        if end < start or (end - start).days > 366:
            raise QuestionClassificationError("question_classifier_range_invalid")
    if time_scope == "none" and any((target_start, target_end, target_datetime)):
        raise QuestionClassificationError("question_classifier_time_scope_invalid")

    return {
        "contract_version": CONTRACT_VERSION,
        "interpreted_question": interpreted_question,
        "primary_topic": primary_topic,
        "time_scope": time_scope,
        "timing_required": timing_required,
        "target_start": target_start,
        "target_end": target_end,
        "target_datetime": target_datetime,
        "required_evidence": required_evidence,
        "sensitivity": sensitivity,
        "confidence": confidence,
        "clarification_required": clarification_required,
        "clarification_question": clarification_question,
    }


def build_request(question, now_iso, conversation_context=None):
    system_text = (
        "Sen Vedik AI soru yonlendiricisisin. Astrolojik analiz veya tavsiye verme; "
        "yalniz kullanicinin gercek niyetini, konu alanini ve zaman kapsamını siniflandir. "
        "Kelime icindeki kisa harf eslesmelerine gore karar verme: 'hissetmiyorum' kariyer "
        "degildir. Ruh hali, duygu, gerginlik, motivasyon veya iyi hissetmeme sorularini "
        "wellbeing olarak siniflandir; career yalniz is, meslek veya kariyer baglami acikca "
        "varsa secilir. 'Simdi/tam su anda' instant, 'bugun' daily, tarih veya donem isteyen "
        "sorular range olur. 'Evlenebilir miyim?' gibi gelecekte bir sonucun olup olmayacağını "
        "soran kipler de range olur; tarih verilmemişse bugünden başlayan 92 günlük ufku seç. "
        "Zaman istemeyen yalnız natal kapasite soruları none olur. Tibbi tani istemeyen ruh hali "
        "sorularini medical yapma; mental_wellbeing olarak isaretle. Dosya, kullanici, profil, "
        "harita, Supabase veya Railway kimligi secme. Yalniz verilen izinli degerleri kullan. "
        "active_conversation içindeki bütün önceki soru-cevapları, current_question ile aynı açık "
        "sohbetin bağlamıdır. 'diğerleri', 'bunu', 'o tarih' gibi devam sorularını bu geçmişe göre "
        "çöz; current_question yeni bir konu açıyorsa geçmiş konuyu zorla taşıma. Sohbet geçmişini "
        "astrolojik kanıt sayma ve geçmiş cevaptaki teknik iddiaları doğrulanmış veri gibi kullanma. "
        "required_evidence her zaman natal_core ve active_dasha icersin. Wellbeing icin ayrica "
        "natal_emotional_core ekle. Zaman sorularinda stored_transit_days, "
        "transit_natal_contacts ve ashtakavarga ekle. Daily ve instant icin "
        "moon_and_panchanga, instant icin current_transit_snapshot ekle. "
        "Ay tutulması, Güneş tutulması veya önemli gökyüzü olayı sorularında "
        "time_scope range olmalı ve required_evidence içine important_sky_events ile "
        "sky_event_natal_contacts eklenmeli; tutulma sorularında ayrıca eclipse_events, "
        "eclipse_nakshatra ve eclipse_pada eklenmeli. Tarih, saat, derece, nakşatra "
        "ve pada hesaplama; yalnız saklanmış transit kaydını iste. Kayıt yoksa "
        "eksik kanıt durumu üret. "
        "Cikti yalniz gecerli JSON olsun."
    )
    schema = {
        "primary_topic": sorted(ALLOWED_TOPICS),
        "time_scope": sorted(ALLOWED_TIME_SCOPES),
        "required_evidence": sorted(ALLOWED_EVIDENCE),
        "sensitivity": sorted(ALLOWED_SENSITIVITY),
        "confidence": sorted(ALLOWED_CONFIDENCE),
    }
    user_text = _canonical_json({
        "current_datetime": now_iso,
        "active_conversation": conversation_context or [],
        "current_question": str(question or "").strip(),
        "allowed_values": schema,
        "required_output": {
            "interpreted_question": "string",
            "primary_topic": "allowed value",
            "time_scope": "allowed value",
            "timing_required": "boolean; true iff time_scope is not none",
            "target_start": "YYYY-MM-DD or null",
            "target_end": "YYYY-MM-DD or null",
            "target_datetime": "ISO datetime, now, or null",
            "required_evidence": "non-empty unique allowed-value array",
            "sensitivity": "allowed value",
            "confidence": "allowed value",
            "clarification_required": "boolean",
            "clarification_question": "string or null",
        },
    })
    return {
        "systemInstruction": {"parts": [{"text": system_text}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 768,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }


def classify_question(
    question,
    request_id,
    model_call,
    now_iso,
    *,
    conversation_context=None,
    apply_server_normalization=True,
):
    question = str(question or "").strip()
    if not question or len(question) > 2_000:
        raise QuestionClassificationError("question_classifier_question_invalid")
    request = build_request(question, now_iso, conversation_context)
    returned_request_id, payload = model_call(request_id, request)
    if returned_request_id != request_id or not isinstance(payload, dict):
        raise QuestionClassificationError("question_classifier_response_invalid")
    try:
        value = json.loads(_response_text(payload))
    except json.JSONDecodeError as exc:
        raise QuestionClassificationError("question_classifier_json_invalid") from exc
    if apply_server_normalization:
        value = normalize_classification(value, question, now_iso)
    else:
        # Gemini-only still keeps semantic topic authority, but an explicit
        # calendar phrase must repair timing/evidence minima before schema
        # validation so it cannot fail closed into a natal-only route.
        value = enforce_explicit_time_scope(value, question, now_iso)
    return validate_classification(value)
