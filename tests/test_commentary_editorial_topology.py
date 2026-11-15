"""Invented-only regression tests for generic native commentary editorial topology."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_editorial_topology import (
    NativeCommentaryEditorialTopology, _heading_span
)


class OriginalNativeEditorialTopologyTests(unittest.TestCase):
    def test_title_number_parser_rejects_ambiguous_or_descending_scopes(self):
        self.assertEqual(_heading_span("Verses 4–6"), (4, 5, 6))
        self.assertEqual(_heading_span("Verse 2, 5"), (2, 5))
        for heading in ("Verse 0", "Verses 6-2", "Verses 7, 7",
                        "Verse 177", "Some prose in verse 3"):
            with self.subTest(heading=heading):
                self.assertIsNone(_heading_span(heading))

    def test_synthetic_noncontiguous_and_cross_chapter_reuse_only_reported(self):
        scan = NativeCommentaryEditorialTopology()
        source = b"<title>Verses 1-2</title><div>Invented passage A.</div>"
        for ref in ("Gen.1.1", "Gen.1.2", "Gen.1.5", "Gen.2.1"):
            scan.observe("K", ref, source)
        scan.observe(
            "K", "Gen.1.3",
            b"<title>Verses 9-10</title><div>Invented passage B.</div>",
        )
        scan.observe(
            "K", "Gen.1.4",
            b"<title>Verses 4, 5</title><title>Verse 6</title>"
            b"<div>Invented passage C.</div>",
        )
        scan.observe("I", "Gen.1", b"<title>Invented introduction.</title>")
        scan.observe("U", "TOP", b"opaque")
        receipt = scan.report({"Gen.1": 5, "Gen.2": 5})
        self.assertEqual(receipt["original_native_K_rows_seen"], 6)
        self.assertEqual(receipt["original_native_I_rows_seen"], 1)
        self.assertEqual(receipt["original_native_TOP_rows_seen"], 1)
        self.assertEqual(receipt["distinct_original_K_raw_bodies"], 3)
        count = receipt["candidate_counts"]
        self.assertEqual(count["disconnected_same_body_within_chapter"], 1)
        self.assertEqual(count["identical_raw_body_reused_in_multiple_chapters"], 1)
        self.assertEqual(count["distinct_numbered_xml_titles_in_same_body"], 1)
        self.assertEqual(count["first_numeric_title_vs_first_native_slot_disagree"], 1)
        self.assertEqual(count["numbered_title_outside_native_chapter_verse_limit"], 2)
        self.assertEqual(
            receipt["candidate_samples"]["disconnected_same_body_within_chapter"][0]
            ["separate_native_runs"], 2,
        )
        self.assertTrue(receipt["candidate_is_not_an_editorial_defect_verdict"])
        self.assertFalse(receipt["original_words_or_xml_in_report"])
        self.assertFalse(receipt["release_authorized"])
        self.assertNotIn("Invented passage", str(receipt))

    def test_missing_or_invalid_registry_rejected(self):
        scan = NativeCommentaryEditorialTopology()
        scan.observe("K", "Gen.1.1", b"<title>Verse 1</title>Invented content")
        with self.assertRaises(ValueError):
            scan.report({})
        with self.assertRaises(ValueError):
            scan.report({"Gen.1": 0})

    def test_unparseable_or_duplicate_native_entries_fail_closed(self):
        scan = NativeCommentaryEditorialTopology()
        for ref, original in (
            ("Gen.1.1", b"<title>Unclosed"),
            ("Gen.1.1", b"<!DOCTYPE x [ <!ENTITY z SYSTEM 'file:///tmp/z'> ]>"
                           b"<title>&z;</title>"),
            ("not-a-verse", b"<title>Verse 1</title>"),
        ):
            with self.subTest(key=ref, raw=original[:12]):
                with self.assertRaises(ValueError):
                    scan.observe("K", ref, original)
        scan.observe("K", "Gen.1.1", b"<title>Verse 1</title>A")
        scan.observe("K", "Gen.1.1", b"<title>Verse 1</title>A")
        with self.assertRaises(ValueError):
            scan.report({"Gen.1": 10})

    def test_single_title_and_contiguous_aliases_are_not_flagged(self):
        scan = NativeCommentaryEditorialTopology()
        body = b"<title>Verses 1-3</title><div>Invented ordinary block</div>"
        for n in (1, 2, 3):
            scan.observe("K", f"Gen.1.{n}", body)
        report = scan.report({"Gen.1": 31})
        self.assertEqual(report["candidate_counts"], {})
        self.assertEqual(report["original_native_K_rows_seen"], 3)


if __name__ == "__main__":
    unittest.main()
