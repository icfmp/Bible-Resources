"""Private source division title and scripCom OSIS book/start consistency audit."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_private_text_compare import _original_source_markers
from commentary_original_div1_book_consistency import private_original_div1_book_code_consistency
from pilot_preflight import PilotError


def synthetic_original():
    # Two physically distinct original book divisions deliberately share an
    # scripCom target book/start value. Neither source nor compiled module
    # is silently corrected based on this syntactic collision.
    xml=(
        b'<?xml version="1.0"?><ThML><ThML.body>'
        b'<div1 title="Early original book heading"><div2>'
        b'<scripCom osisRef="Bible:Judg.1.1"/>'
        b'<div><p>An early source explanatory paragraph.</p></div>'
        b'</div2></div1>'
        b'<div1 title="Different original book heading"><div2>'
        b'<scripCom osisRef="Bible:Judg.1.1"/>'
        b'<div><p>A late source explanatory paragraph.</p></div>'
        b'<scripCom osisRef="Bible:Judg.1.4-Judg.1.5"/>'
        b'<div><p>Another later original source paragraph.</p></div>'
        b'</div2></div1>'
        b'</ThML.body></ThML>'+b" "*1100
    )
    source,_=_original_source_markers(xml)
    units=[(key,u) for key,v in source.items() for u in v]
    sample_group={
        "native_shared_raw_SHA256":sha256(b"<p>Stock raw</p>").hexdigest(),
        "distinct_original_scripCom_source_units_starting_in_shared_run":len(units),
        "original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order":[
            {
                "original_source_line":u["original_source_line"],
                "original_full_reference_sha256":u["original_full_reference_sha256"],
                "original_source_body_sha256":u["original_text_sha256"],
                "original_enclosing_div1_ordinal_in_original_XML_document":
                    u["private_original_enclosing_div1_document_ordinal"],
            }
            for key,u in units
        ],
    }
    return source,{
        "bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports":[sample_group]
    }


class OriginalDiv1OsisBookClaimTests(unittest.TestCase):
    def test_different_original_div1_heading_and_same_source_book_start_is_exposed_without_rewrite(self):
        source,shared=synthetic_original()
        report=private_original_div1_book_code_consistency(source,shared)
        self.assertEqual(report["original_source_div1_document_total"],2)
        self.assertEqual(report["original_div1_with_at_least_one_verse_range_source_marker_count"],2)
        self.assertEqual(report["original_verse_range_source_units_considered"],3)
        self.assertEqual(report["distinct_original_osisRef_book_code_count"],1)
        self.assertEqual(report["original_osisRef_book_tokens_used_in_more_than_one_div1_count"],1)
        self.assertEqual(report["original_scripCom_start_key_reused_across_different_div1_count"],1)
        self.assertEqual(report["original_div1_distinct_declared_osisRef_book_token_count_distribution"],{1:2})
        self.assertEqual(report["original_osisRef_book_tokens_original_div1_occurrence_count_distribution"],{2:1})
        self.assertEqual(report["original_source_div1_heading_origin_counts"],{"title_attribute":2})
        group=report["focused_shared_raw_source_group_original_bookcode_and_div1_heading_evidence"][0]
        self.assertEqual(group["original_source_unit_count"],3)
        self.assertEqual(group["distinct_original_div1_count"],2)
        self.assertEqual(group["original_div1_document_ordinals"],[1,2])
        self.assertEqual(group["distinct_original_declared_book_token_count"],1)
        self.assertTrue(group["all_original_source_units_claim_same_osisRef_book_code"])
        self.assertTrue(group["same_claimed_book_code_occurs_in_multiple_original_div1_sections"])
        self.assertEqual(group["distinct_nonempty_original_div1_heading_SHA256_count"],2)
        self.assertTrue(group["original_source_div1_heading_hashes_distinct_when_present"])
        self.assertEqual([u["original_div1_document_ordinal"] for u in
            group["source_members_line_sha256_and_div1_heading_metadata"]],[1,2,2])
        raw=json.dumps(report)
        self.assertNotIn("Early original book heading",raw)
        self.assertNotIn("Different original book heading",raw)
        self.assertNotIn("Judg.1",raw)
        self.assertNotIn("explanatory paragraph",raw)

    def test_forged_div1_ancestry_blocks_aggregated_source_report(self):
        source,shared=synthetic_original()
        bad=source["Judg.1.1"][0]
        bad["private_original_enclosing_div1_document_ordinal"]=20
        with self.assertRaises(PilotError):
            private_original_div1_book_code_consistency(source,shared)

    def test_one_original_div1_heading_hash_must_be_stable_across_all_markers(self):
        source,shared=synthetic_original()
        source["Judg.1.4"][0]["private_original_div1_heading_sha256"]="0"*64
        with self.assertRaises(PilotError):
            private_original_div1_book_code_consistency(source,shared)

    def test_no_same_book_div1_title_claim_without_original_source_case(self):
        source,shared=synthetic_original()
        group=shared["bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports"][0]
        group["original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order"][0][
            "original_body_sha256"]="0"*64
        with self.assertRaises(PilotError):
            private_original_div1_book_code_consistency(source,shared)


if __name__=="__main__":
    unittest.main()
