"""Source-proven, reversible one-reference-per-passage OSIS transformations."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from normalize_bible_references import run, ReviewError  # noqa: E402
from segment_osis_reference_destinations import (  # noqa: E402
    _exact_reference_spans, segment_candidate,
)

NS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"


def mock(clean_dest: str):
    cleaned=(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
        '<osisText osisIDWork="Demo" osisRefWork="Bible"><header/>'
        '<div type="book" osisID="Gen">'
        '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
        '<verse osisID="Gen.1.2">Two</verse></chapter>'
        '<chapter osisID="Gen.2"><verse osisID="Gen.2.1">Three</verse></chapter>'
        '<note type="crossReference" n="a"><reference type="annotateRef" subType="x-origin">1.1 </reference>'
        f'<reference>{clean_dest}</reference></note>'
        '<div type="introduction"><list><item><reference subType="x-introduction">'
        '1:1–2:1</reference></item></list></div></div></osisText></osis>'
    ).encode()
    original=(
        '<usfx><book id="GEN"><x caller="a"><xo>1.1</xo>'
        f'<xt>{clean_dest}</xt></x><ior>1:1–2:1</ior></book></usfx>'
    ).encode()
    return cleaned,original


class SplitSourceReferencesTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.aliases={"Ge":"Gen"}

    def tearDown(self):
        self.temp.cleanup()

    def build(self,label="Ge 1:1, 2; 2:1."):
        cleaned,usfx=mock(label)
        source=self.path/"cleaned.xml"
        original=self.path/"original.zip"
        source.write_bytes(cleaned)
        with ZipFile(original,"w") as z:
            z.writestr("demo_usfx.xml",usfx)
        manifest=self.path/"manifest.json"
        manifest.write_text(json.dumps({
            "cleaned_osis_sha256":sha256(cleaned).hexdigest(),
            "original_usfx_sha256":sha256(original.read_bytes()).hexdigest(),
        }))
        crosswalk=self.path/"crosswalk.json"
        crosswalk.write_text(json.dumps({"books":[{"usfm":"GEN","osis":"Gen"}]}))
        witness=self.path/"alias.json"
        witness.write_text(json.dumps({
            "schema_version":1,
            "crosswalk":"config/standard_usfm_osis_66.json",
            "printed_sources":["https://example.org/original-1910-table"],
            "aliases":self.aliases,
        }))
        candidate,proof=run(cleaned_path=source,usfx_zip=original,
                            manifest_path=manifest,crosswalk_path=crosswalk,
                            destination_aliases_path=witness,
                            complete_citation_lists=True)
        return candidate, proof

    def test_separate_links_preserve_complete_original_label_exactly(self):
        candidate,source_receipt=self.build()
        result,receipt=segment_candidate(candidate,self.aliases)
        self.assertEqual(receipt["segmented_destination_labels"],1)
        self.assertEqual(receipt["individual_reference_elements_created"],3)
        self.assertEqual(receipt["new_reference_elements"],2)
        self.assertIn(b'<reference osisRef="Gen.1.1">Ge 1:1</reference>, '
                      b'<reference osisRef="Gen.1.2">2</reference>; '
                      b'<reference osisRef="Gen.2.1">2:1</reference>.',result)
        self.assertEqual("".join(etree.fromstring(candidate).itertext()),
                         "".join(etree.fromstring(result).itertext()))
        self.assertEqual(source_receipt["resolved_original_destination_labels"],1)
        self.assertEqual(source_receipt["candidate_additions"],3)

    def test_repeat_source_book_after_full_stop_without_swallowing_punctuation(self):
        candidate,_=self.build("Ge 1:1. Ge 1:2.")
        split,report=segment_candidate(candidate,self.aliases)
        self.assertEqual(report["individual_reference_elements_created"],2)
        self.assertIn(b'<reference osisRef="Gen.1.1">Ge 1:1</reference>. '
                      b'<reference osisRef="Gen.1.2">Ge 1:2</reference>.',split)

    def test_range_is_one_link_and_following_label_remains_individual(self):
        candidate,_=self.build("Ge 1:1-2. Ge 2:1.")
        split,report=segment_candidate(candidate,self.aliases)
        self.assertIn(b'<reference osisRef="Gen.1.1-Gen.1.2">Ge 1:1-2</reference>. '
                      b'<reference osisRef="Gen.2.1">Ge 2:1</reference>.',split)
        self.assertEqual(report["individual_reference_elements_created"],2)

    def test_disambiguated_chapter_verse_is_one_explicit_source_slice(self):
        verses={"Exod.20.11","Exod.31.17"}
        spans=_exact_reference_spans(
            "Ex 20:11, 31, 17.",{"Ex":"Exod"},verses,
            disambiguated_chapter_commas=True)
        self.assertEqual([key for _a,_b,key in spans],
                         ["Exod.20.11","Exod.31.17"])
        self.assertEqual(["Ex 20:11, 31, 17."[a:b] for a,b,_ in spans],
                         ["Ex 20:11","31, 17"])
        with self.assertRaisesRegex(ReviewError,"Cannot split"):
            _exact_reference_spans("Ex 20:11, 31, 17.",
                                   {"Ex":"Exod"},verses)

    def test_disambiguated_chapter_missing_target_is_not_partially_linked(self):
        verses={"Exod.20.11"}
        with self.assertRaisesRegex(ReviewError,"Cannot split"):
            _exact_reference_spans(
                "Ex 20:11, 31, 17.",{"Ex":"Exod"},verses,
                disambiguated_chapter_commas=True)

    def test_single_reference_never_retyped(self):
        candidate,_=self.build("Ge 1:1.")
        split,report=segment_candidate(candidate,self.aliases)
        self.assertEqual(candidate,split)
        self.assertNotIn("segmented_destination_labels",report)

    def test_boundary_whitespace_remains_byte_identical(self):
        label=" Ge 1:1; 2:1. "
        candidate,_=self.build(label)
        split,receipt=segment_candidate(candidate,self.aliases)
        self.assertEqual(receipt["segmented_destination_labels"],1)
        self.assertIn(b'> <reference osisRef="Gen.1.1">Ge 1:1</reference>; <reference osisRef="Gen.2.1">2:1. </reference>',
                      split)
        self.assertEqual("".join(etree.fromstring(candidate).itertext()),
                         "".join(etree.fromstring(split).itertext()))

    def test_terminal_original_source_space_stays_inside_last_link_for_native_sword(self):
        candidate,_=self.build("Ge 1:1. Ge 1:2. ")
        split,receipt=segment_candidate(candidate,self.aliases)
        self.assertIn(b'<reference osisRef="Gen.1.2">Ge 1:2. </reference>',split)
        self.assertEqual("".join(etree.fromstring(candidate).itertext()),
                         "".join(etree.fromstring(split).itertext()))
        self.assertEqual(receipt["segmented_destination_labels"],1)

    def test_idempotence(self):
        candidate,_=self.build()
        once,report=segment_candidate(candidate,self.aliases)
        twice,report2=segment_candidate(once,self.aliases)
        self.assertEqual(once,twice)
        self.assertEqual(report2.get("segmented_destination_labels",0),0)

    def test_wrong_existing_machine_target_list_blocks_all_splitting(self):
        candidate,_=self.build()
        bad=candidate.replace(
            b'osisRef="Gen.1.1 Gen.1.2 Gen.2.1"',
            b'osisRef="Gen.1.1 Gen.1.2 Gen.1.1"')
        with self.assertRaisesRegex(ReviewError,"segmentation differs"):
            segment_candidate(bad,self.aliases)

    def test_unknown_verse_blocks_no_partial_source_label(self):
        with self.assertRaisesRegex(ReviewError,"Cannot split"):
            _exact_reference_spans("Ge 1:1; 9:9.",self.aliases,
                                   {"Gen.1.1","Gen.1.2"})

    def test_printed_whitespace_and_punctuation_are_not_removed(self):
        candidate,_=self.build("Ge 1:1,  2;  2:1.")
        split,receipt=segment_candidate(candidate,self.aliases)
        self.assertIn(b'</reference>,  <reference',split)
        self.assertIn(b'</reference>;  <reference',split)
        self.assertEqual(receipt["segmented_destination_labels"],1)

    def test_original_note_callout_and_source_origin_metadata_preserved(self):
        candidate,_=self.build()
        result,_=segment_candidate(candidate,self.aliases)
        before=etree.fromstring(candidate).find(".//"+NS+"note")
        after=etree.fromstring(result).find(".//"+NS+"note")
        self.assertEqual(before.attrib,after.attrib)
        self.assertEqual(before[0].attrib,after[0].attrib)
        self.assertEqual(before[0].text,after[0].text)
        self.assertEqual("".join(before.itertext()),"".join(after.itertext()))


if __name__=="__main__":
    unittest.main()
