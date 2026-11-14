"""Synthetic regressions for source-neutral commentary section-scope triage."""
import sys
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_section_scope_audit import (
    heading_extent, classify, compare_independent_thml_witness
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
        self.assertIsNone(heading_extent(b"Verses 2,4-7 Text"))

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

    def test_missing_members_of_dash_section(self):
        outcome = classify({
            "Song.1.2": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
            "Song.1.3": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
        })
        self.assertEqual(outcome["anomalies"][0]["missing_slots"], ["Song.1.4"])



class IndependentWitnessTests(unittest.TestCase):
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
