"""Generic original ThML title evidence against existing 66-book English/OSIS aliases."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_private_text_compare import _original_source_markers
from commentary_source_english_osis_alias import (
    _classify, original_div1_english_alias_vs_declared_osis,
    read_existing_66_book_english_aliases,
)
from pilot_preflight import PilotError


def fixtures():
    xml=(
        b'<?xml version="1.0"?><ThML><ThML.body>'
        b'<div1 title="The Book of Judges"><div2>'
        b'<scripCom osisRef="Bible:Judg.1.1-Judg.1.3"/>'
        b'<div><p>Old source section comment.</p></div>'
        b'</div2></div1>'
        b'<div1 title="The Epistle of Jude"><div2>'
        b'<scripCom osisRef="Bible:Judg.1.1-Judg.1.2"/>'
        b'<div><p>Different new Testament source comment.</p></div>'
        b'</div2></div1>'
        b'</ThML.body></ThML>'+b" "*1100
    )
    source,_=_original_source_markers(xml)
    units=source["Judg.1.1"]
    shared={
        "bounded_shared_native_raw_run_source_unit_line_sha256_and_alignment_reports":[{
            "native_shared_raw_SHA256":sha256(b"<p>Compiled stock</p>").hexdigest(),
            "original_source_unit_starts_inside_same_native_raw_run_in_CCEl_XML_order":[
                {
                    "original_source_line":unit["original_source_line"],
                    "original_full_reference_sha256":unit["original_full_reference_sha256"],
                    "original_source_body_sha256":unit["original_text_sha256"],
                } for unit in units
            ],
        }]
    }
    return source,shared


class CanonicalEnglishTitleWitnessTests(unittest.TestCase):
    def test_existing_repo_66_book_crosswalk_is_complete_and_read_only(self):
        aliases,proof=read_existing_66_book_english_aliases()
        self.assertEqual(len(aliases),66)
        self.assertEqual(aliases["Judg"],"Judges")
        self.assertEqual(aliases["Jude"],"Jude")
        self.assertTrue(proof["comparison_uses_exact_existing_66_book_registry_without_edits"])
        self.assertEqual(len(proof["canonical_usfm_osis_66_config_sha256"]),64)

    def test_different_source_div1_title_points_to_different_book_than_original_scripcom(self):
        source,shared=fixtures()
        report=original_div1_english_alias_vs_declared_osis(source,shared)
        self.assertEqual(report["source_div1_with_exactly_one_declared_book_code_title_compared"],2)
        self.assertEqual(report["canonical_english_alias_heading_conflicts_found"],1)
        self.assertEqual(report["source_original_div1_title_vs_canonical_english_alias_classes"],{
            "original_title_contains_english_alias_matching_claimed_book_code":1,
            "original_title_contains_english_alias_for_different_book_code":1,
        })
        group=report["focused_shared_stock_raw_original_source_book_title_alias_checks"][0]
        self.assertEqual(group["original_source_units_checked"],2)
        members=group["source_line_original_full_hash_and_title_alias_class_members"]
        self.assertEqual([m["original_div1_document_ordinal"] for m in members],[1,2])
        self.assertEqual([m["english_title_alias_vs_actual_original_osis_claim_class"] for m in members],[
            "original_title_contains_english_alias_matching_claimed_book_code",
            "original_title_contains_english_alias_for_different_book_code",
        ])
        self.assertNotEqual(
            members[1]["unambiguous_canonical_english_title_candidate_osis_SHA256"],
            members[1]["original_scripCom_osis_book_code_SHA256"]
        )
        output=json.dumps(report)
        self.assertNotIn("Judges",output)
        self.assertNotIn("Jude",output)
        self.assertNotIn("Old source section",output)
        self.assertNotIn("Bible:Judg",output)
        self.assertFalse(report["book_codes_or_original_source_titles_exposed"])

    def test_jude_and_judges_remain_distinct_original_source_title_witnesses(self):
        aliases,_=read_existing_66_book_english_aliases()
        # Exact original titles are evidence; they do not amend any scripCom.
        self.assertEqual(
            _classify("Jude","Judg",aliases),
            ("original_title_exact_english_alias_points_to_different_book_code","Jude",1),
        )
        self.assertEqual(
            _classify("Judges","Judg",aliases),
            ("original_title_exact_english_alias_matches_claimed_book_code","Judg",1),
        )
        self.assertEqual(
            _classify("Jude","Jude",aliases),
            ("original_title_exact_english_alias_matches_claimed_book_code","Jude",1),
        )

    def test_ambiguous_english_book_heading_is_not_silently_approved(self):
        alias,_=read_existing_66_book_english_aliases()
        category,code,amount=_classify("First Letter: 1 John","1John",alias)
        # Candidate "John" and "1 John" are different canonical book labels.
        self.assertEqual(category,"original_title_matches_multiple_canonical_aliases_unreviewed")
        self.assertIsNone(code)
        self.assertGreaterEqual(amount,2)

    def test_unknown_heading_can_stay_unreviewed_without_canonical_assumption(self):
        aliases,_=read_existing_66_book_english_aliases()
        category,code,count=_classify("Editorial Remarks on the Scriptures","Judg",aliases)
        self.assertEqual(category,"original_title_no_canonical_english_alias_found_unreviewed")
        self.assertIsNone(code)
        self.assertEqual(count,0)

    def test_original_source_div1_title_sha_must_be_valid(self):
        source,shared=fixtures()
        source["Judg.1.1"][1]["private_original_div1_heading_text"]="Changed"
        with self.assertRaises(PilotError):
            original_div1_english_alias_vs_declared_osis(source,shared)


if __name__=="__main__":
    unittest.main()
