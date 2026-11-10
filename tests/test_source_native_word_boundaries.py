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
        for forbidden in ("PRIVATE", "alpha", "beta", "gamma", "delta", "sID=\\\"line\\\"", "p1", "p2"):
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


    def test_moving_boundary_to_next_verse_is_visible_even_if_word_ordinals_match(self):
        first=(b'alpha <l sID="line"/>beta<l eID="line"/> gamma ')
        second=(b'<div type="x-p" eID="p1"/>'
                b'<div type="x-p" sID="p2"/>'
                b'delta <div type="x-p" eID="p2"/>')
        receipt=compare(first=first,second=second)
        self.assertTrue(receipt["all_mapped_book_p_q_start_end_word_ordinals_match"])
        c=receipt["original_vs_compiled_event_word_position_counts"]
        self.assertGreater(c["same_word_ordinals_but_original_native_record_scope_differs"],0)
        self.assertIn("matching_word_ordinals_different_record_scope",
                      [x["problem"] for x in
                       receipt["first_source_native_boundary_findings_reference_ordinals_only"]])
        self.assertTrue(receipt[
            "identical_book_word_ordinals_not_exact_verse_record_or_markup_placement"])

    def test_moving_second_same_kind_paragraph_start_one_word_earlier_is_found(self):
        early=(b'alpha <l sID="line"/>beta<l eID="line"/>'
               b'<div type="x-p" eID="p1"/>'
               b'<div type="x-p" sID="p2"/> gamma ')
        receipt=compare(first=early)
        self.assertEqual(receipt["original_vs_compiled_event_word_position_counts"][
            "opening_word_position_mismatches"],1)
        self.assertFalse(receipt["all_mapped_book_p_q_start_end_word_ordinals_match"])

    def test_unaddressable_native_top_never_certifies_complete_boundary_proof(self):
        a,sc=original()
        native=NativeBodyBoundaries()
        native.observe("U","TOP:1",b'<div type="x-p" sID="unmapped"/>')
        native.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
        native.observe("K","Gen.1.1",b'alpha <l sID="line"/>beta'
                       b'<l eID="line"/> gamma <div type="x-p" eID="p1"/>'
                       b'<div type="x-p" sID="p2"/>')
        native.observe("K","Gen.1.2",b'delta <div type="x-p" eID="p2"/>')
        b,nc=native.finish()
        receipt=compare_body_boundary_word_positions(a,b,sc,nc)
        self.assertFalse(receipt["all_mapped_book_p_q_start_end_word_ordinals_match"])
        self.assertEqual(receipt["original_vs_compiled_event_word_position_counts"][
            "unaddressable_native_top_records"],1)
        self.assertEqual(receipt["original_vs_compiled_event_word_position_counts"][
            "unaddressable_top_body_event_occurrences"],1)


    def test_anonymous_nonbody_top_does_not_block_only_p_q_word_boundaries(self):
        source, source_counts=original()
        observer=NativeBodyBoundaries()
        observer.observe("U","TOP:1",
                         b'<div type="x-milestone" sID="PRIVATE_NONBODY"/>'
                         b'<title>PRIVATE BOOK HEADER</title>')
        observer.observe("I","Gen.1",b'<div type="x-p" sID="p1"/>')
        observer.observe("K","Gen.1.1",b'alpha <l sID="line"/>beta'
                         b'<l eID="line"/> gamma <div type="x-p" eID="p1"/>'
                         b'<div type="x-p" sID="p2"/>')
        observer.observe("K","Gen.1.2",b'delta <div type="x-p" eID="p2"/>')
        native,native_counts=observer.finish()
        report=compare_body_boundary_word_positions(
            source,native,source_counts,native_counts)
        self.assertTrue(report["all_mapped_book_p_q_start_end_word_ordinals_match"])
        c=report["original_vs_compiled_event_word_position_counts"]
        self.assertEqual(c["unaddressable_native_top_records"],1)
        self.assertEqual(c["parseable_native_top_records"],1)
        self.assertEqual(c.get("unaddressable_top_body_event_occurrences",0),0)
        self.assertTrue(report[
            "top_records_only_screened_for_p_q_body_markup_not_all_editorial_content"])
        self.assertNotIn("PRIVATE",str(report))

    def test_unparseable_anonymous_native_top_fails_closed(self):
        audit=NativeBodyBoundaries()
        with self.assertRaises(BoundaryAuditError):
            audit.observe("U","TOP:1",b'<div type="x-p" sID="BROKEN"')
        with self.assertRaises(BoundaryAuditError):
            audit.observe("U","BAD:1",b'<div/>')

    def test_note_subtree_in_top_not_confused_with_body_markup(self):
        audit=NativeBodyBoundaries()
        audit.observe("U","TOP:1",
                      b'<note><l sID="PRIVATE_NOTE_ONLY"/></note>')
        self.assertEqual(audit.counts["parseable_native_top_records"],1)
        self.assertEqual(audit.counts["unaddressable_top_body_event_occurrences"],0)


if __name__ == "__main__":
    unittest.main()
