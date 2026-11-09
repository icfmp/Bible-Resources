"""Privacy-safe whitespace change classification tests (synthetic notes only)."""
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from note_whitespace_diagnostics import classify_note_whitespace


class NoteWhitespaceClassificationTests(unittest.TestCase):
    def test_exact_including_unicode_spaces(self):
        x="un\u00a0mot  ici\nfin"
        result=classify_note_whitespace(x,x)
        self.assertEqual(result["class"],"exact")
        self.assertTrue(result["content_equivalent"])

    def test_newline_replaced_with_ascii_space_is_not_silently_approved(self):
        result=classify_note_whitespace("alpha\nbeta","alpha beta")
        self.assertEqual(result["class"],"internal_whitespace_only")
        self.assertEqual(result["changed_internal_runs"],1)
        self.assertEqual(result["source_newline_runs_changed"],1)
        self.assertEqual(result["compiled_newline_runs_changed"],0)
        self.assertEqual(result["changed_runs_same_length"],1)
        self.assertFalse(result["exact"])
        self.assertTrue(result["content_equivalent"])

    def test_nbsp_replacement_is_detected(self):
        result=classify_note_whitespace("alpha\u00a0beta","alpha beta")
        self.assertEqual(result["source_unicode_space_runs_changed"],1)
        self.assertEqual(result["compiled_unicode_space_runs_changed"],0)
        self.assertEqual(result["changed_runs_same_length"],1)

    def test_multiple_ascii_spaces_are_classified_separately(self):
        result=classify_note_whitespace("alpha  beta","alpha beta")
        self.assertEqual(result["changed_runs_entirely_ascii_spaces"],1)
        self.assertEqual(result["changed_runs_decreased_length"],1)
        self.assertEqual(result["source_newline_runs_changed"],0)

    def test_tab_at_boundary_and_internal_changes_both_report(self):
        result=classify_note_whitespace("\talpha  beta","alpha beta")
        self.assertEqual(result["class"],"internal_and_boundary_whitespace_only")
        self.assertEqual(result["changed_internal_runs"],1)
        self.assertEqual(result["changed_boundary_runs"],1)
        self.assertEqual(result["source_tab_runs_changed"],1)

    def test_only_trailing_whitespace_does_not_count_as_internal(self):
        result=classify_note_whitespace("alpha beta\n","alpha beta")
        self.assertEqual(result["class"],"boundary_whitespace_only")
        self.assertEqual(result["changed_internal_runs"],0)
        self.assertEqual(result["changed_boundary_runs"],1)

    def test_real_text_or_punctuation_change_is_not_misclassified(self):
        for compiled in ("alphabeta", "alpha, beta", "alpha gamma"):
            with self.subTest(compiled=compiled):
                result=classify_note_whitespace("alpha beta",compiled)
                self.assertEqual(result["class"],"non_whitespace_tokens_differ")
                self.assertFalse(result["content_equivalent"])
                self.assertNotIn("alpha",str(result))
                self.assertNotIn("gamma",str(result))


if __name__=="__main__":
    unittest.main()
