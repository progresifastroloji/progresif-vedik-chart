"""Opt-in, redacted Gemini request context accounting.

The live provider reports one prompt token total per call.  This module keeps
the request builder unchanged and records a redacted component breakdown when
``VEDIC_TOKEN_AUDIT_PATH`` is set.  It deliberately stores no prompt text,
chart JSON, conversation text, or user question.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


_METHOD_MARKER = "METODOLOJİ KİMLİĞİ:"
_METHOD_DOC_MARKER = "METODOLOJİ BELGESİ:"
_TECHNICAL_CATALOG_MARKER = "GEÇERLİ EVIDENCE_PATH KATALOĞU:"
_CONVERSATION_MARKER = "SOHBET BAĞLAMI (KANIT DEĞİLDİR):"
_EVIDENCE_MARKER = "KANIT PAKETİ:"
_FULL_SOURCE_MARKER = "TAM MARKDOWN KAYNAKLARI"
_GUIDANCE_MARKERS = (
    "REHBERLİK METODOLOJİSİ KİMLİĞİ:",
    "ETKİN REHBERLİK BECERİSİ KİMLİĞİ:",
)
_GUIDANCE_DOC_MARKERS = (
    "REHBERLİK METODOLOJİSİ BELGESİ:",
    "ETKİN REHBERLİK BECERİSİ:",
)
_NARRATIVE_INPUT_MARKER = "DOĞRULANMIŞ AŞAMA 1:"
_RETRY_SUFFIX = re.compile(r"-(analysis|narrative)-retry-(\d+)$")
_CALL_SUFFIX = re.compile(r"-(analysis|narrative)(?:-retry-\d+)?$")

_CHART_KEYS = {
    "chart_summary",
    "vedic_spine",
    "active_dasha",
    "strength_summary",
    "natal_sections",
}
_TOPIC_KEYS = {"topic_packet", "topic_files", "topic_file"}
_TIMING_KEYS = {
    "transits",
    "transit",
    "stored_transit_days",
    "transit_natal_contacts",
    "ashtakavarga",
    "important_sky_events",
    "timing_evidence",
}
_PROFILE_KEYS = {
    "personal_memory_summary",
    "personal_memory_context",
    "user_profile",
    "profile",
    "stored_context",
}
_QUESTION_KEYS = {"question", "current_user_message", "user_message"}
_RAG_KEYS = {"rag_context", "retrieved_context", "retrieval", "rag"}

_TRANSIT_GROUPS = (
    "daily_panchanga",
    "planetary_positions",
    "transit_aspects_natal_contacts",
    "house_contacts",
    "nakshatra_data",
    "dasha_timing_links",
    "strength_scoring_fields",
    "date_time_location_metadata",
    "evidence_paths",
    "unused_null_fields",
    "other",
)
_TRANSIT_GROUP_RISK = {
    "daily_panchanga": "Panchanga zaman göstergeleri kaybolur; günlük zamanlama ve eksik veri yorumu zayıflar.",
    "planetary_positions": "Transit sign/derece/retrograde ve ilgili gezegen bağları kaybolur; temel transit hükmü risk altına girer.",
    "transit_aspects_natal_contacts": "Natal temaslar ve karşıt göstergeler kaybolur; yüksek metodolojik risk.",
    "house_contacts": "Transitlerin Lagna/Ay ev bağları kaybolur; konuya göre yön tayini zayıflar.",
    "nakshatra_data": "Nakshatra/pada/lord zamanlama bağları kaybolur; yüksek metodolojik risk.",
    "dasha_timing_links": "Aktif daşa ile transit tetikleyicisi arasındaki zincir kopar; yüksek metodolojik risk.",
    "strength_scoring_fields": "Destek/güç/karşı ağırlık sinyalleri kaybolur; aşırı olumlu/olumsuz yorum riski artar.",
    "date_time_location_metadata": "Kayıtların hangi gün/saat/konum için geçerli olduğu belirsizleşir; orta-yüksek risk.",
    "evidence_paths": "Kaynağın izlenebilirliği ve kanıt sözleşmesi zayıflar; veri doğrulama riski.",
    "unused_null_fields": "Tek başına metodolojik değer taşımaz; ancak null/missing durumları eksik veri sinyali olabilir.",
    "other": "İçerik alanına göre değişir; kaldırmadan önce alan bazında incelenmelidir.",
}
_TRANSIT_OVERLAY_RISK = {
    "repeated_natal_references": "Tekrarlanan natal referanslar kaldırılabilir; ancak transitin hangi natal hedefe bağlandığını koruyan tek referans bırakılmalıdır.",
    "repeated_planet_metadata": "Gezegen ad/sign/house/nakshatra metadata'sı sabit tabloda tutulup gün bazında yalnız değişen alanlar gönderilebilir; yanlış dedup transit değişimini gizleyebilir.",
}


def _encoded(value):
    if isinstance(value, bytes):
        return value
    return str(value or "").encode("utf-8")


def _estimate_tokens(value):
    """Conservative local estimate; provider usage remains authoritative."""

    size = len(_encoded(value))
    return max(1, round(size / 4)) if size else 0


def _measure(name, value, *, kind="text"):
    raw = _encoded(value)
    return {
        "name": name,
        "kind": kind,
        "utf8_bytes": len(raw),
        "estimated_tokens": _estimate_tokens(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _between(text, start_marker, end_marker=None):
    start = text.find(start_marker)
    if start < 0:
        return ""
    end = text.find(end_marker, start + len(start_marker)) if end_marker else -1
    return text[start:end if end >= 0 else len(text)]


def _first_marker(text, markers):
    matches = [(text.find(marker), marker) for marker in markers if text.find(marker) >= 0]
    return min(matches)[1] if matches else ""


def _first_text(request, key):
    parts = ((request.get(key) or {}).get("parts") or [])
    return "\n".join(str(part.get("text") or "") for part in parts if isinstance(part, dict))


def _load_json_section(text, marker, end_marker=None):
    section = _between(text, marker, end_marker)
    if not section:
        return None
    payload = section.split("\n", 1)[1] if "\n" in section else ""
    try:
        return json.loads(payload.strip())
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _add(components, name, value, *, kind="text"):
    if value in (None, "", [], {}):
        return
    components.append(_measure(name, value, kind=kind))


def _nested_components(components, payload, *, prefix="evidence"):
    if not isinstance(payload, dict):
        return
    for key, value in payload.items():
        if key in _CHART_KEYS:
            name = "chart_data." + key
        elif key in _TOPIC_KEYS:
            name = "topic_files." + key
        elif key in _TIMING_KEYS:
            name = "timing_evidence." + key
        elif key in _PROFILE_KEYS:
            name = "user_profile." + key
        elif key in _QUESTION_KEYS:
            name = "current_user_message"
        elif key in _RAG_KEYS:
            name = "rag_context." + key
        elif key == "question_route":
            name = "technical_route_metadata"
        else:
            name = "other." + key
        serialized = json.dumps({key: value}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        _add(components, name, serialized, kind="logical_json_component")


def _transit_path_group(path):
    """Assign each transit leaf to one non-overlapping audit bucket."""

    lowered = " ".join(str(part).lower() for part in path)
    if any(part in lowered for part in ("evidence_path", "source_paths", "path_catalog")):
        return "evidence_paths"
    if any(part in lowered for part in ("date", "datetime", "time", "timezone", "tz_offset", "period", "selection", "location")):
        return "date_time_location_metadata"
    if any(part in lowered for part in ("panchanga", "tithi", "paksha", "vara", "yoga", "karana")):
        return "daily_panchanga"
    if any(part in lowered for part in ("nakshatra", "pada")):
        return "nakshatra_data"
    if any(part in lowered for part in ("dasha", "timing", "active_path", "maha", "antara", "pratyantar")):
        return "dasha_timing_links"
    if any(part in lowered for part in ("strength", "score", "support", "ashtakavarga", "bav", "sav")):
        return "strength_scoring_fields"
    if any(part in lowered for part in ("house_from", "natal_house", "transit_house", "house_contact")):
        return "house_contacts"
    if any(part in lowered for part in ("contact", "aspect", "closest_approach", "natal_contacts")):
        return "transit_aspects_natal_contacts"
    if any(part in lowered for part in ("planet", "moon", "retrograde", "sign", "degree", "speed")):
        return "planetary_positions"
    return "other"


def _transit_subgroup_audit(transits):
    """Return redacted byte/token measurements for transit leaves.

    The grouping is intentionally a wire-shape audit, not a claim that a
    model semantically attended to a field.  The complete transit object is
    still measured separately as ``timing_evidence.transits``.
    """

    buckets = {name: [] for name in _TRANSIT_GROUPS}
    null_paths = []
    all_leaves = []

    def walk(value, path):
        if value is None:
            null_paths.append(".".join(path))
            buckets["unused_null_fields"].append({"path": ".".join(path), "value": None})
            return
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, path + [str(key)])
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, path + [str(index)])
            return
        group = _transit_path_group(path)
        leaf = {"path": ".".join(path), "value": value}
        all_leaves.append(leaf)
        buckets[group].append(leaf)

    walk(transits, ["transits"])
    rows = []
    for name in _TRANSIT_GROUPS:
        leaves = buckets[name]
        # ``payload_encoded`` is the component estimate used in the report.
        # It intentionally excludes full JSON paths so the same parent path is
        # not charged once per leaf.  ``annotated_encoded`` remains available
        # to explain why component estimates are not expected to sum exactly
        # to the enclosing transit wire size.
        payload_encoded = json.dumps(
            [item["value"] for item in leaves],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        annotated_encoded = json.dumps(
            leaves,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        rows.append({
            "name": name,
            "utf8_bytes": len(payload_encoded),
            "estimated_tokens": _estimate_tokens(payload_encoded),
            "annotated_path_bytes": len(annotated_encoded),
            "annotated_path_estimated_tokens": _estimate_tokens(annotated_encoded),
            "leaf_count": len(leaves),
            "sent_to_technical_model": True,
            "semantic_use_observable": False,
            "risk_if_removed": _TRANSIT_GROUP_RISK[name],
            "overlap_with_other_context": (
                name in {"dasha_timing_links", "nakshatra_data", "house_contacts"}
            ),
            "overlap_note": {
                "dasha_timing_links": "active_dasha/vedic_spine ile aynı lord/path alanları kısmen tekrar edebilir.",
                "nakshatra_data": "chart_summary/vedic_spine/natal_sections içindeki natal nakshatra alanlarıyla karşılaştırılmalıdır.",
                "house_contacts": "chart_summary ve natal_sections içindeki natal ev referanslarıyla aynı hedefe bağlanır; transit-house değeri dinamik kalır.",
            }.get(name, ""),
        })
    overlay_leaves = {
        "repeated_natal_references": [
            item for item in all_leaves
            if any(token in item["path"].lower() for token in (
                "natal_reference",
                "natal_planet",
                "natal_house",
                "natal_planets_in_sign",
            ))
        ],
        "repeated_planet_metadata": [
            item for item in all_leaves
            if ".planets." in item["path"].lower()
            and item["path"].rsplit(".", 1)[-1] in {
                "name", "sign", "degree_str", "house_from_lagna", "house_from_moon",
                "retrograde", "nakshatra", "nakshatra_pada", "nakshatra_lord",
            }
        ],
    }
    for name, leaves in overlay_leaves.items():
        encoded = json.dumps(
            [item["value"] for item in leaves],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        rows.append({
            "name": name,
            "utf8_bytes": len(encoded),
            "estimated_tokens": _estimate_tokens(encoded),
            "annotated_path_bytes": 0,
            "annotated_path_estimated_tokens": 0,
            "leaf_count": len(leaves),
            "sent_to_technical_model": True,
            "semantic_use_observable": False,
            "risk_if_removed": _TRANSIT_OVERLAY_RISK[name],
            "overlap_with_other_context": True,
            "overlap_only": True,
            "duplicate_count": len(leaves),
        })
    return {
        "method": "redacted_leaf_payload_bytes_div_4",
        "exact_provider_component_tokens": None,
        "provider_semantic_use": "not observable from usageMetadata",
        "accounting_note": "Component payload estimates are non-overlapping by leaf classification but omit enclosing JSON syntax; they are not expected to sum exactly to the full transit wire size.",
        "null_leaf_count": len(null_paths),
        "groups": rows,
    }


def _technical_components(request):
    system = _first_text(request, "systemInstruction")
    user = "\n".join(
        str(part.get("text") or "")
        for content in (request.get("contents") or [])
        for part in (content.get("parts") or [])
        if isinstance(part, dict)
    )
    components = []
    _add(components, "system_instructions", _between(system, "", _METHOD_MARKER) or system)
    _add(components, "methodology_identity", _between(system, _METHOD_MARKER, _METHOD_DOC_MARKER))
    methodology = _between(system, _METHOD_DOC_MARKER, "\n\nTAM KAYNAK BAĞLAMI ETKİN:")
    if not methodology:
        methodology = _between(system, _METHOD_DOC_MARKER)
    _add(components, "methodology", methodology)
    _add(components, "technical_call_extra", _between(user, "", _TECHNICAL_CATALOG_MARKER))
    _add(components, "evidence_path_catalog", _between(user, _TECHNICAL_CATALOG_MARKER, _CONVERSATION_MARKER))
    _add(components, "conversation_history", _between(user, _CONVERSATION_MARKER, _EVIDENCE_MARKER))
    evidence_text = _between(user, _EVIDENCE_MARKER, _FULL_SOURCE_MARKER)
    if not evidence_text:
        evidence_text = _between(user, _EVIDENCE_MARKER)
    _add(components, "evidence_json_wire", evidence_text)
    evidence_payload = _load_json_section(user, _EVIDENCE_MARKER, _FULL_SOURCE_MARKER)
    _nested_components(components, evidence_payload)
    if isinstance(evidence_payload, dict) and isinstance(evidence_payload.get("transits"), dict):
        components.append({
            "name": "timing_evidence.transit_subgroups",
            "kind": "redacted_subgroup_audit",
            "utf8_bytes": 0,
            "estimated_tokens": 0,
            "audit": _transit_subgroup_audit(evidence_payload["transits"]),
        })
    _add(components, "other.full_markdown_or_source_context", _between(user, _FULL_SOURCE_MARKER))
    return components


def _narrative_components(request):
    system = _first_text(request, "systemInstruction")
    user = "\n".join(
        str(part.get("text") or "")
        for content in (request.get("contents") or [])
        for part in (content.get("parts") or [])
        if isinstance(part, dict)
    )
    components = []
    guidance_marker = _first_marker(system, _GUIDANCE_MARKERS)
    guidance_doc_marker = _first_marker(system, _GUIDANCE_DOC_MARKERS)
    _add(components, "narrative_call_extra", _between(system, "", guidance_marker) if guidance_marker else system)
    _add(components, "narrative_methodology_identity", _between(system, guidance_marker, guidance_doc_marker))
    _add(components, "narrative_methodology", _between(system, guidance_doc_marker))
    _add(components, "narrative_call_extra.user_instructions", _between(user, "", _NARRATIVE_INPUT_MARKER))
    input_text = _between(user, _NARRATIVE_INPUT_MARKER)
    _add(components, "narrative_input_wire", input_text)
    payload = _load_json_section(user, _NARRATIVE_INPUT_MARKER)
    if isinstance(payload, dict):
        _add(components, "conversation_history", json.dumps(payload.get("conversation_context"), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        _add(components, "current_user_message", json.dumps({"question": payload.get("question")}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        _add(components, "technical_output", json.dumps({"analysis": payload.get("analysis")}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        _add(components, "technical_route_metadata", json.dumps({"question_route": payload.get("question_route")}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        _add(components, "user_profile.personal_memory_summary", json.dumps({"personal_memory_summary": payload.get("personal_memory_summary")}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        memory = payload.get("personal_memory_context")
        if isinstance(memory, dict):
            for key, name in (
                ("user_memory_profile", "user_memory_profile"),
                ("relevant_memories", "relevant_memories"),
                ("active_topics", "active_topics"),
                ("astrological_memory", "astrological_memory"),
            ):
                _add(
                    components,
                    name,
                    json.dumps(memory.get(key), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    kind="logical_json_component",
                )
    return components


def decompose_request(request, *, call_type="technical", request_id=None):
    """Return a redacted component map for one actual provider request."""

    if not isinstance(request, dict):
        raise TypeError("request must be a dictionary")
    call_type = "narrative" if call_type == "narrative" else "technical"
    components = _technical_components(request) if call_type == "technical" else _narrative_components(request)
    raw = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    component_bytes = sum(
        item["utf8_bytes"]
        for item in components
        if item["kind"] != "logical_json_component"
    )
    logical_component_bytes = sum(
        item["utf8_bytes"]
        for item in components
        if item["kind"] == "logical_json_component"
    )
    retry_match = _RETRY_SUFFIX.search(str(request_id or ""))
    return {
        "call_type": call_type,
        "request_id": request_id,
        "is_retry": bool(retry_match),
        "retry_attempt": int(retry_match.group(2)) if retry_match else 0,
        "request_json_bytes": len(raw),
        "estimated_prompt_tokens": _estimate_tokens(raw),
        "component_bytes_sum": component_bytes,
        "logical_component_bytes_sum": logical_component_bytes,
        "unattributed_wire_bytes": max(len(raw) - component_bytes, 0),
        "components": components,
    }


def request_group_id(request_id):
    """Collapse analysis/narrative/retry suffixes to one question/job group."""

    value = str(request_id or "")
    return _CALL_SUFFIX.sub("", value)


def aggregate_usage_calls(usage_calls):
    """Sum all provider calls belonging to the same question group.

    This is intentionally call-count independent: technical, narrative and
    retry calls all contribute to the same question total.
    """

    grouped = {}
    for call in usage_calls or []:
        if not isinstance(call, dict):
            continue
        group = request_group_id(call.get("request_id"))
        bucket = grouped.setdefault(group, {"request_id": group, "calls": 0})
        bucket["calls"] += 1
        for field in ("prompt_tokens", "cached_content_tokens", "response_tokens", "thoughts_tokens", "total_tokens"):
            value = call.get(field)
            if isinstance(value, (int, float)):
                bucket[field] = bucket.get(field, 0) + value
    return list(grouped.values())


def record_request(request_id, call_type, request):
    """Append one redacted request audit when explicitly enabled."""

    path = str(os.environ.get("VEDIC_TOKEN_AUDIT_PATH") or "").strip()
    if not path:
        return None
    try:
        record = decompose_request(request, call_type=call_type, request_id=request_id)
        record["record_type"] = "request"
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record
    except (OSError, TypeError, ValueError):
        # Diagnostics must never make a provider call fail.
        return None


def record_usage(call):
    """Append provider usageMetadata already normalized by the orchestrator."""

    path = str(os.environ.get("VEDIC_TOKEN_AUDIT_PATH") or "").strip()
    if not path or not isinstance(call, dict):
        return None
    try:
        record = {
            "record_type": "usage",
            "request_id": call.get("request_id"),
            "call_type": call.get("call_type"),
            "attempt": call.get("attempt"),
            "usage": {
                field: call.get(field)
                for field in (
                    "prompt_tokens",
                    "cached_content_tokens",
                    "response_tokens",
                    "thoughts_tokens",
                    "total_tokens",
                    "model_version",
                )
            },
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record
    except (OSError, TypeError, ValueError):
        return None
