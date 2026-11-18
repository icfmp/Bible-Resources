"""Synthetic original-K body linked-range transport proof; no real source prose."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_modern_k_scope_preview import generate,NS

ZIP="a"*64
NATIVE="b"*64
RAW="c"*64


def data():
    manifest={
        "status":"PRIVATE_PROVISIONAL_EXISTING_K_SOURCE_RANGE_LINK_PREVIEW_NOT_EDITORIAL_APPROVAL",
        "source_module":"MHCC 0.1.1",
        "source_zip_sha256":"a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746",
        "source_native_corpus_sha256":NATIVE,
        "cases":[{
            "chapter_osis":"Deut.20",
            "source_original_first_key":"Deut.20.10",
            "source_original_last_key":"Deut.20.12",
            "source_original_raw_sha256":RAW,
            "modern_declared_first_verse":10,
            "modern_declared_last_verse":20,
            "chapter_kjv_verse_count":20,
            "manuscript":"accepted/deuteronomy-20.md",
            "modern_heading":"Peace offered and the limits of ancient warfare (verses 10–20)"
        }]
    }
    receipt={
        "status":"SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
        "original_compiled_corpus_sha256":NATIVE,
        "source_prose_or_original_markup_exported":False,
        "semantic_translation_independently_approved":False,
        "chapters":{"Deut.20":{
            "source_placement":"NUMBERED_KEYS_WITH_SEPARATE_INTRO",
            "original_native_numbered_keys":12,
            "original_units":[
                {"first_key":"Deut.20.1","keys":[f"Deut.20.{i}" for i in range(1,10)],"source_unit_sha256":"d"*64},
                {"first_key":"Deut.20.10","keys":[f"Deut.20.{i}" for i in range(10,13)],"source_unit_sha256":RAW}
            ]
        }}
    }
    return manifest,receipt


class ExistingKNativeRangePreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        path=self.root/"work/mhcc-modern/production/accepted/deuteronomy-20.md"
        path.parent.mkdir(parents=True)
        manuscript="""---
chapter_osis: "Deut.20"
source_module: "MHCC 0.1.1"
source_zip_sha256: "a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746"
source_native_corpus_sha256: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
publication_status: "NOT RELEASED — private draft"
---

# Modern Deuteronomy

## Original chapter outline

| Table | Verses |
| --- | --- |
| Peace | 10–20 |

## Peace offered and the limits of ancient warfare (verses 10–20)

These are more than a few words of synthetic test commentary and none of them derive from a real author.

A second paragraph demonstrates that a single original body can keep its scope without duplication.

A third paragraph makes the shape unambiguous and allows the preview to refuse a missing passage, without changing any original authorial boundaries, notes, reference targets, punctuation, headings, or source contents.

---

## Editorial review

Not approved.
"""
        path.write_text(manuscript,encoding="utf-8")

    def test_all_extra_verse_keys_share_one_preview_body(self):
        manifest,receipt=data()
        xml,report=generate(manifest,receipt,self.root,"TESTKLINK")
        element=ET.fromstring(xml)
        divisions=element.findall(f".//{{{NS}}}div[@annotateType='commentary']")
        self.assertEqual(len(divisions),1)
        self.assertEqual(divisions[0].get("annotateRef"),"Deut.20.10-Deut.20.20")
        self.assertEqual(len(divisions[0].findall(f"{{{NS}}}p")),3)
        self.assertEqual(report["cases"][0]["additional_originally_unoccupied_verse_keys"],8)
        self.assertEqual(report["cases"][0]["authorial_source_K_bodies_added_or_split"],0)
        self.assertFalse(report["sword_published"])

    def test_other_original_verse_key_collision_fails_closed(self):
        manifest,receipt=data()
        receipt["chapters"]["Deut.20"]["original_units"].append({
            "first_key":"Deut.20.13","keys":["Deut.20.13"],"source_unit_sha256":"e"*64
        })
        with self.assertRaisesRegex(ValueError,"overwrite another authorial K body"):
            generate(manifest,receipt,self.root,"TESTKLINK")

    def test_false_original_hash_is_not_accepted(self):
        manifest,receipt=data()
        manifest["cases"][0]["source_original_raw_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"Original numbered-K body hash/bounds"):
            generate(manifest,receipt,self.root,"TESTKLINK")

    def test_guide_cannot_be_used_as_global_intro_fallback(self):
        manifest,receipt=data()
        receipt["chapters"]["Deut.20"]["source_placement"]="INTRO_ONLY_NEEDS_INDEPENDENT_REVIEW"
        with self.assertRaisesRegex(ValueError,"Refuse implicit chapter-wide fallback"):
            generate(manifest,receipt,self.root,"TESTKLINK")

    def test_absent_source_identity_and_source_edition_change_rejected(self):
        manifest,receipt=data()
        manifest["source_native_corpus_sha256"]="z"*64
        with self.assertRaisesRegex(ValueError,"Original source/rights status"):
            generate(manifest,receipt,self.root,"TESTKLINK")

    def test_target_must_extend_genuine_authored_group(self):
        manifest,receipt=data()
        manifest["cases"][0]["modern_declared_last_verse"]=12
        with self.assertRaisesRegex(ValueError,"Original editorial wider verse range"):
            generate(manifest,receipt,self.root,"TESTKLINK")


if __name__=="__main__":
    unittest.main()
