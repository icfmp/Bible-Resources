"""Synthetic gates for two approved I-only source layouts; no source text export."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_modern_ionly_preview import generate
from commentary_modern_draft_osis_preview import NS


class IOnlyTransportPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((
            ROOT / "work/mhcc-modern/production/IONLY_CHAPTER_LINK_PREVIEW.json"
        ).read_text(encoding="utf-8"))

    def source_receipt(self):
        source = self.manifest
        result = {
            "status": "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
            "original_compiled_corpus_sha256": source["source_native_corpus_sha256"],
            "source_prose_or_original_markup_exported": False,
            "intro_only_chapters_needing_editorial_review": [
                c["chapter_osis"] for c in source["chapters"]
            ],
            "chapters": {}
        }
        for c in source["chapters"]:
            result["chapters"][c["chapter_osis"]] = {
                "source_placement": "INTRO_ONLY_NEEDS_INDEPENDENT_REVIEW",
                "original_native_numbered_keys": 0,
                "distinct_original_raw_units": 0,
                "original_units": [],
                "native_introductions_not_assumed_to_be_exposition": [{
                    "key": c["chapter_osis"],
                    "raw_sha256": c["intro_raw_sha256"],
                    "visible_word_tokens": 150,
                    "markup": {"strict_xml_fragment": True, "tag_counts": {"title": 1}}
                }]
            }
        return result

    def test_exactly_two_distinct_full_chapter_sections(self):
        payload, report = generate(self.manifest, self.source_receipt(), ROOT, "MHCCIONLY")
        root = ET.fromstring(payload)
        sections = root.findall(f".//{{{NS}}}div[@annotateType='commentary']")
        self.assertEqual(len(sections), 2)
        self.assertEqual([s.attrib["annotateRef"] for s in sections],
                         ["Lev.19.1-Lev.19.37", "Ps.108.1-Ps.108.13"])
        self.assertTrue(all(len(s.findall(f"{{{NS}}}p")) > 3 for s in sections))
        self.assertFalse(report["original_source_module_modified"])
        self.assertFalse(report["semantic_translation_independently_approved"])
        self.assertFalse(report["sword_publication_authorized"])
        self.assertEqual(sum(x["expected_compiled_linked_verse_keys"]
                             for x in report["chapters"]), 50)
        self.assertNotIn("This chapter includes a few", json.dumps(report))
        self.assertNotIn("Lord, visit our souls", json.dumps(report))

    def test_reject_original_verse_level_entry(self):
        r = self.source_receipt()
        r["chapters"]["Lev.19"]["original_native_numbered_keys"] = 1
        with self.assertRaisesRegex(ValueError, "overwrite"):
            generate(self.manifest, r, ROOT, "MHCCIONLY")

    def test_reject_original_i_sha_mismatch(self):
        r = self.source_receipt()
        r["chapters"]["Ps.108"]["native_introductions_not_assumed_to_be_exposition"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ownership"):
            generate(self.manifest, r, ROOT, "MHCCIONLY")

    def test_reject_original_link_or_note_unaccounted(self):
        r = self.source_receipt()
        r["chapters"]["Lev.19"]["native_introductions_not_assumed_to_be_exposition"][0]["markup"]["tag_counts"]["reference"] = 1
        with self.assertRaisesRegex(ValueError, "references/notes"):
            generate(self.manifest, r, ROOT, "MHCCIONLY")

    def test_reject_any_general_fallback_case(self):
        r = self.source_receipt()
        r["intro_only_chapters_needing_editorial_review"].append("Gen.1")
        with self.assertRaisesRegex(ValueError, "I-only chapter set"):
            generate(self.manifest, r, ROOT, "MHCCIONLY")

    def test_reject_changed_versification_boundary(self):
        m = json.loads(json.dumps(self.manifest))
        m["chapters"][0]["verse_count"] = 0
        with self.assertRaisesRegex(ValueError, "verse registry"):
            generate(m, self.source_receipt(), ROOT, "MHCCIONLY")

    def test_reject_published_preview_or_source_pin_mismatch(self):
        m = json.loads(json.dumps(self.manifest))
        m["publication_authorized"] = True
        with self.assertRaisesRegex(ValueError, "unvalidated"):
            generate(m, self.source_receipt(), ROOT, "MHCCIONLY")
        m = json.loads(json.dumps(self.manifest))
        m["source_native_corpus_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "absent or unpinned"):
            generate(m, self.source_receipt(), ROOT, "MHCCIONLY")


if __name__ == "__main__":
    unittest.main()
