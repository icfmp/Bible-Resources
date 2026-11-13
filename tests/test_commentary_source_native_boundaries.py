"""Original ThML marker neighborhood versus genuine native occupied raw K-run edges."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_private_text_compare import _original_source_markers
from commentary_source_native_boundaries import (
    NativeRawRunBoundaryInventory, original_marker_boundary,
)
from pilot_preflight import PilotError


def original_fixture():
    xml=(
        b'<?xml version="1.0"?><ThML><ThML.body><div1><div2>'
        b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.3"/>'
        b'<div><p>First original plain paragraph.</p></div>'
        b'<scripCom osisRef="Bible:Gen.1.4"/>'
        b'<div><p>Second original plain paragraph.</p></div>'
        b'<scripCom osisRef="Bible:Gen.2"/>'
        b'<h2>Chapter heading</h2>'
        b'</div2></div1></ThML.body></ThML>'+b" "*1100
    )
    source,_proof=_original_source_markers(xml)
    return source


def review_case(source,key="Gen.1.1",raw=b"<div>Raw shared</div>"):
    unit=source[key][0]
    return {
        "original_source_line":unit["original_source_line"],
        "original_full_reference_sha256":unit["original_full_reference_sha256"],
        "original_body_sha256":unit["original_text_sha256"],
        "stock_raw_sha256":sha256(raw).hexdigest(),
    }


class SourceVersusNativeRunBoundaryTests(unittest.TestCase):
    def test_source_sibling_neighbors_preserve_actual_original_marker_order(self):
        source=original_fixture()
        first=source["Gen.1.1"][0]["private_source_marker_boundary"]
        self.assertEqual(first["original_annotation_reference_kind"],
                         "work_qualified_same_book_verse_range")
        self.assertTrue(first["original_range_ends_in_same_chapter"])
        self.assertEqual(first["source_marker_parent_tag"],"div2")
        self.assertEqual(first["source_body_direct_child_tag_counts"],{"p":1})
        self.assertEqual(first["preceding_sibling_tag_before_source_marker"],"_none")
        self.assertEqual(first["immediately_following_sibling_after_source_body_tag"],"scripCom")
        self.assertEqual(first["immediately_following_original_marker_reference_kind"],
                         "work_qualified_verse")
        self.assertTrue(first["immediately_following_marker_same_chapter"])
        second=source["Gen.1.4"][0]["private_source_marker_boundary"]
        self.assertTrue(second["preceding_sibling_was_div_preceded_by_scripCom"])
        self.assertEqual(second["immediately_following_original_marker_reference_kind"],
                         "work_qualified_chapter")
        self.assertFalse(second["original_range_ends_in_same_chapter"])
        self.assertFalse(second["immediately_following_marker_same_chapter"])
        self.assertNotIn("Gen.2",json.dumps(second))

    def test_native_identical_raw_occupied_key_run_has_bounded_true_endpoints(self):
        source=original_fixture()
        raw=b"<div>Raw shared</div>"
        other=b"<div>Different original compiled content</div>"
        ledger=NativeRawRunBoundaryInventory()
        for k,p in [
            ("Gen.1.1",raw),("Gen.1.2",raw),("Gen.1.3",raw),
            ("Gen.1.4",other),("Gen.2.1",raw),("Gen.2.3",raw),
            ("Gen.2.4",other),
        ]:
            ledger.observe("K",k,p)
        ledger.observe("I","Gen.1.0",b"Chapter introduction")
        out=ledger.report(source,[review_case(source)])
        record=out["original_source_marker_native_run_sha256_and_metadata_only_cases"][0]
        self.assertEqual(out["actual_native_K_occupied_keys_in_full_corpus"],7)
        self.assertEqual(out["actual_native_I_intro_keys_in_full_corpus"],1)
        self.assertEqual(record["native_K_occurrences_with_same_raw_in_source_book"],5)
        self.assertEqual(record["native_K_consecutive_occupied_key_run_length"],3)
        self.assertEqual(record["native_K_run_consecutive_occupied_keys_before_selected"],0)
        self.assertEqual(record["native_K_run_consecutive_occupied_keys_after_selected"],2)
        self.assertEqual(record["native_K_separate_identical_raw_runs_in_same_book"],2)
        self.assertEqual(record["native_K_run_other_identical_raw_keys_outside_selected_run"],2)
        self.assertEqual(record["native_K_run_key_count_in_same_selected_chapter"],3)
        self.assertFalse(record["native_K_run_has_keys_in_another_chapter_same_book"])
        self.assertEqual(len(record["native_run_last_key_sha256"]),64)
        self.assertNotIn("Gen.1.3",json.dumps(record))
        self.assertNotIn("Raw shared",json.dumps(record))

    def test_repeated_native_bytes_across_chapter_boundary_are_not_authorial_mapping(self):
        source=original_fixture()
        raw=b"<div>Raw shared</div>"
        ledger=NativeRawRunBoundaryInventory()
        ledger.observe("K","Gen.1.1",raw)
        ledger.observe("K","Gen.1.2",raw)
        ledger.observe("K","Gen.2.1",raw)
        report=ledger.report(source,[review_case(source)])
        unit=report["original_source_marker_native_run_sha256_and_metadata_only_cases"][0]
        self.assertTrue(unit["native_K_run_has_keys_in_another_chapter_same_book"])
        self.assertEqual(unit["native_K_run_key_count_in_same_selected_chapter"],2)
        self.assertTrue(report["native_K_run_is_only_consecutive_occupied_keys_not_numeric_verses"])

    def test_original_source_hash_identity_and_compiled_selected_raw_digest_fail_closed(self):
        source=original_fixture()
        ledger=NativeRawRunBoundaryInventory()
        ledger.observe("K","Gen.1.1",b"<div>Raw shared</div>")
        case=review_case(source)
        with self.assertRaises(PilotError):
            ledger.report(source,[dict(case,original_body_sha256="0"*64)])
        with self.assertRaises(PilotError):
            ledger.report(source,[dict(case,stock_raw_sha256="0"*64)])

    def test_native_raw_run_excludes_duplicate_intro_keys_from_K_boundary(self):
        source=original_fixture()
        stock=b"<div>Raw shared</div>"
        ledger=NativeRawRunBoundaryInventory()
        ledger.observe("I","Gen.1.0",stock)
        ledger.observe("K","Gen.1.1",stock)
        result=ledger.report(source,[review_case(source)])
        row=result["original_source_marker_native_run_sha256_and_metadata_only_cases"][0]
        self.assertEqual(row["native_K_occurrences_with_same_raw_in_source_book"],1)
        self.assertEqual(row["native_K_consecutive_occupied_key_run_length"],1)
        self.assertEqual(row["native_K_separate_identical_raw_runs_in_same_book"],1)

    def test_source_verse_range_grammar_unknown_is_not_guessed(self):
        from lxml import etree
        root=etree.fromstring(
            b'<d><scripCom osisRef="Bible:Gen.1.1"/>'
            b'<div><p>Actual text</p></div></d>'
        )
        marker=root[0]
        with self.assertRaises(PilotError):
            original_marker_boundary(marker,root[1],"Bible:Gen.1.2","Gen.1.2")


if __name__=="__main__":
    unittest.main()
