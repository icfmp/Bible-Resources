"""Synthetic regressions for source-neutral commentary section-scope triage."""
import sys
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_section_scope_audit import (
    heading_extent, classify, compare_independent_thml_witness,
    describe_unrecognized_heading, audit_unrecognized_slots,
)


class HeadingTests(unittest.TestCase):
    def test_comma_section_with_space_outside_heading(self):
        self.assertEqual(
            heading_extent(b"<title>Verse 7</title> ,8 Observe carefully."),
            ((7, 8), "comma")
        )

    def test_dash_and_plural_heading(self):
        self.assertEqual(
            heading_extent(b"<title>Verses 2-6</title><p>Some prose.</p>"),
            ((2, 3, 4, 5, 6), "dash")
        )

    def test_multiple_explicit_comma_verses(self):
        self.assertEqual(heading_extent(b"Verses 1,2,3 Comment"),
                         ((1, 2, 3), "comma"))

    def test_single_verse_and_no_heading(self):
        self.assertEqual(heading_extent(b"<title>Verse 4</title>"),
                         ((4,), "single"))
        self.assertIsNone(heading_extent(b"<p>A sermon concerning the book.</p>"))

    def test_reversed_and_ambiguous_range_not_guessed(self):
        self.assertIsNone(heading_extent(b"Verses 7-2 Text"))
        self.assertIsNone(heading_extent(b"Verses 8,4-7 Text"))
        self.assertIsNone(heading_extent(b"Verses 2-5,4-7 Text"))

    def test_discontinuous_nonoverlapping_ranges_are_not_lost(self):
        self.assertEqual(
            heading_extent(b"<title>Verses 24-30, 36-43</title><p>Discussion</p>"),
            (tuple(range(24, 31)) + tuple(range(36, 44)), "discontinuous")
        )
        self.assertEqual(
            heading_extent(b"<title>Verses 2,4-7</title>"),
            ((2,4,5,6,7), "discontinuous")
        )

    def test_xml_malformed_or_entities_rejected(self):
        self.assertIsNone(heading_extent(b"<p>Verse 2 <b>unclosed</p>"))
        self.assertIsNone(heading_extent(b"<p>&madeup; Verse 1</p>"))


class ClassificationTests(unittest.TestCase):
    def test_same_native_raw_for_whole_declared_section(self):
        records = {
            "Song.1.7": {"sha256": "a", "heading": ((7, 8), "comma")},
            "Song.1.8": {"sha256": "a", "heading": ((7, 8), "comma")},
        }
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["start_anchored_sections"], 1)
        self.assertEqual(outcome["counts"]["all_declared_slots_same_raw_payload"], 1)
        self.assertEqual(outcome["anomalies"], [])
        self.assertEqual(outcome["probes"]["Song.1.7"]["same_payload_slots"], ["Song.1.8"])

    def test_missing_verse_for_comma_span_stays_suspected(self):
        records = {"Jer.4.1": {"sha256": "a", "heading": ((1, 2), "comma")}}
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["missing_slots_within_declared_section"], 1)
        self.assertEqual(outcome["anomalies"][0]["missing_slots"], ["Jer.4.2"])
        self.assertEqual(outcome["anomalies"][0]["classification"],
                         "SUSPECTED_NOT_EDITORIALLY_CONFIRMED")

    def test_distinct_payload_in_declared_range(self):
        records = {
            "Jer.4.3": {"sha256": "a", "heading": ((3, 4), "comma")},
            "Jer.4.4": {"sha256": "b", "heading": ((3, 4), "comma")},
        }
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["distinct_payload_within_declared_section"], 1)

    def test_discontinuous_commentary_reports_missing_second_block(self):
        entries = {
            f"Matt.13.{verse}": {
                "sha256": "a", "heading": (
                    tuple(range(24, 31)) + tuple(range(36, 44)),
                    "discontinuous"
                )
            }
            for verse in range(24, 31)
        }
        report = classify(entries)
        self.assertEqual(report["counts"]["start_sections_discontinuous"], 1)
        self.assertEqual(
            report["anomalies"][0]["missing_slots"],
            [f"Matt.13.{verse}" for verse in range(36,44)]
        )

    def test_missing_members_of_dash_section(self):
        outcome = classify({
            "Song.1.2": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
            "Song.1.3": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
        })
        self.assertEqual(outcome["anomalies"][0]["missing_slots"], ["Song.1.4"])



class UnknownHeadingTests(unittest.TestCase):
    def test_no_verse_title_is_not_mistaken_for_lost_content(self):
        p = describe_unrecognized_heading(b"<title>Introduction</title><p>Context</p>")
        self.assertEqual(p["reason"], "NON_NUMERIC_XML_TITLE")
        self.assertTrue(p["visible_nonempty"])

    def test_empty_and_invalid_xml_have_different_classes(self):
        self.assertEqual(describe_unrecognized_heading(b" ")["reason"], "EMPTY_RAW_PAYLOAD")
        self.assertEqual(describe_unrecognized_heading(b"<p>broken</b>")["reason"],
                         "INVALID_XML_FRAGMENT")

    def test_no_title_and_nonempty_prose(self):
        p = describe_unrecognized_heading(b"<p>Context without numbered title</p>")
        self.assertEqual(p["reason"], "UNLABELLED_VISIBLE_PROSE")

    def test_unparsed_heading_not_automatically_corrected(self):
        p = describe_unrecognized_heading(b"<title>Verses two to five</title>")
        self.assertEqual(p["reason"], "UNPARSED_VERSE_LABEL")

    def test_raw_payload_groups_are_tracked_without_prose(self):
        unknown = describe_unrecognized_heading(b"<title>Introduction</title>")
        rows = {
            "Gen.1.1": {"sha256": "a", "heading": None, "unrecognized_profile": unknown},
            "Gen.1.2": {"sha256": "a", "heading": None, "unrecognized_profile": unknown},
            "Gen.1.3": {"sha256": "b", "heading": ((3, 4), "dash"),
                        "unrecognized_profile": None},
        }
        result = audit_unrecognized_slots(rows)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["reason_counts"]["NON_NUMERIC_XML_TITLE"], 2)
        self.assertEqual(result["distinct_native_raw_payload_hashes"], 1)
        self.assertEqual(result["first_verse_entries"], 1)
        self.assertEqual(result["single_occupied_slot_chapters_among_unknown"], 0)
        self.assertEqual(result["case_rows"][0]["number_of_occupied_native_slots_in_chapter"], 3)
        self.assertEqual(result["case_rows"][0]["highest_occupied_native_verse_in_chapter"], 3)
        self.assertFalse(result["unrecognized_means_missing_text_proven"])
        self.assertTrue(result["all_output_is_original_text_free_metadata"])


class IndependentWitnessTests(unittest.TestCase):
    def test_unlabelled_stock_entry_can_have_explicit_independent_section(self):
        xml = (
            b"<root>"
            b'<scripCom osisRef="Bible:Gen.36.1-Gen.36.43"/>'
            b'<scripRef osisRef="Bible:Gen.36.1-Gen.36.43"/>'
            b"</root>"
        )
        digest = sha256(xml).hexdigest()
        manifest = {"commentary_source": {
            "xml_witness_url": "https://www.ccel.org/fake.xml",
            "xml_witness_sha256": digest,
        }}
        unknown = [{
            "native_key": "Gen.36.1",
            "raw_payload_sha256": "fake-unique-payload",
            "number_of_occupied_native_slots_in_chapter": 1,
        }]
        def fixture(url, dest, provider):
            dest.write_bytes(xml)
            return {"sha256": digest, "bytes": len(xml)}
        with TemporaryDirectory() as td, patch(
            "commentary_section_scope_audit.fetch", fixture
        ):
            got = compare_independent_thml_witness(
                manifest, [], [], Path(td), unknown
            )
        self.assertEqual(
            got["unrecognized_source_annotation_classes"],
            {"SOURCE_EXPLICIT_MULTI_VERSE_SECTION": 1}
        )
        self.assertEqual(
            got["unrecognized_distinct_payload_source_rows"][0]["source_section_endpoints"],
            ["Gen.36.43"]
        )
        self.assertFalse(got["editorial_correctness_proven"])

    def test_citation_range_is_not_commentary_section_anchor(self):
        xml = (
            b"<root>"
            b'<scripRef osisRef="Bible:Song.1.7-Song.1.8"/>'
            b'<scripCom osisRef="Bible:Song.1.9-Song.1.17"/>'
            b"</root>"
        )
        digest = sha256(xml).hexdigest()
        manifest = {"commentary_source": {
            "xml_witness_url": "https://www.ccel.org/fake.xml",
            "xml_witness_sha256": digest
        }}
        sections = [
            {"start": "Song.1.7", "declared_end": 8, "heading_kind": "comma"},
            {"start": "Song.1.9", "declared_end": 17, "heading_kind": "dash"}
        ]
        anomalies = [{"start": "Song.1.7", "declared_end": 8}]

        def private_fixture_fetch(url, dest, provider):
            self.assertEqual(provider, "ccel")
            dest.write_bytes(xml)
            return {"sha256": digest, "bytes": len(xml)}

        with TemporaryDirectory() as td:
            with patch("commentary_section_scope_audit.fetch", private_fixture_fetch):
                outcome = compare_independent_thml_witness(
                    manifest, sections, anomalies, Path(td)
                )
        self.assertEqual(
            outcome["source_range_agreement_counts"], {
                "NO_MATCHING_INDEPENDENT_START": 1,
                "SAME_DECLARED_RANGE_IN_INDEPENDENT_EDITION": 1
            }
        )
        self.assertEqual(
            outcome["independent_scripref_range_agreement_counts"], {
                "EXACT_INDEPENDENT_SCRIPREF_RANGE": 1,
                "NO_EXACT_INDEPENDENT_SCRIPREF_RANGE": 1
            }
        )
        case = outcome["anomaly_source_range_corroboration"][0]
        self.assertEqual(case["relation"], "NO_MATCHING_INDEPENDENT_START")
        self.assertTrue(case["same_end_in_independent_scripref"])
        self.assertFalse(outcome["ccel_edition_equivalence_to_stock_proven"])


if __name__ == "__main__":
    unittest.main()
