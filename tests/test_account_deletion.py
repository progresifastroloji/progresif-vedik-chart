import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import app, _beta_db


USER_ID = "11111111-1111-4111-8111-111111111111"
OTHER_USER_ID = "22222222-2222-4222-8222-222222222222"


class AccountDeletionTest(unittest.TestCase):
    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_user_data_root = app.config["USER_DATA_ROOT"]
        self._old_local_access_only = app.config["LOCAL_ACCESS_ONLY"]
        self._old_api_token = app.config["API_TOKEN"]
        self._old_account_delete_token = app.config["ACCOUNT_DELETE_TOKEN"]
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        app.config["BETA_DB_PATH"] = str(root / "beta.sqlite3")
        app.config["USER_DATA_ROOT"] = str(root / "users")
        self.client = app.test_client()

    def tearDown(self):
        app.config["BETA_DB_PATH"] = self._old_beta_db_path
        app.config["USER_DATA_ROOT"] = self._old_user_data_root
        app.config["LOCAL_ACCESS_ONLY"] = self._old_local_access_only
        app.config["API_TOKEN"] = self._old_api_token
        app.config["ACCOUNT_DELETE_TOKEN"] = self._old_account_delete_token
        self._tmp.cleanup()

    def _seed_user(self, user_id, profile_id=None):
        profile_id = profile_id or user_id
        with closing(_beta_db()) as conn:
            conn.execute(
                "INSERT INTO beta_profiles (id, name, group_name, birth_json, options_json, chart_id, created_at, owner_user_id) VALUES (?, ?, ?, '{}', '{}', ?, '2026-08-02', ?)",
                (profile_id, f"User {user_id[:4]}", "Beta", f"chart-{profile_id}", user_id),
            )
            conn.execute(
                "INSERT INTO beta_charts (id, profile_id, chart_json, created_at, owner_user_id) VALUES (?, ?, '{}', '2026-08-02', ?)",
                (f"chart-{profile_id}", profile_id, user_id),
            )
            conn.execute(
                "INSERT INTO beta_chat_messages (id, profile_id, chart_id, question, response_json, created_at) VALUES (?, ?, ?, 'question', '{}', '2026-08-02')",
                (f"message-{profile_id}", profile_id, f"chart-{profile_id}"),
            )
            conn.execute(
                "INSERT INTO beta_feedback (id, message_id, profile_id, rating, comment, created_at) VALUES (?, ?, ?, 'good', '', '2026-08-02')",
                (f"feedback-{profile_id}", f"message-{profile_id}", profile_id),
            )
            conn.execute(
                "INSERT INTO beta_usage_events (day, action, profile_id, created_at) VALUES ('2026-08-02', 'chat_draft', ?, '2026-08-02')",
                (profile_id,),
            )
            conn.execute(
                "INSERT INTO beta_methodology_comparisons (id, profile_id, chart_id, question, status, response_json, created_at, updated_at) VALUES (?, ?, ?, 'question', 'comparison_ready', '{}', '2026-08-02', '2026-08-02')",
                (f"comparison-{profile_id}", profile_id, f"chart-{profile_id}"),
            )
            conn.commit()

        user_dir = Path(app.config["USER_DATA_ROOT"]) / user_id / "charts"
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / f"private-{profile_id}.json").write_text("personal", encoding="utf-8")

    def _table_count(self, table, column, value):
        with sqlite3.connect(app.config["BETA_DB_PATH"]) as conn:
            return conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",
                (value,),
            ).fetchone()[0]

    def test_delete_removes_only_target_user_data_and_is_idempotent(self):
        self._seed_user(USER_ID)
        self._seed_user(OTHER_USER_ID)
        payload = {"user_id": USER_ID, "request_id": "delete-user-test-1"}

        response = self.client.post("/api/v2/account/delete-data", json=payload)
        second_response = self.client.post("/api/v2/account/delete-data", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertEqual(response.get_json()["status"], "railway_user_data_deleted")
        self.assertFalse(Path(app.config["USER_DATA_ROOT"], USER_ID).exists())
        self.assertTrue(Path(app.config["USER_DATA_ROOT"], OTHER_USER_ID).exists())
        for table, column in (
            ("beta_profiles", "id"),
            ("beta_charts", "profile_id"),
            ("beta_chat_messages", "profile_id"),
            ("beta_feedback", "profile_id"),
            ("beta_usage_events", "profile_id"),
            ("beta_methodology_comparisons", "profile_id"),
        ):
            self.assertEqual(self._table_count(table, column, USER_ID), 0)
            self.assertEqual(self._table_count(table, column, OTHER_USER_ID), 1)

    def test_delete_rejects_invalid_user_id_without_removing_data(self):
        self._seed_user(USER_ID)

        response = self.client.post(
            "/api/v2/account/delete-data",
            json={"user_id": "../../unsafe", "request_id": "delete-user-test-2"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Path(app.config["USER_DATA_ROOT"], USER_ID).exists())
        self.assertEqual(self._table_count("beta_profiles", "id", USER_ID), 1)

    def test_delete_removes_all_profiles_owned_by_user(self):
        first_profile = "33333333-3333-4333-8333-333333333333"
        second_profile = "44444444-4444-4444-8444-444444444444"
        other_profile = "55555555-5555-4555-8555-555555555555"
        self._seed_user(USER_ID, first_profile)
        self._seed_user(USER_ID, second_profile)
        self._seed_user(OTHER_USER_ID, other_profile)

        response = self.client.post(
            "/api/v2/account/delete-data",
            json={"user_id": USER_ID, "request_id": "delete-owned-profiles-test"},
        )

        self.assertEqual(response.status_code, 200)
        for profile_id in (first_profile, second_profile):
            self.assertEqual(self._table_count("beta_profiles", "id", profile_id), 0)
            self.assertEqual(self._table_count("beta_charts", "profile_id", profile_id), 0)
            self.assertEqual(self._table_count("beta_methodology_comparisons", "profile_id", profile_id), 0)
        self.assertEqual(self._table_count("beta_profiles", "id", other_profile), 1)

    def test_delete_endpoint_requires_service_bearer_token(self):
        self._seed_user(USER_ID)
        app.config["LOCAL_ACCESS_ONLY"] = False
        app.config["API_TOKEN"] = "different-general-api-token"
        app.config["ACCOUNT_DELETE_TOKEN"] = "test-account-delete-token"
        payload = {"user_id": USER_ID, "request_id": "delete-user-test-3"}

        unauthorized = self.client.post("/api/v2/account/delete-data", json=payload)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertTrue(Path(app.config["USER_DATA_ROOT"], USER_ID).exists())

        general_token = self.client.post(
            "/api/v2/account/delete-data",
            json=payload,
            headers={"Authorization": "Bearer different-general-api-token"},
        )
        self.assertEqual(general_token.status_code, 401)
        self.assertTrue(Path(app.config["USER_DATA_ROOT"], USER_ID).exists())

        authorized = self.client.post(
            "/api/v2/account/delete-data",
            json=payload,
            headers={"Authorization": "Bearer test-account-delete-token"},
        )

        self.assertEqual(authorized.status_code, 200)
        self.assertFalse(Path(app.config["USER_DATA_ROOT"], USER_ID).exists())


if __name__ == "__main__":
    unittest.main()
