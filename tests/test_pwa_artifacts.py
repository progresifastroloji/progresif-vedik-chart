import hashlib
import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import (
    PWA_ARTIFACT_MANIFEST_VERSION,
    PWA_ARTIFACT_PROFILE_COMPACT,
    PWA_ARTIFACT_PROFILE_LEGACY,
    PWA_ARTIFACT_SCHEMA_VERSION,
    _beta_build_chat_draft,
    _beta_db,
    _beta_load_json,
    _pwa_full_markdown_documents,
    _strip_natal_model_instructions,
    app,
)
from methodology_orchestrator import (
    MAX_PROMPT_BYTES,
    _canonical_json,
    _model_request,
    compact_evidence,
    load_methodology_candidates,
)


OWNER_USER_ID = "55555555-5555-4555-8555-555555555555"
OTHER_USER_ID = "66666666-6666-4666-8666-666666666666"
CHART_ID = "77777777-7777-5777-8777-777777777777"


class PwaArtifactEndpointTest(unittest.TestCase):
    def setUp(self):
        self._old_beta_db_path = app.config["BETA_DB_PATH"]
        self._old_user_data_root = app.config["USER_DATA_ROOT"]
        self._old_testing = app.config.get("TESTING")
        self._tmp = tempfile.TemporaryDirectory()
        app.config["BETA_DB_PATH"] = f"{self._tmp.name}/beta.sqlite3"
        app.config["USER_DATA_ROOT"] = f"{self._tmp.name}/users"
        app.config["TESTING"] = True
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
        app.config["TESTING"] = self._old_testing
        self._tmp.cleanup()

    def _generate(self, owner_user_id=OWNER_USER_ID, artifact_profile=None):
        payload = {
            "owner_user_id": owner_user_id,
            "profile_id": OWNER_USER_ID,
            "chart_id": CHART_ID,
        }
        if artifact_profile:
            payload["artifact_profile"] = artifact_profile
        return self.client.post(
            "/api/v2/pwa/artifacts/generate",
            json=payload,
        )

    def test_generates_exact_artifact_set_and_replays_from_verified_manifest(self):
        first = self._generate()
        self.assertEqual(first.status_code, 200)
        payload = first.get_json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["replayed"])
        manifest = payload["manifest"]
        self.assertEqual(manifest["schema_version"], PWA_ARTIFACT_SCHEMA_VERSION)
        self.assertEqual(manifest["contract_version"], PWA_ARTIFACT_MANIFEST_VERSION)
        self.assertEqual(manifest["artifact_profile"], PWA_ARTIFACT_PROFILE_COMPACT)
        self.assertEqual(manifest["artifact_count"], 2)
        self.assertEqual(len(manifest["artifacts"]), 2)
        self.assertEqual(
            {item["code"] for item in manifest["artifacts"]},
            {"natal_interpretation", "transit_three_month"},
        )
        natal = next(item for item in manifest["artifacts"] if item["code"] == "natal_interpretation")
        self.assertEqual(natal["section_count"], 33)
        self.assertEqual(len(natal["sections"]), 33)
        self.assertEqual(natal["sections"][0]["id"], "gemini_reading_protocol")
        self.assertEqual(natal["sections"][-1]["id"], "technical_layer_status")
        self.assertEqual(len({item["id"] for item in natal["sections"]}), 33)
        self.assertEqual(natal["sections"][-1]["byte_end"], natal["byte_size"])

        root = (
            Path(app.config["USER_DATA_ROOT"])
            / OWNER_USER_ID
            / CHART_ID
            / PWA_ARTIFACT_SCHEMA_VERSION
            / PWA_ARTIFACT_PROFILE_COMPACT
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
            f"?profile={PWA_ARTIFACT_PROFILE_COMPACT}"
        )
        self.assertEqual(download.status_code, 200)
        download_data = download.data
        self.assertEqual(
            download.headers["X-Artifact-Sha256"],
            hashlib.sha256(download_data).hexdigest(),
        )
        self.assertEqual(json.loads(download_data)["birth"]["person"]["id"], OWNER_USER_ID)
        download.close()

    def test_legacy_profile_remains_available_as_server_side_rollback(self):
        response = self._generate(artifact_profile=PWA_ARTIFACT_PROFILE_LEGACY)

        self.assertEqual(response.status_code, 200)
        manifest = response.get_json()["manifest"]
        self.assertEqual(manifest["artifact_profile"], PWA_ARTIFACT_PROFILE_LEGACY)
        self.assertEqual(manifest["artifact_count"], 15)
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
            / PWA_ARTIFACT_PROFILE_LEGACY
        )
        self.assertTrue((root / "manifest.json").is_file())

    def test_real_chart_question_contexts_stay_below_model_gateway_limit(self):
        with closing(_beta_db()) as conn:
            row = conn.execute(
                "SELECT chart_json FROM beta_charts WHERE id = ?",
                (CHART_ID,),
            ).fetchone()
        chart = _beta_load_json(row["chart_json"])
        methodology = load_methodology_candidates()[0]

        for question in (
            "Genel haritamı zengin biçimde yorumla",
            "Kariyerimde güçlü ve zorlayıcı yanlarım neler?",
            "Önümüzdeki üç ay kariyerimde neler öne çıkıyor?",
        ):
            draft = _beta_build_chat_draft(question, chart)
            evidence = compact_evidence(draft)
            request, _ = _model_request(methodology, evidence)
            self.assertLess(
                len(_canonical_json(request).encode("utf-8")),
                MAX_PROMPT_BYTES,
            )

    def test_rejects_cross_user_artifact_generation(self):
        response = self._generate(OTHER_USER_ID)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_code"], "pwa_artifact_ownership_mismatch")

    def test_full_source_reader_accepts_verified_legacy_v1_layout(self):
        legacy_root = (
            Path(app.config["USER_DATA_ROOT"])
            / OWNER_USER_ID
            / CHART_ID
            / "vedic-pwa-artifacts-v1"
        )
        legacy_root.mkdir(parents=True)
        natal = b"# Legacy natal\n"
        transit = b"# Legacy transit\n"
        (legacy_root / "main-chart.md").write_bytes(natal)
        (legacy_root / "transit-three-month.md").write_bytes(transit)
        manifest = {
            "owner_user_id": OWNER_USER_ID,
            "chart_id": CHART_ID,
            "artifacts": [
                {
                    "code": "main_chart",
                    "filename": "main-chart.md",
                    "sha256": hashlib.sha256(natal).hexdigest(),
                },
                {
                    "code": "transit_three_month",
                    "filename": "transit-three-month.md",
                    "sha256": hashlib.sha256(transit).hexdigest(),
                },
            ],
        }
        (legacy_root / "manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

        loaded = _pwa_full_markdown_documents(
            OWNER_USER_ID,
            CHART_ID,
            include_transit=True,
        )

        self.assertEqual(
            [item["filename"] for item in loaded["documents"]],
            ["main-chart.md", "transit-three-month.md"],
        )
        self.assertEqual(loaded["documents"][0]["content"], natal.decode())
        self.assertEqual(loaded["documents"][1]["content"], transit.decode())

    def test_natal_sanitizer_removes_numbered_model_instruction_sections(self):
        source = (
            "# Natal\n\n"
            "## 1. Gemini Okuma Protokolü\n\n"
            "1. Dosyayı böyle oku.\n\n"
            "## 2. Kullanım Sınırı\n\n"
            "- Eski model talimatı.\n\n"
            "## 3. Lagna\n\n"
            "- Oğlak.\n"
        )

        cleaned = _strip_natal_model_instructions(source)

        self.assertNotIn("Gemini Okuma Protokolü", cleaned)
        self.assertNotIn("Kullanım Sınırı", cleaned)
        self.assertIn("## Paket Kapsamı", cleaned)
        self.assertIn("## Veri Sınırları", cleaned)
        self.assertIn("## 3. Lagna", cleaned)


if __name__ == "__main__":
    unittest.main()
