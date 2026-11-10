"""Source/native punctuation-relative p/q boundary corruption fixtures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from source_native_maintext_probe import authored_usfx_main_text
from source_native_word_boundaries import (
    original_usfx_body_boundaries, NativeBodyBoundaries,
    compare_body_boundary_word_positions,
)
from source_native_nonspace_boundaries import (
    compare_punctuation_sensitive_boundaries, NonspaceBoundaryError,
)

SOURCE=(b'<usfx><book id="GEN"><p sfm="mt">PRIVATE TITLE</p><c id="1"/>'
        b'<p><v id="1"/>alpha, <q>beta,</q> gamma<ve/></p></book></usfx>')
BOOKS=[("GEN","Gen")]


def audit(native_verse=None):
    if native_verse is None:
        native_verse=(b'alpha, <l sID="PRIVATE-LINE"/>beta,'
                      b'<l eID="PRIVATE-LINE"/> gamma'
                      b'<div type="x-p" eID="PRIVATE-P"/>')
    text,_=authored_usfx_main_text(SOURCE,BOOKS)
    original,_=original_usfx_body_boundaries(SOURCE,BOOKS,text)
    witness=NativeBodyBoundaries()
    witness.observe("I","Gen.1",b'<div type="x-p" sID="PRIVATE-P"/>')
    witness.observe("K","Gen.1.1",native_verse)
    compiled,_=witness.finish()
    return original,compiled


class OriginalNativeNonspaceBoundariesTests(unittest.TestCase):
    def test_full_book_nonspace_text_and_both_p_q_endpoints_match(self):
        source,compiled=audit()
        receipt=compare_punctuation_sensitive_boundaries(source,compiled)
        self.assertTrue(receipt["all_p_q_source_native_nonwhitespace_codepoint_boundaries_match"])
        self.assertEqual(receipt["status"],
                         "all_p_q_nonwhitespace_codepoint_boundaries_match_diagnostic_only")
        counts=receipt["character_sensitive_source_native_counts"]
        self.assertEqual(counts["p_q_events_compared"],2)
        self.assertEqual(counts["source_event_endpoints_checked"],4)
        self.assertEqual(counts["open_same_nonwhitespace_codepoint_ordinal"],2)
        self.assertEqual(counts["close_same_nonwhitespace_codepoint_ordinal"],2)
        self.assertEqual(counts["books_with_exact_private_nonwhitespace_text_match"],1)
        self.assertEqual(receipt["source_p_q_nonspace_codepoint_event_hash_sha256"],
                         receipt["native_p_q_nonspace_codepoint_event_hash_sha256"])
        self.assertTrue(receipt["source_original_whitespace_and_newlines_not_compared_or_approved"])
        for private in ("alpha","beta","gamma","PRIVATE TITLE","PRIVATE-LINE","PRIVATE-P"):
            self.assertNotIn(private,str(receipt))

    def test_poetry_opening_moved_across_comma_detected_with_same_word_ordinal(self):
        raw=(b'alpha<l sID="PRIVATE-LINE"/>, beta,'
             b'<l eID="PRIVATE-LINE"/> gamma'
             b'<div type="x-p" eID="PRIVATE-P"/>')
        src,native=audit(raw)
        self.assertTrue(compare_body_boundary_word_positions(
            src,native,{}, {})["all_mapped_book_p_q_start_end_word_ordinals_match"])
        receipt=compare_punctuation_sensitive_boundaries(src,native)
        c=receipt["character_sensitive_source_native_counts"]
        self.assertEqual(c["open_nonwhitespace_codepoint_ordinal_differs"],1)
        self.assertEqual(c["close_nonwhitespace_codepoint_ordinal_differs"],0)
        self.assertFalse(receipt["all_p_q_source_native_nonwhitespace_codepoint_boundaries_match"])
        self.assertEqual(c["books_with_exact_private_nonwhitespace_text_match"],1)
        self.assertNotIn("alpha",str(receipt))

    def test_poetry_closing_before_comma_detected_even_with_same_words(self):
        raw=(b'alpha, <l sID="PRIVATE-LINE"/>beta'
             b'<l eID="PRIVATE-LINE"/>, gamma'
             b'<div type="x-p" eID="PRIVATE-P"/>')
        src,native=audit(raw)
        receipt=compare_punctuation_sensitive_boundaries(src,native)
        self.assertEqual(receipt["character_sensitive_source_native_counts"][
            "close_nonwhitespace_codepoint_ordinal_differs"],1)
        self.assertFalse(receipt["all_p_q_source_native_nonwhitespace_codepoint_boundaries_match"])

    def test_changed_punctuation_blocks_private_full_book_character_match(self):
        raw=(b'alpha; <l sID="PRIVATE-LINE"/>beta,'
             b'<l eID="PRIVATE-LINE"/> gamma'
             b'<div type="x-p" eID="PRIVATE-P"/>')
        src,native=audit(raw)
        receipt=compare_punctuation_sensitive_boundaries(src,native)
        self.assertEqual(receipt["character_sensitive_source_native_counts"][
            "books_with_nonwhitespace_maintext_character_difference"],1)
        self.assertFalse(receipt["all_p_q_source_native_nonwhitespace_codepoint_boundaries_match"])
        self.assertEqual(receipt["status"],"nonwhitespace_text_or_event_boundary_differs")

    def test_whitespace_only_change_cannot_be_approved_as_original_linebreak(self):
        raw=(b'alpha,  \n\t <l sID="PRIVATE-LINE"/>beta,'
             b'<l eID="PRIVATE-LINE"/>\n gamma'
             b'<div type="x-p" eID="PRIVATE-P"/>')
        src,native=audit(raw)
        receipt=compare_punctuation_sensitive_boundaries(src,native)
        self.assertTrue(receipt["all_p_q_source_native_nonwhitespace_codepoint_boundaries_match"])
        self.assertTrue(receipt["source_original_whitespace_and_newlines_not_compared_or_approved"])
        self.assertFalse(receipt["book_intro_and_punctuation_encoding_editorial_approval_not_given"] is False)

    def test_incorrect_original_word_ordinal_remains_a_hard_prerequisite(self):
        src,native=audit()
        native["Gen"][1][1]["open"]["word_ordinal"] += 1
        with self.assertRaises(NonspaceBoundaryError):
            compare_punctuation_sensitive_boundaries(src,native)

    def test_invalid_or_missing_private_nonspace_digest_is_rejected(self):
        src,native=audit()
        native["Gen"][1][1]["open"]["private_book_nonwhitespace_sha256"] = "PRIVATE"
        with self.assertRaises(NonspaceBoundaryError):
            compare_punctuation_sensitive_boundaries(src,native)

    def test_missing_compiled_book_or_mismatched_event_kind_rejected(self):
        src,native=audit()
        with self.assertRaises(NonspaceBoundaryError):
            compare_punctuation_sensitive_boundaries(src,{})
        native["Gen"][1][1]["kind"]="p"
        with self.assertRaises(NonspaceBoundaryError):
            compare_punctuation_sensitive_boundaries(src,native)


if __name__=="__main__":
    unittest.main()
