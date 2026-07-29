#!/usr/bin/env python3
"""Validate the passive golden fixture and reference-template shape.

This script does not calculate charts and does not run the application. It only
checks that the golden fixture and reference files are structurally ready for
later tests.
"""

from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
FIXTURES_PATH = BASE_DIR / "fixtures.json"
REFERENCES_DIR = BASE_DIR / "references"

REQUIRED_PLANETS = {
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu (True)",
    "Ketu",
}

ALLOWED_SOURCE_STATUS = {
    "planning_skeleton",
    "swiss_only_pending_jhora",
    "swiss_and_jhora_matched",
    "source_discrepancy_pending_review",
}

REQUIRED_SWISS_REFERENCE_MARKERS = [
    "## Lagna",
    "## Planets",
    "## Bhava Chalit / Sripati Raw Reference",
    "### Sripati Cusps",
    "### Planet House Assignment",
    "Status: swiss_only_pending_jhora",
]

REQUIRED_JHORA_REFERENCE_MARKERS = [
    "Status: external_reference_pending",
    "## D1 Lagna",
    "## D1 Planets",
    "## Bhava Chalit / Sripati",
    "### Cusp Table",
    "### Planet House Assignment",
    "## Moon Nakshatra",
    "## Vimshottari Active at Birth",
    "## Vargas",
    "## Difference Notes",
]

REQUIRED_VARSHAPHALA_TAJIKA_REFERENCE_MARKERS = [
    "Status: external_reference_pending",
    "## Capture Checklist",
    "## Varsha Year",
    "## Varsha Lagna / Muntha",
    "## Varshesha Candidates",
    "## Mudda Dasha",
    "## Sahams",
    "## Tajika Aspects / Deeptamsa",
    "## Tajika Yoga Candidates",
    "## Rectification Use Decision",
    "## Difference Notes",
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_keys(mapping: dict, keys: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(keys - set(mapping.keys()))
    require(not missing, f"{label} missing keys: {', '.join(missing)}", errors)


def validate_birth(fixture_id: str, birth: dict, errors: list[str]) -> None:
    require_keys(
        birth,
        {"date", "time", "timezone_id", "tz_offset", "place", "lat", "lon"},
        f"{fixture_id}.birth",
        errors,
    )
    require(isinstance(birth.get("date"), str) and birth.get("date"), f"{fixture_id}.birth.date is empty", errors)
    require(isinstance(birth.get("time"), str) and birth.get("time"), f"{fixture_id}.birth.time is empty", errors)
    require(isinstance(birth.get("lat"), (int, float)), f"{fixture_id}.birth.lat must be numeric", errors)
    require(isinstance(birth.get("lon"), (int, float)), f"{fixture_id}.birth.lon must be numeric", errors)


def validate_lagna(fixture_id: str, lagna: dict, errors: list[str]) -> None:
    require_keys(
        lagna,
        {"longitude", "sign", "sign_index", "degree", "degree_str"},
        f"{fixture_id}.expected.lagna",
        errors,
    )
    require(isinstance(lagna.get("longitude"), (int, float)), f"{fixture_id}.expected.lagna.longitude must be numeric", errors)
    require(isinstance(lagna.get("sign_index"), int), f"{fixture_id}.expected.lagna.sign_index must be integer", errors)
    require(0 <= lagna.get("sign_index", -1) <= 11, f"{fixture_id}.expected.lagna.sign_index out of range", errors)


def validate_planets(fixture_id: str, planets: dict, errors: list[str]) -> None:
    require(isinstance(planets, dict), f"{fixture_id}.expected.planets must be an object", errors)
    missing = sorted(REQUIRED_PLANETS - set(planets.keys()))
    require(not missing, f"{fixture_id}.expected.planets missing: {', '.join(missing)}", errors)
    for planet_name, planet in planets.items():
        label = f"{fixture_id}.expected.planets.{planet_name}"
        require_keys(
            planet,
            {"longitude", "sign", "sign_index", "degree", "degree_str", "retrograde"},
            label,
            errors,
        )
        require(isinstance(planet.get("longitude"), (int, float)), f"{label}.longitude must be numeric", errors)
        require(isinstance(planet.get("sign_index"), int), f"{label}.sign_index must be integer", errors)
        require(0 <= planet.get("sign_index", -1) <= 11, f"{label}.sign_index out of range", errors)
        require(isinstance(planet.get("retrograde"), bool), f"{label}.retrograde must be boolean", errors)


def validate_moon_nakshatra(fixture_id: str, moon_nakshatra: dict, errors: list[str]) -> None:
    require_keys(
        moon_nakshatra,
        {"name", "number", "pada", "lord", "degree_in_nakshatra"},
        f"{fixture_id}.expected.moon_nakshatra",
        errors,
    )
    require(1 <= moon_nakshatra.get("number", 0) <= 27, f"{fixture_id}.expected.moon_nakshatra.number out of range", errors)
    require(1 <= moon_nakshatra.get("pada", 0) <= 4, f"{fixture_id}.expected.moon_nakshatra.pada out of range", errors)


def validate_pending_fields(fixture_id: str, expected: dict, errors: list[str], warnings: list[str]) -> None:
    if expected.get("vimshottari_active") is None:
        warnings.append(f"{fixture_id}.expected.vimshottari_active pending")

    if expected.get("chara_antardasha") is None:
        warnings.append(f"{fixture_id}.expected.chara_antardasha pending")

    if expected.get("yogini_pratyantardasha") is None:
        warnings.append(f"{fixture_id}.expected.yogini_pratyantardasha pending")

    if expected.get("bhava_chalit") is None:
        warnings.append(f"{fixture_id}.expected.bhava_chalit pending")

    if expected.get("bhava_bala") is None:
        warnings.append(f"{fixture_id}.expected.bhava_bala pending")

    if expected.get("vimshopaka_bala") is None:
        warnings.append(f"{fixture_id}.expected.vimshopaka_bala pending")

    if expected.get("avasthas") is None:
        warnings.append(f"{fixture_id}.expected.avasthas pending")

    if expected.get("varshaphala_tajika_rectification") is None:
        warnings.append(f"{fixture_id}.expected.varshaphala_tajika_rectification pending")

    vargas = expected.get("vargas")
    require(isinstance(vargas, dict), f"{fixture_id}.expected.vargas must be an object", errors)
    if not isinstance(vargas, dict):
        return

    for division in ["D9", "D10", "D7"]:
        require(division in vargas, f"{fixture_id}.expected.vargas.{division} missing", errors)
        if vargas.get(division) is None:
            warnings.append(f"{fixture_id}.expected.vargas.{division} pending")


def validate_reference_file(
    path: Path,
    markers: list[str],
    label: str,
    errors: list[str],
) -> None:
    if not path.exists():
        errors.append(f"{label} reference missing: {path.name}")
        return

    text = path.read_text(encoding="utf-8")
    for marker in markers:
        require(marker in text, f"{label} missing marker: {marker}", errors)


def validate_reference_templates(fixture_id: str, errors: list[str]) -> None:
    validate_reference_file(
        REFERENCES_DIR / f"{fixture_id}_swiss_ephemeris.txt",
        REQUIRED_SWISS_REFERENCE_MARKERS,
        f"{fixture_id}.swiss_reference",
        errors,
    )
    validate_reference_file(
        REFERENCES_DIR / f"{fixture_id}_jhora.txt",
        REQUIRED_JHORA_REFERENCE_MARKERS,
        f"{fixture_id}.jhora_reference",
        errors,
    )
    validate_reference_file(
        REFERENCES_DIR / f"{fixture_id}_varshaphala_tajika.txt",
        REQUIRED_VARSHAPHALA_TAJIKA_REFERENCE_MARKERS,
        f"{fixture_id}.varshaphala_tajika_reference",
        errors,
    )


def validate_fixture(fixture: dict, errors: list[str], warnings: list[str]) -> None:
    fixture_id = fixture.get("id", "<missing-id>")
    require_keys(fixture, {"id", "label", "birth", "settings", "expected", "flags"}, fixture_id, errors)
    require(isinstance(fixture.get("id"), str) and fixture.get("id"), "fixture.id is empty", errors)

    birth = fixture.get("birth")
    require(isinstance(birth, dict), f"{fixture_id}.birth must be an object", errors)
    if isinstance(birth, dict):
        validate_birth(fixture_id, birth, errors)

    expected = fixture.get("expected")
    require(isinstance(expected, dict), f"{fixture_id}.expected must be an object", errors)
    if not isinstance(expected, dict):
        return

    source_status = expected.get("source_status")
    require(source_status in ALLOWED_SOURCE_STATUS, f"{fixture_id}.expected.source_status invalid: {source_status}", errors)
    if source_status == "swiss_only_pending_jhora":
        warnings.append(f"{fixture_id} awaits JHora cross-check")

    lagna = expected.get("lagna")
    require(isinstance(lagna, dict), f"{fixture_id}.expected.lagna must be filled", errors)
    if isinstance(lagna, dict):
        validate_lagna(fixture_id, lagna, errors)

    planets = expected.get("planets")
    if isinstance(planets, dict):
        validate_planets(fixture_id, planets, errors)
    else:
        errors.append(f"{fixture_id}.expected.planets must be filled")

    moon_nakshatra = expected.get("moon_nakshatra")
    require(isinstance(moon_nakshatra, dict), f"{fixture_id}.expected.moon_nakshatra must be filled", errors)
    if isinstance(moon_nakshatra, dict):
        validate_moon_nakshatra(fixture_id, moon_nakshatra, errors)

    validate_pending_fields(fixture_id, expected, errors, warnings)
    validate_reference_templates(fixture_id, errors)


def main() -> int:
    payload = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    require(isinstance(payload.get("fixtures"), list), "fixtures must be a list", errors)
    for fixture in payload.get("fixtures", []):
        validate_fixture(fixture, errors, warnings)

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {len(payload.get('fixtures', []))} golden fixture(s) and reference template(s) structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
