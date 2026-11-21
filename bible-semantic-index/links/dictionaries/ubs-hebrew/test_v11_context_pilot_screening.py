#!/usr/bin/env python3
"""Reject unproven contextual choices and fabricated source-witness judgments."""
import runpy,unittest
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name("verify_v11_context_pilot_screening.py")))
class TestScreening(unittest.TestCase):
    def test_invalid_records_rejected(self):
        with self.assertRaises((ValueError,KeyError)):
            m["verify"]({"status":"PUBLIC"}, {})
    def test_report_categories_conserve_sample(self):
        expected=m["EXPECTED"]
        self.assertEqual(sum(expected.values()),72)
        self.assertEqual(expected["apparent_lexical_sense_or_granularity_conflict"],3)
        self.assertEqual(expected["context_or_phrase_boundary_uncertain"],3)
        self.assertEqual(expected["no_obvious_conflict_in_short_source_context_NOT_independent_validation"],66)
if __name__=="__main__":
    unittest.main()
