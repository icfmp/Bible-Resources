"""Synthetic privacy, chapter/intro ownership and fail-closed tests."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_modern_source_receipt import Receipt


class NativeModernReceiptTests(unittest.TestCase):
    def test_distinct_chapter_sections_and_book_intro(self):
        rec = Receipt(["Ruth.1", "Ruth.2", "Rom.3"])
        rec.observe("I", "Ruth.0.0", b"<div>PRIVATE INTRO</div>")
        rec.observe("I", "Ruth.1.0", b"<div>PRIVATE CHAPTER HEADER</div>")
        first = b"<div><hi>PRIVATE SECTION ONE</hi></div>"
        rec.observe("K", "Ruth.1.1", first)
        rec.observe("K", "Ruth.1.2", first)
        rec.observe("K", "Ruth.1.3", b"<div>PRIVATE SECTION TWO</div>")
        rec.observe("K", "Ruth.2.1", b"<div>PRIVATE RUTH TWO</div>")
        rec.observe("K", "Rom.3.1", b"<div>PRIVATE ROMANS</div>")
        rec.observe("U", "TOP:1", b"OPAQUE PRIVATE")
        source = {
            "all_native_raw_entries_ordered_sha256": "a" * 64,
            "actual_occupied_numbered_entry_count": 5,
            "actual_occupied_intro_entry_count": 2,
            "actual_occupied_anonymous_top_entry_count": 1
        }
        result = rec.report(source, "a" * 64)
        self.assertEqual(result["chapters"]["Ruth.1"]["distinct_original_raw_units"], 2)
        self.assertEqual(result["chapters"]["Ruth.1"]["original_native_numbered_keys"], 3)
        self.assertEqual(result["chapters"]["Ruth.2"]["distinct_original_raw_units"], 1)
        self.assertEqual(len(result["chapters"]["Ruth.1"]["native_introductions_not_assumed_to_be_exposition"]), 2)
        self.assertEqual(result["chapters"]["Ruth.2"]["native_introductions_not_assumed_to_be_exposition"], [])
        encoded = json.dumps(result)
        self.assertNotIn("PRIVATE", encoded)
        self.assertFalse(result["semantic_translation_independently_approved"])
        self.assertFalse(result["source_prose_or_original_markup_exported"])

    def test_full_canonical_catalogue_is_bounded(self):
        # One read-only streaming pass can inventory all 1,189 Protestant
        # chapters without exposing original commentary words.
        chapters = [f"A.{i}" for i in range(1, 1000)]
        chapters += [f"B.{i}" for i in range(1, 191)]
        rec = Receipt(chapters)
        self.assertEqual(len(rec.chapters), 1189)
        with self.assertRaisesRegex(ValueError, "1–1200"):
            Receipt([f"A.{i}" for i in range(1, 1000)]
                    + [f"B.{i}" for i in range(1, 203)])

    def test_wrong_complete_corpus_hash_is_rejected(self):
        rec = Receipt(["Ruth.1"])
        rec.observe("K", "Ruth.1.1", b"<div>original</div>")
        with self.assertRaisesRegex(ValueError, "hash does not match"):
            rec.report({
                "all_native_raw_entries_ordered_sha256": "a" * 64,
                "actual_occupied_numbered_entry_count": 1,
                "actual_occupied_intro_entry_count": 0,
                "actual_occupied_anonymous_top_entry_count": 0
            }, "b" * 64)

    def test_missing_chapter_is_rejected(self):
        rec = Receipt(["Ruth.1"])
        with self.assertRaisesRegex(ValueError, "has no observed"):
            rec.report({
                "all_native_raw_entries_ordered_sha256": "a" * 64,
                "actual_occupied_numbered_entry_count": 0,
                "actual_occupied_intro_entry_count": 0,
                "actual_occupied_anonymous_top_entry_count": 0
            }, "a" * 64)

    def test_invalid_chapters_rejected(self):
        for chapters in ([], ["Ruth.1", "Ruth.1"], ["Ruth.0"],
                         ["Ruth.1;rm -rf /"], ["Rom.3.1"]):
            with self.subTest(chapters=chapters):
                with self.assertRaises(ValueError):
                    Receipt(chapters)


if __name__ == "__main__":
    unittest.main()
