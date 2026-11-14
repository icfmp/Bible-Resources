"""Offline safety and exact-index tests for stock commentary raw corpus scanner."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_native_raw_inventory import (
    private_crosscheck, NativeCommentaryMarkupCensus, MAX_RAW_MARKUP_BYTES,
    original_osisref_form,
)
from pilot_preflight import PilotError
from sword_native_raw_corpus_inventory import parse_native_raw_corpus,RawCorpusError


class CommentaryRawInventoryTests(unittest.TestCase):
    def index(self):
        return (b"M\tTestCom\tKJV\t1.9.0\tzCom\n"
                b"I\tGen\n"
                b"K\tGen.1.1\n"
                b"K\tGen.1.3\n"
                b"U\tTOP:1\n"
                b"S\t30000\t2\t1\t1\n")

    def stream(self):
        entries=[
            ("I","Gen",b"<p>Unmodified book introduction</p>"),
            ("K","Gen.1.1",b"<p>The original commentary, not for reporting.</p>"),
            ("K","Gen.1.3",b"<p>Another original section with a comma, punctuation!</p>"),
            ("U","TOP:1",b"Opaque intro fragment"),
        ]
        data=b"".join((f"{k}\t{ref}\t{len(raw)}\n".encode("ascii")+raw)
                      for k,ref,raw in entries)
        return data+b"S\t4\t2\t1\t1\n",entries

    def test_every_raw_framed_record_has_full_slot_coverage(self):
        raw,entries=self.stream()
        seen=[]
        parsed,k,intros,top=parse_native_raw_corpus(
            BytesIO(raw),on_entry=lambda kind,ref,value: seen.append((kind,ref,value)))
        self.assertEqual(len(seen),4)
        self.assertEqual(k,["Gen.1.1","Gen.1.3"])
        self.assertEqual(intros,["Gen"])
        self.assertEqual(top,["TOP:1"])
        matched=private_crosscheck(self.index(),"TestCom",
            [(kind,ref) for kind,ref,_ in seen],parsed)
        self.assertTrue(matched["exact_all_occupied_stock_keys_read_and_crosschecked"])
        self.assertEqual(matched["all_stock_occupied_keys_count"],4)
        self.assertNotIn("The original commentary",json.dumps(matched))
        self.assertFalse(parsed["source_original_authorial_text_compared"])

    def test_different_key_order_or_reference_blocks(self):
        raw,entries=self.stream()
        parsed,*_=parse_native_raw_corpus(BytesIO(raw))
        with self.assertRaisesRegex(PilotError,"diverged"):
            private_crosscheck(self.index(),"TestCom",
                [("I","Gen"),("K","Gen.1.3"),("K","Gen.1.1"),("U","TOP:1")],parsed)
        with self.assertRaisesRegex(PilotError,"diverged"):
            private_crosscheck(self.index(),"TestCom",
                [("I","Gen"),("K","Gen.1.1"),("K","Gen.1.2"),("U","TOP:1")],parsed)

    def test_incomplete_content_stream_fails_closed(self):
        raw,_=self.stream()
        with self.assertRaises(RawCorpusError):
            parse_native_raw_corpus(BytesIO(raw[:-12]))
        with self.assertRaises(RawCorpusError):
            parse_native_raw_corpus(BytesIO(raw+b"garbage"))

    def test_index_count_mismatch_detected(self):
        raw,_=self.stream()
        parsed,*_=parse_native_raw_corpus(BytesIO(raw))
        with self.assertRaises(PilotError):
            private_crosscheck(self.index().replace(b"S\t30000\t2\t1\t1",
                                                   b"S\t30000\t3\t1\t1"),
                               "TestCom",
                               [("I","Gen"),("K","Gen.1.1"),("K","Gen.1.3"),("U","TOP:1")],
                               parsed)



class OriginalCommentaryMarkupCensusTests(unittest.TestCase):
    def test_all_source_frames_reconciled_and_fixed_structure_counts_only(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("K", "Gen.1.3", (
            b"<title>Secret original heading</title>"
            b"<p>Private original paragraph "
            b'<reference osisRef="Gen.2.1">secret target label</reference></p>'
            b'<table><row><cell>Private textual table</cell></row></table>'
            b"<note>Private editorial note</note>"
        ))
        census.observe("I", "Gen", b"  ")
        census.observe("U", "TOP:1", b"opaque unparsed top-level source")
        report = census.report(3)
        self.assertTrue(report["all_original_native_entries_accounted_for"])
        self.assertEqual(report["strict_xml_parseable_numbered_or_intro_entries"], 1)
        self.assertEqual(report["empty_numbered_or_intro_entries"], 1)
        self.assertEqual(report["opaque_top_entries_not_assumed_to_be_xml"], 1)
        self.assertEqual(report["entries_with_title_markup"], 1)
        self.assertEqual(report["entries_with_paragraph_markup"], 1)
        self.assertEqual(report["entries_with_reference_markup"], 1)
        self.assertEqual(report["entries_with_table_markup"], 1)
        self.assertEqual(report["entries_with_note_markup"], 1)
        self.assertEqual(report["reference_elements_with_osisref_attribute"], 1)
        self.assertEqual(report["original_element_counts_by_fixed_category"]["row"], 1)
        self.assertEqual(report["original_element_counts_by_fixed_category"]["cell"], 1)
        output = json.dumps(report)
        for forbidden in ("Secret original", "Private", "Gen.2.1", "Gen.1.3", "TOP:1"):
            self.assertNotIn(forbidden, output)
        self.assertFalse(report["source_to_other_digital_edition_parity_proven"])
        self.assertFalse(report["real_reader_layout_or_click_navigation_proven"])

    def test_invalid_source_xml_is_classified_not_silently_fixed(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("K", "Gen.1.1", b"<p>Unclosed original markup")
        census.observe("I", "Gen.1", b"<note>&unknownEntity;</note>")
        census.observe("K", "Gen.1.2", b"<reference>Original label</reference>")
        report = census.report(3)
        self.assertEqual(report["unparseable_numbered_or_intro_entries"], 2)
        self.assertEqual(report["strict_xml_parseable_numbered_or_intro_entries"], 1)
        self.assertEqual(report["reference_elements_without_osisref_attribute"], 1)
        self.assertTrue(report["no_original_source_bytes_rewritten"])
        self.assertNotIn("Original label", str(report))

    def test_opaque_and_noncanonical_tags_cannot_be_exposed_in_receipt(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("U", "TOP:1", b"<notactuallyxml>opaque")
        census.observe("K", "Gen.1.1", b"<privateSourceName>Actual words</privateSourceName>")
        report = census.report(2)
        self.assertEqual(report["original_element_counts_by_fixed_category"]["other"], 1)
        self.assertEqual(report["strict_xml_parseable_numbered_or_intro_entries"], 1)
        self.assertNotIn("privateSourceName", str(report))
        self.assertNotIn("notactuallyxml", str(report))

    def test_binary_and_oversized_payloads_are_not_accepted_as_parsed(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("K", "Gen.1.1", b"<p>broken\x00data</p>")
        census.observe("K", "Gen.1.2", b"a" * (MAX_RAW_MARKUP_BYTES + 1))
        report = census.report(2)
        self.assertEqual(report["oversized_or_binary_numbered_or_intro_entries"], 2)
        self.assertEqual(report["strict_xml_parseable_numbered_or_intro_entries"], 0)

    def test_incomplete_or_malformed_frame_accounting_fails_closed(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("I", "Gen", b"")
        with self.assertRaisesRegex(PilotError, "Unreconciled"):
            census.report(2)
        for invalid_kind, invalid_key, invalid_content in (
            ("X", "Gen.1", b""),
            ("K", None, b""),
            ("K", "Gen.1.1", "untrusted unicode"),
        ):
            with self.assertRaisesRegex(PilotError, "Unreviewed"):
                census.observe(invalid_kind, invalid_key, invalid_content)



class OriginalCommentaryLinkFormTests(unittest.TestCase):
    def test_common_original_target_forms_are_observations_not_verse_validation(self):
        samples = {
            "Gen.1.1": "single_osis_verse",
            "1John.3.16": "single_osis_verse",
            "Bible:Ps.119.176": "single_osis_verse",
            "Exod.3.1-Exod.3.5": "verse_range_like",
            "Bible:Exod.3.1-5": "verse_range_like",
            "Matt": "book_or_chapter_like",
            "Matt.5": "book_or_chapter_like",
            "Luke.2.1,3": "compound_target",
            "Bible:Luke.2.1 Luke.2.2": "compound_target",
            "KJV:Luke.3.3": "other_unclassified",
            "Gen.1.1!note": "other_unclassified",
            "Gen.1.0": "other_unclassified",
        }
        for target, category in samples.items():
            with self.subTest(category=category):
                self.assertEqual(original_osisref_form(target), category)
        with self.assertRaisesRegex(PilotError, "absent"):
            original_osisref_form("")

    def test_complete_reference_label_title_inventory_has_no_source_leak(self):
        audit = NativeCommentaryMarkupCensus()
        audit.observe("K", "Gen.1.1", (
            b"<title>Private authored chapter title</title>"
            b"<title> </title>"
            b'<reference osisRef="Bible:Gen.2.1">Original citation prose</reference>'
            b'<reference osisRef="Ps.3.1-Ps.3.5"><hi>Next</hi> original label</reference>'
            b'<reference osisRef="1John.2"> </reference>'
            b'<reference osisRef="Some:unknownTarget">Unexpected reference</reference>'
            b'<reference osisRef="Gen.1.1,Gen.1.2">Compound</reference>'
            b'<reference osisRef="Gen.2.2"/>'
            b'<reference>Missing source target</reference>'
        ))
        report = audit.report(1)
        self.assertEqual(report["reference_elements_with_osisref_attribute"], 6)
        self.assertEqual(report["reference_elements_without_osisref_attribute"], 1)
        self.assertEqual(report["original_reference_elements_with_literal_Bible_work_prefix"], 1)
        self.assertEqual(report["original_reference_labels_with_visible_text"], 5)
        self.assertEqual(report["original_reference_labels_without_visible_text"], 2)
        self.assertEqual(report["original_title_elements_with_visible_text"], 1)
        self.assertEqual(report["original_title_elements_without_visible_text"], 1)
        self.assertEqual(report["original_osisref_form_count_by_fixed_category"], {
            "single_osis_verse": 2, "verse_range_like": 1,
            "book_or_chapter_like": 1, "compound_target": 1,
            "other_unclassified": 1,
        })
        self.assertTrue(report["no_osisref_value_normalization_or_verse_existence_claim"])
        serialized=json.dumps(report)
        for original in ("Gen.2.1", "Some:unknownTarget", "Original citation",
                         "Private authored", "Missing source", "Some:", "Gen.1.1"):
            self.assertNotIn(original, serialized)

    def test_unknown_osis_reference_attribute_is_classified_without_correction(self):
        census = NativeCommentaryMarkupCensus()
        census.observe("K", "Rev.22.1",
                       b'<reference osisRef="A deliberately odd source target">'
                       b'Original words in the source</reference>')
        summary = census.report(1)
        self.assertEqual(summary["original_osisref_form_count_by_fixed_category"]
                         ["compound_target"], 1)
        self.assertTrue(summary["no_original_source_bytes_rewritten"])
        self.assertNotIn("deliberately", str(summary))



if __name__=="__main__":
    unittest.main()
