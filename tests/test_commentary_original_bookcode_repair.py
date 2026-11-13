"""Original ThML annotation repair is exact-source-bound, reversible and PRIVATE."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_original_bookcode_repair import (
    propose_private_source_bookcode_repair,
)
from pilot_preflight import PilotError


def review(raw: bytes):
    return propose_private_source_bookcode_repair(
        raw, expected_source_sha256=sha256(raw).hexdigest(),
    )


class SourceDiv1BookMarkerRepairTests(unittest.TestCase):
    def setUp(self):
        self.patcher = patch(
            "commentary_original_bookcode_repair.read_existing_66_book_english_aliases",
            return_value=(
                {"Jude": "Jude", "Judg": "Judges", "Gen": "Genesis"},
                {"reviewed_test_registry": True},
            ),
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_only_two_original_conflicting_book_tokens_change_and_original_restored(self):
        raw = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<ThML>\n'
            b'  <div1 title="Jude">\n'
            b'    <scripCom osisRef="Bible:Judg.1.1"/>\n'
            b'    <div><p>Original Jude commentary text.</p></div>\n'
            b'    <scripCom osisRef="Bible:Judg.1.4-Judg.1.5"/>\n'
            b'    <div><p>Another original passage <scripRef osisRef="Bible:Gen.1.1">Genesis</scripRef>.</p></div>\n'
            b'  </div1>\n'
            b'  <div1 title="Genesis"><scripCom osisRef="Bible:Gen.1.1"/>\n'
            b'    <div>Unchanged authorial text.</div></div1>\n'
            b'</ThML>\n'
        )
        proposed, receipt = review(raw)
        expected = raw.replace(
            b'osisRef="Bible:Judg.1.1"',
            b'osisRef="Bible:Jude.1.1"',
        ).replace(
            b'osisRef="Bible:Judg.1.4-Judg.1.5"',
            b'osisRef="Bible:Jude.1.4-Jude.1.5"',
        )
        self.assertEqual(proposed, expected)
        self.assertEqual(receipt["reviewed_private_original_bookcode_replacements"], 2)
        self.assertEqual(receipt["all_original_scripCom_elements_preserved"], 3)
        self.assertEqual(
            receipt["original_source_sha256"], sha256(raw).hexdigest()
        )
        self.assertEqual(
            receipt["private_corrected_source_sha256"], sha256(expected).hexdigest()
        )
        self.assertTrue(receipt["original_source_byte_for_byte_restorable"])
        self.assertTrue(
            receipt["every_original_other_XML_text_title_note_reference_and_structure_unmodified"]
        )
        self.assertFalse(receipt["original_crosswire_sword_data_or_versification_changed"])
        self.assertFalse(receipt["source_owner_or_editor_approved"])
        self.assertFalse(receipt["public_release_authorized"])
        self.assertNotIn("Bible:Judg", str(receipt))
        self.assertNotIn("Bible:Jude", str(receipt))
        self.assertNotIn("Original Jude commentary", str(receipt))

    def test_mixed_original_claimed_codes_under_one_heading_not_guessed(self):
        raw = (b'<ThML><div1 title="Jude">'
               b'<scripCom osisRef="Bible:Judg.1.1"/><div>first</div>'
               b'<scripCom osisRef="Bible:Jude.1.2"/><div>second</div>'
               b'</div1></ThML>')
        candidate, evidence = review(raw)
        self.assertEqual(candidate, raw)
        self.assertEqual(evidence["reviewed_private_original_bookcode_replacements"], 0)

    def test_contains_heading_alias_is_not_exact_edition_source_title(self):
        raw = (b'<ThML><div1 title="Notes about Jude">'
               b'<scripCom osisRef="Bible:Judg.1.1"/><div>first</div>'
               b'</div1></ThML>')
        candidate, evidence = review(raw)
        self.assertEqual(candidate, raw)
        self.assertEqual(evidence["reviewed_private_original_bookcode_replacements"], 0)

    def test_original_has_no_silent_punctuation_or_reference_label_rewrite(self):
        raw = (
            b'<ThML><div1 title="Jude">'
            b'<scripCom osisRef="Bible:Judg.1.1"/><div>'
            b'<p>Original paragraph <scripRef osisRef="Bible:Judg.1.1">'
            b'not part of the SOURCE marker</scripRef>.</p></div></div1></ThML>'
        )
        candidate, _receipt = review(raw)
        self.assertIn(
            b'<scripRef osisRef="Bible:Judg.1.1">', candidate
        )
        self.assertIn(b'<scripCom osisRef="Bible:Jude.1.1"/>', candidate)

    def test_unreviewed_range_or_cross_book_endpoint_fails_closed(self):
        raw = (b'<ThML><div1 title="Jude">'
               b'<scripCom osisRef="Bible:Judg.1.1-Gen.1.2"/><div>first</div>'
               b'</div1></ThML>')
        with self.assertRaisesRegex(PilotError, "cross-book"):
            review(raw)

    def test_wrong_source_sha_or_untraceable_tag_bytes_refused(self):
        raw = (b'<ThML><div1 title="Jude">'
               b'<scripCom osisRef="Bible:Judg.1.1"/><div>first</div>'
               b'</div1></ThML>')
        with self.assertRaisesRegex(PilotError, "pinned SHA"):
            propose_private_source_bookcode_repair(
                raw, expected_source_sha256="a" * 64,
            )
        with self.assertRaisesRegex(PilotError, "byte positions"):
            review(
                b'<ThML><!-- <scripCom osisRef="Bible:Judg.1.1"/> -->'
                + raw[len(b'<ThML>'):]
            )

    def test_non_conflicting_original_remains_identical(self):
        raw = (b'<ThML><div1 title="Genesis">'
               b'<scripCom osisRef="Bible:Gen.1.1"/><div>first</div>'
               b'</div1></ThML>')
        candidate, receipt = review(raw)
        self.assertIs(candidate, raw)
        self.assertEqual(receipt["reviewed_private_original_bookcode_replacements"], 0)


if __name__ == "__main__":
    unittest.main()
