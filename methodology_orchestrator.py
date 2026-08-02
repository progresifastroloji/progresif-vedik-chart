"""Controlled comparison runner for the three Vedik methodology candidates."""

import hashlib
import json
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


CONTRACT_VERSION = "vedic-methodology-comparison-v1"
MAX_METHODOLOGY_BYTES = 64 * 1024
MAX_PROMPT_BYTES = 220 * 1024
CONFIDENCE_LEVELS = {"low", "medium", "high"}
RETRYABLE_RESPONSE_ERRORS = {
    "methodology_model_json_invalid",
    "methodology_model_response_empty",
    "methodology_model_schema_invalid",
}
EVIDENCE_PATH_PATTERN = re.compile(r"^evidence(?:\.[a-zA-Z0-9_\-]+)+$")

CANDIDATE_MANIFEST = (
    {
        "id": "vedic-classical-strict-v1",
        "title": "Klasik ve Sıkı Vedik Metodoloji",
        "version": "1.0.0",
        "status": "candidate",
        "filename": "vedic-classical-strict-v1.md",
        "sha256": "f38a9dfb3f6954f46c2e8b2b5863aaeecb7983aef709a3a5e2b644ec0a78cd1d",
    },
    {
        "id": "vedic-comprehensive-deep-v1",
        "title": "Geniş ve Derin Vedik Metodoloji",
        "version": "1.0.0",
        "status": "candidate",
        "filename": "vedic-comprehensive-deep-v1.md",
        "sha256": "f6d9a85e35029d096d2cc681399a5620d9aece2fa4b7647b186b77d759fa7d88",
    },
    {
        "id": "vedic-ai-application-v1",
        "title": "AI ve Uygulama Odaklı Vedik Metodoloji",
        "version": "1.0.0",
        "status": "candidate",
        "filename": "vedic-ai-application-v1.md",
        "sha256": "b89d8db41983c9a8589b9cd33a8a14eb2cf64bac2cca65334493c2f9e1a8147b",
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
    root_path = Path(root or Path(__file__).resolve().parent / "methodologies" / "candidates")
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
        for key in ("id", "title", "version", "status"):
            if metadata.get(key) != expected[key]:
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
        "status": draft.get("status"),
        "confidence": draft.get("confidence"),
        "chart_summary": source.get("chart_summary"),
        "active_dasha": source.get("active_dasha"),
        "topic_packet": source.get("topic_packet"),
        "data_quality": source.get("data_quality"),
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
            for index, child in enumerate(value):
                path = f"{prefix}.{index}"
                paths.append(path)
                walk(child, path)

    walk(evidence, "evidence")
    return sorted(paths)


def _model_request(candidate, evidence):
    evidence_json = _canonical_json(evidence)
    evidence_path_catalog_json = _canonical_json(_evidence_path_catalog(evidence))
    system_text = (
        "Yalnız aşağıdaki tek Vedik/Jyotisha metodoloji adayını uygula. "
        "Başka metodoloji, Batı/Tropical astroloji veya hesap uydurma kullanma. "
        "Sadece verilen kanıt paketindeki teknik gerçekleri yorumla. Eksik veri varsa açıkça sınırla. "
        "Adayı diğer adaylarla kıyaslama, seçme veya nihai ilan etme. "
        "Yanıt yalnız geçerli JSON olsun.\n\n"
        f"METODOLOJİ KİMLİĞİ: {candidate['id']}@{candidate['version']}\n"
        f"METODOLOJİ SHA256: {candidate['sha256']}\n\n"
        f"METODOLOJİ BELGESİ:\n{candidate['document']}"
    )
    user_text = (
        "Aşağıdaki kanıt paketini metodolojiye göre incele. JSON alanları tam olarak şunlar olsun: "
        "summary (string), supporting_evidence (claim ve evidence_path içeren array), "
        "challenging_evidence (claim ve evidence_path içeren array), missing_layers (string array), "
        "confidence (low|medium|high), limitations (string array). "
        "Her evidence_path evidence. ile başlamalı ve paketteki gerçek alana işaret etmelidir. "
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
            "maxOutputTokens": 4096,
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
    summary = str(value.get("summary") or "").strip()
    confidence = str(value.get("confidence") or "").strip().lower()
    if not summary or confidence not in CONFIDENCE_LEVELS:
        raise MethodologyOrchestrationError("methodology_model_schema_invalid", 502)
    return {
        "summary": summary,
        "supporting_evidence": _evidence_rows(value.get("supporting_evidence"), evidence),
        "challenging_evidence": _evidence_rows(value.get("challenging_evidence"), evidence),
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
        "selection": None,
        "selection_status": "user_review_required",
        "completed_count": completed,
        "candidate_count": len(results),
    }


def new_comparison_id():
    return f"methodology-compare-{uuid.uuid4()}"
