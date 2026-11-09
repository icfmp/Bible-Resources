"""Semantic OSIS source-fidelity regression tests, edition neutral and offline.

These are distinct synthetic OSIS source designs. They are not a source→
compiled-SWORD acceptance proof or an editorially approved new translation.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from osis_semantic_fidelity import (
    compare_semantics, semantic_snapshot, _write_new_report, FidelityError,
)
from source_osis_inventory import SourceInventoryError

NS = 'xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"'


def rich_document():
    return (f'<osis {NS}><osisText osisIDWork="Original">'
            '<div type="book" osisID="Alpha">'
            '<title>Before chapter one</title>'
            '<chapter osisID="Alpha.1" sID="c1"/>'
            '<title type="section">Intro title</title>'
            '<verse osisID="Alpha.1.1" sID="v1"/>'
            '<p sID="p1"/>'
            '<w lemma="strong:A1" morph="x">In</w> the '
            '<w lemma="strong:A2">beginning</w>, '
            '<note type="study" n="a">a note <hi type="italic">with markup</hi></note>'
            '<reference osisRef="Alpha.1.2">next verse</reference>'
            '<l sID="line1"/>poetry.'
            '<l eID="line1"/>'
            '<p eID="p1"/>'
            '<verse eID="v1"/>'
            '<verse osisID="Alpha.1.2"><w lemma="strong:A3">Again</w>!</verse>'
            '<chapter eID="c1"/>'
            '</div></osisText></osis>').encode("utf-8")


def different_edition():
    return (f'<osis {NS}><osisText osisIDWork="Alternative">'
            '<div type="book" osisID="Beta">'
            '<chapter osisID="Beta.1"><verse osisID="Beta.1.1">'
            'Line <w>one</w>! '
            '<note type="translation" n="b">translator note</note>'
            '</verse><verse osisID="Beta.1.2">Two.</verse></chapter>'
            '</div><div type="book" osisID="Gamma">'
            '<chapter osisID="Gamma.1"><verse osisID="Gamma.1.1">'
            '<lg><l>Different poetry</l></lg>'
            '</verse></chapter>'
            '</div></osisText></osis>').encode("utf-8")


class SemanticOsisTests(unittest.TestCase):
    def expect_block(self, old, changed, lane):
        report = compare_semantics(old, changed)
        self.assertEqual(report["status"],
                         "blocked_source_to_candidate_semantic_drift")
        self.assertIn(lane, report["different_lanes_book_counts"])
        self.assertFalse(report["compiled_stock_sword_reader_semantics_verified"])
        self.assertFalse(report["approved_for_publication"])
        return report

    def test_rich_source_self_comparison_preserves_every_stream(self):
        old = rich_document()
        report = compare_semantics(old, old)
        self.assertEqual(report["status"], "source_to_candidate_semantics_exact")
        self.assertTrue(report["authorial_verse_keys_exact"])
        self.assertEqual(report["source_authored_verse_count"], 2)
        self.assertEqual(report["source_book_count"], 1)
        self.assertEqual(report["source_osis_sha256"], hashlib.sha256(old).hexdigest())
        self.assertFalse(report["compiled_stock_sword_reader_semantics_verified"])
        self.assertFalse(report["approved_for_publication"])
        snapshot = semantic_snapshot(old)
        book = snapshot["books"][0]
        self.assertEqual(book["source_word_tag_count"], 3)
        self.assertEqual(book["source_note_tag_count"], 1)
        self.assertEqual(book["source_explicit_reference_tag_count"], 1)
        self.assertEqual(book["markup_counts"]["title"], 2)

    def test_second_different_multi_book_container_edition(self):
        doc = different_edition()
        report = compare_semantics(doc, doc)
        self.assertEqual(report["status"], "source_to_candidate_semantics_exact")
        self.assertEqual(report["source_book_count"], 2)
        self.assertEqual(report["source_authored_verse_count"], 3)
        snap = semantic_snapshot(doc)
        self.assertEqual([x["book"] for x in snap["books"]], ["Beta", "Gamma"])

    def test_biblical_word_modified_in_place(self):
        old = rich_document()
        changed = old.replace(b">beginning</w>", b">beginnings</w>")
        self.expect_block(old, changed, "main_text_exact_utf8_sha256_after_xml_entity_decoding")
        self.expect_block(old, changed, "lexical_words")

    def test_punctuation_removed_even_though_word_tags_unchanged(self):
        old = rich_document()
        changed = old.replace(b"</w>, ", b"</w> ")
        result = self.expect_block(
            old, changed, "main_text_exact_utf8_sha256_after_xml_entity_decoding")
        self.assertTrue(result["authorial_verse_keys_exact"])

    def test_lemma_attribute_changed_without_word_loss(self):
        old = rich_document()
        changed = old.replace(b"strong:A2", b"strong:X2")
        result = self.expect_block(old, changed, "lexical_words")
        self.assertEqual(result["source_authored_verse_count"],
                         result["candidate_authored_verse_count"])

    def test_note_body_changed_without_main_text_change(self):
        old = rich_document()
        changed = old.replace(b"translator note", b"translator notes") if False \
            else old.replace(b"a note ", b"a changed note ")
        report = self.expect_block(old, changed, "note_bodies_callers_positions")
        self.assertNotIn("main_text_exact_utf8_sha256_after_xml_entity_decoding",
                         report["different_lanes_book_counts"])

    def test_note_caller_and_type_are_semantic(self):
        old = rich_document()
        for changed in (old.replace(b'n="a"', b'n="b"'),
                        old.replace(b'type="study"', b'type="translation"')):
            with self.subTest(changed=changed[:80]):
                self.expect_block(old, changed, "note_bodies_callers_positions")

    def test_moved_note_at_exact_word_offset_is_detected(self):
        old = rich_document()
        original = (b'<w lemma="strong:A2">beginning</w>, '
                    b'<note type="study" n="a">')
        moved = (b'<note type="study" n="a">')
        changed = old.replace(original, moved).replace(
            b'</note><reference', b'</note><w lemma="strong:A2">beginning</w>, <reference')
        self.expect_block(old, changed, "note_bodies_callers_positions")

    def test_explicit_reference_target_change_detected(self):
        old = rich_document()
        changed = old.replace(b'osisRef="Alpha.1.2"', b'osisRef="Alpha.1.1"')
        result = self.expect_block(old, changed, "explicit_reference_targets")
        self.assertTrue(result["authorial_verse_keys_exact"])

    def test_targetless_reference_not_auto_inferred(self):
        old = rich_document()
        changed = old.replace(b'osisRef="Alpha.1.2"', b'osisRef=""')
        self.expect_block(old, changed, "explicit_reference_targets")

    def test_reversed_poetry_milestone_is_detected(self):
        old = rich_document()
        changed = old.replace(b'<l eID="line1"/>', b'<l sID="line1"/>')
        self.expect_block(old, changed, "ordered_structure_boundaries")

    def test_removed_intro_heading_is_detected(self):
        old = rich_document()
        changed = old.replace(b"<title>Before chapter one</title>", b"")
        self.expect_block(old, changed, "ordered_structure_boundaries")

    def test_changed_verse_id_cannot_pass_as_unchanged_text(self):
        old = rich_document()
        changed = old.replace(b'osisID="Alpha.1.2"', b'osisID="Alpha.1.3"')
        self.expect_block(old, changed, "verse_keys")

    def test_reordered_books_are_detected_even_if_each_is_same(self):
        old = different_edition()
        start_a = old.index(b'<div type="book" osisID="Beta">')
        start_b = old.index(b'<div type="book" osisID="Gamma">')
        end = old.index(b"</osisText>")
        changed = old[:start_a] + old[start_b:end] + old[start_a:start_b] + old[end:]
        self.expect_block(old, changed, "book_order")

    def test_preserved_xml_semantics_but_different_entity_spelling(self):
        first = different_edition().replace(b"Different poetry", b"One &amp; two")
        second = first.replace(b"&amp;", b"&#38;")
        report = compare_semantics(first, second)
        self.assertEqual(report["status"], "source_to_candidate_semantics_exact")
        self.assertNotEqual(report["source_osis_sha256"],
                            report["candidate_osis_sha256"])
        self.assertFalse(report["raw_xml_bytes_identical"])

    def test_source_comments_retained_in_original_bytes_but_not_bible_text(self):
        original = different_edition()
        commented = original.replace(b"<verse osisID=", b"<!-- reviewed -->"
                                     b"<verse osisID=", 1)
        report = compare_semantics(original, commented)
        self.assertEqual(report["status"], "source_to_candidate_semantics_exact")
        self.assertFalse(report["raw_xml_bytes_identical"])

    def test_dtd_entities_rejected(self):
        bad = b'<!DOCTYPE osis [<!ENTITY foo "extra">]>' + rich_document()
        with self.assertRaises(SourceInventoryError):
            semantic_snapshot(bad)

    def test_unsupported_nested_notes_blocked(self):
        old = rich_document()
        bad = old.replace(b'a note ', b'a <note>nested</note> note ')
        with self.assertRaisesRegex(FidelityError, "nested notes"):
            semantic_snapshot(bad)

    def test_invalid_markup_cannot_be_misreported_as_exact(self):
        old = rich_document()
        bad = old.replace(b'<l sID="line1"/>', b'<l sID=""/>')
        with self.assertRaisesRegex(FidelityError, "empty structural milestone"):
            semantic_snapshot(bad)

    def test_sha_bound_private_report_and_refuse_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "original.xml"
            candidate = root / "candidate.xml"
            reportfile = root / "receipt.json"
            original.write_bytes(rich_document())
            candidate.write_bytes(rich_document())
            result = compare_semantics(original.read_bytes(), candidate.read_bytes())
            _write_new_report(reportfile, original, candidate, result)
            self.assertEqual(json.loads(reportfile.read_text()), result)
            with self.assertRaisesRegex(FidelityError, "unsafe or existing"):
                _write_new_report(reportfile, original, candidate, result)
            with self.assertRaisesRegex(FidelityError, "unsafe or existing"):
                _write_new_report(original, original, candidate, result)
            self.assertEqual(original.read_bytes(), rich_document())

    def test_full_report_does_not_emit_source_text(self):
        source = rich_document()
        candidate = source.replace(b"beginning", b"changed_word")
        result = compare_semantics(source, candidate)
        serialized = json.dumps(result)
        self.assertNotIn("beginning", serialized)
        self.assertNotIn("changed_word", serialized)
        self.assertNotIn("a changed note", serialized)


if __name__ == "__main__":
    unittest.main()
