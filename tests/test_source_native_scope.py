"""Standard USFM↔native-SWORD book scope: deliberately mixed-canon fixtures.

The verified canonical subset MUST NOT erase original additional books or
authorise publication. No real Scripture, notes or version metadata hardcoded.
"""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_native_scope import (
    read_crosswalk, compare_mapped_scope, BookScopeError
)

PAIRS = [("GEN", "Gen"), ("EXO", "Exod")]


class NativeCanonicalScopeTests(unittest.TestCase):
    def test_standard_mapping_uses_usfm_32_codes_and_66_unique_sword_names(self):
        rows = read_crosswalk(ROOT / "config/standard_usfm_osis_66.json")
        self.assertEqual(len(rows), 66)
        self.assertEqual(rows[0], ("GEN", "Gen"))
        self.assertEqual(rows[-1], ("REV", "Rev"))
        self.assertEqual(len(set(rows)), 66)
        self.assertIn(("1CO", "1Cor"), rows)
        self.assertIn(("PSA", "Ps"), rows)

    def test_exact_mapped_subset_preserves_unmapped_numbered_and_intro_books(self):
        report = compare_mapped_scope(
            ["FRT", "GEN", "PS2", "EXO", "GLO"],
            [("GEN", 1, 1), ("GEN", 1, 2), ("PS2", 1, 1),
             ("PS2", 1, 2), ("EXO", 1, 1)],
            "Gen.1.1\nGen.1.2\nExod.1.1\n", PAIRS)
        self.assertEqual(
            report["status"],
            "canonical_index_exact_source_has_extra_authored_books_to_review")
        self.assertTrue(report["canonical_verse_keys_exact_after_explicit_book_mapping"])
        self.assertEqual(report["source_canonical_numbered_key_count"], 3)
        self.assertEqual(report["native_canonical_numbered_key_count"], 3)
        self.assertEqual(report["additional_original_source_numbered_verse_count"], 2)
        self.assertEqual(report["all_original_extra_source_books_preserved_as_evidence"], [
            {"source_usfm_code": "FRT", "authored_numbered_verses": 0},
            {"source_usfm_code": "PS2", "authored_numbered_verses": 2},
            {"source_usfm_code": "GLO", "authored_numbered_verses": 0}
        ])
        self.assertFalse(report["authorial_full_source_to_compiled_scope_fidelity_verified"])
        self.assertFalse(report["source_to_compiled_text_notes_lexical_and_layout_verified"])
        self.assertFalse(report["rights_and_publication_approved"])

    def test_exact_without_extra_books_still_does_not_prove_content(self):
        report = compare_mapped_scope(
            ["GEN", "EXO"], [("GEN", 1, 1), ("EXO", 1, 1)],
            "Gen.1.1\nExod.1.1\n", PAIRS)
        self.assertEqual(report["status"],
                         "canonical_index_exact_but_compiled_content_unverified")
        self.assertEqual(report["source_canonical_keys_sha256"],
                         report["native_canonical_keys_sha256"])
        self.assertFalse(report["exact_original_source_edition_and_revision_equals_sword_verified"])

    def test_actual_source_missing_native_key_fails_closed(self):
        report = compare_mapped_scope(
            ["GEN", "EXO"],
            [("GEN", 1, 1), ("GEN", 1, 2), ("EXO", 1, 1)],
            "Gen.1.1\nExod.1.1\n", PAIRS)
        self.assertEqual(report["status"], "blocked_mapped_canonical_verse_key_difference")
        self.assertEqual(report["source_canonical_refs_unreachable_in_reader_count"], 1)
        self.assertEqual(report["first_unreachable_source_refs"], ["Gen.1.2"])

    def test_invented_native_key_not_accepted_even_with_same_counts(self):
        report = compare_mapped_scope(
            ["GEN", "EXO"], [("GEN", 1, 1), ("EXO", 1, 1)],
            "Gen.1.2\nExod.1.1\n", PAIRS)
        self.assertEqual(report["source_canonical_numbered_key_count"],
                         report["native_canonical_numbered_key_count"])
        self.assertFalse(report["canonical_verse_keys_exact_after_explicit_book_mapping"])
        self.assertEqual(report["first_unreachable_source_refs"], ["Gen.1.1"])
        self.assertEqual(report["first_unexpected_reader_refs"], ["Gen.1.2"])

    def test_unmapped_native_books_block_entire_mapped_canon_order(self):
        report = compare_mapped_scope(
            ["GEN", "EXO"], [("GEN", 1, 1), ("EXO", 1, 1)],
            "Gen.1.1\nPs.1.1\nExod.1.1\n", PAIRS)
        self.assertEqual(report["status"], "blocked_crosswalk_book_scope_or_order_mismatch")
        self.assertEqual(report["unexpected_native_book_codes"], ["Ps"])

    def test_source_reordering_blocks_even_if_reference_sets_are_same(self):
        report = compare_mapped_scope(
            ["EXO", "GEN"], [("GEN", 1, 1), ("EXO", 1, 1)],
            "Gen.1.1\nExod.1.1\n", PAIRS)
        self.assertFalse(report["source_canonical_book_order_verified"])
        self.assertFalse(report["canonical_verse_keys_exact_after_explicit_book_mapping"])

    def test_native_reordering_blocks_even_with_identical_reference_sets(self):
        report = compare_mapped_scope(
            ["GEN", "EXO"], [("GEN", 1, 1), ("EXO", 1, 1)],
            "Exod.1.1\nGen.1.1\n", PAIRS)
        self.assertEqual(report["status"], "blocked_crosswalk_book_scope_or_order_mismatch")

    def test_crosswalk_rejects_ambiguous_or_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "mapping.json"
            for books in [
                [{"usfm": "GEN", "osis": "Gen"}, {"usfm": "GEN", "osis": "Exod"}],
                [{"usfm": "GEN", "osis": "Gen"}, {"usfm": "EXO", "osis": "Gen"}],
                [{"usfm": "GEN", "osis": "Gen"}, {"usfm": "../", "osis": "Exod"}],
                [{"usfm": "GEN", "osis": "Gen", "undocumented": "exception"}],
            ]:
                with self.subTest(books=books):
                    path.write_text(json.dumps({"schema_version": 1, "books": books}))
                    with self.assertRaises(BookScopeError):
                        read_crosswalk(path)

    def test_crosswalk_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "map.json"
            original.write_text('{"schema_version":1,"books":[{"usfm":"GEN","osis":"Gen"}]}')
            symlink = root / "link.json"
            symlink.symlink_to(original)
            with self.assertRaises(BookScopeError):
                read_crosswalk(symlink)

    def test_repeated_authorial_key_blocks(self):
        with self.assertRaisesRegex(BookScopeError, "Repeated"):
            compare_mapped_scope(
                ["GEN", "EXO"], [("GEN", 1, 1), ("GEN", 1, 1), ("EXO", 1, 1)],
                "Gen.1.1\nExod.1.1\n", PAIRS)

    def test_source_reference_outside_actual_book_inventory_blocks(self):
        with self.assertRaisesRegex(BookScopeError, "outside identified book"):
            compare_mapped_scope(
                ["GEN", "EXO"], [("GEN", 1, 1), ("LEV", 1, 1)],
                "Gen.1.1\nExod.1.1\n", PAIRS)

    def test_noncontiguous_native_book_occurrences_block(self):
        with self.assertRaisesRegex(BookScopeError, "noncontiguous"):
            compare_mapped_scope(
                ["GEN", "EXO"], [("GEN", 1, 1), ("EXO", 1, 1)],
                "Gen.1.1\nExod.1.1\nGen.1.2\n", PAIRS)

    def test_report_never_contains_scripture(self):
        report = compare_mapped_scope(
            ["GEN", "PS2", "EXO"], [("GEN", 1, 1), ("PS2", 1, 1), ("EXO", 1, 1)],
            "Gen.1.1\nExod.1.1\n", PAIRS)
        self.assertNotIn("In the beginning", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
