import os
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from flask import Flask

from digest import paid_store, paid_writer
from digest import paid_routes
from digest.paid_routes import _required_snapshot_days
from digest.paid_situation import (
    FOCUS_BY_HOUSE,
    HOMEPAGE_CONTEXT_VERSION,
    HOMEPAGE_METHODOLOGY_VERSION,
    _current_dasha_lord,
    build_homepage_context,
)
from digest.situation import planet_signs_at


class PaidHomepageDigestContractTests(unittest.TestCase):
    def test_context_is_versioned_and_does_not_contain_identity_or_raw_chart(self):
        chart = {
            "id": "chart-secret-id",
            "owner_user_id": "user-secret-id",
            "birth": {"latitude": 41.0, "longitude": 29.0},
            "meta": {"engine_version": "vedic-engine-test"},
            "planets": [{"name": "Moon", "sign_index": 2}],
            "dashas": {"vimshottari": {"current_active": {}}},
        }
        context = build_homepage_context(
            chart,
            date(2026, 8, 21),
            {
                "daily": {
                    "ana_tema": "dinlenme",
                    "snapshot_local_datetime": "2026-08-21T17:00:00+03:00",
                },
                "weekly": {},
            },
        )
        self.assertEqual(context["schema_version"], HOMEPAGE_CONTEXT_VERSION)
        self.assertNotIn("id", context)
        self.assertNotIn("owner_user_id", context)
        self.assertNotIn("birth", context)
        self.assertEqual(
            context["calculation"]["current_snapshot_local_datetime"],
            "2026-08-21T17:00:00+03:00",
        )
        self.assertEqual(context["calculation"]["weekly_snapshot_hour_istanbul"], 12)
        self.assertEqual(set(context["layers"]), {"daily", "weekly"})

    def test_required_days_are_deduplicated(self):
        days = _required_snapshot_days(date(2026, 8, 21))
        self.assertEqual(len(days), len(set(days)))
        self.assertEqual(len(days), 7)

    def test_homepage_methodology_version_and_focus_contract_are_current(self):
        self.assertEqual(HOMEPAGE_CONTEXT_VERSION, "homepage_digest_context_v2")
        self.assertEqual(HOMEPAGE_METHODOLOGY_VERSION, "digest-methodology-v4")
        self.assertEqual(set(FOCUS_BY_HOUSE), set(range(1, 13)))
        self.assertEqual(set(FOCUS_BY_HOUSE.values()), paid_writer.ALLOWED_FOCUS)

    def test_weekly_period_is_resolved_for_now_instead_of_saved_current_active(self):
        chart = {
            "dashas": {
                "vimshottari": {
                    "current_active": {"pratyantar": {"lord": "Stale"}},
                    "maha": [{
                        "level": "maha",
                        "lord": "Saturn",
                        "actual_start_jd": 100,
                        "actual_end_jd": 200,
                        "antara": [{
                            "level": "antara",
                            "lord": "Ketu",
                            "actual_start_jd": 100,
                            "actual_end_jd": 200,
                            "pratyantar": [{
                                "level": "pratyantar",
                                "lord": "Jupiter",
                                "actual_start_jd": 140,
                                "actual_end_jd": 160,
                            }],
                        }],
                    }],
                },
            },
        }
        self.assertEqual(_current_dasha_lord(chart, "weekly", 150), "Jupiter")

    def test_writer_rejects_unsafe_or_uncontrolled_output(self):
        valid = {
            "motto": "Yavaşlamak alan açabilir.",
            "gunluk": {"metin": "Bugün yakın konularda yumuşak bir akış olabilir.", "odak": "dinlenme"},
            "haftalik": {"metin": "Bu hafta iç sesini duymak biraz kolaylaşabilir.", "odak": "huzur"},
        }
        cleaned, error = paid_writer.validate(valid)
        self.assertIsNotNone(cleaned)
        self.assertIsNone(error)

        invalid_focus = dict(valid)
        invalid_focus["gunluk"] = {"metin": "Bugün yumuşak bir akış olabilir.", "odak": "rastgele"}
        self.assertEqual(paid_writer.validate(invalid_focus)[1], "gunluk_odak_allowlist_disi")

        imperative = dict(valid)
        imperative["gunluk"] = {"metin": "Bugün başla ve kendine daha geniş bir alan aç.", "odak": "kendin"}
        self.assertEqual(paid_writer.validate(imperative)[1], "emir_kipi")

    def test_writer_rejects_generic_or_context_mismatched_layers(self):
        expected = {
            "gunluk": {"odak": "dinlenme"},
            "haftalik": {"odak": "huzur"},
        }
        valid = {
            "motto": "Sakinlik bugün sana alan açabilir.",
            "gunluk": {"metin": "Bugün dinlenmek ve sessiz kalmak zihnini toparlamana yardım edebilir.", "odak": "dinlenme"},
            "haftalik": {"metin": "Bu hafta evde kuracağın sakin ritim iç huzurunu destekleyebilir.", "odak": "huzur"},
        }
        cleaned, error = paid_writer.validate(valid, expected)
        self.assertIsNotNone(cleaned)
        self.assertIsNone(error)

        generic = dict(valid)
        generic["gunluk"] = {
            "metin": "Bugün kendine alan açmak sana daha iyi gelebilir.",
            "odak": "dinlenme",
        }
        self.assertEqual(
            paid_writer.validate(generic, expected)[1],
            "gunluk_metin_baglamla_uyusmuyor",
        )

        wrong_focus = dict(valid)
        wrong_focus["haftalik"] = {
            "metin": "Bu hafta ilişkiler ve ortak kararlar daha görünür olabilir.",
            "odak": "ilişki",
        }
        self.assertEqual(
            paid_writer.validate(wrong_focus, expected)[1],
            "haftalik_odak_baglamla_uyusmuyor",
        )

    def test_current_snapshot_uses_requested_istanbul_hour(self):
        local_hour = datetime(2026, 8, 21, 17, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        chart = {"planets": [{"abbr": "Mo", "sign_index": 4}]}
        with patch("vedic_chart.calculate_chart", return_value=chart) as calculate:
            snapshot = planet_signs_at(local_hour)

        self.assertEqual(snapshot["local_datetime"], "2026-08-21T17:00:00+03:00")
        self.assertEqual(snapshot["planets"]["Moon"], 4)
        calculate.assert_called_once_with(2026, 8, 21, 17, 0, 3.0, 41.0082, 28.9784)

    def test_homepage_cache_is_scoped_by_owner_chart_date_and_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("PAID_DIGEST_DB_PATH")
            os.environ["PAID_DIGEST_DB_PATH"] = os.path.join(tmp, "paid_digest.sqlite3")
            try:
                d = date(2026, 8, 21)
                payload = {"motto": "Örnek"}
                paid_store.set_homepage("user-a", "chart-a", payload, d, "hash-a")
                self.assertEqual(
                    paid_store.get_homepage("user-a", "chart-a", d, "hash-a"),
                    payload,
                )
                self.assertIsNone(
                    paid_store.get_homepage("user-b", "chart-a", d, "hash-a")
                )
                self.assertIsNone(
                    paid_store.get_homepage("user-a", "chart-a", d, "hash-b")
                )
            finally:
                if old is None:
                    os.environ.pop("PAID_DIGEST_DB_PATH", None)
                else:
                    os.environ["PAID_DIGEST_DB_PATH"] = old

    def test_route_generates_once_and_reuses_homepage_cache(self):
        app = Flask(__name__)
        app.register_blueprint(paid_routes.paid_digest_bp)
        chart = {
            "meta": {"engine_version": "vedic-engine-test"},
            "planets": [{"name": "Moon", "sign_index": 2}],
            "dashas": {"vimshottari": {"current_active": {}}},
        }
        response_payload = {
            "motto": "Yavaşlamak alan açabilir.",
            "gunluk": {"metin": "Bugün yumuşak bir akış olabilir.", "odak": "huzur"},
            "haftalik": {"metin": "Bu hafta iç sesini duymak kolaylaşabilir.", "odak": "dinlenme"},
        }
        current_hour = datetime(2026, 8, 21, 17, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        with patch.object(paid_routes, "_load_owned_chart", return_value=((chart, "chart-1", "profile-1", "user-1"), None)), \
                patch.object(paid_routes, "current_hour_ist", return_value=current_hour), \
                patch.object(paid_routes, "_load_current_snapshot", return_value=({"date": "2026-08-21", "local_datetime": current_hour.isoformat(), "planets": {}}, 0)), \
                patch.object(paid_routes, "_load_weekly_snapshots", return_value=([{"date": "2026-08-21", "planets": {}}], 0)), \
                patch.object(paid_routes, "build_paid_situation", return_value={"ana_tema": "huzur"}), \
                patch.object(paid_routes, "build_homepage_context", return_value={"schema_version": HOMEPAGE_CONTEXT_VERSION}), \
                patch.object(paid_routes, "_sha256", side_effect=["chart-hash", "snapshot-hash", "context-hash"] * 2), \
                patch.object(paid_routes.paid_store, "get_homepage", side_effect=[None, None, response_payload]), \
                patch.object(paid_routes.paid_store, "acquire_lock", return_value="lock-owner"), \
                patch.object(paid_routes.paid_store, "release_lock"), \
                patch.object(paid_routes.paid_store, "set_homepage"), \
                patch.object(paid_routes.paid_writer, "generate", return_value=(response_payload, None)) as generate:
            client = app.test_client()
            first = client.post("/api/v2/pwa/digest/personal", json={})
            second = client.post("/api/v2/pwa/digest/personal", json={})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json()["status"], "ready")
        self.assertEqual(second.get_json()["kaynak"], "onbellek")
        self.assertNotIn("aylik", first.get_json()["digest"])
        generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
