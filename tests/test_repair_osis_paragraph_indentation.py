"""OSIS paragraph whitespace repair is strict, reversible and never changes notes."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from repair_osis_paragraph_indentation import (
    ParagraphWhitespaceError, trim_publisher_paragraph_indentation,
)
from publisher_osis_usfx_parity import original_osis_verses_and_notes

SOURCE = b"""<?xml version='1.0' encoding='utf-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'>
<osisText><div type='book' osisID='Gen'><chapter osisID='Gen.1'>
<p><verse osisID='Gen.1.1' sID='Gen.1.1'/>
            Paragraph start<note n='a'>Unmodified note.</note>
<verse eID='Gen.1.1'/></p>
<l><verse osisID='Gen.1.2' sID='Gen.1.2'/>
            Poetry must preserve its whitespace<verse eID='Gen.1.2'/></l>
<p><verse osisID='Gen.1.3' sID='Gen.1.3'/>
              Another paragraph<verse eID='Gen.1.3'/></p>
<p><verse osisID='Gen.1.4' sID='Gen.1.4'/> Authored inline whitespace stays<verse eID='Gen.1.4'/></p>
</chapter></div></osisText></osis>
"""


def run(src=SOURCE):
    return trim_publisher_paragraph_indentation(src, expected_sha256=sha256(src).hexdigest())


class TestPrivateParagraphIndentation(unittest.TestCase):
    def test_only_exact_p_xml_indent_removed(self):
        result, receipt = run()
        self.assertEqual(receipt["counts"]["paragraphs_with_exact_xml_indent"], 2)
        self.assertEqual(receipt["counts"]["formatting_spaces_removed"], 26)
        self.assertIn(b"Paragraph start", result)
        self.assertIn(b"Another paragraph", result)
        self.assertNotIn(b"\n            Paragraph start", result)
        self.assertNotIn(b"\n              Another paragraph", result)
        self.assertIn(b"\n            Poetry must preserve its whitespace", result)
        self.assertIn(b"/> Authored inline whitespace stays", result)
        a, notes_a, _ = original_osis_verses_and_notes(SOURCE)
        b, notes_b, _ = original_osis_verses_and_notes(result)
        self.assertEqual(notes_a, notes_b)
        self.assertEqual(a["Gen.1.2"], b["Gen.1.2"])
        self.assertEqual(a["Gen.1.4"], b["Gen.1.4"])
        self.assertFalse(receipt["native_reader_indentation_reduction_proved"])

    def test_source_hash_required(self):
        with self.assertRaises(ParagraphWhitespaceError):
            trim_publisher_paragraph_indentation(SOURCE, expected_sha256="0"*64)

    def test_undocumented_indent_within_verse_is_not_modified(self):
        changed = SOURCE.replace(b"Paragraph start", b"Paragraph start\n            text")
        result, _ = run(changed)
        self.assertIn(b"Paragraph start\n            text", result)


if __name__ == "__main__":
    unittest.main()
