"""Regression tests for generic, non-destructive commentary navigation proposals."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_navigation_link_plan import (
    propose_commentary_links, UnsafeCommentaryLinkPlan,
    parse_native_commentary_verse_registry, triage_missing_native_section_links,
)

A = "a" * 64
B = "b" * 64


def source(master, segments, digest=A, reviewed=True):
    return {"master_key": master, "raw_sha256": digest,
            "segments": segments, "source_scope_reviewed": reviewed,
            "evidence_ids": ["independent-scope-collation:sha256:" + "c" * 64]}


def span(chapter, first, last):
    return {"chapter": chapter, "from": first, "through": last}


class PlanTests(unittest.TestCase):
    def test_two_verse_comment_creates_one_alias_without_editing_master(self):
        result = propose_commentary_links(
            occupied={"Song.1.7": A},
            valid_verse_keys={"Song.1.7", "Song.1.8"},
            reviewed_sections=[source("Song.1.7", [span("Song.1", 7, 8)])])
        self.assertEqual(result["new_native_aliases"], {
            "Song.1.8": {"link_to": "Song.1.7", "source_raw_sha256": A}
        })
        self.assertFalse(result["original_keys_overwritten"])
        self.assertFalse(result["candidate_built_or_reader_tested"])

    def test_disjoint_passage_does_not_overwrite_middle_commentary(self):
        original = {**{f"Matt.13.{v}": A for v in range(24, 31)},
                    **{f"Matt.13.{v}": B for v in range(31, 36)}}
        outcome = propose_commentary_links(
            occupied=original,
            valid_verse_keys={f"Matt.13.{v}" for v in range(24, 44)},
            reviewed_sections=[source("Matt.13.24", [
                span("Matt.13", 24, 30), span("Matt.13", 36, 43)
            ])])
        self.assertEqual(set(outcome["new_native_aliases"]),
                         {f"Matt.13.{v}" for v in range(36, 44)})
        self.assertNotIn("Matt.13.31", outcome["new_native_aliases"])

    def test_whole_chapter_links_are_possible_when_editorially_reviewed(self):
        result = propose_commentary_links(
            occupied={"Gen.36.1": A},
            valid_verse_keys={f"Gen.36.{v}" for v in range(1, 44)},
            reviewed_sections=[source("Gen.36.1", [span("Gen.36", 1, 43)])])
        self.assertEqual(result["added_alias_count"], 42)
        self.assertEqual(result["original_occupied_keys_to_preserve"], 1)

    def test_same_payload_native_slots_are_noop(self):
        result = propose_commentary_links(
            occupied={"Amos.1.1": A, "Amos.1.2": A},
            valid_verse_keys={"Amos.1.1", "Amos.1.2"},
            reviewed_sections=[source("Amos.1.1", [span("Amos.1", 1, 2)])])
        self.assertEqual(result["added_alias_count"], 0)
        self.assertEqual(result["already_occupied_identical_body_keys"],
                         ["Amos.1.1", "Amos.1.2"])

    def test_different_payload_conflict_is_hard_block(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Matt.13.24": A, "Matt.13.31": B},
                valid_verse_keys={"Matt.13.24", "Matt.13.31"},
                reviewed_sections=[source("Matt.13.24",
                                         [span("Matt.13", 24, 31)])])

    def test_unreviewed_chapter_claim_is_hard_block(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Gen.36.1": A},
                valid_verse_keys={"Gen.36.1", "Gen.36.2"},
                reviewed_sections=[source("Gen.36.1",
                                          [span("Gen.36", 1, 2)], reviewed=False)])

    def test_canonical_registry_prevents_invented_verse(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Song.1.7": A}, valid_verse_keys={"Song.1.7"},
                reviewed_sections=[source("Song.1.7", [span("Song.1", 7, 8)])])

    def test_range_outside_master_is_blocked(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Gen.36.1": A}, valid_verse_keys={"Gen.36.1", "Gen.36.2"},
                reviewed_sections=[source("Gen.36.1", [span("Gen.36", 2, 2)])])

    def test_overlap_in_separate_segments_is_blocked(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Matt.13.24": A},
                valid_verse_keys={f"Matt.13.{v}" for v in range(24, 31)},
                reviewed_sections=[source("Matt.13.24", [
                    span("Matt.13", 24, 27), span("Matt.13", 27, 30)
                ])])

    def test_two_approved_sections_cannot_claim_same_unoccupied_key(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Song.1.7": A, "Song.1.9": B},
                valid_verse_keys={"Song.1.7", "Song.1.8", "Song.1.9"},
                reviewed_sections=[source("Song.1.7", [span("Song.1", 7, 8)]),
                                   source("Song.1.9", [span("Song.1", 8, 9)], B)])

    def test_missing_evidence_is_blocked(self):
        section = source("Song.1.7", [span("Song.1", 7, 8)])
        section["evidence_ids"] = []
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            propose_commentary_links(
                occupied={"Song.1.7": A},
                valid_verse_keys={"Song.1.7", "Song.1.8"},
                reviewed_sections=[section])



class MissingNativeSectionPreflightTests(unittest.TestCase):
    def test_missing_second_verse_is_candidate_not_edit_approval(self):
        result = triage_missing_native_section_links(
            occupied={"Song.1.7": A},
            valid_verse_keys={"Song.1.7", "Song.1.8"},
            source_heading_anomalies=[{
                "start": "Song.1.7", "missing_slots": ["Song.1.8"],
                "different_payload_slots": []
            }],
        )
        self.assertEqual(result["candidate_section_count"], 1)
        self.assertEqual(result["candidate_additional_native_target_keys"], 1)
        self.assertEqual(result["candidate_sections"][0]["original_master_raw_sha256"], A)
        self.assertEqual(result["candidate_sections"][0]["unoccupied_native_target_keys"], ["Song.1.8"])
        self.assertFalse(result["candidate_sections"][0]["source_scope_editorially_reviewed"])
        self.assertFalse(result["compiled_binary_modified"])
        self.assertFalse(result["release_authorized"])

    def test_discontinuous_section_has_only_actual_missing_second_block(self):
        occupied = {f"Matt.13.{n}": A for n in range(24, 31)}
        occupied.update({f"Matt.13.{n}": B for n in range(31, 36)})
        result = triage_missing_native_section_links(
            occupied=occupied,
            valid_verse_keys={f"Matt.13.{n}" for n in range(24,44)},
            source_heading_anomalies=[{
                "start": "Matt.13.24",
                "missing_slots": [f"Matt.13.{n}" for n in range(36,44)],
                "different_payload_slots": []
            }]
        )
        self.assertEqual(result["candidate_additional_native_target_keys"], 8)
        self.assertNotIn("Matt.13.31",result["candidate_sections"][0]["unoccupied_native_target_keys"])

    def test_collision_with_other_original_body_stays_blocked(self):
        result = triage_missing_native_section_links(
            occupied={"Matt.13.24": A, "Matt.13.31": B},
            valid_verse_keys={"Matt.13.24", "Matt.13.31", "Matt.13.36"},
            source_heading_anomalies=[{
                "start": "Matt.13.24", "missing_slots": ["Matt.13.36"],
                "different_payload_slots": ["Matt.13.31"]
            }]
        )
        self.assertEqual(result["candidate_section_count"],0)
        self.assertEqual(len(result["blocked_sections_with_different_existing_original_payload"]),1)

    def test_never_accept_an_occupied_or_noncannonical_missing_target(self):
        for valid, occupied in (
            ({"Song.1.7", "Song.1.8"}, {"Song.1.7": A, "Song.1.8": B}),
            ({"Song.1.7"}, {"Song.1.7": A}),
        ):
            with self.assertRaises(UnsafeCommentaryLinkPlan):
                triage_missing_native_section_links(
                    occupied=occupied, valid_verse_keys=valid,
                    source_heading_anomalies=[{
                        "start": "Song.1.7", "missing_slots": ["Song.1.8"],
                        "different_payload_slots": []
                    }]
                )

class NativeRegistryTests(unittest.TestCase):
    def test_exact_chapter_bounds_can_feed_generic_link_plan(self):
        payload = (
            b"M\tMHCC\tKJV\t1.9.0\tzCom\n"
            b"R\tGen.36\t43\n"
            b"R\tSong.1\t17\n"
            b"S\t2\t60\n"
        )
        registry = parse_native_commentary_verse_registry(payload, "MHCC")
        self.assertEqual(registry["chapter_count"], 2)
        self.assertEqual(registry["chapter_maximums"]["Gen.36"], 43)
        self.assertNotIn("Gen.36.44", registry["verse_keys"])
        result = propose_commentary_links(
            occupied={"Gen.36.1": A},
            valid_verse_keys=registry["verse_keys"],
            reviewed_sections=[source("Gen.36.1", [span("Gen.36", 1, 43)])]
        )
        self.assertEqual(result["added_alias_count"], 42)

    def test_rejects_forged_registry_totals_or_duplicate_chapters(self):
        for raw in (
            b"M\tMHCC\tKJV\t1.9.0\tzCom\nR\tGen.36\t43\nS\t1\t44\n",
            b"M\tMHCC\tKJV\t1.9.0\tzCom\nR\tGen.36\t43\nR\tGen.36\t43\nS\t2\t86\n",
            b"M\tMHCC\tKJV\t1.9.0\tzCom\nR\tGen.36\t43\nS\t1\t43\n", # valid
        ):
            if raw.endswith(b"S\t1\t43\n") and raw.count(b"R\t") == 1:
                parsed = parse_native_commentary_verse_registry(raw, "MHCC")
                self.assertEqual(parsed["canonical_verse_count"], 43)
            else:
                with self.assertRaises(UnsafeCommentaryLinkPlan):
                    parse_native_commentary_verse_registry(raw, "MHCC")

    def test_mismatched_module_and_out_of_range_verses_blocked(self):
        for raw in (
            b"M\tMHC\tKJV\t1.9.0\tzCom\nR\tGen.36\t43\nS\t1\t43\n",
            b"M\tMHCC\tKJV\t1.9.0\tzCom\nR\tGen.36\t1001\nS\t1\t1001\n",
            b"M\tMHCC\tKJV\t1.9.0\tzCom\nR\tGen.36\t0\nS\t1\t0\n",
        ):
            with self.assertRaises(UnsafeCommentaryLinkPlan):
                parse_native_commentary_verse_registry(raw, "MHCC")


if __name__ == "__main__":
    unittest.main()
