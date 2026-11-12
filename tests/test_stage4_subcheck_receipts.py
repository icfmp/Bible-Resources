"""No-network tests: lossless metadata-only 4a–4d receipts and safe replay."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stage4_subcheck_receipts import (
    create_subcheck_receipts, verify_receipts_for_reuse, Stage4ReceiptError
)

SHA = "e" * 40
URL = "https://github.com/icfmp/Bible-Resources/actions/runs/1234567"


def manifest():
    return {
        "resource_id": "synthetic-test",
        "source": {"sha256": "a" * 64, "format": "USFX"},
        "sword": {"sha256": "b" * 64, "module_id": "fixture", "driver": "zText"},
        "schema_version": 1,
        "purpose": "research_only"
    }


def early_result():
    return {
        "status": "BLOCKED",
        "evidence": {
            "original_archives": {
                "source": {"sha256": "a" * 64},
                "sword": {"sha256": "b" * 64}
            },
            "whole_corpus_scan_performed": False,
            "fast_stock_note_preflight": {
                "fast_stock_reuse_disqualified": True,
                "sampled_exact_source_reference": "Gen.1.2",
                "independent_exact_native_verse_probes": 1,
                "original_numbered_note_inventory_count": 6340,
                "reason_code": "PRIVATE ORIGINAL NOTE WORDS MUST NOT LEAK"
            }
        }
    }


def full_result():
    result = early_result()
    result["status"] = "PARTIAL"
    evidence = result["evidence"]
    evidence["fast_stock_note_preflight"]["fast_stock_reuse_disqualified"] = False
    evidence["actual_native_raw_manifest_sha256"] = "c" * 64
    evidence["reference_index"] = {
        "comparison": {"exact_reference_key_parity": True}}
    evidence["maintext_scope_classification"] = {
        "all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding": True}
    evidence["maintext"] = {
        "classifications": {"matching_indexed_keys_checked": 31233},
        "source_native_body_boundary_word_position_screen": {
            "all_mapped_book_p_q_start_end_word_ordinals_match": True},
        "source_native_nonwhitespace_codepoint_boundary_screen": {
            "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match": True},
        "source_native_ordered_body_kind_screen": {
            "same_order_and_kind_in_every_mapped_book": True},
        "source_native_p_q_event_topology_diagnostic": {
            "status":"source_native_structural_topology_positions_equal_not_layout_certificate",
            "all_source_native_p_q_open_close_event_topology_match":True},
    }
    evidence["stock_reuse_preflight"] = {"proven_material_stock_loss": False}
    return result


def create(result):
    return create_subcheck_receipts(
        manifest(), result, commit_sha=SHA, run_url=URL)


class StageFourSubchecksTests(unittest.TestCase):
    def test_rejected_stock_yields_only_machine_blockers_without_full_scan(self):
        receipt = create(early_result())
        self.assertEqual(receipt["schema_version"], 1)
        self.assertTrue(receipt["verified_exact_original_archives_in_this_run"])
        self.assertEqual([receipt["subchecks"][s]["status"] for s in
                          ("4a","4b","4c","4d")], ["BLOCKED"] * 4)
        self.assertFalse(receipt["subchecks"]["4c"]["completed_full_native_corpus_scan"])
        self.assertEqual(receipt["subchecks"]["4d"]["counts"]["exact_native_verse_probes"], 1)
        self.assertEqual(receipt["subchecks"]["4d"]["sampled_original_reference_ids"],
                         ["Gen.1.2"])
        self.assertNotIn("PRIVATE ORIGINAL NOTE WORDS", json.dumps(receipt))
        self.assertNotIn("original_source_text", json.dumps(receipt))
        self.assertFalse(receipt["editorial_or_publication_approved"])
        self.assertEqual(verify_receipts_for_reuse(
            receipt, manifest(), commit_sha=SHA, subcheck="4d")["status"],
            "BLOCKED")

    def test_complete_index_but_other_machine_proofs_remain_narrow(self):
        receipt = create(full_result())
        self.assertEqual(receipt["subchecks"]["4a"]["status"], "DONE")
        self.assertEqual(receipt["subchecks"]["4b"]["status"], "PARTIAL")
        self.assertEqual(receipt["subchecks"]["4c"]["status"], "PARTIAL")
        self.assertEqual(receipt["subchecks"]["4d"]["status"], "REVIEW_REQUIRED")
        self.assertTrue(receipt["subchecks"]["4c"]["completed_full_native_corpus_scan"])
        self.assertEqual(verify_receipts_for_reuse(
            receipt, manifest(), commit_sha=SHA, subcheck="4c")[
            "machine_receipt_reused_only"], True)

    def test_shifted_closing_and_opening_block_even_when_counts_match(self):
        for field in ("all_mapped_book_p_q_start_end_word_ordinals_match",
                      "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match",
                      "same_order_and_kind_in_every_mapped_book"):
            with self.subTest(field=field):
                result = full_result()
                main = result["evidence"]["maintext"]
                for part in ("source_native_body_boundary_word_position_screen",
                             "source_native_nonwhitespace_codepoint_boundary_screen",
                             "source_native_ordered_body_kind_screen"):
                    if field in main[part]:
                        main[part][field] = False
                receipt = create(result)
                self.assertEqual(receipt["subchecks"]["4c"]["status"], "BLOCKED")
                self.assertIn(
                    "source_native_p_q_boundary_or_kind_difference",
                    receipt["subchecks"]["4c"]["unverified_machine_codes"])

    def test_proven_same_count_structural_displacement_blocks_4c(self):
        result=full_result()
        # Word/punctuation and kind-order flags can remain green in a stale
        # or incomplete previous audit; a new semantic event displacement
        # must independently block structure receipt 4c.
        result["evidence"]["maintext"][
            "source_native_p_q_event_topology_diagnostic"]={
                "status":"source_native_structural_topology_differs",
                "all_source_native_p_q_open_close_event_topology_match":False}
        receipt=create(result)
        self.assertEqual(receipt["subchecks"]["4c"]["status"],"BLOCKED")
        self.assertIn("source_native_p_q_boundary_or_kind_difference",
                      receipt["subchecks"]["4c"]["unverified_machine_codes"])

    def test_incomplete_source_acquisition_cannot_be_reused(self):
        result = full_result()
        result["evidence"]["original_archives"]["sword"]["sha256"] = "0" * 64
        receipt = create(result)
        self.assertFalse(receipt["verified_exact_original_archives_in_this_run"])
        self.assertTrue(all(r["status"] == "BLOCKED" for r in
                            receipt["subchecks"].values()))
        with self.assertRaises(Stage4ReceiptError):
            verify_receipts_for_reuse(
                receipt, manifest(), commit_sha=SHA, subcheck="4a")

    def test_any_changed_source_module_manifest_tool_or_dependency_blocks_reuse(self):
        receipt = create(full_result())
        cases = []
        changed = manifest()
        changed["source"]["sha256"] = "f" * 64
        cases.append((receipt, changed, SHA))
        changed = manifest()
        changed["sword"]["sha256"] = "f" * 64
        cases.append((receipt, changed, SHA))
        changed = manifest()
        changed["edition"] = "silent new publisher revision"
        cases.append((receipt, changed, SHA))
        cases.append((receipt, manifest(), "f" * 40))
        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["subchecks"]["4a"]["status"] = "BLOCKED"
        cases.append((changed_receipt, manifest(), SHA))
        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["subchecks"]["4c"]["dependencies"]["4b"] = "0" * 64
        changed_receipt["subchecks"]["4c"]["digest_sha256"] = "0" * 64
        cases.append((changed_receipt, manifest(), SHA))
        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["subchecks"]["4b"]["sampled_original_reference_ids"] = [
            "PRIVATE NOTE CONTENT"]
        cases.append((changed_receipt, manifest(), SHA))
        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["run_url"] = "https://evil.example/collect"
        cases.append((changed_receipt, manifest(), SHA))
        for i, (candidate, identity, sha) in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(Stage4ReceiptError):
                verify_receipts_for_reuse(
                    candidate, identity, commit_sha=sha, subcheck="4d")

    def test_unknown_original_verse_reference_not_leaked(self):
        result = early_result()
        result["evidence"]["fast_stock_note_preflight"][
            "sampled_exact_source_reference"] = "SECRET {text of a note}"
        with self.assertRaises(Stage4ReceiptError):
            create(result)

    def test_local_unpinned_receipts_are_not_reusable(self):
        receipt = create_subcheck_receipts(
            manifest(), full_result(), commit_sha="local-unpinned", run_url=None)
        with self.assertRaises(Stage4ReceiptError):
            verify_receipts_for_reuse(
                receipt, manifest(), commit_sha="local-unpinned", subcheck="4a")


if __name__ == "__main__":
    unittest.main()
