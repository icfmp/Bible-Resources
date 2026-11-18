"""Synthetic coverage guard tests: must never assert semantic approval."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_modern_draft_guard import (read_chapter_draft,
                                            verify_draft_against_native_map, run)

H = "a" * 64
R = "b" * 64


def draft(ch="Ruth.1", title="Elimelech (verses 1–3)") -> str:
    return f"""---
edition: "Synthetic Modern English draft"
chapter_osis: "{ch}"
status: "DRAFT — NOT VALIDATED"
source_zip_sha256: "{H}"
source_native_corpus_sha256: "{R}"
---

# Ruth 1 working chapter

## {title}

This is a completely synthetic section of prose for the
source-coverage tests. Its words carry no source or theological claims.

---

## Draft review queue

- [ ] Not approved.
"""


def native(ch="Ruth.1"):
    return {
        "units": [{"first_key": f"{ch}.1",
                   "native_keys": [f"{ch}.1", f"{ch}.2", f"{ch}.3"],
                   "raw_sha256": "c" * 64}],
        "source_payload_groups": 1,
        "native_occupied_verse_keys": 3,
        "original_introduction_keys": 0,
        "introductions": []
    }


class DraftGuardTests(unittest.TestCase):
    def test_read_and_match_range_with_status_always_unapproved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "chapter.DRAFT.md"
            path.write_text(draft())
            item = read_chapter_draft(path)
            result = verify_draft_against_native_map(item, native(),
                source_zip_sha256=H, source_native_sha256=R)
            self.assertEqual(result["section_count"], 1)
            self.assertEqual(result["source_key_count"], 3)
            self.assertFalse(result["semantic_source_text_compared"])
            self.assertFalse(result["approved_or_published"])

    def test_wrong_source_range_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "chapter.DRAFT.md"
            path.write_text(draft(title="Elimelech (verses 1–2)"))
            with self.assertRaisesRegex(ValueError, "misstates original range"):
                verify_draft_against_native_map(read_chapter_draft(path), native(),
                    source_zip_sha256=H, source_native_sha256=R)

    def test_discontinuous_original_verse_group_exactly_matches_modern_heading(self):
        chapter = "Matt.13"
        # One authenticated-style authored unit can address two nonadjacent
        # verse runs. Another, separate authored unit occupies the gap.
        original = native(chapter)
        verses = list(range(24, 31)) + list(range(36, 44))
        original["units"][0]["first_key"] = "Matt.13.24"
        original["units"][0]["native_keys"] = [f"Matt.13.{v}" for v in verses]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "matthew-13.DRAFT.md"
            path.write_text(draft(ch=chapter, title=
                "Weeds (verses 24–30 and 36–43)"), encoding="utf-8")
            report = verify_draft_against_native_map(
                read_chapter_draft(path), original,
                source_zip_sha256=H, source_native_sha256=R)
            self.assertEqual(report["source_key_count"], 15)
            self.assertTrue(report["exact_source_unit_anchors"][0][
                "editorial_heading_range_claim_checked"])
            for invalid in (
                "Weeds (verses 24–43)",  # Swallows the distinct 31–35 body.
                "Weeds (verses 24–30 and 31–43)",
                "Weeds (verses 24–30 and 36–42)",
                "Weeds (verses 24–30, 36–43, 43)"
            ):
                with self.subTest(heading=invalid):
                    path.write_text(draft(ch=chapter, title=invalid),
                                    encoding="utf-8")
                    with self.assertRaises(ValueError):
                        verify_draft_against_native_map(
                            read_chapter_draft(path), original,
                            source_zip_sha256=H, source_native_sha256=R)

    def test_changed_hash_or_approved_status_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "chapter.DRAFT.md"
            path.write_text(draft())
            with self.assertRaisesRegex(ValueError, "ZIP pin"):
                verify_draft_against_native_map(read_chapter_draft(path), native(),
                    source_zip_sha256="d" * 64, source_native_sha256=R)
            path.write_text(draft().replace("DRAFT — NOT VALIDATED", "VALIDATED"))
            with self.assertRaisesRegex(ValueError, "unapproved draft"):
                read_chapter_draft(path)

    def test_intrinsic_book_introduction_is_not_a_numbered_chapter(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "chapter.DRAFT.md").write_text(draft())
            (p / "intro.DRAFT.md").write_text("""---
unit: "book introduction"
status: "DRAFT — NOT VALIDATED"
---

# Separate Ruth introduction

The real intro is a different native key.
""")
            evidence = {
                "native_source_integrity_passed": True,
                "semantic_translation_review_approved": False,
                "source_full_raw_osis_markup_exported": False,
                "package_sha256": H,
                "whole_native_source_sha256": R,
                "chapters": {"Ruth.1": native()}
            }
            path = p / "native.json"
            path.write_text(json.dumps(evidence))
            result = run(p, path)
            self.assertEqual(result["checked_chapters"], 1)
            self.assertEqual(result["checked_original_source_raw_groups"], 1)
            self.assertFalse(result["semantic_translation_review_approved"])
            (p / "extra.DRAFT.md").write_text(draft(ch="Ruth.2"))
            with self.assertRaisesRegex(ValueError, "mismatch or duplicate"):
                run(p, path)


if __name__ == "__main__":
    unittest.main()
