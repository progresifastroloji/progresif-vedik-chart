import copy
import hashlib
import json
import unittest
from datetime import datetime, timezone

from app import (
    _beta_build_chart, _beta_options, _build_natal_interpretation_package_markdown,
    _expert_shadbala_note, _natal_remove_empty_tables, _refresh_runtime_dasha,
    _beta_selected_natal_sections, _natal_evidence_valid_until, _build_natal_markdown,
)
from natal_evidence import _library, nakshatra_character


class NatalEvidencePackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.birth = {"year": 1978, "month": 5, "day": 28, "hour": 0, "minute": 15,
                     "timezone_id": "Europe/Istanbul", "lat": 40.7654, "lon": 29.9408,
                     "place": "İzmit", "time_confidence": "rectified"}
        cls.chart = _beta_build_chart({"name": "Test"}, cls.birth, _beta_options({}))

    def test_four_character_anchors_have_meanings_and_distinct_complete_chains(self):
        anchors = self.chart["vedic_spine"]["anchors"][:4]
        self.assertEqual([a["anchor"] for a in anchors], ["Lagna", "LagnaLord", "Moon", "Sun"])
        self.assertEqual([a["position"]["nakshatra"] for a in anchors], ["Shravana", "Magha", "Dhanishta", "Rohini"])
        for anchor in anchors:
            meaning = anchor["position"]["nakshatra_character"]
            self.assertEqual(meaning["status"], "available")
            self.assertTrue(meaning["pada_meaning"])
            for key in ("nakshatra_lord_chain", "dispositor_chain"):
                self.assertIn(anchor[key]["termination"], {"cycle", "self_lord"})
                names = [s["planet"] for s in anchor[key]["steps"]]
                self.assertEqual(len(names), len(set(names)))

    def test_all_27_existing_meanings_and_four_padas_resolve(self):
        for entry in _library()["entries"]:
            for pada in range(1, 5):
                meaning = nakshatra_character({"name": entry["latin"], "pada": pada}, "Moon")
                self.assertEqual(meaning["status"], "available")
                self.assertTrue(meaning["pada_meaning"], entry["latin"])

    def test_historical_snapshot_upgrade_refreshes_dasha_and_strength_without_mutating_source(self):
        old = copy.deepcopy(self.chart)
        old.pop("vedic_spine")
        old["vargas"].pop("D16")
        for planet in old["shadbala"]["planets"]:
            planet.pop("professional_total", None)
        before = json.dumps(old, sort_keys=True)
        reference = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
        fresh = _refresh_runtime_dasha(old, reference, strict=True)
        self.assertEqual(before, json.dumps(old, sort_keys=True))
        self.assertIn("D16", fresh["vargas"])
        self.assertEqual(fresh["dashas"]["vimshottari"]["current_active_reference_utc"], reference.isoformat(timespec="seconds"))
        self.assertTrue(all(p["professional_total"]["strength_ratio"] is not None for p in fresh["shadbala"]["planets"]))
        self.assertEqual(fresh["birth"]["time_confidence"], "rectified")

    def test_rectified_is_preserved_without_relabeling_other_declarations(self):
        self.assertEqual(self.chart["birth"]["time_confidence_label"], "biliniyor, rektifikasyonlu")
        self.assertTrue(self.chart["data_quality"]["accepted_as_rectified"])
        for declaration in ("exact", "approximate", "unknown"):
            chart = _beta_build_chart({}, dict(self.birth, time_confidence=declaration), _beta_options({}))
            self.assertNotEqual(chart["birth"]["time_confidence"], "rectified")
            if declaration == "unknown":
                self.assertEqual(chart["lagna"]["reference_frame"], "chandra_lagna")

    def test_missing_professional_strength_is_not_weakness(self):
        note = _expert_shadbala_note({"total_score": 500})
        self.assertIn("hesaplanmamış", note)
        self.assertNotIn("Minimumun altinda", note)

    def test_section_order_headers_byte_indexes_and_absence_reasons(self):
        content, index = _build_natal_interpretation_package_markdown(self.chart, "Test", "PWA")
        self.assertEqual(len(index), 33)
        self.assertEqual(len({i["id"] for i in index}), 33)
        ids = [i["id"] for i in index]
        self.assertLess(ids.index("vedic_spine"), ids.index("d1_planets"))
        self.assertLess(ids.index("varga_confidence"), ids.index("varga_tables"))
        self.assertIn("### Güneş\n", content)
        self.assertLess(content.index("D9 Navamsha Full Tablo"), content.index("D2 Hora Full Tablo"))
        self.assertNotIn("Kartografi Çekirdeği", content)
        self.assertNotIn("Okunmuş Teknik Zincir", content)
        self.assertNotIn("Moon → Moon", content)
        self.assertIn("Lagna → Moon → Mars", content)
        events_section = content.split("## 32. Kayıtlı Yaşam Olayları\n", 1)[1].split("## 33.", 1)[0]
        self.assertNotIn("|", events_section)
        self.assertIn("veri kaynağı", events_section)
        legacy = _build_natal_markdown(self.chart, "Test", "PWA")
        self.assertLess(legacy.index("Karakter önceliği"), legacy.index("## Lagna\n"))
        for name in ("Shravana", "Magha", "Dhanishta", "Rohini"):
            self.assertIn(name, legacy)
        encoded = content.encode()
        for item in index:
            block = encoded[item["byte_start"]:item["byte_end"]]
            self.assertEqual(len(block), item["byte_size"])
            self.assertEqual(hashlib.sha256(block).hexdigest(), item["sha256"])
        empty = _natal_remove_empty_tables("| A | B |\n| --- | --- |")
        self.assertIn("not_available", empty)
        self.assertNotIn("|", empty)
        timing = _beta_selected_natal_sections(self.chart, "career", timing_mode=True)
        self.assertIn("varga_confidence", [s["id"] for s in timing])

    def test_registered_events_are_preserved_but_absence_is_not_a_table(self):
        content, _ = _build_natal_interpretation_package_markdown(
            self.chart, "Test", "PWA", rectification_record={"events": []},
        )
        section = content.split("## 32. Kayıtlı Yaşam Olayları\n", 1)[1].split("## 33.", 1)[0]
        self.assertNotIn("|", section)
        self.assertIn("Kayıtlı yaşam olayı yok", section)
        content, _ = _build_natal_interpretation_package_markdown(
            self.chart, "Test", "PWA", rectification_record={"events": [
                {"date": "2026-01-01", "label": "Test olayı", "documented": True}
            ]},
        )
        section = content.split("## 32. Kayıtlı Yaşam Olayları\n", 1)[1].split("## 33.", 1)[0]
        self.assertIn("| 2026-01-01 | Test olayı |", section)

    def test_cache_expires_at_short_period_boundary(self):
        chart = copy.deepcopy(self.chart)
        # An expired boundary must invalidate reuse, even within the one hour TTL.
        chart["dashas"]["vimshottari"]["current_active"]["prana"]["actual_end_jd"] = 2461315.5
        self.assertLess(_natal_evidence_valid_until(chart), datetime.now(timezone.utc).isoformat(timespec="seconds"))


if __name__ == "__main__":
    unittest.main()
