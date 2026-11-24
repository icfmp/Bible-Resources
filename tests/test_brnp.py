"""Synthetic, offline tests for the read-only BRNP v0.1 structural pilot."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_brnp import check  # noqa: E402
from normalize_osis import brnp_regressions  # noqa: E402

NS = 'http://www.bibletechnologies.net/2003/OSIS/namespace'


def document(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<osis xmlns="{NS}"><osisText osisIDWork="Demo" '
        f'osisRefWork="Bible"><header/><div type="book" osisID="Gen">'
        f'{body}</div></osisText></osis>'
    )


class BRNPStructuralPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "synthetic.osis.xml"

    def tearDown(self):
        self.temp.cleanup()

    def inspect(self, content, kind="bible"):
        self.path.write_text(content, encoding="utf-8")
        return check(self.path, kind)

    def test_bible_with_paragraph_and_paired_verses(self):
        xml = document(
            '<chapter osisID="Gen.1"><p>'
            '<verse osisID="Gen.1.1" sID="Gen.1.1"/>One.'
            '<verse eID="Gen.1.1"/>'
            '<verse osisID="Gen.1.2" sID="Gen.1.2"/>Two.'
            '<verse eID="Gen.1.2"/>'
            '</p></chapter>'
        )
        report = self.inspect(xml)
        self.assertEqual(report["status"], "diagnostic_only_schema_not_checked")
        self.assertFalse(report["brnp_conformance_certified"])
        self.assertEqual(report["verse_identifier_count"], 2)

    def test_commentary_entry_with_range(self):
        xml = document(
            '<div type="section" annotateType="commentary" '
            'annotateRef="Gen.1.1-Gen.1.2"><p>One note.</p></div>'
        )
        report = self.inspect(xml, "commentary")
        self.assertEqual(report["commentary_entry_count"], 1)
        self.assertEqual(report["finding_count"], 0)

    def test_standard_work_language_metadata(self):
        xml = document('<div annotateType="commentary" annotateRef="Gen.1.1" type="section"><p>Note</p></div>')
        xml = xml.replace("<header/>", '<header><work osisWork="Demo"><title>Demo</title><description>Test</description><language type="IETF">en</language></work></header>')
        self.assertEqual(self.inspect(xml, "commentary")["finding_count"], 0)

    def test_language_metadata_outside_work_header_rejected(self):
        xml = document('<div annotateType="commentary" annotateRef="Gen.1.1" type="section"><p><language>en</language>Note</p></div>')
        report = self.inspect(xml, "commentary")
        self.assertIn("INVALID_STRUCTURAL_PARENT", report["finding_codes"])

    def test_unmatched_verse_is_blocked(self):
        report = self.inspect(document(
            '<verse osisID="Gen.1.1" sID="Gen.1.1"/>Text'
        ))
        self.assertIn("UNCLOSED_VERSE_MILESTONE", [f["code"] for f in report["findings"]])

    def test_unknown_markup_is_blocked_without_loss(self):
        content = document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">A'
            '<invented>word</invented>.</verse></chapter>'
        )
        report = self.inspect(content)
        self.assertIn("UNREVIEWED_ELEMENT", [f["code"] for f in report["findings"]])
        self.assertEqual(report["finding_codes"]["UNREVIEWED_ELEMENT"], 1)
        self.assertEqual(report["unreviewed_elements"]["invented"], 1)
        self.assertEqual(report["finding_examples_by_code"]["UNREVIEWED_ELEMENT"]["element"], "invented")
        self.assertEqual(report["profile_version"], "0.3-draft")
        self.assertIn("<invented>word</invented>", self.path.read_text(encoding="utf-8"))

    def test_commentary_missing_reference_is_blocked(self):
        report = self.inspect(document(
            '<div annotateType="commentary"><p>Note</p></div>'
        ), "commentary")
        self.assertIn("ANNOTATE_REF", [f["code"] for f in report["findings"]])

    def test_reports_do_not_include_source_prose(self):
        report = self.inspect(document(
            '<verse osisID="Gen.1.1">Private sentinel phrase</verse>'
        ))
        self.assertNotIn("Private sentinel phrase", json.dumps(report))
        self.assertFalse(report["publication_approved"])
        self.assertEqual(report["official_osis"]["status"], "not_run")


    def test_duplicate_book_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse></chapter>'
            '<div type="book" osisID="Gen"><chapter osisID="Gen.2">'
            '<verse osisID="Gen.2.1">Two</verse></chapter></div>'
        ))
        self.assertIn("BOOK_ID", [f["code"] for f in report["findings"]])

    def test_unclosed_chapter_milestone_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="Gen.1"/>'
            '<verse osisID="Gen.1.1">One</verse>'
        ))
        self.assertIn("UNCLOSED_CHAPTER_MILESTONE", [f["code"] for f in report["findings"]])

    def test_chapter_pair_is_accepted(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="Gen.1"/>'
            '<verse osisID="Gen.1.1">One</verse>'
            '<chapter eID="Gen.1"/>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["chapter_identifier_count"], 1)

    def test_duplicate_chapter_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse></chapter>'
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.2">Two</verse></chapter>'
        ))
        self.assertIn("CHAPTER_CONTAINER_ID", [f["code"] for f in report["findings"]])


    def test_official_osis_table_and_list_are_not_flattened(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
            '<table><row><cell>Cell</cell></row></table>'
            '<list><item>Item</item></list></chapter>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["element_counts"]["cell"], 1)

    def test_commentary_repeated_book_divisions_not_rejected_as_bible_duplicates(self):
        report = self.inspect(document(
            '<div type="book" osisID="Gen"><div type="section" '
            'annotateType="commentary" annotateRef="Gen.1.1">'
            '<p>First</p></div></div>'
            '<div type="book" osisID="Gen"><div type="section" '
            'annotateType="commentary" annotateRef="Gen.1.2">'
            '<p>Second</p></div></div>'
        ), kind="commentary")
        self.assertIn("COMMENTARY_REPEATED_BOOK_DIVISION", report["finding_codes"])
        self.assertEqual(report["commentary_entry_count"], 2)


    def test_osis_milestone_pairing_id_may_differ_from_canonical_osis_id(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1" sID="v-001"/>'
            'Text<verse eID="v-001"/></chapter>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["verse_identifier_count"], 1)


    def test_canonical_and_pairing_ids_are_independently_unique(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1">'
            '<verse osisID="Gen.1.1" sID="v-001"/>One<verse eID="v-001"/>'
            '<verse osisID="Gen.1.1" sID="v-002"/>Two<verse eID="v-002"/>'
            '</chapter>'
        ))
        self.assertIn("VERSE_START_ID", report["finding_codes"])
        self.assertEqual(report["verse_start_reasons"]["duplicate_osisID"], 1)

    def test_repeated_pairing_key_is_blocked_even_for_different_verses(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1">'
            '<verse osisID="Gen.1.1" sID="v-001"/>One<verse eID="v-001"/>'
            '<verse osisID="Gen.1.2" sID="v-001"/>Two<verse eID="v-001"/>'
            '</chapter>'
        ))
        self.assertEqual(report["verse_start_reasons"]["duplicate_sID"], 1)

    def test_wrong_table_cell_or_list_item_parent_is_blocked(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
            '<cell>Wrongly detached cell</cell>'
            '<list><row><item>Wrongly detached item</item></row></list>'
            '</chapter>'
        ))
        self.assertGreaterEqual(report["finding_codes"]["INVALID_STRUCTURAL_PARENT"], 3)

    def test_bible_chapter_cannot_be_in_wrong_book(self):
        report = self.inspect(document(
            '<chapter osisID="Exod.1"><verse osisID="Exod.1.1">Text</verse></chapter>'
        ))
        self.assertIn("REFERENCE_BOOK_SCOPE", report["finding_codes"])

    def test_bible_verse_cannot_claim_different_chapter(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.2.1">Text</verse></chapter>'
        ))
        self.assertIn("REFERENCE_CHAPTER_SCOPE", report["finding_codes"])

    def test_bible_verse_cannot_appear_outside_book(self):
        report = self.inspect(
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<osis xmlns="{NS}"><osisText osisIDWork="Demo" osisRefWork="Bible">'
            '<header/><verse osisID="Gen.1.1">Text</verse></osisText></osis>'
        )
        self.assertIn("BOOK_SCOPE", report["finding_codes"])

    def test_nested_book_is_rejected(self):
        report = self.inspect(document(
            '<div type="book" osisID="Exod"><chapter osisID="Exod.1">'
            '<verse osisID="Exod.1.1">Text</verse></chapter></div>'
        ))
        self.assertIn("NESTED_BOOK", report["finding_codes"])

    def test_distinct_verse_pair_id_does_not_change_chapter_scope(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><p><verse osisID="Gen.1.1" sID="verse-a"/>'
            'Text<verse eID="verse-a"/></p></chapter>'
        ))
        self.assertNotIn("REFERENCE_CHAPTER_SCOPE", report["finding_codes"])
        self.assertEqual(report["finding_count"], 0)

    def test_duplicate_member_of_compound_bible_verse_is_rejected(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1">'
            '<verse osisID="Gen.1.1 Gen.1.2">Combined</verse>'
            '<verse osisID="Gen.1.2">Duplicated member</verse>'
            '</chapter>'
        ))
        self.assertIn("VERSE_CONTAINER_ID", report["finding_codes"])

    def test_verse_scope_under_chapter_milestone(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="chapter-1"/>'
            '<p><verse osisID="Gen.2.1" sID="v1"/>Wrong chapter'
            '<verse eID="v1"/></p><chapter eID="chapter-1"/>'
        ))
        self.assertIn("REFERENCE_CHAPTER_SCOPE", report["finding_codes"])

    def test_chapter_milestone_pair_id_can_differ_from_canonical(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="chapter-a"/>'
            '<p><verse osisID="Gen.1.1" sID="v1"/>Correct'
            '<verse eID="v1"/></p><chapter eID="chapter-a"/>'
        ))
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["chapter_pair_identifier_count"], 1)

    def test_duplicate_chapter_pair_key_is_rejected(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="chapter-a"/>'
            '<verse osisID="Gen.1.1">First</verse><chapter eID="chapter-a"/>'
            '<chapter osisID="Gen.2" sID="chapter-a"/>'
            '<verse osisID="Gen.2.1">Second</verse><chapter eID="chapter-a"/>'
        ))
        self.assertIn("CHAPTER_START_ID", report["finding_codes"])

    def test_normalizer_detects_new_finding_class_even_if_total_decreases(self):
        before = {"finding_codes": {"INVALID_STRUCTURAL_PARENT": 3}}
        after = {"finding_codes": {"BOOK_SCOPE": 1}}
        self.assertEqual(brnp_regressions(before, after), {"BOOK_SCOPE": 1})

    def test_normalizer_accepts_only_nonincreasing_finding_counts(self):
        before = {"finding_codes": {"BOOK_SCOPE": 2, "VERSE_END_PAIR": 1}}
        after = {"finding_codes": {"BOOK_SCOPE": 1}}
        self.assertEqual(brnp_regressions(before, after), {})

    def test_reversed_commentary_range_is_rejected_by_shared_guard(self):
        report = self.inspect(document(
            '<div type="section" annotateType="commentary" '
            'annotateRef="Gen.1.9-Gen.1.2"><p>Note.</p></div>'
        ), kind="commentary")
        self.assertIn("COMMENTARY_REFERENCE_INVALID", report["finding_codes"])

    def test_unreviewed_commentary_work_prefix_is_rejected(self):
        report = self.inspect(document(
            '<div type="section" annotateType="commentary" '
            'annotateRef="Bible:Gen.1.1"><p>Note.</p></div>'
        ), kind="commentary")
        self.assertIn("COMMENTARY_REFERENCE_INVALID", report["finding_codes"])

    def test_unresolved_cross_reference_must_not_be_guessed(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">'
            '<reference>See some passage</reference></verse></chapter>'
        ))
        self.assertIn("UNRESOLVED_REFERENCE_TARGET", report["finding_codes"])

    def test_reviewed_cross_reference_is_accepted(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">'
            '<reference osisRef="Gen.1.2">See another verse</reference>'
            '</verse></chapter>'
        ))
        self.assertNotIn("UNRESOLVED_REFERENCE_TARGET", report["finding_codes"])

    def test_poetry_line_requires_reviewed_stanza_group(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><l>Ungrouped line</l>'
            '<verse osisID="Gen.1.1">Text</verse></chapter>'
        ))
        self.assertIn("POETRY_LINE_OUTSIDE_GROUP", report["finding_codes"])

    def test_grouped_poetry_is_accepted(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><lg><l>First line</l>'
            '<l>Second line</l></lg><verse osisID="Gen.1.1">Text</verse></chapter>'
        ))
        self.assertNotIn("POETRY_LINE_OUTSIDE_GROUP", report["finding_codes"])

    def test_book_milestone_inside_book_is_not_a_second_container(self):
        report = self.inspect(document(
            '<div type="book" osisID="Gen" sID="gen-marker"/>'
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">Text</verse></chapter>'
            '<div type="book" osisID="Gen" eID="gen-marker"/>'
        ))
        self.assertNotIn("NESTED_BOOK", report["finding_codes"])
        self.assertNotIn("BOOK_ID", report["finding_codes"])
        self.assertEqual(report["finding_codes"]["BOOK_MILESTONE_WITHIN_CONTAINER"], 1)
        self.assertEqual(report["book_identifier_count"], 1)

    def test_repeated_book_milestone_pair_key_is_flagged(self):
        report = self.inspect(document(
            '<div type="book" osisID="Gen" sID="same"/>'
            '<div type="book" osisID="Gen" sID="same"/>'
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">Text</verse></chapter>'
            '<div type="book" osisID="Gen" eID="same"/>'
            '<div type="book" osisID="Gen" eID="same"/>'
        ))
        self.assertEqual(report["finding_codes"]["DUPLICATE_BOOK_MILESTONE_KEY"], 1)
        self.assertNotIn("UNCLOSED_BOOK_MILESTONE", report["finding_codes"])

    def test_origin_metadata_is_not_a_missing_link_target(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">'
            '<note type="crossReference"><reference type="annotateRef" '
            'subType="x-origin">1.1</reference>'
            '<reference>Other chapter</reference></note>'
            '</verse></chapter>'
        ))
        self.assertEqual(report["finding_codes"]["NONCANONICAL_REFERENCE_ORIGIN"], 1)
        self.assertEqual(report["finding_codes"]["UNRESOLVED_REFERENCE_TARGET"], 1)

    def test_intro_span_is_not_misreported_as_note_crosslink(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">Text</verse>'
            '<list><item><reference subType="x-introduction">'
            '1:1–2:23</reference></item></list></chapter>'
        ))
        self.assertEqual(report["finding_codes"]["UNRESOLVED_INTRODUCTION_SPAN"], 1)

    def test_source_unchanged(self):
        content = document('<verse osisID="Gen.1.1">Test</verse>')
        self.path.write_text(content, encoding="utf-8")
        before = self.path.read_bytes()
        check(self.path, "bible")
        self.assertEqual(before, self.path.read_bytes())



    def test_paired_commentary_crosses_paragraphs_and_poetry(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="ch"/>'
            '<p>Original heading<verse osisID="Gen.1.1 Gen.1.2" sID="a"/>'
            'First paragraph.</p><lg><l>Original poetry<verse eID="a"/></l></lg>'
            '<chapter eID="ch"/>'), "commentary")
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["commentary_representation"], "paired_verse_milestones")
        self.assertEqual(report["paired_commentary_entry_count"], 1)
        self.assertEqual(report["paired_commentary_member_count"], 2)

    def test_paired_commentary_under_chapter_container(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1"><p><verse osisID="Gen.1.1" sID="v"/>'
            'One<verse eID="v"/></p></chapter>'), "commentary")
        self.assertEqual(report["finding_count"], 0)

    def test_paired_commentary_strict_negative_cases(self):
        cases = [
            ('<verse osisID="Gen.1.1 Gen.1.2" sID="a"/>A<verse eID="a"/>'
             '<verse osisID="Gen.1.2 Gen.1.3" sID="b"/>B<verse eID="b"/>',
             "COMMENTARY_MILESTONE_MEMBER_ID"),
            ('<verse osisID="Gen.1.1" sID="a"/>A<verse eID="a"/>'
             '<verse osisID="Gen.1.2" sID="a"/>B<verse eID="a"/>',
             "COMMENTARY_MILESTONE_PAIR_ID"),
            ('<verse osisID="Gen.1.1" sID="a"/>A'
             '<verse osisID="Gen.1.2" sID="b"/>B<verse eID="b"/><verse eID="a"/>',
             "COMMENTARY_MILESTONE_OVERLAP"),
            ('<verse osisID="Gen.1.1" sID="a"/>A<verse eID="b"/>',
             "COMMENTARY_MILESTONE_PAIR"),
            ('<verse osisID="Gen.1.1" sID="a"/>A',
             "COMMENTARY_MILESTONE_UNCLOSED"),
            ('<verse osisID="Exod.1.1" sID="a"/>A<verse eID="a"/>',
             "COMMENTARY_MILESTONE_SCOPE"),
            ('<verse osisID="Gen.2.1" sID="a"/>A<verse eID="a"/>',
             "COMMENTARY_MILESTONE_SCOPE"),
            ('<verse osisID="Gen.1.0" sID="a"/>A<verse eID="a"/>',
             "COMMENTARY_MILESTONE_MEMBER_ID"),
            ('<verse osisID="Gen.1.3 Gen.1.2" sID="a"/>A<verse eID="a"/>',
             "COMMENTARY_MILESTONE_MEMBER_ORDER"),
            ('<verse osisID="Gen.1.1">A</verse>',
             "COMMENTARY_MILESTONE_FORM"),
            ('<verse osisID="Gen.1.1" sID="a"/>A<verse eID="a"/>'
             '<div annotateType="commentary" annotateRef="Gen.1.2">B</div>',
             "COMMENTARY_MIXED_REPRESENTATIONS"),
            ('<verse osisID="Gen.1.1" sID="a">A</verse><verse eID="a"/>',
             "COMMENTARY_MILESTONE_NONEMPTY_MARKER"),
        ]
        for body, expected in cases:
            with self.subTest(expected=expected):
                report = self.inspect(document(
                    '<chapter osisID="Gen.1" sID="ch"/><p>'+body+
                    '</p><chapter eID="ch"/>'), "commentary")
                self.assertIn(expected, report["finding_codes"])

    def test_paired_commentary_cannot_cross_chapter_boundary(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="a"/><p>'
            '<verse osisID="Gen.1.1" sID="v"/>One</p><chapter eID="a"/>'
            '<chapter osisID="Gen.2" sID="b"/><p>Two<verse eID="v"/></p>'
            '<chapter eID="b"/>'), "commentary")
        self.assertIn("COMMENTARY_MILESTONE_CHAPTER_BOUNDARY", report["finding_codes"])

    def test_paired_commentary_requires_chapter_scope(self):
        report = self.inspect(document(
            '<p><verse osisID="Gen.1.1" sID="v"/>One<verse eID="v"/></p>'),
            "commentary")
        self.assertIn("COMMENTARY_MILESTONE_SCOPE", report["finding_codes"])

    def test_paired_commentary_does_not_waive_other_diagnostics(self):
        report = self.inspect(document(
            '<chapter osisID="Gen.1" sID="ch"/><p>'
            '<verse osisID="Gen.1.1" sID="v"/>'
            '<reference osisRef=" Gen.1.2">Link</reference>'
            '<verse eID="v"/></p><chapter eID="ch"/>'), "commentary")
        self.assertEqual(report["finding_codes"], {"REFERENCE_TARGET_WHITESPACE": 1})


if __name__ == "__main__":
    unittest.main()
