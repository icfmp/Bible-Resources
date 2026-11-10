"""Synthetic full-group authorial verse → occupied native-entry witnesses.

No original publisher Scripture is embedded in or emitted from these tests.
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from native_absorbed_verse_groups import (
    inspect_absorbed_source_verse_groups, AbsorbedVerseEvidenceError,
)

AUTHORED = {
    "Rom.14.23": "First original phrase. ",
    "Rom.14.24": "Second authored part. ",
    "Rom.14.25": "Third authored segment. ",
    "Rom.14.26": "Last authored section.",
}
NATIVE = {"Rom.14.23"}


def compare(original=None, native_text=None, occupied=None):
    text = original if original is not None else AUTHORED
    main = (native_text if native_text is not None else
            {"Rom.14.23": "".join(text.values())})
    return inspect_absorbed_source_verse_groups(
        text, occupied if occupied is not None else NATIVE, main)


class CompleteAbsorbedSourceVerseTests(unittest.TestCase):
    def test_all_adjacent_source_only_verse_words_exist_in_same_actual_slot(self):
        report = compare()
        self.assertEqual(report["source_only_reference_count"], 3)
        self.assertEqual(report["source_only_refs_whose_full_grouped_word_sequence_is_present"], 3)
        self.assertEqual(
            report["status"],
            "all_bounded_source_only_verse_groups_word_preservation_witnessed")
        entry = report["grouped_source_verses"][0]
        self.assertEqual(entry["occupied_native_ref"], "Rom.14.23")
        self.assertEqual(entry["original_source_only_refs"],
                         ["Rom.14.24", "Rom.14.25", "Rom.14.26"])
        self.assertTrue(entry["complete_grouped_semantic_characters_exact"])
        self.assertTrue(entry["complete_grouped_word_sequence_equal_diagnostic_only"])
        self.assertFalse(report["source_versification_preserved_in_native_reader"])
        self.assertTrue(report["source_only_references_still_unindexed"])
        self.assertFalse(report["notes_references_lexical_structure_verified"])
        self.assertFalse(report["whole_original_source_fidelity_verified"])
        self.assertFalse(report["publication_approved"])
        self.assertNotIn("First original phrase", json.dumps(report))
        self.assertNotIn("Second authored part", json.dumps(report))

    def test_whitespace_difference_does_not_claim_exact_character_identity(self):
        raw = {"Rom.14.23": "First original phrase. Second authored part. "
               "Third authored segment.   Last authored section."}
        report = compare(native_text=raw)
        entry = report["grouped_source_verses"][0]
        self.assertTrue(entry["complete_grouped_word_sequence_equal_diagnostic_only"])
        self.assertTrue(entry["complete_grouped_characters_equal_after_whitespace_folding"])
        self.assertFalse(entry["complete_grouped_semantic_characters_exact"])

    def test_punctuation_difference_is_not_accepted_as_characters_match(self):
        raw = {"Rom.14.23": "".join(AUTHORED.values()).replace(
            "First original phrase.", "First original phrase?")}
        report = compare(native_text=raw)
        entry = report["grouped_source_verses"][0]
        self.assertTrue(entry["complete_grouped_word_sequence_equal_diagnostic_only"])
        self.assertFalse(entry["complete_grouped_characters_equal_after_whitespace_folding"])
        self.assertFalse(entry["complete_grouped_semantic_characters_exact"])

    def test_missing_earlier_words_fails_whole_group_even_if_tail_matches(self):
        report = compare(native_text={"Rom.14.23": "".join(
            list(AUTHORED.values())[1:])})
        self.assertEqual(report["status"],
                         "blocked_or_incomplete_absorbed_source_verse_group_evidence")
        self.assertEqual(report["source_only_refs_without_complete_grouped_word_witness"], 3)

    def test_mutated_word_order_fails_even_if_all_word_runs_present(self):
        chunks = list(AUTHORED.values())
        report = compare(native_text={"Rom.14.23": chunks[0] + chunks[2]
                                      + chunks[1] + chunks[3]})
        self.assertFalse(report["grouped_source_verses"][0][
            "complete_grouped_word_sequence_equal_diagnostic_only"])

    def test_missing_predecessor_private_raw_never_becomes_success(self):
        report = compare(native_text={})
        self.assertEqual(report["grouped_source_verses"][0]["status"],
                         "blocked_no_captured_same_native_entry_maintext")
        self.assertEqual(report["source_only_refs_without_complete_grouped_word_witness"], 3)

    def test_nonconsecutive_or_out_of_chapter_source_refs_block(self):
        disconnected = {
            "Rom.14.23": "first",
            "Rom.14.25": "a missing number",
            "Rom.15.1": "next chapter unindexed",
        }
        report = compare(original=disconnected, native_text={"Rom.14.23": "first"},
                         occupied={"Rom.14.23"})
        self.assertEqual(report["source_only_reference_count"], 2)
        self.assertEqual(report["source_only_refs_without_complete_grouped_word_witness"], 2)
        self.assertTrue(report["unresolved_source_verse_refs"])

    def test_mixed_unreviewed_native_key_blocks_complete_status(self):
        report = compare(occupied={"Rom.14.23", "Rom.14.88"})
        self.assertEqual(report["native_occupied_refs_without_authored_counterpart_count"], 1)
        self.assertNotEqual(report["status"],
                            "all_bounded_source_only_verse_groups_word_preservation_witnessed")

    def test_untrusted_identifiers_or_captured_ref_outside_registry_rejected(self):
        with self.assertRaises(AbsorbedVerseEvidenceError):
            compare(original={"../../bad": "word"})
        with self.assertRaises(AbsorbedVerseEvidenceError):
            compare(native_text={"Rom.14.24": "fake native passage"})

    def test_many_source_only_verses_are_bounded_not_falsely_passed(self):
        raw = {"Gen.1.1": "original start"}
        for i in range(2, 70):
            raw[f"Gen.1.{i}"] = "synthetic"
        report = compare(original=raw, occupied={"Gen.1.1"},
                         native_text={"Gen.1.1": "original start"})
        self.assertEqual(report["status"],
                         "blocked_too_many_source_only_refs_for_bounded_diagnostic")
        self.assertFalse(report["whole_original_source_fidelity_verified"])


if __name__ == "__main__":
    unittest.main()
