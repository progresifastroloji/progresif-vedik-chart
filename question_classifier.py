"""Gemini-backed, schema-limited question classification for Vedik AI.

The classifier never reads chart files and never makes astrological claims. It
only converts the user's natural-language question into a small allow-listed
routing decision. The application server remains responsible for ownership,
artifact access, evidence selection, calculations, and methodology execution.
"""

from __future__ import annotations

import json
from datetime import date, datetime


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
    required_layers = {"natal_core", "active_dasha"}
    if primary_topic == "wellbeing":
        required_layers.add("natal_emotional_core")
    if time_scope != "none":
        required_layers.update({
            "stored_transit_days",
            "transit_natal_contacts",
            "ashtakavarga",
        })
    if time_scope in {"daily", "instant"}:
        required_layers.add("moon_and_panchanga")
    if time_scope == "instant":
        required_layers.add("current_transit_snapshot")
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


def build_request(question, now_iso):
    system_text = (
        "Sen Vedik AI soru yonlendiricisisin. Astrolojik analiz veya tavsiye verme; "
        "yalniz kullanicinin gercek niyetini, konu alanini ve zaman kapsamını siniflandir. "
        "Kelime icindeki kisa harf eslesmelerine gore karar verme: 'hissetmiyorum' kariyer "
        "degildir. Ruh hali, duygu, gerginlik, motivasyon veya iyi hissetmeme sorularini "
        "wellbeing olarak siniflandir; career yalniz is, meslek veya kariyer baglami acikca "
        "varsa secilir. 'Simdi/tam su anda' instant, 'bugun' daily, tarih veya donem isteyen "
        "sorular range, zaman istemeyen sorular none olur. Tibbi tani istemeyen ruh hali "
        "sorularini medical yapma; mental_wellbeing olarak isaretle. Dosya, kullanici, profil, "
        "harita, Supabase veya Railway kimligi secme. Yalniz verilen izinli degerleri kullan. "
        "required_evidence her zaman natal_core ve active_dasha icersin. Wellbeing icin ayrica "
        "natal_emotional_core ekle. Zaman sorularinda stored_transit_days, "
        "transit_natal_contacts ve ashtakavarga ekle. Daily ve instant icin "
        "moon_and_panchanga, instant icin current_transit_snapshot ekle. "
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
        "question": str(question or "").strip(),
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


def classify_question(question, request_id, model_call, now_iso):
    question = str(question or "").strip()
    if not question or len(question) > 2_000:
        raise QuestionClassificationError("question_classifier_question_invalid")
    request = build_request(question, now_iso)
    returned_request_id, payload = model_call(request_id, request)
    if returned_request_id != request_id or not isinstance(payload, dict):
        raise QuestionClassificationError("question_classifier_response_invalid")
    try:
        value = json.loads(_response_text(payload))
    except json.JSONDecodeError as exc:
        raise QuestionClassificationError("question_classifier_json_invalid") from exc
    return validate_classification(value)
