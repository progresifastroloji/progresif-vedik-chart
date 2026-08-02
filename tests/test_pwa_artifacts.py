import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app import PWA_ARTIFACT_SCHEMA_VERSION, app


OWNER_USER_ID = "55555555-5555-4555-8555-555555555555"
OTHER_USER_ID = "66666666-6666-4666-8666-666666666666"
CHART_ID = "77777777-7777-5777-8777-777777777777"


class PwaArtifactEndpointTest(unittest.TestCase):
    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_user_data_root = app.config["USER_DATA_ROOT"]
        self._tmp = tempfile.TemporaryDirectory()
        app.config["BETA_DB_PATH"] = f"{self._tmp.name}/beta.sqlite3"
        app.config["USER_DATA_ROOT"] = f"{self._tmp.name}/users"
        self.client = app.test_client()

        response = self.client.post(
            "/api/v2/beta/profile",
            json={
                "owner_user_id": OWNER_USER_ID,
                "profile_id": OWNER_USER_ID,
                "chart_id": CHART_ID,
                "person": {"name": "PWA Test", "group": "PWA"},
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
            },
        )
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        app.config["BETA_DB_PATH"] = self._old_beta_db_path
        app.config["USER_DATA_ROOT"] = self._old_user_data_root
        self._tmp.cleanup()

    def _generate(self, owner_user_id=OWNER_USER_ID):
        return self.client.post(
            "/api/v2/pwa/artifacts/generate",
            json={
                "owner_user_id": owner_user_id,
                "profile_id": OWNER_USER_ID,
                "chart_id": CHART_ID,
            },
        )

    def test_generates_exact_artifact_set_and_replays_from_verified_manifest(self):
        first = self._generate()
        self.assertEqual(first.status_code, 200)
        payload = first.get_json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["replayed"])
        manifest = payload["manifest"]
        self.assertEqual(manifest["schema_version"], PWA_ARTIFACT_SCHEMA_VERSION)
        self.assertEqual(manifest["artifact_count"], 15)
        self.assertEqual(len(manifest["artifacts"]), 15)
        self.assertEqual(
            {item["code"] for item in manifest["artifacts"]},
            {
                "main_chart", "career", "health", "family", "education",
                "relocation", "finance", "relationship", "character",
                "spiritual", "varshaphala", "legal", "planet_roles",
                "session", "transit_three_month",
            },
        )

        root = (
            Path(app.config["USER_DATA_ROOT"])
            / OWNER_USER_ID
            / CHART_ID
            / PWA_ARTIFACT_SCHEMA_VERSION
        )
        self.assertTrue((root / "manifest.json").is_file())
        self.assertTrue((root / "canonical-snapshot.json").is_file())
        for item in manifest["artifacts"]:
            content = (root / item["filename"]).read_bytes()
            self.assertEqual(len(content), item["byte_size"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])

        replay = self._generate()
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.get_json()["replayed"])
        self.assertEqual(replay.get_json()["manifest_sha256"], payload["manifest_sha256"])

        download = self.client.get(
            f"/api/v2/pwa/artifacts/{OWNER_USER_ID}/{CHART_ID}/canonical_snapshot"
        )
        self.assertEqual(download.status_code, 200)
        download_data = download.data
        self.assertEqual(
            download.headers["X-Artifact-Sha256"],
            hashlib.sha256(download_data).hexdigest(),
        )
        self.assertEqual(json.loads(download_data)["birth"]["person"]["id"], OWNER_USER_ID)
        download.close()

    def test_rejects_cross_user_artifact_generation(self):
        response = self._generate(OTHER_USER_ID)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_code"], "pwa_artifact_ownership_mismatch")


if __name__ == "__main__":
    unittest.main()
