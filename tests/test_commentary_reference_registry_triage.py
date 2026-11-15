"""Invented-only original SWORD reference target / registry tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_reference_registry_triage import (
    OriginalCommentaryReferenceRegistryTriage,
    classify_original_reference_target,
)


class NativeCommentaryReferenceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.verses = {"Gen.1.1", "Gen.1.2", "Gen.1.3"}
        self.chapters = {"Gen.1": 3}

    def test_plain_and_bible_qualified_literal_targets(self):
        expected = {
            "Bible:Gen.1.1": "EXACT_SINGLE_VERSE_IN_REGISTRY",
            "Gen.1.1-2": "EXACT_VERSE_RANGE_ENDPOINTS_IN_REGISTRY",
            "Bible:Gen.1.1-Gen.1.3": "EXACT_VERSE_RANGE_ENDPOINTS_IN_REGISTRY",
            "Gen.1": "EXACT_CHAPTER_IN_REGISTRY",
            "Gen": "BOOK_ONLY_NOT_VERSE_VALIDATED",
            "Gen.1.9": "SIMPLE_SINGLE_VERSE_NOT_IN_REGISTRY",
            "Gen.3": "SIMPLE_CHAPTER_NOT_IN_REGISTRY",
            "Gen.1.1-9": "SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY",
            "Gen.1.3-Gen.1.1": "REVERSED_SAME_CHAPTER_VERSE_RANGE",
            "Bible:Gen.1.1,Gen.1.3": "COMPLEX_OR_EXTENDED_OSIS_TARGET_UNREVIEWED",
            "OtherWork:Gen.1.1": "COMPLEX_OR_EXTENDED_OSIS_TARGET_UNREVIEWED",
            "": "EMPTY_OR_MISSING_OSISREF_ATTRIBUTE",
        }
        for reference, category in expected.items():
            with self.subTest(reference=reference):
                self.assertEqual(classify_original_reference_target(
                    reference, canonical_verses=self.verses,
                    canonical_chapters=self.chapters
                ), category)

    def test_full_native_K_I_U_observation_and_metadata_only_report(self):
        scan = OriginalCommentaryReferenceRegistryTriage()
        body = (
            b"<div>Invented prose</div>"
            b'<reference osisRef="Bible:Gen.1.1">Invented reference</reference>'
            b'<reference osisRef="Gen.1.9">Invented incorrect locator</reference>'
            b'<reference osisRef="Gen.1.3-Gen.1.1">Invented reversed</reference>'
            b"<reference>Invented unqualified target</reference>"
        )
        scan.observe("K", "Gen.1.1", body)
        scan.observe("K", "Gen.1.2", body)  # Source-linked alias, not a new body
        scan.observe(
            "I", "Gen.1",
            b'<reference osisRef="Gen.1.1-9">Invented intro target</reference>'
        )
        scan.observe("U", "TOP", b"opaque")
        report = scan.report(canonical_verses=self.verses,
                             canonical_chapters=self.chapters)
        self.assertEqual(report["original_native_K_seen"], 2)
        self.assertEqual(report["original_native_I_seen"], 1)
        self.assertEqual(report["original_native_TOP_seen"], 1)
        self.assertEqual(report["original_distinct_K_I_payload_bodies"], 2)
        self.assertEqual(report["distinct_body_reference_elements_classified"], 5)
        self.assertEqual(
            report["reference_target_classes"]["EXACT_SINGLE_VERSE_IN_REGISTRY"], 1)
        self.assertEqual(
            report["reference_target_classes"]["SIMPLE_SINGLE_VERSE_NOT_IN_REGISTRY"], 1)
        self.assertEqual(
            report["reference_target_classes"]["REVERSED_SAME_CHAPTER_VERSE_RANGE"], 1)
        self.assertEqual(
            report["reference_target_classes"]["EMPTY_OR_MISSING_OSISREF_ATTRIBUTE"], 1)
        self.assertEqual(
            report["reference_target_classes"]["SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY"], 1)
        self.assertFalse(report["original_reference_targets_or_prose_exported"])
        self.assertFalse(report["original_reference_targets_or_prose_changed"])
        self.assertFalse(report["publication_authorized"])
        self.assertNotIn("Gen.1.9", str(report))
        self.assertNotIn("Invented incorrect", str(report))

    def test_invalid_source_and_missing_registry_fail_closed(self):
        scan = OriginalCommentaryReferenceRegistryTriage()
        with self.assertRaises(ValueError):
            scan.observe("K", "Gen.1.1", b"<reference broken")
        with self.assertRaises(ValueError):
            scan.observe("K", "Gen.1.1", b"<reference>&unknown;</reference>")
        scan.observe("K", "Gen.1.1", b"<div>Safe invented source</div>")
        with self.assertRaises(ValueError):
            scan.report(canonical_verses=set(), canonical_chapters=self.chapters)


if __name__ == "__main__":
    unittest.main()
