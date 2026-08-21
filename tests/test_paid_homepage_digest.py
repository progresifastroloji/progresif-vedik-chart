import os
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from flask import Flask

from digest import paid_store, paid_writer
from digest import paid_routes
from digest.paid_routes import _required_snapshot_days
from digest.paid_situation import (
    HOMEPAGE_CONTEXT_VERSION,
    build_homepage_context,
)


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
            {"daily": {"ana_tema": "dinlenme"}, "weekly": {}, "monthly": {}},
        )
        self.assertEqual(context["schema_version"], HOMEPAGE_CONTEXT_VERSION)
        self.assertNotIn("id", context)
        self.assertNotIn("owner_user_id", context)
        self.assertNotIn("birth", context)
        self.assertEqual(context["calculation"]["snapshot_hour_istanbul"], 12)

    def test_required_days_are_deduplicated(self):
        days = _required_snapshot_days(date(2026, 8, 21))
        self.assertEqual(len(days), len(set(days)))
        self.assertGreaterEqual(len(days), 31)

    def test_writer_rejects_unsafe_or_uncontrolled_output(self):
        valid = {
            "motto": "Yavaşlamak alan açabilir.",
            "gunluk": {"metin": "Bugün yakın konularda yumuşak bir akış olabilir.", "odak": "dinlenme"},
            "haftalik": {"metin": "Bu hafta iç sesini duymak kolaylaşabilir.", "odak": "huzur"},
            "aylik": {"metin": "Bu ay sadeleşmek sana iyi gelebilir.", "odak": "düzen"},
        }
        cleaned, error = paid_writer.validate(valid)
        self.assertIsNotNone(cleaned)
        self.assertIsNone(error)

        invalid_focus = dict(valid)
        invalid_focus["gunluk"] = {"metin": "Bugün yumuşak bir akış olabilir.", "odak": "rastgele"}
        self.assertEqual(paid_writer.validate(invalid_focus)[1], "gunluk_odak_allowlist_disi")

        imperative = dict(valid)
        imperative["gunluk"] = {"metin": "Bugün başla ve kendine alan aç.", "odak": "kendin"}
        self.assertEqual(paid_writer.validate(imperative)[1], "emir_kipi")

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
            "aylik": {"metin": "Bu ay sadeleşmek sana iyi gelebilir.", "odak": "düzen"},
        }
        with patch.object(paid_routes, "_load_owned_chart", return_value=((chart, "chart-1", "profile-1", "user-1"), None)), \
                patch.object(paid_routes, "_load_homepage_snapshots", return_value=([{"date": "2026-08-21", "planets": {}}], 0)), \
                patch.object(paid_routes, "required_days", return_value=[]), \
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
        generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
