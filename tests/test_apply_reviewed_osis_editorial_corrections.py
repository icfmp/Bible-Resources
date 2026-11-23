"""Fail-closed reviewed OSIS editorial-overlay tests (synthetic, unpublished)."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_reviewed_osis_editorial_corrections import (  # noqa: E402
    apply_plan, ReviewError,
)

NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def fixture():
    return (
        f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
        '<chapter osisID="Gen.1">'
        '<verse osisID="Gen.1.1">First text</verse>'
        '<verse osisID="Gen.1.2">Second text</verse>'
        '<note type="crossReference" n="a">'
        '<reference type="annotateRef" subType="x-origin">1.1</reference>'
        '<reference>Ge 1:99. Ge 1:2.</reference>'
        '</note><list><item>'
        '<reference subType="x-introduction">1:1-99</reference> '
        '<reference subType="x-introduction">1:1-2, et</reference>'
        '</item></list></chapter></div></osisText></osis>'
    ).encode("utf-8")


def approved_plan(raw):
    return {
        "schema_version": 1,
        "status": "owner_authorized_isolated_editorial_candidate",
        "approved_for_candidate_only": True,
        "publication_or_master_replacement_approved": False,
        "input_sha256": sha256(raw).hexdigest(),
        "original_usfx_zip_sha256": "0" * 64,
        "edits": [
            {"type": "cross_reference_fragment", "reference_index": 1,
             "book": "Gen", "source_origin": "1.1", "source_note_caller": "a",
             "original_label": "Ge 1:99. Ge 1:2.",
             "old_fragment": "Ge 1:99", "new_fragment": "Ge 1:1",
             "new_label": "Ge 1:1. Ge 1:2.",
             "printed_target_osis": "Gen.1.1",
             "original_printed_scan_page": 5, "printed_note_callout": "a",
             "printed_fragment": "Ge. 1. 1.",
             "editorial_decision":
                 "source_specific_fragment_repaired_in_separate_candidate"},
            {"type": "introduction_text_correction", "reference_index": 2,
             "book": "Gen", "original_label": "1:1-99", "new_label": "1:1-2",
             "evidence_url": "https://example.org/original-title",
             "editorial_decision":
                 "correct_source_heading_typo_in_separate_candidate",
             "segments": [{"literal": "1:1-2",
                           "osis_ref": "Gen.1.1-Gen.1.2"}]},
            {"type": "introduction_link_split", "reference_index": 3,
             "book": "Gen", "original_label": "1:1-2, et",
             "new_label": "1:1-2, et",
             "segments": [{"literal": "1:1-2",
                           "osis_ref": "Gen.1.1-Gen.1.2"}]},
        ],
    }


class ReviewedEditorialOverlayTests(unittest.TestCase):
    def test_reviewed_changes_are_exact_and_original_bytes_immutable(self):
        raw = fixture()
        result, receipt = apply_plan(
            raw, approved_plan(raw), {"Ge": "Gen"}, "0" * 64)
        self.assertEqual(receipt["edits_executed"], 3)
        self.assertEqual(receipt["reference_fragment_edits"], 1)
        self.assertEqual(receipt["intro_source_text_corrections"], 1)
        self.assertEqual(receipt["intro_structural_link_splits"], 1)
        self.assertTrue(receipt["verse_order_and_index_preserved"])
        self.assertFalse(receipt["publication_approved"])
        self.assertIn(
            b'<reference osisRef="Gen.1.1 Gen.1.2">Ge 1:1. Ge 1:2.</reference>', result)
        self.assertIn(
            b'<reference subType="x-introduction" osisRef="Gen.1.1-Gen.1.2">1:1-2</reference>, et', result)
        self.assertIn(b'First text', result)
        self.assertIn(b'Ge 1:99.', raw)
        self.assertNotIn(b'Ge 1:99.', result)
        self.assertEqual(len(list(etree.fromstring(result).iter(
            "{"+NS+"}"+"note"))), 1)

    def test_rejects_stale_source_and_unapproved_publication(self):
        raw = fixture()
        plan = approved_plan(raw)
        for key, bad in (("input_sha256", "1" * 64),
                         ("approved_for_candidate_only", False),
                         ("publication_or_master_replacement_approved", True)):
            with self.subTest(key=key):
                changed = deepcopy(plan)
                changed[key] = bad
                with self.assertRaises(ReviewError):
                    apply_plan(raw, changed, {"Ge": "Gen"}, "0" * 64)
        with self.assertRaises(ReviewError):
            apply_plan(raw, plan, {"Ge": "Gen"}, "1" * 64)

    def test_rejects_unattested_target_missing_original_anchor_and_duplicate(self):
        raw = fixture()
        plan = approved_plan(raw)
        for key, val in (("new_fragment", "Ge 1:100"),
                         ("source_origin", "2.1"),
                         ("source_note_caller", "b"),
                         ("original_label", "Ge 1:33. Ge 1:2.")):
            with self.subTest(key=key):
                changed = deepcopy(plan)
                changed["edits"][0][key] = val
                with self.assertRaises(ReviewError):
                    apply_plan(raw, changed, {"Ge": "Gen"}, "0" * 64)
        changed = deepcopy(plan)
        changed["edits"].append(deepcopy(changed["edits"][0]))
        with self.assertRaises(ReviewError):
            apply_plan(raw, changed, {"Ge": "Gen"}, "0" * 64)

    def test_rejects_unreviewed_intro_prose_changes_or_unknown_range(self):
        raw = fixture()
        plan = approved_plan(raw)
        for key, val in (("new_label", "1:1-2 et"),
                         ("original_label", "1:1-2 et")):
            changed = deepcopy(plan)
            changed["edits"][2][key] = val
            with self.assertRaises(ReviewError):
                apply_plan(raw, changed, {"Ge": "Gen"}, "0" * 64)
        changed = deepcopy(plan)
        changed["edits"][2]["segments"][0]["osis_ref"] = "Gen.1.1-Gen.1.99"
        with self.assertRaises(ReviewError):
            apply_plan(raw, changed, {"Ge": "Gen"}, "0" * 64)

    def test_real_review_plan_is_still_only_an_unpublished_candidate(self):
        plan = json.loads((ROOT /
            "sources/cleaned/bibles/fr/lsg-1910/editorial/"
            "REVIEWED_REFERENCE_AND_INTRO_OVERLAY_2026-11-23.json").read_text(
                encoding="utf-8"))
        self.assertFalse(plan["publication_or_master_replacement_approved"])
        self.assertTrue(plan["approved_for_candidate_only"])
        self.assertEqual(len(plan["edits"]), 15)
        kinds = [e["type"] for e in plan["edits"]]
        self.assertEqual(kinds.count("cross_reference_fragment"), 12)
        self.assertEqual(kinds.count("introduction_text_correction"), 1)
        self.assertEqual(kinds.count("introduction_link_split"), 2)
        self.assertEqual(len({e["reference_index"] for e in plan["edits"]}), 15)


if __name__ == "__main__":
    unittest.main()
