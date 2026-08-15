import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import (
    PWA_ARTIFACT_DEFAULT_PROFILE,
    app,
    _beta_build_chat_draft,
    _pwa_artifact_set_root,
    _pwa_get_or_create_transit_runtime_cache,
    _pwa_write_transit_runtime_cache,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"
PROFILE_ID = "33333333-3333-4333-8333-333333333333"
CHART_ID = "chart-transit-cache-test"


def _planet(name, sign="Aries"):
    return {
        "name": name,
        "sign": sign,
        "sign_tr": "Koç",
        "sign_index": 0,
        "degree_str": "10° 00' 00\"",
        "nakshatra": "Ashwini",
        "nakshatra_lord": "Ketu",
        "nakshatra_pada": 1,
        "house_from_lagna": 1,
        "house_from_moon": 12,
        "retrograde": False,
        "speed_status": "direct",
        "natal_planets_in_sign": [],
        "ashtakavarga": {
            "sav": 30,
            "bav": 4,
            "sav_support_level": "supportive",
            "bav_support_level": "average",
        },
    }


def _day(day="2026-08-15", requested_time="12:00"):
    return {
        "date": day,
        "reference_datetime_utc": f"{day}T09:00:00+00:00",
        "requested_time": requested_time,
        "requested_tz_offset": 3,
        "active_dasha_path": ["Saturn", "Venus", "Jupiter"],
        "active_dasha": [{"level": "maha", "lord": "Saturn"}],
        "panchanga": {"tithi": {"name": "Shukla Dvitiya"}},
        "planets": [_planet("Sun"), _planet("Moon", "Taurus")],
        "natal_contacts": [{
            "transit_planet": "Moon",
            "natal_planet": "Moon",
            "contact_type": "degree_orb",
            "orb": 0.5,
            "sign": "Taurus",
            "house_from_lagna": 2,
            "house_from_moon": 1,
        }],
        "dasha_cross_reference": {"status": "available"},
        "special_checks": {"moon": {"status": "checked"}},
    }


def _pack(day="2026-08-15", requested_time="12:00", period="three_month"):
    return {
        "period": {
            "type": period,
            "range_start": day,
            "range_end": "2026-11-14" if period == "three_month" else day,
            "day_count": 92 if period == "three_month" else 1,
        },
        "natal": {"lagna_sign": "Aries", "moon_sign": "Taurus"},
        "days": [_day(day, requested_time)],
    }


class TransitQuestionRoutingTest(unittest.TestCase):
    def setUp(self):
        self._old_user_data_root = app.config["USER_DATA_ROOT"]
        self._tmp = tempfile.TemporaryDirectory()
        app.config["USER_DATA_ROOT"] = self._tmp.name
        self.chart = {
            "birth": {
                "person": {"id": PROFILE_ID, "name": "Test"},
                "timezone_id": "Europe/Istanbul",
            },
            "lagna": {"sign": "Aries"},
            "dashas": {
                "vimshottari": {
                    "current_active": {
                        "path": ["Saturn", "Venus", "Jupiter"],
                        "maha": "Saturn",
                    },
                },
            },
            "missing": [],
            "data_quality": {"status": "complete"},
        }

    def tearDown(self):
        app.config["USER_DATA_ROOT"] = self._old_user_data_root
        self._tmp.cleanup()

    def _write_manifest(self):
        root = _pwa_artifact_set_root(
            OWNER_ID,
            CHART_ID,
            PWA_ARTIFACT_DEFAULT_PROFILE,
        )
        root.mkdir(parents=True, exist_ok=True)
        (root / "manifest.json").write_text(json.dumps({
            "owner_user_id": OWNER_ID,
            "profile_id": PROFILE_ID,
            "chart_id": CHART_ID,
            "artifact_profile": PWA_ARTIFACT_DEFAULT_PROFILE,
            "artifacts": [{"code": "transit_three_month"}],
        }), encoding="utf-8")

    @patch("app._pwa_transit_pack")
    def test_stored_three_month_cache_is_reused_without_recalculation(self, build_pack):
        self._write_manifest()
        stored = _pack()
        _pwa_write_transit_runtime_cache(
            OWNER_ID,
            PROFILE_ID,
            CHART_ID,
            PWA_ARTIFACT_DEFAULT_PROFILE,
            self.chart,
            stored,
        )

        pack, source, regenerated = _pwa_get_or_create_transit_runtime_cache(
            OWNER_ID,
            PROFILE_ID,
            CHART_ID,
            PWA_ARTIFACT_DEFAULT_PROFILE,
            self.chart,
            "Test",
            "2026-08-15",
            "2026-08-15",
        )

        self.assertEqual(pack, stored)
        self.assertEqual(source, "stored_runtime_artifact")
        self.assertFalse(regenerated)
        build_pack.assert_not_called()

    @patch("app._beta_instant_transit_pack")
    @patch("app._pwa_get_or_create_transit_runtime_cache")
    def test_instant_question_reads_day_and_calculates_only_one_snapshot(
        self,
        get_cache,
        instant_pack,
    ):
        get_cache.return_value = (_pack(), "stored_runtime_artifact", False)
        instant_pack.return_value = _pack(
            requested_time="18:42",
            period="daily",
        )
        routing = {
            "mode": "active",
            "status": "model_selected",
            "agreement": False,
            "legacy": {},
            "model": {},
            "selected": {
                "contract_version": "vedic-question-route-v1",
                "primary_topic": "wellbeing",
                "time_scope": "instant",
                "timing_required": True,
                "target_start": None,
                "target_end": None,
                "target_datetime": "2026-08-15T18:42:00+03:00",
                "required_evidence": [
                    "natal_core", "natal_emotional_core", "active_dasha",
                    "stored_transit_days", "current_transit_snapshot",
                    "moon_and_panchanga", "transit_natal_contacts",
                    "ashtakavarga",
                ],
                "sensitivity": "mental_wellbeing",
                "confidence": "high",
                "clarification_required": False,
                "clarification_question": None,
            },
        }

        draft = _beta_build_chat_draft(
            "Tam şu anda neden böyle hissediyorum?",
            self.chart,
            routing=routing,
            owner_user_id=OWNER_ID,
            profile_id=PROFILE_ID,
            chart_id=CHART_ID,
        )

        transits = draft["evidence"]["transits"]
        self.assertEqual(draft["subject_topic"], "wellbeing")
        self.assertEqual(draft["question_route"]["time_scope"], "instant")
        self.assertFalse(transits["three_month_recalculated_for_question"])
        self.assertEqual(len(transits["daily_records"]), 1)
        self.assertEqual(len(transits["daily_records"][0]["planets"]), 2)
        self.assertEqual(
            transits["daily_records"][0]["panchanga"]["tithi"]["name"],
            "Shukla Dvitiya",
        )
        self.assertEqual(transits["instant_snapshot"]["requested_time"], "18:42")
        self.assertTrue(
            any("psikolojik/psikiyatrik teşhis" in note for note in draft["safety_notes"])
        )
        get_cache.assert_called_once()
        instant_pack.assert_called_once()


if __name__ == "__main__":
    unittest.main()
