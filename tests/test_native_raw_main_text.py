"""Synthetic regression for the shared OSIS/USFX-independent SWORD raw reader."""
import unittest

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from research.bible.native_raw_main_text import (
    native_raw_main_text, MainTextParityError,
)


class NativeRawMainTextTests(unittest.TestCase):
    def test_notes_and_titles_are_excluded_but_numbered_words_remain(self):
        text, skipped = native_raw_main_text(
            b'<p>Alpha <note>PRIVATE NOTE</note>beta'
            b'<title>PRIVATE TITLE</title> gamma.</p>')
        self.assertEqual(text, "Alpha beta gamma.")
        self.assertEqual(skipped, {"note": 1, "title": 1})

    def test_malformed_native_fragment_fails_closed(self):
        with self.assertRaises(MainTextParityError):
            native_raw_main_text(b'<p>unclosed text')

    def test_declared_dtd_and_xml_are_rejected(self):
        for raw in (b'<!DOCTYPE foo><p>text</p>',
                    b'<?xml version="1.0"?><p>text</p>'):
            with self.subTest(raw=raw), self.assertRaises(MainTextParityError):
                native_raw_main_text(raw)


if __name__ == "__main__":
    unittest.main()
