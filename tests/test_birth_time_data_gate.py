import unittest

from topic_pack_contract import resolve_data_gate


class BirthTimeDataGateTest(unittest.TestCase):
    def _unknown_chart(self):
        return {
            "birth": {"time_confidence": "unknown"},
            "data_quality": {
                "birth_time_confidence": "unknown",
                "birth_time_declaration": "unknown",
                "customer_declaration_basis": True,
                "accepted_as_rectified": False,
                "reference_frame": "chandra_lagna",
                "calculation_reference_time": "12:00",
                "lagna_interpretation_confidence": "none",
                "reference_lagna_interpretation_confidence": "high",
                "house_interpretation_confidence": "high",
                "planet_sign_interpretation_confidence": "high",
                "varga_interpretation_confidence": {
                    "D1": "very_low",
                    "D9": "medium",
                    "D10": "very_low",
                },
                "supported_vargas": ["D9"],
            },
        }

    def test_unknown_time_allows_medium_d9_with_chandra_lagna(self):
        gate = resolve_data_gate(self._unknown_chart(), "P01-MAR")
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["confidence_cap"], "medium")
        self.assertEqual(gate["reference_frame"], "chandra_lagna")

    def test_unknown_time_blocks_very_low_required_varga(self):
        gate = resolve_data_gate(self._unknown_chart(), "P03-CAR")
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["required_conflict"], ["D10 (güven: very_low)"])


if __name__ == "__main__":
    unittest.main()
