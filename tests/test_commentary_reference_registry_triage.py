"""Invented-only original SWORD reference target / registry tests."""
import sys
import unittest
from lxml import etree
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

    def test_reversed_original_source_range_requires_independent_and_native_agreement(self):
        """Do not infer proposed labels from CCEL alone."""
        scan = OriginalCommentaryReferenceRegistryTriage()
        original = (
            b"<div>Invented original summary "
            b'<reference osisRef="Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</reference>.</div>"
        )
        scan.observe("K", "Gen.1.1", original)
        witness = etree.fromstring(
            b"<ThML><div2>"
            b'<scripRef osisRef="Bible:Gen.1.3-Gen.1.1">Gen 1:3-1</scripRef>'
            b'<scripCom osisRef="Bible:Gen.1.3-Gen.1.5">Invented section</scripCom>'
            b"</div2></ThML>"
        )
        good = scan.triangulate_reversed_ranges_against_independent_witness(
            witness, canonical_verses={f"Gen.1.{n}" for n in range(1, 6)},
            native_section_spans={"Gen.1.3": (3, 4, 5)},
        )
        self.assertEqual(good["source_original_distinct_body_reversed_reference_count"], 1)
        case = good["case_rows"][0]
        self.assertEqual(case["original_native_entry"], "Gen.1.1")
        self.assertTrue(case["original_link_display_text_contains_reversed_numeric_span"])
        self.assertTrue(case["independent_source_same_display_label_literal_match"])
        self.assertEqual(case["independent_source_same_bad_range_scripref_count"], 1)
        self.assertEqual(case["independent_source_full_range_scripcom_same_start_count"], 1)
        self.assertEqual(case["independent_source_and_native_heading_matching_candidate_count"], 1)
        self.assertEqual(case["candidate_end_verse_if_both_witnesses_agree"], 5)
        self.assertFalse(good["correction_authorized"])
        self.assertFalse(good["source_text_xml_or_original_reference_target_exported"])
        self.assertNotIn("Invented", str(good))

        # A different native passage, absent source section, or a source
        # with an invalid candidate endpoint can never approve a repair.
        no_native = scan.triangulate_reversed_ranges_against_independent_witness(
            witness, canonical_verses={f"Gen.1.{n}" for n in range(1, 6)},
            native_section_spans={"Gen.1.3": (3, 4)},
        )
        self.assertIsNone(
            no_native["case_rows"][0]["candidate_end_verse_if_both_witnesses_agree"])
        missing_source = etree.fromstring(
            b'<ThML><scripRef osisRef="Bible:Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</scripRef></ThML>"
        )
        no_source = scan.triangulate_reversed_ranges_against_independent_witness(
            missing_source, canonical_verses={f"Gen.1.{n}" for n in range(1, 6)},
            native_section_spans={"Gen.1.3": (3, 4, 5)},
        )
        self.assertIsNone(
            no_source["case_rows"][0]["candidate_end_verse_if_both_witnesses_agree"])

    def test_single_verse_source_section_anchor_needs_independent_valid_range(self):
        scan = OriginalCommentaryReferenceRegistryTriage()
        scan.observe(
            "K", "Gen.1.1",
            b'<reference osisRef="Gen.1.3-Gen.1.1">Gen 1:3-1</reference>'
        )
        native = {"Gen.1.3": (3, 4, 5)}
        verses = {f"Gen.1.{v}" for v in range(1, 6)}
        source = etree.fromstring(
            b'<ThML><scripRef osisRef="Bible:Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</scripRef>"
            b'<scripCom osisRef="Bible:Gen.1.3">Invented source start</scripCom>'
            b'<scripRef osisRef="Bible:Gen.1.3-Gen.1.5">'
            b"Gen 1:3-5</scripRef></ThML>"
        )
        receipt = scan.triangulate_reversed_ranges_against_independent_witness(
            source, canonical_verses=verses, native_section_spans=native)
        candidate = receipt["case_rows"][0]
        self.assertEqual(candidate["candidate_end_verse_if_both_witnesses_agree"], 5)
        self.assertEqual(
            candidate["independent_source_single_verse_scripcom_same_start_count"], 1)
        self.assertEqual(
            candidate["independent_source_valid_range_scripref_matching_native_count"], 1)
        self.assertTrue(candidate["independent_source_same_reversed_numeric_label_present"])
        self.assertFalse(candidate["editorial_approval"])
        missing_valid_range = etree.fromstring(
            b'<ThML><scripCom osisRef="Bible:Gen.1.3">'
            b"Invented source start only</scripCom></ThML>"
        )
        blocked = scan.triangulate_reversed_ranges_against_independent_witness(
            missing_valid_range, canonical_verses=verses, native_section_spans=native)
        self.assertIsNone(
            blocked["case_rows"][0]["candidate_end_verse_if_both_witnesses_agree"])

    def test_reversed_range_witness_rejects_invalid_inputs(self):
        scan = OriginalCommentaryReferenceRegistryTriage()
        scan.observe("K", "Gen.1.1", b'<reference osisRef="Gen.1.3-Gen.1.1">3-1</reference>')
        with self.assertRaises(ValueError):
            scan.triangulate_reversed_ranges_against_independent_witness(
                "not an XML witness", canonical_verses={"Gen.1.3"}, native_section_spans={}
            )
        with self.assertRaises(ValueError):
            scan.triangulate_reversed_ranges_against_independent_witness(
                etree.Element("ThML"), canonical_verses=set(), native_section_spans={}
            )

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
