"""Fail-closed, text-free paragraph-leading marker diagnostics."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from inspect_paragraph_rendering import (
    ParagraphRenderingProbeError, diff, shape, source_structure,
)


class TestParagraphRendering(unittest.TestCase):
    def test_star_kept_as_editorial_symbol_not_automatically_removed(self):
        d = diff("\n  *Ce sont ici", " *Ce sont ici")
        self.assertEqual(d["original"]["starts_with_editorial_symbol_candidate"], "*")
        self.assertEqual(d["compiled"]["starts_with_editorial_symbol_candidate"], "*")
        self.assertFalse(d["same_leading_whitespace"])
        self.assertTrue(d["same_nonspace_characters"])
        self.assertFalse(d["same_exact_verse_characters"])

    def test_double_star_and_plain_text_are_distinct(self):
        self.assertEqual(shape("**Division")["starts_with_editorial_symbol_candidate"], "**")
        self.assertIsNone(shape("Ce * n'est pas un alinea")["starts_with_editorial_symbol_candidate"])

    def test_inline_divine_name_star_is_not_subject_division_without_context(self):
        d = shape("*Dieu")
        self.assertEqual(d["starts_with_editorial_symbol_candidate"], "*")
        # Lexical shape alone never classifies the semantic meaning.
        self.assertNotIn("strong_subject_division", d)

    def test_whitespace_categories(self):
        s = shape(" \n\u00a0\u202fTexte ")
        self.assertEqual(s["leading_whitespace_codepoints"], 4)
        self.assertEqual(s["leading_ascii_spaces"], 1)
        self.assertEqual(s["leading_lf"], 1)
        self.assertEqual(s["leading_nbsp"], 1)
        self.assertEqual(s["leading_narrow_nbsp"], 1)
        self.assertEqual(s["trailing_whitespace_codepoints"], 1)

    def test_nonspace_substitution_is_detected(self):
        d = diff("**Ce", "*Ce")
        self.assertFalse(d["same_nonspace_characters"])
        self.assertFalse(d["same_leading_symbol"])

    def test_source_structure_requires_exact_refs(self):
        source = (
            b"<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'>"
            b"<osisText><div type='book' osisID='Gen'><chapter osisID='Gen.1'>"
            b"<p><verse osisID='Gen.1.1' sID='Gen.1.1'/>*A<verse eID='Gen.1.1'/></p>"
            b"</chapter></div></osisText></osis>"
        )
        d = source_structure(source, {"Gen.1.1"})
        self.assertEqual(d["Gen.1.1"]["authorial_container_chain"], ["p"])
        with self.assertRaises(ParagraphRenderingProbeError):
            source_structure(source, {"Gen.1.2"})


if __name__ == "__main__":
    unittest.main()
