"""Boundary corruption fixtures: source USFX vs actual native SWORD start/end."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_maintext_probe import authored_usfx_main_text
from source_native_word_boundaries import (
    BoundaryAuditError, NativeBodyBoundaries,
    original_usfx_body_boundaries, compare_body_boundary_word_positions,
)

MAPPING = [("GEN","Gen")]
SOURCE = (b'<usfx><book id="GEN">'
          b'<p sfm="mt">PRIVATE TITLE</p><c id="1"/>'
          b'<p><v id="1"/>alpha <q>beta</q> gamma <ve/></p>'
          b'<p><v id="2"/>delta <ve/></p>'
          b'</book></usfx>')


def original(xml=SOURCE):
    verses,_=authored_usfx_main_text(xml,MAPPING)
    return original_usfx_body_boundaries(xml,MAPPING,verses)


def compiled(first=None, second=None, intro=True):
    first=(first if first is not None else
           b'alpha <l sID="line"/>beta<l eID="line"/> gamma '
           b'<div type="x-p" eID="p1"/>'
           b'<div type="x-p" sID="p2"/>')
    second=(second if second is not None else
            b'delta <div type="x-p" eID="p2"/>')
    native=NativeBodyBoundaries()
    if intro:
        native.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
    native.observe("K","Gen.1.1",first)
    native.observe("K","Gen.1.2",second)
    return native.finish()


def compare(xml=SOURCE,first=None,second=None):
    a,sc=original(xml)
    b,nc=compiled(first,second)
    return compare_body_boundary_word_positions(a,b,sc,nc)


class SourceNativeWordBoundaryTests(unittest.TestCase):
    def test_original_start_and_end_positions_match_native_compiled_word_stream(self):
        result=compare()
        self.assertEqual(result["status"],
                         "all_p_q_word_start_end_positions_match_diagnostic_only")
        self.assertTrue(result["all_mapped_book_p_q_start_end_word_ordinals_match"])
        counts=result["original_vs_compiled_event_word_position_counts"]
        self.assertEqual(counts["source_p_opens"],2)
        self.assertEqual(counts["source_q_opens"],1)
        self.assertEqual(counts["source_p_closes"],2)
        self.assertEqual(counts["source_q_closes"],1)
        self.assertEqual(counts["native_p_opens"],2)
        self.assertEqual(counts["native_p_closes"],2)
        self.assertEqual(counts["native_q_opens"],1)
        self.assertEqual(counts["native_q_closes"],1)
        self.assertEqual(counts["same_kind_event_word_start_and_end_positions_match"],3)
        self.assertFalse(result["source_native_original_style_and_linebreak_fidelity_unverified"] is False)
        for forbidden in ("PRIVATE", "alpha", "beta", "gamma", "delta", "line", "p1", "p2"):
            self.assertNotIn(forbidden,str(result))

    def test_early_paragraph_closure_detected_even_if_counts_and_words_match(self):
        early=(b'alpha <l sID="line"/>beta<l eID="line"/>'
               b'<div type="x-p" eID="p1"/> gamma '
               b'<div type="x-p" sID="p2"/>')
        r=compare(first=early)
        self.assertFalse(r["all_mapped_book_p_q_start_end_word_ordinals_match"])
        c=r["original_vs_compiled_event_word_position_counts"]
        self.assertEqual(c["closing_word_position_mismatches"],1)
        self.assertEqual(c["native_p_opens"],2)
        self.assertEqual(c["source_p_opens"],2)
        self.assertEqual(c["source_words"],c["native_words"])
        self.assertIn("different_close_word_ordinal",
                      [x["problem"] for x in
                       r["first_source_native_boundary_findings_reference_ordinals_only"]])

    def test_late_poetry_open_detected_with_identical_kind_order_and_text(self):
        late=(b'alpha beta<l sID="line"/><l eID="line"/> gamma '
              b'<div type="x-p" eID="p1"/>'
              b'<div type="x-p" sID="p2"/>')
        r=compare(first=late)
        self.assertEqual(r["original_vs_compiled_event_word_position_counts"][
            "opening_word_position_mismatches"],1)
        self.assertFalse(r["all_mapped_book_p_q_start_end_word_ordinals_match"])

    def test_boundary_inside_word_blocks_positive_evidence(self):
        broken=(b'alpha <l sID="line"/>be<l eID="line"/>ta gamma '
                b'<div type="x-p" eID="p1"/>'
                b'<div type="x-p" sID="p2"/>')
        r=compare(first=broken)
        self.assertEqual(r["original_vs_compiled_event_word_position_counts"][
            "events_with_boundary_inside_lexical_word"],1)
        self.assertFalse(r["all_mapped_book_p_q_start_end_word_ordinals_match"])

    def test_duplicate_or_orphan_closing_is_rejected(self):
        native=NativeBodyBoundaries()
        native.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
        with self.assertRaises(BoundaryAuditError):
            native.observe("K","Gen.1.1",b'alpha<div type="x-p" eID="bad"/>')

    def test_unclosed_crossverse_opening_is_rejected(self):
        native=NativeBodyBoundaries()
        native.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
        native.observe("K","Gen.1.1",b'alpha')
        with self.assertRaises(BoundaryAuditError):
            native.finish()

    def test_original_note_and_book_title_words_are_excluded(self):
        src=(b'<usfx><book id="GEN"><p sfm="mt">PRIVATE TITLE</p>'
             b'<c id="1"/><p><v id="1"/>alpha'
             b'<f><p>PRIVATE NOTE BODY</p></f> beta<ve/></p></book></usfx>')
        verses,_=authored_usfx_main_text(src,MAPPING)
        events,c=original_usfx_body_boundaries(src,MAPPING,verses)
        self.assertEqual(c["source_book_titles_accounted_elsewhere"],1)
        self.assertEqual(len(events["Gen"][1]),1)
        self.assertEqual(events["Gen"][0],["alpha","beta"])

    def test_source_verse_character_discrepancy_fails_closed(self):
        verses,_=authored_usfx_main_text(SOURCE,MAPPING)
        verses["Gen.1.1"]="INVENTED TEXT"
        with self.assertRaises(BoundaryAuditError):
            original_usfx_body_boundaries(SOURCE,MAPPING,verses)

    def test_native_intro_header_text_not_counted_as_scripture(self):
        a,sc=original()
        native=NativeBodyBoundaries()
        native.observe("I","Gen",b'<title>PRIVATE HEADER</title>')
        native.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
        native.observe("K","Gen.1.1",b'alpha <l sID="line"/>beta'
                       b'<l eID="line"/> gamma <div type="x-p" eID="p1"/>'
                       b'<div type="x-p" sID="p2"/>')
        native.observe("K","Gen.1.2",b'delta <div type="x-p" eID="p2"/>')
        b,nc=native.finish()
        r=compare_body_boundary_word_positions(a,b,sc,nc)
        self.assertTrue(r["all_mapped_book_p_q_start_end_word_ordinals_match"])
        self.assertNotIn("PRIVATE",str(r))


if __name__ == "__main__":
    unittest.main()
