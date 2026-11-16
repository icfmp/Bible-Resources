"""Synthetic OSIS commentary preview: paragraph, range, escaping, non-release."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_modern_draft_osis_preview import generate, _range, NS

H = "a"*64
S = "b"*64


def md(ch="Ruth.1") -> str:
    return f"""---
edition: "Fake modern draft"
chapter_osis: "{ch}"
status: "DRAFT — NOT VALIDATED"
source_zip_sha256: "{H}"
source_native_corpus_sha256: "{S}"
---

# Fake reader chapter

## One commentary (verses 1–3)

**Grace** is shown in ordinary acts of love. Even <script> tags
must be escaped and not interpreted as active markup.

The *next* paragraph is intentionally separate.

---

## Review (outside source)

- [ ] Not approved.
"""


def metadata(ch="Ruth.1"):
    return {
        "package_sha256": H,
        "whole_native_source_sha256": S,
        "semantic_translation_review_approved": False,
        "chapters": {
            ch: {
                "units": [{
                    "native_keys": [f"{ch}.1", f"{ch}.2", f"{ch}.3"],
                    "raw_sha256": "c"*64
                }]
            }
        }
    }


class CommentaryPreviewTests(unittest.TestCase):
    def test_paragraphs_osis_ranges_and_non_release_are_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ruth-1.DRAFT.md").write_text(md(), encoding="utf-8")
            xml, report = generate(root, metadata(), work_id="MHCCWORK")
            top = ET.fromstring(xml)
            ns={"o":NS}
            sections=top.findall(".//o:div[@annotateType='commentary']", ns)
            self.assertEqual(len(sections),1)
            self.assertEqual(sections[0].get("annotateRef"), "Ruth.1.1-Ruth.1.3")
            self.assertEqual(len(sections[0].findall("o:p",ns)),2)
            self.assertEqual(len(sections[0].findall(".//o:hi",ns)),2)
            self.assertIn("&lt;script&gt;", xml.decode())
            self.assertFalse(report["original_book_and_chapter_introductions_included"])
            self.assertFalse(report["original_inline_reference_or_note_fidelity_approved"])
            self.assertFalse(report["sword_publication_authorized"])
            self.assertEqual(report["new_reading_paragraphs"],2)

    def test_discontinuous_groups_serialize_as_separate_references(self):
        self.assertEqual(_range(["Matt.13.36", "Matt.13.24", "Matt.13.37"]),
                         "Matt.13.24 Matt.13.36-Matt.13.37")
        with self.assertRaises(ValueError):
            _range(["Matt.13.1", "Matt.13.1"])
        with self.assertRaises(ValueError):
            _range(["Matt.13.1", "Matt.14.2"])

    def test_missing_chapter_cannot_produce_partial_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Not all source-mapped"):
                generate(Path(folder),metadata(),work_id="MHCCWORK")


if __name__ == "__main__":
    unittest.main()
