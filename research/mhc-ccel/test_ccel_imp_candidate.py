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

    def test_genuine_duplicate_source_starts_reported_without_merging(self):
        raw = source('<scripCom osisRef="Bible:Gen.1.1-Gen.1.2"/>'
                     '<div><p>First original section</p></div>'
                     '<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'
                     '<div><p>Second distinct original section</p></div>')
        census = candidate.inspect_volume_start_collisions(
            raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(census["original_verse_or_range_sections"], 2)
        self.assertEqual(census["distinct_original_start_addresses"], 1)
        self.assertEqual(census["duplicated_original_start_groups"], 1)
        self.assertEqual(census["additional_sections_sharing_original_start"], 1)
        self.assertEqual(census["additional_sections_different_full_ref"], 1)
        self.assertEqual(census["additional_sections_different_markup_body_to_prior"], 1)
        self.assertFalse(census["safe_to_write_one_section_per_sword_key"])
        self.assertFalse(census["original_sections_reordered_or_merged"])

    def test_quarantine_all_original_divisions_with_duplicate_starts(self):
        raw = source('<scripCom osisRef="Bible:Gen.1.1-Gen.1.2"/>'
                     '<div><p>First original section</p></div>'
                     '<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'
                     '<div><p>Second original section</p></div>'
                     '<scripCom osisRef="Bible:Gen.1.4"/>'
                     '<div><p>Third unaffected section</p></div>')
        rows, stats, digest = candidate.extract_volume(
            raw, hashlib.sha256(raw).hexdigest(),
            quarantine_repeated_starts=True)
        self.assertEqual([key for key, _ in rows], ["Gen.1.4"])
        self.assertEqual(stats["verse_or_range_bodies"], 3)
        self.assertEqual(stats["original_source_bodies_quarantined"], 2)
        self.assertEqual(stats["original_colliding_start_groups_quarantined"], 1)
        self.assertIn("Third unaffected section", rows[0][1])
        self.assertNotIn("First original section", rows[0][1])
        self.assertEqual(len(digest), 64)

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
