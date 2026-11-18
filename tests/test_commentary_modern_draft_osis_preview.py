"""Synthetic OSIS commentary preview: paragraph, range, escaping, non-release."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_modern_draft_osis_preview import (generate, _range, NS, _modern_front,
    _modern_items, _write_reading_blocks, _original_intro_candidates)

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

    def test_source_native_discontinuous_group_does_not_swallow_other_body(self):
        first = [f"Matt.13.{v}" for v in list(range(24, 31)) + list(range(36, 44))]
        second = [f"Matt.13.{v}" for v in range(31, 36)]
        self.assertEqual(
            _range(first),
            "Matt.13.24-Matt.13.30 Matt.13.36-Matt.13.43")
        self.assertEqual(_range(second), "Matt.13.31-Matt.13.35")
        self.assertTrue(set(first).isdisjoint(second))
        # The source identities must remain separate when source XML/OSIS
        # is serialized; a min/max collapsed span would overwrite the gap.
        self.assertNotEqual(_range(first), "Matt.13.24-Matt.13.43")

    def test_missing_chapter_cannot_produce_partial_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Not all source-mapped"):
                generate(Path(folder),metadata(),work_id="MHCCWORK")


    def test_single_unvalidated_production_candidate_uses_original_source_units(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate=md().replace("DRAFT — NOT VALIDATED",
                                   "PRODUCTION CANDIDATE — NOT VALIDATED")
            (root/"genesis-01.CANDIDATE.md").write_text(candidate,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Not all source-mapped"):
                generate(root,metadata(),work_id="MHCCWORK")
            xml, report=generate(root,metadata(),work_id="MHCCWORK",
                                 include_candidates=True)
            self.assertEqual(report["modern_chapter_count"],1)
            self.assertEqual(report["annotated_commentary_sections"],1)
            self.assertIn("Grace",xml.decode("utf-8"))
            self.assertFalse(report["original_inline_reference_or_note_fidelity_approved"])
            self.assertFalse(report["sword_publication_authorized"])


class FullCanonicalProductionMarkupTests(unittest.TestCase):
    def test_original_outline_table_and_paragraph_markup_do_not_flatten(self):
        root=ET.Element(f"{{{NS}}}div")
        table=("| Original outline | Verses |\n| --- | --- |\n"
               "| First topic *italic* | 1–3 |\n| Last topic | 4–6 |\n")
        stats=_write_reading_blocks(root,table+
            "\n**Grace** and *wisdom* remain together.\n\n"
            "We preserve the next paragraph separately.\n")
        self.assertEqual(stats["tables"],1)
        self.assertEqual(stats["table_cells"],6)
        self.assertEqual(stats["paragraphs"],2)
        self.assertEqual(len(root.findall(f"{{{NS}}}table")),1)
        self.assertEqual(len(root.findall(f"{{{NS}}}p")),2)
        self.assertEqual(len(root.findall(f".//{{{NS}}}hi")),3)
        self.assertIn("Last topic", "".join(root.itertext()))

    def test_nested_editorial_parent_does_not_invent_authorial_unit(self):
        prose=("# Acts 2 — Modern English\n\n## Original chapter outline\n\n"
               "| Original outline | Verses |\n| --- | --- |\n"
               "| Sermon | 14–36 |\n\n"
               "## Peter preaches (verses 14–36)\n\n"
               "### Peter begins (verses 14–21)\n\n"
               "Christ is preached and Scripture explained.\n\n"
               "### Peter continues (verses 22–36)\n\n"
               "The resurrection is preached to the crowd.\n")
        items=_modern_items(prose)
        self.assertEqual([i["kind"] for i in items],
                         ["prelude","parent","leaf","leaf"])
        self.assertEqual(len([i for i in items if i["kind"]=="leaf"]),2)

    def test_accepted_manuscript_notes_not_serialized_into_source_prose(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"chapter.md"
            path.write_text(
                '---\nchapter_osis: "Gen.1"\npublication_status: "NOT RELEASED"\n'
                '---\n# Genesis 1\n\n## Original chapter outline\n\n'
                '| Section | Verses |\n| --- | --- |\n| A | 1 |\n\n'
                '## Exposition (verse 1)\n\nModern text.\n\n'
                '---\n\n## Editorial review — not for final OSIS\n\n'
                'This editorial note MUST NOT appear in the OSIS.\n',
                encoding="utf-8")
            fields,main=_modern_front(path)
            self.assertEqual(fields["chapter_osis"],"Gen.1")
            self.assertNotIn("MUST NOT appear",main)
            self.assertEqual(len(_modern_items(main)),2)

    def test_unsupported_markdown_and_damaged_tables_fail_closed(self):
        node=ET.Element(f"{{{NS}}}div")
        for markup in (
            "| A | B |\n| ---- |",
            "| A | B |\n| --- | --- |\n| one | two | three |",
            "> A block quotation needing explicit treatment",
            "### A nested heading in body",
        ):
            with self.subTest(markup=markup):
                with self.assertRaises(ValueError):
                    _write_reading_blocks(node,markup)

    def test_numeric_source_emendation_field_is_retained_without_prose_leak(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"genesis-05.md"
            path.write_text(
                '---\nchapter_osis: "Gen.5"\nsource_emendation_issue: 291\n'
                'publication_status: "NOT RELEASED"\n---\n'
                '# Genesis 5\n\n## Exposition (verse 1)\n\nModern reading text.\n'
                '\n---\n## Editorial audit\nNo release.\n',encoding="utf-8")
            fields, prose=_modern_front(path)
            self.assertEqual(fields["source_emendation_issue"],"291")
            self.assertNotIn("No release.",prose)

    def test_unlocated_book_prefaces_are_quarantined_not_invented_as_chapter_I(self):
        from commentary_modern_draft_osis_preview import (
            _SOURCE_ZIP, _SOURCE_CORPUS)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            common=(
                'unit: "separate book introduction"\n'
                'status: "PRODUCTION CANDIDATE — EDITORIAL ACCEPTANCE PENDING"\n'
                'source_module: "MHCC 0.1.1"\n'
                f'source_zip_sha256: "{_SOURCE_ZIP}"\n'
                f'source_native_corpus_sha256: "{_SOURCE_CORPUS}"\n')
            (root/"acts-book-introduction.CANDIDATE.md").write_text(
                '---\nbook_osis: "Acts"\n'+common+'---\n'
                '# Acts — Unlocated preface\n\nEditorial draft only.\n'
                '\n---\n## Review\nNot source-position approved.\n',encoding="utf-8")
            (root/"second-john-book-introduction.CANDIDATE.md").write_text(
                '---\nbook_osis: "2John"\n'+common+
                'source_native_intro_key: "I:2John.1"\n'
                'source_native_intro_raw_sha256: "'+"a"*64+'"\n'
                '---\n# 2 John — Book preface\n\nModern intro prose.\n'
                '\n---\n## Review\nNot independently approved.\n',encoding="utf-8")
            source={"chapters":{
                "Acts.1":{"source_placement":"NUMBERED_KEYS_WITH_SEPARATE_INTRO",
                          "native_introductions_not_assumed_to_be_exposition":[]},
                "2John.1":{"source_placement":"NUMBERED_KEYS_WITH_SEPARATE_INTRO",
                    "native_introductions_not_assumed_to_be_exposition":[{
                        "key":"2John.1","visible_word_tokens":71,
                        "raw_sha256":"a"*64}]}}}
            selected=_original_intro_candidates(root,source)
            self.assertEqual(set(selected),{"2John"})
            self.assertNotIn("Acts",selected)



if __name__ == "__main__":
    unittest.main()
