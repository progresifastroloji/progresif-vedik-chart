import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import app


class DeploymentSecurityTest(unittest.TestCase):
    def setUp(self):
        self.previous_config = {
            "API_TOKEN": app.config.get("API_TOKEN"),
            "LOCAL_ACCESS_ONLY": app.config.get("LOCAL_ACCESS_ONLY"),
            "PLACES_DB_PATH": app.config.get("PLACES_DB_PATH"),
        }
        self.temp_dir = tempfile.TemporaryDirectory()
        self.catalog = Path(self.temp_dir.name) / "places.sqlite3"
        with closing(sqlite3.connect(self.catalog)) as conn:
            conn.execute("CREATE TABLE catalog_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute(
                "INSERT INTO catalog_metadata(key, value) VALUES ('place_count', '1')"
            )
            conn.commit()
        app.config["PLACES_DB_PATH"] = str(self.catalog)
        self.client = app.test_client()

    def tearDown(self):
        app.config.update(self.previous_config)
        self.temp_dir.cleanup()

    def test_healthcheck_is_public_when_catalog_is_ready(self):
        app.config["LOCAL_ACCESS_ONLY"] = False
        app.config["API_TOKEN"] = ""

        response = self.client.get(
            "/healthz",
            environ_base={"REMOTE_ADDR": "203.0.113.5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ready")

    def test_healthcheck_fails_when_catalog_is_missing(self):
        app.config["PLACES_DB_PATH"] = str(Path(self.temp_dir.name) / "missing.sqlite3")

        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.get_json()["catalog_ready"])

    def test_public_mode_fails_closed_without_configured_token(self):
        app.config["LOCAL_ACCESS_ONLY"] = False
        app.config["API_TOKEN"] = ""

        response = self.client.get("/api/v1/places/search?q=istan")

        self.assertEqual(response.status_code, 503)

    def test_public_mode_rejects_missing_or_wrong_token(self):
        app.config["LOCAL_ACCESS_ONLY"] = False
        app.config["API_TOKEN"] = "correct-secret"

        missing = self.client.get("/api/v1/places/search?q=istan")
        wrong = self.client.get(
            "/api/v1/places/search?q=istan",
            headers={"Authorization": "Bearer wrong-secret"},
        )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(missing.headers["WWW-Authenticate"], "Bearer")

    def test_public_mode_accepts_correct_bearer_token(self):
        app.config["LOCAL_ACCESS_ONLY"] = False
        app.config["API_TOKEN"] = "correct-secret"

        response = self.client.get(
            "/protected-route-that-does-not-exist",
            headers={"Authorization": "Bearer correct-secret"},
        )

        self.assertEqual(response.status_code, 404)

    def test_local_mode_keeps_loopback_access(self):
        app.config["LOCAL_ACCESS_ONLY"] = True
        app.config["API_TOKEN"] = ""

        response = self.client.get("/api/v1/places/search?q=istan")

        self.assertNotIn(response.status_code, {401, 403})


if __name__ == "__main__":
    unittest.main()
