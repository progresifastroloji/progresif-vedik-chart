#!/usr/bin/env python3
"""Validate the local chat-training candidate without calling Vertex AI."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "comparison_audit_v1.jsonl"
SFT_PATH = ROOT / "vertex_sft_candidate_v1.jsonl"
MANIFEST_PATH = ROOT / "manifest_v1.json"

FORBIDDEN_KEYS = {
    "birth_date",
    "birth_time",
    "birth_place",
    "email",
    "profile_id",
    "user_id",
    "token",
    "api_key",
}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"{path.name}:{line_number} nesne olmalı")
        rows.append(value)
    return rows


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).casefold()
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def validate_sft(row: dict) -> dict:
    assert set(row) == {"systemInstruction", "contents"}
    instruction = row["systemInstruction"]
    assert isinstance(instruction.get("parts"), list) and instruction["parts"]
    assert all(set(part) == {"text"} and part["text"].strip() for part in instruction["parts"])
    contents = row["contents"]
    assert [item.get("role") for item in contents] == ["user", "model"]
    assert all(isinstance(item.get("parts"), list) and item["parts"] for item in contents)
    target = json.loads(contents[-1]["parts"][0]["text"])
    assert set(target) == {"opening_summary", "answer"}
    assert target["opening_summary"].strip() and target["answer"].strip()
    return target


def main() -> None:
    audit_rows = read_jsonl(AUDIT_PATH)
    sft_rows = read_jsonl(SFT_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert len(audit_rows) == len(sft_rows) == len(manifest["records"]) == 1
    manifest_record = manifest["records"][0]
    assert manifest_record["id"] == audit_rows[0]["id"]
    assert manifest_record["status"] == "astrolog_review_pending"
    assert manifest_record["may_upload_for_tuning"] is False
    assert not (set(walk_keys(audit_rows)) & FORBIDDEN_KEYS)
    assert not (set(walk_keys(sft_rows)) & FORBIDDEN_KEYS)
    targets = [validate_sft(row) for row in sft_rows]
    assert targets[0] == audit_rows[0]["proposed_target"]
    print("OK: 1 sohbet eğitim adayı biçim ve gizlilik kontrollerinden geçti; astrolog onayı bekliyor.")


if __name__ == "__main__":
    main()
