"""Controlled comparison runner for the three Vedik methodology candidates."""

import hashlib
import json
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


CONTRACT_VERSION = "vedic-system-analysis-v2"
MAX_METHODOLOGY_BYTES = 64 * 1024
MAX_PROMPT_BYTES = 220 * 1024
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
}
EVIDENCE_PATH_PATTERN = re.compile(r"^evidence(?:\.[a-zA-Z0-9_\-]+)+$")

CANDIDATE_MANIFEST = (
    {
        "id": "vedic-system-methodology-v1",
        "title": "Vedik Analiz Sistem Metodolojisi",
        "version": "1.0.0",
        "status": "active",
        "filename": "SYSTEM_METHODOLOGY.txt",
        "sha256": "8f86a845acdbdb1fc402439b883eb8432f3277f66f451d22455fcb30bf72a10a",
    },
)


class MethodologyOrchestrationError(Exception):
    """Safe orchestration failure with a stable public error code."""

    def __init__(self, code, http_status=500):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


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
        "status": draft.get("status"),
        "confidence": draft.get("confidence"),
        "chart_summary": source.get("chart_summary"),
        "active_dasha": source.get("active_dasha"),
        "topic_packet": source.get("topic_packet"),
        "natal_sections": source.get("natal_sections") or [],
        "data_quality": source.get("data_quality"),
        "context_strategy": draft.get("context_strategy"),
        "missing": draft.get("missing") or [],
        "safety_notes": draft.get("safety_notes") or [],
    }
    if draft.get("topic") == "transit":
        evidence["transits"] = source.get("transits")
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


def _model_request(candidate, evidence):
    evidence_json = _canonical_json(evidence)
    evidence_path_catalog_json = _canonical_json(_evidence_path_catalog(evidence))
    system_text = (
        "Yalnız aşağıdaki tek ve aktif Vedik/Jyotisha sistem metodolojisini uygula. "
        "Başka metodoloji, Batı/Tropical astroloji veya hesap uydurma kullanma. "
        "Sadece verilen kanıt paketindeki teknik gerçekleri yorumla. Eksik veri varsa açıkça sınırla. "
        "Metodolojide anılan fakat kanıt paketinde bulunmayan registry içeriğini uydurma. "
        "Önce soruyu sınıflandır; sonra doğru konu, veri kapısı ve zorunlu analiz sırasını uygula. "
        "question_intent.primary_topic değeri kanıt paketindeki subject_topic ile birebir aynı olmalı; "
        "timing_required yalnız topic=transit ise true olmalı. "
        "Shadbala gezegen sıralamasında yalnız evidence.strength_summary içindeki strength_ratio kullanılır; "
        "legacy_raw_total gezegenler arası güç karşılaştırması değildir. "
        "Teknik analiz tamamlanmadan koçluk veya motivasyon ekleme. "
        "Yanıt yalnız geçerli JSON olsun.\n\n"
        f"METODOLOJİ KİMLİĞİ: {candidate['id']}@{candidate['version']}\n"
        f"METODOLOJİ SHA256: {candidate['sha256']}\n\n"
        f"METODOLOJİ BELGESİ:\n{candidate['document']}"
    )
    user_text = (
        "Aşağıdaki kanıt paketini metodolojiye göre eksiksiz incele. JSON alanları tam olarak şunlar olsun: "
        "question_intent (interpreted_question string, primary_topic string, timing_required boolean), "
        "analysis_status (COMPLETE|INCOMPLETE), methodology_coverage (array; her satır step, status ve note içerir), "
        "summary (soruyu doğrudan yanıtlayan, teknik liste olmayan zengin string), "
        "supporting_evidence (claim ve evidence_path içeren array), "
        "challenging_evidence (claim ve evidence_path içeren array), missing_layers (string array), "
        "confidence (low|medium|high), limitations (string array). "
        "methodology_coverage şu adımların her birini tam bir kez ve bu sırada içermeli: "
        + ", ".join(REQUIRED_METHODOLOGY_STEPS)
        + ". status yalnız applied|not_applicable|missing olabilir. "
        "Zorunlu bir adım missing ise analysis_status INCOMPLETE olmalıdır. "
        "Her evidence_path evidence. ile başlamalı ve paketteki gerçek alana işaret etmelidir. "
        "Shadbala veya strength_ratio hakkında her supporting_evidence/challenging_evidence iddiası "
        "evidence.strength_summary yolunu ya da onun altındaki gerçek bir yolu kullanmalıdır. "
        "Uzun zaman serilerindeki birden fazla satırı destekleyen iddia için dizinin kök yolunu "
        "(örneğin evidence.transits.daily_timing) kullan. "
        "Konu paketindeki houses, planets, lordships, yogas, vargas ve active_dasha alanları "
        "evidence.topic_packet.evidence altında bulunur; örneğin "
        "evidence.topic_packet.evidence.houses.0.occupants. "
        "Alan yolunu aşağıdaki geçerli yol kataloğundan eksiksiz kopyala; katalog dışında yol üretme.\n\n"
        f"GEÇERLİ EVIDENCE_PATH KATALOĞU:\n{evidence_path_catalog_json}\n\n"
        f"KANIT PAKETİ:\n{evidence_json}"
    )
    request = {
        "systemInstruction": {"parts": [{"text": system_text}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }
    raw = _canonical_json(request).encode("utf-8")
    if len(raw) > MAX_PROMPT_BYTES:
        raise MethodologyOrchestrationError("methodology_prompt_too_large", 413)
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
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    rows = []
    for item in value:
        if not isinstance(item, dict):
            raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
        claim = str(item.get("claim") or "").strip()
        evidence_path = str(item.get("evidence_path") or "").strip()
        canonical_path = (
            _canonical_evidence_path(evidence, evidence_path)
            if EVIDENCE_PATH_PATTERN.fullmatch(evidence_path)
            else None
        )
        if (
            not claim
            or not canonical_path
        ):
            raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
        rows.append({"claim": claim, "evidence_path": canonical_path})
    return rows


def _string_list(value):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    return [item.strip() for item in value if item.strip()]


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
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    interpreted_question = str(question_intent.get("interpreted_question") or "").strip()
    primary_topic = str(question_intent.get("primary_topic") or "").strip()
    timing_required = question_intent.get("timing_required")
    if not interpreted_question or not primary_topic or not isinstance(timing_required, bool):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    expected_topic = str(evidence.get("subject_topic") or "").strip()
    expected_timing = evidence.get("topic") == "transit"
    if primary_topic != expected_topic or timing_required is not expected_timing:
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    if analysis_status not in {"COMPLETE", "INCOMPLETE"} or not isinstance(coverage, list):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    normalized_coverage = []
    for expected_step, row in zip(REQUIRED_METHODOLOGY_STEPS, coverage, strict=False):
        if not isinstance(row, dict):
            raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
        step = str(row.get("step") or "").strip()
        status = str(row.get("status") or "").strip()
        note = str(row.get("note") or "").strip()
        if step != expected_step or status not in COVERAGE_STATUSES or not note:
            raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
        normalized_coverage.append({"step": step, "status": status, "note": note})
    if len(coverage) != len(REQUIRED_METHODOLOGY_STEPS):
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    if any(row["status"] == "missing" for row in normalized_coverage) and analysis_status != "INCOMPLETE":
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    summary = str(value.get("summary") or "").strip()
    confidence = str(value.get("confidence") or "").strip().lower()
    if not summary or confidence not in CONFIDENCE_LEVELS:
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    supporting_evidence = _evidence_rows(value.get("supporting_evidence"), evidence)
    challenging_evidence = _evidence_rows(value.get("challenging_evidence"), evidence)
    for row in [*supporting_evidence, *challenging_evidence]:
        if (
            re.search(r"\b(?:shadbala|strength_ratio)\b", row["claim"], re.IGNORECASE)
            and not row["evidence_path"].startswith("evidence.strength_summary")
        ):
            raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
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


def _usage(payload):
    usage = payload.get("usageMetadata") or {}
    return {
        "prompt_tokens": usage.get("promptTokenCount"),
        "response_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
        "model_version": payload.get("modelVersion"),
    }


def _run_candidate(candidate, comparison_id, evidence, evidence_sha256, model_call, clock):
    base_request_id = f"{comparison_id}-{candidate['id']}"
    request, prompt_sha256 = _model_request(candidate, evidence)
    started = clock()
    for attempt_index in range(2):
        request_id = (
            base_request_id
            if attempt_index == 0
            else f"{base_request_id}-retry-{attempt_index}"
        )
        try:
            returned_request_id, payload = model_call(request_id, request)
            if returned_request_id != request_id or not isinstance(payload, dict):
                raise MethodologyOrchestrationError("methodology_model_response_invalid", 502)
            analysis = validate_methodology_response(payload, evidence)
            return {
                "status": "completed",
                "methodology": {key: candidate[key] for key in ("id", "title", "version", "status", "sha256")},
                "request_id": request_id,
                "attempt_count": attempt_index + 1,
                "evidence_sha256": evidence_sha256,
                "prompt_sha256": prompt_sha256,
                "latency_ms": max(round((clock() - started) * 1000), 0),
                "usage": _usage(payload),
                "analysis": analysis,
            }
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
                "prompt_sha256": prompt_sha256,
                "latency_ms": max(round((clock() - started) * 1000), 0),
                "error": code if str(code).startswith(("methodology_", "vertex_")) else "methodology_model_failed",
            }


def run_methodology_comparison(draft, comparison_id, model_call, *, candidates_root=None, clock=None):
    candidates = load_methodology_candidates(candidates_root)
    evidence = compact_evidence(draft)
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
            ),
            candidates,
        ))

    completed = sum(result["status"] == "completed" for result in results)
    comparison_status = "comparison_ready" if completed == len(results) else "partial" if completed else "failed"
    return {
        "contract_version": CONTRACT_VERSION,
        "comparison_id": comparison_id,
        "status": comparison_status,
        "question": draft.get("question"),
        "topic": draft.get("topic"),
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
