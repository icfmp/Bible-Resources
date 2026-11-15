"""Regression tests for generic, non-destructive commentary navigation proposals."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_navigation_link_plan import (
    propose_commentary_links, UnsafeCommentaryLinkPlan,
    parse_native_commentary_verse_registry, triage_missing_native_section_links,
    triage_single_key_chapter_navigation,
    verify_original_native_adjacent_section_boundaries,
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




class WholeChapterSourceTriageTests(unittest.TestCase):
    def case(self, key, *, scope="SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE",
             overlap="HIGH_95_PLUS", unmatched=0, target_count=0,
             target_paired=0):
        return {
            "native_start":key,
            "source_div2_structure_class":scope,
            "independent_lexical_comparison":{
                "overlap_class":overlap,
                "ordered_word_alignment":{
                    "original_plain_words_not_matched_in_exact_order":unmatched,
                    "stock_plain_words_not_matched_in_exact_order":0,
                }
            },
            "independent_reference_target_comparison":{
                "original_scripRef_with_nonempty_osisRef_target_count":target_count,
                "original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock":
                    target_paired,
                "original_scripRef_osisRef_work_qualifier_only_matches_in_stock":0
            }
        }

    def test_strong_chapter_witness_is_review_candidate_without_new_aliases(self):
        observed=triage_single_key_chapter_navigation(
            occupied={"Gen.36.1":A},
            chapter_verse_maximums={"Gen.36":43},
            independent_chapter_cases=[self.case("Gen.36.1")],
            original_chapter_intro_has_visible_prose={"Gen.36":False},
        )
        self.assertEqual(observed["original_single_key_chapter_candidates"],1)
        self.assertEqual(observed["potential_total_new_chapter_aliases_if_every_scope_approved"],42)
        self.assertEqual(observed["classes"],{
            "INDEPENDENT_UNDIVIDED_CHAPTER_SCOPE_STRONGLY_CORROBORATED":1
        })
        self.assertFalse(observed["any_new_aliases_created"])
        self.assertFalse(observed["publication_authorized"])

    def test_source_mapping_word_drift_and_native_intro_prose_have_distinct_blocks(self):
        cases=[
            self.case("Gen.1.1",scope="NO_SAFE_SOURCE_DIV2_FOR_NATIVE_CHAPTER"),
            self.case("Exod.1.1",overlap="HIGH_80_PLUS"),
            self.case("Lev.1.1"),
            self.case("Num.1.1",target_count=2,target_paired=1),
        ]
        observed=triage_single_key_chapter_navigation(
            occupied={r["native_start"]:A for r in cases},
            chapter_verse_maximums={r["native_start"].rsplit(".",1)[0]:20
                                    for r in cases},
            independent_chapter_cases=cases,
            original_chapter_intro_has_visible_prose={
                "Gen.1":False, "Exod.1":False,
                "Lev.1":True, "Num.1":False
            }
        )
        self.assertEqual(observed["classes"],{
            "NO_SAFE_INDEPENDENT_UNDIVIDED_CHAPTER_SCOPE":1,
            "INDEPENDENT_SOURCE_AND_NATIVE_TEXT_NEED_WORD_REVIEW":1,
            "ADDITIONAL_NATIVE_CHAPTER_INTRO_PROSE_NEEDS_OWNERSHIP_REVIEW":1,
            "INDEPENDENT_UNDIVIDED_CHAPTER_SCOPE_STRONGLY_CORROBORATED":1,
        })
        self.assertEqual(observed["source_reference_differences_needing_separate_review"],1)
        self.assertEqual(observed["chapter_intro_prose_needing_independent_ownership_review"],1)
        self.assertFalse(observed["any_new_aliases_created"])

    def test_structural_first_chapter_prefix_kept_distinct_from_explicit_div2(self):
        sample=self.case(
            "Gen.1.1",
            scope="SOURCE_BOOK_PREFIX_FIRST_CHAPTER_UNDIVIDED_CANDIDATE"
        )
        sample["source_book_prefix_first_chapter_structural_witness"]={
            "all_source_book_identity_and_chapter_order_guards_pass":True,
            "source_book_prefix_prose_is_complete_in_original_K":True,
            "source_book_prefix_first_chapter_attribution_approved":False,
        }
        given=dict(occupied={"Gen.1.1":A},
                   chapter_verse_maximums={"Gen.1":31},
                   independent_chapter_cases=[sample],
                   original_chapter_intro_has_visible_prose={"Gen.1":False})
        result=triage_single_key_chapter_navigation(**given)
        self.assertEqual(result["classes"],{
            "SOURCE_FIRST_CHAPTER_PROSE_PRESERVED_OUTSIDE_DIV2":1
        })
        self.assertFalse(result["publication_authorized"])
        sample["source_book_prefix_first_chapter_structural_witness"][
            "all_source_book_identity_and_chapter_order_guards_pass"]=False
        bad=triage_single_key_chapter_navigation(**given)
        self.assertEqual(bad["classes"],{
            "SOURCE_BOOK_PREFIX_STRUCTURAL_EVIDENCE_UNVERIFIED":1
        })

    def test_extra_original_book_heading_is_preserved_not_auto_removed(self):
        case=self.case("Neh.1.1",overlap="HIGH_80_PLUS")
        case["independent_lexical_comparison"]={
            "overlap_class":"HIGH_80_PLUS",
            "ordered_word_alignment":{
                "original_plain_words_not_matched_in_exact_order":0,
                "stock_plain_words_not_matched_in_exact_order":29,
            },
            "stock_extra_prefix_xml_topology":{
                "prefix_text_top_level_owner_types":["title","_ROOT_TAIL"],
                "full_original_source_word_sequence_inside_stock":True,
            },
            "stock_prefix_independent_source_neighbor_correspondence":{
                "source_neighbor_to_stock_element_correspondence_classes":{
                    "exact_unicode:title:source_div1_title_attribute":1
                }
            }
        }
        result=triage_single_key_chapter_navigation(
            occupied={"Neh.1.1":A},
            chapter_verse_maximums={"Neh.1":11},
            independent_chapter_cases=[case],
            original_chapter_intro_has_visible_prose={"Neh.1":False})
        self.assertEqual(result["classes"],{
            "SOURCE_PROSE_PRESERVED_WITH_EXTRA_STOCK_BOOK_HEADING":1
        })
        self.assertTrue(result["case_rows"][0][
            "complete_independent_source_prose_with_original_stock_heading"])
        self.assertFalse(result["any_new_aliases_created"])
        case["independent_lexical_comparison"][
            "stock_prefix_independent_source_neighbor_correspondence"
        ]={}
        fail=triage_single_key_chapter_navigation(
            occupied={"Neh.1.1":A},
            chapter_verse_maximums={"Neh.1":11},
            independent_chapter_cases=[case],
            original_chapter_intro_has_visible_prose={"Neh.1":False})
        self.assertEqual(fail["classes"],{
            "INDEPENDENT_SOURCE_AND_NATIVE_TEXT_NEED_WORD_REVIEW":1
        })

    def test_existing_different_section_and_ambiguous_original_is_refused(self):
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            triage_single_key_chapter_navigation(
                occupied={"Gen.1.1":A, "Gen.1.3":B},
                chapter_verse_maximums={"Gen.1":31},
                independent_chapter_cases=[self.case("Gen.1.1")])
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            triage_single_key_chapter_navigation(
                occupied={"Gen.1.1":A},
                chapter_verse_maximums={"Gen.1":31},
                independent_chapter_cases=[self.case("Gen.1.3")])
        with self.assertRaises(UnsafeCommentaryLinkPlan):
            triage_single_key_chapter_navigation(
                occupied={"Gen.1.1":A},
                chapter_verse_maximums={"Gen.1":31},
                independent_chapter_cases=[self.case("Gen.1.1"),
                                           self.case("Gen.1.1")])



class CompleteOriginalNativeLinkedBoundaryTests(unittest.TestCase):
    def run_audit(self, occupied, pairs):
        linked=sum(last for first,second,last in pairs)
        line=["M\tMHCC\tKJV\t1.9.0\tzCom"]
        line.extend(f"L\t{a}\t{b}\t{n}" for a,b,n in pairs)
        line.append(f"S\t{len(pairs)}\t{linked}\t{len(pairs)-linked}")
        return verify_original_native_adjacent_section_boundaries(
            ("\n".join(line)+"\n").encode(),
            expected_module="MHCC",original_occupied_sha256=occupied
        )

    def test_exactly_equal_adjacent_entries_are_not_assumed_native_linked(self):
        got=self.run_audit({
            "Gen.1.1":A, "Gen.1.2":A, "Gen.1.3":A,
            "Gen.1.4":B,"Gen.1.5":B
        },[
            ("Gen.1.1","Gen.1.2",1),
            ("Gen.1.2","Gen.1.3",0),
            ("Gen.1.3","Gen.1.4",0),
            ("Gen.1.4","Gen.1.5",1),
        ])
        self.assertEqual(got["original_native_linked_pair_count"],2)
        self.assertEqual(
            got["same_original_raw_payload_but_independently_unlinked_pair_count"],1
        )
        self.assertEqual(
            got["same_original_raw_unlinked_first_ten"],[["Gen.1.2","Gen.1.3"]]
        )
        self.assertFalse(got["raw_payload_based_osis_grouping_is_native_identity_faithful"])

    def test_native_identity_and_raw_footprints_compatible(self):
        got=self.run_audit({
            "Gen.1.1":A,"Gen.1.2":A,"Gen.1.3":B,
            "Gen.1.5":B,
        },[
            ("Gen.1.1","Gen.1.2",1),
            ("Gen.1.2","Gen.1.3",0),
        ])
        self.assertEqual(got["original_adjacent_occupied_K_pair_count"],2)
        self.assertTrue(got["all_original_adjacent_native_section_identities_proven"])
        self.assertTrue(got["raw_payload_based_osis_grouping_is_native_identity_faithful"])
        self.assertTrue(got["original_source_text_copied_or_mutated"] is False)

    def test_missing_or_duplicate_native_identity_position_is_blocked(self):
        for rows in (
            [("Gen.1.1","Gen.1.2",1)],
            [("Gen.1.1","Gen.1.2",1),("Gen.1.1","Gen.1.2",0)],
            [("Gen.1.1","Gen.1.3",1),("Gen.1.2","Gen.1.3",0)],
        ):
            with self.subTest(rows=rows),self.assertRaises(UnsafeCommentaryLinkPlan):
                self.run_audit({
                    "Gen.1.1":A,"Gen.1.2":A,"Gen.1.3":B
                },rows)



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
