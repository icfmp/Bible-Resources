"""No-network, source-preserving title-vs-OSIS collision safeguards."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_source_identity_lexical_gate import classify_lexical_source_identity
from pilot_preflight import PilotError


def h(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def original(line: int, title: str) -> dict:
    return {
        "original_source_line": line,
        "original_full_reference_sha256": h(f"source reference {line}"),
        "original_text_sha256": h(f"source body {line}"),
        "private_original_enclosing_div1_document_ordinal": line,
        "private_original_total_div1_in_document": 80,
        "private_original_div1_heading_text": title,
        "private_original_div1_heading_sha256": h(title),
    }


def case(item: dict) -> dict:
    return {
        "original_source_line": item["original_source_line"],
        "original_full_reference_sha256": item["original_full_reference_sha256"],
        "original_body_sha256": item["original_text_sha256"],
        "stock_raw_sha256": h("different stock body " + str(item["original_source_line"])),
        "exact_plain_word_alignment": {
            "original_plain_words_not_matched_in_exact_order": 6
        },
    }


class SourceLexicalIdentityGuardTests(unittest.TestCase):
    def test_cross_book_original_title_claim_is_quarantined_without_rewriting(self):
        disputed = original(66, "Jude")
        matched = original(8, "Judges")
        source = {"Judg.1.1": [disputed, matched]}
        with patch(
            "commentary_source_identity_lexical_gate.read_existing_66_book_english_aliases",
            return_value=({"Judg": "Judges", "Jude": "Jude"}, {
                "comparison_uses_exact_existing_66_book_registry_without_edits": True,
            }),
        ):
            report = classify_lexical_source_identity(
                source, [case(disputed), case(matched)]
            )
        self.assertEqual(report["original_source_compiled_lexical_attention_cases_checked"], 2)
        counts = report["original_div1_book_identity_gate_classes"]
        self.assertEqual(counts["quarantine_original_book_title_vs_osis_marker_conflict"], 1)
        self.assertEqual(counts["meaningful_separate_editions_lexical_review_still_required"], 1)
        self.assertTrue(report["cross_book_join_is_not_evidence_of_missing_stock_prose"])
        self.assertFalse(report["editorial_decisions_approved"])
        self.assertFalse(report["published"])
        self.assertNotIn("Jude", str(report))
        self.assertNotIn("Judg", str(report))

    def test_unknown_original_heading_is_never_implicitly_assigned_to_stock_book(self):
        unreviewed = original(12, "Chapter Notes")
        with patch(
            "commentary_source_identity_lexical_gate.read_existing_66_book_english_aliases",
            return_value=({"Gen": "Genesis"}, {}),
        ):
            result = classify_lexical_source_identity(
                {"Gen.1.1": [unreviewed]}, [case(unreviewed)]
            )
        self.assertEqual(result["original_div1_book_identity_gate_classes"], {
            "ambiguous_original_source_book_identity_manual_review": 1
        })

    def test_rejects_wrong_source_line_reference_or_body_hash_join(self):
        item = original(1, "Genesis")
        with patch(
            "commentary_source_identity_lexical_gate.read_existing_66_book_english_aliases",
            return_value=({"Gen": "Genesis"}, {}),
        ):
            bad = case(item)
            bad["original_body_sha256"] = h("some other original body")
            with self.assertRaisesRegex(PilotError, "unique original source"):
                classify_lexical_source_identity({"Gen.1.1":[item]}, [bad])
            duplicate = [case(item), case(item)]
            with self.assertRaisesRegex(PilotError, "unique original source"):
                classify_lexical_source_identity({"Gen.1.1":[item]}, duplicate)

    def test_fails_closed_when_original_source_heading_was_changed(self):
        unit = original(1, "Genesis")
        unit["private_original_div1_heading_text"] = "Jude"
        with patch(
            "commentary_source_identity_lexical_gate.read_existing_66_book_english_aliases",
            return_value=({"Gen":"Genesis","Jude":"Jude"}, {}),
        ):
            with self.assertRaisesRegex(PilotError, "SHA-attested"):
                classify_lexical_source_identity({"Gen.1.1":[unit]}, [case(unit)])

    def test_no_lexical_difference_can_claim_authorial_parity_without_review(self):
        item = original(1, "Genesis")
        bad = case(item)
        bad["exact_plain_word_alignment"][
            "original_plain_words_not_matched_in_exact_order"
        ] = 0
        with patch(
            "commentary_source_identity_lexical_gate.read_existing_66_book_english_aliases",
            return_value=({"Gen":"Genesis"}, {}),
        ):
            with self.assertRaisesRegex(PilotError, "exact-matching"):
                classify_lexical_source_identity({"Gen.1.1":[item]}, [bad])


if __name__ == "__main__":
    unittest.main()
