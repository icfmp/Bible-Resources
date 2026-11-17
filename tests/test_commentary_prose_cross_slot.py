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
    OriginalExtraGapNativeChapterProbe,
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

    def test_four_word_fallback_remains_weak_and_does_not_count_as_six_word_witness(self):
        source,cases,selected,_=fixture()
        probe=OriginalProseAlternativeNativeSlotProbe(source,cases)
        probe.observe("K","Gen.1.1",selected)
        probe.observe("K","Gen.1.4",b"<p>w0 w1 w2 w3 unrelated longer rest</p>")
        result=probe.report()
        unit=result["all_original_large_plain_word_case_line_fullhash_scope_witnesses"][0]
        scope=unit["by_native_scope"]["other_numbered_key_same_chapter"]
        self.assertEqual(scope["scope_outcome"],
                         "other_stock_entry_improves_original_ordered_word_match")
        self.assertEqual(scope["best_candidate"][
            "original_contiguous_anchor_strength_class"],
            "only_four_or_five_original_words_contiguous_in_stock")
        self.assertEqual(scope["best_candidate"][
            "longest_exact_contiguous_source_word_run"],4)
        self.assertEqual(unit["native_slots_with_any_six_word_anchor_in_distinct_payload"],0)
        self.assertEqual(unit["native_slots_with_four_or_five_word_anchor_in_distinct_payload"],1)
        self.assertTrue(result[
            "weak_four_or_five_word_anchor_does_not_prove_same_original_authorial_section"])

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
                         "no_nonidentical_stock_payload_with_four_contiguous_source_words")
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



class OriginalExtraGapChapterNativeTests(unittest.TestCase):
    def _original_case(self):
        from commentary_nonlink_words import compare_words_outside_links
        first=[f"secretFirst{i}" for i in range(105)]
        second=[f"secretSecond{i}" for i in range(12)]
        source=["opening"]+first+["middle"]+second+["closing"]
        stock=["opening","middle","closing"]
        original=" ".join(source)
        raw=b"<p>opening middle closing</p>"
        item={
            "original_text":original,
            "original_source_line":27749,
            "original_text_sha256":sha256(original.encode()).hexdigest(),
            "original_full_reference_sha256":sha256(b"authorial source ref").hexdigest(),
            "private_original_scripRef_word_indices":[],
        }
        evidence=compare_words_outside_links(source,stock,[],[])
        return ("Gen.1.1",item,raw,evidence),first,second

    def test_full_original_extra_spans_located_only_in_distinct_same_chapter_raw(self):
        sample,first,second=self._original_case()
        probe=OriginalExtraGapNativeChapterProbe([sample])
        probe.observe("K","Gen.1.1",sample[2])
        probe.observe("K","Gen.1.2",sample[2])
        probe.observe("K","Gen.1.3",("<p>preface "+" ".join(first)+" conclusion</p>").encode())
        probe.observe("I","Gen.1.0",("<p>preface "+" ".join(second)+" conclusion</p>").encode())
        probe.observe("K","Gen.2.3",("<p>"+" ".join(first)+"</p>").encode())
        result=probe.report()
        self.assertEqual(result["source_extra_outlier_cases_examined"],1)
        self.assertEqual(result["complete_original_native_raw_entries_replayed"],5)
        case=result["original_source_line_hash_and_native_other_slot_counts_only"][0]
        self.assertEqual(case["original_unlinked_extra_word_span_lengths"],[105,12])
        self.assertEqual(case["extra_spans_tested_with_minimum_six_original_words"],2)
        self.assertEqual(case["extra_spans_exactly_witnessed_in_distinct_same_chapter_K_raw"],1)
        self.assertEqual(case["extra_spans_exactly_witnessed_in_distinct_same_chapter_I_raw"],1)
        self.assertEqual(case["distinct_extra_spans_witnessed_in_any_other_same_chapter_raw"],2)
        self.assertEqual(case["identical_selected_native_raw_repeat_keys_not_independent"],2)
        self.assertNotIn("secretFirst",json.dumps(result))
        self.assertNotIn("Gen.1.3",json.dumps(result))

    def test_an_unsupported_or_wrong_source_span_fails_closed(self):
        sample,_,_=self._original_case()
        baditem=dict(sample[1],original_text_sha256="0"*64)
        with self.assertRaises(PilotError):
            OriginalExtraGapNativeChapterProbe([(sample[0],baditem,sample[2],sample[3])])
        badmeta=dict(sample[3],source_extra_unlinked_word_gap_layout=None)
        with self.assertRaises(PilotError):
            OriginalExtraGapNativeChapterProbe([(sample[0],sample[1],sample[2],badmeta)])

    def test_exact_source_thml_paragraph_ownership_is_metadata_only(self):
        sample, first, second=self._original_case()
        marker=b"Bible:Gen.1.1"
        body=(
            "<div><p>opening "+" ".join(first)+" middle</p> "
            "<p>"+" ".join(second)+" closing</p></div>"
        )
        xml=(
            b"<ThML>\n<div1>\n<scripCom osisRef='Bible:Gen.1.1'/>"
            +body.encode("utf-8")
            +b"<scripCom osisRef='Bible:Gen.1.2'/><div><p>next text</p></div>"
            +b"</div1></ThML>"
        )
        item=dict(sample[1],
                  original_source_line=3,
                  original_full_reference_sha256=sha256(marker).hexdigest())
        probe=OriginalExtraGapNativeChapterProbe([
            (sample[0],item,sample[2],sample[3])
        ])
        report=probe.original_thml_extra_gap_structure(
            xml,expected_source_sha256=sha256(xml).hexdigest())
        cases=report["source_line_hash_and_original_adjacent_paragraph_structure_only"]
        self.assertEqual(len(cases),1)
        row=cases[0]
        self.assertEqual(row["original_adjacent_div_p_element_total"],2)
        self.assertEqual(row["original_next_sibling_element_type_only"],"scripCom")
        spans=row["original_extra_word_spans_authentically_within_adjacent_source_div"]
        self.assertEqual([x["exact_original_unlinked_extra_word_count"] for x in spans],
                         [105,12])
        self.assertEqual([x["original_paragraph_ownership_class"] for x in spans],
                         ["extra_span_inside_one_original_p"]*2)
        self.assertEqual([x["distinct_original_p_elements_touched"] for x in spans],[1,1])
        self.assertEqual([x["partially_covered_original_p_elements"] for x in spans],[1,1])
        self.assertNotIn("secretFirst",json.dumps(report))
        self.assertNotIn("Bible:Gen.1.1",json.dumps(report))
        with self.assertRaises(PilotError):
            probe.original_thml_extra_gap_structure(
                xml,expected_source_sha256="0"*64)

    def test_cross_original_p_gap_is_not_misattributed_to_one_paragraph(self):
        sample,first,second=self._original_case()
        first_left=" ".join(first[:60])
        first_right=" ".join(first[60:])
        original=sample[1]["original_text"]
        body=(
            "<div><p>opening "+first_left+"</p> "
            "<p>"+first_right+" middle "+" ".join(second)+" closing</p></div>"
        )
        self.assertEqual(
            __import__("lxml.etree",fromlist=["fromstring"]).fromstring(
                body.encode()).xpath("string(.)"),original)
        xml=(
            b"<ThML>\n<div1>\n<scripCom osisRef='Bible:Gen.1.1'/>"
            +body.encode()+b"</div1></ThML>"
        )
        item=dict(sample[1],original_source_line=3,
                  original_full_reference_sha256=sha256(b"Bible:Gen.1.1").hexdigest())
        probe=OriginalExtraGapNativeChapterProbe([
            (sample[0],item,sample[2],sample[3])
        ])
        structure=probe.original_thml_extra_gap_structure(
            xml,expected_source_sha256=sha256(xml).hexdigest())
        spans=structure[
            "source_line_hash_and_original_adjacent_paragraph_structure_only"][0][
            "original_extra_word_spans_authentically_within_adjacent_source_div"]
        self.assertEqual(spans[0]["original_paragraph_ownership_class"],
                         "extra_span_crosses_multiple_original_p_elements")
        self.assertEqual(spans[0]["distinct_original_p_elements_touched"],2)

    def test_no_hit_in_same_chapter_does_not_claim_text_lost(self):
        sample,_,_=self._original_case()
        probe=OriginalExtraGapNativeChapterProbe([sample])
        probe.observe("K","Gen.1.1",sample[2])
        probe.observe("K","Gen.1.3",b"<p>other chapter words only</p>")
        report=probe.report()
        case=report["original_source_line_hash_and_native_other_slot_counts_only"][0]
        self.assertEqual(case["distinct_extra_spans_witnessed_in_any_other_same_chapter_raw"],0)
        self.assertTrue(case["same_chapter_no_hit_does_not_prove_absence_elsewhere_or_authorial_loss"])


if __name__=="__main__":
    unittest.main()
