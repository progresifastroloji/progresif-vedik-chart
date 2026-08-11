import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import DEFAULT, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import (  # noqa: E402
    ABDA_BALA_LORD_SEQUENCE,
    CHESHTA_CLASS_SCORES,
    CHESHTA_MEAN_DAILY_SPEEDS,
    MASA_BALA_EPOCH_DAY_COUNT,
    MASA_BALA_LORD_SEQUENCE,
    PLANETARY_HOUR_SEQUENCE,
    SAPTAVARGA_DIVISIONS,
    VARGA_NAMES,
    _build_budha_aditya_yogas,
    _build_chandra_mangala_yogas,
    _build_rectification_decision,
    _build_rectification_v1_status,
    _build_parivartana_yogas,
    _build_rectification_embedded_markdown,
    _rectification_ranking_mode,
    _build_session_preparation_package_markdown,
    _build_war_map,
    _build_transit_pack,
    _build_varshaphala_analysis_data_package_markdown,
    _career_selected_transit_coverage_rows,
    _abda_bala_detail,
    _active_transit_source_markdown,
    _active_dasha_chain_for_jd,
    _active_vimshottari_chain_direct,
    _combustion_for_planet,
    _build_vimshottari_maha_tree,
    _cheshta_bala_score,
    _dignity_for_planet,
    _dig_bala_score,
    _expert_graha_yuddha_rows,
    _hora_bala_detail,
    _latest_saved_transit_pack,
    _latest_saved_transit_range_pack,
    _masa_bala_detail,
    _natonnata_bala_detail,
    _ojayugma_bala_detail,
    _paksha_bala_detail,
    _parse_vault_natal_birth,
    _parashari_drik_aspect_virupa,
    _planet_package_point,
    _rectification_event_rule,
    _rectification_score_event,
    _rectification_expected_lagna_from_birth_base,
    _resolve_timezone_offset,
    _save_analysis_data_packages,
    _saptavargaja_bala_detail,
    _solar_meridian_context,
    _topic_planet,
    _topic_shadbala,
    _topic_varga_planet,
    _transit_pack_dates,
    _transit_reference_from_options,
    _vara_bala_detail,
    _yuddha_bala_detail,
    _varga_position_from_longitude,
    app,
    calculate_chart,
    date_to_jd,
)


ASTROSEEK_VERIFIED_PERSON_VARGAS = [
    "D2",
    "D3",
    "D4",
    "D6",
    "D7",
    "D9",
    "D10",
    "D11",
    "D12",
    "D20",
    "D24",
    "D30",
    "D60",
]

RECTIFIED_VARGAS = [
    "D1",
    "D2",
    "D3",
    "D4",
    "D6",
    "D7",
    "D9",
    "D10",
    "D11",
    "D12",
    "D20",
    "D24",
    "D30",
    "D60",
]

GOLDEN_FIXTURES_PATH = PROJECT_ROOT / "tests" / "golden" / "fixtures.json"


class ChartApiV2Test(unittest.TestCase):
    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_beta_daily_chat_limit = app.config["BETA_DAILY_CHAT_LIMIT"]
        self._beta_tmp = tempfile.TemporaryDirectory()
        app.config["BETA_DB_PATH"] = str(Path(self._beta_tmp.name) / "beta.sqlite3")
        app.config["BETA_DAILY_CHAT_LIMIT"] = 20
        self.client = app.test_client()
        from rectification_app import rectification_app
        self.rectification_client = rectification_app.test_client()

    def tearDown(self):
        app.config["BETA_DB_PATH"] = self._old_beta_db_path
        app.config["BETA_DAILY_CHAT_LIMIT"] = self._old_beta_daily_chat_limit
        self._beta_tmp.cleanup()

    def test_topic_planet_helpers_normalize_rahu_names(self):
        chart = {
            "planets": [
                {"name": "Rahu (True)", "sign_index": 2},
                {"name": "Ketu", "sign_index": 8},
            ],
            "vargas": {
                "D9": {
                    "planets": [
                        {"name": "Rahu (True)", "sign_index": 4},
                        {"name": "Ketu", "sign_index": 10},
                    ],
                },
            },
            "shadbala": {
                "planets": [
                    {"planet": "Rahu (True)", "total_score": 1.0},
                ],
            },
        }

        self.assertEqual(_topic_planet(chart, "Rahu")["sign_index"], 2)
        self.assertEqual(_topic_planet(chart, "Rahu (True)")["sign_index"], 2)
        self.assertEqual(
            _topic_varga_planet(chart, "D9", "Rahu")["sign_index"],
            4,
        )
        self.assertEqual(_topic_shadbala(chart, "Rahu")["total_score"], 1.0)
        self.assertEqual(
            _planet_package_point(chart, "Rahu")["sign_index"],
            2,
        )

    def _assert_astroseek_verified_vargas(self, data):
        self.assertEqual(
            data["data_quality"]["person_verified_vargas"],
            ASTROSEEK_VERIFIED_PERSON_VARGAS,
        )
        for division in ASTROSEEK_VERIFIED_PERSON_VARGAS:
            self.assertEqual(data["vargas"][division]["confidence"], "high")
            self.assertEqual(
                data["vargas"][division]["external_validation"]["status"],
                "customer_time_declaration_policy",
            )
            self.assertEqual(
                data["data_quality"]["varga_interpretation_confidence"][division],
                "high",
            )

        self.assertNotIn("D2", data["birth_time_policy"]["low_confidence_interpretations"])
        self.assertNotIn("D60", data["birth_time_policy"]["low_confidence_interpretations"])

    def _assert_rectified_vargas_confidence(
        self,
        data,
        expected_status="customer_time_declaration_policy",
    ):
        self.assertEqual(
            data["data_quality"]["supported_vargas"],
            RECTIFIED_VARGAS,
        )
        for division in RECTIFIED_VARGAS:
            expected_confidence = "high"
            self.assertEqual(
                data["vargas"][division]["confidence"],
                expected_confidence,
            )
            self.assertEqual(
                data["vargas"][division]["external_validation"]["status"],
                expected_status,
            )
            self.assertEqual(
                data["data_quality"]["varga_interpretation_confidence"][division],
                expected_confidence,
            )

        self.assertNotIn("D1", data["birth_time_policy"]["low_confidence_interpretations"])
        self.assertNotIn("D60", data["birth_time_policy"]["low_confidence_interpretations"])

    def _load_golden_fixtures(self):
        payload = json.loads(GOLDEN_FIXTURES_PATH.read_text(encoding="utf-8"))
        return payload["fixtures"]

    def _golden_chart_payload(self, fixture):
        year, month, day = [int(part) for part in fixture["birth"]["date"].split("-")]
        hour, minute = [int(part) for part in fixture["birth"]["time"].split(":")[:2]]
        return {
            "person": {
                "id": fixture["id"],
                "name": fixture["label"],
            },
            "birth": {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute,
                "timezone_id": fixture["birth"]["timezone_id"],
                "lat": fixture["birth"]["lat"],
                "lon": fixture["birth"]["lon"],
                "place": fixture["birth"]["place"],
                "time_confidence": "high",
            },
            "options": {
                "ayanamsa": "Lahiri",
                "zodiac": "sidereal",
                "house_system": "whole_sign",
                "node_type": "true",
                "language": "tr",
            },
        }

    def _normalized_golden_planet_name(self, name):
        return "Rahu (True)" if name in {"Rahu", "Rahu (True)"} else name

    def _assert_golden_vimshottari_matches_api(self, fixture, data):
        expected = fixture["expected"].get("vimshottari_active")
        self.assertIsInstance(expected, dict, fixture["id"])
        self.assertEqual(
            expected.get("levels_verified"),
            ["maha", "antara", "pratyantar"],
            fixture["id"],
        )
        active = data["dashas"]["vimshottari"]["active"]
        for level in expected["levels_verified"]:
            self.assertEqual(
                active[level]["lord"],
                expected[level],
                f"{fixture['id']} vimshottari.{level}",
            )
        fine_level_status = expected.get("fine_level_status")
        self.assertIn(
            fine_level_status,
            {"pending_jhora_alignment", "aligned_in_external_reference"},
            fixture["id"],
        )
        if fine_level_status != "aligned_in_external_reference":
            return

        alignment = data["dashas"]["vimshottari"]["external_reference_alignment"]
        self.assertEqual(
            alignment["status"],
            "implemented_jhora_fine_level_alignment",
            fixture["id"],
        )
        self.assertEqual(alignment["sidereal_mode"], "SIDM_TRUE_CITRA", fixture["id"])
        self.assertEqual(
            alignment["levels"],
            ["maha", "antara", "pratyantar", "sookshma", "prana", "deha"],
            fixture["id"],
        )
        reference_active = alignment["birth_active"]
        jhora_fine = expected["jhora_visible_fine_levels"]
        for level in ["maha", "antara", "pratyantar"]:
            self.assertEqual(
                reference_active[level]["lord"],
                expected[level],
                f"{fixture['id']} jhora_reference.{level}",
            )
        for level in ["sookshma", "prana"]:
            self.assertEqual(
                reference_active[level]["lord"],
                jhora_fine[level],
                f"{fixture['id']} jhora_reference.{level}",
            )
        self.assertIn("deha", reference_active, f"{fixture['id']} jhora_reference.deha")
        self.assertEqual(
            alignment["deha_status"],
            "candidate_pending_jhora_timing_window_validation",
            fixture["id"],
        )
        self.assertNotEqual(
            reference_active["deha"]["lord"],
            jhora_fine["deha"],
            f"{fixture['id']} deha_not_promoted_to_jhora_alignment",
        )
        self.assertNotIn("deha", active, f"{fixture['id']} primary_lahiri.deha")

    def _assert_golden_vargas_match_api(self, fixture, data):
        expected_vargas = fixture["expected"]["vargas"]
        for division in ["D9", "D10", "D7"]:
            expected = expected_vargas.get(division)
            self.assertIsInstance(expected, dict, f"{fixture['id']} {division}")
            api_varga = data["vargas"][division]
            api_positions = {
                "Lagna": api_varga["lagna"]["sign"],
            }
            api_positions.update({
                self._normalized_golden_planet_name(planet["name"]): planet["sign"]
                for planet in api_varga["planets"]
            })
            for point, expected_sign in expected.items():
                if point in {"source", "cross_check"}:
                    continue
                self.assertEqual(
                    api_positions.get(point),
                    expected_sign,
                    f"{fixture['id']} {division}.{point}",
                )

    def _assert_golden_bhava_chalit_matches_api(self, fixture, data):
        expected = fixture["expected"].get("bhava_chalit")
        self.assertIsInstance(expected, dict, fixture["id"])
        bhava = data["bhava_chalit"]
        self.assertEqual(bhava["status"], "implemented_passive_technical_layer")
        self.assertEqual(len(bhava["houses"]), 12)

        expected_planets = expected.get("planets") or {}
        if expected_planets:
            api_planets = {
                self._normalized_golden_planet_name(planet["planet"]): planet
                for planet in bhava["planets"]
            }
            for planet_name, expected_planet in expected_planets.items():
                self.assertEqual(
                    api_planets[planet_name]["whole_sign_house"],
                    expected_planet["whole_sign_house"],
                    f"{fixture['id']} bhava_chalit.{planet_name}.whole_sign_house",
                )
                self.assertEqual(
                    api_planets[planet_name]["bhava_chalit_house"],
                    expected_planet["bhava_chalit_house"],
                    f"{fixture['id']} bhava_chalit.{planet_name}.bhava_chalit_house",
                )
                self.assertEqual(
                    api_planets[planet_name]["house_changed"],
                    expected_planet["house_changed"],
                    f"{fixture['id']} bhava_chalit.{planet_name}.house_changed",
                )

    def test_chart_full_matches_golden_external_reference_layers(self):
        for fixture in self._load_golden_fixtures():
            with self.subTest(fixture=fixture["id"]):
                self.assertEqual(
                    fixture["expected"]["source_status"],
                    "swiss_and_jhora_matched",
                )
                response = self.client.post(
                    "/api/v2/chart/full",
                    json=self._golden_chart_payload(fixture),
                )

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self._assert_golden_vimshottari_matches_api(fixture, data)
                self._assert_golden_vargas_match_api(fixture, data)
                self._assert_golden_bhava_chalit_matches_api(fixture, data)

    def test_shadbala_saptavargaja_uses_classical_compound_relationship_scores(self):
        self.assertEqual(
            SAPTAVARGA_DIVISIONS,
            ["D1", "D2", "D3", "D7", "D9", "D12", "D30"],
        )

        def planets_with_positions(overrides):
            planets = []
            defaults = {
                "Sun": 4,
                "Moon": 3,
                "Mars": 0,
                "Mercury": 2,
                "Jupiter": 8,
                "Venus": 1,
                "Saturn": 10,
            }
            for planet_name, default_sign in defaults.items():
                sign_index = overrides.get(planet_name, default_sign)
                planets.append({
                    "name": planet_name,
                    "varga_status": {
                        division: {
                            "sign": f"Sign-{sign_index}",
                            "sign_index": sign_index,
                            "degree": 10.0,
                        }
                        for division in SAPTAVARGA_DIVISIONS
                    },
                })
            return planets

        own_planets = planets_with_positions({"Sun": 4})
        own_detail = _saptavargaja_bala_detail(own_planets[0], own_planets)
        self.assertEqual(own_detail["rows"][0]["dignity"], "moolatrikona")
        self.assertEqual(own_detail["rows"][0]["score"], 45.0)
        self.assertEqual(own_detail["rows"][0]["compound_relationship"], "self")
        self.assertTrue(
            all(row["score"] == 30.0 for row in own_detail["rows"][1:])
        )

        friend_planets = planets_with_positions({"Sun": 0, "Mars": 1})
        friend_detail = _saptavargaja_bala_detail(
            friend_planets[0],
            friend_planets,
        )
        self.assertTrue(
            all(
                row["compound_relationship"] == "great_friend"
                and row["score"] == 22.5
                for row in friend_detail["rows"]
            )
        )

        enemy_planets = planets_with_positions({"Sun": 6, "Venus": 6})
        enemy_detail = _saptavargaja_bala_detail(
            enemy_planets[0],
            enemy_planets,
        )
        self.assertTrue(
            all(
                row["compound_relationship"] == "great_enemy"
                and row["score"] == 1.875
                for row in enemy_detail["rows"]
            )
        )

        data = self._sample_v2_chart()
        for planet in data["shadbala"]["planets"]:
            saptavargaja = (
                planet["components"]["sthana_bala"]["components"]["saptavargaja_bala"]
            )
            self.assertEqual(
                saptavargaja["divisions_used"],
                SAPTAVARGA_DIVISIONS,
            )
            self.assertNotIn(
                "D30_trimsamsa_not_available_in_current_engine",
                saptavargaja["excluded_rules"],
            )
            self.assertEqual(
                saptavargaja["classical_total_virupa"],
                saptavargaja["raw_total"],
            )

    def test_shadbala_ojayugma_uses_d1_and_d9_parity(self):
        cases = [
            ("Moon", 1, 3, "even", 30.0),
            ("Sun", 0, 1, "odd", 15.0),
            ("Mercury", 0, 2, "odd", 30.0),
            ("Saturn", 1, 3, "odd", 0.0),
        ]
        for planet_name, d1_sign, d9_sign, expected_parity, expected_score in cases:
            with self.subTest(planet=planet_name):
                detail = _ojayugma_bala_detail({
                    "name": planet_name,
                    "sign": VARGA_NAMES.get("D1", "Rashi"),
                    "sign_index": d1_sign,
                    "varga_status": {
                        "D9": {
                            "sign": VARGA_NAMES["D9"],
                            "sign_index": d9_sign,
                        },
                    },
                })
                self.assertEqual(detail["expected_parity"], expected_parity)
                self.assertEqual(detail["divisions_used"], ["D1", "D9"])
                self.assertEqual(detail["score"], expected_score)
                self.assertEqual(
                    detail["score"],
                    sum(row["score"] for row in detail["rows"]),
                )

    def test_shadbala_dig_bala_uses_exact_cardinal_longitudes(self):
        angles = {
            "lagna": {"longitude": 10.0},
            "dsc": {"longitude": 190.0},
            "mc": {"longitude": 100.0},
        }
        cases = [
            ("Sun", 100.0, 280.0, "mc", "ic"),
            ("Mars", 100.0, 280.0, "mc", "ic"),
            ("Moon", 280.0, 100.0, "ic", "mc"),
            ("Venus", 280.0, 100.0, "ic", "mc"),
            ("Jupiter", 10.0, 190.0, "lagna", "dsc"),
            ("Mercury", 10.0, 190.0, "lagna", "dsc"),
            ("Saturn", 190.0, 10.0, "dsc", "lagna"),
        ]

        for planet_name, strong, weak, strong_angle, weak_angle in cases:
            planet = {"name": planet_name, "longitude": strong, "house": 1}
            strong_score, strong_detail = _dig_bala_score(planet, angles)
            self.assertEqual(strong_score, 60.0, planet_name)
            self.assertEqual(strong_detail["strongest_angle"], strong_angle)
            self.assertEqual(strong_detail["weakest_angle"], weak_angle)
            self.assertEqual(strong_detail["angular_distance_from_strongest"], 0.0)
            self.assertEqual(strong_detail["angular_distance_from_weakest"], 180.0)

            planet["longitude"] = weak
            weak_score, weak_detail = _dig_bala_score(planet, angles)
            self.assertEqual(weak_score, 0.0, planet_name)
            self.assertEqual(weak_detail["angular_distance_from_strongest"], 180.0)
            self.assertEqual(weak_detail["angular_distance_from_weakest"], 0.0)

            planet["longitude"] = (weak + 90.0) % 360.0
            midpoint_score, midpoint_detail = _dig_bala_score(planet, angles)
            self.assertEqual(midpoint_score, 30.0, planet_name)
            self.assertEqual(midpoint_detail["angular_distance_from_weakest"], 90.0)

    def test_shadbala_cheshta_uses_planet_specific_speed_classes(self):
        mean_speed = CHESHTA_MEAN_DAILY_SPEEDS["Mars"]
        cases = [
            (0.00, False, "vikala", 15.0),
            (0.25, False, "mandatara", 7.5),
            (0.60, False, "manda", 15.0),
            (1.00, False, "sama", 30.0),
            (1.50, False, "chara", 45.0),
            (2.00, False, "atichara", 30.0),
            (-0.20, True, "anuvakra", 30.0),
            (-1.00, True, "vakra", 60.0),
        ]

        for ratio, retrograde, expected_class, expected_score in cases:
            planet = {
                "name": "Mars",
                "motion": {
                    "speed": mean_speed * ratio,
                    "speed_status": "retrograde" if retrograde else "normal",
                    "retrograde": retrograde,
                },
            }
            score, factors, detail = _cheshta_bala_score(planet)
            self.assertEqual(score, expected_score, expected_class)
            self.assertEqual(detail["motion_class"], expected_class)
            self.assertEqual(detail["class_score"], expected_score)
            self.assertEqual(
                detail["mean_daily_speed"],
                CHESHTA_MEAN_DAILY_SPEEDS["Mars"],
            )
            self.assertAlmostEqual(
                detail["normalized_speed_ratio"],
                abs(ratio),
                places=6,
            )
            self.assertEqual(
                CHESHTA_CLASS_SCORES[expected_class],
                expected_score,
            )
            self.assertIn(expected_class, factors)

    def test_shadbala_hora_bala_uses_unequal_day_and_night_hours(self):
        self.assertEqual(
            PLANETARY_HOUR_SEQUENCE,
            ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"],
        )
        day_context = {
            "start_jd": 100.0,
            "duration": 0.5,
            "birth_jd": 100.0,
            "period": "day",
            "day_lord": "Sun",
        }
        sun_detail = _hora_bala_detail({"name": "Sun"}, day_context)
        self.assertEqual(sun_detail["hora_number"], 1)
        self.assertEqual(sun_detail["hora_lord"], "Sun")
        self.assertEqual(sun_detail["score"], 60.0)

        day_context["birth_jd"] = 100.0 + day_context["duration"] / 12.0
        venus_detail = _hora_bala_detail({"name": "Venus"}, day_context)
        self.assertEqual(venus_detail["hora_number"], 2)
        self.assertEqual(venus_detail["hora_lord"], "Venus")
        self.assertEqual(venus_detail["score"], 60.0)

        night_context = {
            "start_jd": 100.5,
            "duration": 0.5,
            "birth_jd": 100.5,
            "period": "night",
            "day_lord": "Sun",
        }
        jupiter_detail = _hora_bala_detail({"name": "Jupiter"}, night_context)
        self.assertEqual(jupiter_detail["hora_number"], 13)
        self.assertEqual(jupiter_detail["hora_lord"], "Jupiter")
        self.assertEqual(jupiter_detail["score"], 60.0)
        self.assertEqual(
            _hora_bala_detail({"name": "Sun"}, night_context)["score"],
            0.0,
        )

    def test_shadbala_vara_bala_uses_sunrise_based_planetary_day(self):
        before_sunrise_context = {
            "period": "night",
            "day_lord": "Saturn",
            "planetary_day_start_jd": 100.25,
        }
        saturn_detail = _vara_bala_detail(
            {"name": "Saturn"},
            before_sunrise_context,
        )
        sun_detail = _vara_bala_detail(
            {"name": "Sun"},
            before_sunrise_context,
        )

        self.assertEqual(saturn_detail["score"], 45.0)
        self.assertEqual(saturn_detail["vara_lord"], "Saturn")
        self.assertEqual(saturn_detail["period"], "night")
        self.assertEqual(saturn_detail["planetary_day_start_jd"], 100.25)
        self.assertEqual(sun_detail["score"], 0.0)

        unavailable = _vara_bala_detail({"name": "Saturn"}, None)
        self.assertEqual(unavailable["score"], 0.0)
        self.assertIsNone(unavailable["vara_lord"])

    def test_shadbala_natonnata_uses_solar_midnight_noon_arc(self):
        midnight_context = {
            "period": "night",
            "previous_anchor": {"type": "solar_midnight", "jd": 100.0},
            "next_anchor": {"type": "solar_noon", "jd": 100.5},
            "elapsed_ratio": 0.0,
            "day_strength_virupa": 0.0,
            "night_strength_virupa": 60.0,
            "nearest_solar_noon_jd": 100.5,
            "nearest_solar_midnight_jd": 100.0,
        }
        self.assertEqual(
            _natonnata_bala_detail({"name": "Sun"}, midnight_context)["score"],
            0.0,
        )
        self.assertEqual(
            _natonnata_bala_detail({"name": "Moon"}, midnight_context)["score"],
            60.0,
        )
        self.assertEqual(
            _natonnata_bala_detail({"name": "Mercury"}, midnight_context)["score"],
            60.0,
        )

        midpoint_context = {
            **midnight_context,
            "elapsed_ratio": 0.5,
            "day_strength_virupa": 30.0,
            "night_strength_virupa": 30.0,
        }
        self.assertEqual(
            _natonnata_bala_detail({"name": "Jupiter"}, midpoint_context)["score"],
            30.0,
        )
        self.assertEqual(
            _natonnata_bala_detail({"name": "Saturn"}, midpoint_context)["score"],
            30.0,
        )

        birth = {
            "year": 1978,
            "month": 5,
            "day": 28,
            "hour": 0,
            "minute": 15,
            "lat": 40.7654,
            "lon": 29.9408,
        }
        birth_jd = date_to_jd(1978, 5, 28, 0, 15, 3.0)
        real_context = _solar_meridian_context(birth, 3.0, birth_jd)
        self.assertIsNotNone(real_context)
        self.assertNotEqual(
            real_context["previous_anchor"]["type"],
            real_context["next_anchor"]["type"],
        )
        self.assertAlmostEqual(
            real_context["day_strength_virupa"]
            + real_context["night_strength_virupa"],
            60.0,
            places=2,
        )

    def test_shadbala_paksha_bala_doubles_moon_value(self):
        full_moon_chart = {
            "planets": [
                {"abbr": "Su", "longitude": 0.0},
                {"abbr": "Mo", "longitude": 180.0},
            ],
        }

        moon_detail = _paksha_bala_detail(
            {"name": "Moon"},
            full_moon_chart,
        )
        venus_detail = _paksha_bala_detail(
            {"name": "Venus"},
            full_moon_chart,
        )
        sun_detail = _paksha_bala_detail(
            {"name": "Sun"},
            full_moon_chart,
        )

        self.assertEqual(moon_detail["base_score"], 60.0)
        self.assertEqual(moon_detail["multiplier"], 2.0)
        self.assertEqual(moon_detail["final_virupa"], 120.0)
        self.assertEqual(moon_detail["score"], 120.0)
        self.assertEqual(moon_detail["max_virupa"], 120.0)
        self.assertEqual(venus_detail["score"], 60.0)
        self.assertEqual(venus_detail["multiplier"], 1.0)
        self.assertEqual(sun_detail["score"], 0.0)

    def test_rectification_legal_event_rule_is_supported(self):
        rule_key, rule = _rectification_event_rule("mahkeme")

        self.assertEqual(rule_key, "legal")
        self.assertEqual(rule["topic"], "legal")
        self.assertEqual(rule["houses"], [6, 7, 8, 9, 12])
        self.assertIn("Jupiter", rule["planets"])
        self.assertIn("D10", rule["vargas"])

    def test_rectification_embedded_record_excludes_candidate_report(self):
        text = _build_rectification_embedded_markdown({
            "person": {"name": "Test", "group": "Grup-01"},
            "analysis_profile": {"mode": "technical"},
            "birth_base": {
                "year": 1980,
                "month": 5,
                "day": 19,
                "hour": 4,
                "minute": 30,
                "tz_offset": 3,
                "timezone_id": "Europe/Istanbul",
            },
            "birth_window": {
                "timezone_id": "Europe/Istanbul",
            },
            "source_docs": [],
            "search_window": {
                "start_time": "04:00:00",
                "end_time": "05:00:00",
                "step_minutes": 1,
                "step_seconds": 0,
            },
            "events": [],
        })

        self.assertNotIn("### Rektifikasyon API Payload", text)
        self.assertNotIn("### Rektifikasyon Teknik Rapor Snapshot", text)
        self.assertNotIn('"candidate_rankings"', text)

    def test_rectification_decision_blocks_underqualified_data(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 42.0},
                {"time": "01:05:00", "hour": 1, "minute": 5, "second": 0, "ranking_score": 21.0},
            ],
            {
                "professional_readiness": "partial",
                "event_count": 5,
                "documented_event_count": 1,
                "source_quality": "weak",
                "source_doc_count": 0,
            },
            [
                {"field": "events", "status": "recommended_more_data"},
                {"field": "source_docs", "status": "missing"},
                {"field": "birth_window.source_quality", "status": "low_or_unknown"},
            ],
        )

        self.assertEqual(decision["status"], "not_ready")
        self.assertEqual(decision["confidence"], "low")
        self.assertIsNone(decision["suggested_time"])
        self.assertEqual(decision["score_gap"], 21.0)
        self.assertEqual(len(decision["blocking_factors"]), 3)
        self.assertFalse(decision["selection_allowed"])
        self.assertIn(
            "source_docs_missing",
            {flag["code"] for flag in decision["review_flags"]},
        )

    def test_rectification_decision_marks_close_scores_ambiguous(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 42.0},
                {"time": "01:05:00", "hour": 1, "minute": 5, "second": 0, "ranking_score": 40.5},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 9,
                "documented_event_count": 4,
                "source_quality": "silver",
                "source_doc_count": 2,
            },
            [],
        )

        self.assertEqual(decision["status"], "ambiguous")
        self.assertIsNone(decision["suggested_time"])
        self.assertEqual(decision["score_gap"], 1.5)
        self.assertFalse(decision["selection_allowed"])

    def test_rectification_decision_blocks_exact_time_selection_until_calibrated(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 42.0},
                {"time": "01:05:00", "hour": 1, "minute": 5, "second": 0, "ranking_score": 31.0},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
        )

        self.assertEqual(decision["status"], "review_window")
        self.assertEqual(decision["confidence"], "medium")
        self.assertIsNone(decision["suggested_time"])
        self.assertEqual(decision["score_gap"], 11.0)
        self.assertFalse(decision["selection_allowed"])
        self.assertFalse(decision["quality_gate"]["exact_time_selection_enabled"])
        self.assertIn("exact_time_selection_disabled_until_calibrated", decision["safety_notes"])

    def test_rectification_decision_allows_clear_candidate_with_explicit_calibration_gate(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 42.0},
                {"time": "01:05:00", "hour": 1, "minute": 5, "second": 0, "ranking_score": 31.0},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
            {"allow_exact_time_selection": True},
        )

        self.assertEqual(decision["status"], "candidate_for_review")
        self.assertEqual(decision["suggested_time"], "01:00:00")
        self.assertTrue(decision["selection_allowed"])
        self.assertTrue(decision["quality_gate"]["exact_time_selection_enabled"])

    def test_rectification_v1_status_maps_decision_to_product_state(self):
        ready = {"status": "ready"}
        partial = {"status": "partial"}

        review_window = _build_rectification_v1_status(
            {
                "status": "review_window",
                "selection_allowed": False,
                "suggested_window": {"start_time": "01:00:00", "end_time": "01:10:00"},
                "score_gap": 11.0,
            },
            ready,
        )
        self.assertEqual(review_window["code"], "candidate_window_available")
        self.assertFalse(review_window["can_save_rectified_time"])
        self.assertFalse(review_window["final_birth_time_claim_allowed"])

        insufficient = _build_rectification_v1_status(
            {
                "status": "not_ready",
                "selection_allowed": False,
                "blocking_factors": [{"field": "source_docs"}],
            },
            partial,
        )
        self.assertEqual(insufficient["code"], "insufficient_data")
        self.assertIn("source_docs", insufficient["blocking_codes"])

        selectable = _build_rectification_v1_status(
            {
                "status": "candidate_for_review",
                "selection_allowed": True,
                "suggested_time": "01:00:00",
                "score_gap": 11.0,
            },
            ready,
        )
        self.assertEqual(selectable["code"], "review_candidate_available")
        self.assertTrue(selectable["can_save_rectified_time"])
        self.assertFalse(selectable["final_birth_time_claim_allowed"])

    def test_rectification_decision_blocks_single_candidate_window(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:40:00", "hour": 1, "minute": 40, "second": 0, "ranking_score": 42.0},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
        )

        self.assertEqual(decision["status"], "not_ready")
        self.assertEqual(decision["confidence"], "low")
        self.assertIsNone(decision["suggested_time"])
        self.assertFalse(decision["selection_allowed"])
        self.assertIn(
            "single_candidate_window_no_real_scan",
            {flag["code"] for flag in decision["review_flags"]},
        )

    def test_rectification_decision_blocks_poor_minute_discrimination(self):
        decision = _build_rectification_decision(
            [
                {
                    "time": "01:00:00",
                    "hour": 1,
                    "minute": 0,
                    "second": 0,
                    "ranking_score": 42.0,
                    "event_total_score": 20.0,
                    "average_event_score": 4.0,
                },
                {
                    "time": "01:35:00",
                    "hour": 1,
                    "minute": 35,
                    "second": 0,
                    "ranking_score": 31.0,
                    "event_total_score": 19.7,
                    "average_event_score": 3.94,
                },
                {
                    "time": "02:10:00",
                    "hour": 2,
                    "minute": 10,
                    "second": 0,
                    "ranking_score": 29.5,
                    "event_total_score": 19.5,
                    "average_event_score": 3.9,
                },
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
        )

        self.assertEqual(decision["status"], "not_ready")
        self.assertFalse(decision["selection_allowed"])
        self.assertEqual(decision["score_diagnostics"]["average_event_score_range"], 0.1)
        self.assertIn(
            "event_score_not_minute_discriminative",
            {flag["code"] for flag in decision["review_flags"]},
        )

    def test_direct_vimshottari_chain_matches_full_tree_for_rectification(self):
        chart = calculate_chart(1978, 5, 28, 0, 15, 3.0, 40.7654, 29.9408)
        birth_jd = date_to_jd(1978, 5, 28, 0, 15, 3.0)
        event_jd = date_to_jd(2021, 3, 12, 12, 0, 3.0)
        moon = next(planet for planet in chart["planets"] if planet["abbr"] == "Mo")
        full_tree = _build_vimshottari_maha_tree(moon["longitude"], birth_jd)

        direct = _active_vimshottari_chain_direct(moon["longitude"], birth_jd, event_jd)
        from_tree = _active_dasha_chain_for_jd(full_tree, event_jd)

        self.assertEqual(direct["path"], from_tree["path"])
        for level in ["maha", "antara", "pratyantar", "sookshma", "prana"]:
            self.assertEqual(direct[level]["lord"], from_tree[level]["lord"])
            self.assertAlmostEqual(
                direct[level]["actual_start_jd"],
                from_tree[level]["actual_start_jd"],
                places=5,
            )
            self.assertAlmostEqual(
                direct[level]["actual_end_jd"],
                from_tree[level]["actual_end_jd"],
                places=5,
            )

    def test_rectification_decision_blocks_start_boundary_hugging_candidate(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 42.0},
                {"time": "01:10:00", "hour": 1, "minute": 10, "second": 0, "ranking_score": 31.0},
                {"time": "01:20:00", "hour": 1, "minute": 20, "second": 0, "ranking_score": 28.0},
                {"time": "01:30:00", "hour": 1, "minute": 30, "second": 0, "ranking_score": 24.0},
                {"time": "01:40:00", "hour": 1, "minute": 40, "second": 0, "ranking_score": 20.0},
                {"time": "01:50:00", "hour": 1, "minute": 50, "second": 0, "ranking_score": 18.0},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
            {
                "allow_exact_time_selection": True,
                "candidate_count": 6,
                "search_window": {
                    "start_time": "01:00:00",
                    "end_time": "01:50:00",
                    "step_minutes": 10,
                    "step_seconds": 0,
                },
            },
        )

        self.assertEqual(decision["status"], "not_ready")
        self.assertIsNone(decision["suggested_time"])
        self.assertFalse(decision["selection_allowed"])
        boundary_flag = next(
            flag for flag in decision["review_flags"] if flag["code"] == "boundary_candidate_bias"
        )
        self.assertEqual(boundary_flag["edge"], "start")

    def test_rectification_decision_blocks_end_boundary_hugging_candidate(self):
        decision = _build_rectification_decision(
            [
                {"time": "01:50:00", "hour": 1, "minute": 50, "second": 0, "ranking_score": 42.0},
                {"time": "01:40:00", "hour": 1, "minute": 40, "second": 0, "ranking_score": 31.0},
                {"time": "01:30:00", "hour": 1, "minute": 30, "second": 0, "ranking_score": 28.0},
                {"time": "01:20:00", "hour": 1, "minute": 20, "second": 0, "ranking_score": 24.0},
                {"time": "01:10:00", "hour": 1, "minute": 10, "second": 0, "ranking_score": 20.0},
                {"time": "01:00:00", "hour": 1, "minute": 0, "second": 0, "ranking_score": 18.0},
            ],
            {
                "professional_readiness": "ready",
                "event_count": 10,
                "documented_event_count": 4,
                "source_quality": "gold",
                "source_doc_count": 2,
            },
            [],
            {
                "allow_exact_time_selection": True,
                "candidate_count": 6,
                "search_window": {
                    "start_time": "01:00:00",
                    "end_time": "01:50:00",
                    "step_minutes": 10,
                    "step_seconds": 0,
                },
            },
        )

        self.assertEqual(decision["status"], "not_ready")
        self.assertIsNone(decision["suggested_time"])
        self.assertFalse(decision["selection_allowed"])
        boundary_flag = next(
            flag for flag in decision["review_flags"] if flag["code"] == "boundary_candidate_bias"
        )
        self.assertEqual(boundary_flag["edge"], "end")

    def test_rectification_ranking_mode_uses_event_baseline_when_minute_signal_is_flat(self):
        mode = _rectification_ranking_mode(
            [
                {
                    "time": "01:00:00",
                    "ranking_score": 42.0,
                    "event_total_score": 20.0,
                    "average_event_score": 4.0,
                },
                {
                    "time": "01:35:00",
                    "ranking_score": 31.0,
                    "event_total_score": 19.7,
                    "average_event_score": 3.94,
                },
                {
                    "time": "02:10:00",
                    "ranking_score": 29.5,
                    "event_total_score": 19.5,
                    "average_event_score": 3.9,
                },
            ]
        )

        self.assertEqual(mode, "event_sensitive_baseline_only")

    def test_rectification_score_event_ignores_same_sign_transit_contacts(self):
        chart = {"planets": []}
        dashas = {"vimshottari": {"maha": []}}
        event = {"type": "career", "date": "2020-01-01", "confidence": "high"}

        with patch(
            "app._rectification_event_rule",
            return_value=(
                "career",
                {
                    "topic": "career",
                    "houses": [10],
                    "lordships": ["10"],
                    "planets": ["Mercury"],
                    "vargas": [],
                },
            ),
        ), patch(
            "app._rectification_weight_for_event",
            return_value={
                "combined_weight": 1.0,
                "certainty": "day_exact",
                "confidence_weight": 1.0,
            },
        ), patch(
            "app._build_lordships",
            return_value={"10": {"lord": "Saturn"}},
        ), patch(
            "app._planet_index_by_name",
            return_value={"Saturn": {"house": 10}, "Mercury": {"sign_index": 2}},
        ), patch(
            "app._active_dasha_chain_for_jd",
            return_value={},
        ), patch(
            "app._build_transits",
            return_value={
                "planets": [],
                "natal_contacts": [
                    {
                        "transit_planet": "Mercury",
                        "natal_planet": "Saturn",
                        "contact_type": "same_sign",
                        "orb": 12.0,
                    },
                    {
                        "transit_planet": "Mercury",
                        "natal_planet": "Saturn",
                        "contact_type": "degree_orb",
                        "orb": 2.4,
                    },
                ],
            },
        ):
            score = _rectification_score_event(chart, dashas, event, 2458849.5, {})

        self.assertEqual(score["weighted_score"], 1.0)
        self.assertEqual(score["factor_count"], 1)
        self.assertEqual(score["factors"][0]["contact_type"], "degree_orb")
        self.assertEqual(score["factors"][0]["weight"], 1.0)

    def test_rectification_score_event_requires_both_sides_relevant_for_natal_contact(self):
        chart = {"planets": []}
        dashas = {"vimshottari": {"maha": []}}
        event = {"type": "career", "date": "2020-01-01", "confidence": "high"}

        with patch(
            "app._rectification_event_rule",
            return_value=(
                "career",
                {
                    "topic": "career",
                    "houses": [10],
                    "lordships": ["10"],
                    "planets": ["Mercury"],
                    "vargas": [],
                },
            ),
        ), patch(
            "app._rectification_weight_for_event",
            return_value={
                "combined_weight": 1.0,
                "certainty": "day_exact",
                "confidence_weight": 1.0,
            },
        ), patch(
            "app._build_lordships",
            return_value={"10": {"lord": "Saturn"}},
        ), patch(
            "app._planet_index_by_name",
            return_value={"Saturn": {"house": 10}, "Mercury": {"sign_index": 2}},
        ), patch(
            "app._active_dasha_chain_for_jd",
            return_value={},
        ), patch(
            "app._build_transits",
            return_value={
                "planets": [],
                "natal_contacts": [
                    {
                        "transit_planet": "Mercury",
                        "natal_planet": "Mars",
                        "contact_type": "degree_orb",
                        "orb": 0.8,
                    },
                    {
                        "transit_planet": "Mercury",
                        "natal_planet": "Saturn",
                        "contact_type": "degree_orb",
                        "orb": 0.8,
                    },
                ],
            },
        ):
            score = _rectification_score_event(chart, dashas, event, 2458849.5, {})

        self.assertEqual(score["weighted_score"], 2.0)
        self.assertEqual(score["factor_count"], 1)
        self.assertEqual(score["factors"][0]["natal_planet"], "Saturn")
        self.assertEqual(score["factors"][0]["weight"], 2.0)

    def test_rectification_score_event_only_scores_fine_dasha_lord_matches(self):
        chart = {"planets": []}
        dashas = {"vimshottari": {"maha": []}}
        event = {"type": "career", "date": "2020-01-01", "confidence": "high"}

        with patch(
            "app._rectification_event_rule",
            return_value=(
                "career",
                {
                    "topic": "career",
                    "houses": [10],
                    "lordships": ["10"],
                    "planets": ["Mercury"],
                    "vargas": [],
                },
            ),
        ), patch(
            "app._rectification_weight_for_event",
            return_value={
                "combined_weight": 1.0,
                "certainty": "day_exact",
                "confidence_weight": 1.0,
            },
        ), patch(
            "app._build_lordships",
            return_value={"10": {"lord": "Mercury"}},
        ), patch(
            "app._planet_index_by_name",
            return_value={"Mercury": {"house": 10, "sign_index": 2}},
        ), patch(
            "app._active_dasha_chain_for_jd",
            return_value={
                "maha": {"lord": "Mercury"},
                "antara": {"lord": "Mercury"},
                "pratyantar": {"lord": "Mercury"},
                "sookshma": {"lord": "Mercury"},
            },
        ), patch(
            "app._build_transits",
            return_value={"planets": [], "natal_contacts": []},
        ):
            score = _rectification_score_event(chart, dashas, event, 2458849.5, {})

        self.assertEqual(score["raw_score"], 35.75)
        self.assertEqual(score["layer_scores"]["dasha"], 35.75)
        factor_map = {
            (factor["type"], factor["level"]): factor
            for factor in score["factors"]
            if factor["type"] in {
                "dasha_lord_matches_topic_house_lord",
                "dasha_lord_matches_topic_karaka",
            }
        }
        self.assertFalse(factor_map[("dasha_lord_matches_topic_house_lord", "maha")]["score_applied"])
        self.assertFalse(factor_map[("dasha_lord_matches_topic_karaka", "antara")]["score_applied"])
        self.assertTrue(factor_map[("dasha_lord_matches_topic_house_lord", "pratyantar")]["score_applied"])
        self.assertTrue(factor_map[("dasha_lord_matches_topic_karaka", "sookshma")]["score_applied"])

    def test_rectification_score_event_requires_dual_reference_for_topic_house_transit(self):
        chart = {"planets": []}
        dashas = {"vimshottari": {"maha": []}}
        event = {"type": "career", "date": "2020-01-01", "confidence": "high"}

        with patch(
            "app._rectification_event_rule",
            return_value=(
                "career",
                {
                    "topic": "career",
                    "houses": [10],
                    "lordships": ["10"],
                    "planets": ["Mercury"],
                    "vargas": [],
                },
            ),
        ), patch(
            "app._rectification_weight_for_event",
            return_value={
                "combined_weight": 1.0,
                "certainty": "day_exact",
                "confidence_weight": 1.0,
            },
        ), patch(
            "app._build_lordships",
            return_value={"10": {"lord": "Saturn"}},
        ), patch(
            "app._planet_index_by_name",
            return_value={"Saturn": {"house": 3}, "Mercury": {"sign_index": 2}},
        ), patch(
            "app._active_dasha_chain_for_jd",
            return_value={},
        ), patch(
            "app._build_transits",
            return_value={
                "planets": [
                    {
                        "name": "Mercury",
                        "house_from_natal_lagna": 10,
                        "house_from_natal_moon": 9,
                    },
                    {
                        "name": "Mercury",
                        "house_from_natal_lagna": 10,
                        "house_from_natal_moon": 10,
                    },
                ],
                "natal_contacts": [],
            },
        ):
            score = _rectification_score_event(chart, dashas, event, 2458849.5, {})

        self.assertEqual(score["weighted_score"], 4.0)
        topic_house_factors = [
            factor for factor in score["factors"]
            if factor["type"] == "relevant_transit_in_topic_house"
        ]
        self.assertEqual(len(topic_house_factors), 2)
        self.assertFalse(topic_house_factors[0]["score_applied"])
        self.assertEqual(topic_house_factors[0]["weight"], 0.0)
        self.assertTrue(topic_house_factors[1]["score_applied"])
        self.assertEqual(topic_house_factors[1]["weight"], 4.0)

    def test_rectification_score_event_only_scores_primary_varga_match(self):
        chart = {"planets": []}
        dashas = {"vimshottari": {"maha": []}}
        event = {"type": "childbirth", "date": "2020-01-01", "confidence": "high"}

        with patch(
            "app._rectification_event_rule",
            return_value=(
                "childbirth",
                {
                    "topic": "marriage",
                    "houses": [5, 9, 2, 11],
                    "lordships": ["5", "9", "2", "11"],
                    "planets": ["Jupiter", "Moon", "Venus"],
                    "vargas": ["D7", "D9"],
                },
            ),
        ), patch(
            "app._rectification_weight_for_event",
            return_value={
                "combined_weight": 1.0,
                "certainty": "day_exact",
                "confidence_weight": 1.0,
            },
        ), patch(
            "app._build_lordships",
            return_value={},
        ), patch(
            "app._planet_index_by_name",
            return_value={
                "Jupiter": {"name": "Jupiter", "sign_index": 2},
                "Moon": {"name": "Moon", "sign_index": 4},
                "Venus": {"name": "Venus", "sign_index": 6},
            },
        ), patch(
            "app._active_dasha_chain_for_jd",
            return_value={},
        ), patch(
            "app._build_transits",
            return_value={"planets": [], "natal_contacts": []},
        ), patch(
            "app._varga_lagna",
            side_effect=lambda _chart, division: {
                "D7": {"sign_index": 2, "sign": "Gemini"},
                "D9": {"sign_index": 2, "sign": "Gemini"},
            }[division],
        ):
            score = _rectification_score_event(chart, dashas, event, 2458849.5, {})

        self.assertEqual(score["weighted_score"], 1.5)
        varga_factors = [
            factor for factor in score["factors"]
            if factor["type"] == "varga_lagna_matches_relevant_planet_sign"
        ]
        self.assertEqual(len(varga_factors), 2)
        self.assertTrue(varga_factors[0]["score_applied"])
        self.assertEqual(varga_factors[0]["division"], "D7")
        self.assertEqual(varga_factors[0]["weight"], 1.5)
        self.assertFalse(varga_factors[1]["score_applied"])
        self.assertEqual(varga_factors[1]["division"], "D9")
        self.assertEqual(varga_factors[1]["weight"], 0.0)

    def test_shadbala_masa_bala_uses_thirty_day_savana_month_lord(self):
        self.assertEqual(
            MASA_BALA_LORD_SEQUENCE,
            ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon"],
        )
        before_boundary = {"year": 1952, "month": 1, "day": 5}
        boundary = {"year": 1952, "month": 1, "day": 6}

        saturn_detail = _masa_bala_detail({"name": "Saturn"}, before_boundary)
        self.assertEqual(saturn_detail["epoch_day_count"], MASA_BALA_EPOCH_DAY_COUNT)
        self.assertEqual(saturn_detail["ahargana_days"], 179)
        self.assertEqual(saturn_detail["savana_month_index"], 5)
        self.assertEqual(saturn_detail["masa_lord"], "Saturn")
        self.assertEqual(saturn_detail["score"], 30.0)

        moon_detail = _masa_bala_detail({"name": "Moon"}, boundary)
        self.assertEqual(moon_detail["ahargana_days"], 180)
        self.assertEqual(moon_detail["savana_month_index"], 6)
        self.assertEqual(moon_detail["masa_lord"], "Moon")
        self.assertEqual(moon_detail["score"], 30.0)
        self.assertEqual(
            _masa_bala_detail({"name": "Saturn"}, boundary)["score"],
            0.0,
        )

    def test_shadbala_abda_bala_uses_three_hundred_sixty_day_savana_year_lord(self):
        self.assertEqual(
            ABDA_BALA_LORD_SEQUENCE,
            ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon"],
        )
        before_boundary = {"year": 1952, "month": 7, "day": 3}
        boundary = {"year": 1952, "month": 7, "day": 4}

        mercury_detail = _abda_bala_detail({"name": "Mercury"}, before_boundary)
        self.assertEqual(mercury_detail["epoch_day_count"], MASA_BALA_EPOCH_DAY_COUNT)
        self.assertEqual(mercury_detail["ahargana_days"], 359)
        self.assertEqual(mercury_detail["savana_year_index"], 0)
        self.assertEqual(mercury_detail["abda_lord"], "Mercury")
        self.assertEqual(mercury_detail["score"], 15.0)

        saturn_detail = _abda_bala_detail({"name": "Saturn"}, boundary)
        self.assertEqual(saturn_detail["ahargana_days"], 360)
        self.assertEqual(saturn_detail["savana_year_index"], 1)
        self.assertEqual(saturn_detail["abda_lord"], "Saturn")
        self.assertEqual(saturn_detail["score"], 15.0)
        self.assertEqual(
            _abda_bala_detail({"name": "Mercury"}, boundary)["score"],
            0.0,
        )

    def test_shadbala_drik_bala_uses_exact_parashari_aspect_virupa(self):
        cases = [
            ("Sun", 180.0, 60.0),
            ("Mars", 90.0, 60.0),
            ("Mars", 210.0, 60.0),
            ("Jupiter", 120.0, 60.0),
            ("Jupiter", 240.0, 60.0),
            ("Saturn", 60.0, 60.0),
            ("Saturn", 270.0, 60.0),
            ("Venus", 0.0, 0.0),
        ]
        for planet_name, angle, expected in cases:
            with self.subTest(planet=planet_name, angle=angle):
                self.assertEqual(
                    _parashari_drik_aspect_virupa(planet_name, angle),
                    expected,
                )

    def test_shadbala_drik_bala_has_nonzero_exact_chart_contributions(self):
        data = self._sample_v2_chart()
        details = [
            row["components"]["drik_bala"]
            for row in data["shadbala"]["planets"]
        ]
        self.assertTrue(any(detail["aspect_count"] > 0 for detail in details))
        self.assertTrue(any(detail["classical_net_virupa"] != 0 for detail in details))

        for detail in details:
            expected_net = (
                detail["benefic_aspect_virupa"]
                - detail["malefic_aspect_virupa"]
            ) / 4.0
            self.assertAlmostEqual(
                detail["classical_net_virupa"],
                expected_net,
                places=2,
            )

    def test_new_starter_yogas_return_technical_matches(self):
        planets = [
            {
                "id": "sun",
                "name": "Sun",
                "sign": "Aries",
                "sign_index": 0,
                "house": 1,
                "combustion": {"is_combust": False, "severity": "none"},
            },
            {
                "id": "mercury",
                "name": "Mercury",
                "sign": "Aries",
                "sign_index": 0,
                "house": 1,
                "combustion": {"is_combust": True, "severity": "mild"},
            },
            {
                "id": "moon",
                "name": "Moon",
                "sign": "Taurus",
                "sign_index": 1,
                "house": 2,
                "combustion": {"is_combust": False, "severity": "none"},
            },
            {
                "id": "mars",
                "name": "Mars",
                "sign": "Scorpio",
                "sign_index": 7,
                "house": 8,
                "combustion": {"is_combust": False, "severity": "none"},
            },
            {
                "id": "venus",
                "name": "Venus",
                "sign": "Scorpio",
                "sign_index": 7,
                "house": 8,
                "combustion": {"is_combust": False, "severity": "none"},
            },
        ]

        parivartana_planets = [
            {
                "id": "mars",
                "name": "Mars",
                "sign": "Taurus",
                "sign_index": 1,
                "house": 2,
                "combustion": {"is_combust": False, "severity": "none"},
            },
            {
                "id": "venus",
                "name": "Venus",
                "sign": "Aries",
                "sign_index": 0,
                "house": 1,
                "combustion": {"is_combust": False, "severity": "none"},
            },
        ]

        matches = [
            *_build_budha_aditya_yogas(planets),
            *_build_chandra_mangala_yogas(planets),
            *_build_parivartana_yogas(parivartana_planets),
        ]
        ids = {match["id"] for match in matches}

        self.assertIn("budha_aditya", ids)
        self.assertIn("chandra_mangala", ids)
        self.assertIn("parivartana_mars_venus", ids)
        for match in matches:
            self.assertEqual(match["source"], "starter_rule")
            self.assertIn(match["effect_type"], {"supportive", "mixed"})
            self.assertIsInstance(match["supporting_factors"], list)

    def test_europe_istanbul_timezone_id_uses_historical_dst(self):
        self.assertEqual(
            _resolve_timezone_offset({"timezone_id": "Europe/Istanbul"}, 2015, 1, 15, 12, 0),
            (2.0, "Europe/Istanbul"),
        )
        self.assertEqual(
            _resolve_timezone_offset({"timezone_id": "Europe/Istanbul"}, 2015, 7, 15, 12, 0),
            (3.0, "Europe/Istanbul"),
        )
        self.assertEqual(
            _resolve_timezone_offset({"timezone_id": "Europe/Istanbul"}, 2017, 1, 15, 12, 0),
            (3.0, "Europe/Istanbul"),
        )

        reference = _transit_reference_from_options(
            {
                "transit_date": "2015-01-15",
                "transit_time": "12:00",
                "transit_timezone_id": "Europe/Istanbul",
                "transit_tz_offset": 3,
            },
            3,
        )
        self.assertEqual(reference["tz_offset"], 2.0)
        self.assertEqual(reference["timezone_id"], "Europe/Istanbul")

    def test_life_period_analysis_returns_technical_dasha_and_transit_tables(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "1",
                "to_date": "1982-05-28",
                "planets": "saturn,jupiter",
                "include_dasha": "true",
                "include_antardasha": "true",
                "include_pratyantardasha": "false",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["person_info"]["person_id"], "test-kisi")
        self.assertEqual(data["person_info"]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(data["analysis_period"]["from_age"], 1)
        self.assertEqual(
            data["analysis_period"]["dasha_levels"],
            ["maha", "antara", "pratyantar"],
        )
        self.assertIn("vimshottari_dasha_timeline", data)
        self.assertGreater(len(data["vimshottari_dasha_timeline"]["maha"]), 0)
        self.assertGreater(len(data["vimshottari_dasha_timeline"]["antara"]), 0)
        self.assertGreater(
            len(data["vimshottari_dasha_timeline"]["pratyantar"]),
            0,
        )

        saturn = data["saturn_transit_timeline"]
        jupiter = data["jupiter_transit_timeline"]
        self.assertGreater(len(saturn["periods"]), 0)
        self.assertGreater(len(jupiter["periods"]), 0)
        saturn_row = saturn["periods"][0]
        self.assertEqual([row["aspect"] for row in saturn_row["vedic_aspects"]], [3, 7, 10])
        self.assertIn("start_date", saturn_row)
        self.assertIn("end_date", saturn_row)
        self.assertIn("technical_statement", saturn_row)
        self.assertIn("Saturn transiting", saturn_row["technical_statement"])
        self.assertNotIn("zorlayıcı", saturn_row["technical_statement"].casefold())
        self.assertEqual(
            [row["aspect"] for row in jupiter["periods"][0]["vedic_aspects"]],
            [5, 7, 9],
        )
        self.assertIn("retrograde_periods", saturn)
        rahu_ketu = data["rahu_ketu_transit_timeline"]
        self.assertEqual(rahu_ketu["method"], "lahiri_sidereal_sign_periods")
        self.assertEqual(rahu_ketu["node_type"], "true_node")
        self.assertGreater(len(rahu_ketu["periods"]), 0)
        node_row = rahu_ketu["periods"][0]
        expected_node_keys = {
            "start_date",
            "end_date",
            "age_start",
            "age_end",
            "start_jd",
            "end_jd",
            "rahu_sign",
            "rahu_sign_tr",
            "rahu_sign_index",
            "ketu_sign",
            "ketu_sign_tr",
            "ketu_sign_index",
            "rahu_house_from_lagna",
            "ketu_house_from_lagna",
            "rahu_house_from_moon",
            "ketu_house_from_moon",
            "natal_planet_contacts",
            "technical_statement",
        }
        self.assertEqual(set(node_row.keys()), expected_node_keys)
        self.assertEqual((node_row["rahu_sign_index"] + 6) % 12, node_row["ketu_sign_index"])
        self.assertIn(node_row["rahu_house_from_lagna"], range(1, 13))
        self.assertIn(node_row["ketu_house_from_lagna"], range(1, 13))
        for period in rahu_ketu["periods"]:
            for contact in period["natal_planet_contacts"]:
                self.assertNotIn(contact["natal_planet"], {"Rahu", "Rahu (True)", "Ketu"})
                self.assertIn(
                    contact["contact_type"],
                    {
                        "rahu_same_sign",
                        "ketu_same_sign",
                        "rahu_vedic_aspect_to_sign",
                        "ketu_vedic_aspect_to_sign",
                    },
                )
        self.assertIn("saturn_jupiter_combined_periods", data)
        self.assertIn("dasha_transit_overlap_periods", data)
        self.assertIn("activated_houses_from_lagna", data)
        self.assertIn("activated_houses_from_moon", data)
        self.assertIn("natal_planet_contacts", data)
        neptune = data["neptune_career_transit_evidence_v1"]
        self.assertEqual(neptune["status"], "experimental_hybrid_evidence")
        self.assertEqual(neptune["version"], "v1")
        self.assertFalse(neptune["known_life_events_used"])
        self.assertFalse(neptune["affects_career_event_scores"])
        self.assertEqual(neptune["minimum_age"], 15.0)
        self.assertEqual(neptune["orb_limit"], 1.5)
        self.assertEqual(
            neptune["primary_aspects"],
            ["conjunction", "square", "opposition"],
        )
        self.assertEqual(neptune["helper_aspects"], ["sextile", "trine"])
        self.assertEqual(neptune["processes"], [])
        career_timing = data["career_timing_evidence_v2"]
        self.assertEqual(career_timing["status"], "technical_evidence_only")
        self.assertEqual(career_timing["version"], "v2")
        self.assertFalse(career_timing["known_life_events_used"])
        self.assertEqual(
            career_timing["primary_vargas"],
            ["D1", "D9", "D10", "D30"],
        )
        self.assertEqual(
            career_timing["direction_rule"],
            "direction_uncertain_when_support_and_challenge_are_both_substantive",
        )
        self.assertEqual(
            career_timing["event_type_scoring"]["types"],
            [
                "career_entry",
                "specialization",
                "status_change",
                "interruption",
                "restructuring",
            ],
        )
        self.assertEqual(
            career_timing["event_type_scoring"]["ranking_min_age"],
            18.0,
        )
        self.assertEqual(
            career_timing["event_type_scoring"]["rankings_scope"],
            "adult_career_windows_only",
        )
        self.assertIn(
            "paid_work",
            career_timing["event_type_scoring"]["interpretation_guidance"]
            ["career_entry"]["interpretation_limit"],
        )
        self.assertGreater(career_timing["total_window_count"], 0)
        self.assertGreater(career_timing["selected_window_count"], 0)
        self.assertLessEqual(career_timing["selected_window_count"], 36)
        self.assertEqual(
            len(career_timing["windows"]),
            career_timing["total_window_count"],
        )
        self.assertEqual(
            len(career_timing["ranked_windows"]),
            career_timing["selected_window_count"],
        )
        career_window = career_timing["windows"][0]
        self.assertEqual(career_window["precision"], "pratyantar_window")
        self.assertEqual(len(career_window["dasha_path"]), 3)
        self.assertAlmostEqual(
            career_window["activation_score"],
            career_window["support_score"] + career_window["challenge_score"],
        )
        self.assertIn(
            career_window["direction"]["status"],
            {
                "direction_uncertain",
                "direction_leaning_not_event_prediction",
            },
        )
        self.assertGreater(len(career_window["event_type_candidates"]), 0)
        self.assertEqual(
            set(career_window["event_type_scores"]),
            set(career_timing["event_type_scoring"]["types"]),
        )
        self.assertIn(
            career_window["dominant_event_type"],
            {
                *career_timing["event_type_scoring"]["types"],
                "not_distinguished",
            },
        )
        for score in career_window["event_type_scores"].values():
            self.assertAlmostEqual(
                score["net_score"],
                score["support_score"] - score["counter_score"],
            )
            self.assertIn(
                score["status"],
                {
                    "insufficient_evidence",
                    "mixed_evidence",
                    "technical_candidate_not_prediction",
                },
            )
        self.assertEqual(
            set(career_timing["event_type_rankings"]),
            set(career_timing["event_type_scoring"]["types"]),
        )
        self.assertIn("early_career_candidates", career_timing)
        self.assertIn("local_transition_turning_points", career_timing)
        self.assertTrue(
            all(
                15 <= row["age_start"] < 18
                for row in career_timing["early_career_candidates"]
            )
        )
        self.assertTrue(
            all(
                row["forward_net"] >= 2.5
                and row["transition_net"] >= 2.5
                for row in career_timing["local_transition_turning_points"]
            )
        )
        for ranking in career_timing["event_type_rankings"].values():
            self.assertTrue(all(row["age_start"] >= 18 for row in ranking))
            self.assertTrue(
                all(row["interpretation_limit"] for row in ranking)
            )
        self.assertGreater(len(career_window["independent_layers"]), 0)
        self.assertIn(
            "activation_score_is_not_probability",
            career_timing["safety_notes"],
        )
        health_timing = data["health_timing_evidence_v1"]
        self.assertEqual(
            health_timing["status"],
            "technical_evidence_only_not_medical_advice",
        )
        self.assertEqual(health_timing["version"], "v1")
        self.assertFalse(health_timing["known_life_events_used"])
        self.assertEqual(
            health_timing["event_types"],
            [
                "acute_crisis",
                "chronic_strain",
                "psychological_pressure",
            ],
        )
        self.assertEqual(
            health_timing["event_type_guidance"]["acute_crisis"]["precision"],
            "sookshma",
        )
        self.assertEqual(
            health_timing["event_type_guidance"]["chronic_strain"]["precision"],
            "pratyantar",
        )
        self.assertEqual(
            health_timing["event_type_guidance"]
            ["psychological_pressure"]["precision"],
            "pratyantar",
        )
        self.assertEqual(health_timing["acute_ingress_convergences"], [])
        self.assertTrue(
            all(
                not rows
                for rows in health_timing["rankings"].values()
            )
        )
        family_timing = data["family_timing_evidence_v1"]
        self.assertEqual(family_timing["status"], "technical_evidence_only")
        self.assertEqual(family_timing["version"], "v1")
        self.assertFalse(family_timing["known_life_events_used"])
        self.assertEqual(
            family_timing["event_types"],
            [
                "family_expansion_parenthood",
                "childbirth_context",
                "family_restructuring",
                "parental_care_responsibility",
                "family_separation_distance",
                "family_loss_grief_context",
            ],
        )
        self.assertEqual(
            set(family_timing["rankings"]),
            set(family_timing["event_types"]),
        )
        self.assertEqual(family_timing["primary_vargas"], ["D1", "D7", "D12"])
        self.assertIn("D60", family_timing["supporting_vargas"])
        self.assertIn(
            "no_death_person_or_death_date_prediction_is_generated",
            family_timing["safety_notes"],
        )
        self.assertIn(
            "does_not_predict_death",
            family_timing["event_type_guidance"]
            ["family_loss_grief_context"]["interpretation_limit"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in family_timing["rankings"].values()
            )
        )
        education_timing = data["education_timing_evidence_v1"]
        self.assertEqual(education_timing["status"], "technical_evidence_only")
        self.assertFalse(education_timing["known_life_events_used"])
        self.assertEqual(
            education_timing["event_types"],
            [
                "education_entry",
                "completion_credential",
                "specialization_training",
                "education_interruption",
                "return_retraining",
            ],
        )
        self.assertEqual(education_timing["primary_vargas"], ["D1", "D24"])
        self.assertIn(
            "d24_is_low_confidence_and_external_validation_pending",
            education_timing["safety_notes"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in education_timing["rankings"].values()
            )
        )
        relocation_timing = data["relocation_timing_evidence_v1"]
        self.assertEqual(relocation_timing["status"], "technical_evidence_only")
        self.assertFalse(relocation_timing["known_life_events_used"])
        self.assertEqual(len(relocation_timing["event_types"]), 6)
        self.assertEqual(relocation_timing["primary_vargas"], ["D1", "D4"])
        self.assertTrue(
            all(
                not rows
                for rows in relocation_timing["rankings"].values()
            )
        )
        finance_timing = data["finance_timing_evidence_v1"]
        self.assertEqual(
            finance_timing["status"],
            "technical_evidence_only_not_financial_advice",
        )
        self.assertFalse(finance_timing["known_life_events_used"])
        self.assertEqual(len(finance_timing["event_types"]), 6)
        self.assertEqual(finance_timing["primary_vargas"], ["D1", "D2"])
        self.assertTrue(
            all(
                not rows
                for rows in finance_timing["rankings"].values()
            )
        )
        relationship_timing = data["relationship_timing_evidence_v1"]
        self.assertEqual(
            relationship_timing["status"],
            "technical_evidence_only",
        )
        self.assertFalse(relationship_timing["known_life_events_used"])
        self.assertEqual(len(relationship_timing["event_types"]), 6)
        self.assertEqual(
            relationship_timing["primary_vargas"],
            ["D1", "D9"],
        )
        self.assertIn(
            "no_partner_identity_gender_or_person_prediction_is_generated",
            relationship_timing["safety_notes"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in relationship_timing["rankings"].values()
            )
        )
        character_activation = data["character_activation_evidence_v1"]
        self.assertEqual(
            character_activation["status"],
            "technical_evidence_only_not_psychological_assessment",
        )
        self.assertFalse(character_activation["known_life_events_used"])
        self.assertEqual(len(character_activation["dimensions"]), 6)
        self.assertEqual(character_activation["primary_vargas"], ["D1", "D9"])
        self.assertIn(
            "dimensions_may_overlap_and_are_not_forced_into_one_dominant_trait",
            character_activation["safety_notes"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in character_activation["rankings"].values()
            )
        )
        spiritual_activation = data["spiritual_activation_evidence_v1"]
        self.assertEqual(
            spiritual_activation["status"],
            "technical_evidence_only",
        )
        self.assertFalse(spiritual_activation["known_life_events_used"])
        self.assertEqual(len(spiritual_activation["dimensions"]), 6)
        self.assertEqual(
            spiritual_activation["primary_vargas"],
            ["D1", "D9", "D20"],
        )
        self.assertIn(
            "d20_is_low_confidence_and_external_validation_pending",
            spiritual_activation["safety_notes"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in spiritual_activation["rankings"].values()
            )
        )
        legal_timing = data["legal_timing_evidence_v1"]
        self.assertEqual(
            legal_timing["status"],
            "technical_evidence_only_not_legal_advice",
        )
        self.assertFalse(legal_timing["known_life_events_used"])
        self.assertEqual(len(legal_timing["event_types"]), 6)
        self.assertEqual(
            legal_timing["primary_vargas"],
            ["D1", "D9", "D10"],
        )
        self.assertIn(
            "no_crime_fault_lawsuit_verdict_penalty_or_outcome_prediction_is_generated",
            legal_timing["safety_notes"],
        )
        self.assertTrue(
            all(
                not rows
                for rows in legal_timing["rankings"].values()
            )
        )
        self.assertTrue(
            any("No interpretive sentences" in note for note in data["technical_notes"])
        )

    def test_health_timing_surfaces_july_2015_acute_convergence_without_event_input(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "36",
                "to_date": "2016-05-28",
                "planets": "saturn,jupiter",
            },
        )

        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["health_timing_evidence_v1"]
        self.assertFalse(timing["known_life_events_used"])
        self.assertIn(
            "acute_ingress_convergence_is_separate_from_total_score_ranking",
            timing["safety_notes"],
        )

        target = next(
            row
            for row in timing["acute_ingress_convergences"]
            if row["start_date"] <= "2015-07-17" <= row["end_date"]
        )
        self.assertEqual(
            target["dasha_path"],
            ["Jupiter", "Rahu", "Rahu", "Jupiter"],
        )
        self.assertEqual(target["precision"], "sookshma")
        evidence_codes = {
            item["code"]
            for item in target["evidence"]
        }
        self.assertIn(
            "transit_Jupiter_ingress_health_house_8",
            evidence_codes,
        )
        self.assertIn("transit_Jupiter_same_sign_Saturn", evidence_codes)
        self.assertFalse(
            any(
                ("_Rahu_d6_" in code)
                or ("_Rahu_d30_" in code)
                or ("_Ketu_d6_" in code)
                or ("_Ketu_d30_" in code)
                for code in evidence_codes
            )
        )

    def test_family_timing_ranks_six_independent_adult_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "18",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )

        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["family_timing_evidence_v1"]
        self.assertFalse(timing["known_life_events_used"])
        self.assertEqual(len(timing["rankings"]), 6)
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 18 for row in rows))
            self.assertTrue(
                all(
                    row["event_type"] == event_type
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )
            self.assertFalse(
                any(
                    item["layer"] in {"D4", "D7", "D9", "D12", "D60"}
                    and (
                        "_Rahu_" in item["code"]
                        or "_Ketu_" in item["code"]
                    )
                    for row in rows
                    for item in row["evidence"]
                )
            )

        loss_rows = timing["rankings"]["family_loss_grief_context"]
        self.assertTrue(
            all(
                "does_not_predict_death" in row["interpretation_limit"]
                for row in loss_rows
            )
        )

    def test_education_timing_ranks_five_independent_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "15",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )

        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["education_timing_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 5)
        self.assertFalse(timing["known_life_events_used"])
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 15 for row in rows))
            self.assertTrue(
                all(
                    row["event_type"] == event_type
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_relocation_timing_ranks_six_independent_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "15",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["relocation_timing_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 15 for row in rows))
            self.assertTrue(
                all(
                    row["event_type"] == event_type
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_finance_timing_ranks_six_independent_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "18",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["finance_timing_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 18 for row in rows))
            self.assertTrue(all(row["interpretation_limit"] for row in rows))

    def test_relationship_timing_ranks_six_independent_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "18",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["relationship_timing_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 18 for row in rows))
            self.assertTrue(
                all(
                    row["event_type"] == event_type
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_character_activation_ranks_six_independent_dimensions(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "15",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["character_activation_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for dimension, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, dimension)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 15 for row in rows))
            self.assertTrue(
                all(
                    row["dimension"] == dimension
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_spiritual_activation_ranks_six_independent_dimensions(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "15",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["spiritual_activation_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for dimension, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, dimension)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 15 for row in rows))
            self.assertTrue(
                all(
                    row["dimension"] == dimension
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_legal_timing_ranks_six_independent_contexts(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "18",
                "to_date": "2021-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(response.status_code, 200)
        timing = response.get_json()["legal_timing_evidence_v1"]
        self.assertEqual(len(timing["rankings"]), 6)
        self.assertFalse(timing["known_life_events_used"])
        for event_type, rows in timing["rankings"].items():
            self.assertGreater(len(rows), 0, event_type)
            self.assertLessEqual(len(rows), 8)
            self.assertTrue(all(row["age_start"] >= 18 for row in rows))
            self.assertTrue(
                all(
                    row["event_type"] == event_type
                    and row["precision"] == "pratyantar"
                    and row["interpretation_limit"]
                    for row in rows
                )
            )

    def test_neptune_career_evidence_merges_retrograde_repeats_without_changing_scores(self):
        response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "38",
                "to_date": "2021-02-08",
                "planets": "saturn,jupiter",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        evidence = data["neptune_career_transit_evidence_v1"]
        self.assertFalse(evidence["affects_career_event_scores"])
        self.assertIn(
            "d10_degree_aspects_are_experimental_hybrid_evidence",
            evidence["safety_notes"],
        )

        d10_moon_square = next(
            row
            for row in evidence["processes"]
            if row["layer"] == "D10"
            and row["target"] == "D10 Moon"
            and row["aspect"] == "square"
        )
        self.assertLessEqual(d10_moon_square["start_date"], "2018-04-23")
        self.assertGreaterEqual(d10_moon_square["end_date"], "2021-01-07")
        self.assertEqual(d10_moon_square["evidence_class"], "primary")
        self.assertGreaterEqual(d10_moon_square["repeat_count"], 4)
        self.assertIn("amatyakaraka", d10_moon_square["target_roles"])
        self.assertIn("moon", d10_moon_square["target_roles"])

        d1_mercury_sextile = next(
            row
            for row in evidence["processes"]
            if row["layer"] == "D1"
            and row["target"] == "D1 Mercury"
            and row["aspect"] == "sextile"
        )
        self.assertEqual(d1_mercury_sextile["evidence_class"], "helper")
        self.assertGreaterEqual(d1_mercury_sextile["repeat_count"], 4)
        self.assertIn("6th_lord", d1_mercury_sextile["target_roles"])

    def test_full_chart_can_embed_life_period_analysis_for_expert_package(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                    "include_life_period_analysis": True,
                    "life_from_age": 1,
                    "life_to_date": "1982-05-28",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        life_period = data.get("life_period_analysis")

        self.assertIsInstance(life_period, dict)
        self.assertNotEqual(life_period.get("status"), "not_available")
        self.assertEqual(life_period["analysis_period"]["from_age"], 1)
        self.assertEqual(life_period["analysis_period"]["to_date"], "1982-05-28")
        self.assertIn("maha", life_period["vimshottari_dasha_timeline"])
        self.assertIn("antara", life_period["vimshottari_dasha_timeline"])
        self.assertIn("pratyantar", life_period["vimshottari_dasha_timeline"])
        self.assertIn("prana", life_period["vimshottari_dasha_timeline"])
        self.assertIn("periods", life_period["saturn_transit_timeline"])
        self.assertIn("periods", life_period["jupiter_transit_timeline"])
        self.assertIn("periods", life_period["rahu_ketu_transit_timeline"])
        self.assertGreater(len(life_period["rahu_ketu_transit_timeline"]["periods"]), 0)
        self.assertIn("career_timing_evidence_v2", life_period)

    def test_full_chart_exposes_passive_bhava_chalit_without_replacing_whole_sign(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["meta"]["house_system"], "whole_sign")
        self.assertIn("bhava_chalit", data)

        bhava = data["bhava_chalit"]
        self.assertEqual(bhava["status"], "implemented_passive_technical_layer")
        self.assertEqual(
            bhava["method"],
            "sripati_house_cusps_with_chalit_planet_house_assignment",
        )
        self.assertIn("whole_sign_primary_house_system_unchanged", bhava["assumptions"])
        self.assertIn("rectification_window_collapse", bhava["excluded_rules"])
        self.assertEqual(len(bhava["houses"]), 12)
        self.assertEqual(len(bhava["planets"]), 9)
        self.assertTrue(bhava["summary"]["birth_time_sensitive"])
        self.assertTrue(bhava["summary"]["whole_sign_primary_house_system_unchanged"])

        expected_house_keys = {
            "house",
            "cusp_longitude",
            "cusp_sign",
            "cusp_sign_tr",
            "cusp_sign_index",
            "cusp_degree",
            "cusp_degree_str",
            "start_longitude",
            "end_longitude",
            "lord",
        }
        for house in bhava["houses"]:
            self.assertEqual(set(house.keys()), expected_house_keys)
            self.assertGreaterEqual(house["house"], 1)
            self.assertLessEqual(house["house"], 12)
            self.assertGreaterEqual(house["cusp_sign_index"], 0)
            self.assertLessEqual(house["cusp_sign_index"], 11)

        whole_sign_houses = {
            planet["name"].replace(" (True)", ""): planet["house"]
            for planet in data["planets"]
        }
        expected_planet_keys = {
            "planet",
            "planet_id",
            "longitude",
            "sign",
            "sign_tr",
            "sign_index",
            "degree",
            "degree_str",
            "whole_sign_house",
            "bhava_chalit_house",
            "house_changed",
            "distance_from_cusp",
        }
        for planet in bhava["planets"]:
            self.assertEqual(set(planet.keys()), expected_planet_keys)
            self.assertIn(planet["planet"], whole_sign_houses)
            self.assertEqual(
                planet["whole_sign_house"],
                whole_sign_houses[planet["planet"]],
            )
            self.assertGreaterEqual(planet["whole_sign_house"], 1)
            self.assertLessEqual(planet["whole_sign_house"], 12)
            self.assertGreaterEqual(planet["bhava_chalit_house"], 1)
            self.assertLessEqual(planet["bhava_chalit_house"], 12)
            self.assertIsInstance(planet["house_changed"], bool)

    def test_full_chart_exposes_passive_bhava_bala_without_new_scoring(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["meta"]["house_system"], "whole_sign")
        self.assertIn("bhava_bala", data)

        bhava_bala = data["bhava_bala"]
        self.assertEqual(bhava_bala["status"], "starter_technical_layer")
        self.assertEqual(
            bhava_bala["method"],
            "compiled_house_evidence_from_existing_layers_no_new_weighting",
        )
        self.assertIn("no_weighted_score", bhava_bala["assumptions"])
        self.assertIn("new_weighted_house_strength_score", bhava_bala["excluded_rules"])
        self.assertIn("rectification_window_collapse", bhava_bala["excluded_rules"])
        self.assertFalse(bhava_bala["summary"]["scored"])
        self.assertEqual(len(bhava_bala["houses"]), 12)

        first_house = bhava_bala["houses"][0]
        self.assertEqual(first_house["house"], data["houses"][0]["house"])
        self.assertEqual(first_house["sign"], data["houses"][0]["sign"])
        self.assertEqual(first_house["lord"], data["lordships"]["1"]["lord"])
        self.assertIsNone(first_house["score"])
        self.assertEqual(first_house["score_status"], "not_scored")
        self.assertIn("sav", first_house["ashtakavarga"])
        self.assertIn("lord_bav", first_house["ashtakavarga"])
        self.assertIn("total_score", first_house["lord_shadbala"])
        self.assertIn("cusp_sign", first_house["bhava_chalit"])
        self.assertIn("graha_aspected_by", first_house)
        self.assertIn("rashi_aspected_by", first_house)

    def test_full_chart_returns_backend_expert_copy_package(self):
        analysis_profile = {
            "mode": "technical",
            "label": "Teknik mod",
            "interpretation_language": "evidence_first",
            "certainty_policy": "yorumdan önce veri, kural, güven ve eksik kontrol bildir",
            "usage_rule": "Yorum üretmeden önce teknik kanıtları, kullanılan kaynak alanlarını ve eksikleri açıkça sırala.",
        }
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
                "analysis_profile": analysis_profile,
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        package = data["copy_packages"]["expert"]
        markdown = package["markdown"]
        self.assertEqual(package["source"], "backend_generator")
        self.assertEqual(package["generator"], "_build_expert_copy_markdown")
        self.assertEqual(package["analysis_profile"]["mode"], "technical")
        self.assertEqual(data["analysis_profile"]["mode"], "technical")
        self.assertIn("# Test Kisi Teknik Harita Paketi", markdown)
        self.assertIn("| analysis_mode | technical |", markdown)
        self.assertIn("## Chara Dasha v1 Aktif Periyot", markdown)
        self.assertIn("implemented_starter_chara_maha_antara", markdown)
        self.assertIn("## Yogini Dasha v1 Aktif Periyot", markdown)
        self.assertIn("implemented_starter_yogini_maha_antara_pratyantar", markdown)
        self.assertIn("## Vimshopaka Bala", markdown)
        self.assertIn("varga dignity kanıt tablosu", markdown)
        self.assertIn("## Avasthalar", markdown)
        self.assertIn("gezegen kondisyon kanıt tablosu", markdown)
        self.assertIn("## Shadbala", markdown)
        self.assertIn("| Ozet | Deger |", markdown)
        self.assertIn("En guclu gezegen", markdown)
        self.assertIn("| Gezegen | Legacy Toplam | Rupa | Gerekli Rupa | Oran | Durum | En Guclu | En Zayif | Yuddha Adj. |", markdown)
        self.assertIn("| Gezegen | Teknik Not |", markdown)
        self.assertIn("Minimum", markdown)
        self.assertNotIn("Rektifikasyon aday pencereleri", markdown)
        self.assertNotIn("rektifikasyon tamamlanmadan", markdown)
        for division, name in VARGA_NAMES.items():
            self.assertIn(f"## {division} {name} Full Tablo", markdown)
        self.assertNotIn("## D10 Dashamsha Meslek Haritası", markdown)
        self.assertNotIn("## D12 Sağlık/Hassasiyet Varga Tablosu", markdown)

    def test_expert_copy_endpoint_refreshes_backend_markdown_for_analysis_mode(self):
        chart = self._sample_v2_chart()
        response = self.client.post(
            "/api/v2/chart/expert-copy",
            json={
                "chart": chart,
                "person": {"name": "Test Kisi", "group": "Grup-99"},
                "analysis_profile": {
                    "mode": "astrolog",
                    "label": "Astrolog modu",
                    "interpretation_language": "strong_professional",
                    "certainty_policy": "çoklu gösterge desteği varsa güçlü hüküm dili; yine de kader kesinliği yok",
                    "usage_rule": "Natal vaat, dasha, transit ve varga aynı temayı destekliyorsa daha net astrolog dili kullan.",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        package = data["copy_packages"]["expert"]
        markdown = package["markdown"]
        self.assertEqual(data["status"], "expert_copy_ready")
        self.assertEqual(package["source"], "backend_generator")
        self.assertEqual(package["analysis_profile"]["mode"], "astrolog")
        self.assertIn("| analysis_mode | astrolog |", markdown)
        self.assertIn("## D3 Drekkana Full Tablo", markdown)

    def _sample_v2_chart(self, options=None):
        request_options = {
            "ayanamsa": "Lahiri",
            "zodiac": "sidereal",
            "house_system": "whole_sign",
            "node_type": "true",
            "language": "tr",
        }
        request_options.update(options or {})
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": request_options,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def _sample_beta_profile_payload(self):
        return {
            "person": {"name": "Beta Kisi", "group": "Beta"},
            "birth": {
                "year": 1978,
                "month": 5,
                "day": 28,
                "hour": 0,
                "minute": 15,
                "timezone_id": "Europe/Istanbul",
                "lat": 40.7654,
                "lon": 29.9408,
                "place": "Izmit, Turkey",
                "time_confidence": "high",
            },
        }

    def _sample_transit_pack_payload(self):
        return {
            "person": {"id": "test-kisi", "name": "Test Kisi", "group": "Grup-99"},
            "birth": {
                "year": 1978,
                "month": 5,
                "day": 28,
                "hour": 0,
                "minute": 15,
                "timezone_id": "Europe/Istanbul",
                "lat": 40.7654,
                "lon": 29.9408,
                "place": "Izmit, Turkey",
                "time_confidence": "high",
            },
            "transit_time": "12:00",
            "transit_timezone_id": "Europe/Istanbul",
        }

    def test_chart_full_accepts_birth_seconds(self):
        base_payload = {
            "person": {"id": "oya", "name": "Oya", "group": "Grup-01"},
            "birth": {
                "year": 1975,
                "month": 3,
                "day": 31,
                "hour": 6,
                "minute": 15,
                "timezone_id": "Europe/Istanbul",
                "lat": 40.35222,
                "lon": 27.97667,
                "place": "Oya reference",
                "time_confidence": "high",
            },
            "options": {
                "ayanamsa": "Lahiri",
                "zodiac": "sidereal",
                "house_system": "whole_sign",
                "node_type": "true",
                "language": "tr",
            },
        }
        without_seconds = self.client.post("/api/v2/chart/full", json=base_payload)
        with_seconds_payload = {
            **base_payload,
            "birth": {
                **base_payload["birth"],
                "second": 52,
            },
        }
        with_seconds = self.client.post("/api/v2/chart/full", json=with_seconds_payload)

        self.assertEqual(without_seconds.status_code, 200)
        self.assertEqual(with_seconds.status_code, 200)
        base = without_seconds.get_json()
        exact = with_seconds.get_json()
        self.assertEqual(base["birth"]["time"], "06:15:00")
        self.assertEqual(exact["birth"]["time"], "06:15:52")
        self.assertEqual(exact["birth"]["second"], 52)
        self.assertGreater(exact["lagna"]["longitude"], base["lagna"]["longitude"])
        self._assert_astroseek_verified_vargas(exact)

    def test_chart_full_marks_levo_vargas_astroseek_verified(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "levo", "name": "Levo", "group": "Grup-01"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Levo reference",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self._assert_astroseek_verified_vargas(response.get_json())

    def test_analysis_modules_are_always_returned_as_technical_statuses(self):
        data = self._sample_v2_chart()
        modules = data["analysis_modules"]
        self.assertEqual(
            set(modules.keys()),
            {
                "prashna",
                "muhurta",
                "health",
                "finance",
                "children_education",
                "property_legal",
                "vastu",
                "spiritual_karma_dharma",
                "varshaphala",
            },
        )
        expected_packet_keys = {
            "module",
            "label",
            "status",
            "confidence",
            "reason",
            "available_data",
            "missing_data",
            "evidence_refs",
            "required_vargas",
            "supporting_vargas",
            "safety_notes",
        }
        for module_key, packet in modules.items():
            self.assertEqual(set(packet.keys()), expected_packet_keys)
            self.assertEqual(packet["module"], module_key)
            self.assertIsInstance(packet["available_data"], list)
            self.assertIsInstance(packet["missing_data"], list)
            self.assertIsInstance(packet["evidence_refs"], list)
            self.assertIn("technical_evidence_only", packet["safety_notes"])
            self.assertNotIn("interpretation", packet)
            self.assertNotIn("prediction", packet)

        self.assertEqual(modules["prashna"]["status"], "requires_context")
        self.assertEqual(modules["prashna"]["confidence"], "none")
        self.assertIn("context.question_text", modules["prashna"]["missing_data"])
        self.assertIn("context.question_datetime", modules["prashna"]["missing_data"])
        self.assertIn("requires_separate_prashna_chart", modules["prashna"]["safety_notes"])

        self.assertEqual(modules["muhurta"]["status"], "requires_context")
        self.assertIn("context.candidate_datetime", modules["muhurta"]["missing_data"])
        self.assertIn("requires_separate_muhurta_datetime", modules["muhurta"]["safety_notes"])

        health = modules["health"]
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["confidence"], "high")
        self.assertIn("D1", health["available_data"])
        self.assertIn("D6", health["available_data"])
        self.assertIn("D12", health["available_data"])
        self.assertIn("D30", health["available_data"])
        self.assertIn("houses", health["available_data"])
        self.assertIn("lordships", health["available_data"])
        self.assertIn("dashas", health["available_data"])
        self.assertNotIn("vargas.D6", health["missing_data"])
        self.assertNotIn("vargas.D30", health["missing_data"])
        self.assertIn("houses.1", health["evidence_refs"])
        self.assertIn("houses.6", health["evidence_refs"])
        self.assertIn("houses.8", health["evidence_refs"])
        self.assertIn("houses.12", health["evidence_refs"])
        self.assertIn("not_medical_advice", health["safety_notes"])
        self.assertNotIn("limited_by_low_confidence_or_pending_varga", health["safety_notes"])

        self.assertIn("D11", modules["finance"]["available_data"])
        self.assertEqual(modules["finance"]["status"], "ready")
        self.assertNotIn("vargas.D11", modules["finance"]["missing_data"])
        self.assertIn("not_financial_advice", modules["finance"]["safety_notes"])
        self.assertIn("D24", modules["children_education"]["available_data"])
        self.assertNotIn("vargas.D24", modules["children_education"]["missing_data"])
        self.assertIn("D4", modules["property_legal"]["available_data"])
        self.assertNotIn("vargas.D4", modules["property_legal"]["missing_data"])
        self.assertIn("not_legal_advice", modules["property_legal"]["safety_notes"])
        self.assertIn("D4", modules["vastu"]["available_data"])
        self.assertNotIn("vargas.D4", modules["vastu"]["missing_data"])
        self.assertIn("D20", modules["spiritual_karma_dharma"]["available_data"])
        self.assertNotIn("vargas.D20", modules["spiritual_karma_dharma"]["missing_data"])
        self.assertIn("varshaphala", modules["varshaphala"]["available_data"])
        self.assertIn("tajik.full_saham_catalog", modules["varshaphala"]["missing_data"])
        self.assertIn("tajik.saham_day_night_variants", modules["varshaphala"]["missing_data"])

        decision_engine = data["decision_engine"]
        self.assertEqual(decision_engine["version"], "0.1")
        self.assertEqual(decision_engine["scope"], "technical_analysis_only")
        self.assertEqual(
            set(decision_engine["modules"].keys()),
            {
                "panchanga_tithi",
                "muhurta",
                "prashna",
                "health",
                "finance",
                "property_legal",
                "vastu",
                "spiritual_karma_dharma",
                "varshaphala",
                "chara_dasha",
                "yogini_dasha",
            },
        )
        expected_decision_keys = {
            "status",
            "score",
            "confidence",
            "decision",
            "reasons",
            "warnings",
            "missing_data",
            "evidence_refs",
            "safety_notes",
        }
        for key, packet in decision_engine["modules"].items():
            self.assertTrue(expected_decision_keys.issubset(packet.keys()), key)
            self.assertEqual(packet["decision"], "technical_only")
            self.assertIsInstance(packet["score"], int)
            self.assertIn("no_prediction_generated", packet["safety_notes"])
            self.assertNotIn("prediction", packet)

        tithi_decision = decision_engine["modules"]["panchanga_tithi"]
        self.assertEqual(tithi_decision["status"], "ready")
        self.assertEqual(tithi_decision["confidence"], "medium")
        self.assertIn("technical_packet", tithi_decision)
        self.assertEqual(tithi_decision["technical_packet"]["tithi_name"], data["panchanga"]["tithi"]["name"])
        self.assertIn("generic_panchanga_meaning_not_event_specific_muhurta", tithi_decision["safety_notes"])

        self.assertEqual(decision_engine["modules"]["muhurta"]["status"], "requires_context")
        self.assertIn("context.candidate_datetime", decision_engine["modules"]["muhurta"]["missing_data"])
        self.assertIn("requires_separate_context_before_decision", decision_engine["modules"]["muhurta"]["warnings"])
        self.assertEqual(decision_engine["modules"]["prashna"]["status"], "requires_context")
        self.assertEqual(decision_engine["modules"]["health"]["status"], "ready")
        self.assertEqual(decision_engine["modules"]["chara_dasha"]["status"], "limited")
        self.assertEqual(decision_engine["modules"]["chara_dasha"]["score"], 45)
        self.assertIn("dashas.chara.parampara_specific_variants", decision_engine["modules"]["chara_dasha"]["missing_data"])
        self.assertIn("dashas.chara.current_active.maha", decision_engine["modules"]["chara_dasha"]["evidence_refs"])
        self.assertIn("dashas.chara.current_active.antara", decision_engine["modules"]["chara_dasha"]["evidence_refs"])
        self.assertEqual(decision_engine["modules"]["yogini_dasha"]["status"], "limited")
        self.assertEqual(decision_engine["modules"]["yogini_dasha"]["score"], 42)
        self.assertIn("dashas.yogini.interpretive_judgement_rules", decision_engine["modules"]["yogini_dasha"]["missing_data"])
        self.assertIn("dashas.yogini.current_active.maha", decision_engine["modules"]["yogini_dasha"]["evidence_refs"])
        self.assertIn("dashas.yogini.current_active.antara", decision_engine["modules"]["yogini_dasha"]["evidence_refs"])
        self.assertIn("dashas.yogini.current_active.pratyantar", decision_engine["modules"]["yogini_dasha"]["evidence_refs"])

    def test_analysis_modules_ignore_subset_hint_and_keep_full_technical_pack(self):
        data = self._sample_v2_chart({"analysis_modules": "health,finance,health"})
        self.assertEqual(
            set(data["analysis_modules"].keys()),
            {
                "prashna",
                "muhurta",
                "health",
                "finance",
                "children_education",
                "property_legal",
                "vastu",
                "spiritual_karma_dharma",
                "varshaphala",
            },
        )

    def test_beta_page_is_additive_to_expert_dashboard(self):
        dashboard_response = self.client.get("/")
        beta_response = self.client.get("/beta")

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(beta_response.status_code, 200)
        dashboard_html = dashboard_response.get_data(as_text=True)
        self.assertIn("Okuma Paneli", dashboard_html)
        self.assertIn("Rektifikasyona Geç", dashboard_html)
        self.assertIn('id="btn-open-rectification"', dashboard_html)
        for division in ["D1", "D2", "D3", "D4", "D6", "D7", "D9", "D10", "D11", "D12", "D20", "D24", "D30", "D60"]:
            self.assertIn(f'data-varga="{division}"', dashboard_html)
        self.assertIn("Progresif Vedik Beta", beta_response.get_data(as_text=True))

    def test_local_access_security_headers_and_request_size_limit(self):
        local_response = self.client.get("/")
        self.assertEqual(local_response.status_code, 200)
        self.assertEqual(local_response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(local_response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(local_response.headers["Referrer-Policy"], "no-referrer")

        api_response = self.client.get("/api/v2/vault/list")
        self.assertEqual(api_response.headers["Cache-Control"], "no-store")

        external_response = self.client.get(
            "/api/v2/vault/list",
            environ_base={"REMOTE_ADDR": "192.0.2.10"},
        )
        self.assertEqual(external_response.status_code, 403)
        self.assertIn("yalnızca yerel cihazdan", external_response.get_json()["error"])

        old_limit = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 128
        try:
            oversized_response = self.client.post(
                "/api/v2/chart/full",
                data='{"payload":"' + ("x" * 256) + '"}',
                content_type="application/json",
            )
        finally:
            app.config["MAX_CONTENT_LENGTH"] = old_limit

        self.assertEqual(oversized_response.status_code, 413)
        self.assertIn("boyut sınırını", oversized_response.get_json()["error"])
        chart_js = (PROJECT_ROOT / "static" / "js" / "chart.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function vaultSaveChartPayload(chart)", chart_js)
        self.assertIn("delete payload.life_period_analysis", chart_js)
        self.assertIn("chart: vaultSaveChartPayload(lastChartData)", chart_js)
        self.assertIn("const RECTIFICATION_API_BASE = 'http://127.0.0.1:5051'", chart_js)
        self.assertIn("rectificationApiUrl('/api/v2/rectification/analyze')", chart_js)
        self.assertIn("rectificationApiUrl('/api/v2/rectification/save')", chart_js)
        self.assertIn("productStatus.can_save_rectified_time", chart_js)
        self.assertIn("productStatus.code || decision.status", chart_js)
        self.assertIn("['Rektifikasyon Kaynağı', quality.rectification_source_label || quality.rectification_source]", chart_js)
        self.assertIn("const scoreV1 = data.rectification_score_v1 || {};", chart_js)
        self.assertIn("<span>Skor v1</span>", chart_js)
        self.assertIn("scoreV1.excluded_from_score", chart_js)
        self.assertIn("function vaultRectifiedTimeSaveBlockReason(chart)", chart_js)
        self.assertIn("currentRectificationProductStatus()", chart_js)
        self.assertIn("const rectifiedSaveBlockReason = vaultRectifiedTimeSaveBlockReason(lastChartData);", chart_js)
        self.assertIn("v1_gate_missing", chart_js)

    def test_rectification_app_exposes_only_rectification_surface(self):
        from rectification_app import rectification_app

        rectification_client = rectification_app.test_client()
        health_response = rectification_client.get("/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(
            health_response.get_json()["status"],
            "rectification_service_ready",
        )
        self.assertEqual(health_response.headers["Cache-Control"], "no-store")
        self.assertEqual(rectification_client.get("/healthz").status_code, 200)

        cors_health_response = rectification_client.get(
            "/health",
            headers={"Origin": "http://127.0.0.1:5000"},
        )
        self.assertEqual(
            cors_health_response.headers["Access-Control-Allow-Origin"],
            "http://127.0.0.1:5000",
        )

        preflight_response = rectification_client.open(
            "/api/v2/rectification/analyze",
            method="OPTIONS",
            headers={
                "Origin": "http://127.0.0.1:5000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        self.assertEqual(preflight_response.status_code, 200)
        self.assertEqual(
            preflight_response.headers["Access-Control-Allow-Origin"],
            "http://127.0.0.1:5000",
        )

        blocked_origin_response = rectification_client.get(
            "/health",
            headers={"Origin": "http://example.com"},
        )
        self.assertNotIn("Access-Control-Allow-Origin", blocked_origin_response.headers)

        chart_response = rectification_client.post("/api/v2/chart/full", json={})
        self.assertEqual(chart_response.status_code, 404)

        for route in (
            "/api/v2/rectification/analyze",
            "/api/v2/rectification/report",
            "/api/v2/rectification/save",
        ):
            self.assertEqual(self.client.post(route, json={}).status_code, 404)

        analyze_response = rectification_client.post(
            "/api/v2/rectification/analyze",
            json={},
        )
        self.assertEqual(analyze_response.status_code, 400)
        self.assertIn("Geçersiz veri", analyze_response.get_json()["error"])

        external_response = rectification_client.get(
            "/health",
            environ_base={"REMOTE_ADDR": "192.0.2.10"},
        )
        self.assertEqual(external_response.status_code, 200)
        self.assertEqual(
            external_response.get_json()["status"],
            "rectification_service_ready",
        )

        old_local = rectification_app.config["LOCAL_ACCESS_ONLY"]
        old_token = rectification_app.config["API_TOKEN"]
        try:
            rectification_app.config["LOCAL_ACCESS_ONLY"] = False
            rectification_app.config["API_TOKEN"] = "separate-test-token"
            self.assertEqual(rectification_client.get("/health").status_code, 200)
            self.assertEqual(
                rectification_client.post("/api/v2/rectification/analyze", json={}).status_code,
                401,
            )
            authorized = rectification_client.post(
                "/api/v2/rectification/analyze",
                json={},
                headers={"Authorization": "Bearer separate-test-token"},
            )
            self.assertEqual(authorized.status_code, 400)
            rectification_app.config["API_TOKEN"] = ""
            self.assertEqual(rectification_client.get("/health").status_code, 200)
            self.assertEqual(
                rectification_client.post("/api/v2/rectification/analyze", json={}).status_code,
                503,
            )
        finally:
            rectification_app.config["LOCAL_ACCESS_ONLY"] = old_local
            rectification_app.config["API_TOKEN"] = old_token

    def test_dashboard_exposes_panchanga_district_city_input(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Panchanga İlçe / İl", html)
        self.assertIn('id="panchanga-place"', html)
        self.assertIn('list="panchanga-place-options"', html)
        self.assertIn('id="panchanga-place-options"', html)

    def test_beta_profile_saves_valid_birth_and_chart_reference(self):
        response = self.client.post(
            "/api/v2/beta/profile",
            json=self._sample_beta_profile_payload(),
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "profile_saved")
        self.assertTrue(data["profile_id"])
        self.assertTrue(data["chart_id"])
        self.assertEqual(data["profile"]["name"], "Beta Kisi")
        self.assertIn("lagna", data["chart_summary"])
        self.assertEqual(data["chart_summary"]["schema_version"], "vedic-pwa-chart-summary-v2")
        self.assertEqual(data["chart_summary"]["display_name"], "Beta Kisi")
        self.assertGreaterEqual(len(data["chart_summary"]["planets"]), 9)
        self.assertIn("D9", data["chart_summary"]["vargas"])
        self.assertTrue(data["chart_summary"]["active_dasha_periods"][0]["start_date"])
        self.assertTrue(data["chart_summary"]["active_dasha_periods"][0]["end_date"])
        self.assertEqual(data["usage"]["chat"]["limit"], 20)

    def test_beta_chart_summary_returns_only_owned_browser_summary(self):
        payload = self._sample_beta_profile_payload()
        payload.update({
            "owner_user_id": "11111111-1111-4111-8111-111111111111",
            "profile_id": "22222222-2222-4222-8222-222222222222",
            "chart_id": "33333333-3333-4333-8333-333333333333",
        })
        create_response = self.client.post("/api/v2/beta/profile", json=payload)
        self.assertEqual(create_response.status_code, 200)

        response = self.client.post(
            "/api/v2/beta/chart/summary",
            json={
                "owner_user_id": payload["owner_user_id"],
                "profile_id": payload["profile_id"],
                "chart_id": payload["chart_id"],
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "summary_ready")
        self.assertEqual(data["chart_summary"]["schema_version"], "vedic-pwa-chart-summary-v2")
        self.assertNotIn("dashas", data["chart_summary"])
        self.assertNotIn("topic_packets", data["chart_summary"])

        forbidden = self.client.post(
            "/api/v2/beta/chart/summary",
            json={
                "owner_user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "profile_id": payload["profile_id"],
                "chart_id": payload["chart_id"],
            },
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_beta_profile_rejects_invalid_birth(self):
        payload = self._sample_beta_profile_payload()
        payload["birth"]["month"] = 13

        response = self.client.post("/api/v2/beta/profile", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Geçersiz beta profil verisi", response.get_json()["error"])

    def test_beta_chat_draft_returns_technical_evidence_package(self):
        profile_response = self.client.post(
            "/api/v2/beta/profile",
            json=self._sample_beta_profile_payload(),
        )
        profile = profile_response.get_json()

        response = self.client.post(
            "/api/v2/beta/chat/draft",
            json={
                "profile_id": profile["profile_id"],
                "chart_id": profile["chart_id"],
                "question": "Kariyer açısından hangi teknik kanıtlar var?",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["topic"], "career")
        self.assertIn(data["status"], {"evidence_ready", "evidence_ready_with_missing_layers"})
        self.assertIn("evidence", data)
        self.assertIn("topic_packet", data["evidence"])
        self.assertIn("active_dasha", data["evidence"])
        self.assertIn("missing", data)
        self.assertIn(data["confidence"], {"low", "medium", "high"})
        self.assertIn("safety_notes", data)
        self.assertIn("next_action", data)
        self.assertEqual(data["usage"]["chat"]["used"], 1)

    def test_beta_chat_reports_missing_layers_without_interpretation(self):
        profile_response = self.client.post(
            "/api/v2/beta/profile",
            json=self._sample_beta_profile_payload(),
        )
        profile = profile_response.get_json()

        response = self.client.post(
            "/api/v2/beta/chat/draft",
            json={
                "profile_id": profile["profile_id"],
                "chart_id": profile["chart_id"],
                "question": "Rektifikasyon için hangi kanıtlar eksik?",
            },
        )

        self.assertEqual(response.status_code, 422)
        data = response.get_json()
        self.assertEqual(data["status"], "rectification_service_separate")
        self.assertEqual(
            data["error_code"],
            "rectification_not_available_in_customer_api",
        )

    def test_beta_chat_daily_limit_returns_controlled_response(self):
        profile_response = self.client.post(
            "/api/v2/beta/profile",
            json=self._sample_beta_profile_payload(),
        )
        profile = profile_response.get_json()
        app.config["BETA_DAILY_CHAT_LIMIT"] = 0

        response = self.client.post(
            "/api/v2/beta/chat/draft",
            json={
                "profile_id": profile["profile_id"],
                "chart_id": profile["chart_id"],
                "question": "Kariyer?",
            },
        )

        self.assertEqual(response.status_code, 429)
        data = response.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["status"], "limit_exceeded")
        self.assertEqual(data["usage"]["chat"]["remaining"], 0)

    def test_beta_feedback_and_usage_are_recorded(self):
        profile_response = self.client.post(
            "/api/v2/beta/profile",
            json=self._sample_beta_profile_payload(),
        )
        profile = profile_response.get_json()
        chat_response = self.client.post(
            "/api/v2/beta/chat/draft",
            json={
                "profile_id": profile["profile_id"],
                "chart_id": profile["chart_id"],
                "question": "Para açısından hangi kanıtlar var?",
            },
        )
        message = chat_response.get_json()

        feedback_response = self.client.post(
            "/api/v2/beta/feedback",
            json={
                "profile_id": profile["profile_id"],
                "message_id": message["message_id"],
                "rating": "good",
            },
        )
        usage_response = self.client.get(
            f"/api/v2/beta/usage?profile_id={profile['profile_id']}"
        )

        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.get_json()["status"], "feedback_saved")
        self.assertEqual(usage_response.status_code, 200)
        usage = usage_response.get_json()
        self.assertEqual(usage["counts"]["chat_messages"], 1)
        self.assertEqual(usage["counts"]["feedback"], 1)

    def test_full_chart_supports_timezone_id_and_maps_d1_d9(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["meta"]["api_version"], "v2")
        self.assertEqual(data["birth"]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(data["birth"]["tz_offset"], 3.0)
        self.assertEqual(set(data["angles"].keys()), {"lagna", "mc", "dsc"})
        self.assertEqual(data["angles"]["lagna"]["sign_index"], data["lagna"]["sign_index"])
        self.assertEqual(data["angles"]["lagna"]["house"], 1)
        self.assertEqual(
            data["angles"]["dsc"]["sign_index"],
            (data["lagna"]["sign_index"] + 6) % 12,
        )
        self.assertEqual(data["angles"]["dsc"]["house"], 7)
        self.assertIn(data["angles"]["mc"]["house"], range(1, 13))
        self.assertEqual(data["angles"]["mc"]["confidence"], "high")
        for angle_key in ("lagna", "mc", "dsc"):
            nakshatra = data["angles"][angle_key]["nakshatra"]
            self.assertIn("name", nakshatra)
            self.assertIn("pada", nakshatra)
            self.assertIn("lord", nakshatra)
        self.assertIn("D1", data["vargas"])

        for division, name in {
            "D1": "Rashi",
            "D2": "Hora",
            "D3": "Drekkana",
            "D4": "Chaturthamsha",
            "D6": "Shashthamsa",
            "D7": "Saptamsha",
            "D9": "Navamsha",
            "D10": "Dashamsha",
            "D11": "Rudramsa",
            "D12": "Dwadashamsha",
            "D20": "Vimshamsha",
            "D24": "Chaturvimshamsha",
            "D30": "Trimshamsha",
            "D60": "Shashtiamsha",
        }.items():
            self.assertIn(division, data["vargas"])
            self.assertEqual(data["vargas"][division]["name"], name)
            self.assertIn("lagna", data["vargas"][division])
            self.assertIn("sign", data["vargas"][division]["lagna"])
            self.assertEqual(len(data["vargas"][division]["planets"]), 9)
            self.assertIn("confidence", data["vargas"][division])
            self.assertIn("source_rule", data["vargas"][division])
        varga_planets_by_division = {
            division: {
                planet["name"]: planet
                for planet in data["vargas"][division]["planets"]
            }
            for division in ["D1", "D2", "D3", "D4", "D6", "D7", "D9", "D10", "D11", "D12", "D20", "D24", "D30", "D60"]
        }
        lagna_vargottama = (
            data["lagna"]["sign_index"]
            == data["vargas"]["D9"]["lagna"]["sign_index"]
        )
        for planet in data["planets"]:
            varga_status = planet["varga_status"]
            for division in ["D1", "D2", "D3", "D4", "D6", "D7", "D9", "D10", "D11", "D12", "D20", "D24", "D30", "D60"]:
                self.assertIn(division, varga_status)
                self.assertEqual(
                    varga_status[division]["sign"],
                    varga_planets_by_division[division][planet["name"]]["sign"],
                )
                self.assertEqual(
                    varga_status[division]["sign_index"],
                    varga_planets_by_division[division][planet["name"]]["sign_index"],
                )
                self.assertEqual(
                    varga_status["vargas"][division],
                    varga_status[division]["sign"],
                )
            self.assertIn("vargottama", varga_status)
            self.assertIn("lagna_vargottama", varga_status)
            self.assertIn("vargas", varga_status)
            self.assertEqual(varga_status["D1"]["sign"], planet["sign"])
            self.assertEqual(varga_status["D1"]["sign_index"], planet["sign_index"])
            self.assertEqual(
                varga_status["vargottama"],
                varga_status["D1"]["sign_index"] == varga_status["D9"]["sign_index"],
            )
            self.assertEqual(varga_status["lagna_vargottama"], lagna_vargottama)
        self.assertIn("vimshopaka_bala", data)
        vimshopaka = data["vimshopaka_bala"]
        self.assertEqual(vimshopaka["status"], "starter_technical_layer")
        self.assertEqual(vimshopaka["score_status"], "not_final")
        self.assertFalse(vimshopaka["summary"]["scored"])
        self.assertFalse(vimshopaka["summary"]["rahu_ketu_scored"])
        self.assertFalse(vimshopaka["summary"]["rectification_score_used"])
        self.assertEqual(len(vimshopaka["planets"]), 7)
        self.assertEqual(
            {planet["planet"] for planet in vimshopaka["planets"]},
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
        )
        self.assertEqual(
            {planet["planet"] for planet in vimshopaka["excluded_planets"]},
            {"Rahu (True)", "Ketu"},
        )
        self.assertEqual(
            vimshopaka["schemes"]["saptavarga"]["weights_status"],
            "pending_reference_validation",
        )
        sun_vimshopaka = next(
            planet for planet in vimshopaka["planets"] if planet["planet"] == "Sun"
        )
        self.assertEqual(
            sun_vimshopaka["schemes"]["saptavarga"]["score_status"],
            "not_final",
        )
        self.assertEqual(
            [row["division"] for row in sun_vimshopaka["schemes"]["saptavarga"]["rows"]],
            SAPTAVARGA_DIVISIONS,
        )
        self.assertIn("avasthas", data)
        avasthas = data["avasthas"]
        self.assertEqual(avasthas["status"], "starter_technical_layer")
        self.assertEqual(avasthas["score_status"], "not_scored")
        self.assertFalse(avasthas["summary"]["scored"])
        self.assertFalse(avasthas["summary"]["rahu_ketu_scored"])
        self.assertFalse(avasthas["summary"]["rectification_score_used"])
        self.assertEqual(len(avasthas["planets"]), 7)
        self.assertEqual(
            {planet["planet"] for planet in avasthas["planets"]},
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
        )
        self.assertEqual(
            {planet["planet"] for planet in avasthas["excluded_planets"]},
            {"Rahu (True)", "Ketu"},
        )
        sun_avastha = next(
            planet for planet in avasthas["planets"] if planet["planet"] == "Sun"
        )
        self.assertEqual(sun_avastha["bala_avastha"]["score_status"], "not_scored")
        self.assertEqual(
            sun_avastha["jagradadi_avastha"]["status"],
            "pending_reference_validation",
        )
        self.assertEqual(sun_avastha["deeptadi_avastha"]["score"], None)
        self.assertEqual(
            sun_avastha["lajjitaadi_avastha"]["status"],
            "not_available_pending_rules",
        )
        dignity_by_planet = {
            planet["name"]: planet["dignity"]
            for planet in data["planets"]
        }
        self.assertEqual(dignity_by_planet["Sun"]["natural_friendship"], "enemy")
        self.assertEqual(dignity_by_planet["Sun"]["essential"], "enemy")
        self.assertTrue(dignity_by_planet["Mars"]["neecha"])
        self.assertEqual(dignity_by_planet["Mars"]["essential"], "debilitated")
        self.assertEqual(dignity_by_planet["Jupiter"]["natural_friendship"], "enemy")
        self.assertEqual(dignity_by_planet["Venus"]["natural_friendship"], "friend")
        combustion_by_planet = {
            planet["name"]: planet["combustion"]
            for planet in data["planets"]
        }
        for combustion in combustion_by_planet.values():
            self.assertIn("is_combust", combustion)
            self.assertIn("distance_from_sun", combustion)
            self.assertIn("threshold", combustion)
            self.assertIn("severity", combustion)
        self.assertEqual(combustion_by_planet["Sun"]["severity"], "not_calculated")
        self.assertEqual(combustion_by_planet["Sun"]["threshold"], None)
        self.assertEqual(combustion_by_planet["Moon"]["severity"], "none")
        self.assertEqual(combustion_by_planet["Moon"]["threshold"], None)
        self.assertEqual(combustion_by_planet["Mars"]["threshold"], 17.0)
        self.assertFalse(combustion_by_planet["Mars"]["is_combust"])
        self.assertEqual(combustion_by_planet["Mars"]["severity"], "none")
        war_by_planet = {
            planet["name"]: planet["war"]
            for planet in data["planets"]
        }
        for war in war_by_planet.values():
            self.assertIn("in_graha_yuddha", war)
            self.assertIn("opponent", war)
            self.assertIn("status", war)
            self.assertIn("orb", war)
        self.assertEqual(war_by_planet["Sun"]["status"], "not_applicable")
        self.assertEqual(war_by_planet["Moon"]["status"], "not_applicable")
        self.assertEqual(war_by_planet["Rahu (True)"]["status"], "not_applicable")
        self.assertEqual(war_by_planet["Ketu"]["status"], "not_applicable")
        self.assertEqual(war_by_planet["Mars"]["status"], "none")
        self.assertFalse(war_by_planet["Mars"]["in_graha_yuddha"])
        graha_drishti = data["aspects"]["graha_drishti"]
        self.assertEqual(len(graha_drishti), 13)
        self.assertIn("rashi_drishti", data["aspects"])
        rashi_drishti = data["aspects"]["rashi_drishti"]
        self.assertEqual(len(rashi_drishti), 27)
        expected_rashi_keys = {
            "from",
            "from_id",
            "from_house",
            "from_sign",
            "from_sign_index",
            "from_rashi_type",
            "to_house",
            "to_sign",
            "to_sign_index",
            "to_rashi_type",
            "to_planets",
            "aspect_type",
            "strength",
        }
        for aspect in rashi_drishti:
            self.assertEqual(set(aspect.keys()), expected_rashi_keys)
            self.assertEqual(aspect["aspect_type"], "jaimini_rashi_drishti")
            self.assertEqual(aspect["strength"], "sign")
            self.assertIn(aspect["from_rashi_type"], {"movable", "fixed", "dual"})
            self.assertIn(aspect["to_rashi_type"], {"movable", "fixed", "dual"})
        mars_special_4th = next(
            aspect for aspect in graha_drishti
            if aspect["from"] == "Mars" and aspect["aspect_type"] == "special_4th"
        )
        self.assertEqual(mars_special_4th["to_house"], 10)
        self.assertEqual(mars_special_4th["to_sign"], "Libra")
        self.assertEqual(mars_special_4th["strength"], "full")
        jupiter_special_9th = next(
            aspect for aspect in graha_drishti
            if aspect["from"] == "Jupiter" and aspect["aspect_type"] == "special_9th"
        )
        self.assertEqual(jupiter_special_9th["to_house"], 2)
        self.assertEqual(jupiter_special_9th["to_sign"], "Aquarius")
        saturn_special_10th = next(
            aspect for aspect in graha_drishti
            if aspect["from"] == "Saturn" and aspect["aspect_type"] == "special_10th"
        )
        self.assertEqual(saturn_special_10th["to_house"], 5)
        self.assertEqual(saturn_special_10th["to_planets"], ["Sun"])
        self.assertTrue(any(
            aspect["from"] == "Saturn" and aspect["aspect_type"] == "special_3rd"
            for aspect in graha_drishti
        ))
        self.assertEqual(len(data["houses"]), 12)
        self.assertEqual(data["houses"][0]["house"], 1)
        self.assertEqual(data["houses"][0]["sign"], data["lagna"]["sign"])
        self.assertEqual(
            set(data["houses"][9]["aspected_by"]),
            {"Mars", "Mercury", "Jupiter", "Saturn"},
        )
        self.assertEqual(
            set(data["houses"][1]["aspected_by"]),
            {"Mars", "Jupiter", "Saturn"},
        )
        self.assertEqual(data["houses"][0]["lord"], data["lordships"]["1"]["lord"])
        self.assertTrue(any(house["rashi_aspected_by"] for house in data["houses"]))
        self.assertEqual(len(data["lordships"]), 12)
        self.assertIn("lord_house", data["lordships"]["1"])
        self.assertIn("condition", data["lordships"]["1"])
        self.assertIn("moolatrikona", data["lordships"]["1"]["condition"])
        self.assertIn("natural_friendship", data["lordships"]["1"]["condition"])
        self.assertEqual(
            data["lordships"]["1"]["lord_sign"],
            next(
                planet["sign"]
                for planet in data["planets"]
                if planet["name"] == data["lordships"]["1"]["lord"]
            ),
        )
        self.assertEqual(data["jaimini"]["chara_karakas"]["system"], "7-karaka")
        self.assertFalse(data["jaimini"]["chara_karakas"]["include_rahu"])
        for role in ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]:
            self.assertIn(role, data["jaimini"]["chara_karakas"])
            self.assertIn("planet", data["jaimini"]["chara_karakas"][role])
        self.assertEqual(data["jaimini"]["arudha"]["status"], "implemented_strengths")
        self.assertEqual(len(data["jaimini"]["arudha"]["padas"]), 12)
        self.assertIn("A1", data["jaimini"]["arudha"]["padas"])
        self.assertIn("upapada", data["jaimini"]["arudha"])
        self.assertIn("source_rule", data["jaimini"]["arudha"])
        self.assertIn("assumptions", data["jaimini"]["arudha"])
        self.assertIn("excluded_rules", data["jaimini"]["arudha"])
        self.assertIn("upapada_detail", data["jaimini"]["arudha"])
        upapada_detail = data["jaimini"]["arudha"]["upapada_detail"]
        self.assertEqual(upapada_detail["status"], "implemented_technical_detail")
        self.assertIn("method", upapada_detail)
        self.assertIn("source_rule", upapada_detail)
        self.assertIn("assumptions", upapada_detail)
        self.assertIn("excluded_rules", upapada_detail)
        self.assertIn("upapada_lord", upapada_detail)
        self.assertIn("second_from_upapada", upapada_detail)
        self.assertIn("occupants", upapada_detail)
        self.assertIn("pada_strengths", data["jaimini"]["arudha"])
        pada_strengths = data["jaimini"]["arudha"]["pada_strengths"]
        self.assertEqual(pada_strengths["status"], "implemented_technical_scoring")
        self.assertEqual(len(pada_strengths["padas"]), 12)
        for key, strength in pada_strengths["padas"].items():
            self.assertTrue(key.startswith("A"))
            self.assertIn("pada_lord", strength)
            self.assertIn("occupants", strength)
            self.assertIn("score", strength)
            self.assertIn("factors", strength)
            self.assertGreaterEqual(strength["score"], 0)
        self.assertEqual(data["jaimini"]["argala"]["status"], "implemented_strengths")
        self.assertIn("source_rule", data["jaimini"]["argala"])
        self.assertIn("assumptions", data["jaimini"]["argala"])
        self.assertIn("excluded_rules", data["jaimini"]["argala"])
        self.assertIn("summary", data["jaimini"]["argala"])
        self.assertIn("strongest_sources", data["jaimini"]["argala"]["summary"])
        self.assertGreaterEqual(len(data["jaimini"]["argala"]["sources"]), 2)
        for source in data["jaimini"]["argala"]["sources"]:
            self.assertEqual(len(source["entries"]), 4)
            self.assertIn("primary_active_count", source)
            self.assertIn("primary_obstructed_count", source)
            self.assertIn("secondary_active_count", source)
            self.assertIn("secondary_obstructed_count", source)
            self.assertIn("net_score", source)
            self.assertIn(source["strength"], {"strong", "moderate", "mild", "neutral", "obstructed"})
            for entry in source["entries"]:
                self.assertIn(entry["type"], {"primary", "secondary"})
                self.assertIn("argala_sign", entry)
                self.assertIn("obstruction_sign", entry)
        karakamsa = data["jaimini"]["karakamsa"]
        self.assertEqual(karakamsa["status"], "implemented_technical_detail")
        self.assertIn("source_rule", karakamsa)
        self.assertIn("assumptions", karakamsa)
        self.assertIn("excluded_rules", karakamsa)
        self.assertIn("karakamsa_lagna", karakamsa)
        self.assertIn("atmakaraka_d1", karakamsa)
        self.assertIn("d9_planets_from_karakamsa", karakamsa)
        self.assertIn("support_factors", karakamsa)
        self.assertIn("challenge_factors", karakamsa)
        self.assertGreaterEqual(len(karakamsa["d9_planets_from_karakamsa"]), 7)
        for row in karakamsa["d9_planets_from_karakamsa"]:
            self.assertIn(row["house_from_karakamsa"], range(1, 13))
            self.assertIn(row["house_class"], {"trikona", "kendra", "dusthana", "upachaya", "other"})
        self.assertEqual(data["jaimini"]["swamsha"]["status"], "implemented_technical_detail")
        self.assertIn("source_rule", data["jaimini"]["swamsha"])
        self.assertIn("assumptions", data["jaimini"]["swamsha"])
        self.assertIn("excluded_rules", data["jaimini"]["swamsha"])
        self.assertIn("d9_planets_from_swamsha", data["jaimini"]["swamsha"])
        self.assertEqual(
            data["jaimini"]["swamsha"]["swamsha_lagna"],
            karakamsa["karakamsa_lagna"],
        )
        vimshottari = data["dashas"]["vimshottari"]
        self.assertEqual(
            vimshottari["levels"],
            ["maha", "antara", "pratyantar", "sookshma", "prana"],
        )
        self.assertGreater(len(vimshottari["maha"]), 0)
        self.assertGreater(len(vimshottari["antara"]), 0)
        self.assertGreater(len(vimshottari["pratyantar"]), 0)
        self.assertGreater(vimshottari["sookshma"]["count"], 0)
        self.assertGreater(vimshottari["prana"]["count"], 0)
        birth_maha = vimshottari["maha"][0]
        self.assertTrue(birth_maha["is_birth_dasha"])
        self.assertIn("actual_start", birth_maha)
        self.assertIn("antara", birth_maha)
        self.assertGreater(len(birth_maha["antara"]), 0)
        birth_antara = next(
            period for period in birth_maha["antara"]
            if period["active_at_birth"]
        )
        self.assertEqual(birth_antara["level"], "antara")
        self.assertIn("pratyantar", birth_antara)
        birth_pratyantar = next(
            period for period in birth_antara["pratyantar"]
            if period["active_at_birth"]
        )
        self.assertEqual(birth_pratyantar["level"], "pratyantar")
        self.assertIn("sookshma", birth_pratyantar)
        birth_sookshma = next(
            period for period in birth_pratyantar["sookshma"]
            if period["active_at_birth"]
        )
        self.assertNotIn("prana", birth_sookshma)
        active = vimshottari["active"]
        self.assertEqual(active["maha"]["lord"], birth_maha["lord"])
        self.assertEqual(active["antara"]["lord"], birth_antara["lord"])
        self.assertEqual(active["pratyantar"]["lord"], birth_pratyantar["lord"])
        self.assertIn("sookshma", active)
        self.assertIn("prana", active)
        self.assertEqual(
            active["path"],
            [
                active["maha"]["lord"],
                active["antara"]["lord"],
                active["pratyantar"]["lord"],
                active["sookshma"]["lord"],
                active["prana"]["lord"],
            ],
        )
        self.assertIn("current_active", vimshottari)
        current_active = vimshottari["current_active"]
        self.assertIn("calculated_for_jd", current_active)
        self.assertIn("path", current_active)
        self.assertGreater(len(current_active["path"]), 0)
        self.assertIn("current_active_generated_at_utc", vimshottari)
        chara = data["dashas"]["chara"]
        self.assertEqual(chara["status"], "implemented_starter_chara_maha_antara")
        self.assertEqual(chara["confidence"], "low")
        self.assertEqual(chara["levels"], ["maha", "antara"])
        self.assertGreater(len(chara["maha"]), 0)
        self.assertGreater(len(chara["antara"]), 0)
        self.assertTrue(any(period.get("antara") for period in chara["maha"]))
        self.assertIn("parampara_specific_chara_antardasha_variants", chara["excluded_rules"])
        self.assertIn("current_active", chara)
        self.assertIn("maha", chara["current_active"])
        self.assertIn("antara", chara["current_active"])
        self.assertIn("path", chara["current_active"])
        self.assertEqual(
            chara["current_active"]["path"],
            [
                chara["current_active"]["maha"]["rashi"],
                chara["current_active"]["antara"]["rashi"],
            ],
        )
        self.assertIn(chara["current_active"]["maha"]["direction"], {"forward", "reverse"})
        self.assertGreater(chara["current_active"]["maha"]["years"], 0)
        self.assertGreater(chara["current_active"]["antara"]["years"], 0)
        yogini = data["dashas"]["yogini"]
        self.assertEqual(yogini["status"], "implemented_starter_yogini_maha_antara_pratyantar")
        self.assertEqual(yogini["confidence"], "low")
        self.assertEqual(yogini["levels"], ["maha", "antara", "pratyantar"])
        self.assertEqual(yogini["cycle_years"], 36)
        self.assertGreater(len(yogini["maha"]), 0)
        self.assertGreater(len(yogini["antara"]), 0)
        self.assertGreater(len(yogini["pratyantar"]), 0)
        self.assertTrue(any(period.get("antara") for period in yogini["maha"]))
        self.assertTrue(any(
            period.get("pratyantar")
            for maha_period in yogini["maha"]
            for period in maha_period.get("antara", [])
        ))
        self.assertNotIn("pratyantardasha", " ".join(yogini["excluded_rules"]))
        self.assertIn("current_active", yogini)
        self.assertIn("maha", yogini["current_active"])
        self.assertIn("antara", yogini["current_active"])
        self.assertIn("pratyantar", yogini["current_active"])
        self.assertIn("path", yogini["current_active"])
        self.assertEqual(
            yogini["current_active"]["path"],
            [
                yogini["current_active"]["maha"]["yogini"],
                yogini["current_active"]["antara"]["yogini"],
                yogini["current_active"]["pratyantar"]["yogini"],
            ],
        )
        self.assertIn(
            yogini["current_active"]["maha"]["yogini"],
            {item["name"] for item in yogini["sequence"]},
        )
        self.assertIn(
            yogini["current_active"]["antara"]["yogini"],
            {item["name"] for item in yogini["sequence"]},
        )
        self.assertIn(
            yogini["current_active"]["pratyantar"]["yogini"],
            {item["name"] for item in yogini["sequence"]},
        )
        self.assertGreater(yogini["current_active"]["maha"]["years"], 0)
        self.assertGreater(yogini["current_active"]["antara"]["years"], 0)
        self.assertGreater(yogini["current_active"]["pratyantar"]["years"], 0)
        missing_keys = {item["key"] for item in data["missing"]}
        self.assertNotIn("aspects.graha_drishti", missing_keys)
        self.assertNotIn("aspects.rashi_drishti", missing_keys)
        self.assertNotIn("vargas.D2", missing_keys)
        self.assertNotIn("vargas.D3", missing_keys)
        self.assertNotIn("vargas.D4", missing_keys)
        self.assertNotIn("vargas.D6", missing_keys)
        self.assertNotIn("vargas.D7", missing_keys)
        self.assertNotIn("vargas.D10", missing_keys)
        self.assertNotIn("vargas.D11", missing_keys)
        self.assertNotIn("vargas.D12", missing_keys)
        self.assertNotIn("vargas.D20", missing_keys)
        self.assertNotIn("vargas.D24", missing_keys)
        self.assertNotIn("vargas.D30", missing_keys)
        self.assertNotIn("vargas.D60", missing_keys)
        self.assertNotIn("dashas.vimshottari.antara", missing_keys)
        self.assertNotIn("dashas.vimshottari.pratyantar", missing_keys)
        self.assertNotIn("houses", missing_keys)
        self.assertNotIn("lordships", missing_keys)
        self.assertNotIn("jaimini", missing_keys)
        self.assertNotIn("jaimini.arudha", missing_keys)
        self.assertNotIn("jaimini.argala", missing_keys)
        self.assertNotIn("jaimini.karakamsa", missing_keys)
        self.assertNotIn("jaimini.swamsha", missing_keys)
        self.assertNotIn("ashtakavarga", missing_keys)
        ashtakavarga = data["ashtakavarga"]
        self.assertEqual(ashtakavarga["status"], "implemented_shodhana_pinda_and_transit_scoring")
        self.assertEqual(ashtakavarga["confidence"], "medium")
        self.assertEqual(
            ashtakavarga["ruleset"]["target_planets"],
            ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
        )
        self.assertEqual(ashtakavarga["ruleset"]["nodes"], "excluded")
        self.assertEqual(set(ashtakavarga["bhinna"].keys()), set(ashtakavarga["ruleset"]["target_planets"]))
        expected_bhinna_totals = {
            "Sun": 48,
            "Moon": 49,
            "Mars": 39,
            "Mercury": 54,
            "Jupiter": 56,
            "Venus": 52,
            "Saturn": 39,
        }
        for planet_name, expected_total in expected_bhinna_totals.items():
            bhinna = ashtakavarga["bhinna"][planet_name]
            self.assertEqual(bhinna["total"], expected_total)
            self.assertEqual(bhinna["expected_total"], expected_total)
            self.assertEqual(len(bhinna["by_sign"]), 12)
            self.assertEqual(sum(row["bindus"] for row in bhinna["by_sign"]), expected_total)
            self.assertEqual(len(bhinna["sources"]), 8)
        self.assertEqual(ashtakavarga["sarva"]["total"], 337)
        self.assertEqual(ashtakavarga["sarva"]["expected_total"], 337)
        self.assertEqual(len(ashtakavarga["sarva"]["by_sign"]), 12)
        self.assertEqual(
            sum(row["bindus"] for row in ashtakavarga["sarva"]["by_sign"]),
            337,
        )
        self.assertIn("transit_scoring", ashtakavarga)
        transit_scoring = ashtakavarga["transit_scoring"]
        self.assertEqual(transit_scoring["status"], "implemented_snapshot_scoring")
        self.assertIn("method", transit_scoring)
        self.assertIn("source_rule", transit_scoring)
        self.assertIn("assumptions", transit_scoring)
        self.assertIn("excluded_rules", transit_scoring)
        self.assertEqual(len(transit_scoring["rows"]), 9)
        for row in transit_scoring["rows"]:
            self.assertIn("planet", row)
            self.assertIn("sarva_bindus", row)
            self.assertIn(row["sarva_support_level"], {"high_support", "moderate_support", "low_support", "challenging"})
            self.assertGreaterEqual(row["sarva_bindus"], 0)
            self.assertLessEqual(row["sarva_bindus"], 56)
            self.assertIn("planet_bhinna_available", row)
        self.assertIn("shodhana", ashtakavarga)
        trikona = ashtakavarga["shodhana"]["trikona"]
        self.assertEqual(trikona["status"], "implemented_technical_variant")
        self.assertIn("method", trikona)
        self.assertIn("source_rule", trikona)
        self.assertIn("assumptions", trikona)
        self.assertIn("excluded_rules", trikona)
        self.assertEqual(len(trikona["groups"]), 4)
        self.assertEqual(set(trikona["planets"].keys()), set(ashtakavarga["ruleset"]["target_planets"]))
        for planet_name, shodhana in trikona["planets"].items():
            self.assertEqual(shodhana["planet"], planet_name)
            self.assertEqual(len(shodhana["groups"]), 4)
            self.assertEqual(len(shodhana["by_sign"]), 12)
            self.assertLessEqual(shodhana["total_after"], shodhana["total_before"])
            self.assertEqual(
                shodhana["total_before"] - shodhana["total_after"],
                shodhana["total_reduction"],
            )
        self.assertEqual(len(trikona["sarva_after_trikona"]["by_sign"]), 12)
        self.assertLess(
            trikona["sarva_after_trikona"]["total"],
            ashtakavarga["sarva"]["total"],
        )
        ekadhipatya = ashtakavarga["shodhana"]["ekadhipatya"]
        self.assertEqual(ekadhipatya["status"], "implemented_technical_variant")
        self.assertIn("method", ekadhipatya)
        self.assertIn("source_rule", ekadhipatya)
        self.assertIn("assumptions", ekadhipatya)
        self.assertIn("excluded_rules", ekadhipatya)
        self.assertEqual(len(ekadhipatya["pairs"]), 5)
        self.assertEqual(set(ekadhipatya["planets"].keys()), set(ashtakavarga["ruleset"]["target_planets"]))
        for planet_name, shodhana in ekadhipatya["planets"].items():
            self.assertEqual(shodhana["planet"], planet_name)
            self.assertEqual(len(shodhana["pairs"]), 5)
            self.assertEqual(len(shodhana["by_sign"]), 12)
            self.assertLessEqual(shodhana["total_after"], shodhana["total_before"])
            self.assertEqual(
                shodhana["total_before"] - shodhana["total_after"],
                shodhana["total_reduction"],
            )
            for pair in shodhana["pairs"]:
                self.assertIn(pair["action"], {
                    "skipped_zero_bindu_pair",
                    "skipped_both_signs_occupied",
                    "reduced_unoccupied_pair_sign",
                    "reduced_both_unoccupied_pair_signs_by_minimum",
                })
                self.assertEqual(len(pair["signs"]), 2)
        self.assertEqual(len(ekadhipatya["sarva_after_ekadhipatya"]["by_sign"]), 12)
        self.assertLessEqual(
            ekadhipatya["sarva_after_ekadhipatya"]["total"],
            trikona["sarva_after_trikona"]["total"],
        )
        shodhya_pinda = ashtakavarga["shodhana"]["shodhya_pinda"]
        self.assertEqual(shodhya_pinda["status"], "implemented_technical_variant")
        self.assertIn("method", shodhya_pinda)
        self.assertIn("source_rule", shodhya_pinda)
        self.assertIn("assumptions", shodhya_pinda)
        self.assertIn("excluded_rules", shodhya_pinda)
        self.assertEqual(shodhya_pinda["rashi_gunakara"]["Aries"], 7)
        self.assertEqual(shodhya_pinda["rashi_gunakara"]["Pisces"], 12)
        self.assertEqual(shodhya_pinda["graha_gunakara"]["Jupiter"], 10)
        self.assertEqual(set(shodhya_pinda["planets"].keys()), set(ashtakavarga["ruleset"]["target_planets"]))
        self.assertEqual(len(shodhya_pinda["ranking"]), 7)
        for planet_name, pinda in shodhya_pinda["planets"].items():
            self.assertEqual(pinda["planet"], planet_name)
            self.assertEqual(len(pinda["rashi_rows"]), 12)
            self.assertEqual(len(pinda["graha_rows"]), 7)
            self.assertEqual(
                pinda["shodhya_pinda"],
                pinda["rashi_pinda"] + pinda["graha_pinda"],
            )
        self.assertGreaterEqual(pinda["shodhya_pinda"], 0)
        self.assertIn("shadbala", data)
        shadbala = data["shadbala"]
        self.assertEqual(shadbala["status"], "implemented_professional_total_v1")
        self.assertEqual(shadbala["confidence"], "medium")
        self.assertEqual(shadbala["conversion"]["rupa_to_virupa"], 60)
        summary = shadbala["summary"]
        self.assertEqual(summary["planet_count"], 7)
        self.assertEqual(len(summary["ranking_by_total_rupa"]), 7)
        self.assertEqual(len(summary["ranking_by_strength_ratio"]), 7)
        self.assertEqual(
            {row["planet"] for row in summary["ranking_by_total_rupa"]},
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
        )
        self.assertEqual(
            {row["planet"] for row in summary["ranking_by_strength_ratio"]},
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
        )
        self.assertEqual(
            summary["ranking_by_total_rupa"],
            sorted(
                summary["ranking_by_total_rupa"],
                key=lambda item: item["total_rupa"],
                reverse=True,
            ),
        )
        self.assertEqual(
            summary["ranking_by_strength_ratio"],
            sorted(
                summary["ranking_by_strength_ratio"],
                key=lambda item: item["strength_ratio"],
                reverse=True,
            ),
        )
        self.assertEqual(
            summary["strongest_planet"],
            summary["ranking_by_strength_ratio"][0],
        )
        self.assertEqual(
            summary["weakest_planet"],
            summary["ranking_by_strength_ratio"][-1],
        )
        self.assertEqual(summary["needs_attention"], summary["insufficient_planets"])
        self.assertEqual(len(shadbala["planets"]), 7)
        shadbala_planets = {planet["planet"] for planet in shadbala["planets"]}
        self.assertEqual(
            shadbala_planets,
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
        )
        for planet in shadbala["planets"]:
            self.assertEqual(planet["status"], "assessed_professional_total_v1")
            self.assertIn(planet["grade"], {"weak", "moderate", "strong"})
            self.assertGreaterEqual(planet["total_score"], 0)
            professional_total = planet["professional_total"]
            self.assertEqual(professional_total["unit"], "rupa")
            self.assertAlmostEqual(
                professional_total["total_rupa"],
                round(professional_total["total_virupa"] / 60.0, 4),
                places=4,
            )
            self.assertAlmostEqual(
                professional_total["required_virupa"],
                professional_total["required_rupa"] * 60.0,
                places=2,
            )
            self.assertIn(
                professional_total["grade"],
                {"below_required", "borderline", "meets_required", "strong"},
            )
            self.assertIn(
                professional_total["professional_status"],
                {"insufficient", "near_minimum", "sufficient"},
            )
            self.assertAlmostEqual(
                professional_total["difference_virupa"],
                round(
                    professional_total["total_virupa"]
                    - professional_total["required_virupa"],
                    2,
                ),
                places=2,
            )
            self.assertAlmostEqual(
                professional_total["difference_rupa"],
                round(professional_total["difference_virupa"] / 60.0, 4),
                places=4,
            )
            if professional_total["meets_required_strength"]:
                self.assertEqual(professional_total["deficit_virupa"], 0.0)
                self.assertEqual(professional_total["deficit_rupa"], 0.0)
                self.assertGreaterEqual(professional_total["excess_virupa"], 0.0)
                self.assertGreaterEqual(professional_total["excess_rupa"], 0.0)
            else:
                self.assertEqual(professional_total["excess_virupa"], 0.0)
                self.assertEqual(professional_total["excess_rupa"], 0.0)
                self.assertGreaterEqual(professional_total["deficit_virupa"], 0.0)
                self.assertGreaterEqual(professional_total["deficit_rupa"], 0.0)
            self.assertEqual(
                set(professional_total["component_totals_virupa"].keys()),
                {
                    "sthana_bala",
                    "dig_bala",
                    "cheshta_bala",
                    "kala_bala",
                    "drik_bala",
                    "naisargika_bala",
                    "yuddha_bala_adjustment",
                },
            )
            component_summary = professional_total["component_breakdown_summary"]
            self.assertEqual(component_summary["component_count"], 7)
            self.assertIn(
                component_summary["strongest_component"],
                professional_total["component_totals_virupa"],
            )
            self.assertIn(
                component_summary["weakest_component"],
                professional_total["component_totals_virupa"],
            )
            self.assertEqual(
                set(planet["components"].keys()),
                {
                    "sthana_bala",
                    "dig_bala",
                    "cheshta_bala",
                    "kala_bala",
                    "drik_bala",
                    "yuddha_bala",
                    "naisargika_bala",
                },
            )
            for component in planet["components"].values():
                self.assertGreaterEqual(component["score"], 0)
                self.assertLessEqual(component["score"], 60)
            dig_bala = planet["components"]["dig_bala"]
            self.assertIn("method", dig_bala)
            self.assertIn("source_rule", dig_bala)
            self.assertIn("assumptions", dig_bala)
            self.assertIn("excluded_rules", dig_bala)
            self.assertIn("unit", dig_bala)
            self.assertIn("strongest_house", dig_bala)
            self.assertIn("weakest_house", dig_bala)
            self.assertIn("current_house", dig_bala)
            self.assertGreaterEqual(dig_bala["house_distance"], 0)
            self.assertLessEqual(dig_bala["house_distance"], 6)
            cheshta_bala = planet["components"]["cheshta_bala"]
            self.assertIn("method", cheshta_bala)
            self.assertIn("source_rule", cheshta_bala)
            self.assertIn("assumptions", cheshta_bala)
            self.assertIn("excluded_rules", cheshta_bala)
            self.assertIn("unit", cheshta_bala)
            self.assertIn("speed", cheshta_bala)
            self.assertIn("absolute_speed", cheshta_bala)
            self.assertIn("speed_status", cheshta_bala)
            self.assertIn("retrograde", cheshta_bala)
            self.assertIn(
                cheshta_bala["motion_class"],
                {
                    "vikala",
                    "mandatara",
                    "manda",
                    "sama",
                    "chara",
                    "atichara",
                    "anuvakra",
                    "vakra",
                },
            )
            self.assertIn("mean_daily_speed", cheshta_bala)
            self.assertIn("normalized_speed_ratio", cheshta_bala)
            self.assertEqual(
                cheshta_bala["class_score"],
                CHESHTA_CLASS_SCORES[cheshta_bala["motion_class"]],
            )
            naisargika_bala = planet["components"]["naisargika_bala"]
            self.assertIn("method", naisargika_bala)
            self.assertIn("source_rule", naisargika_bala)
            self.assertIn("assumptions", naisargika_bala)
            self.assertIn("excluded_rules", naisargika_bala)
            self.assertEqual(naisargika_bala["unit"], "virupa")
            self.assertGreaterEqual(naisargika_bala["rank"], 1)
            self.assertLessEqual(naisargika_bala["rank"], 7)
            self.assertGreater(naisargika_bala["relative_ratio"], 0)
            self.assertLessEqual(naisargika_bala["relative_ratio"], 1)
            self.assertEqual(
                naisargika_bala["order"],
                ["Sun", "Moon", "Venus", "Jupiter", "Mercury", "Mars", "Saturn"],
            )
            kala_bala = planet["components"]["kala_bala"]
            self.assertIn("method", kala_bala)
            self.assertIn("source_rule", kala_bala)
            self.assertIn("assumptions", kala_bala)
            self.assertIn("excluded_rules", kala_bala)
            self.assertEqual(kala_bala["unit"], "scaled_virupa")
            self.assertEqual(
                set(kala_bala["components"].keys()),
                {
                    "paksha_bala",
                    "tribhaga_bala",
                    "vara_bala",
                    "hora_bala",
                    "masa_bala",
                    "abda_bala",
                    "natonnata_bala",
                    "ayana_bala",
                },
            )
            for component_name, detail in kala_bala["components"].items():
                self.assertIn("method", detail)
                self.assertIn("source_rule", detail)
                self.assertIn("assumptions", detail)
                self.assertIn("excluded_rules", detail)
                self.assertIn("unit", detail)
                self.assertGreaterEqual(detail["score"], 0)
                maximum = (
                    120
                    if component_name == "paksha_bala"
                    and planet["planet"] == "Moon"
                    else 60
                )
                self.assertLessEqual(detail["score"], maximum)
            paksha_bala = kala_bala["components"]["paksha_bala"]
            self.assertEqual(
                paksha_bala["score"],
                paksha_bala["final_virupa"],
            )
            self.assertEqual(
                paksha_bala["final_virupa"],
                round(
                    paksha_bala["base_score"]
                    * paksha_bala["multiplier"],
                    2,
                ),
            )
            self.assertEqual(
                paksha_bala["multiplier"],
                2.0 if planet["planet"] == "Moon" else 1.0,
            )
            vara_bala = kala_bala["components"]["vara_bala"]
            hora_bala = kala_bala["components"]["hora_bala"]
            self.assertIn(vara_bala["score"], {0.0, 45.0})
            self.assertIsNotNone(vara_bala["planetary_day_start_jd"])
            self.assertEqual(vara_bala["vara_lord"], hora_bala["day_lord"])
            natonnata_bala = kala_bala["components"]["natonnata_bala"]
            self.assertIn(
                natonnata_bala["sect"],
                {"day", "night", "both"},
            )
            self.assertIn("previous_anchor", natonnata_bala)
            self.assertIn("next_anchor", natonnata_bala)
            self.assertIn("elapsed_ratio", natonnata_bala)
            self.assertAlmostEqual(
                natonnata_bala["day_strength_virupa"]
                + natonnata_bala["night_strength_virupa"],
                60.0,
                places=2,
            )
            if planet["planet"] == "Mercury":
                self.assertEqual(natonnata_bala["score"], 60.0)
            ayana_bala = kala_bala["components"]["ayana_bala"]
            self.assertEqual(ayana_bala["unit"], "scaled_virupa")
            self.assertIn(ayana_bala["hemisphere"], {"north", "south"})
            self.assertIn(ayana_bala["preferred_hemisphere"], {"north", "south", "both"})
            self.assertGreaterEqual(ayana_bala["declination"], -30)
            self.assertLessEqual(ayana_bala["declination"], 30)
            self.assertGreaterEqual(ayana_bala["ratio"], 0)
            self.assertLessEqual(ayana_bala["ratio"], 1)
            drik_bala = planet["components"]["drik_bala"]
            self.assertIn("method", drik_bala)
            self.assertIn("source_rule", drik_bala)
            self.assertIn("assumptions", drik_bala)
            self.assertIn("excluded_rules", drik_bala)
            self.assertEqual(drik_bala["unit"], "scaled_virupa")
            self.assertIn("neutral_baseline", drik_bala)
            self.assertIn("benefic_points", drik_bala)
            self.assertIn("malefic_points", drik_bala)
            self.assertIn("net_points", drik_bala)
            self.assertIn("benefic_aspect_virupa", drik_bala)
            self.assertIn("malefic_aspect_virupa", drik_bala)
            self.assertIn("classical_net_virupa", drik_bala)
            self.assertEqual(drik_bala["net_points"], drik_bala["classical_net_virupa"])
            self.assertAlmostEqual(
                drik_bala["benefic_points"],
                round(drik_bala["benefic_aspect_virupa"] / 4.0, 2),
                places=2,
            )
            self.assertAlmostEqual(
                drik_bala["malefic_points"],
                round(drik_bala["malefic_aspect_virupa"] / 4.0, 2),
                places=2,
            )
            self.assertEqual(drik_bala["aspect_count"], len(drik_bala["aspects"]))
            for aspect in drik_bala["aspects"]:
                self.assertIn(aspect["nature"], {"benefic", "malefic", "neutral"})
                self.assertIn("from", aspect)
                self.assertIn("from_longitude", aspect)
                self.assertIn("to_longitude", aspect)
                self.assertIn("directed_angle", aspect)
                self.assertIn("aspect_virupa", aspect)
                self.assertGreater(aspect["aspect_virupa"], 0)
                self.assertLessEqual(aspect["aspect_virupa"], 60)
                self.assertIn("contribution", aspect)
            yuddha_bala = planet["components"]["yuddha_bala"]
            self.assertIn("method", yuddha_bala)
            self.assertIn("source_rule", yuddha_bala)
            self.assertIn("assumptions", yuddha_bala)
            self.assertIn("excluded_rules", yuddha_bala)
            self.assertEqual(yuddha_bala["unit"], "modifier_virupa")
            self.assertIn("score_adjustment", yuddha_bala)
            self.assertIn("penalty", yuddha_bala)
            self.assertIn("severity", yuddha_bala)
            self.assertIn(
                yuddha_bala["severity"],
                {"not_applicable", "none", "mild", "moderate", "severe"},
            )
            self.assertLessEqual(yuddha_bala["score_adjustment"], 0)
            self.assertGreaterEqual(yuddha_bala["penalty"], 0)
            sthana_bala = planet["components"]["sthana_bala"]
            self.assertIn("method", sthana_bala)
            self.assertIn("source_rule", sthana_bala)
            self.assertIn("assumptions", sthana_bala)
            self.assertIn("excluded_rules", sthana_bala)
            self.assertEqual(
                set(sthana_bala["components"].keys()),
                {
                    "uccha_bala",
                    "saptavargaja_bala",
                    "ojayugma_bala",
                    "kendradi_bala",
                    "drekkana_bala",
                },
            )
            for detail in sthana_bala["components"].values():
                self.assertIn("method", detail)
                self.assertIn("source_rule", detail)
                self.assertIn("assumptions", detail)
                self.assertIn("excluded_rules", detail)
                self.assertIn("unit", detail)
                self.assertGreaterEqual(detail["score"], 0)
            ojayugma = sthana_bala["components"]["ojayugma_bala"]
            self.assertEqual(ojayugma["divisions_used"], ["D1", "D9"])
            self.assertEqual(len(ojayugma["rows"]), 2)
            self.assertIn(ojayugma["score"], {0.0, 15.0, 30.0})
            self.assertEqual(
                ojayugma["score"],
                sum(row["score"] for row in ojayugma["rows"]),
            )
            saptavargaja = sthana_bala["components"]["saptavargaja_bala"]
            self.assertEqual(
                saptavargaja["divisions_used"],
                SAPTAVARGA_DIVISIONS,
            )
            self.assertEqual(len(saptavargaja["rows"]), 7)
            self.assertEqual(
                saptavargaja["classical_total_virupa"],
                saptavargaja["raw_total"],
            )
            for row in saptavargaja["rows"]:
                self.assertIn(
                    row["score"],
                    {1.875, 3.75, 7.5, 15.0, 22.5, 30.0, 45.0},
                )
                self.assertIn("natural_relationship", row)
                self.assertIn("temporary_relationship", row)
                self.assertIn("compound_relationship", row)
                self.assertIn("relative_sign_offset", row)
        self.assertIn("temporary_friendship", data)
        self.assertIn("compound_friendship", data)
        self.assertIn("Sun", data["temporary_friendship"]["matrix"])
        self.assertIn("Moon", data["temporary_friendship"]["matrix"]["Sun"])
        self.assertIn(
            data["temporary_friendship"]["matrix"]["Sun"]["Moon"]["relationship"],
            {"friend", "enemy"},
        )
        self.assertIn("Sun", data["compound_friendship"]["matrix"])
        self.assertIn("Moon", data["compound_friendship"]["matrix"]["Sun"])
        self.assertIn(
            data["compound_friendship"]["matrix"]["Sun"]["Moon"]["relationship"],
            {"great_friend", "friend", "neutral", "enemy", "great_enemy", "unknown"},
        )
        self.assertEqual(len(data["temporary_friendship"]["pairs"]), 72)
        self.assertEqual(len(data["compound_friendship"]["pairs"]), 72)
        self.assertEqual(data["data_quality"]["house_interpretation_confidence"], "high")
        self.assertIn("D4", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D6", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D7", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D10", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D11", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D12", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D20", data["data_quality"]["varga_interpretation_confidence"])
        self.assertIn("D24", data["data_quality"]["varga_interpretation_confidence"])
        self.assertEqual(data["data_quality"]["person_verified_vargas"], [])
        self.assertEqual(
            data["vargas"]["D2"]["external_validation"]["status"],
            "customer_time_declaration_policy",
        )
        self.assertEqual(
            data["vargas"]["D4"]["external_validation"]["status"],
            "customer_time_declaration_policy",
        )
        self.assertEqual(data["data_quality"]["varga_interpretation_confidence"]["D30"], "high")
        self.assertEqual(data["data_quality"]["varga_interpretation_confidence"]["D60"], "high")
        self.assertNotIn("houses", data["birth_time_policy"]["low_confidence_interpretations"])
        self.assertNotIn("D60", data["birth_time_policy"]["low_confidence_interpretations"])
        self.assertNotIn("panchanga", missing_keys)
        panchanga = data["panchanga"]
        for key in [
            "reference",
            "cartography_seed",
            "planetary_positions",
            "tithi",
            "paksha",
            "vara",
            "yoga",
            "karana",
            "moon_nakshatra",
        ]:
            self.assertIn(key, panchanga)
        self.assertEqual(panchanga["method"], "sidereal_lahiri_local_birth_time")
        self.assertEqual(panchanga["reference"]["date"], "1978-05-28")
        self.assertEqual(panchanga["reference"]["time"], "00:15:00")
        self.assertEqual(panchanga["reference"]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(panchanga["reference"]["tz_offset"], 3.0)
        self.assertEqual(panchanga["reference"]["latitude"], 40.7654)
        self.assertEqual(panchanga["reference"]["longitude_geo"], 29.9408)
        self.assertIn("utc_datetime", panchanga["reference"])
        self.assertIn("julian_day", panchanga["reference"])
        self.assertEqual(panchanga["cartography_seed"]["status"], "ready")
        self.assertIn(
            "reference.utc_datetime",
            panchanga["cartography_seed"]["requires_for_astrocartography"],
        )
        self.assertIn(
            "planet_angular_lines",
            panchanga["cartography_seed"]["missing_layers"],
        )
        self.assertGreaterEqual(len(panchanga["planetary_positions"]), 9)
        self.assertIn(
            "Sun",
            {position["planet"] for position in panchanga["planetary_positions"]},
        )
        self.assertEqual(panchanga["vara"]["name"], "Sunday")
        self.assertEqual(panchanga["vara"]["sanskrit"], "Ravivara")
        self.assertEqual(panchanga["vara"]["weekday_index"], 6)
        self.assertEqual(panchanga["moon_nakshatra"]["name"], "Dhanishta")
        self.assertEqual(panchanga["moon_nakshatra"]["lord"], "Mars")
        self.assertEqual(panchanga["moon_nakshatra"]["pada"], 1)
        self.assertEqual(panchanga["tithi"]["number"], 22)
        self.assertEqual(panchanga["tithi"]["name"], "Saptami")
        self.assertEqual(panchanga["tithi"]["paksha_tithi"], 7)
        self.assertEqual(panchanga["paksha"]["name"], "Krishna")
        self.assertEqual(panchanga["paksha"]["phase"], "waning")
        self.assertEqual(panchanga["yoga"]["number"], 26)
        self.assertEqual(panchanga["yoga"]["name"], "Indra")
        self.assertEqual(panchanga["karana"]["number"], 43)
        self.assertEqual(panchanga["karana"]["name"], "Vishti")
        self.assertGreaterEqual(panchanga["tithi"]["elapsed_degrees"], 0)
        self.assertGreater(panchanga["tithi"]["remaining_degrees"], 0)
        self.assertGreaterEqual(panchanga["karana"]["elapsed_degrees"], 0)
        self.assertGreater(panchanga["karana"]["remaining_degrees"], 0)
        self.assertNotIn("special_lagnas", missing_keys)
        special_lagnas = data["special_lagnas"]
        self.assertEqual(
            set(special_lagnas.keys()),
            {
                "chandra_lagna",
                "surya_lagna",
                "hora_lagna",
                "ghati_lagna",
                "bhava_lagna",
                "indu_lagna",
            },
        )
        expected_special_lagna_keys = {
            "name",
            "sign_index",
            "sign",
            "sign_tr",
            "degree",
            "degree_str",
            "source",
            "confidence",
        }
        for special_lagna in special_lagnas.values():
            self.assertEqual(set(special_lagna.keys()), expected_special_lagna_keys)
            self.assertGreaterEqual(special_lagna["sign_index"], 0)
            self.assertLessEqual(special_lagna["sign_index"], 11)
            self.assertGreaterEqual(special_lagna["degree"], 0)
            self.assertLess(special_lagna["degree"], 30)
            self.assertIn(special_lagna["confidence"], {"low", "medium", "high"})
            self.assertTrue(special_lagna["source"])
        planets_by_name = {planet["name"]: planet for planet in data["planets"]}
        self.assertEqual(
            special_lagnas["chandra_lagna"]["sign_index"],
            planets_by_name["Moon"]["sign_index"],
        )
        self.assertAlmostEqual(
            special_lagnas["chandra_lagna"]["degree"],
            planets_by_name["Moon"]["degree"],
        )
        self.assertEqual(special_lagnas["chandra_lagna"]["confidence"], "high")
        self.assertEqual(
            special_lagnas["surya_lagna"]["sign_index"],
            planets_by_name["Sun"]["sign_index"],
        )
        self.assertAlmostEqual(
            special_lagnas["surya_lagna"]["degree"],
            planets_by_name["Sun"]["degree"],
        )
        self.assertEqual(special_lagnas["surya_lagna"]["confidence"], "high")
        for key in ["hora_lagna", "ghati_lagna", "bhava_lagna", "indu_lagna"]:
            self.assertEqual(special_lagnas[key]["confidence"], "low")
            self.assertIn("starter", special_lagnas[key]["source"])
        self.assertNotIn("sensitive_points", missing_keys)
        self.assertNotIn("sensitive_points.pranapada", missing_keys)
        sensitive_points = data["sensitive_points"]
        self.assertEqual(
            set(sensitive_points.keys()),
            {"gulika", "mandi", "yamakantaka", "kala", "mrityu", "pranapada"},
        )
        expected_sensitive_point_keys = {
            "name",
            "sign_index",
            "sign",
            "sign_tr",
            "degree",
            "degree_str",
            "house",
            "source",
            "confidence",
        }
        for key in ["gulika", "mandi", "yamakantaka", "kala", "mrityu"]:
            point = sensitive_points[key]
            self.assertEqual(set(point.keys()), expected_sensitive_point_keys)
            self.assertGreaterEqual(point["sign_index"], 0)
            self.assertLessEqual(point["sign_index"], 11)
            self.assertGreaterEqual(point["degree"], 0)
            self.assertLess(point["degree"], 30)
            self.assertGreaterEqual(point["house"], 1)
            self.assertLessEqual(point["house"], 12)
            self.assertEqual(point["confidence"], "low")
            self.assertIn("starter_method", point["source"])
            self.assertIn("method_needs_classical_validation", point["source"])
        self.assertEqual(sensitive_points["gulika"]["sign_index"], sensitive_points["mandi"]["sign_index"])
        self.assertAlmostEqual(sensitive_points["gulika"]["degree"], sensitive_points["mandi"]["degree"])
        pranapada = sensitive_points["pranapada"]
        self.assertEqual(set(pranapada.keys()), expected_sensitive_point_keys)
        self.assertGreaterEqual(pranapada["sign_index"], 0)
        self.assertLessEqual(pranapada["sign_index"], 11)
        self.assertGreaterEqual(pranapada["house"], 1)
        self.assertLessEqual(pranapada["house"], 12)
        self.assertEqual(pranapada["confidence"], "low")
        self.assertIn("starter_solar_elapsed_arc", pranapada["source"])
        self.assertIn("classical_method_needs_validation", pranapada["source"])
        self.assertNotIn("sensitive_points.pranapada", missing_keys)
        self.assertNotIn("yogas", missing_keys)
        self.assertIn("matches", data["yogas"])
        self.assertIn("missing_checks", data["yogas"])
        self.assertEqual(data["yogas"]["missing_checks"], [])
        yoga_matches = data["yogas"]["matches"]
        self.assertGreater(len(yoga_matches), 0)
        expected_yoga_keys = {
            "id",
            "name",
            "source",
            "rule",
            "topic",
            "effect_type",
            "strength",
            "confidence",
            "requires",
            "supporting_factors",
            "challenging_factors",
            "cancellation_factors",
        }
        for match in yoga_matches:
            self.assertEqual(set(match.keys()), expected_yoga_keys)
            self.assertIsInstance(match["requires"], list)
            self.assertIsInstance(match["supporting_factors"], list)
            self.assertIsInstance(match["challenging_factors"], list)
            self.assertIsInstance(match["cancellation_factors"], list)
            self.assertIn(match["source"], {"starter_rule"})
            self.assertIn(match["effect_type"], {"supportive", "challenging", "mixed"})
            self.assertIn(match["strength"], {"weak", "medium", "strong"})
            self.assertIn(match["confidence"], {"low", "medium", "high"})
        yoga_ids = {match["id"] for match in yoga_matches}
        self.assertIn("neecha_bhanga_mars", yoga_ids)
        self.assertIn("viparita_rajayoga_lord_12", yoga_ids)
        self.assertIn("rajayoga_k10_t5", yoga_ids)
        neecha_bhanga = next(match for match in yoga_matches if match["id"] == "neecha_bhanga_mars")
        self.assertEqual(neecha_bhanga["name"], "Neecha Bhanga")
        self.assertEqual(neecha_bhanga["effect_type"], "mixed")
        self.assertGreater(len(neecha_bhanga["cancellation_factors"]), 0)
        self.assertIn("doshas", data)
        self.assertEqual(set(data["doshas"].keys()), {"kala_sarpa", "mangala"})
        kala_sarpa = data["doshas"]["kala_sarpa"]
        self.assertEqual(kala_sarpa["status"], "assessed")
        self.assertEqual(kala_sarpa["confidence"], "medium")
        self.assertIn("method", kala_sarpa)
        self.assertIn("source_rule", kala_sarpa)
        self.assertIn("assumptions", kala_sarpa)
        self.assertIn("excluded_rules", kala_sarpa)
        self.assertIn(kala_sarpa["is_present"], {True, False})
        self.assertIn(kala_sarpa["strength"], {"none", "medium", "strong"})
        self.assertGreaterEqual(kala_sarpa["containment_ratio"], 0)
        self.assertLessEqual(kala_sarpa["containment_ratio"], 1)
        self.assertIn("rahu", kala_sarpa["axis"])
        self.assertIn("ketu", kala_sarpa["axis"])
        if kala_sarpa["is_present"]:
            self.assertIn(kala_sarpa["direction"], {"rahu_to_ketu", "ketu_to_rahu"})
            self.assertIsNotNone(kala_sarpa["subtype"])
            self.assertEqual(len(kala_sarpa["contained_planets"]), 7)
            self.assertEqual(kala_sarpa["planets_outside_axis"], [])
        else:
            self.assertEqual(kala_sarpa["direction"], None)
            self.assertIsNone(kala_sarpa["subtype"])
            self.assertGreater(len(kala_sarpa["planets_outside_axis"]), 0)
        self.assertIn("boundary_contacts", kala_sarpa)
        self.assertIn("cancellation_factors", kala_sarpa)
        mangala = data["doshas"]["mangala"]
        self.assertEqual(mangala["status"], "assessed")
        self.assertEqual(mangala["confidence"], "medium")
        self.assertIn("method", mangala)
        self.assertIn("source_rule", mangala)
        self.assertIn("assumptions", mangala)
        self.assertIn("excluded_rules", mangala)
        self.assertIn(mangala["severity"], {"none", "low", "medium", "high"})
        self.assertIn(mangala["net_severity"], {"none", "low", "medium", "high"})
        self.assertEqual(len(mangala["checks"]), 3)
        self.assertEqual(
            {check["source"] for check in mangala["checks"]},
            {"lagna", "moon", "venus"},
        )
        self.assertEqual(mangala["is_present"], bool(mangala["triggered_sources"]))
        for check in mangala["checks"]:
            self.assertGreaterEqual(check["mars_house_from_source"], 1)
            self.assertLessEqual(check["mars_house_from_source"], 12)
            self.assertIn(check["is_triggered"], {True, False})
        self.assertIn("cancellation_factors", mangala)
        for factor in mangala["cancellation_factors"]:
            self.assertIn("rule", factor)
            self.assertIn("is_active", factor)
            self.assertIn("effect", factor)
            self.assertIn("source", factor)
        self.assertEqual(mangala["mars"]["sign"], planets_by_name["Mars"]["sign"])
        self.assertEqual(mangala["mars"]["house"], planets_by_name["Mars"]["house"])
        self.assertNotIn("transits", missing_keys)
        transits = data["transits"]
        self.assertEqual(transits["status"], "implemented_current_snapshot_with_dasha_cross_reference")
        self.assertEqual(transits["confidence"], "medium")
        self.assertIn("source_rule", transits)
        self.assertIn("assumptions", transits)
        self.assertIn("excluded_rules", transits)
        self.assertEqual(transits["reference_mode"], "current")
        self.assertIn("reference_datetime_utc", transits)
        self.assertIsNone(transits["requested_date"])
        self.assertIsNone(transits["requested_time"])
        self.assertEqual(
            transits["reference"]["natal_lagna_sign"],
            data["lagna"]["sign"],
        )
        self.assertEqual(len(transits["planets"]), 9)
        transit_names = {planet["name"] for planet in transits["planets"]}
        self.assertEqual(
            transit_names,
            {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu (True)", "Ketu"},
        )
        expected_transit_keys = {
            "id",
            "name",
            "abbr",
            "longitude",
            "sign_index",
            "sign",
            "sign_tr",
            "degree",
            "degree_str",
            "nakshatra",
            "motion",
            "house_from_natal_lagna",
            "house_from_natal_moon",
            "natal_planets_in_sign",
        }
        for transit_planet in transits["planets"]:
            self.assertEqual(set(transit_planet.keys()), expected_transit_keys)
            self.assertGreaterEqual(transit_planet["sign_index"], 0)
            self.assertLessEqual(transit_planet["sign_index"], 11)
            self.assertGreaterEqual(transit_planet["house_from_natal_lagna"], 1)
            self.assertLessEqual(transit_planet["house_from_natal_lagna"], 12)
            self.assertGreaterEqual(transit_planet["house_from_natal_moon"], 1)
            self.assertLessEqual(transit_planet["house_from_natal_moon"], 12)
        self.assertIn("special_checks", transits)
        self.assertEqual(
            set(transits["special_checks"].keys()),
            {"saturn", "jupiter", "nodes"},
        )
        saturn_checks = transits["special_checks"]["saturn"]
        self.assertEqual(
            set(saturn_checks.keys()),
            {"sade_sati", "ashtama_shani", "kantaka_shani", "from_lagna"},
        )
        self.assertIn(saturn_checks["sade_sati"]["is_active"], {True, False})
        self.assertIn(saturn_checks["ashtama_shani"]["is_active"], {True, False})
        self.assertIn(saturn_checks["kantaka_shani"]["is_active"], {True, False})
        self.assertIn(
            transits["special_checks"]["jupiter"]["from_moon"]["traditionally_supportive"],
            {True, False},
        )
        self.assertEqual(
            set(transits["special_checks"]["nodes"].keys()),
            {"from_moon", "from_lagna"},
        )
        self.assertIn("natal_contacts", transits)
        for contact in transits["natal_contacts"]:
            self.assertEqual(
                set(contact.keys()),
                {
                    "transit_planet",
                    "natal_planet",
                    "contact_type",
                    "orb",
                    "orb_limit",
                    "sign",
                    "transit_degree_str",
                    "natal_degree_str",
                    "house_from_lagna",
                    "house_from_moon",
                },
            )
            self.assertIn(contact["contact_type"], {"degree_orb", "same_sign"})
            self.assertGreaterEqual(contact["orb"], 0)
            self.assertLessEqual(contact["orb"], 180)
        self.assertIn("dasha_cross_reference", transits)
        dasha_cross_reference = transits["dasha_cross_reference"]
        self.assertEqual(
            dasha_cross_reference["status"],
            "implemented_current_dasha_transit_cross_reference",
        )
        self.assertIn("method", dasha_cross_reference)
        self.assertIn("source_rule", dasha_cross_reference)
        self.assertIn("assumptions", dasha_cross_reference)
        self.assertIn("excluded_rules", dasha_cross_reference)
        self.assertEqual(dasha_cross_reference["active_path"], current_active["path"])
        self.assertGreater(len(dasha_cross_reference["rows"]), 0)
        for row in dasha_cross_reference["rows"]:
            self.assertIn(row["level"], {"maha", "antara", "pratyantar", "sookshma", "prana"})
            self.assertIn("lord", row)
            self.assertIn("transit", row)
            self.assertIn("natal", row)
            self.assertIn("contacts_as_transit", row)
            self.assertIn("contacts_to_natal_lord", row)
        self.assertNotIn("topic_packets", missing_keys)
        self.assertEqual(
            set(data["topic_packets"].keys()),
            {"marriage", "career", "wealth", "health"},
        )
        expected_packet_keys = {
            "topic",
            "promise_level",
            "supporting_factors",
            "challenging_factors",
            "mixed_factors",
            "missing_factors",
            "required_but_missing",
            "confidence",
            "evidence",
        }
        for topic_key in ["marriage", "career", "wealth", "health"]:
            packet = data["topic_packets"][topic_key]
            self.assertEqual(set(packet.keys()), expected_packet_keys)
            self.assertEqual(packet["topic"], topic_key)
            self.assertIn(
                packet["promise_level"],
                {
                    "supported_by_evidence",
                    "challenged_by_evidence",
                    "mixed",
                    "insufficient_data",
                    "not_assessed",
                },
            )
            self.assertIn(packet["confidence"], {"low", "medium", "high"})
            self.assertIsInstance(packet["supporting_factors"], list)
            self.assertIsInstance(packet["challenging_factors"], list)
            self.assertIsInstance(packet["mixed_factors"], list)
            self.assertIsInstance(packet["missing_factors"], list)
            self.assertIsInstance(packet["required_but_missing"], list)
            self.assertEqual(packet["required_but_missing"], [])
            self.assertGreater(len(packet["evidence"]["houses"]), 0)
            self.assertGreater(len(packet["evidence"]["lordships"]), 0)
            self.assertGreater(len(packet["evidence"]["planets"]), 0)
            self.assertGreater(len(packet["evidence"]["vargas"]), 0)
            self.assertIn("active_dasha", packet["evidence"])
            self.assertEqual(
                packet["evidence"]["active_dasha"]["path"],
                current_active["path"],
            )
            self.assertEqual(
                packet["evidence"]["active_dasha"]["reference"],
                "current_active",
            )
            self.assertIn("yogas", packet["evidence"])
            self.assertIn("missing", packet["evidence"])
            for yoga_ref in packet["evidence"]["yogas"]:
                self.assertIn(yoga_ref["id"], yoga_ids)
                self.assertIn("name", yoga_ref)
                self.assertIn("effect_type", yoga_ref)
                self.assertIn("strength", yoga_ref)
                self.assertIn("confidence", yoga_ref)
            self.assertFalse(any(
                factor["code"] == "rashi_drishti_unavailable"
                for factor in packet["missing_factors"]
            ))
            self.assertFalse(any(
                factor["code"] == "classic_yogas_unavailable"
                for factor in packet["missing_factors"]
            ))
            self.assertTrue(
                packet["supporting_factors"]
                or packet["challenging_factors"]
                or packet["mixed_factors"]
                or packet["missing_factors"]
            )
        self.assertNotIn("kp", missing_keys)
        kp = data["kp"]
        self.assertEqual(kp["status"], "implemented_sub_sub_significators")
        self.assertIn(kp["confidence"], {"low", "medium"})
        self.assertEqual(len(kp["cusps"]), 12)
        self.assertEqual(len(kp["planets"]), 9)
        expected_kp_position_keys = {
            "longitude",
            "sign_index",
            "sign",
            "sign_tr",
            "degree",
            "degree_str",
            "house_from_lagna",
            "nakshatra",
            "nakshatra_lord",
            "pada",
            "sub_lord",
            "sub_sub_lord",
            "degree_in_nakshatra",
            "sub_lord_start_degree",
            "sub_lord_end_degree",
            "degree_in_sub_lord",
            "sub_sub_lord_start_degree",
            "sub_sub_lord_end_degree",
        }
        for cusp in kp["cusps"]:
            self.assertEqual(set(cusp.keys()), expected_kp_position_keys | {"house"})
            self.assertGreaterEqual(cusp["house"], 1)
            self.assertLessEqual(cusp["house"], 12)
            self.assertIn(cusp["sub_lord"], {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"})
            self.assertIn(cusp["sub_sub_lord"], {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"})
            self.assertGreaterEqual(cusp["degree_in_sub_lord"], 0)
            self.assertLessEqual(cusp["sub_sub_lord_start_degree"], cusp["sub_sub_lord_end_degree"])
        for planet in kp["planets"]:
            self.assertEqual(set(planet.keys()), expected_kp_position_keys | {"planet", "planet_id"})
            self.assertIn(planet["sub_lord"], {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"})
            self.assertIn(planet["sub_sub_lord"], {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"})
        self.assertIn("significators", kp)
        significators = kp["significators"]
        self.assertIn("method", significators)
        self.assertIn("source_rule", significators)
        self.assertIn("assumptions", significators)
        self.assertIn("excluded_rules", significators)
        self.assertEqual(len(significators["planet_significators"]), 9)
        self.assertEqual(set(significators["house_significators"].keys()), {str(house) for house in range(1, 13)})
        for planet in significators["planet_significators"]:
            self.assertIn("planet", planet)
            self.assertIn("star_lord", planet)
            self.assertIn("sub_lord", planet)
            self.assertIn("sub_sub_lord", planet)
            self.assertIn("occupied_house", planet)
            self.assertIn("owned_houses", planet)
            self.assertIn("sub_sub_lord_occupied_house", planet)
            self.assertIn("sub_sub_lord_owned_houses", planet)
            self.assertIn("ranked_houses", planet)
            for house_score in planet["ranked_houses"]:
                self.assertGreaterEqual(house_score["house"], 1)
                self.assertLessEqual(house_score["house"], 12)
                self.assertGreater(house_score["score"], 0)
                self.assertIsInstance(house_score["sources"], list)
        for rows in significators["house_significators"].values():
            for row in rows:
                self.assertIn("planet", row)
                self.assertIn("score", row)
                self.assertIn("sources", row)
        self.assertIn("ruling_planets", kp)
        ruling_planets = kp["ruling_planets"]
        self.assertIn("method", ruling_planets)
        self.assertIn("source_rule", ruling_planets)
        self.assertIn("assumptions", ruling_planets)
        self.assertIn("excluded_rules", ruling_planets)
        self.assertEqual(
            {entry["role"] for entry in ruling_planets["entries"]},
            {
                "day_lord",
                "moon_sign_lord",
                "moon_star_lord",
                "lagna_sign_lord",
                "lagna_star_lord",
                "lagna_sub_lord",
            },
        )
        self.assertGreater(len(ruling_planets["unique_planets"]), 0)
        self.assertEqual(data["missing"], [])

    def test_full_chart_accepts_coordinate_directions_for_west_longitude(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "donald-trump", "name": "Donald Trump", "group": "Public-Figures"},
                "birth": {
                    "year": 1946,
                    "month": 6,
                    "day": 14,
                    "hour": 10,
                    "minute": 54,
                    "timezone_id": "America/New_York",
                    "lat": 40.7128,
                    "lat_direction": "N",
                    "lon": 74.006,
                    "lon_direction": "W",
                    "place": "New York City, United States",
                    "time_confidence": "known",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["birth"]["latitude"], 40.7128)
        self.assertEqual(data["birth"]["longitude_geo"], -74.006)
        self.assertEqual(data["birth"]["timezone_id"], "America/New_York")
        self.assertEqual(data["panchanga"]["reference"]["longitude_geo"], -74.006)

    def test_missing_birth_place_is_resolved_without_none_label(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": None,
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["birth"]["place"], "İzmit, Kocaeli, Türkiye")
        self.assertNotIn("- Yer: None", data["copy_packages"]["expert"]["markdown"])

        parsed = _parse_vault_natal_birth(
            "\n".join([
                'person: "Kisi"',
                'group: "Grup-01"',
                'birth_date: "28.05.1978"',
                'birth_time: "00:15:00"',
                'timezone: "Europe/Istanbul"',
                "- Koordinatlar: 40.7654, 29.9408",
                "- Yer: None",
                "- Zaman güveni: yüksek",
            ])
        )
        self.assertEqual(parsed["birth"]["place"], "İzmit, Kocaeli, Türkiye")

        unknown_place_response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.6565,
                    "lon": 29.9,
                    "place": None,
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )
        self.assertEqual(unknown_place_response.status_code, 200)
        unknown_place = unknown_place_response.get_json()
        self.assertEqual(unknown_place["birth"]["place"], "Belirtilmedi")
        self.assertNotIn("(koordinat)", unknown_place["copy_packages"]["expert"]["markdown"])

    def test_panchanga_can_use_separate_reference_moment_and_location(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                    "panchanga_reference": {
                        "date": "2026-05-31",
                        "time": "18:45",
                        "timezone_id": "Europe/Istanbul",
                        "lat": 39.9334,
                        "lon": 32.8597,
                        "place": "Ankara Merkez, Türkiye",
                    },
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        panchanga = data["panchanga"]
        self.assertEqual(data["birth"]["date"], "28.05.1978")
        self.assertEqual(panchanga["input_source"], "panchanga_reference")
        self.assertEqual(panchanga["method"], "sidereal_lahiri_local_reference_time")
        self.assertEqual(panchanga["reference"]["date"], "2026-05-31")
        self.assertEqual(panchanga["reference"]["time"], "18:45:00")
        self.assertEqual(panchanga["reference"]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(panchanga["reference"]["latitude"], 39.9334)
        self.assertEqual(panchanga["reference"]["longitude_geo"], 32.8597)
        self.assertEqual(panchanga["reference"]["place"], "Ankara Merkez, Türkiye")
        self.assertEqual(panchanga["cartography_seed"]["status"], "ready")
        self.assertIn("planetary_positions", panchanga["cartography_seed"]["available_layers"])

    def test_transit_pack_panchanga_can_use_api_reference_place(self):
        payload = self._sample_transit_pack_payload()
        payload.update({
            "period": "daily",
            "start_date": "2026-06-02",
            "save": False,
            "include_markdown": True,
            "panchanga_reference": {
                "time": "09:30",
                "timezone_id": "Europe/Istanbul",
                "lat": 39.9334,
                "lon": 32.8597,
                "place": "Ankara Merkez, Türkiye",
            },
        })

        response = self.client.post("/api/v2/transits/pack", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        reference = data["panchanga_reference"]
        self.assertEqual(reference["date"], "2026-06-02")
        self.assertEqual(reference["time"], "09:30:00")
        self.assertEqual(reference["timezone_id"], "Europe/Istanbul")
        self.assertEqual(reference["latitude"], 39.9334)
        self.assertEqual(reference["longitude_geo"], 32.8597)
        self.assertEqual(reference["place"], "Ankara Merkez, Türkiye")
        self.assertIn("- Panchanga referans yeri: Ankara Merkez, Türkiye", data["markdown"])

        pack = _build_transit_pack(payload)
        day_panchanga = pack["days"][0]["panchanga"]
        self.assertEqual(day_panchanga["input_source"], "transit_pack_panchanga_reference")
        self.assertEqual(day_panchanga["reference"]["place"], "Ankara Merkez, Türkiye")

    def test_transit_pack_supports_exact_date_range_and_190_day_limit(self):
        payload = self._sample_transit_pack_payload()
        payload.update({
            "period": "range",
            "start_date": "2027-01-26",
            "end_date": "2027-04-01",
            "save": False,
            "include_markdown": True,
        })

        response = self.client.post("/api/v2/transits/pack", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["period"]["type"], "range")
        self.assertEqual(data["period"]["range_start"], "2027-01-26")
        self.assertEqual(data["period"]["range_end"], "2027-04-01")
        self.assertEqual(data["day_count"], 66)
        self.assertIn(
            "Bu paket hazır bir en güçlü pencere sıralaması üretmez.",
            data["markdown"],
        )
        self.assertIn(
            "Burç, retro veya dasha değişim tarihlerini otomatik olarak pencere başlangıcı ya da bitişi sayma.",
            data["markdown"],
        )
        self.assertIn(
            "Özel tarih aralığı analizinde yalnız seçili aralığın günlük kayıtları kullanılır",
            data["markdown"],
        )
        self.assertIn(
            "Analize başlamadan önce bu dosyanın Dönem Özeti içindeki gerçek başlangıç ve bitiş tarihini açıkça yaz.",
            data["markdown"],
        )
        self.assertIn(
            "İstenen dönem dosya aralığından farklıysa yalnız ortak tarih aralığını analiz et",
            data["markdown"],
        )
        self.assertIn(
            "İstenen dönemle dosya aralığı kesişmiyorsa analizi durdur",
            data["markdown"],
        )
        self.assertEqual(
            len(_transit_pack_dates("range", date(2027, 1, 1), date(2027, 7, 9))),
            190,
        )

        too_long_payload = dict(payload)
        too_long_payload["start_date"] = "2027-01-01"
        too_long_payload["end_date"] = "2027-07-10"
        too_long_response = self.client.post(
            "/api/v2/transits/pack",
            json=too_long_payload,
        )
        self.assertEqual(too_long_response.status_code, 400)
        self.assertIn(
            "1-190 gün",
            too_long_response.get_json()["error"],
        )

        reversed_payload = dict(payload)
        reversed_payload["start_date"] = "2027-04-01"
        reversed_payload["end_date"] = "2027-01-26"
        reversed_response = self.client.post(
            "/api/v2/transits/pack",
            json=reversed_payload,
        )
        self.assertEqual(reversed_response.status_code, 400)
        self.assertIn(
            "başlangıç tarihinden önce",
            reversed_response.get_json()["error"],
        )

    def test_saved_range_transit_refreshes_all_analysis_packages(self):
        payload = self._sample_transit_pack_payload()
        payload.update({
            "period": "range",
            "start_date": "1995-05-25",
            "end_date": "1995-05-25",
            "save": True,
            "overwrite": True,
            "include_markdown": False,
        })
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                sync_result = {
                    "ok": True,
                    "status": "analysis_packages_refreshed",
                    "paths": {
                        "career": str(
                            Path(tmp_dir) / "Kariyer Analizi Veri Paketi.md"
                        ),
                        "health": str(
                            Path(tmp_dir) / "Sağlık Analizi Veri Paketi.md"
                        ),
                    },
                }
                with patch(
                    "app._refresh_analysis_packages_for_selected_transit",
                    return_value=sync_result,
                ) as sync_mock:
                    response = self.client.post(
                        "/api/v2/transits/pack",
                        json=payload,
                    )

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual(data["analysis_packages_sync"], sync_result)
                sync_mock.assert_called_once()
                synced_pack = sync_mock.call_args.args[0]
                self.assertEqual(synced_pack["period"]["type"], "range")
                self.assertEqual(
                    synced_pack["_source_path"],
                    data["paths"]["transit_pack"],
                )
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_dashboard_and_vault_save_forward_selected_transit_range(self):
        dashboard_response = self.client.get("/")
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard_html = dashboard_response.get_data(as_text=True)
        self.assertIn('id="transit-start-date"', dashboard_html)
        self.assertIn('id="transit-end-date"', dashboard_html)
        self.assertNotIn('id="transit-time"', dashboard_html)

        chart_js = (PROJECT_ROOT / "static" / "js" / "chart.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function selectedTransitRange()", chart_js)
        self.assertIn("transit_range: transitRange || undefined", chart_js)
        self.assertIn("transit_time: transitDate ? '12:00' : undefined", chart_js)

        chart = {
            "meta": {"api_version": "v2"},
            "birth": {},
            "life_period_analysis": {"status": "ready"},
        }
        transit_range = {
            "start_date": "2027-01-26",
            "end_date": "2027-04-01",
            "day_count": 66,
        }
        mocked_result = {
            "ok": True,
            "status": 200,
            "paths": {"person": "/tmp/Test Kisi.md"},
        }
        with patch("app._save_vault_files", return_value=mocked_result) as save_mock:
            response = self.client.post(
                "/api/v2/vault/save",
                json={
                    "chart": chart,
                    "person": {"name": "Test Kisi", "group": "Grup-99"},
                    "transit_range": transit_range,
                    "overwrite": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        save_mock.assert_called_once_with(
            chart,
            "Test Kisi",
            "Grup-99",
            overwrite=True,
            transit_range=transit_range,
            preserve_existing_analysis_profile=True,
        )

    def test_session_package_labels_selected_range_without_three_month_language(self):
        transit_pack = {
            "period": {
                "type": "range",
                "range_start": "1995-05-25",
                "range_end": "1995-11-23",
                "day_count": 183,
            },
            "days": [],
        }

        markdown = _build_session_preparation_package_markdown(
            {"birth": {}, "data_quality": {}},
            "Test Kisi",
            "Grup-99",
            transit_pack=transit_pack,
        )

        self.assertIn(
            "| Seçili transit aralığı | 1995-05-25 → 1995-11-23 |",
            markdown,
        )
        self.assertIn(
            "## Seçili Transit Aralığı Teknik Değişim Noktaları",
            markdown,
        )
        self.assertIn(
            "Burç, retro veya dasha değişim tarihleri tek başına yoğunlaşma ya da kariyer penceresi sıralaması değildir.",
            markdown,
        )
        self.assertIn(
            "Konu paketindeki aday dönem ile transit dosyasının tarih aralığı farklıysa önce ortak tarih aralığını ve kapsanmayan günleri açıkça belirt.",
            markdown,
        )
        self.assertIn(
            "Transit dosyasının kapsamadığı tarihler için transit kanıtı varmış gibi konuşma.",
            markdown,
        )
        self.assertNotIn("Önümüzdeki 90 Gün", markdown)

    def test_session_package_does_not_overclaim_weak_rectification_record(self):
        chart = {
            "birth": {
                "date": "1979-04-28",
                "time": "01:52:00",
                "place": "Istanbul",
                "time_confidence": "rectified",
                "time_confidence_label": "rektifiye",
                "rectification_status": "yapıldı",
            },
            "data_quality": {},
        }
        rectification_record = {
            "birth_window": {"source_quality": "silver"},
            "search_window": {
                "start_time": "01:40:00",
                "end_time": "01:40:00",
                "step_minutes": 0,
                "step_seconds": 1,
            },
            "source_docs": [],
            "events": [],
        }

        markdown = _build_session_preparation_package_markdown(
            chart,
            "Test Kisi",
            "Grup-99",
            rectification_record=rectification_record,
        )

        self.assertIn("| Rektifikasyon | inceleme gerekli |", markdown)
        self.assertNotIn("| Rektifikasyon | yapıldı |", markdown)
        self.assertNotIn("| 3 aylık transit aralığı |", markdown)

        rectification_record["rectification_v1_status"] = {
            "code": "candidate_window_available",
            "label_tr": "Aday pencere var",
        }
        markdown = _build_session_preparation_package_markdown(
            chart,
            "Test Kisi",
            "Grup-99",
            rectification_record=rectification_record,
        )

        self.assertIn("| Rektifikasyon | aday pencere var |", markdown)
        self.assertNotIn("| Rektifikasyon | yapıldı |", markdown)

    def test_career_selected_transit_coverage_preserves_candidate_dates(self):
        life_period = {
            "career_timing_evidence_v2": {
                "early_career_candidates": [
                    {
                        "start_date": "1995-05-25",
                        "end_date": "1995-11-23",
                        "dasha_path": ["Rahu", "Venus", "Venus"],
                    },
                    {
                        "start_date": "1996-01-17",
                        "end_date": "1996-04-17",
                        "dasha_path": ["Rahu", "Venus", "Moon"],
                    },
                ],
            },
        }
        transit_pack = {
            "period": {
                "type": "range",
                "range_start": "1995-05-25",
                "range_end": "1995-11-25",
            },
        }

        rows = _career_selected_transit_coverage_rows(
            life_period,
            transit_pack,
        )

        self.assertEqual(rows[0][1], "1995-05-25")
        self.assertEqual(rows[0][2], "1995-11-23")
        self.assertEqual(rows[0][5], "1995-05-25 → 1995-11-23")
        self.assertEqual(rows[0][6], "tam_kapsam")
        self.assertEqual(rows[0][7], "")
        self.assertEqual(rows[1][6], "kapsam_dışı")

    def test_active_transit_source_uses_explicit_mode_without_merging(self):
        selected_markdown = _active_transit_source_markdown({
            "period": {
                "type": "range",
                "range_start": "1995-05-25",
                "range_end": "1995-11-25",
                "day_count": 185,
            },
            "_source_path": "/tmp/selected-range.md",
        })
        automatic_markdown = _active_transit_source_markdown({
            "period": {
                "type": "three_month",
                "range_start": "2026-06-01",
                "range_end": "2026-08-31",
                "day_count": 92,
            },
            "_source_path": "/tmp/automatic-three-month.md",
        })

        self.assertIn("- Kaynak modu: selected_range", selected_markdown)
        self.assertNotIn("automatic_three_month", selected_markdown)
        self.assertIn("- Kaynak modu: automatic_three_month", automatic_markdown)
        self.assertNotIn("selected_range", automatic_markdown)
        self.assertIn(
            "Seçili özel aralık ile otomatik üç aylık paket birleştirilmez.",
            selected_markdown,
        )

    def test_latest_saved_transit_range_is_reused_for_any_person(self):
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                transit_dir = (
                    Path(tmp_dir)
                    / "Transitler"
                    / "Grup-99"
                    / "Herhangi Kisi"
                )
                transit_dir.mkdir(parents=True)
                old_path = (
                    transit_dir
                    / "Herhangi Kisi-Transit Aralığı-1994-01-01_1994-01-02.md"
                )
                new_path = (
                    transit_dir
                    / "Herhangi Kisi-Transit Aralığı-1995-05-25_1995-11-25.md"
                )
                old_path.write_text(
                    "\n".join([
                        "---",
                        'type: "transit_pack"',
                        'period: "range"',
                        'range_start: "1994-01-01"',
                        'range_end: "1994-01-02"',
                        "day_count: 2",
                        'created: "2026-06-14T12:00:00+03:00"',
                        "---",
                    ]),
                    encoding="utf-8",
                )
                new_path.write_text(
                    "\n".join([
                        "---",
                        'type: "transit_pack"',
                        'period: "range"',
                        'range_start: "1995-05-25"',
                        'range_end: "1995-11-25"',
                        "day_count: 185",
                        'created: "2026-06-15T12:00:00+03:00"',
                        "---",
                    ]),
                    encoding="utf-8",
                )

                transit_pack = _latest_saved_transit_range_pack(
                    "Grup-99",
                    "Herhangi Kisi",
                )

                self.assertEqual(
                    transit_pack["period"]["range_start"],
                    "1995-05-25",
                )
                self.assertEqual(
                    transit_pack["period"]["range_end"],
                    "1995-11-25",
                )
                self.assertEqual(transit_pack["_source_path"], str(new_path))
                self.assertIsNone(
                    _latest_saved_transit_pack(
                        "Grup-99",
                        "Herhangi Kisi",
                        "three_month",
                    )
                )
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_analysis_package_refresh_defaults_to_automatic_three_month(self):
        automatic_pack = {
            "period": {
                "type": "three_month",
                "range_start": "2026-06-01",
                "range_end": "2026-08-31",
            },
        }
        other_savers = {
            "_save_health_analysis_data_package": DEFAULT,
            "_save_family_analysis_data_package": DEFAULT,
            "_save_education_analysis_data_package": DEFAULT,
            "_save_relocation_analysis_data_package": DEFAULT,
            "_save_finance_analysis_data_package": DEFAULT,
            "_save_relationship_analysis_data_package": DEFAULT,
            "_save_character_analysis_data_package": DEFAULT,
            "_save_spiritual_analysis_data_package": DEFAULT,
            "_save_varshaphala_analysis_data_package": DEFAULT,
            "_save_legal_analysis_data_package": DEFAULT,
            "_save_planet_role_activation_package": DEFAULT,
            "_save_session_preparation_package": DEFAULT,
        }

        with patch(
            "app._latest_saved_transit_pack",
            return_value=automatic_pack,
        ) as latest_mock, patch(
            "app._save_career_analysis_data_package",
            return_value=Path("/tmp/Kariyer Analizi Veri Paketi.md"),
        ) as career_mock, patch.multiple(
            "app",
            **other_savers,
        ) as saver_mocks:
            _save_analysis_data_packages(
                {"birth": {}},
                "Herhangi Kisi",
                "Grup-99",
                transit_pack=None,
            )

        latest_mock.assert_called_once_with(
            "Grup-99",
            "Herhangi Kisi",
            "three_month",
        )
        career_mock.assert_called_once_with(
            {"birth": {}},
            "Herhangi Kisi",
            "Grup-99",
            transit_pack=automatic_pack,
        )
        for saver_mock in saver_mocks.values():
            self.assertEqual(
                saver_mock.call_args.kwargs.get("transit_pack"),
                automatic_pack,
            )

    def test_birth_time_customer_declaration_policy(self):
        def post_for_time(hour, minute, confidence=None):
            birth = {
                "year": 1990,
                "month": 8,
                "day": 15,
                "hour": hour,
                "minute": minute,
                "timezone_id": "Europe/Istanbul",
                "lat": 41.0082,
                "lon": 28.9784,
            }
            if confidence:
                birth["time_confidence"] = confidence
            return self.client.post(
                "/api/v2/chart/full",
                json={
                    "person": {"id": "kisi", "name": "Kisi"},
                    "birth": birth,
                    "options": {
                        "ayanamsa": "Lahiri",
                        "zodiac": "sidereal",
                        "house_system": "whole_sign",
                        "node_type": "true",
                        "language": "tr",
                    },
                },
            )

        exact_response = post_for_time(0, 0, "exact")
        self.assertEqual(exact_response.status_code, 200)
        exact = exact_response.get_json()
        self.assertEqual(exact["birth"]["time_confidence"], "exact")
        self.assertTrue(exact["data_quality"]["accepted_as_rectified"])
        self.assertTrue(all(
            value == "high"
            for value in exact["data_quality"]["varga_interpretation_confidence"].values()
        ))

        approximate_response = post_for_time(10, 30, "approximate")
        self.assertEqual(approximate_response.status_code, 200)
        approximate = approximate_response.get_json()
        self.assertEqual(approximate["birth"]["time_confidence"], "approximate")
        self.assertFalse(approximate["data_quality"]["accepted_as_rectified"])
        for division, value in approximate["data_quality"]["varga_interpretation_confidence"].items():
            self.assertEqual(value, "low" if division in {"D30", "D60"} else "high")
        self.assertEqual(approximate["data_quality"]["house_interpretation_confidence"], "high")

        unknown_response = post_for_time(12, 0, "unknown")
        self.assertEqual(unknown_response.status_code, 200)
        unknown = unknown_response.get_json()
        self.assertEqual(unknown["birth"]["time_confidence"], "unknown")
        self.assertEqual(unknown["birth"]["calculation_reference_time"], "12:00")
        self.assertEqual(unknown["lagna"]["reference_frame"], "chandra_lagna")
        self.assertFalse(unknown["lagna"]["is_birth_ascendant"])
        moon = next(planet for planet in unknown["planets"] if planet["id"] == "moon")
        self.assertAlmostEqual(unknown["lagna"]["longitude"], moon["longitude"])
        self.assertEqual(unknown["bhava_chalit"]["status"], "not_applicable_unknown_birth_time")
        for division, value in unknown["data_quality"]["varga_interpretation_confidence"].items():
            self.assertEqual(value, "medium" if division == "D9" else "very_low")
        self.assertNotIn("rectification", unknown)
        self.assertIn("birth_time_policy", unknown)

    def test_rectified_chart_marks_all_supported_vargas_high(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "rectified-person", "name": "Rectified Person"},
                "birth": {
                    "year": 1990,
                    "month": 8,
                    "day": 15,
                    "hour": 10,
                    "minute": 30,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 41.0082,
                    "lon": 28.9784,
                    "time_confidence": "rectified",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["birth"]["time_confidence_label"], "eminim")
        self.assertTrue(data["data_quality"]["accepted_as_rectified"])
        self._assert_rectified_vargas_confidence(data)
        self.assertEqual(data["analysis_modules"]["health"]["status"], "ready")

    def test_transits_can_use_user_selected_reference_datetime(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                    "transit_date": "2026-05-20",
                    "transit_time": "21:30",
                    "transit_tz_offset": 3,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        transits = data["transits"]
        self.assertEqual(
            transits["status"],
            "implemented_selected_date_snapshot_with_dasha_cross_reference",
        )
        self.assertEqual(transits["reference_mode"], "user_selected")
        self.assertEqual(transits["requested_date"], "2026-05-20")
        self.assertEqual(transits["requested_time"], "21:30")
        self.assertEqual(transits["requested_tz_offset"], 3.0)
        self.assertEqual(transits["reference_datetime_utc"], "2026-05-20T18:30:00+00:00")
        self.assertEqual(
            data["dashas"]["vimshottari"]["current_active_reference_utc"],
            transits["reference_datetime_utc"],
        )

    def test_varshaphala_core_uses_selected_reference_year(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {"id": "kisi", "name": "Kisi"},
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                    "transit_date": "2026-05-20",
                    "transit_time": "21:30",
                    "transit_tz_offset": 3,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        varshaphala = data["varshaphala"]
        self.assertEqual(varshaphala["status"], "implemented_technical_varshaphala_core")
        self.assertEqual(varshaphala["reference_mode"], "user_selected")
        self.assertEqual(varshaphala["requested_date"], "2026-05-20")
        self.assertEqual(varshaphala["year"]["varsha_start_year"], 2025)
        self.assertEqual(varshaphala["year"]["completed_years"], 47)
        self.assertLess(varshaphala["year"]["sun_return_error_degrees"], 0.0001)
        self.assertIn("source_rule", varshaphala)
        self.assertIn("assumptions", varshaphala)
        self.assertIn("excluded_rules", varshaphala)
        self.assertIn("varsha_lagna", varshaphala)
        self.assertIn("muntha", varshaphala)
        self.assertIn(varshaphala["muntha"]["house_from_varsha_lagna"], range(1, 13))
        self.assertEqual(len(varshaphala["houses"]), 12)
        self.assertEqual(len(varshaphala["planets"]), 9)
        self.assertEqual(len(varshaphala["mudda_dasha"]["periods"]), 9)
        self.assertIsNotNone(varshaphala["mudda_dasha"]["active"])
        self.assertIn("selected", varshaphala["year_lord"])
        self.assertEqual(
            varshaphala["varshesha_arbitration_readiness"]["status"],
            "not_ready_pending_reference_validation",
        )
        self.assertEqual(
            varshaphala["varshesha_arbitration_readiness"]["score_status"],
            "not_scored",
        )
        self.assertFalse(
            varshaphala["varshesha_arbitration_readiness"]["final_varshesha_ready"]
        )
        self.assertFalse(
            varshaphala["varshesha_arbitration_readiness"]["summary"]["scored"]
        )
        self.assertFalse(
            varshaphala["varshesha_arbitration_readiness"]["summary"]["rectification_score_used"]
        )
        self.assertEqual(
            varshaphala["varshesha_arbitration_readiness"]["summary"]["candidate_count"],
            len(varshaphala["year_lord"]["candidates"]),
        )
        self.assertEqual(
            varshaphala["varshesha_arbitration_readiness"]["current_selected_candidate"]["planet"],
            varshaphala["year_lord"]["selected"]["planet"],
        )
        self.assertEqual(
            varshaphala["varshesha_arbitration_readiness"]["current_selected_candidate"]["interpretation_limit"],
            "selected_candidate_is_not_final_parampara_judgement",
        )
        varshesha_blockers = {
            row["key"]
            for row in varshaphala["varshesha_arbitration_readiness"]["blocking_items"]
        }
        self.assertIn(
            "full_panchadhikari_varshesha_arbitration",
            varshesha_blockers,
        )
        self.assertIn(
            "tajika_aspectual_strength_in_year_lord_selection",
            varshesha_blockers,
        )
        self.assertEqual(
            varshaphala["sahams"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertEqual(varshaphala["sahams"]["score_status"], "not_scored")
        self.assertFalse(varshaphala["sahams"]["summary"]["scored"])
        self.assertFalse(varshaphala["sahams"]["summary"]["rectification_score_used"])
        self.assertEqual(
            {row["key"] for row in varshaphala["sahams"]["points"]},
            {"punya_saham", "karma_saham", "vivaha_saham"},
        )
        for point in varshaphala["sahams"]["points"]:
            self.assertEqual(point["status"], "starter_pending_reference_validation")
            self.assertEqual(point["score_status"], "not_scored")
            self.assertIn(point["point"]["house"], range(1, 13))
        self.assertEqual(
            varshaphala["tajika_aspects"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertEqual(varshaphala["tajika_aspects"]["score_status"], "not_scored")
        self.assertFalse(varshaphala["tajika_aspects"]["summary"]["scored"])
        self.assertFalse(
            varshaphala["tajika_aspects"]["summary"]["rectification_score_used"]
        )
        self.assertEqual(varshaphala["tajika_aspects"]["summary"]["planet_count"], 7)
        self.assertGreater(
            varshaphala["tajika_aspects"]["summary"]["relationship_count"],
            0,
        )
        first_relationship = varshaphala["tajika_aspects"]["relationships"][0]
        self.assertIn(
            first_relationship["status"],
            {
                "candidate_orb_within_starter_limit",
                "nearest_angle_reference_only",
            },
        )
        self.assertEqual(first_relationship["score_status"], "not_scored")
        self.assertIn(
            "ithasala_isarapha_yoga_judgement",
            varshaphala["tajika_aspects"]["excluded_rules"],
        )
        self.assertEqual(
            varshaphala["tajika_relationships"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertEqual(varshaphala["tajika_relationships"]["score_status"], "not_scored")
        self.assertFalse(varshaphala["tajika_relationships"]["summary"]["scored"])
        self.assertFalse(
            varshaphala["tajika_relationships"]["summary"]["rectification_score_used"]
        )
        self.assertEqual(
            varshaphala["tajika_relationships"]["summary"]["condition_count"],
            varshaphala["tajika_aspects"]["summary"]["relationship_count"],
        )
        first_condition = varshaphala["tajika_relationships"]["conditions"][0]
        self.assertIn(
            first_condition["motion_status"],
            {"applying_candidate", "separating_candidate", "stationary_or_unclear"},
        )
        self.assertIn(
            first_condition["relationship_status"],
            {
                "ithasala_condition_candidate",
                "isarapha_condition_candidate",
                "technical_reference_only",
                "outside_starter_orb_reference_only",
            },
        )
        self.assertEqual(first_condition["score_status"], "not_scored")
        self.assertIn(
            "full_ithasala_isarapha_judgement",
            varshaphala["tajika_relationships"]["excluded_rules"],
        )
        self.assertEqual(
            varshaphala["tajika_yoga_candidates"]["status"],
            "starter_candidate_inventory",
        )
        self.assertEqual(
            varshaphala["tajika_yoga_candidates"]["score_status"],
            "not_scored",
        )
        self.assertFalse(varshaphala["tajika_yoga_candidates"]["summary"]["scored"])
        self.assertFalse(
            varshaphala["tajika_yoga_candidates"]["summary"]["rectification_score_used"]
        )
        self.assertEqual(
            varshaphala["tajika_yoga_candidates"]["summary"]["candidate_count"],
            len(varshaphala["tajika_yoga_candidates"]["candidates"]),
        )
        for candidate in varshaphala["tajika_yoga_candidates"]["candidates"]:
            self.assertEqual(
                candidate["status"],
                "candidate_pending_reference_validation",
            )
            self.assertEqual(candidate["score_status"], "not_scored")
            self.assertIn(
                "deeptamsa_or_classical_orb_table_validation",
                candidate["missing_for_final_judgement"],
            )
            self.assertEqual(
                candidate["interpretation_limit"],
                "candidate_inventory_only_not_final_tajika_yoga",
            )
        self.assertEqual(
            varshaphala["tajika_orb_diagnostics"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertEqual(
            varshaphala["tajika_orb_diagnostics"]["score_status"],
            "not_scored",
        )
        self.assertEqual(
            varshaphala["tajika_orb_diagnostics"]["orb_policy"]["starter_orb_limit_degrees"],
            6.0,
        )
        self.assertEqual(
            varshaphala["tajika_orb_diagnostics"]["orb_policy"]["classical_deeptamsa_status"],
            "not_validated",
        )
        self.assertFalse(varshaphala["tajika_orb_diagnostics"]["summary"]["scored"])
        self.assertFalse(
            varshaphala["tajika_orb_diagnostics"]["summary"]["rectification_score_used"]
        )
        self.assertEqual(
            varshaphala["tajika_orb_diagnostics"]["summary"]["relationship_count"],
            varshaphala["tajika_aspects"]["summary"]["relationship_count"],
        )
        self.assertGreater(
            len(varshaphala["tajika_orb_diagnostics"]["rows"]),
            0,
        )
        first_orb_row = varshaphala["tajika_orb_diagnostics"]["rows"][0]
        self.assertEqual(first_orb_row["starter_orb_limit_degrees"], 6.0)
        self.assertEqual(first_orb_row["score_status"], "not_scored")
        self.assertEqual(
            first_orb_row["interpretation_limit"],
            "orb_policy_visibility_only_not_classical_deeptamsa_judgement",
        )
        self.assertIn(
            "deeptamsa_or_classical_orb_table_validation",
            varshaphala["tajika_orb_diagnostics"]["missing_for_final_judgement"],
        )
        self.assertEqual(
            varshaphala["tajika_rule_readiness"]["status"],
            "not_ready_pending_reference_validation",
        )
        self.assertEqual(
            varshaphala["tajika_rule_readiness"]["score_status"],
            "not_scored",
        )
        self.assertFalse(varshaphala["tajika_rule_readiness"]["final_judgement_ready"])
        self.assertFalse(varshaphala["tajika_rule_readiness"]["summary"]["scored"])
        self.assertFalse(
            varshaphala["tajika_rule_readiness"]["summary"]["rectification_score_used"]
        )
        readiness_layers = {
            row["layer"]
            for row in varshaphala["tajika_rule_readiness"]["implemented_inputs"]
        }
        self.assertIn("saham_starter_points", readiness_layers)
        self.assertIn("tajika_aspect_starter", readiness_layers)
        self.assertIn("deeptamsa_orb_diagnostics", readiness_layers)
        readiness_blockers = {
            row["key"]
            for row in varshaphala["tajika_rule_readiness"]["blocking_items"]
        }
        self.assertIn("full_tajika_yoga_set", readiness_blockers)
        self.assertIn(
            "deeptamsa_or_classical_orb_table_validation",
            readiness_blockers,
        )
        self.assertIn(
            "panchadhikari_varshesha_arbitration",
            readiness_blockers,
        )
        technical_layers = {
            row["layer"]: row
            for row in varshaphala["technical_layers"]
        }
        self.assertEqual(
            technical_layers["solar_return_core"]["status"],
            "implemented",
        )
        self.assertEqual(
            technical_layers["varshesha_candidates"]["status"],
            "starter_candidate_scoring",
        )
        self.assertEqual(
            technical_layers["varshesha_arbitration_readiness"]["status"],
            "not_ready_pending_reference_validation",
        )
        self.assertIn(
            "full_panchadhikari_varshesha_arbitration",
            technical_layers["varshesha_arbitration_readiness"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["tajika_full_yogas"]["status"],
            "not_available_pending_rules",
        )
        self.assertEqual(
            technical_layers["tajika_aspects"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertIn(
            "ithasala_isarapha_yoga_judgement",
            technical_layers["tajika_aspects"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["ithasala_isarapha_conditions"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertIn(
            "full_ithasala_isarapha_judgement",
            technical_layers["ithasala_isarapha_conditions"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["tajika_yoga_candidates"]["status"],
            "starter_candidate_inventory",
        )
        self.assertIn(
            "final_ithasala_isarapha_judgement",
            technical_layers["tajika_yoga_candidates"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["tajika_orb_diagnostics"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertIn(
            "deeptamsa_or_classical_orb_table_validation",
            technical_layers["tajika_orb_diagnostics"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["tajika_rule_readiness"]["status"],
            "not_ready_pending_reference_validation",
        )
        self.assertIn(
            "full_tajika_yoga_set",
            technical_layers["tajika_rule_readiness"]["missing_data"],
        )
        self.assertIn(
            "full_tajika_yoga_set",
            technical_layers["tajika_full_yogas"]["missing_data"],
        )
        self.assertEqual(
            technical_layers["saham_points"]["status"],
            "starter_pending_reference_validation",
        )
        self.assertIn(
            "full_saham_catalog",
            technical_layers["saham_points"]["missing_data"],
        )

    def test_varshaphala_package_uses_selected_year_and_partial_limits(self):
        response = self.client.post(
            "/api/v2/chart/full",
            json={
                "person": {
                    "id": "kisi",
                    "name": "Kisi",
                    "group": "Grup-01",
                },
                "birth": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "hour": 0,
                    "minute": 15,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                    "time_confidence": "high",
                },
                "options": {
                    "ayanamsa": "Lahiri",
                    "zodiac": "sidereal",
                    "house_system": "whole_sign",
                    "node_type": "true",
                    "language": "tr",
                    "transit_date": "2026-05-20",
                    "transit_time": "21:30",
                    "transit_tz_offset": 3,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        chart = response.get_json()
        text = _build_varshaphala_analysis_data_package_markdown(
            chart,
            "Kisi",
            "Grup-01",
        )
        self.assertIn('reference_year: "2025"', text)
        self.assertIn("## Yıllık Alan Teknik Yoğunlukları", text)
        self.assertIn("Kariyer ve Kamusal Rol", text)
        self.assertIn("İçsel Yönelim ve Anlam Bağlamı", text)
        self.assertIn("full_tajika_yoga_set", text)
        self.assertIn("full_saham_catalog", text)
        self.assertIn("## Varshesha Hakemlik Hazırlık Kapısı", text)
        self.assertIn("final Panchadhikari hakemliği değildir", text)
        self.assertIn("full_panchadhikari_varshesha_arbitration", text)
        self.assertIn("## Saham Noktaları Starter", text)
        self.assertIn("Punya Saham", text)
        self.assertIn("starter_pending_reference_validation", text)
        self.assertIn("## Tajika Aspekt Starter", text)
        self.assertIn("angular_contact_only_not_tajika_yoga_judgement", text)
        self.assertIn("## Ithasala / Isarapha Starter", text)
        self.assertIn(
            "starter_condition_only_not_final_ithasala_isarapha_judgement",
            text,
        )
        self.assertIn("## Tajika Yoga Aday Envanteri", text)
        self.assertIn("candidate_inventory_only_not_final_tajika_yoga", text)
        self.assertIn("## Deeptamsa / Orb Diagnostik", text)
        self.assertIn(
            "orb_policy_visibility_only_not_classical_deeptamsa_judgement",
            text,
        )
        self.assertIn(
            "klasik Deeptamsa hükmü veya gezegen bazlı orb doğrulaması değildir",
            text,
        )
        self.assertIn("## Tajika Kural Hazırlık Kapısı", text)
        self.assertIn("Final Tajika hükmü hazır değildir", text)
        self.assertIn("panchadhikari_varshesha_arbitration", text)
        self.assertIn("## Tajika / Saham Katman Durumu", text)
        self.assertIn("Tam Tajika Yoga Seti", text)
        self.assertIn(
            "Yıllık alan skorları olasılık, şiddet veya sonuç ölçümü değildir",
            text,
        )

    def test_rectification_analyze_scores_candidate_times(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "place": "Izmit, Turkey",
                },
                "search_window": {
                    "start_time": "00:00",
                    "end_time": "00:10",
                    "step_minutes": 5,
                },
                "events": [
                    {
                        "date": "2010-06-15",
                        "type": "career",
                        "confidence": "high",
                    },
                    {
                        "date": "2018-09-20",
                        "type": "marriage",
                        "confidence": "medium",
                    },
                    {
                        "date": "2020-01-10",
                        "type": "relocation",
                        "confidence": "medium",
                    },
                    {
                        "date": "2021-03-12",
                        "type": "childbirth",
                        "confidence": "medium",
                    },
                    {
                        "date": "2022-11-05",
                        "type": "property",
                        "confidence": "low",
                    },
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "implemented_layered_rectification_evidence")
        self.assertEqual(data["method"], "layered_candidate_evidence_from_events_dasha_transits_vargas_kp_and_tattwa")
        self.assertIn("source_rule", data)
        self.assertIn("assumptions", data)
        self.assertIn("excluded_rules", data)
        self.assertIn("rectification_layers", data)
        self.assertIn("candidate_windows", data)
        self.assertIn("candidate_rankings", data)
        self.assertIn("ranking_mode", data)
        self.assertIn("event_evidence_matrix", data)
        self.assertIn("kp_evidence", data)
        self.assertIn("tattwa_evidence", data)
        self.assertIn("varga_evidence", data)
        self.assertEqual(data["method_status"]["data_readiness"], "partial")
        self.assertEqual(data["method_status"]["calibration_readiness"], "not_ready")
        self.assertIn("data_readiness", data)
        self.assertEqual(data["data_readiness"]["status"], "partial")
        self.assertEqual(data["data_readiness"]["score_status"], "not_scored")
        self.assertFalse(data["data_readiness"]["selection_score_changed"])
        self.assertFalse(data["data_readiness"]["summary"]["scored"])
        self.assertFalse(data["data_readiness"]["summary"]["rectification_score_used"])
        readiness_checks = {
            row["check"]: row
            for row in data["data_readiness"]["checks"]
        }
        self.assertEqual(readiness_checks["event_count"]["current"], 5)
        self.assertEqual(readiness_checks["event_count"]["status"], "partial")
        self.assertEqual(readiness_checks["source_documents"]["status"], "missing")
        self.assertEqual(readiness_checks["event_topic_diversity"]["status"], "ready")
        self.assertEqual(readiness_checks["event_time_precision"]["status"], "partial")
        self.assertEqual(readiness_checks["event_time_precision"]["current"], 0)
        self.assertEqual(readiness_checks["event_date_certainty"]["status"], "ready")
        self.assertEqual(readiness_checks["event_date_certainty"]["current"], 5)
        self.assertGreaterEqual(
            data["data_readiness"]["summary"]["distinct_topic_count"],
            3,
        )
        self.assertEqual(
            data["data_readiness"]["summary"]["exact_date_event_count"],
            5,
        )
        self.assertEqual(
            data["data_readiness"]["summary"]["time_precise_event_count"],
            0,
        )
        self.assertIn("career", data["data_readiness"]["topic_counts"])
        self.assertIn("calibration_readiness", data)
        self.assertEqual(data["calibration_readiness"]["status"], "not_ready")
        self.assertEqual(data["calibration_readiness"]["score_status"], "not_scored")
        self.assertFalse(data["calibration_readiness"]["selection_score_changed"])
        self.assertFalse(data["calibration_readiness"]["selected_time_allowed"])
        self.assertFalse(data["calibration_readiness"]["summary"]["scored"])
        self.assertFalse(data["calibration_readiness"]["summary"]["rectification_score_used"])
        calibration_gates = {
            row["gate"]: row
            for row in data["calibration_readiness"]["gates"]
        }
        self.assertEqual(
            calibration_gates["input_data_readiness"]["status"],
            "partial",
        )
        self.assertEqual(
            calibration_gates["varshaphala_tajika_calibration"]["status"],
            "not_ready_for_expanded_rectification_scoring",
        )
        self.assertEqual(
            calibration_gates["selection_decision"]["status"],
            "not_ready",
        )
        self.assertEqual(data["method_status"]["selected_time"], "not_returned_by_design")
        self.assertNotIn("selected_time", data)
        self.assertIn("rectification_v1_status", data)
        self.assertEqual(data["rectification_v1_status"]["code"], "insufficient_data")
        self.assertIn("rectification_score_v1", data)
        self.assertEqual(
            data["method_status"]["rectification_score_v1"],
            "active_candidate_ranking_score",
        )
        score_v1 = data["rectification_score_v1"]
        self.assertTrue(score_v1["used_for_candidate_ranking"])
        self.assertFalse(score_v1["used_for_final_time_selection"])
        self.assertEqual(score_v1["top_candidate_time"], data["candidate_rankings"][0]["time"])
        self.assertEqual(score_v1["top_ranking_score"], data["candidate_rankings"][0]["ranking_score"])
        score_layers = {row["key"]: row for row in score_v1["used_layers"]}
        self.assertIn("events_dasha_transit", score_layers)
        self.assertIn("kp", score_layers)
        self.assertIn("tattwa", score_layers)
        self.assertIn("varshaphala_tajika", score_layers)
        self.assertIn("lagna_anchor", score_layers)
        self.assertTrue(score_layers["events_dasha_transit"]["used_for_candidate_ranking"])
        self.assertIn("external_rectification_source", score_v1["excluded_from_score"])
        self.assertEqual(
            data["method_status"]["rectification_v1_status"],
            "insufficient_data",
        )
        self.assertEqual(data["rectification_decision"]["status"], "not_ready")
        self.assertEqual(
            data["rectification_decision"]["product_status"]["code"],
            "insufficient_data",
        )
        self.assertEqual(data["rectification_decision"]["confidence"], "low")
        self.assertIsNone(data["rectification_decision"]["suggested_time"])
        self.assertFalse(data["rectification_decision"]["selection_allowed"])
        self.assertIn("score_diagnostics", data["rectification_decision"])
        self.assertGreater(len(data["rectification_decision"]["blocking_factors"]), 0)
        self.assertIn(
            "auto_kp_judgement_used",
            {flag["code"] for flag in data["rectification_decision"]["review_flags"]},
        )
        self.assertEqual(data["kp_evidence"]["status"], "implemented")
        self.assertTrue(data["input"]["auto_judgement"])
        self.assertEqual(
            data["kp_evidence"]["judgement"]["source"],
            "auto_generated_analysis_time_birth_location",
        )
        self.assertGreater(len(data["kp_evidence"]["candidate_scores"]), 0)
        self.assertEqual(data["tattwa_evidence"]["status"], "not_applicable_missing_input")
        self.assertEqual(data["method_status"]["ayanamsa_scan"], "implemented_technical_ayanamsa_lagna_scan")
        self.assertEqual(
            data["method_status"]["varshaphala_tajika_evidence"],
            "implemented_technical_varshaphala_tajika_evidence",
        )
        self.assertEqual(
            data["method_status"]["varshaphala_tajika_readiness"],
            "not_ready_for_expanded_rectification_scoring",
        )
        self.assertEqual(data["method_status"]["statistical_model"], "not_available")
        self.assertIn("ayanamsa_scan", data)
        self.assertIn("varshaphala_tajika_evidence", data)
        self.assertIn("varshaphala_tajika_readiness", data)
        self.assertIn("statistical_model", data)
        readiness = data["varshaphala_tajika_readiness"]
        self.assertEqual(
            readiness["status"],
            "not_ready_for_expanded_rectification_scoring",
        )
        self.assertEqual(readiness["score_status"], "not_scored")
        self.assertFalse(readiness["rectification_score_changed"])
        self.assertFalse(readiness["summary"]["expanded_tajika_score_ready"])
        self.assertFalse(readiness["summary"]["scored"])
        self.assertFalse(readiness["summary"]["rectification_score_used"])
        readiness_layers = {
            row["layer"]: row
            for row in readiness["annual_inputs"]
        }
        self.assertEqual(
            readiness_layers["muntha"]["current_rectification_use"],
            "used_in_existing_core_score",
        )
        self.assertEqual(
            readiness_layers["saham_starter_points"]["current_rectification_use"],
            "not_used_for_rectification_score",
        )
        self.assertEqual(
            readiness_layers["tajika_yoga_candidate_inventory"]["score_status"],
            "not_scored",
        )
        readiness_blockers = {
            row["key"]
            for row in readiness["blocking_items"]
        }
        self.assertIn(
            "starter_tajika_layers_not_calibrated_for_rectification",
            readiness_blockers,
        )
        self.assertIn(
            "varshesha_final_arbitration_missing",
            readiness_blockers,
        )
        self.assertEqual(data["candidate_count"], 3)
        self.assertEqual(data["input"]["minimum_recommended_events"], 8)
        self.assertEqual(data["input"]["professional_recommended_events"], "8-20")
        self.assertGreaterEqual(len(data["top_candidates"]), 1)
        self.assertEqual(len(data["candidates"]), 3)
        self.assertEqual(
            {candidate["time"] for candidate in data["candidates"]},
            {"00:00:00", "00:05:00", "00:10:00"},
        )
        for candidate in data["candidates"]:
            self.assertIn("lagna", candidate)
            self.assertIn("d9_lagna", candidate)
            self.assertIn("d10_lagna", candidate)
            self.assertIn("d60_lagna", candidate)
            self.assertIn("kp_lagna_cusp", candidate)
            self.assertIn("change_markers_from_previous_candidate", candidate)
            self.assertIn("lagna_anchor", candidate)
            self.assertIn("ranking_score", candidate)
            self.assertEqual(len(candidate["event_scores"]), 5)
            self.assertIn("layer_scores", candidate)
            self.assertIn("event_total_score", candidate)
            self.assertGreaterEqual(candidate["total_score"], 0)
            for event_score in candidate["event_scores"]:
                self.assertIn(event_score["topic"], {"career", "marriage", "wealth", "health"})
                self.assertIn("event_weight", event_score)
                self.assertIn("raw_score", event_score)
                self.assertIn("weighted_score", event_score)
                self.assertIn("dasha_path", event_score)
                self.assertIn("prana_evidence", event_score)
                self.assertIsNotNone(event_score["prana_evidence"])
                self.assertEqual(event_score["prana_evidence"]["status"], "evidence_only_not_scored")
                self.assertEqual(event_score["prana_evidence"]["level"], "prana")
                self.assertIn("factors", event_score)
        matrix_first_row = data["event_evidence_matrix"]["rows"][0]["candidate_scores"][0]
        self.assertIn("prana_lord", matrix_first_row)
        high_event = data["candidates"][0]["event_scores"][0]
        low_event = data["candidates"][0]["event_scores"][-1]
        self.assertTrue(
            all("ranking_mode" in row for row in data["candidate_rankings"])
        )
        self.assertEqual(high_event["event_weight"]["confidence_weight"], 1.0)
        self.assertEqual(low_event["event_weight"]["confidence_weight"], 0.35)
        self.assertLessEqual(low_event["weighted_score"], low_event["raw_score"])

    def test_rectification_report_returns_astrogpt_technical_package(self):
        payload = {
            "person": {"name": "Teknik Kisi", "group": "Grup-01"},
            "birth_base": {
                "year": 1978,
                "month": 5,
                "day": 28,
                "timezone_id": "Europe/Istanbul",
                "lat": 40.7654,
                "lon": 29.9408,
                "place": "Izmit, Turkey",
                "time_confidence": "medium",
            },
            "birth_window": {
                "start_local": "1978-05-28T00:00",
                "end_local": "1978-05-28T00:10",
                "timezone_id": "Europe/Istanbul",
            },
            "judgement": {
                "date": "2026-05-20",
                "time": "21:30",
                "tz_offset": 3,
                "lat": 40.7654,
                "lon": 29.9408,
            },
            "source_docs": [
                {"type": "hospital_card", "exists": True, "quality": "gold"},
                {"type": "family_memory", "exists": True, "uncertainty_min": 15},
            ],
            "search_window": {
                "start_time": "00:00",
                "end_time": "00:10",
                "step_minutes": 5,
            },
            "events": [
                {"date": "2010-06-15", "type": "career", "confidence": "high", "documented": True},
                {"date": "2018-09-20", "type": "marriage", "confidence": "medium", "documented": True},
                {"date": "2020-01-10", "type": "relocation", "confidence": "medium", "documented": True},
                {"date": "2021-03-12", "type": "childbirth", "confidence": "medium"},
                {"date": "2022-11-05", "type": "property", "confidence": "low"},
            ],
        }

        response = self.rectification_client.post("/api/v2/rectification/report", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "rectification_technical_report_ready")
        self.assertEqual(data["report_type"], "astrogpt_rectification_technical_package")
        self.assertEqual(data["birth_window"]["source_quality"], "gold")
        self.assertEqual(data["data_quality"]["documented_event_count"], 3)
        self.assertEqual(data["data_readiness"]["status"], "partial")
        self.assertFalse(data["data_readiness"]["selection_score_changed"])
        self.assertEqual(data["calibration_readiness"]["status"], "not_ready")
        self.assertFalse(data["calibration_readiness"]["selected_time_allowed"])
        self.assertIn("rectification_v1_status", data)
        self.assertEqual(data["rectification_v1_status"]["code"], "insufficient_data")
        self.assertIn("rectification_score_v1", data)
        self.assertEqual(
            data["rectification_score_v1"]["status"],
            "active_candidate_ranking_score",
        )
        self.assertTrue(data["rectification_score_v1"]["used_for_candidate_ranking"])
        self.assertFalse(data["rectification_score_v1"]["used_for_final_time_selection"])
        self.assertEqual(
            data["analysis"]["rectification_decision"]["product_status"]["code"],
            "insufficient_data",
        )
        report_readiness_checks = {
            row["check"]: row
            for row in data["data_readiness"]["checks"]
        }
        self.assertEqual(report_readiness_checks["source_documents"]["status"], "ready")
        self.assertEqual(report_readiness_checks["documented_events"]["status"], "ready")
        self.assertEqual(report_readiness_checks["event_topic_diversity"]["status"], "ready")
        self.assertEqual(report_readiness_checks["event_time_precision"]["status"], "partial")
        self.assertEqual(report_readiness_checks["event_date_certainty"]["status"], "ready")
        self.assertIn("candidate_windows", data)
        self.assertIn("event_evidence_matrix", data)
        self.assertEqual(data["ayanamsa_scan"]["status"], "implemented_technical_ayanamsa_lagna_scan")
        self.assertEqual(
            data["varshaphala_tajika_evidence"]["status"],
            "implemented_technical_varshaphala_tajika_evidence",
        )
        self.assertEqual(
            data["varshaphala_tajika_readiness"]["status"],
            "not_ready_for_expanded_rectification_scoring",
        )
        self.assertFalse(
            data["varshaphala_tajika_readiness"]["rectification_score_changed"]
        )
        self.assertEqual(
            data["prasna_evidence"]["status"],
            "implemented_starter_prasna_technical_cross_check",
        )
        self.assertEqual(
            data["nasta_jataka_reconstruction"]["status"],
            "starter_technical_indicators_only",
        )
        self.assertEqual(data["statistical_model"]["status"], "not_available")
        self.assertTrue(data["statistical_model"]["probability_interval"]["not_statistical_probability"])
        self.assertIn("astrogpt_markdown", data)
        self.assertIn("Yorum: yok; teknik veri.", data["astrogpt_markdown"])
        self.assertIn("## Veri Hazırlık Özeti", data["astrogpt_markdown"])
        self.assertIn("Bu bölüm veri kalitesi kontrolüdür", data["astrogpt_markdown"])
        self.assertIn("## Kalibrasyon Hazırlık Kapısı", data["astrogpt_markdown"])
        self.assertIn("Bu bölüm karar kapısı özetidir", data["astrogpt_markdown"])
        self.assertIn("## Rektifikasyon v1 Kararı", data["astrogpt_markdown"])
        self.assertIn("Kod: insufficient_data", data["astrogpt_markdown"])
        self.assertIn("## Rektifikasyon Skoru v1", data["astrogpt_markdown"])
        self.assertIn("events_dasha_transit", data["astrogpt_markdown"])
        self.assertIn("external_rectification_source", data["astrogpt_markdown"])
        self.assertIn("## Ayanamsa Scan", data["astrogpt_markdown"])
        self.assertIn("## Varshaphala / Tajika Teknik Katmanı", data["astrogpt_markdown"])
        self.assertIn(
            "## Varshaphala / Tajika Rektifikasyon Hazırlık Kapısı",
            data["astrogpt_markdown"],
        )
        self.assertIn(
            "Starter Saham/Tajika katmanları bu aşamada rektifikasyon ağırlığı değildir",
            data["astrogpt_markdown"],
        )
        self.assertIn("## İstatistiksel Model Durumu", data["astrogpt_markdown"])
        self.assertNotIn("selected_time", data)
        self.assertNotIn("selected_time", data["analysis"])
        self.assertEqual(
            data["analysis"]["candidates"][0]["event_scores"][0]["prana_evidence"]["status"],
            "evidence_only_not_scored",
        )
        self.assertTrue(
            any("No interpretive sentences" in note for note in data["technical_notes"])
        )
        self.assertTrue(
            any("Prana Dasha is exposed inside rectification event evidence as evidence only" in note for note in data["technical_notes"])
        )

    def test_rectification_save_writes_event_record_without_overwrite(self):
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                payload = {
                    "person": {"name": "Ramazan", "group": "Grup-01"},
                    "birth": {
                        "date": "19.05.1980",
                        "time": "04:30",
                        "timezone_id": "Europe/Istanbul",
                        "lat": 37.8746,
                        "lon": 32.4932,
                        "place": "Konya Merkez, Türkiye",
                        "time_confidence": "bilinen",
                    },
                    "birth_window": {
                        "start_local": "1980-05-19T04:00",
                        "end_local": "1980-05-19T05:00",
                        "timezone_id": "Europe/Istanbul",
                        "source_quality": "silver",
                    },
                    "source_docs": [
                        {"type": "family_memory", "exists": True, "uncertainty_min": 30, "quality": "weak"},
                        {"type": "hospital_card", "exists": False, "quality": "gold"},
                    ],
                    "events": [
                        {"date": "24.08.1994", "type": "kariyer"},
                        {
                            "date": "30.08.1998",
                            "type": "career",
                            "time_start_local": "1998-08-30T09:00",
                            "time_end_local": "1998-08-30T18:00",
                            "timezone_id": "Europe/Istanbul",
                            "documented": True,
                            "source_type": "family_document",
                            "importance": "high",
                        },
                        {"date": "11.06.2000", "type": "aile"},
                    ],
                    "analysis_profile": {
                        "mode": "technical",
                        "label": "Teknik mod",
                        "interpretation_language": "evidence_first",
                        "certainty_policy": "yorumdan önce veri, kural, güven ve eksik kontrol bildir",
                        "usage_rule": "Yorum üretmeden önce teknik kanıtları, kullanılan kaynak alanlarını ve eksikleri açıkça sırala.",
                    },
                    "overwrite": False,
                }
                response = self.rectification_client.post("/api/v2/rectification/save", json=payload)

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertTrue(data["ok"])
                self.assertEqual(data["status"], "life_events_record_saved")
                self.assertEqual(data["event_count"], 3)
                self.assertNotIn("transit", data)
                self.assertNotIn("transit_3_month", data)
                self.assertNotIn("analysis_packages", data)
                self.assertFalse(
                    (
                        Path(tmp_dir)
                        / "Transitler"
                        / "Grup-01"
                        / "Ramazan"
                        / "Ramazan-Aylık Transit.md"
                    ).exists()
                )
                self.assertEqual(data["birth_base"]["time_confidence"], "high")
                self.assertEqual(data["birth_window"]["source_quality"], "silver")
                self.assertEqual(len(data["source_docs"]), 2)
                self.assertEqual(
                    [event["type"] for event in data["events"]],
                    ["career", "career", "family"],
                )
                self.assertTrue(data["events"][1]["documented"])
                self.assertEqual(data["events"][1]["source_type"], "family_document")

                record_path = Path(data["paths"]["person"])
                self.assertEqual(
                    record_path,
                    Path(tmp_dir)
                    / "Haritalar"
                    / "Grup-01"
                    / "Ramazan"
                    / "Ramazan.md",
                )
                self.assertTrue(record_path.exists())
                text = record_path.read_text(encoding="utf-8")
                self.assertIn('type: "person_chart"', text)
                self.assertIn("Konya Merkez, Türkiye", text)
                self.assertIn("## Yaşam Olayları Kaydı", text)
                self.assertNotIn("### Rektifikasyon API Payload", text)
                self.assertNotIn("### Rektifikasyon Teknik Rapor Snapshot", text)
                self.assertNotIn('"candidate_rankings"', text)
                self.assertIn("## Yorum Dili / Analiz Modu", text)
                self.assertIn("| analysis_mode | technical |", text)
                self.assertIn("| interpretation_language | evidence_first |", text)
                self.assertIn("| 2000-06-11 | aile | family | family | medium | belirtilmedi | Europe/Istanbul |", text)
                self.assertIn('"birth_base"', text)
                self.assertNotIn('"candidate_rankings"', text)

                side_note_path = record_path.parent / "Ramazan temel analiz.md"
                side_note_path.write_text(
                    '---\ntitle: "Ramazan temel analiz"\ntype: "analysis_note"\nperson: "Ramazan"\ngroup: "Grup-01"\n---\n',
                    encoding="utf-8",
                )
                list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(list_response.status_code, 200)
                listed = list_response.get_json()["records"]
                self.assertEqual(len(listed), 1)
                self.assertEqual(listed[0]["name"], "Ramazan")
                self.assertEqual(listed[0]["group"], "Grup-01")
                self.assertEqual(listed[0]["source_type"], "person_file")
                self.assertTrue(listed[0]["has_life_events"])
                self.assertIn("life_events", listed[0])
                self.assertEqual(listed[0]["paths"]["life_events"], str(record_path))
                self.assertEqual(listed[0]["birth_base"]["year"], 1980)
                self.assertEqual(listed[0]["birth_base"]["timezone_id"], "Europe/Istanbul")
                self.assertEqual(listed[0]["birth_base"]["place"], "Konya Merkez, Türkiye")
                self.assertEqual(listed[0]["birth_window"]["source_quality"], "silver")
                self.assertEqual(len(listed[0]["source_docs"]), 2)
                self.assertEqual(
                    [event["type"] for event in listed[0]["events"]],
                    ["career", "career", "family"],
                )

                load_response = self.client.post(
                    "/api/v2/vault/load",
                    json={"path": str(record_path)},
                )
                self.assertEqual(load_response.status_code, 200)
                loaded_chart = load_response.get_json()["chart"]
                loaded_chart["birth"]["time"] = "04:31:00"
                loaded_chart["birth"]["time_confidence"] = "unknown"
                loaded_chart["birth"]["rectification_status"] = "yapılmadı"
                loaded_chart.pop("life_period_analysis", None)
                overwrite_response = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": loaded_chart,
                        "person": {"name": "Ramazan", "group": "Grup-01"},
                        "overwrite": True,
                    },
                )
                self.assertEqual(overwrite_response.status_code, 200)
                overwritten_text = record_path.read_text(encoding="utf-8")
                self.assertIn("## Yaşam Olayları Kaydı", overwritten_text)
                self.assertIn('"events"', overwritten_text)
                self.assertIn("1998-08-30", overwritten_text)
                overwritten_record = self.client.post(
                    "/api/v2/vault/load",
                    json={"path": str(record_path)},
                ).get_json()["rectification"]
                self.assertEqual(overwritten_record["birth_base"]["minute"], 31)
                self.assertEqual(overwritten_record["birth_base"]["time_confidence"], "unknown")
                self.assertEqual(len(overwritten_record["events"]), 3)

                duplicate = self.rectification_client.post("/api/v2/rectification/save", json=payload)
                self.assertEqual(duplicate.status_code, 409)
                self.assertEqual(duplicate.get_json()["status"], "life_events_record_exists")

                updated_payload = {
                    **payload,
                    "birth": {
                        **payload["birth"],
                        "time": "04:42",
                        "time_confidence": "rectified",
                    },
                    "overwrite": True,
                }
                update_response = self.rectification_client.post("/api/v2/rectification/save", json=updated_payload)
                self.assertEqual(update_response.status_code, 400)
                updated = update_response.get_json()
                self.assertEqual(updated["status"], "rectified_time_blocked_by_v1_gate")
                self.assertEqual(updated["birth_base"]["time_confidence"], "rectified")
                self.assertIn("rectification_v1_status", updated)
                self.assertFalse(updated["rectification_v1_status"]["can_save_rectified_time"])
                self.assertEqual(updated["requested_time"], "04:42:00")
                self.assertFalse(updated["ok"])

                blocked_text = record_path.read_text(encoding="utf-8")
                self.assertNotIn('"time_confidence": "rectified"', blocked_text)
                blocked_record = self.client.post(
                    "/api/v2/vault/load",
                    json={"path": str(record_path)},
                ).get_json()["rectification"]
                self.assertEqual(blocked_record["birth_base"]["hour"], 4)
                self.assertEqual(blocked_record["birth_base"]["minute"], 31)
                self.assertEqual(blocked_record["birth_base"]["time_confidence"], "unknown")

                updated_payload = {
                    **payload,
                    "birth": {
                        **payload["birth"],
                        "time": "04:42",
                        "time_confidence": "bilinen",
                    },
                    "overwrite": True,
                }
                update_response = self.rectification_client.post("/api/v2/rectification/save", json=updated_payload)
                self.assertEqual(update_response.status_code, 200)
                updated = update_response.get_json()
                self.assertEqual(updated["birth_base"]["hour"], 4)
                self.assertEqual(updated["birth_base"]["minute"], 42)
                self.assertEqual(updated["birth_base"]["second"], 0)
                self.assertEqual(updated["birth_base"]["time_confidence"], "high")
                updated_text = record_path.read_text(encoding="utf-8")
                self.assertIn("## Yaşam Olayları Kaydı", updated_text)
                self.assertIn('"time_confidence": "high"', updated_text)
                self.assertNotIn("### Rektifikasyon Teknik Rapor Snapshot", updated_text)

                updated_list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(updated_list_response.status_code, 200)
                updated_record = updated_list_response.get_json()["records"][0]
                self.assertEqual(updated_record["birth_base"]["hour"], 4)
                self.assertEqual(updated_record["birth_base"]["minute"], 42)
                self.assertEqual(updated_record["birth_base"]["second"], 0)

                load_response = self.client.post(
                    "/api/v2/vault/load",
                    json={"name": "Ramazan", "group": "Grup-01"},
                )
                self.assertEqual(load_response.status_code, 200)
                self.assertEqual(load_response.get_json()["life_events"]["birth_base"]["minute"], 42)

                delete_response = self.client.post(
                    "/api/v2/vault/delete",
                    json={
                        "name": "Ramazan",
                        "group": "Grup-01",
                        "record_type": "rectification",
                    },
                )
                self.assertEqual(delete_response.status_code, 200)
                self.assertIn(f"{record_path}#life-events", delete_response.get_json()["deleted"])
                self.assertTrue(record_path.exists())
                self.assertNotIn("## Yaşam Olayları Kaydı", record_path.read_text(encoding="utf-8"))

                empty_list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(empty_list_response.status_code, 200)
                remaining = empty_list_response.get_json()["records"]
                self.assertEqual(len(remaining), 1)
                self.assertFalse(remaining[0]["has_life_events"])
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_rectification_kp_and_tattwa_layers_activate_with_required_inputs(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "birth_sex": "female",
                },
                "judgement": {
                    "date": "2026-05-20",
                    "time": "21:30",
                    "tz_offset": 3,
                    "lat": 40.7654,
                    "lon": 29.9408,
                },
                "search_window": {
                    "start_time": "00:00",
                    "end_time": "00:05",
                    "step_minutes": 5,
                },
                "events": [
                    {"date": "2010-06-15", "type": "career", "confidence": "high", "certainty": "day_exact"},
                    {"date": "2018-09-20", "type": "marriage", "confidence": "medium", "certainty": "month_known"},
                    {"date": "2020-01-10", "type": "relocation", "confidence": "medium", "certainty": "month_known"},
                    {"date": "2021-03-12", "type": "childbirth", "confidence": "medium", "certainty": "day_exact"},
                    {"date": "2022-11-05", "type": "property", "confidence": "low", "certainty": "year_known"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["kp_evidence"]["status"], "implemented")
        self.assertEqual(data["tattwa_evidence"]["status"], "implemented_technical_variant")
        self.assertGreater(len(data["kp_evidence"]["candidate_scores"]), 0)
        self.assertGreater(len(data["tattwa_evidence"]["candidate_scores"]), 0)
        self.assertIn("birth_sex", data["input"]["birth_base"])
        month_event = data["candidates"][0]["event_scores"][1]
        year_event = data["candidates"][0]["event_scores"][-1]
        self.assertEqual(month_event["event_weight"]["certainty_weight"], 0.75)
        self.assertEqual(year_event["event_weight"]["certainty_weight"], 0.45)

    def test_rectification_uses_known_lagna_as_ranking_anchor(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "timezone_id": "Europe/Istanbul",
                    "lat": 40.7654,
                    "lon": 29.9408,
                    "expected_lagna_sign_index": 3,
                },
                "search_window": {
                    "start_time": "00:00",
                    "end_time": "23:00",
                    "step_minutes": 60,
                },
                "events": [
                    {"date": "2010-06-15", "type": "career", "confidence": "high"},
                    {"date": "2018-09-20", "type": "marriage", "confidence": "medium"},
                    {"date": "2020-01-10", "type": "relocation", "confidence": "medium"},
                    {"date": "2021-03-12", "type": "childbirth", "confidence": "medium"},
                    {"date": "2022-11-05", "type": "property", "confidence": "low"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["lagna_anchor"]["status"], "provided")
        self.assertEqual(data["lagna_anchor"]["sign"], "Cancer")
        self.assertTrue(data["top_candidates"])
        self.assertTrue(
            all(candidate["lagna"]["sign_index"] == 3 for candidate in data["top_candidates"])
        )
        self.assertGreater(
            sum(1 for candidate in data["candidates"] if candidate["lagna_anchor"]["status"] == "mismatch"),
            0,
        )
        self.assertTrue(
            all(
                candidate["ranking_score"] < candidate["total_score"]
                for candidate in data["candidates"]
                if candidate["lagna_anchor"]["status"] == "mismatch"
            )
        )

    def test_rectification_does_not_derive_lagna_anchor_from_approximate_time(self):
        approximate = _rectification_expected_lagna_from_birth_base(
            {
                "hour": 2,
                "minute": 0,
                "time_confidence": "medium",
            },
            1979,
            4,
            28,
            3.0,
            37.0742,
            36.2478,
        )
        known = _rectification_expected_lagna_from_birth_base(
            {
                "hour": 2,
                "minute": 0,
                "time_confidence": "known",
            },
            1979,
            4,
            28,
            3.0,
            37.0742,
            36.2478,
        )

        self.assertEqual(approximate["status"], "not_provided")
        self.assertEqual(
            approximate["reason"],
            "birth_time_confidence_not_strong_enough_for_lagna_anchor",
        )
        self.assertEqual(known["status"], "derived")

    def test_rectification_candidate_lagna_uses_birth_timezone(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1980,
                    "month": 3,
                    "day": 1,
                    "tz_offset": 3,
                    "lat": 40.6565,
                    "lon": 29.9,
                    "expected_lagna_sign_index": 3,
                    "time_confidence": "known",
                },
                "search_window": {
                    "start_time": "16:00",
                    "end_time": "17:00",
                    "step_minutes": 15,
                },
                "events": [
                    {"date": "2010-06-15", "type": "career", "confidence": "high"},
                    {"date": "2018-09-20", "type": "marriage", "confidence": "medium"},
                    {"date": "2020-01-10", "type": "relocation", "confidence": "medium"},
                    {"date": "2021-03-12", "type": "childbirth", "confidence": "medium"},
                    {"date": "2022-11-05", "type": "property", "confidence": "low"},
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["input"]["birth_base"]["tz_offset"], 3.0)
        self.assertEqual(data["lagna_anchor"]["sign"], "Cancer")
        self.assertEqual(
            {candidate["time"] for candidate in data["candidates"]},
            {"16:00:00", "16:15:00", "16:30:00", "16:45:00", "17:00:00"},
        )
        self.assertTrue(
            all(candidate["lagna"]["sign"] == "Cancer" for candidate in data["candidates"])
        )
        self.assertTrue(
            all(candidate["lagna_anchor"]["status"] == "matched" for candidate in data["candidates"])
        )

    def test_rectification_analyze_rejects_too_many_candidates(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "tz_offset": 3,
                    "lat": 40.7654,
                    "lon": 29.9408,
                },
                "search_window": {
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "step_minutes": 1,
                },
                "events": [{"date": "2010-06-15", "type": "career"}],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Çok fazla aday saat", response.get_json()["error"])

    def test_rectification_analyze_supports_second_level_steps(self):
        response = self.rectification_client.post(
            "/api/v2/rectification/analyze",
            json={
                "birth_base": {
                    "year": 1978,
                    "month": 5,
                    "day": 28,
                    "tz_offset": 3,
                    "lat": 40.7654,
                    "lon": 29.9408,
                },
                "search_window": {
                    "start_time": "00:00:00",
                    "end_time": "00:01:00",
                    "step_minutes": 0,
                    "step_seconds": 30,
                },
                "events": [{"date": "2010-06-15", "type": "career"}],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["candidate_count"], 3)
        self.assertEqual(data["input"]["search_window"]["step_minutes"], 0)
        self.assertEqual(data["input"]["search_window"]["step_seconds"], 30)
        self.assertEqual(
            {candidate["time"] for candidate in data["candidates"]},
            {"00:00:00", "00:00:30", "00:01:00"},
        )
        self.assertIn(30, {candidate["second"] for candidate in data["candidates"]})

    def test_legacy_calculate_keeps_existing_response_shape(self):
        response = self.client.post(
            "/api/calculate",
            json={
                "year": 1978,
                "month": 5,
                "day": 28,
                "hour": 0,
                "minute": 15,
                "tz_offset": 3,
                "lat": 40.7654,
                "lon": 29.9408,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn("birth_info", data)
        self.assertIn("planets", data)
        self.assertNotIn("meta", data)
        self.assertNotIn("vargas", data)
        self.assertNotIn("aspects", data)
        self.assertNotIn("combustion", data["planets"][0])
        self.assertNotIn("war", data["planets"][0])
        self.assertNotIn("varga_status", data["planets"][0])

    def test_transit_pack_writes_monthly_file_and_supports_three_day_output(self):
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                monthly_payload = self._sample_transit_pack_payload()
                monthly_payload.update({
                    "period": "monthly",
                    "start_date": "2026-05-24",
                    "save": True,
                    "overwrite": True,
                    "include_markdown": False,
                })
                transit_dir = Path(tmp_dir) / "Transitler" / "Grup-99" / "Test Kisi"
                transit_dir.mkdir(parents=True, exist_ok=True)
                old_monthly_path = transit_dir / "Test Kisi-Aylık Transit-2026-05.md"
                old_current_path = transit_dir / "Test Kisi-Güncel Transit.md"
                old_markdown = "\n".join([
                    "---",
                    'type: "transit_pack"',
                    'period: "monthly"',
                    "---",
                    "",
                ])
                old_monthly_path.write_text(old_markdown, encoding="utf-8")
                old_current_path.write_text(old_markdown, encoding="utf-8")
                response = self.client.post("/api/v2/transits/pack", json=monthly_payload)

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertTrue(data["ok"])
                self.assertEqual(data["status"], "transit_pack_saved")
                self.assertEqual(data["period"]["type"], "monthly")
                self.assertEqual(data["period"]["range_start"], "2026-05-01")
                self.assertEqual(data["period"]["range_end"], "2026-05-31")
                self.assertEqual(data["day_count"], 31)
                self.assertNotIn("markdown", data)

                pack_path = Path(data["paths"]["transit_pack"])
                self.assertEqual(
                    pack_path,
                    Path(tmp_dir)
                    / "Transitler"
                    / "Grup-99"
                    / "Test Kisi"
                    / "Test Kisi-Aylık Transit.md",
                )
                self.assertTrue(pack_path.exists())
                self.assertNotIn("transit_current", data["paths"])
                self.assertFalse(old_monthly_path.exists())
                self.assertFalse(old_current_path.exists())
                self.assertEqual(
                    sorted(data["removed_duplicates"]),
                    sorted([str(old_monthly_path), str(old_current_path)]),
                )
                markdown = pack_path.read_text(encoding="utf-8")
                self.assertIn('title: "Test Kisi - Aylık Transit 2026-05-01 - 2026-05-31"', markdown)
                self.assertIn('type: "transit_pack"', markdown)
                self.assertIn('period: "monthly"', markdown)
                self.assertIn('range_start: "2026-05-01"', markdown)
                self.assertIn('range_end: "2026-05-31"', markdown)
                self.assertIn("## AstroGPT Kullanım Notu", markdown)
                self.assertIn("## Transit Veri Paketi Kılavuzu", markdown)
                self.assertIn("### AstroGPT Okuma Talimatı", markdown)
                self.assertIn("### Kullanım Sırası", markdown)
                self.assertIn("Dasha ana dönem aktivasyonudur", markdown)
                self.assertIn("Panchanga ve Ay nakshatra/pada günlük kalite ve zamanlama verir", markdown)
                self.assertIn("3 aylık analizde her gün taranır", markdown)
                self.assertIn("## Günlük Özet Tablosu", markdown)
                self.assertIn("Ay Nakshatra", markdown)
                self.assertIn("2026-05-24", markdown)
                self.assertIn("#### Panchanga", markdown)
                self.assertIn("#### Transit Gezegen Snapshot", markdown)
                self.assertIn("| Gezegen | Burç | Derece | Nakshatra | Pada | Lagna Ev | Ay Ev | SAV | SAV Seviye | BAV | BAV Seviye | R | Aynı Burçtaki Natal |", markdown)
                self.assertIn("SAV ve BAV skorlarını kontrol et", markdown)
                self.assertIn("low_support", markdown)
                self.assertIn("moderate_support", markdown)
                self.assertIn("| Tithi |", markdown)
                self.assertIn("yorum veya kehanet", markdown)

                duplicate = self.client.post("/api/v2/transits/pack", json=monthly_payload)
                self.assertEqual(duplicate.status_code, 200)
                self.assertEqual(duplicate.get_json()["status"], "transit_pack_saved")

                three_day_payload = self._sample_transit_pack_payload()
                three_day_payload.update({
                    "period": "daily",
                    "days": 3,
                    "start_date": "2026-05-24",
                    "save": False,
                    "include_markdown": True,
                })
                three_day_response = self.client.post(
                    "/api/v2/transits/pack",
                    json=three_day_payload,
                )
                self.assertEqual(three_day_response.status_code, 200)
                three_day = three_day_response.get_json()
                self.assertTrue(three_day["ok"])
                self.assertEqual(three_day["period"]["range_start"], "2026-05-24")
                self.assertEqual(three_day["period"]["range_end"], "2026-05-26")
                self.assertEqual(three_day["day_count"], 3)
                self.assertIn("2026-05-26", three_day["markdown"])
                self.assertIn("#### Panchanga", three_day["markdown"])
                self.assertIn("Ay Nakshatra", three_day["markdown"])
                self.assertIn("SAV Seviye", three_day["markdown"])
                self.assertIn("BAV Seviye", three_day["markdown"])
                self.assertNotIn("paths", three_day)

                three_month_payload = self._sample_transit_pack_payload()
                three_month_payload.update({
                    "period": "three_month",
                    "start_date": "2026-05-24",
                    "save": True,
                    "overwrite": False,
                    "include_markdown": True,
                })
                three_month_response = self.client.post("/api/v2/transits/pack", json=three_month_payload)
                self.assertEqual(three_month_response.status_code, 200)
                three_month = three_month_response.get_json()
                self.assertTrue(three_month["ok"])
                self.assertEqual(three_month["period"]["type"], "three_month")
                self.assertEqual(three_month["period"]["range_start"], "2026-05-01")
                self.assertEqual(three_month["period"]["range_end"], "2026-07-31")
                self.assertEqual(three_month["period"]["cadence"], "daily_snapshot")
                self.assertEqual(three_month["day_count"], 92)
                three_month_path = Path(three_month["paths"]["transit_pack"])
                self.assertEqual(
                    three_month_path,
                    Path(tmp_dir)
                    / "Transitler"
                    / "Grup-99"
                    / "Test Kisi"
                    / "Test Kisi-3 Aylık Transit-2026-05_2026-07.md",
                )
                self.assertTrue(three_month_path.exists())
                self.assertNotIn("transit_current", three_month["paths"])
                self.assertIn('title: "Test Kisi - 3 Aylık Transit 2026-05-01 - 2026-07-31"', three_month["markdown"])
                self.assertIn('period: "three_month"', three_month["markdown"])
                self.assertIn('cadence: "daily_snapshot"', three_month["markdown"])
                self.assertIn("2026-07-31", three_month["markdown"])
                self.assertIn("#### Panchanga", three_month["markdown"])
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_vault_save_writes_single_person_file_without_overwrite(self):
        chart = self._sample_v2_chart()
        life_response = self.client.get(
            "/vedic/life-period-analysis",
            query_string={
                "person_id": "test-kisi",
                "birth_date": "1978-05-28",
                "birth_time": "00:15",
                "birth_place": "40.7654,29.9408",
                "from_age": "1",
                "to_date": "1982-05-28",
                "planets": "saturn,jupiter",
            },
        )
        self.assertEqual(life_response.status_code, 200)
        chart["life_period_analysis"] = life_response.get_json()
        chart.pop("life_period_analysis")
        analysis_profile = {
            "mode": "astrolog",
            "label": "Astrolog modu",
            "interpretation_language": "strong_professional",
            "certainty_policy": "çoklu gösterge desteği varsa güçlü hüküm dili; yine de kader kesinliği yok",
            "usage_rule": "Natal vaat, dasha, transit ve varga aynı temayı destekliyorsa daha net astrolog dili kullan.",
        }
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                response = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": chart,
                        "person": {"name": "Test Kisi", "group": "Grup-99"},
                        "analysis_profile": analysis_profile,
                        "overwrite": False,
                    },
                )
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertIn("copy_packages", data)
                self.assertIn("expert", data["copy_packages"])
                self.assertEqual(
                    data["copy_packages"]["expert"]["generator"],
                    "_build_expert_copy_markdown",
                )
                self.assertIn(
                    "# Test Kisi Teknik Harita Paketi",
                    data["copy_packages"]["expert"]["markdown"],
                )
                person_path = Path(data["paths"]["person"])
                legacy_natal_path = Path(tmp_dir) / "Haritalar" / "Grup-99" / "Test Kisi" / "Test Kisi-Natal.md"
                legacy_dashas_path = Path(tmp_dir) / "Dashas" / "Grup-99" / "Test Kisi" / "Test Kisi-Dashas.md"

                self.assertEqual(
                    person_path,
                    Path(tmp_dir) / "Haritalar" / "Grup-99" / "Test Kisi" / "Test Kisi.md",
                )
                self.assertTrue(person_path.exists())
                self.assertNotIn("transit", data)
                self.assertTrue(data["transit_3_month"]["ok"])
                self.assertEqual(data["transit_3_month"]["period"]["type"], "three_month")
                self.assertEqual(data["transit_3_month"]["period"]["cadence"], "daily_snapshot")
                topic_package_keys = {
                    "career",
                    "health",
                    "family",
                    "education",
                    "relocation",
                    "finance",
                    "relationship",
                    "character",
                    "spiritual",
                    "varshaphala",
                    "legal",
                    "planets",
                }
                for package_key in topic_package_keys:
                    package_text = Path(
                        data["analysis_packages"][package_key]["path"]
                    ).read_text(encoding="utf-8")
                    self.assertIn(
                        "## Aktif Transit Veri Kaynağı",
                        package_text,
                    )
                    self.assertIn(
                        "- Kaynak modu: automatic_three_month",
                        package_text,
                    )
                career_package_path = Path(data["analysis_packages"]["career"]["path"])
                self.assertEqual(
                    career_package_path,
                    Path(tmp_dir)
                    / "Haritalar"
                    / "Grup-99"
                    / "Test Kisi"
                    / "Kariyer Analizi Veri Paketi.md",
                )
                self.assertTrue(career_package_path.exists())
                career_package_text = career_package_path.read_text(encoding="utf-8")
                self.assertIn("# Test Kisi - Kariyer Analizi Veri Paketi", career_package_text)
                self.assertIn("Sohbete ekle.", career_package_text)
                self.assertIn("## Kariyer Analiz Veri Paketi", career_package_text)
                self.assertIn("### D10 Dashamsha", career_package_text)
                self.assertIn("### Kariyer / Meslek Özeti", career_package_text)
                self.assertIn(
                    "## Kariyer Olay Zamanlama Kanıtı v2",
                    career_package_text,
                )
                self.assertIn(
                    "Aktivasyon puanı olasılık değildir",
                    career_package_text,
                )
                self.assertIn(
                    "### Yetişkin Dönemi Olay Türü Aktivasyon Sıralamaları",
                    career_package_text,
                )
                self.assertIn(
                    "Teknik aktivasyon dış dünyada gerçekleşmeyi göstermez",
                    career_package_text,
                )
                self.assertIn(
                    "### Erken Kariyer Adayları (15-17.99 Yaş)",
                    career_package_text,
                )
                self.assertIn(
                    "### Yerel Kesinti / Yeniden Yapılanma Dönüm Noktaları",
                    career_package_text,
                )
                self.assertIn(
                    "## Neptün Transit Kariyer Kanıtı v1",
                    career_package_text,
                )
                self.assertIn(
                    "Mevcut beş kariyer olay türünün puanlarını veya sıralamalarını değiştirmez",
                    career_package_text,
                )
                self.assertNotIn("### İlişki / Ortaklık Özeti", career_package_text)

                range_payload = self._sample_transit_pack_payload()
                range_payload.update({
                    "period": "range",
                    "start_date": "1995-05-25",
                    "end_date": "1995-05-25",
                    "save": True,
                    "overwrite": True,
                    "include_markdown": False,
                })
                range_response = self.client.post(
                    "/api/v2/transits/pack",
                    json=range_payload,
                )
                self.assertEqual(range_response.status_code, 200)
                range_data = range_response.get_json()
                self.assertTrue(range_data["analysis_packages_sync"]["ok"])
                self.assertEqual(
                    range_data["analysis_packages_sync"]["paths"]["career"],
                    str(career_package_path),
                )
                for package_key in topic_package_keys:
                    package_text = Path(
                        range_data["analysis_packages_sync"]["paths"][package_key]
                    ).read_text(encoding="utf-8")
                    self.assertIn(
                        "- Kaynak modu: selected_range",
                        package_text,
                    )
                    self.assertNotIn(
                        "- Kaynak modu: automatic_three_month",
                        package_text,
                    )
                career_package_text = career_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "- Seçili transit aralığı: 1995-05-25 → 1995-05-25",
                    career_package_text,
                )
                self.assertIn(
                    f"- Kaynak transit dosyası: {range_data['paths']['transit_pack']}",
                    career_package_text,
                )

                health_package_path = Path(data["analysis_packages"]["health"]["path"])
                self.assertEqual(
                    health_package_path,
                    person_path.parent / "Sağlık Analizi Veri Paketi.md",
                )
                health_package_text = health_package_path.read_text(encoding="utf-8")
                self.assertIn("## Sağlık Analizi Tanımı", health_package_text)
                self.assertIn("beden bölgeleri", health_package_text)
                self.assertIn(
                    "## Sağlık Beden Bölgesi ve Mekanizma Adayları",
                    health_package_text,
                )
                self.assertIn("Doku-Akış Mekanizması", health_package_text)
                self.assertIn("teşhis değil", health_package_text)
                self.assertIn("## D1 Sağlık Evleri", health_package_text)
                self.assertIn("### D6 Full Tablo", health_package_text)
                self.assertIn("### D30 Full Tablo", health_package_text)
                self.assertIn(
                    "## Sağlık Olay Zamanlama Kanıtı v1",
                    health_package_text,
                )
                self.assertIn(
                    "### Akut / Ani Kriz Aktivasyonu",
                    health_package_text,
                )
                self.assertIn(
                    "### Akut Keskin Transit Yakınsamaları",
                    health_package_text,
                )
                self.assertIn(
                    "Gerçek yaşam sağlık olayları hesaplama girdisi olarak kullanılmamıştır",
                    health_package_text,
                )
                family_package_path = Path(
                    data["analysis_packages"]["family"]["path"]
                )
                self.assertEqual(
                    family_package_path,
                    person_path.parent
                    / "Aile ve Ebeveynlik Analizi Veri Paketi.md",
                )
                self.assertTrue(family_package_path.exists())
                family_package_text = family_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Aile ve Ebeveynlik Analizi Veri Paketi",
                    family_package_text,
                )
                self.assertIn(
                    "## D1 Aile ve Ebeveynlik Evleri",
                    family_package_text,
                )
                self.assertIn(
                    "### D7 Saptamsha Full Tablo",
                    family_package_text,
                )
                self.assertIn(
                    "### D12 Dwadashamsha Full Tablo",
                    family_package_text,
                )
                self.assertIn(
                    "## Aile Olay Zamanlama Kanıtı v1",
                    family_package_text,
                )
                self.assertIn(
                    "### Aile Kaybı / Yas Bağlamı",
                    family_package_text,
                )
                self.assertIn(
                    "Kayıp/yas bağlamı ölüm, kişi veya ölüm tarihi tahmini değildir",
                    family_package_text,
                )
                education_package_path = Path(
                    data["analysis_packages"]["education"]["path"]
                )
                self.assertEqual(
                    education_package_path,
                    person_path.parent
                    / "Eğitim ve Uzmanlaşma Analizi Veri Paketi.md",
                )
                education_package_text = education_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Eğitim ve Uzmanlaşma Analizi Veri Paketi",
                    education_package_text,
                )
                self.assertIn(
                    "### D24 Chaturvimshamsha Full Tablo",
                    education_package_text,
                )
                self.assertIn(
                    "## Eğitim Olay Zamanlama Kanıtı v1",
                    education_package_text,
                )
                self.assertIn(
                    "### Eğitimde Kesinti veya Ara",
                    education_package_text,
                )
                relocation_package_path = Path(
                    data["analysis_packages"]["relocation"]["path"]
                )
                self.assertEqual(
                    relocation_package_path,
                    person_path.parent
                    / "Taşınma Yurtdışı ve Yerleşim Analizi Veri Paketi.md",
                )
                relocation_package_text = relocation_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Taşınma Yurtdışı ve Yerleşim Analizi Veri Paketi",
                    relocation_package_text,
                )
                self.assertIn(
                    "### D4 Chaturthamsha Full Tablo",
                    relocation_package_text,
                )
                self.assertIn(
                    "## Taşınma Olay Zamanlama Kanıtı v1",
                    relocation_package_text,
                )
                self.assertIn(
                    "### Yurtdışı Seyahat veya Yaşam Bağlamı",
                    relocation_package_text,
                )
                finance_package_path = Path(
                    data["analysis_packages"]["finance"]["path"]
                )
                self.assertEqual(
                    finance_package_path,
                    person_path.parent
                    / "Finans Gelir ve Mülk Analizi Veri Paketi.md",
                )
                finance_package_text = finance_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Finans Gelir ve Mülk Analizi Veri Paketi",
                    finance_package_text,
                )
                self.assertIn("### D2 Hora Full Tablo", finance_package_text)
                self.assertIn(
                    "## Finans Olay Zamanlama Kanıtı v1",
                    finance_package_text,
                )
                self.assertIn(
                    "### Borç, Yükümlülük ve Baskı Bağlamı",
                    finance_package_text,
                )
                relationship_package_path = Path(data["analysis_packages"]["relationship"]["path"])
                self.assertEqual(
                    relationship_package_path,
                    person_path.parent / "İlişki ve Evlilik Analizi Veri Paketi.md",
                )
                relationship_package_text = relationship_package_path.read_text(encoding="utf-8")
                self.assertIn("## D1 İlişki Evleri", relationship_package_text)
                self.assertIn("## D9 Navamsha Full Tablo", relationship_package_text)
                self.assertIn("## Jaimini İlişki Göstergeleri", relationship_package_text)
                self.assertIn("## Mangala Dosha Teknik Durumu", relationship_package_text)
                self.assertIn(
                    "## İlişki Olay Zamanlama Kanıtı v1",
                    relationship_package_text,
                )
                self.assertIn(
                    "### Ayrışma veya İlişki Sonu Bağlamı",
                    relationship_package_text,
                )
                character_package_path = Path(data["analysis_packages"]["character"]["path"])
                self.assertEqual(
                    character_package_path,
                    person_path.parent / "Karakter Analizi Veri Paketi.md",
                )
                character_package_text = character_package_path.read_text(encoding="utf-8")
                self.assertIn("## Lagna ve Lagna Yöneticisi", character_package_text)
                self.assertIn("## Temel Karakter Gezegenleri", character_package_text)
                self.assertIn("## Jaimini Kimlik Göstergeleri", character_package_text)
                self.assertIn("## Doğum Panchanga Göstergeleri", character_package_text)
                self.assertIn(
                    "## Karakter Dönemsel Aktivasyon Kanıtı v1",
                    character_package_text,
                )
                self.assertIn(
                    "### Zihin, Öğrenme ve İletişim",
                    character_package_text,
                )
                spiritual_package_path = Path(
                    data["analysis_packages"]["spiritual"]["path"]
                )
                self.assertEqual(
                    spiritual_package_path,
                    person_path.parent
                    / "Ruhsal Yönelim Dharma ve İçsel Dönüşüm Veri Paketi.md",
                )
                spiritual_package_text = spiritual_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Ruhsal Yönelim Dharma ve İçsel Dönüşüm Veri Paketi",
                    spiritual_package_text,
                )
                self.assertIn(
                    "### D20 Vimshamsha Teknik Tablosu",
                    spiritual_package_text,
                )
                self.assertIn(
                    "## Natal Rahu-Ketu Ekseni",
                    spiritual_package_text,
                )
                self.assertIn(
                    "Rahu, Swiss Ephemeris TRUE_NODE",
                    spiritual_package_text,
                )
                self.assertNotRegex(
                    spiritual_package_text,
                    r"\|\s*Rahu\s*\|\s*veri yok",
                )
                self.assertIn(
                    "## Ruhsal Yönelim Dönemsel Aktivasyon Kanıtı v1",
                    spiritual_package_text,
                )
                self.assertIn(
                    "### İnanç ve Değerlerde Yeniden Yapılanma",
                    spiritual_package_text,
                )
                varshaphala_package_path = Path(
                    data["analysis_packages"]["varshaphala"]["path"]
                )
                self.assertEqual(
                    varshaphala_package_path,
                    person_path.parent
                    / "Yıllık Döngü ve Varshaphala Teknik Veri Paketi.md",
                )
                varshaphala_package_text = (
                    varshaphala_package_path.read_text(encoding="utf-8")
                )
                self.assertIn(
                    "# Test Kisi - Yıllık Döngü ve Varshaphala Teknik Veri Paketi",
                    varshaphala_package_text,
                )
                self.assertIn(
                    "## Yıllık Alan Teknik Yoğunlukları",
                    varshaphala_package_text,
                )
                self.assertIn(
                    "## Mudda Dasha",
                    varshaphala_package_text,
                )
                self.assertIn(
                    "full_tajika_yoga_set",
                    varshaphala_package_text,
                )
                legal_package_path = Path(
                    data["analysis_packages"]["legal"]["path"]
                )
                self.assertEqual(
                    legal_package_path,
                    person_path.parent
                    / "Hukuki Süreç Sözleşme ve Uyuşmazlık Teknik Veri Paketi.md",
                )
                legal_package_text = legal_package_path.read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "# Test Kisi - Hukuki Süreç Sözleşme ve Uyuşmazlık Teknik Veri Paketi",
                    legal_package_text,
                )
                self.assertIn(
                    "## Natal Rahu-Ketu Ekseni",
                    legal_package_text,
                )
                self.assertIn(
                    "Rahu, Swiss Ephemeris TRUE_NODE",
                    legal_package_text,
                )
                self.assertNotRegex(
                    legal_package_text,
                    r"\|\s*Rahu\s*\|\s*veri yok",
                )
                self.assertIn(
                    "## Hukuki Süreç Zamanlama Kanıtı v1",
                    legal_package_text,
                )
                self.assertIn(
                    "### Uyuşmazlık ve Hukuki Süreç Bağlamı",
                    legal_package_text,
                )
                self.assertIn(
                    "Bu paket hukuki, finansal, vergi veya profesyonel tavsiye değildir",
                    legal_package_text,
                )
                planets_package_path = Path(data["analysis_packages"]["planets"]["path"])
                self.assertEqual(
                    planets_package_path,
                    person_path.parent
                    / "Gezegen Rol ve Aktivasyon Veri Paketi.md",
                )
                self.assertTrue(planets_package_path.exists())
                planets_package_text = planets_package_path.read_text(encoding="utf-8")
                self.assertIn("# Test Kisi - Gezegen Rol ve Aktivasyon Veri Paketi", planets_package_text)
                self.assertIn("## GPT İçin Okuma Sırası", planets_package_text)
                self.assertIn("## GPT İçin Hızlı Okuma", planets_package_text)
                self.assertIn("## Ev Bazlı Drishti Özeti", planets_package_text)
                self.assertIn("## Teknik Kanıt Ekleri", planets_package_text)
                self.assertIn(
                    "| Gezegen | Kişisel Roller | Doğal Karaka | D1 Konum | Shadbala | Güncel Aktivasyon | KP İlk 3 Ev |",
                    planets_package_text,
                )
                self.assertIn(
                    "| Ev | Burç | Graha Drishti Alanlar | Rashi Drishti Alanlar | Sayım |",
                    planets_package_text,
                )
                self.assertLess(
                    planets_package_text.index("## GPT İçin Hızlı Okuma"),
                    planets_package_text.index("## Ev Bazlı Drishti Özeti"),
                )
                self.assertLess(
                    planets_package_text.index("## Ev Bazlı Drishti Özeti"),
                    planets_package_text.index("## Teknik Kanıt Ekleri"),
                )
                self.assertLess(
                    planets_package_text.index("## Teknik Kanıt Ekleri"),
                    planets_package_text.index("## Güneş"),
                )
                summary_text = planets_package_text[
                    planets_package_text.index("## GPT İçin Hızlı Okuma"):
                    planets_package_text.index("## Teknik Kanıt Ekleri")
                ]
                self.assertNotIn("aktif Vimshottari lordu", summary_text)
                self.assertEqual(planets_package_text.count("### Derin Bağlantı Zinciri"), 9)
                self.assertEqual(planets_package_text.count("### Okunmuş Teknik Zincir"), 9)
                self.assertEqual(planets_package_text.count("### Rol Özeti"), 9)
                self.assertEqual(planets_package_text.count("### Natal Durum"), 9)
                self.assertIn("Nakshatra zinciri", planets_package_text)
                self.assertIn("Graha drishti zinciri", planets_package_text)
                self.assertIn("Rashi drishti zinciri", planets_package_text)
                self.assertIn("Kısa yorum: Bu zincir", planets_package_text)
                self.assertIn("Aktivasyon notu:", planets_package_text)
                self.assertIn("natal/Jaimini omurga kanıtıdır", planets_package_text)
                self.assertIn("ev yöneticiliği", planets_package_text)
                self.assertIn("### Dispozitör ve Nakshatra Bağlantıları", planets_package_text)
                self.assertIn("### Açı Bağlantıları", planets_package_text)
                self.assertIn("### Varga Konumları", planets_package_text)
                self.assertIn("vargas.D1.planets.rahu", planets_package_text)
                session_package_path = Path(data["analysis_packages"]["session"]["path"])
                self.assertEqual(
                    session_package_path,
                    person_path.parent
                    / "Seans Hazırlık Teknik Veri Paketi.md",
                )
                self.assertTrue(session_package_path.exists())
                session_package_text = session_package_path.read_text(encoding="utf-8")
                self.assertIn(
                    "# Test Kisi - Seans Hazırlık Teknik Veri Paketi",
                    session_package_text,
                )
                self.assertIn("## Seans Hazırlık Durumu", session_package_text)
                self.assertIn("Kayıtlı yaşam olayı yok", session_package_text)
                self.assertIn("## Güncel Vimshottari Zinciri", session_package_text)
                self.assertIn("## Aktif Gezegen Teknik Özeti", session_package_text)
                self.assertIn(
                    "## Seçili Transit Aralığı Teknik Değişim Noktaları",
                    session_package_text,
                )
                self.assertIn(
                    "| Seçili transit aralığı | 1995-05-25 → 1995-05-25 |",
                    session_package_text,
                )
                self.assertIn("transit_pack.days[]", session_package_text)
                self.assertNotIn("kesin gerçekleşecek", session_package_text)
                transit_3_month_path = Path(data["transit_3_month"]["paths"]["transit_pack"])
                self.assertIn("Test Kisi-3 Aylık Transit-", transit_3_month_path.name)
                self.assertTrue(transit_3_month_path.exists())
                transit_3_month_text = transit_3_month_path.read_text(encoding="utf-8")
                self.assertIn('period: "three_month"', transit_3_month_text)
                self.assertIn('cadence: "daily_snapshot"', transit_3_month_text)
                self.assertIn("#### Panchanga", transit_3_month_text)
                self.assertFalse(
                    (
                        Path(tmp_dir)
                        / "Transitler"
                        / "Grup-99"
                        / "Test Kisi"
                        / "Test Kisi-Aylık Transit.md"
                    ).exists()
                )
                self.assertFalse(legacy_natal_path.exists())
                self.assertFalse(legacy_dashas_path.exists())

                person_text = person_path.read_text(encoding="utf-8")
                self.assertIn("---", person_text)
                self.assertIn('type: "person_chart"', person_text)
                self.assertIn('person: "Test Kisi"', person_text)
                self.assertIn('group: "Grup-99"', person_text)
                self.assertIn('modified: "', person_text)
                self.assertIn("- Dosya değişim tarihi: ", person_text)
                self.assertLess(
                    person_text.index("- Dosya değişim tarihi: "),
                    person_text.index("## Bağlantılar"),
                )
                self.assertIn("## Gezegen Tablosu", person_text)
                self.assertIn("Dignity", person_text)
                self.assertIn("Combustion", person_text)
                self.assertIn("War", person_text)
                self.assertIn("[[Test Kisi-Yorumlar|Yorumlar]]", person_text)
                self.assertIn("## D9 Navamsha", person_text)
                self.assertIn("## Jaimini Chara Karakalar", person_text)
                self.assertIn("## Vimshottari Dasha Özeti", person_text)
                self.assertIn("## Maha Dasha Özeti", person_text)
                self.assertIn("## Uzman Kopya Paketi", person_text)
                self.assertIn("# Test Kisi Teknik Harita Paketi", person_text)
                self.assertNotIn("## Teknik Harita Paketi Kılavuzu", person_text)
                self.assertIn("| Gezegen | Legacy Toplam | Rupa | Gerekli Rupa | Oran | Durum | En Guclu | En Zayif | Yuddha Adj. |", person_text)
                self.assertIn("| Gezegen | Teknik Not |", person_text)
                self.assertIn("## Yorum Dili / Analiz Modu", person_text)
                self.assertIn("| analysis_mode | astrolog |", person_text)
                self.assertIn("| interpretation_language | strong_professional |", person_text)
                self.assertIn("## Panchanga Teknik Paketi", person_text)
                self.assertNotIn("### Panchanga Okuma Talimatı", person_text)
                self.assertIn("### Panchanga Referansı", person_text)
                self.assertIn("### Panchanga Angaları", person_text)
                self.assertIn("### Kartografi Çekirdeği", person_text)
                self.assertIn("### Panchanga Gezegen Boylamları", person_text)
                self.assertIn("| Tithi | Saptami | 22 | 7 |", person_text)
                self.assertIn("| Vara | Sunday | Ravivara | 6 |", person_text)
                self.assertIn("| Ay Nakshatra | Dhanishta | 23 | 1 | Mars |", person_text)
                self.assertIn("planet_angular_lines", person_text)
                self.assertIn("## D9 Navamsha Full Tablo", person_text)
                self.assertNotIn("## Varga Paketleri Okuma Talimatı", person_text)
                for division, name in VARGA_NAMES.items():
                    self.assertIn(f"## {division} {name} Full Tablo", person_text)
                self.assertNotIn("## D10 Dashamsha Meslek Haritası", person_text)
                self.assertNotIn("## D12 Sağlık/Hassasiyet Varga Tablosu", person_text)
                self.assertIn("## Varga Güven Durumu", person_text)
                self.assertIn("customer_time_declaration_policy", person_text)
                self.assertNotIn("## Chara Dasha Aktif Periyotlar", person_text)
                self.assertNotIn("## Yogini Dasha Aktif Periyotlar", person_text)
                self.assertNotIn("API response içinde aktif periyot yok", person_text)
                self.assertNotIn("### Dasha Okuma Talimatı", person_text)
                self.assertIn("## Yoga Listesi", person_text)
                self.assertIn("### SAV per House", person_text)
                self.assertIn("SAV toplamı Ashtakavarga kontrol toplamıdır", person_text)
                self.assertIn("### BAV per House", person_text)
                self.assertIn("| Ev | Burç | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |", person_text)
                self.assertIn("## Bhava Bala", person_text)
                self.assertIn("starter_technical_layer", person_text)
                self.assertIn("### Ev Bazlı Kanıt Tablosu", person_text)
                self.assertIn("| Ev | Burç | Lord | Gezegenler | Graha Drishti | Rashi Drishti | SAV | Lord BAV | Lord Shadbala | Shadbala Seviye | Dignity | Combust | Bhava Cusp | Chalit Değişim | Skor Durumu |", person_text)
                self.assertIn("not_scored", person_text)
                self.assertIn("yeni ağırlıklı Bhava Bala skoru üretmez", person_text)
                self.assertIn("## Bhava Chalit", person_text)
                self.assertIn("implemented_passive_technical_layer", person_text)
                self.assertIn("### Gezegen Ev Karşılaştırması", person_text)
                self.assertIn("### Sripati Cusp Tablosu", person_text)
                self.assertIn("Zamanlama kararı veya tahmin aralığı bu tabloyla üretilmez", person_text)
                self.assertIn("## Vimshopaka Bala", person_text)
                self.assertIn("## Avasthalar", person_text)
                self.assertNotIn("Rektifikasyon aday pencereleri", person_text)
                self.assertNotIn("API response içinde bhava_chalit alanı yok", person_text)
                self.assertIn("## Graha Yuddha Sonucu", person_text)
                self.assertIn("## KP Star / Sub / Sub-Sub", person_text)
                self.assertIn("## Varshaphala Teknik Paketi", person_text)
                self.assertNotIn("### Varshaphala Okuma Talimatı", person_text)
                self.assertIn("### Varshaphala Özet", person_text)
                self.assertIn("### Varshesha Adayları", person_text)
                self.assertIn("### Yıllık Evler", person_text)
                self.assertIn("### Yıllık Gezegenler", person_text)
                self.assertIn("### Mudda Dasha", person_text)
                self.assertIn("Muntha", person_text)
                self.assertIn("Varsha Lagna", person_text)
                self.assertIn("full_tajika_yoga_set", person_text)
                self.assertNotIn("## TeknikAstroGPT Analiz Modülleri", person_text)
                self.assertNotIn("## TeknikAstroGPT Analiz Paketleri Detay", person_text)
                self.assertNotIn("| prashna | requires_context | none |", person_text)
                self.assertIn("## Kariyer Analiz Veri Paketi", person_text)
                self.assertNotIn("### Kullanım Kılavuzu", person_text)
                self.assertNotIn("TeknikAstroGPT bu bölümü", person_text)
                self.assertIn("### Hesap Bilgileri", person_text)
                self.assertIn("| House system | whole_sign |", person_text)
                self.assertIn("### D1 Kariyer Evleri", person_text)
                self.assertIn("| Ev | Burç | Lord | Gezegenler | Graha Drishti | Rashi Drishti | Karakalar | SAV |", person_text)
                self.assertIn("### D1 Kariyer Ev Lordları", person_text)
                self.assertIn("| Ev | Lord | D1 Konum | Derece | Nakshatra | Dignity | Combustion | War | R | D10 Konum |", person_text)
                self.assertIn("Rohini / Pada 1 / Moon", person_text)
                self.assertIn("### Kariyer Karakaları", person_text)
                self.assertIn("| Gezegen | D1 Konum | Derece | Nakshatra | Dignity | Shadbala | Seviye | D10 Konum |", person_text)
                self.assertIn("### D10 Dashamsha", person_text)
                self.assertIn("### Jaimini Kariyer Göstergeleri", person_text)
                self.assertIn("Amatyakaraka", person_text)
                self.assertIn("### Aktif Vimshottari Kariyer Bağlantısı", person_text)
                self.assertIn("| Seviye | Lord | D1 Konum | Nakshatra | Yönettiği Evler | D10 Konum |", person_text)
                self.assertIn("### Ashtakavarga Kariyer Evleri", person_text)
                self.assertIn("| Ev | SAV | Sun BAV | Saturn BAV | Mercury BAV | Jupiter BAV | Mars BAV | Venus BAV |", person_text)
                self.assertIn("### Kariyer Yoga Kanıtları", person_text)
                self.assertIn("## Konu Analiz Özetleri", person_text)
                self.assertIn("Bu bölüm API tarafından deterministik olarak derlenmiş", person_text)
                self.assertNotIn("### Konu Paketi Okuma Talimatı", person_text)
                self.assertIn("### Kariyer / Meslek Özeti", person_text)
                self.assertIn("### İlişki / Ortaklık Özeti", person_text)
                self.assertIn("### Servet / Maddi Özeti", person_text)
                self.assertIn("### Ruhsal / Karma Özeti", person_text)
                self.assertIn("- Bu özet API tarafından üretilmiştir; yorum içermez.", person_text)
                self.assertIn("- Dasha lordlarının D10 konumu:", person_text)
                self.assertIn("- BAV Kariyer Evleri:", person_text)
                self.assertIn("- BAV Servet Evleri:", person_text)
                self.assertIn("- 7. ev: SAV=", person_text)
                self.assertLess(
                    person_text.index("## Kariyer Analiz Veri Paketi"),
                    person_text.index("## Konu Analiz Özetleri"),
                )
                self.assertLess(
                    person_text.index("## Konu Analiz Özetleri"),
                    person_text.index("## Uzun Dönem Dasha + Satürn/Jüpiter Transit Teknik Tablosu"),
                )
                self.assertIn("## Uzun Dönem Dasha + Satürn/Jüpiter Transit Teknik Tablosu", person_text)
                self.assertNotIn("### Uzun Dönem Okuma Talimatı", person_text)
                self.assertIn("### Life Maha Dasha", person_text)
                self.assertIn("### Life Antardasha", person_text)
                self.assertIn("### Life Pratyantardasha", person_text)
                self.assertIn("### Kariyer Olay Zamanlama Kanıtı v2", person_text)
                self.assertIn(
                    "#### Yetişkin Dönemi Olay Türü Aktivasyon Sıralamaları",
                    person_text,
                )
                self.assertIn(
                    "#### Erken Kariyer Adayları (15-17.99 Yaş)",
                    person_text,
                )
                self.assertIn(
                    "#### Yerel Kesinti / Yeniden Yapılanma Dönüm Noktaları",
                    person_text,
                )
                self.assertIn("Bu tablo olay tahmini değildir", person_text)
                self.assertIn("Aktivasyon puanı olasılık değildir", person_text)
                self.assertIn("Yön Durumu", person_text)
                self.assertIn("Life tabloları seçilen tarih aralığına kırpılır", person_text)
                self.assertIn("### Saturn Sidereal Transit Periods", person_text)
                self.assertIn("### Rahu-Ketu Sidereal Transit Periods", person_text)
                self.assertIn("true_node", person_text)
                self.assertIn("### Jupiter Sidereal Transit Periods", person_text)
                self.assertIn("### Dasha Transit Overlap Periods", person_text)
                self.assertNotIn("- Durum: not_available", person_text)
                self.assertNotIn("life_period_analysis eklenmeden üretildi", person_text)
                self.assertNotIn("## Transit Snapshot", person_text)
                self.assertNotIn("Transit referansı UTC", person_text)
                self.assertIn("obsidian_links", data)
                self.assertIn("person", data["obsidian_links"])
                self.assertIn("wiki_links", data)

                duplicate = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": chart,
                        "person": {"name": "Test Kisi", "group": "Grup-99"},
                        "overwrite": False,
                    },
                )
                self.assertEqual(duplicate.status_code, 409)
                self.assertEqual(duplicate.get_json()["error"], "Dosya zaten var")

                chart_without_modules = dict(chart)
                chart_without_modules.pop("analysis_modules", None)
                default_overwrite = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": chart_without_modules,
                        "person": {"name": "Test Kisi", "group": "Grup-99"},
                    },
                )
                self.assertEqual(default_overwrite.status_code, 200)
                updated_text = person_path.read_text(encoding="utf-8")
                self.assertNotIn("## TeknikAstroGPT Analiz Modülleri", updated_text)
                self.assertIn("## Konu Analiz Özetleri", updated_text)

                planets_package_path = (
                    person_path.parent
                    / "Gezegen Rol ve Aktivasyon Veri Paketi.md"
                )
                planets_package_path.unlink()
                legacy_planets_path = (
                    Path(tmp_dir)
                    / "Analiz Veri Paketleri"
                    / "Grup-99"
                    / "Test Kisi"
                    / "Gezegen Rol ve Aktivasyon Veri Paketi.txt"
                )
                legacy_planets_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_planets_path.write_text("eski paket", encoding="utf-8")
                career_package_path.write_text(
                    "eski kariyer paketi",
                    encoding="utf-8",
                )
                health_package_path.write_text(
                    "eski sağlık paketi",
                    encoding="utf-8",
                )
                relationship_package_path.write_text(
                    "eski ilişki paketi",
                    encoding="utf-8",
                )
                self.assertIn("<!-- chart-snapshot:start -->", person_text)
                self.assertIn("<!-- chart-snapshot:data", person_text)
                self.assertIn('"snapshot_schema": "minimal_chart_v1"', person_text)
                self.assertIn('"api_version": "v2"', person_text)
                self.assertIn('"active_dasha_path": [', person_text)
                self.assertIn('"planet": "Sun"', person_text)
                self.assertIn("chart-snapshot:data-end -->", person_text)
                self.assertIn("<!-- chart-snapshot:end -->", person_text)
                person_text_before_load = person_path.read_text(encoding="utf-8")
                transit_text_before_load = transit_3_month_path.read_text(
                    encoding="utf-8"
                )

                load_response = self.client.post(
                    "/api/v2/vault/load",
                    json={"path": str(person_path)},
                )
                self.assertEqual(load_response.status_code, 200)
                loaded = load_response.get_json()
                self.assertTrue(loaded["ok"])
                self.assertEqual(
                    loaded["load_mode"],
                    "recomputed_from_saved_birth_markdown",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["birth"],
                    "saved_markdown",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["chart"],
                    "recomputed_from_saved_birth_markdown",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["saved_snapshot"]["available"],
                    True,
                )
                self.assertEqual(
                    loaded["source_of_truth"]["saved_snapshot"]["schema"],
                    "minimal_chart_v1",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["saved_snapshot"]["reason"],
                    "embedded_minimal_snapshot_present_but_not_used_for_chart_response",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["saved_snapshot"]["summary"]["planet_count"],
                    9,
                )
                self.assertEqual(
                    loaded["source_of_truth"]["saved_snapshot"]["summary"]["house_count"],
                    12,
                )
                self.assertIn(
                    "saved_at",
                    loaded["source_of_truth"]["saved_snapshot"]["summary"],
                )
                self.assertIsInstance(
                    loaded["source_of_truth"]["saved_snapshot"]["summary"]["active_dasha_path"],
                    list,
                )
                self.assertTrue(
                    loaded["source_of_truth"]["saved_snapshot"]["comparison"]["lagna_sign_matches"],
                )
                self.assertTrue(
                    loaded["source_of_truth"]["saved_snapshot"]["comparison"]["planet_count_matches"],
                )
                self.assertTrue(
                    loaded["source_of_truth"]["saved_snapshot"]["comparison"]["house_count_matches"],
                )
                self.assertTrue(
                    loaded["source_of_truth"]["saved_snapshot"]["comparison"]["active_dasha_path_matches"],
                )
                self.assertTrue(
                    loaded["source_of_truth"]["saved_snapshot"]["comparison"]["all_compared_fields_match"],
                )
                self.assertEqual(
                    loaded["source_of_truth"]["expert_copy"],
                    "regenerated_from_loaded_chart",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["expert_copy_details"]["generator"],
                    "_build_expert_copy_markdown",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["expert_copy_details"]["source"],
                    "backend_generator",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["expert_copy_details"]["analysis_mode"],
                    "astrolog",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["expert_copy_details"]["saved_analysis_mode"],
                    "astrolog",
                )
                self.assertTrue(
                    loaded["source_of_truth"]["expert_copy_details"]["matches_saved_analysis_mode"],
                )
                self.assertEqual(
                    loaded["source_of_truth"]["analysis_packages"],
                    "regenerated_on_load",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["analysis_packages_details"]["mode"],
                    "regenerated_on_load",
                )
                self.assertEqual(
                    loaded["source_of_truth"]["analysis_packages_details"]["package_count"],
                    13,
                )
                self.assertEqual(loaded["person"]["name"], "Test Kisi")
                self.assertEqual(loaded["person"]["group"], "Grup-99")
                self.assertEqual(loaded["chart"]["meta"]["api_version"], "v2")
                self.assertEqual(loaded["chart"]["birth"]["date"], chart["birth"]["date"])
                self.assertEqual(loaded["chart"]["birth"]["time"], chart["birth"]["time"])
                self.assertIn("life_period_analysis", loaded["chart"])
                self.assertNotEqual(
                    loaded["chart"]["life_period_analysis"].get("status"),
                    "not_available",
                )
                self.assertIn("copy_packages", loaded)
                self.assertIn("expert", loaded["copy_packages"])
                self.assertEqual(
                    loaded["copy_packages"]["expert"]["generator"],
                    "_build_expert_copy_markdown",
                )
                self.assertIn(
                    "# Test Kisi Teknik Harita Paketi",
                    loaded["copy_packages"]["expert"]["markdown"],
                )
                self.assertEqual(
                    set(loaded["analysis_packages"]),
                    {
                        "career",
                        "health",
                        "family",
                        "education",
                        "relocation",
                        "finance",
                        "relationship",
                        "character",
                        "spiritual",
                        "varshaphala",
                        "legal",
                        "planets",
                        "session",
                    },
                )
                self.assertEqual(
                    Path(loaded["analysis_packages"]["career"]["path"]),
                    career_package_path,
                )
                self.assertIn(
                    "## Kariyer Olay Zamanlama Kanıtı v2",
                    career_package_path.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    Path(loaded["analysis_packages"]["health"]["path"]),
                    health_package_path,
                )
                self.assertIn(
                    "## Sağlık Olay Zamanlama Kanıtı v1",
                    health_package_path.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    Path(loaded["analysis_packages"]["relationship"]["path"]),
                    relationship_package_path,
                )
                self.assertIn(
                    "## İlişki Olay Zamanlama Kanıtı v1",
                    relationship_package_path.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    Path(loaded["analysis_packages"]["planets"]["path"]),
                    planets_package_path,
                )
                self.assertTrue(planets_package_path.exists())
                self.assertIn(
                    "# Test Kisi - Gezegen Rol ve Aktivasyon Veri Paketi",
                    planets_package_path.read_text(encoding="utf-8"),
                )
                loaded_session_path = Path(
                    loaded["analysis_packages"]["session"]["path"]
                )
                self.assertEqual(
                    loaded_session_path,
                    person_path.parent
                    / "Seans Hazırlık Teknik Veri Paketi.md",
                )
                self.assertTrue(loaded_session_path.exists())
                self.assertIn(
                    "# Test Kisi - Seans Hazırlık Teknik Veri Paketi",
                    loaded_session_path.read_text(encoding="utf-8"),
                )
                self.assertFalse(legacy_planets_path.exists())
                self.assertEqual(
                    person_path.read_text(encoding="utf-8"),
                    person_text_before_load,
                )
                self.assertEqual(
                    transit_3_month_path.read_text(encoding="utf-8"),
                    transit_text_before_load,
                )

                list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(list_response.status_code, 200)
                listed = list_response.get_json()
                self.assertTrue(listed["ok"])
                self.assertEqual(len(listed["records"]), 1)
                self.assertEqual(listed["records"][0]["name"], "Test Kisi")
                self.assertEqual(listed["records"][0]["group"], "Grup-99")
                self.assertEqual(listed["records"][0]["paths"]["person"], str(person_path))
                self.assertEqual(listed["records"][0]["source_type"], "person_file")

                delete_response = self.client.post(
                    "/api/v2/vault/delete",
                    json={"name": "Test Kisi", "group": "Grup-99"},
                )
                self.assertEqual(delete_response.status_code, 200)
                deleted = delete_response.get_json()
                self.assertTrue(deleted["ok"])
                self.assertIn(str(person_path), deleted["deleted"])
                self.assertFalse(person_path.exists())
                self.assertFalse(career_package_path.exists())
                self.assertFalse(health_package_path.exists())
                self.assertFalse(relationship_package_path.exists())
                self.assertFalse(character_package_path.exists())

                empty_list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(empty_list_response.status_code, 200)
                self.assertEqual(empty_list_response.get_json()["records"], [])

                legacy_natal_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_dashas_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_natal_path.write_text(person_text, encoding="utf-8")
                legacy_dashas_path.write_text("# Legacy Dashas", encoding="utf-8")

                legacy_list_response = self.client.get("/api/v2/vault/list")
                self.assertEqual(legacy_list_response.status_code, 200)
                legacy_record = legacy_list_response.get_json()["records"][0]
                self.assertEqual(legacy_record["source_type"], "legacy_split_files")
                self.assertEqual(legacy_record["paths"]["person"], str(legacy_natal_path))
                self.assertEqual(legacy_record["paths"]["legacy_dashas"], str(legacy_dashas_path))

                legacy_load_response = self.client.post(
                    "/api/v2/vault/load",
                    json={"name": "Test Kisi", "group": "Grup-99"},
                )
                self.assertEqual(legacy_load_response.status_code, 200)
                self.assertEqual(legacy_load_response.get_json()["person"]["name"], "Test Kisi")
                self.assertIn("life_period_analysis", legacy_load_response.get_json()["chart"])

                legacy_delete_response = self.client.post(
                    "/api/v2/vault/delete",
                    json={"name": "Test Kisi", "group": "Grup-99"},
                )
                self.assertEqual(legacy_delete_response.status_code, 200)
                self.assertFalse(legacy_natal_path.exists())
                self.assertFalse(legacy_dashas_path.exists())
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_frontend_invalidates_rectification_after_manual_time_change(self):
        template_text = (PROJECT_ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        chart_js = (PROJECT_ROOT / "static" / "js" / "chart.js").read_text(encoding="utf-8")

        self.assertIn('<option value="unknown">Rektifikasyonsuz</option>', template_text)
        self.assertIn('<option value="known" selected>Biliniyor</option>', template_text)
        self.assertIn('<option value="rectified">Rektifikasyonlu</option>', template_text)
        self.assertNotIn('<option value="rectified" hidden>', template_text)
        self.assertIn("birth.rectification_status === 'yapıldı'", chart_js)
        self.assertIn("['known', 'unknown', 'rectified'].includes(status.value)", chart_js)
        self.assertIn("function rectificationSourceForForm()", chart_js)
        self.assertIn("external_astrolog_or_user_confirmed", chart_js)
        self.assertIn("rectification_source: rectificationSourceForForm()", chart_js)
        self.assertIn("function invalidateRectifiedBirthTime()", chart_js)
        self.assertIn("status.value = 'unknown';", chart_js)
        self.assertNotIn("status.value === 'rectified'", chart_js)
        self.assertIn("['hour', 'minute', 'second'].includes(id)", chart_js)

    def test_frontend_prefers_vault_record_over_stale_local_recent_save(self):
        chart_js = (PROJECT_ROOT / "static" / "js" / "chart.js").read_text(encoding="utf-8")

        merge_start = chart_js.index("function mergeRecentAndVaultSaves")
        merge_end = chart_js.index("async function loadVaultSaveItems", merge_start)
        merge_source = chart_js[merge_start:merge_end]
        self.assertIn("if (item.source === 'vault')", merge_source)
        self.assertIn("merged[existingPersonIndex] = item;", merge_source)

    def test_vault_save_writes_rectified_varga_confidence_to_obsidian(self):
        chart = self._sample_v2_chart()
        chart["birth"]["time_confidence"] = "rectified"
        chart["birth"]["rectification_status"] = "yapıldı"
        old_root = app.config["VAULT_ASTROLOGY_ROOT"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            app.config["VAULT_ASTROLOGY_ROOT"] = tmp_dir
            try:
                response = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": chart,
                        "person": {"name": "Rectified Person", "group": "Grup-99"},
                        "overwrite": True,
                    },
                )

                self.assertEqual(response.status_code, 400)
                blocked = response.get_json()
                self.assertEqual(blocked["status"], "rectified_time_blocked_by_v1_gate")
                self.assertFalse(blocked["ok"])
                self.assertEqual(blocked["requested_time"], chart["birth"]["time"])

                external_chart = {
                    **chart,
                    "birth": {
                        **chart["birth"],
                        "rectification_source": "external_astrolog_or_user_confirmed",
                    },
                }
                response = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": external_chart,
                        "person": {"name": "External Rectified", "group": "Grup-99"},
                        "overwrite": True,
                    },
                )

                self.assertEqual(response.status_code, 200)
                external_person_text = Path(response.get_json()["paths"]["person"]).read_text(
                    encoding="utf-8",
                )
                self.assertIn("rectified_time_supported", external_person_text)
                self.assertIn("- Müşteri saat beyanı: rektifiye", external_person_text)
                self.assertIn(
                    "Uzman rektifikasyon kaynağı: Dış/onaylı rektifikasyon",
                    external_person_text,
                )
                self.assertIn(
                    "Uzman rektifikasyon kaydı (Dış/onaylı rektifikasyon) müşteri beyanı güveninden ayrı bir teknik kayıt olarak korunur.",
                    external_person_text,
                )
                external_load = self.client.post(
                    "/api/v2/vault/load",
                    json={
                        "name": "External Rectified",
                        "group": "Grup-99",
                    },
                )
                self.assertEqual(external_load.status_code, 200)
                external_loaded_chart = external_load.get_json()["chart"]
                self.assertEqual(
                    external_loaded_chart["data_quality"]["rectification_source"],
                    "external_astrolog_or_user_confirmed",
                )
                self.assertEqual(
                    external_loaded_chart["data_quality"]["rectification_source_label"],
                    "Dış/onaylı rektifikasyon",
                )
                self._assert_rectified_vargas_confidence(
                    external_loaded_chart,
                    expected_status="rectified_time_supported",
                )

                person_path = (
                    Path(tmp_dir)
                    / "Haritalar"
                    / "Grup-99"
                    / "Rectified Person"
                    / "Rectified Person.md"
                )
                person_path.parent.mkdir(parents=True, exist_ok=True)
                person_path.write_text(
                    _build_rectification_embedded_markdown({
                        "person": {"name": "Rectified Person", "group": "Grup-99"},
                        "birth_base": {
                            "year": 1978,
                            "month": 5,
                            "day": 28,
                            "hour": 0,
                            "minute": 15,
                            "second": 0,
                            "timezone_id": "Europe/Istanbul",
                            "tz_offset": 3,
                            "lat": 40.7654,
                            "lon": 29.9408,
                            "time_confidence": "rectified",
                        },
                        "birth_window": {"source_quality": "gold"},
                        "source_docs": [],
                        "search_window": {
                            "start_time": "00:00:00",
                            "end_time": "00:30:00",
                            "step_minutes": 5,
                            "step_seconds": 0,
                        },
                        "events": [],
                        "rectification_v1_status": {
                            "code": "review_candidate_available",
                            "can_save_rectified_time": True,
                            "suggested_time": chart["birth"]["time"],
                        },
                    }),
                    encoding="utf-8",
                )

                response = self.client.post(
                    "/api/v2/vault/save",
                    json={
                        "chart": chart,
                        "person": {"name": "Rectified Person", "group": "Grup-99"},
                        "overwrite": True,
                    },
                )

                self.assertEqual(response.status_code, 200)
                person_path = Path(response.get_json()["paths"]["person"])
                person_text = person_path.read_text(encoding="utf-8")
                self.assertIn("## Varga Güven Durumu", person_text)
                self.assertIn("rectified_time_supported", person_text)
                self.assertIn(
                    "Uzman rektifikasyon kaynağı: API v1 rektifikasyon karar kapısı",
                    person_text,
                )
                self.assertNotIn("pending_astroseek_crosscheck", person_text)
                self.assertIn(
                    "Uzman rektifikasyon kaydı (API v1 rektifikasyon karar kapısı) müşteri beyanı güveninden ayrı bir teknik kayıt olarak korunur.",
                    person_text,
                )
                for division in RECTIFIED_VARGAS:
                    self.assertIn(f"| {division} | available |", person_text)
                self.assertIn("| D1 | available | Rashi | high |", person_text)
                self.assertIn("| D10 | available | Dashamsha | high |", person_text)
                self.assertIn("| D60 | available | Shashtiamsha | high |", person_text)
                self.assertNotIn("| health | ready | high |", person_text)
                self.assertIn("## Konu Analiz Özetleri", person_text)
            finally:
                app.config["VAULT_ASTROLOGY_ROOT"] = old_root

    def test_dignity_flags_classical_strengths(self):
        cases = [
            (
                {"name": "Sun / Güneş", "sign_index": 0, "degree": 10.0},
                {
                    "essential": "exalted",
                    "uccha": True,
                    "neecha": False,
                    "swakshetra": False,
                    "moolatrikona": False,
                    "natural_friendship": "friend",
                },
            ),
            (
                {"name": "Sun / Güneş", "sign_index": 4, "degree": 10.0},
                {
                    "essential": "moolatrikona",
                    "uccha": False,
                    "neecha": False,
                    "swakshetra": True,
                    "moolatrikona": True,
                    "natural_friendship": "own",
                },
            ),
            (
                {"name": "Sun / Güneş", "sign_index": 4, "degree": 25.0},
                {
                    "essential": "own_sign",
                    "uccha": False,
                    "neecha": False,
                    "swakshetra": True,
                    "moolatrikona": False,
                    "natural_friendship": "own",
                },
            ),
            (
                {"name": "Jupiter / Guru", "sign_index": 2, "degree": 14.0},
                {
                    "essential": "enemy",
                    "uccha": False,
                    "neecha": False,
                    "swakshetra": False,
                    "moolatrikona": False,
                    "natural_friendship": "enemy",
                },
            ),
        ]

        for planet, expected in cases:
            with self.subTest(planet=planet):
                dignity = _dignity_for_planet(planet)
                for key, value in expected.items():
                    self.assertEqual(dignity[key], value)

    def test_combustion_uses_solar_distance_and_thresholds(self):
        sun_longitude = 100.0
        cases = [
            (
                {"name": "Sun / Güneş", "longitude": sun_longitude},
                {
                    "is_combust": False,
                    "distance_from_sun": 0.0,
                    "threshold": None,
                    "severity": "not_calculated",
                },
            ),
            (
                {"name": "Moon / Ay", "longitude": 105.0},
                {
                    "is_combust": False,
                    "distance_from_sun": 5.0,
                    "threshold": None,
                    "severity": "none",
                },
            ),
            (
                {"name": "Mercury / Budha", "longitude": 108.0},
                {
                    "is_combust": True,
                    "distance_from_sun": 8.0,
                    "threshold": 14.0,
                    "severity": "moderate",
                },
            ),
            (
                {"name": "Saturn / Shani", "longitude": 104.0},
                {
                    "is_combust": True,
                    "distance_from_sun": 4.0,
                    "threshold": 15.0,
                    "severity": "severe",
                },
            ),
            (
                {"name": "Mars / Mangal", "longitude": 117.0},
                {
                    "is_combust": False,
                    "distance_from_sun": 17.0,
                    "threshold": 17.0,
                    "severity": "none",
                },
            ),
            (
                {"name": "Rahu (True)", "longitude": 102.0},
                {
                    "is_combust": False,
                    "distance_from_sun": 2.0,
                    "threshold": None,
                    "severity": "not_calculated",
                },
            ),
        ]

        for planet, expected in cases:
            with self.subTest(planet=planet):
                combustion = _combustion_for_planet(planet, sun_longitude)
                self.assertEqual(combustion["is_combust"], expected["is_combust"])
                self.assertEqual(combustion["threshold"], expected["threshold"])
                self.assertEqual(combustion["severity"], expected["severity"])
                self.assertAlmostEqual(
                    combustion["distance_from_sun"],
                    expected["distance_from_sun"],
                )

    def test_combustion_distance_wraps_across_zero_degrees(self):
        combustion = _combustion_for_planet(
            {"name": "Mars / Mangal", "longitude": 5.0},
            350.0,
        )

        self.assertAlmostEqual(combustion["distance_from_sun"], 15.0)
        self.assertTrue(combustion["is_combust"])
        self.assertEqual(combustion["severity"], "mild")

    def test_graha_yuddha_only_applies_to_tara_grahas(self):
        war_by_name = _build_war_map([
            {"name": "Sun / Güneş", "longitude": 10.1},
            {"name": "Moon / Ay", "longitude": 10.2},
            {"name": "Mars / Mangal", "longitude": 10.0},
            {"name": "Mercury / Budha", "longitude": 10.75},
            {"name": "Jupiter / Guru", "longitude": 13.0},
            {"name": "Venus / Shukra", "longitude": 359.6},
            {"name": "Saturn / Shani", "longitude": 0.2},
            {"name": "Rahu (True)", "longitude": 10.3},
            {"name": "Ketu", "longitude": 190.3},
        ])

        self.assertEqual(war_by_name["Sun"]["status"], "not_applicable")
        self.assertEqual(war_by_name["Moon"]["status"], "not_applicable")
        self.assertEqual(war_by_name["Rahu"]["status"], "not_applicable")
        self.assertEqual(war_by_name["Ketu"]["status"], "not_applicable")
        self.assertTrue(war_by_name["Mars"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Mars"]["opponent"], "Mercury")
        self.assertEqual(war_by_name["Mars"]["status"], "in_war")
        self.assertAlmostEqual(war_by_name["Mars"]["orb"], 0.75)
        self.assertTrue(war_by_name["Mercury"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Mercury"]["opponent"], "Mars")
        self.assertFalse(war_by_name["Jupiter"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Jupiter"]["status"], "none")
        self.assertTrue(war_by_name["Venus"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Venus"]["opponent"], "Saturn")
        self.assertAlmostEqual(war_by_name["Venus"]["orb"], 0.6)
        self.assertTrue(war_by_name["Saturn"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Saturn"]["opponent"], "Venus")

    def test_graha_yuddha_includes_one_and_half_degree_boundary(self):
        war_by_name = _build_war_map([
            {"name": "Mars / Mangal", "longitude": 100.0},
            {"name": "Mercury / Budha", "longitude": 101.5},
        ])

        self.assertTrue(war_by_name["Mars"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Mars"]["opponent"], "Mercury")
        self.assertAlmostEqual(war_by_name["Mars"]["orb"], 1.5)

    def test_graha_yuddha_detects_close_venus_jupiter_pair(self):
        war_by_name = _build_war_map([
            {"name": "Jupiter / Guru", "longitude": 74.700675},
            {"name": "Venus / Shukra", "longitude": 73.405213},
        ])

        self.assertTrue(war_by_name["Jupiter"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Jupiter"]["opponent"], "Venus")
        self.assertAlmostEqual(war_by_name["Jupiter"]["orb"], 1.295462)
        self.assertTrue(war_by_name["Venus"]["in_graha_yuddha"])
        self.assertEqual(war_by_name["Venus"]["opponent"], "Jupiter")

    def test_expert_graha_yuddha_rows_explain_status_without_false_winner_text(self):
        rows = _expert_graha_yuddha_rows({
            "planets": [
                {"name": "Sun", "war": {"status": "not_applicable", "in_graha_yuddha": False}},
                {"name": "Mars", "war": {"status": "none", "in_graha_yuddha": False}},
                {"name": "Venus", "war": {"status": "in_war", "in_graha_yuddha": True, "opponent": "Jupiter", "orb": 1.295462}},
            ],
        })

        self.assertEqual(rows[0][5], "Graha Yuddha kapsam dışı")
        self.assertEqual(rows[1][5], "Graha Yuddha yok")
        self.assertEqual(rows[2][5], "Graha Yuddha var; kazanan/kaybeden hesaplanmıyor")

    def test_yuddha_bala_uses_orb_based_modifier_without_victory_claim(self):
        detail = _yuddha_bala_detail({
            "name": "Mars",
            "war": {
                "in_graha_yuddha": True,
                "opponent": "Mercury",
                "status": "in_war",
                "orb": 0.2,
            },
        })

        self.assertEqual(detail["method"], "graha_yuddha_orb_based_modifier")
        self.assertEqual(detail["severity"], "severe")
        self.assertEqual(detail["score"], 30.0)
        self.assertEqual(detail["score_adjustment"], -30.0)
        self.assertEqual(detail["opponent"], "Mercury")
        self.assertIn("apparent_diameter_based_victory", detail["excluded_rules"])

    def test_varga_position_rules_for_supported_divisions(self):
        cases = [
            (10.0, "D2", "Leo", 20.0),
            (20.0, "D2", "Cancer", 10.0),
            (40.0, "D2", "Cancer", 20.0),
            (50.0, "D2", "Leo", 10.0),
            (5.0, "D3", "Aries", 15.0),
            (15.0, "D3", "Leo", 15.0),
            (25.0, "D3", "Sagittarius", 15.0),
            (33.0, "D4", "Taurus", 12.0),
            (44.0, "D4", "Leo", 26.0),
            (53.0, "D4", "Aquarius", 2.0),
            (71.0, "D6", "Gemini", 6.0),
            (229.0, "D6", "Capricorn", 24.0),
            (15.0, "D7", "Cancer", 15.0),
            (45.0, "D7", "Aquarius", 15.0),
            (48.0, "D10", "Cancer", 0.0),
            (75.0, "D10", "Scorpio", 0.0),
            (71.0, "D11", "Gemini", 1.0),
            (229.0, "D11", "Pisces", 29.0),
            (112.5, "D12", "Aries", 0.0),
            (71.0, "D20", "Pisces", 10.0),
            (229.0, "D20", "Sagittarius", 20.0),
            (71.0, "D24", "Aries", 24.0),
            (229.0, "D24", "Libra", 6.0),
            (2.0, "D30", "Aries", 12.0),
            (7.0, "D30", "Aquarius", 12.0),
            (14.0, "D30", "Sagittarius", 15.0),
            (20.0, "D30", "Gemini", 8.5714285714),
            (27.0, "D30", "Libra", 12.0),
            (32.0, "D30", "Taurus", 12.0),
            (37.0, "D30", "Virgo", 8.5714285714),
            (46.0, "D30", "Pisces", 15.0),
            (52.0, "D30", "Capricorn", 12.0),
            (57.0, "D30", "Scorpio", 12.0),
            (0.25, "D60", "Aries", 15.0),
            (0.75, "D60", "Taurus", 15.0),
            (30.25, "D60", "Taurus", 15.0),
            (30.75, "D60", "Aries", 15.0),
        ]

        for longitude, division, sign, degree in cases:
            with self.subTest(longitude=longitude, division=division):
                position = _varga_position_from_longitude(longitude, division)
                self.assertEqual(position["sign"], sign)
                self.assertAlmostEqual(position["degree"], degree)


if __name__ == "__main__":
    unittest.main()
