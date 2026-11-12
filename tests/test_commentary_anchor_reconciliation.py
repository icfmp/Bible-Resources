"""Offline whole-anchor source→native-slot reconnaissance, never text parity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from commentary_anchor_reconciliation import parse_source_markers, reconcile_occupied_slots
from commentary_native_inventory import parse_index
from pilot_preflight import PilotError


class CommentaryAnchorReconTests(unittest.TestCase):
    def source(self) -> bytes:
        return (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b"<ThML><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.3'/>"
            b"<p>ORIGINAL PRIVATE WORDS, NEVER INCLUDED IN RECEIPT</p>"
            b"<scripCom osisRef='Bible:Gen.1.2'/>"
            b"<scripCom osisRef='Bible:Gen.2'/>"
            b"<scripCom osisRef='Bible:John.3.15-John.3.17'/>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.3'/>"
            b"<scripCom osisRef='Not qualified'/>"
            b"</div2></div1></ThML>" + b" " * 1100
        )

    def rows(self):
        return [("K","Gen.1.2"), ("K","Gen.2.1"),
                ("K","John.3.15"), ("K","John.3.17"),
                ("I","Gen.2"), ("U","TOP:1")]

    def test_complete_source_markers_and_native_candidates_without_original_text(self):
        refs, source = parse_source_markers(self.source())
        self.assertEqual(source["source_marker_total"], 6)
        self.assertEqual(source["source_duplicate_osisref_count"], 1)
        self.assertEqual(source["source_markers_by_kind"]["range"], 3)
        self.assertEqual(source["source_markers_by_kind"]["verse"], 1)
        self.assertEqual(source["source_markers_by_kind"]["chapter"], 1)
        self.assertEqual(source["source_markers_by_kind"]["unreviewed"], 1)
        recon = reconcile_occupied_slots(refs, self.rows())
        self.assertEqual(recon["source_markers_with_candidate_native_occupied_slot"], 5)
        self.assertEqual(recon["source_markers_without_candidate_native_occupied_slot"], 0)
        self.assertEqual(recon["source_markers_with_unreviewed_reference_grammar"], 1)
        self.assertEqual(recon["distinct_stock_numbered_slots_inside_any_original_span"], 4)
        self.assertEqual(recon["john_3_16_original_markers_covering_reference"], 1)
        self.assertFalse(recon["john_3_16_exact_native_slot_occupied"])
        self.assertFalse(recon["comments_and_content_equivalence_verified"])
        self.assertFalse(recon["copyright_and_redistribution_approved"])
        report = json.dumps({"source":source, "reconciliation":recon})
        self.assertNotIn("ORIGINAL PRIVATE WORDS", report)
        self.assertNotIn("Not qualified", report)
        self.assertNotIn("Bible:Gen", report)

    def test_unmatched_reference_retains_source_location_and_sha_not_quoted_text(self):
        raw = self.source().replace(b"Bible:Gen.1.2", b"Bible:Gen.17.77")
        refs, _ = parse_source_markers(raw)
        report = reconcile_occupied_slots(refs, self.rows())
        self.assertEqual(report["source_markers_without_candidate_native_occupied_slot"], 1)
        self.assertEqual(report["unmatched_candidate_anchor_samples"][0]["source_marker"], 2)
        self.assertNotIn("Gen.17.77", json.dumps(report))
        self.assertEqual(len(report["unmatched_candidate_anchor_samples"][0]["source_reference_sha256"]), 64)

    def test_wrong_native_book_is_not_silently_mapped_to_nearest_book(self):
        refs, _ = parse_source_markers(self.source().replace(b"Bible:John.3.15-John.3.17",
                                                              b"Bible:Jhn.3.15-Jhn.3.17"))
        report = reconcile_occupied_slots(refs, self.rows())
        self.assertEqual(report["source_markers_without_candidate_native_occupied_slot"], 1)

    def test_dtd_external_entity_blocks_no_incomplete_inventory_allowed(self):
        source = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE ThML [<!ENTITY private SYSTEM "file:///etc/passwd">]>'
            b'<ThML><scripCom osisRef="Bible:Gen.1.1"/>&private;</ThML>'
            + b" " * 1100
        )
        with self.assertRaises(PilotError):
            parse_source_markers(source)

    def test_native_in_memory_rows_only_when_explicitly_requested(self):
        payload = (b"M\tTestCom\tKJV\t1.9.0\tzCom\n"
                   b"K\tGen.1.1\nS\t31000\t1\t0\t0\n")
        minimal = parse_index(payload, "TestCom")
        full = parse_index(payload, "TestCom", include_rows=True)
        self.assertNotIn("native_occupied_rows_for_in_memory_reconciliation", minimal)
        self.assertEqual(full["native_occupied_rows_for_in_memory_reconciliation"], [("K", "Gen.1.1")])
        self.assertEqual(minimal["ordered_occupied_key_sha256"], full["ordered_occupied_key_sha256"])


if __name__=="__main__":
    unittest.main()
