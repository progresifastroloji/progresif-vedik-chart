import tempfile
import unittest
from pathlib import Path

from app import _resolve_timezone_offset, app
from place_catalog import build_places_database, normalize_place_text, search_places


def _geonames_row(
    geoname_id,
    name,
    ascii_name,
    aliases,
    latitude,
    longitude,
    country_code,
    admin1_code,
    population,
    timezone_id,
    feature_code="PPLA",
):
    return "\t".join(
        map(
            str,
            (
                geoname_id,
                name,
                ascii_name,
                aliases,
                latitude,
                longitude,
                "P",
                feature_code,
                country_code,
                "",
                admin1_code,
                "",
                "",
                "",
                population,
                "",
                "",
                timezone_id,
                "2026-01-01",
            ),
        )
    )


class PlaceCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        cities = root / "cities500.txt"
        cities.write_text(
            "\n".join(
                (
                    _geonames_row(
                        745044,
                        "İstanbul",
                        "Istanbul",
                        "Constantinople,Stamboul",
                        41.0082,
                        28.9784,
                        "TR",
                        "34",
                        14804116,
                        "Europe/Istanbul",
                    ),
                    _geonames_row(
                        5128581,
                        "New York City",
                        "New York City",
                        "NYC,New York",
                        40.71427,
                        -74.00597,
                        "US",
                        "NY",
                        8804190,
                        "America/New_York",
                    ),
                    _geonames_row(
                        2867714,
                        "Munich",
                        "Munich",
                        "München,Muenchen",
                        48.13743,
                        11.57549,
                        "DE",
                        "02",
                        1260391,
                        "Europe/Berlin",
                    ),
                    _geonames_row(
                        2867707,
                        "Münchenbernsdorf",
                        "Munchenbernsdorf",
                        "",
                        50.82114,
                        11.93226,
                        "DE",
                        "15",
                        3450,
                        "Europe/Berlin",
                        "PPL",
                    ),
                )
            )
            + "\n",
            encoding="utf-8",
        )
        countries = root / "countryInfo.txt"
        countries.write_text(
            "TR\tTUR\t792\tTU\tTurkey\nUS\tUSA\t840\tUS\tUnited States\n",
            encoding="utf-8",
        )
        admin1 = root / "admin1CodesASCII.txt"
        admin1.write_text(
            "TR.34\tIstanbul\tIstanbul\t745042\nUS.NY\tNew York\tNew York\t5128638\n",
            encoding="utf-8",
        )
        self.database = root / "places.sqlite3"
        self.assertEqual(
            build_places_database(
                cities,
                self.database,
                country_info_path=countries,
                admin1_codes_path=admin1,
            ),
            4,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalization_ignores_turkish_case_and_diacritics(self):
        self.assertEqual(normalize_place_text(" İSTANBUL  "), "istanbul")

    def test_search_returns_coordinates_and_iana_timezone(self):
        results = search_places(self.database, "istan")
        self.assertEqual(results[0]["name"], "İstanbul")
        self.assertEqual(results[0]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(results[0]["label"], "İstanbul, Istanbul, Turkey")

    def test_search_uses_alternative_names_and_country_filter(self):
        results = search_places(self.database, "NYC", country_code="US")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["place_id"], "5128581")

    def test_exact_alternative_name_ranks_before_longer_prefix(self):
        results = search_places(self.database, "München")
        self.assertEqual(results[0]["name"], "Munich")

    def test_http_endpoint_exposes_resolved_place_contract(self):
        previous = app.config.get("PLACES_DB_PATH")
        app.config["PLACES_DB_PATH"] = str(self.database)
        try:
            response = app.test_client().get("/api/v1/places/search?q=istan&limit=5")
        finally:
            app.config["PLACES_DB_PATH"] = previous
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["places"][0]["timezone_id"], "Europe/Istanbul")
        self.assertEqual(payload["source"]["license"], "CC BY 4.0")

    def test_selected_place_timezone_resolves_historical_birth_offset(self):
        place = search_places(self.database, "istan")[0]
        winter_offset = _resolve_timezone_offset(
            {"timezone_id": place["timezone_id"]},
            2015,
            1,
            15,
            12,
            0,
        )
        summer_offset = _resolve_timezone_offset(
            {"timezone_id": place["timezone_id"]},
            2015,
            7,
            15,
            12,
            0,
        )
        self.assertEqual(winter_offset, (2.0, "Europe/Istanbul"))
        self.assertEqual(summer_offset, (3.0, "Europe/Istanbul"))

    def test_http_endpoint_rejects_unbounded_query(self):
        previous = app.config.get("PLACES_DB_PATH")
        app.config["PLACES_DB_PATH"] = str(self.database)
        try:
            response = app.test_client().get(f"/api/v1/places/search?q={'a' * 101}")
        finally:
            app.config["PLACES_DB_PATH"] = previous
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
