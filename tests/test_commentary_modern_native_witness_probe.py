"""Read-only lexical source-witness checks on synthetic, harmless XML."""
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_modern_native_witness_probe import (
    word_tokens, anchor_found, visible_text_and_references)


class SourceWitnessProbeTests(unittest.TestCase):
    def test_ordered_punctuation_normalization(self):
        words = word_tokens("Whenever we enter God's presence, give thanks for grace.")
        self.assertTrue(anchor_found(words, "enter God's presence give thanks"))
        self.assertFalse(anchor_found(words, "give God's presence enter thanks"))
        self.assertFalse(anchor_found(words, "enter their presence give thanks"))

    def test_does_not_match_missing_source_clause(self):
        words = word_tokens("The beginning of an author's paragraph stops here.")
        self.assertFalse(anchor_found(words, "the end of another paragraph is absent"))

    def test_probe_bounded_to_real_multiple_word_evidence(self):
        with self.assertRaisesRegex(ValueError, "4–18"):
            anchor_found(word_tokens("one two three four"), "one")
        with self.assertRaisesRegex(ValueError, "4–18"):
            anchor_found(word_tokens("one two three four"),
                         " ".join(["word"] * 19))

    def test_source_xml_text_and_reference_targets_not_automatically_rewritten(self):
        raw = (b'<div><title>PRIVATE HEADER</title><p>PRIVATE example '
               b'<reference osisRef="Ps.110.3">Psalm 110:3</reference> '
               b'and an <note>original note</note></p></div>')
        text, refs, marks = visible_text_and_references(raw)
        self.assertIn("PRIVATE", text)
        self.assertEqual(refs, ["Ps.110.3"])
        self.assertEqual(marks["reference_tags"], 1)
        self.assertEqual(marks["note_tags"], 1)
        self.assertEqual(marks["title_tags"], 1)
        self.assertEqual(marks["paragraph_tags"], 1)

    def test_malformed_original_xml_does_not_pass(self):
        with self.assertRaises(ET.ParseError):
            visible_text_and_references(b"<div>broken")


if __name__ == "__main__":
    unittest.main()
