#!/usr/bin/env python3
"""Generate passive Swiss Ephemeris reference text for golden fixtures.

Default behavior prints to stdout only. Use --write explicitly to replace the
matching references/chart_*_swiss_ephemeris.txt files.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe


BASE_DIR = Path(__file__).resolve().parent
FIXTURES_PATH = BASE_DIR / "fixtures.json"
REFERENCES_DIR = BASE_DIR / "references"

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

NAKSHATRAS = [
    ("Ashwini", "Ketu"),
    ("Bharani", "Venus"),
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Mrigashira", "Mars"),
    ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"),
    ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"),
    ("Purva Phalguni", "Venus"),
    ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"),
    ("Chitra", "Mars"),
    ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"),
    ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"),
    ("Dhanishta", "Mars"),
    ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"),
    ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

NAKSHATRA_SPAN = 13.0 + 20.0 / 60.0

PLANETS = [
    (swe.SUN, "Sun"),
    (swe.MOON, "Moon"),
    (swe.MARS, "Mars"),
    (swe.MERCURY, "Mercury"),
    (swe.JUPITER, "Jupiter"),
    (swe.VENUS, "Venus"),
    (swe.SATURN, "Saturn"),
    (swe.TRUE_NODE, "Rahu (True)"),
]

SIGN_LORDS = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}


def dms(value: float) -> str:
    degrees = int(value)
    minute_float = (value - degrees) * 60.0
    minutes = int(minute_float)
    seconds = (minute_float - minutes) * 60.0
    return f"{degrees:02d}deg {minutes:02d}' {seconds:05.2f}\""


def sign_index(longitude: float) -> int:
    return int((longitude % 360.0) / 30.0)


def angular_distance(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def longitude_in_arc(longitude: float, start: float, end: float) -> bool:
    longitude = longitude % 360.0
    start = start % 360.0
    end = end % 360.0
    if start <= end:
        return start <= longitude < end
    return longitude >= start or longitude < end


def nakshatra(longitude: float) -> dict[str, object]:
    normalized = longitude % 360.0
    index = min(26, int(normalized / NAKSHATRA_SPAN))
    degree_in_nakshatra = normalized - (index * NAKSHATRA_SPAN)
    pada = min(4, int(degree_in_nakshatra / (NAKSHATRA_SPAN / 4.0)) + 1)
    name, lord = NAKSHATRAS[index]
    return {
        "name": name,
        "number": index + 1,
        "pada": pada,
        "lord": lord,
        "degree_in_nakshatra": degree_in_nakshatra,
    }


def local_to_utc(birth: dict[str, object]) -> tuple[datetime, datetime, str]:
    local_naive = datetime.fromisoformat(f"{birth['date']}T{birth['time']}:00")
    timezone_id = str(birth.get("timezone_id") or "").strip()
    if timezone_id:
        try:
            local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_id))
            return local_dt, local_dt.astimezone(timezone.utc), "timezone_id"
        except ZoneInfoNotFoundError:
            pass

    offset = float(birth["tz_offset"])
    fixed_zone = timezone(timedelta(hours=offset))
    local_dt = local_naive.replace(tzinfo=fixed_zone)
    return local_dt, local_dt.astimezone(timezone.utc), "fixed_tz_offset"


def julian_day(dt_utc: datetime) -> float:
    hour = (
        dt_utc.hour
        + (dt_utc.minute / 60.0)
        + (dt_utc.second / 3600.0)
        + (dt_utc.microsecond / 3_600_000_000.0)
    )
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def planet_rows(jd: float) -> list[dict[str, object]]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    rows = []
    rahu_row = None
    for body_id, name in PLANETS:
        position, _ = swe.calc_ut(jd, body_id, flags)
        longitude = position[0] % 360.0
        speed = position[3]
        idx = sign_index(longitude)
        row = {
            "name": name,
            "longitude": longitude,
            "sign": SIGNS[idx],
            "sign_index": idx,
            "degree": longitude % 30.0,
            "degree_str": dms(longitude % 30.0),
            "speed": speed,
            "retrograde": speed < 0 if body_id not in (swe.SUN, swe.MOON) else False,
            "nakshatra": nakshatra(longitude),
        }
        rows.append(row)
        if name == "Rahu (True)":
            rahu_row = row

    if rahu_row:
        ketu_longitude = (float(rahu_row["longitude"]) + 180.0) % 360.0
        idx = sign_index(ketu_longitude)
        rows.append({
            "name": "Ketu",
            "longitude": ketu_longitude,
            "sign": SIGNS[idx],
            "sign_index": idx,
            "degree": ketu_longitude % 30.0,
            "degree_str": dms(ketu_longitude % 30.0),
            "speed": rahu_row["speed"],
            "retrograde": bool(rahu_row["retrograde"]),
            "nakshatra": nakshatra(ketu_longitude),
            "derived_from": "opposite_true_rahu",
        })
    return rows


def ascendant(jd: float, lat: float, lon: float) -> dict[str, object]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", flags)
    longitude = ascmc[0] % 360.0
    idx = sign_index(longitude)
    return {
        "longitude": longitude,
        "sign": SIGNS[idx],
        "sign_index": idx,
        "degree": longitude % 30.0,
        "degree_str": dms(longitude % 30.0),
        "nakshatra": nakshatra(longitude),
    }


def whole_sign_house(longitude: float, lagna_longitude: float) -> int:
    lagna_sign_index = sign_index(lagna_longitude)
    planet_sign_index = sign_index(longitude)
    return ((planet_sign_index - lagna_sign_index) % 12) + 1


def sripati_houses(jd: float, lat: float, lon: float) -> list[dict[str, object]]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    cusps, _ascmc = swe.houses_ex(jd, lat, lon, b"O", flags)
    cusp_longitudes = [longitude % 360.0 for longitude in cusps[:12]]
    houses = []
    for index, cusp_longitude in enumerate(cusp_longitudes):
        previous_cusp = cusp_longitudes[index - 1]
        next_cusp = cusp_longitudes[(index + 1) % 12]
        idx = sign_index(cusp_longitude)
        houses.append({
            "house": index + 1,
            "cusp_longitude": cusp_longitude,
            "cusp_sign": SIGNS[idx],
            "cusp_sign_index": idx,
            "cusp_degree": cusp_longitude % 30.0,
            "cusp_degree_str": dms(cusp_longitude % 30.0),
            "start_longitude": (
                previous_cusp + ((cusp_longitude - previous_cusp) % 360.0) / 2.0
            ) % 360.0,
            "end_longitude": (
                cusp_longitude + ((next_cusp - cusp_longitude) % 360.0) / 2.0
            ) % 360.0,
            "lord": SIGN_LORDS[idx],
        })
    return houses


def sripati_house_for_longitude(longitude: float, houses: list[dict[str, object]]) -> int | None:
    for house in houses:
        if longitude_in_arc(
            longitude,
            float(house["start_longitude"]),
            float(house["end_longitude"]),
        ):
            return int(house["house"])
    return None


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def render_fixture(fixture: dict[str, object]) -> str:
    birth = fixture["birth"]
    local_dt, utc_dt, time_source = local_to_utc(birth)
    jd = julian_day(utc_dt)
    lat = float(birth["lat"])
    lon = float(birth["lon"])
    lagna = ascendant(jd, lat, lon)
    planets = planet_rows(jd)
    bhava_houses = sripati_houses(jd, lat, lon)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    planet_table = []
    bhava_planet_table = []
    for planet in planets:
        nak = planet["nakshatra"]
        planet_table.append([
            planet["name"],
            f"{float(planet['longitude']):.6f}",
            planet["sign"],
            planet["sign_index"],
            f"{float(planet['degree']):.6f}",
            planet["degree_str"],
            nak["name"],
            nak["pada"],
            f"{float(planet['speed']):.8f}",
            planet["retrograde"],
        ])
        bhava_house = sripati_house_for_longitude(float(planet["longitude"]), bhava_houses)
        cusp = next(
            (house for house in bhava_houses if house["house"] == bhava_house),
            None,
        )
        whole_house = whole_sign_house(float(planet["longitude"]), float(lagna["longitude"]))
        bhava_planet_table.append([
            planet["name"],
            f"{float(planet['longitude']):.6f}",
            whole_house,
            bhava_house or "",
            bool(bhava_house and bhava_house != whole_house),
            f"{angular_distance(float(planet['longitude']), float(cusp['cusp_longitude'])):.6f}" if cusp else "",
        ])

    bhava_house_table = [
        [
            house["house"],
            f"{float(house['cusp_longitude']):.6f}",
            house["cusp_sign"],
            house["cusp_sign_index"],
            f"{float(house['cusp_degree']):.6f}",
            house["cusp_degree_str"],
            f"{float(house['start_longitude']):.6f}",
            f"{float(house['end_longitude']):.6f}",
            house["lord"],
        ]
        for house in bhava_houses
    ]

    lines = [
        f"# {fixture['id']} - Swiss Ephemeris Reference",
        "",
        "Status: generated_with_python_swisseph",
        "",
        "Important note:",
        "- This is a Swiss Ephemeris raw reference, not an independent JHora cross-check.",
        "- It must not fill fixtures.json expected values alone if JHora disagrees.",
        "",
        "Birth data:",
        f"- Date: {birth['date']}",
        f"- Time: {birth['time']}",
        f"- Timezone: {birth.get('timezone_id')}",
        f"- UTC offset fixture value: {birth.get('tz_offset')}",
        f"- Place: {birth.get('place')}",
        f"- Latitude: {lat}",
        f"- Longitude: {lon}",
        "",
        "Computed reference:",
        f"- Local datetime: {local_dt.isoformat()}",
        f"- UTC datetime: {utc_dt.isoformat()}",
        f"- Time source: {time_source}",
        f"- Julian day UT: {jd:.8f}",
        f"- Swiss Ephemeris version: {getattr(swe, '__version__', 'unknown')}",
        f"- Ayanamsa: Lahiri / {ayanamsa:.8f}",
        f"- Node: True Rahu; Ketu derived as opposite point",
        f"- House system for ascendant call: Whole Sign (`houses_ex` code `W`)",
        f"- Bhava Chalit raw reference: Sripati/Porphyry (`houses_ex` code `O`)",
        "",
        "## Lagna",
        "",
        markdown_table(
            ["Longitude", "Sign", "Sign Index", "Degree", "Degree String", "Nakshatra", "Pada"],
            [[
                f"{float(lagna['longitude']):.6f}",
                lagna["sign"],
                lagna["sign_index"],
                f"{float(lagna['degree']):.6f}",
                lagna["degree_str"],
                lagna["nakshatra"]["name"],
                lagna["nakshatra"]["pada"],
            ]],
        ),
        "",
        "## Planets",
        "",
        markdown_table(
            [
                "Planet",
                "Longitude",
                "Sign",
                "Sign Index",
                "Degree",
                "Degree String",
                "Nakshatra",
                "Pada",
                "Speed",
                "Retrograde",
            ],
            planet_table,
        ),
        "",
        "## Bhava Chalit / Sripati Raw Reference",
        "",
        "Status: swiss_only_pending_jhora",
        "",
        "Important note:",
        "- This section is a raw Swiss reference for later cross-check.",
        "- It does not make `fixtures.json` expected.bhava_chalit final.",
        "- Whole Sign remains the primary house system in the application.",
        "- Rectification candidate windows and prediction ranges must not be collapsed by this table.",
        "",
        "### Sripati Cusps",
        "",
        markdown_table(
            [
                "House",
                "Cusp Longitude",
                "Cusp Sign",
                "Cusp Sign Index",
                "Cusp Degree",
                "Cusp Degree String",
                "Start Longitude",
                "End Longitude",
                "Lord",
            ],
            bhava_house_table,
        ),
        "",
        "### Planet House Assignment",
        "",
        markdown_table(
            [
                "Planet",
                "Longitude",
                "Whole Sign House",
                "Sripati Bhava House",
                "House Changed",
                "Distance From Cusp",
            ],
            bhava_planet_table,
        ),
        "",
        "## Not Included",
        "",
        "- Vimshottari dasha validation still needs the project dasha formula plus JHora cross-check.",
        "- D9/D10/D7 validation still needs a separate varga reference pass.",
        "- This output does not modify fixtures.json expected values.",
        "",
    ]
    return "\n".join(lines)


def load_fixtures() -> list[dict[str, object]]:
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return data["fixtures"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate passive Swiss Ephemeris reference text for golden fixtures."
    )
    parser.add_argument(
        "--fixture",
        action="append",
        help="Fixture id to render. Can be passed multiple times. Defaults to all.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Replace references/chart_*_swiss_ephemeris.txt files. Default prints only.",
    )
    args = parser.parse_args()

    selected_ids = set(args.fixture or [])
    fixtures = [
        fixture for fixture in load_fixtures()
        if not selected_ids or fixture["id"] in selected_ids
    ]
    missing = selected_ids - {fixture["id"] for fixture in fixtures}
    if missing:
        raise SystemExit(f"Unknown fixture id(s): {', '.join(sorted(missing))}")

    for index, fixture in enumerate(fixtures):
        rendered = render_fixture(fixture)
        if args.write:
            target = REFERENCES_DIR / f"{fixture['id']}_swiss_ephemeris.txt"
            target.write_text(rendered, encoding="utf-8")
            print(f"wrote {target}")
            continue

        if index:
            print("\n" + "=" * 80 + "\n")
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
