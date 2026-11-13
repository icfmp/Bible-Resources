"""Synthetic, content-private original scripture-target relocation/range topology."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_reference_cross_slot import (
    ReferenceCrossSlotTopology, actual_stock_osisref_targets,
    _private_target_counts, original_link_target_match_statuses,
)
from commentary_private_text_compare import _original_source_markers, compare_private_texts
from pilot_preflight import PilotError


def unit(line: int, *targets):
    return {
        "original_source_line":line,
        "original_full_reference_sha256":sha256(f"fake-ref-{line}".encode()).hexdigest(),
        "original_text_sha256":sha256(f"fake-body-{line}".encode()).hexdigest(),
        "private_original_scripRef_links":[
            {"private_original_osisRef_target": t, "text":"private dummy label",
             "attribute_name_types":["osisRef"]}
            for t in targets
        ],
    }


def expected(markers: int, source: int, stock: int, matched: int, without_ref: int,
             *, label_classes=None):
    return {
        "source_vs_stock_unresolved_word_selection_cases":markers,
        "original_scripRef_total_across_unresolved_entries":source,
        "stock_reference_total_across_unresolved_entries":stock,
        "raw_exact_osisRef_target_multiset_match_count":0,
        "literal_Bible_work_qualifier_only_osisRef_target_multiset_match_count":matched,
        "stock_reference_presence":{"stock_no_reference":without_ref,
                                     "stock_has_reference":markers-without_ref},
        "original_scripRef_display_label_location_in_stock_text_classes":(
            label_classes if label_classes is not None else
            {"original_label_text_not_located_in_selected_stock_entry":source}
        ),
    }


class OriginalReferenceCrossSlotTests(unittest.TestCase):
    def test_individual_source_target_occurrence_matching_prefers_exact_before_qualifier(self):
        labels=[
            {"private_original_osisRef_target":"Bible:Gen.1.3"},
            {"private_original_osisRef_target":"Bible:Gen.1.3"},
        ]
        self.assertEqual(original_link_target_match_statuses(labels,["Gen.1.3"]),[
            "literal_Bible_work_prefix_only_match","unpaired_original_target"
        ])
        labels=[
            {"private_original_osisRef_target":"Bible:Gen.1.3"},
            {"private_original_osisRef_target":"Gen.1.3"},
        ]
        self.assertEqual(original_link_target_match_statuses(labels,["Gen.1.3"]),[
            "unpaired_original_target","raw_target_exact_match"
        ])

    def test_unmatched_target_can_preserve_original_plain_label_outside_reference_tag(self):
        original={"Gen.1.1":[unit(15,"Bible:Gen.1.3")]}
        stock=b"<p>prefix private dummy label suffix</p>"
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        observed=probe.report(expected(
            1,1,0,0,1,
            label_classes={"literal_label_in_stock_text_outside_confirmed_reference_element":1}
        ))
        self.assertEqual(observed[
            "original_target_match_status_x_selected_stock_label_location"],{
                "unpaired_original_target":{
                    "literal_label_in_stock_text_outside_confirmed_reference_element":1
                }
            })
        self.assertEqual(observed[
            "unpaired_original_target_scope_x_selected_stock_label_location"],{
                "target_not_witnessed_in_other_same_book_stock_reference_markup":{
                    "literal_label_in_stock_text_outside_confirmed_reference_element":1
                }
            })
        self.assertNotIn("private dummy label",json.dumps(observed))

    def test_limited_target_multiplicity_accounting_does_not_duplicate_one_stock_link(self):
        remaining_source, remaining_stock, exact, prefix = _private_target_counts([
            {"private_original_osisRef_target":"Bible:Gen.1.3"},
            {"private_original_osisRef_target":"Bible:Gen.1.3"},
        ], ["Gen.1.3"])
        self.assertEqual((exact,prefix),(0,1))
        self.assertEqual(remaining_source,{"Bible:Gen.1.3":1})
        self.assertEqual(remaining_stock,{})

    def test_cross_slot_reference_is_a_witness_not_approved_citation_move(self):
        original={"Gen.1.1":[unit(15,"Bible:Gen.1.3","Bible:Gen.1.4")]}
        stock=b'<p>One <reference osisRef="Gen.1.3">label</reference></p>'
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_stock("K","Gen.1.2",
            b'<p>Elsewhere <reference osisRef="Gen.1.4">label</reference></p>')
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        result=probe.report(expected(1,2,1,1,0))
        self.assertEqual(result["source_unpaired_target_occurrence_location_classes"],{
            "target_witnessed_in_other_numbered_key_same_chapter":1
        })
        self.assertEqual(result["stock_unpaired_target_occurrence_source_classes"],{})
        self.assertTrue(result[
            "original_target_at_other_key_is_only_a_location_witness_not_source_annotation_parity"])
        self.assertNotIn("Gen.1.4",json.dumps(result))

    def test_same_chapter_intro_location_separate_from_verse(self):
        original={"Gen.1.1":[unit(15,"Bible:Gen.1.3")]}
        stock=b"<p>No scripture targets</p>"
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_stock("I","Gen.1.0",
            b'<reference osisRef="Gen.1.3">intro label</reference>')
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        result=probe.report(expected(1,1,0,0,1))
        self.assertEqual(result["source_unpaired_target_occurrence_location_classes"],{
            "target_witnessed_in_same_chapter_intro_key":1
        })

    def test_no_reference_and_range_propagation_are_distinct(self):
        original={"Gen.1.1":[unit(15,"Bible:Gen.1.3")]}
        stock=b"<p>Unmarked plain content</p>"
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_stock("K","Gen.1.2",stock)
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        result=probe.report(expected(1,1,0,0,1))
        case=result["bounded_all_no_stock_reference_case_line_fullhash_topology"][0]
        self.assertEqual(case["same_book_numbered_native_keys_with_identical_selected_raw"],2)
        self.assertEqual(case["unpaired_original_target_scope_counts"],{
            "target_not_witnessed_in_other_same_book_stock_reference_markup":1
        })
        self.assertNotIn("Unmarked",json.dumps(result))

    def test_original_other_source_unit_target_can_explain_extra_stock_target_location(self):
        original={
            "Gen.1.1":[unit(15,"Bible:Gen.1.3")],
            "Gen.1.2":[unit(20,"Bible:Gen.2.2")],
        }
        stock=(b'<reference osisRef="Gen.1.3">a</reference>'
               b'<reference osisRef="Gen.2.2">b</reference>')
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        result=probe.report(expected(1,1,2,1,0))
        self.assertEqual(result["stock_unpaired_target_occurrence_source_classes"],{
            "target_witnessed_in_other_original_source_unit_same_chapter":1
        })

    def test_generic_integration_receives_only_preexisting_unresolved_classification(self):
        original_xml=(
            b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
            b'<scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>Opening <scripRef osisRef="Bible:Gen.2.1">original'
            b'</scripRef> ending.</p></div>'
            b'</div2></div1></ThML.body></ThML>'+b" "*1100
        )
        source,_=_original_source_markers(original_xml)
        stock=b'<p>Opening <reference osisRef="Gen.2.1">changed</reference> ending.</p>'
        probe=ReferenceCrossSlotTopology(source)
        probe.observe_stock("K","Gen.1.1",stock)
        analysis=compare_private_texts(source,{"Gen.1.1":stock},
                                      on_unresolved_word_case=probe.observe_unresolved)
        result=probe.report(analysis["unresolved_source_stock_lexical_selection_triage"])
        self.assertEqual(result["source_markers_with_lexically_unresolved_reference_issues"],1)
        self.assertEqual(result["source_and_stock_literal_Bible_work_prefix_only_matches"],1)
        self.assertFalse(result["authorial_original_to_stock_text_markup_or_edition_parity_verified"])

    def test_private_plain_word_anomaly_stock_duplicate_proof_uses_original_hash(self):
        original={"Gen.1.1":[unit(15,"Bible:Gen.1.3")]}
        stock=b"<p>Repeated original content within this compiled native range.</p>"
        probe=ReferenceCrossSlotTopology(original)
        probe.observe_stock("K","Gen.1.1",stock)
        probe.observe_stock("K","Gen.1.2",stock)
        probe.observe_unresolved("Gen.1.1",original["Gen.1.1"][0],stock)
        case={
            "original_source_line":15,
            "original_full_reference_sha256":original["Gen.1.1"][0][
                "original_full_reference_sha256"],
            "original_body_sha256":original["Gen.1.1"][0]["original_text_sha256"],
            "stock_raw_sha256":sha256(stock).hexdigest(),
        }
        topology=probe.report_nonlink_plain_word_stock_payloads(
            [case],total_nonlink_review_cases=1
        )
        self.assertEqual(topology["total_original_plain_word_cases_requiring_review"],1)
        self.assertFalse(topology["bounded_review_cases_truncated"])
        self.assertEqual(topology["source_plain_word_stock_payload_repetition_classes"],{
            "identical_stock_raw_payload_in_multiple_native_keys_same_book":1
        })
        witness=topology[
            "bounded_plain_word_cases_line_fullhash_and_repeated_native_slot_counts"][0]
        self.assertEqual(witness[
            "same_book_numbered_native_keys_with_identical_raw_payload"],2)
        self.assertNotIn("Repeated original",json.dumps(topology))
        with self.assertRaises(PilotError):
            probe.report_nonlink_plain_word_stock_payloads(
                [dict(case,original_body_sha256="0"*64)],
                total_nonlink_review_cases=1
            )

    def test_invalid_native_reference_xml_rejected_and_not_silently_considered_citation(self):
        with self.assertRaises(PilotError):
            actual_stock_osisref_targets(b'<reference osisRef="Gen.1.1"></incorrect>')


if __name__=="__main__":
    unittest.main()
