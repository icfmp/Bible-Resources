"""Original-to-stock-SWORD whitespace evidence uses metadata only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from maintext_whitespace_patterns import MainTextWhitespacePatterns


class MainTextWhitespacePatternsTests(unittest.TestCase):
    def test_boundary_vs_internal_vs_line_and_unicode_changes(self):
        results=MainTextWhitespacePatterns()
        results.observe("Gen.1.1", " alpha, beta!", "alpha, beta!")
        results.observe("Ps.23.1", "alpha\nbeta", "alpha beta")
        results.observe("John.3.16", "alpha\u00a0beta", " alpha beta")
        report=results.finish()
        self.assertEqual(report["whitespace_only_verses_inspected"],3)
        self.assertEqual(report["whitespace_change_types"],{
            "boundary_whitespace_only":1,
            "internal_whitespace_only":1,
            "internal_and_boundary_whitespace_only":1,
        })
        self.assertEqual(report["changed_whitespace_totals"]["source_newline_runs_changed"],1)
        self.assertEqual(report["changed_whitespace_totals"]["source_unicode_space_runs_changed"],1)
        self.assertEqual(report["changed_whitespace_totals"]["changed_internal_runs"],2)
        self.assertEqual(report["changed_whitespace_totals"]["changed_boundary_runs"],2)
        self.assertTrue(report["no_scripture_or_raw_whitespace_in_report"])
        self.assertFalse(report["compiled_paragraph_poetry_or_layout_fidelity_verified"])
        self.assertFalse(report["publication_approved"])
        self.assertNotIn("alpha",str(report))
        self.assertNotIn("beta",str(report))

    def test_nonwhitespace_changes_or_exact_are_not_misclassified(self):
        inputs=(
            ("alpha beta", "alpha gamma"),
            ("alpha beta", "alpha, beta"),
            ("alpha beta", "alpha beta"),
        )
        for a,b in inputs:
            with self.subTest(a=a,b=b), self.assertRaises(ValueError):
                MainTextWhitespacePatterns().observe("Gen.1.1",a,b)

    def test_bounded_metadata_samples_without_raw_content(self):
        result=MainTextWhitespacePatterns()
        for verse in range(1,18):
            result.observe(f"Gen.1.{verse}", " content", "content")
        report=result.finish()
        self.assertEqual(report["whitespace_only_verses_inspected"],17)
        self.assertEqual(len(report["first_reference_ids_without_scripture"]["boundary_whitespace_only"]),4)
        self.assertEqual(report["changed_whitespace_totals"]["changed_boundary_runs"],17)
        self.assertEqual(report["changed_whitespace_totals"]["changed_internal_runs"],0)
        self.assertNotIn("content",str(report))


if __name__=="__main__":
    unittest.main()
