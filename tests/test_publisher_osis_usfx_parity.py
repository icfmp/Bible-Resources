"""Synthetic, text-private tests for official publisher OSIS vs pinned USFX."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from publisher_osis_usfx_parity import (
    original_osis_verses_and_notes, compare_original_sources,
    PublisherSourceParityError, _bounded_priority_findings,
)

ROOT="""<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText osisIDWork="TEST"><div type="book" osisID="Gen">
{verses}</div></osisText></osis>"""

def make_xml(label="a",body="PRIVATE ORIGINAL NOTE",two=True):
    v1=('''<chapter osisID="Gen.1"/><p>
    <verse osisID="Gen.1.1" sID="Gen.1.1"/>alpha
    <note type="x-footnote" n="'''+label+'''">'''+body+'''</note> beta
    <verse eID="Gen.1.1"/></p>''')
    v2=('''<p><verse osisID="Gen.1.2" sID="Gen.1.2"/>gamma
    <verse eID="Gen.1.2"/></p>''' if two else "")
    return ROOT.format(verses=v1+v2).encode()

def input_data():
    text={"Gen.1.1":"alpha beta","Gen.1.2":"gamma"}
    notes={"Gen.1.1":[("f","PRIVATE ORIGINAL NOTE")]}
    attrs={"Gen.1.1":[{"caller":"a","explicit_targets":()}]}
    positions={"Gen.1.1":(5,), "Gen.1.2":()}
    return text,notes,attrs,positions


class OfficialSourceParityTests(unittest.TestCase):
    def test_exact_codepoints_and_original_footnote_position(self):
        verses,notes,meta=original_osis_verses_and_notes(make_xml())
        self.assertEqual(set(verses),{"Gen.1.1","Gen.1.2"})
        self.assertEqual("".join(verses["Gen.1.1"].split()),"alphabeta")
        self.assertEqual(notes["Gen.1.1"][0]["caller"],"a")
        self.assertEqual(notes["Gen.1.1"][0]["point"],5)
        self.assertEqual(meta["publisher_numbered_note_count"],1)
        result=compare_original_sources(
            *input_data(),verses,notes,meta)
        count=result["original_source_comparison_counts"]
        self.assertEqual(result["status"],"exact_index_main_text_note_caller_precheck")
        self.assertEqual(count["shared_verse_nonspace_characters_equal"],2)
        self.assertEqual(count["note_anchor_punctuation_ordinal_equal"],1)
        self.assertEqual(count["source_note_caller_labels_equal"],1)
        self.assertEqual(count["note_body_words_punctuation_equal_after_space_folding"],1)
        self.assertFalse(result["safe_for_automatic_source_switch_or_rebuild"])
        for secret in ("PRIVATE ORIGINAL NOTE","alpha","gamma"):
            self.assertNotIn(secret,json.dumps(result))

    def test_four_missing_source_verse_ids_never_reintroduced(self):
        verses,notes,meta=original_osis_verses_and_notes(make_xml(two=False))
        result=compare_original_sources(*input_data(),verses,notes,meta)
        count=result["original_source_comparison_counts"]
        self.assertEqual(count["usfx_only_reference_count"],1)
        self.assertEqual(result["status"],
                         "material_publisher_osis_usfx_differences_require_review")
        self.assertEqual(
            result["bounded_reference_and_note_ordinal_findings_only"][0]["reference"],
            "Gen.1.2")

    def test_changed_authorial_label_not_hidden_by_equal_note_body(self):
        verses,notes,meta=original_osis_verses_and_notes(make_xml(label="aa"))
        result=compare_original_sources(*input_data(),verses,notes,meta)
        c=result["original_source_comparison_counts"]
        self.assertEqual(c["source_note_caller_labels_differ"],1)
        sample=next(x for x in result["bounded_reference_and_note_ordinal_findings_only"]
                    if x["finding"]=="source_note_caller_label_difference")
        self.assertEqual(sample["official_shape"],"other_unreviewed_literal")
        self.assertEqual(sample["one_based_note"],1)
        self.assertNotIn('"caller": "aa"',json.dumps(result))

    def test_same_verse_keys_do_not_hide_word_change(self):
        verses,notes,meta=original_osis_verses_and_notes(
            make_xml(body="DIFFERENT PRIVATE ANNOTATION"))
        result=compare_original_sources(*input_data(),verses,notes,meta)
        c=result["original_source_comparison_counts"]
        self.assertEqual(c["note_body_folded_different"],1)
        self.assertNotIn("DIFFERENT PRIVATE",json.dumps(result))

    def test_moved_note_anchor_detected_without_outputting_verse(self):
        xml=make_xml().replace(
            b'alpha\n    <note',b'al\n    <note').replace(
            b'</note> beta',b'</note>pha beta')
        verses,notes,meta=original_osis_verses_and_notes(xml)
        result=compare_original_sources(*input_data(),verses,notes,meta)
        c=result["original_source_comparison_counts"]
        self.assertEqual(c["note_anchor_punctuation_ordinal_different"],1)
        self.assertEqual(c["shared_verse_nonspace_characters_equal"],2)
        self.assertNotIn("PRIVATE ORIGINAL NOTE",json.dumps(result))

    def test_missing_verses_not_hidden_by_note_mismatch_sample_saturation(self):
        # An edit-heavy edition can have hundreds of note differences, but
        # the first bounded reviewer list must expose every sampled missing key.
        findings = {
            "note_body_folded_difference": [
                {"reference": "Gen.1.1", "finding": "note_body_folded_difference"}
                for _ in range(18)
            ],
            "source_note_caller_label_difference": [
                {"reference": "Gen.1.1", "finding": "source_note_caller_label_difference"}
                for _ in range(18)
            ],
            "source_reference_target_difference": [
                {"reference": "Gen.1.1", "finding": "source_reference_target_difference"}
                for _ in range(18)
            ],
            "source_note_anchor_position_difference": [
                {"reference": "Gen.1.1", "finding": "source_note_anchor_position_difference"}
                for _ in range(18)
            ],
            "usfx_reference_absent_in_official_publisher": [
                {"reference": "Gen.1.2",
                 "finding": "usfx_reference_absent_in_official_publisher"}
            ],
        }
        rows = _bounded_priority_findings(findings)
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows[0]["reference"], "Gen.1.2")
        self.assertNotIn("PRIVATE", json.dumps(rows))

    def test_empty_or_overlapping_scope_blocks(self):
        xml=make_xml().replace(b'<verse eID="Gen.1.1"/>',b'')
        with self.assertRaises((ValueError,PublisherSourceParityError)):
            original_osis_verses_and_notes(xml)


if __name__=="__main__":
    unittest.main()
