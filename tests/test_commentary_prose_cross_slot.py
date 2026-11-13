"""Synthetic, private location-only original commentary prose cross-slot tests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_prose_cross_slot import (
    OriginalProseAlternativeNativeSlotProbe,
    strict_native_stock_plain_words,
    longest_contiguous_original_word_run,
)
from pilot_preflight import PilotError


def fixture():
    original=" ".join(f"w{n}" for n in range(18))
    src_hash=sha256(original.encode()).hexdigest()
    ref_hash=sha256(b"private-source-reference").hexdigest()
    selected=b"<p>w0 w1 unrelated words</p>"
    item={
        "original_source_line":123,
        "original_full_reference_sha256":ref_hash,
        "original_text_sha256":src_hash,
        "original_text":original,
        "private_original_scripRef_word_indices":[],
    }
    case={
        "original_source_line":123,
        "original_full_reference_sha256":ref_hash,
        "original_body_sha256":src_hash,
        "stock_raw_sha256":sha256(selected).hexdigest(),
        "exact_plain_word_alignment":{
            "original_plain_word_tokens":18,
            "original_plain_words_not_matched_in_exact_order":16,
            "exact_unicode_longest_common_subsequence_word_count":2,
        },
    }
    return {"Gen.1.1":[item]},[case],selected,original


class OriginalLargeProseAlternativeSlotTests(unittest.TestCase):
    def test_nonlink_source_words_exclude_only_actual_compiled_reference_labels(self):
        self.assertEqual(
            strict_native_stock_plain_words(
                b'<p>intro <reference osisRef="Gen.1.1">label text</reference> outro</p>'
            ),["intro","outro"])
        self.assertEqual(
            strict_native_stock_plain_words(
                b'<p>intro label text outro</p>'
            ),["intro","label","text","outro"])

    def test_longest_exact_contiguous_source_run_has_no_fuzzy_matching(self):
        index={"one":[0],"two":[1],"three":[2],"four":[3]}
        self.assertEqual(longest_contiguous_original_word_run(
            index,["garbage","one","two","three","extra","four"]
        ),3)
        self.assertEqual(longest_contiguous_original_word_run(index,["ones","twos"]),0)

    def test_other_numbered_same_chapter_full_match_is_only_location_witness(self):
        source,cases,selected,original=fixture()
        probe=OriginalProseAlternativeNativeSlotProbe(source,cases)
        probe.observe("K","Gen.1.1",selected)
        probe.observe("K","Gen.1.2",selected)
        probe.observe("K","Gen.1.3",
                      ("<p>prefix "+original+" suffix</p>").encode())
        out=probe.report()
        self.assertEqual(out["original_source_large_plain_word_cases"],1)
        info=out["all_original_large_plain_word_case_line_fullhash_scope_witnesses"][0]
        self.assertEqual(info["same_raw_selected_payload_other_native_key_repetitions"],1)
        self.assertEqual(info["overall_scope_conclusion"],
            "source_plain_words_fully_in_order_in_other_native_payload_not_section_proof")
        same=info["by_native_scope"]["other_numbered_key_same_chapter"]
        self.assertEqual(same["scope_outcome"],
                         "all_original_plain_words_present_in_selected_other_stock_entry")
        self.assertEqual(same["best_candidate"]["original_plain_words_not_matched_in_order"],0)
        self.assertEqual(len(same["best_candidate"]["best_compiled_native_key_sha256"]),64)
        self.assertNotIn("Gen.1.3",json.dumps(out))
        self.assertNotIn("w12",json.dumps(out))

    def test_different_chapter_and_same_chapter_intro_are_separate_uncertain_witnesses(self):
        source,cases,selected,original=fixture()
        probe=OriginalProseAlternativeNativeSlotProbe(source,cases)
        probe.observe("K","Gen.1.1",selected)
        probe.observe("K","Gen.2.2",("<p>"+original+"</p>").encode())
        probe.observe("I","Gen.1.0",
                      ("<p>"+ " ".join(f"w{n}" for n in range(12)) +"</p>").encode())
        report=probe.report()
        by=report["all_original_large_plain_word_case_line_fullhash_scope_witnesses"][0]["by_native_scope"]
        self.assertEqual(by["numbered_key_other_chapter_same_book"]["scope_outcome"],
                         "all_original_plain_words_present_in_selected_other_stock_entry")
        self.assertEqual(by["same_chapter_intro"]["scope_outcome"],
                         "other_stock_entry_improves_original_ordered_word_match")

    def test_six_word_anchor_negative_does_not_claim_original_prose_missing(self):
        source,cases,selected,_=fixture()
        probe=OriginalProseAlternativeNativeSlotProbe(source,cases)
        probe.observe("K","Gen.1.1",selected)
        probe.observe("K","Gen.1.9",b"<p>random other words with no original passage</p>")
        r=probe.report()
        item=r["all_original_large_plain_word_case_line_fullhash_scope_witnesses"][0]
        self.assertEqual(item["overall_scope_conclusion"],
            "no_better_ordered_source_plain_word_witness_in_sampled_native_slots")
        self.assertEqual(item["by_native_scope"]["other_numbered_key_same_chapter"]["scope_outcome"],
                         "no_nonidentical_stock_payload_with_six_contiguous_source_words")
        self.assertTrue(r[
            "nonidentical_native_payload_match_is_not_an_original_source_range_or_edition_proof"])

    def test_authentic_source_line_full_reference_and_body_hashes_required(self):
        source,cases,selected,_=fixture()
        bad=[dict(cases[0],original_body_sha256="0"*64)]
        with self.assertRaises(PilotError):
            OriginalProseAlternativeNativeSlotProbe(source,bad)
        with self.assertRaises(PilotError):
            strict_native_stock_plain_words(b"<p>not closed</reference>")

    def test_no_source_word_or_literal_reference_target_in_public_report(self):
        source,cases,selected,original=fixture()
        probe=OriginalProseAlternativeNativeSlotProbe(source,cases)
        probe.observe("K","Gen.1.1",selected)
        probe.observe("K","Gen.1.2",("<p>"+original+"</p>").encode())
        encoded=json.dumps(probe.report())
        self.assertNotIn("w7",encoded)
        self.assertNotIn("Gen.1.2",encoded)
        self.assertIn("original_source_line",encoded)


if __name__=="__main__":
    unittest.main()
