"""Synthetic, source-neutral CCEL↔stock SWORD private lexical comparison checks."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_private_text_compare import (
    _original_source_markers,compare_private_texts,raw_as_strict_xml_text)
from pilot_preflight import PilotError


class CommentaryOriginalStockTextTests(unittest.TestCase):
    def source(self):
        return (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b"<ThML><ThML.body><div1><div2>"
            b"<scripCom osisRef='Bible:Gen.1.1-Gen.1.3'/>"
            b"<div><p>Exact private text, punctuation!</p></div>"
            b"<scripCom osisRef='Bible:Gen.1.4'/>"
            b"<div><p>Original next paragraph.</p></div>"
            b"<scripCom osisRef='Bible:Gen.1'/>"
            b"<h2>Chapter heading not a verse unit.</h2>"
            b"</div2></div1></ThML.body></ThML>" + b" " * 1100)

    def test_exact_and_changed_punctuation_are_distinct_and_private(self):
        units,proof=_original_source_markers(self.source())
        self.assertEqual(proof["original_verse_or_range_body_count"],2)
        self.assertEqual(proof["chapter_source_markers_not_compared"],1)
        out=compare_private_texts(units,{
            "Gen.1.1":b"<p>Exact private text, punctuation!</p>",
            "Gen.1.4":b"<p>Original next paragraph?</p>",
        })
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["exact_unicode_text_match"],1)
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["lexical_text_or_punctuation_difference"],1)
        self.assertFalse(out["all_selected_verse_range_body_text_exact_matches"])
        self.assertFalse(out["full_authored_to_stock_parity_verified"])
        self.assertFalse(out["original_paragraphs_notes_and_quotations_verified"])
        self.assertNotIn("Exact private text",json.dumps(out))
        self.assertNotIn("Original next paragraph",json.dumps(out))

    def test_whitespace_only_differences_are_not_exact_fidelity(self):
        units,_=_original_source_markers(self.source())
        out=compare_private_texts(units,{
            "Gen.1.1":b"<p> Exact private text, punctuation! </p>",
            "Gen.1.4":b"<p>Original  next paragraph.</p>",
        })
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["edge_whitespace_difference_only"],1)
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["interior_whitespace_difference_only"],1)
        self.assertFalse(out["all_selected_verse_range_body_text_exact_matches"])

    def test_raw_xml_must_parse_without_guesswork(self):
        self.assertIsNone(raw_as_strict_xml_text(b"<p>bad</span>"))
        self.assertIsNone(raw_as_strict_xml_text(b"<!DOCTYPE x><p>unsupported</p>"))
        self.assertEqual(raw_as_strict_xml_text(b"<p>Fine punctuation.</p>"),"Fine punctuation.")

    def test_missing_native_start_is_not_claimed_as_missing_source_text(self):
        units,_=_original_source_markers(self.source())
        out=compare_private_texts(units,{"Gen.1.1":b"<p>Exact private text, punctuation!</p>"})
        self.assertEqual(out["per_source_marker_text_diagnostic_counts"]["missing_original_start_in_native_raw"],1)
        self.assertFalse(out["full_authored_to_stock_parity_verified"])

    def test_intervening_nonwhitespace_original_text_blocks(self):
        source=self.source().replace(
            b"<scripCom osisRef='Bible:Gen.1.4'/>",
            b"<scripCom osisRef='Bible:Gen.1.4'/>Original words before div"
        )
        with self.assertRaisesRegex(PilotError,"Nonwhitespace"):
            _original_source_markers(source)


if __name__=="__main__":
    unittest.main()
