"""Strict synthetic safeguards for the private CCEL MHC verse/range experiment."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "candidate", Path(__file__).with_name("ccel_imp_candidate.py"))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def source(content):
    return ('<?xml version="1.0" encoding="utf-8"?><ThML><head><title>'
            + 'T' * 1000 + '</title></head><body><div1><div2>' + content +
            '</div2></div1></body></ThML>').encode()


class Extract(unittest.TestCase):
    def test_thml_body_original_content_kept_and_chapter_marker_not_misused(self):
        raw = source('<scripCom osisRef="Bible:Gen.1"/>'
                     '<scripCom osisRef="Bible:Gen.1.1-Gen.1.4"/>'
                     '<div><p>One\ntwo <i>three</i>.</p><p>Four &amp; five</p></div>')
        rows, stats, digest = candidate.extract_volume(
            raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(stats['chapter_markers_unhandled'], 1)
        self.assertEqual(stats['verse_or_range_bodies'], 1)
        self.assertEqual(rows[0][0], 'Gen.1.1-Gen.1.4')
        self.assertIn('&#10;', rows[0][1])
        self.assertIn('<i>three</i>', rows[0][1])
        self.assertEqual(len(digest), 64)

    def test_unknown_reference_fails_closed(self):
        raw = source('<scripCom osisRef="Bible:Gen.1.999-EXTRA"/>'
                     '<div><p>Text</p></div>')
        with self.assertRaisesRegex(ValueError, 'Unclassified'):
            candidate.extract_volume(raw, hashlib.sha256(raw).hexdigest())

    def test_duplicate_verse_start_fails_closed(self):
        raw = source('<scripCom osisRef="Bible:Gen.1.1"/><div><p>A</p></div>'
                     '<scripCom osisRef="Bible:Gen.1.1"/><div><p>B</p></div>')
        with self.assertRaisesRegex(ValueError, 'Collision'):
            candidate.extract_volume(raw, hashlib.sha256(raw).hexdigest())

    def test_modified_source_fails_pin(self):
        raw = source('<scripCom osisRef="Bible:Gen.1.1"/><div><p>A</p></div>')
        with self.assertRaisesRegex(ValueError, 'digest'):
            candidate.extract_volume(raw, '0' * 64)

    def test_chapter_marker_not_body_fails_closed(self):
        raw = source('<scripCom osisRef="Bible:Gen.1"/><div><p>chapter intro</p></div>')
        with self.assertRaisesRegex(ValueError, 'chapter marker'):
            candidate.extract_volume(raw, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
