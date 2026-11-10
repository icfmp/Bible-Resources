"""Whitespaces are source evidence, not silently approved formatting edits."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/ "scripts"))
from source_native_maintext_probe import authored_usfx_main_text
from source_native_word_boundaries import original_usfx_body_boundaries
from source_native_structural_whitespace import (
    MainTextStructuralWhitespaceTriage, StructuralWhitespaceError,
)

MAPPING=[("GEN","Gen")]


def original(verse_markup=b'<p><v id="1"/>alpha,\n<q>beta</q> gamma<ve/></p>'):
    xml=b'<usfx><book id="GEN"><p sfm="mt">PRIVATE TITLE</p><c id="1"/>'+verse_markup+b'</book></usfx>'
    verses,_=authored_usfx_main_text(xml,MAPPING)
    boundaries,_=original_usfx_body_boundaries(xml,MAPPING,verses)
    return verses,boundaries


def scan(verse_markup=None,native="alpha, beta gamma"):
    source,boundaries=original(verse_markup if verse_markup is not None else
                              b'<p><v id="1"/>alpha,\n<q>beta</q> gamma<ve/></p>')
    observer=MainTextStructuralWhitespaceTriage(source,boundaries)
    observer.observe("Gen.1.1",native)
    return observer.finish()


class StructuralWhitespaceTriageTests(unittest.TestCase):
    def test_newline_at_original_poetic_start_is_not_silently_treated_as_preserved(self):
        result=scan()
        totals=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(totals["indexed_verses_checked"],1)
        self.assertEqual(totals["source_newline_runs_absent_in_native_verse_text"],1)
        self.assertEqual(totals["source_newline_absent_at_q_open_candidate"],1)
        self.assertEqual(totals["structure_at_original_poetry_line_opening"],1)
        self.assertEqual(result["status"],
                         "whitespace_differences_classified_not_editorially_approved")
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])
        for secret in ("PRIVATE TITLE","alpha","beta","gamma","\n"):
            self.assertNotIn(secret,str(result))

    def test_newline_removed_not_at_any_original_p_q_marker_requires_review(self):
        raw=b'<p><v id="1"/>alpha,\nbeta <q>gamma</q><ve/></p>'
        result=scan(raw,"alpha, beta gamma")
        totals=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(totals["source_newline_absent_without_p_q_marker_review"],1)
        self.assertEqual(totals["structure_without_original_p_q_marker_at_that_character_boundary"],1)
        self.assertEqual(totals["unmarked_internal_source_newline_review"],1)
        self.assertEqual(totals["unmarked_source_verse_end_newline_candidate"],0)
        self.assertEqual(totals[
            "change_source_newline_not_present_in_compiled_verse_text_at_verse_internal"],1)

    def test_unmarked_source_newline_at_verse_end_is_not_inferred_as_poetry_loss(self):
        raw=(b'<p><v id="1"/>alpha beta\n<ve/>'
             b'<v id="2"/>gamma<ve/></p>')
        verses,boundaries=original(raw)
        triage=MainTextStructuralWhitespaceTriage(verses,boundaries)
        triage.observe("Gen.1.1","alpha beta")
        triage.observe("Gen.1.2","gamma")
        result=triage.finish()
        c=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["source_newline_absent_without_p_q_marker_review"],1)
        self.assertEqual(c["unmarked_source_verse_end_newline_candidate"],1)
        self.assertEqual(c["unmarked_internal_source_newline_review"],0)
        self.assertEqual(c[
            "change_source_newline_not_present_in_compiled_verse_text_at_verse_end"],1)
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])
        self.assertNotIn("alpha",str(result))

    def test_poetry_close_linebreak_has_distinct_category(self):
        raw=b'<p><v id="1"/>alpha, <q>beta</q>\n gamma<ve/></p>'
        result=scan(raw,"alpha, beta gamma")
        totals=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(totals["structure_at_original_poetry_line_closing"],1)
        self.assertEqual(totals["source_newline_absent_without_p_q_marker_review"],0)

    def test_identical_source_and_native_verse_whitespace_is_reported_as_exact_only(self):
        result=scan(native="alpha,\nbeta gamma")
        c=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["changed_whitespace_runs"],0)
        self.assertEqual(c["numbered_verses_with_exact_source_native_whitespace"],1)
        self.assertFalse(result["source_native_original_whitespace_layout_verified"])

    def test_changed_whitespace_not_at_poetry_marker_cannot_be_auto_approved(self):
        src=b'<p><v id="1"/>alpha, <q>beta</q> gamma<ve/></p>'
        receipt=scan(src,"alpha,  beta gamma")
        c=receipt["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["change_spacing_or_unicode_space_run_differs"],1)
        self.assertEqual(c["structure_at_original_poetry_line_opening"],1)
        self.assertFalse(receipt["source_native_original_whitespace_layout_verified"])

    def test_replacing_original_characters_blocks_whitespace_only_proof(self):
        result=scan(native="alpha; beta gamma")
        c=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["verses_with_nonwhitespace_difference_blocking_layout_triage"],1)
        self.assertEqual(result["status"],"blocked_nonwhitespace_source_native_text_difference")
        self.assertNotIn("alpha",str(result))

    def test_missing_duplicated_and_unmapped_verse_fail_closed(self):
        source,boundaries=original()
        triage=MainTextStructuralWhitespaceTriage(source,boundaries)
        with self.assertRaises(StructuralWhitespaceError):
            triage.finish()
        with self.assertRaises(StructuralWhitespaceError):
            triage.observe("Other.1.1","alpha, beta gamma")
        triage.observe("Gen.1.1","alpha, beta gamma")
        with self.assertRaises(StructuralWhitespaceError):
            triage.observe("Gen.1.1","alpha, beta gamma")

    def test_empty_wrong_or_reversed_source_book_scope_blocks(self):
        source,boundaries=original()
        with self.assertRaises(StructuralWhitespaceError):
            MainTextStructuralWhitespaceTriage({},boundaries)
        with self.assertRaises(StructuralWhitespaceError):
            MainTextStructuralWhitespaceTriage(source,{})
        with self.assertRaises(StructuralWhitespaceError):
            MainTextStructuralWhitespaceTriage(source,{"Other":boundaries["Gen"]})

    def test_no_verse_separator_is_mistaken_for_original_newline(self):
        raw=(b'<p><v id="1"/>alpha, <q>beta</q><ve/></p>'
             b'<p><v id="2"/>gamma<ve/></p>')
        source,boundaries=original(raw)
        triage=MainTextStructuralWhitespaceTriage(source,boundaries)
        triage.observe("Gen.1.1","alpha, beta")
        triage.observe("Gen.1.2","gamma")
        result=triage.finish()
        c=result["source_native_original_whitespace_gap_counts"]
        self.assertEqual(c["source_newline_runs_absent_in_native_verse_text"],0)
        self.assertEqual(c["changed_whitespace_runs"],0)
        self.assertEqual(c["indexed_verses_checked"],2)

    def test_source_notes_are_not_included_in_gap_inventories(self):
        raw=(b'<p><v id="1"/>alpha,'
             b'<f>PRIVATE NOTE \n BODY</f>\n<q>beta</q> gamma<ve/></p>')
        result=scan(raw,"alpha, beta gamma")
        self.assertEqual(result["source_native_original_whitespace_gap_counts"][
            "source_newline_absent_at_q_open_candidate"],1)
        self.assertNotIn("PRIVATE",str(result))


if __name__=="__main__":
    unittest.main()
