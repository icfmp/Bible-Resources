"""Private source-linked candidate preview: source literal links and book intro."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_modern_linked_candidate_preview import (
    build_verified_preview, _inject_reference_at_exact_marker, NS)
from commentary_modern_reference_gate import SourceReferenceGate

FULL="b"*64
ZIP="a"*64
ORIGINAL=(b'<div><title>Chapter outline</title>'
          b'Genesis was described in the original first section.'
          b'<table><row><cell>Creation</cell><cell>1-2</cell></row></table>'
          b'The first verse teaches us about creation.'
          b'<reference osisRef="Bible:1John.5.20">1Jo 5:20</reference>'
          b' and original theological prose.</div>')
INTRO=b'<div/>'


def fixture():
    metadata={
      "scope":"Gen.1",
      "published_zip_sha256":ZIP,
      "verified_entire_native_corpus_sha256":FULL,
      "sections":[{
        "first_key":"Gen.1.1",
        "native_keys":["Gen.1.1","Gen.1.2"],
        "source_sha256":hashlib.sha256(ORIGINAL).hexdigest(),
        "markup_census":{"tag_counts":{"reference":1,"row":1,"table":1,"title":1}}
      }],
      "intro_provenance_expectations":{
          "original_first_numbered_key":"Gen.1.1",
          "expected_original_book_intro_start":"Genesis was described in the original first section",
          "expected_original_exposition_start":"The first verse teaches us about creation",
          "expected_original_chapter_outline_table_count":1,
          "expected_original_chapter_outline_row_count":1,
          "expected_original_chapter_outline_title_count":1
      },
      "introductions":[{
        "native_key":"Gen",
        "source_sha256":hashlib.sha256(INTRO).hexdigest(),
        "markup_census":{"tag_counts":{"div":1}}
      }]
    }
    expect={"Gen.1.1":[{"canonical_target":"1John.5.20",
                          "modern_text_marker":"(1 John 5:20)"}]}
    return metadata,expect


def make_candidate(root):
    source, _=fixture()
    (root/"genesis-01.CANDIDATE.md").write_text(f"""---
chapter: "Genesis 1"
chapter_osis: "Gen.1"
status: "PRODUCTION CANDIDATE — NOT VALIDATED"
source_zip_sha256: "{ZIP}"
source_native_corpus_sha256: "{FULL}"
---

# Genesis 1

## God's light (verses 1–2)

The Son shines and grants understanding (1 John 5:20).
**Grace** transforms and renews the human soul in the
Lord's light, for the good of all believers.

---

## Editorial review

- [ ] Not complete.
""",encoding="utf-8")
    (root/"genesis-book-introduction.CANDIDATE.md").write_text(f"""---
book_osis: "Gen"
status: "PRODUCTION CANDIDATE — NOT VALIDATED"
source_zip_sha256: "{ZIP}"
source_native_corpus_sha256: "{FULL}"
---

# Genesis — Book introduction

This is a first full paragraph of forty modern English words, meant only
to test that an original book introduction has its own structural
location without being silently inserted inside the first numbered
chapter commentary unit.

A second paragraph confirms the reader will retain appropriate
separation of the introduction from the chapter.

---

## Review queue
""",encoding="utf-8")
    return root/"genesis-book-introduction.CANDIDATE.md"


class LinkedPreviewTests(unittest.TestCase):
    def test_source_literal_link_inserted_and_book_intro_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            intro=make_candidate(root)
            src,refs=fixture()
            gate=SourceReferenceGate(source_map=src,expected_refs=refs,
                                      candidate=(root/"genesis-01.CANDIDATE.md").read_text())
            gate.observe("I","Gen",INTRO)
            gate.observe("K","Gen.1.1",ORIGINAL)
            xml,proof=build_verified_preview(root=root,source_map=src,
                expected_refs=refs,gate=gate,
                complete_raw_report={"all_native_raw_entries_ordered_sha256":FULL},
                candidate_book_intro=intro,temp_id="MHCCGENP")
            top=ET.fromstring(xml)
            ns={"o":NS}
            links=top.findall(".//o:reference",ns)
            self.assertEqual(len(links),1)
            self.assertEqual(links[0].get("osisRef"),"Bible:1John.5.20")
            self.assertIn("(1 John 5:20)", "".join(links[0].itertext()))
            intro_nodes=top.findall(".//o:div[@type='introduction']",ns)
            self.assertEqual(len(intro_nodes),1)
            self.assertTrue(proof["original_source_link_targets_embedded_exactly"])
            self.assertFalse(proof["original_chapter_intro_native_markup_preserved"])
            self.assertFalse(proof["semantic_translation_independently_approved"])
            self.assertNotIn("original theological prose",xml.decode("utf-8"))

    def test_missing_inline_reference_raises_before_any_approval(self):
        sec=ET.Element(f"{{{NS}}}div")
        ET.SubElement(sec,f"{{{NS}}}p").text="There is no citation here"
        with self.assertRaisesRegex(ValueError,"exactly once"):
            _inject_reference_at_exact_marker(sec,marker="(1 John 5:20)",
                                               literal_osisref="Bible:1John.5.20")

    def test_duplicate_inline_reference_raises(self):
        sec=ET.Element(f"{{{NS}}}div")
        ET.SubElement(sec,f"{{{NS}}}p").text="One (1 John 5:20) two (1 John 5:20)"
        with self.assertRaisesRegex(ValueError,"exactly once"):
            _inject_reference_at_exact_marker(sec,marker="(1 John 5:20)",
                                               literal_osisref="Bible:1John.5.20")


if __name__=="__main__":
    unittest.main()
