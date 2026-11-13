"""Chapter-adjacent ThML source text compared to native intro, never whole chapter."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_chapter_neighbors import original_chapter_neighbors, compare_chapter_neighbors
from commentary_private_text_compare import raw_as_strict_xml_text
from pilot_preflight import PilotError


def fixture(marker_body=b"<h2>Chapter commentary.</h2>"):
    return (
        b"<?xml version='1.0'?><ThML><ThML.body><div1><div2>"
        b"<scripCom osisRef='Bible:Gen.1'/>" + marker_body +
        b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.3'/>"
        b"<div><p>A different commentary passage.</p></div>"
        b"</div2></div1></ThML.body></ThML>"
    )


class ChapterSiblingWitnessTests(unittest.TestCase):
    def test_marked_h2_vs_exact_intro_is_only_local_witness(self):
        source, proof = original_chapter_neighbors(fixture())
        self.assertEqual(proof["explicit_chapter_source_marker_count"], 1)
        self.assertEqual(proof["original_chapter_adjacent_sibling_tag_counts"], {"h2": 1})
        result = compare_chapter_neighbors(
            source, {"Gen.1": b"<h2>Chapter commentary.</h2>"}, raw_as_strict_xml_text)
        self.assertEqual(result["source_chapter_sibling_to_occupied_native_intro_classes"],
                         {"exact_unicode_text": 1})
        self.assertFalse(result["full_original_chapter_body_compared"])
        self.assertNotIn("Chapter commentary.", json.dumps(result))

    def test_p_sibling_with_compiled_prefix_is_only_containment(self):
        source, _ = original_chapter_neighbors(fixture(b"<p>Source chapter words.</p>"))
        result = compare_chapter_neighbors(
            source, {"Gen.1.0": b"<title>Independent stock label</title>"
                      b"<p>Source chapter words.</p>"}, raw_as_strict_xml_text)
        self.assertEqual(
            result["source_chapter_sibling_to_occupied_native_intro_classes"],
            {"original_sibling_exact_substring_of_stock_intro": 1})
        self.assertFalse(result["full_original_chapter_body_compared"])

    def test_missing_ambiguous_and_invalid_raw_are_not_exact_matches(self):
        source, _ = original_chapter_neighbors(fixture())
        self.assertIn("no_native_intro_at_explicit_source_key",
                      compare_chapter_neighbors(source, {}, raw_as_strict_xml_text)
                      ["source_chapter_sibling_to_occupied_native_intro_classes"])
        self.assertIn("ambiguous_two_occupied_intro_key_spellings",
                      compare_chapter_neighbors(source, {"Gen.1": b"<p>x</p>",
                                                         "Gen.1.0": b"<p>y</p>"},
                                                raw_as_strict_xml_text)
                      ["source_chapter_sibling_to_occupied_native_intro_classes"])
        self.assertIn("stock_intro_raw_xml_not_strictly_parseable",
                      compare_chapter_neighbors(source, {"Gen.1": b"<p>broken</title>"},
                                                raw_as_strict_xml_text)
                      ["source_chapter_sibling_to_occupied_native_intro_classes"])

    def test_non_sibling_text_and_unrecognized_markers_fail_closed(self):
        with self.assertRaisesRegex(PilotError, "intervening"):
            original_chapter_neighbors(fixture().replace(
                b"<scripCom osisRef='Bible:Gen.1'/>",
                b"<scripCom osisRef='Bible:Gen.1'/>Unmapped content"))
        with self.assertRaisesRegex(PilotError, "unreviewed next sibling"):
            original_chapter_neighbors(fixture(b"<div>Unreviewed body</div>"))


if __name__ == "__main__":
    unittest.main()
