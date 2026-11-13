"""Original source-complete inventory for one native repeated-raw K-key group."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_private_text_compare import _original_source_markers
from commentary_shared_raw_source_units import (
    inspect_shared_original_units_in_native_runs
)
from commentary_source_native_boundaries import NativeRawRunBoundaryInventory
from pilot_preflight import PilotError


def fixtures():
    xml=(
        b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
        b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.2"/>'
        b'<div><p>Alpha original scripture text with source reference '
        b'<scripRef osisRef="Bible:Gen.2.2">Gen two</scripRef> and words.</p></div>'
        b'<scripCom osisRef="Bible:Gen.1.3-Gen.1.4"/>'
        b'<div><p>Second original commentary body independently penned.</p></div>'
        b'<scripCom osisRef="Bible:Gen.1.5-Gen.1.6"/>'
        b'<div><p>Third original scripture comment with distinct words.</p></div>'
        b'</div2></div1></ThML.body></ThML>'+b" "*1100
    )
    original,_proof=_original_source_markers(xml)
    compiled=(b'<p>Compiled different original source text, '
              b'<reference osisRef="Gen.2.2">Reference label</reference> '
              b'but other prose exists.</p>')
    source_starts=("Gen.1.1","Gen.1.3","Gen.1.5")
    ledger=NativeRawRunBoundaryInventory()
    for key in ("Gen.1.1","Gen.1.2","Gen.1.3","Gen.1.4","Gen.1.5","Gen.1.6"):
        ledger.observe("K",key,compiled)
    ledger.observe("I","Gen.1.0",b"<title>Chapter summary</title>")
    matches={key:compiled for key in source_starts}
    def receipt(key):
        unit=original[key][0]
        return {
            "original_source_line":unit["original_source_line"],
            "original_full_reference_sha256":unit["original_full_reference_sha256"],
            "original_body_sha256":unit["original_text_sha256"],
            "stock_raw_sha256":sha256(compiled).hexdigest(),
        }
    serious=[receipt("Gen.1.1"),receipt("Gen.1.5")]
    return original,ledger,matches,serious,compiled


class CompleteOriginalUnitsPerNativeRawRunTests(unittest.TestCase):
    def test_two_large_source_cases_find_all_three_authentic_original_units_and_words(self):
        original,ledger,matches,serious,_=fixtures()
        report=inspect_shared_original_units_in_native_runs(
            original,ledger,matches,serious)
        self.assertEqual(report["multi_original_source_start_same_native_raw_run_groups"],1)
        self.assertEqual(report["full_authentic_original_source_units_in_those_runs"],3)
        self.assertEqual(report["previously_unreviewed_original_source_units_now_identified"],1)
        group=report["bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports"][0]
        self.assertEqual(group["native_occupied_numbered_K_keys_in_shared_raw_run"],6)
        self.assertEqual(group["previously_known_serious_original_prose_cases_in_this_run"],2)
        self.assertEqual(group["additional_authentic_original_source_units_identified"],1)
        self.assertEqual(group["native_raw_run_K_keys_covered_by_at_least_one_actual_original_source_range"],6)
        self.assertEqual(group["native_raw_run_K_keys_claimed_by_multiple_original_source_ranges"],0)
        self.assertEqual(group["native_raw_run_K_keys_uncovered_by_original_source_ranges_starting_in_run"],0)
        units=group["original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order"]
        self.assertEqual(len(units),3)
        self.assertEqual([u["original_declared_source_start_ordinal_inside_identical_raw_native_run"] for u in units],[1,3,5])
        self.assertEqual([u["original_source_comment_was_one_of_previously_seven_large_discrepancies"] for u in units],[True,False,True])
        self.assertEqual([u["original_source_numeric_verse_span"] for u in units],[2,2,2])
        self.assertTrue(all(u["original_declared_source_end_key_within_shared_raw_run"] for u in units))
        self.assertEqual(units[0]["original_source_scripRef_element_count"],1)
        self.assertEqual(units[1]["original_source_scripRef_element_count"],0)
        self.assertEqual(units[0]["original_source_direct_body_tag_counts"]["p"],1)
        self.assertEqual(units[0]["original_source_direct_body_tag_counts"]["scripRef"],1)
        self.assertEqual(units[0]["compiled_shared_raw_plain_word_token_count"],
                         units[1]["compiled_shared_raw_plain_word_token_count"])
        self.assertTrue(group["combined_original_source_plain_words_in_original_XML_unit_order_vs_one_stock_raw"][
            "longest_common_subsequence_is_not_textual_or_edition_parity"])
        self.assertNotIn("Bible:Gen",json.dumps(report))
        self.assertNotIn("Second original commentary body",json.dumps(report))
        self.assertNotIn("Reference label",json.dumps(report))
        self.assertNotIn("Gen.1.1",json.dumps(report))
        self.assertNotIn("Gen.1.3",json.dumps(report))
        self.assertNotIn("Gen.1.5",json.dumps(report))

    def test_one_source_case_only_does_not_make_multi_source_group(self):
        original,ledger,matches,serious,_=fixtures()
        result=inspect_shared_original_units_in_native_runs(
            original,ledger,matches,serious[:1])
        self.assertEqual(result["multi_original_source_start_same_native_raw_run_groups"],0)
        self.assertEqual(result["full_authentic_original_source_units_in_those_runs"],0)

    def test_same_payload_hash_in_disjoint_native_raw_runs_is_not_one_group(self):
        original,ledger,matches,serious,raw=fixtures()
        distinct=NativeRawRunBoundaryInventory()
        for k,p in (("Gen.1.1",raw),("Gen.1.2",raw),
                    ("Gen.1.3",b"<p>OTHER</p>"),
                    ("Gen.1.4",b"<p>OTHER</p>"),
                    ("Gen.1.5",raw),("Gen.1.6",raw)):
            distinct.observe("K",k,p)
        result=inspect_shared_original_units_in_native_runs(
            original,distinct,matches,serious)
        self.assertEqual(result["multi_original_source_start_same_native_raw_run_groups"],0)

    def test_full_original_hash_and_actual_stock_K_digest_required(self):
        original,ledger,matches,serious,_=fixtures()
        bad=[dict(serious[0],original_body_sha256="0"*64),serious[1]]
        with self.assertRaises(PilotError):
            inspect_shared_original_units_in_native_runs(original,ledger,matches,bad)
        with self.assertRaises(PilotError):
            inspect_shared_original_units_in_native_runs(
                original,ledger,dict(matches,**{"Gen.1.3":b"<p>Other unreviewed bytes</p>"}),serious)

    def test_original_nonlink_verse_range_cannot_be_guessed_outside_one_chapter(self):
        original,ledger,matches,serious,_=fixtures()
        original["Gen.1.3"][0]["private_original_declared_range_end_key"]="Gen.2.2"
        with self.assertRaises(PilotError):
            inspect_shared_original_units_in_native_runs(original,ledger,matches,serious)


if __name__=="__main__":
    unittest.main()
