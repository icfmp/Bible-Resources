"""Regression tests for honest, text-free real SWORD smoke diagnostics."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from smoke import reader_failure_class


class ReaderSmokeDiagnostics(unittest.TestCase):
    def test_original_commentary_natural_language_is_not_reader_error(self):
        original="Genesis 1:1: Matthew Henry explains something was not found, but God created."
        self.assertIsNone(reader_failure_class(0,original))
        self.assertIsNone(reader_failure_class(0,"Genesis 1:1: This error: of men was recorded."))
        self.assertIsNone(reader_failure_class(0,"Genesis 1:1: No modules were found in their houses."))

    def test_true_missing_module_and_reader_failures_are_blocked(self):
        for actual_error in (
            "Module BRMHCC not found.",
            "Module 'BRMHCC' not found",
            "ERROR: No suitable SWORD module",
            "Usage: diatheke -b <module>",
            "No modules found",
            "Unable to find module BRMHCC",
            "Not a valid reference",
        ):
            with self.subTest(actual_error=actual_error):
                self.assertEqual(reader_failure_class(0,actual_error),"reader_diagnostic")
        self.assertEqual(reader_failure_class(0," "), "empty_output")
        self.assertEqual(reader_failure_class(2,"Genesis 1:1: valid prose"),"nonzero_exit")


if __name__=="__main__":
    unittest.main()
