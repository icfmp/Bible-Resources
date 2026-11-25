"""Synthetic, offline tests for the read-only BRNP v0.1 structural pilot."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_brnp import check, canonical_digest, unlinked_review_inventory, inspect_approved_osis  # noqa: E402
from hashlib import sha256
from lxml import etree
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
        self.assertEqual(report["profile_version"], "0.4")
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



class BRNPReviewedUnlinkedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.path = root / "source.xml"
        self.receipt = root / "receipt.json"
        self.xml = document('<chapter osisID="Gen.1"><verse osisID="Gen.1.1">Text'
                            '<note type="crossReference" n="a"><reference type="annotateRef" '
                            'subType="x-origin" osisRef="Gen.1.1">1.1</reference>'
                            '<reference>Unresolved original label.</reference></note>'
                            '</verse></chapter>')
        self.path.write_text(self.xml, encoding="utf-8")
        _, entries, count = unlinked_review_inventory(etree.fromstring(self.path.read_bytes()))
        self.review = {
            "schema_version": 1, "status": "exact_reviewed_unlinked_preservation_evidence",
            "current_master_sha256": sha256(self.path.read_bytes()).hexdigest(),
            "historically_reviewed_master_sha256": "a" * 64,
            "original_usfx_archive_sha256": "b" * 64,
            "historical_approval_manifest_sha256": "c" * 64,
            "historical_review": "synthetic fixture", "current_release_review": "synthetic fixture",
            "all_unlinked_reference_indices_reconciled": True,
            "destination_semantics_certified": False, "mandatory_gate_approved": False,
            "entries_sha256": canonical_digest(entries), "source_notes_reconciled": count,
            "preserved_unlinked_groups": len(entries),
        }

    def tearDown(self):
        self.temp.cleanup()

    def inspect(self):
        self.receipt.write_text(json.dumps(self.review), encoding="utf-8")
        return check(self.path, "bible", review_receipt=self.receipt,
                     review_receipt_sha256=sha256(self.receipt.read_bytes()).hexdigest())

    def test_unlinked_requires_explicit_receipt(self):
        self.assertEqual(check(self.path, "bible")["finding_codes"], {"UNRESOLVED_REFERENCE_TARGET": 1})
        before = self.path.read_bytes()
        report = self.inspect()
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["reviewed_unlinked_reference_count"], 1)
        self.assertFalse(report["brnp_conformance_certified"])
        self.assertFalse(report["publication_approved"])
        self.assertNotIn("Unresolved original label.", json.dumps(report))
        self.assertEqual(report, self.inspect())
        self.assertEqual(before, self.path.read_bytes())

    def test_changed_source_rejects_old_receipt(self):
        for mutation in ("Unresolved changed label.", "Unresolved original label!"):
            self.path.write_text(self.xml.replace("Unresolved original label.", mutation))
            with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_MASTER_CHANGED"):
                self.inspect()

    def test_new_unreviewed_label_does_not_inherit_review(self):
        self.path.write_text(self.xml.replace("</verse>", '<reference>Another label.</reference></verse>'))
        with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_MASTER_CHANGED"):
            self.inspect()

    def test_count_alone_cannot_approve_changed_label(self):
        self.path.write_text(self.xml.replace("Unresolved original label.", "Different label."))
        self.review["current_master_sha256"] = sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_INVENTORY_CHANGED"):
            self.inspect()

    def test_changed_receipt_pin_is_rejected(self):
        self.inspect()
        with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_RECEIPT_CHANGED"):
            check(self.path, "bible", review_receipt=self.receipt, review_receipt_sha256="0"*64)

    def test_receipt_does_not_certify_destination_or_gate(self):
        for key in ("destination_semantics_certified", "mandatory_gate_approved"):
            self.review[key] = True
            with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_SCOPE"):
                self.inspect()
            self.review[key] = False

    def test_blank_target_or_nested_markup_not_eligible(self):
        for fragment in ('<reference osisRef="">Unresolved original label.</reference>',
                         '<reference><hi type="italic">Unresolved original label.</hi></reference>'):
            self.path.write_text(self.xml.replace('<reference>Unresolved original label.</reference>', fragment))
            self.review["current_master_sha256"] = sha256(self.path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "BRNP_REVIEW_INVENTORY_CHANGED"):
                self.inspect()



class BRNPPublicationGateTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        folder = self.root / "sources/cleaned/bibles/fr/synthetic"
        folder.mkdir(parents=True)
        self.source = folder / "synthetic.osis.xml"
        self.source.write_text(document('<chapter osisID="Gen.1"><verse osisID="Gen.1.1">Text</verse></chapter>'))
        mdir = self.root / "modules/synthetic"
        mdir.mkdir(parents=True)
        (mdir / "metadata.json").write_text(json.dumps({"id":"synthetic","category":"bible","language":"fr","version":"1.0.0","quality":{"status":"approved"}}))
        self.proof = mdir / "SOURCE_VALIDATION.json"
        self.proof.write_text(json.dumps({"status":"validated","source_sha256":sha256(self.source.read_bytes()).hexdigest()}))
        (self.root / "config").mkdir()
        (self.root / "config/brnp-reviewed-unlinked.json").write_text('{"schema_version":1,"reviewed_receipts":{}}')
        self.schema = self.root / "pinned.xsd"
        self.real_check = check
        # Only the independent schema backend is stubbed in these small
        # control-flow fixtures. Real pinned XSD is required on all editions
        # in the integration workflow.
        def fixture_check(source, kind, **kwargs):
            self.assertEqual(kwargs.pop("schema_path"), self.schema)
            report = self.real_check(source, kind, **kwargs)
            report["official_osis"] = {"status":"validated"}
            return report
        self.patcher = patch("check_brnp.check", side_effect=fixture_check)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_gate_accepts_exact_approved_master_without_modifying_bytes(self):
        before = self.source.read_bytes()
        result = inspect_approved_osis(self.root, self.schema)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["finding_count"], 0)
        self.assertEqual(before, self.source.read_bytes())

    def test_gate_rejects_unresolved_candidate_even_when_source_receipt_updated(self):
        self.source.write_text(document('<chapter osisID="Gen.1"><verse osisID="Gen.1.1"><reference>Unknown label</reference></verse></chapter>'))
        self.proof.write_text(json.dumps({"status":"validated","source_sha256":sha256(self.source.read_bytes()).hexdigest()}))
        self.assertEqual(inspect_approved_osis(self.root,self.schema,enforce=False)[0]["finding_count"],1)
        with self.assertRaisesRegex(ValueError, "BRNP_PUBLICATION_BLOCKED"):
            inspect_approved_osis(self.root,self.schema)

    def test_gate_rejects_unbound_or_missing_master(self):
        self.source.write_text(self.source.read_text().replace("Text","Changed"))
        with self.assertRaisesRegex(ValueError, "BRNP_APPROVED_SOURCE_MISMATCH"):
            inspect_approved_osis(self.root,self.schema)
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, "BRNP_MASTER_MISSING_OR_AMBIGUOUS"):
            inspect_approved_osis(self.root,self.schema)

    def test_unverified_header_revision_cannot_override_approval_hash(self):
        data = json.loads(self.proof.read_text())
        data["header_revision"] = {"candidate_source_sha256": sha256(self.source.read_bytes()).hexdigest()}
        self.proof.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "BRNP_HEADER_REVISION_UNSUPPORTED"):
            inspect_approved_osis(self.root,self.schema)

    def test_publisher_requires_gate_before_coverage_or_public_write(self):
        from unittest.mock import patch
        import publish_reviewed_release as publisher
        argv=["publisher","--root",str(self.root),"--built",str(self.root),
              "--repository","owner/repo","--target-sha","a"*40,"--brnp-schema",str(self.schema)]
        with patch.object(sys,"argv",argv), patch("check_brnp.inspect_approved_osis",side_effect=ValueError("blocked")), patch.object(publisher,"coverage") as coverage, patch.object(publisher,"publish_one") as publish:
            with self.assertRaisesRegex(publisher.ReleaseError,"BRNP structural"):
                publisher.main()
            coverage.assert_not_called()
            publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
