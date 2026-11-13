#!/usr/bin/env python3
"""Bounded private chapter-paragraph anchor and leftover-word diagnostics.

Original source paragraph and compiled stock entry are different witnesses.
A shared word run in a stock verse entry is not approved authorial equivalence.
No text, punctuation, raw XML, book/reference names or word tokens are emitted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from commentary_chapter_paragraph_overlap import (
    MAX_SOURCE_P_WORDS, MAX_STOCK_ENTRY_WORDS,
    SOURCE_WORD_RE, longest_common_contiguous_word_run,
)
from pilot_preflight import PilotError
from commentary_chapter_ref_labels import link_label_location

MAX_SAFE_SOURCE_P = 1000
MAX_REVIEW_CASES = 12
HEX_SHA = re.compile(r"[0-9a-f]{64}")


def anchor_window(source_words: list[str], stock_words: list[str], run: int) -> tuple[int, int, int]:
    """Earliest actual exact-token start positions and count of stock windows."""
    if run < 1 or run > min(len(source_words), len(stock_words)):
        raise PilotError("Original-to-stock paragraph anchor length is invalid")
    lookup = {}
    for i in range(len(source_words) - run + 1):
        lookup.setdefault(tuple(source_words[i:i+run]), i)
    first = None
    occurrences = 0
    for j in range(len(stock_words) - run + 1):
        key = tuple(stock_words[j:j+run])
        i = lookup.get(key)
        if i is not None:
            occurrences += 1
            if first is None:
                first = (i, j)
    if first is None:
        raise PilotError("Longest source-to-stock word anchor was not actually present")
    return first[0], first[1], occurrences


class ChapterParagraphBoundaryProbe:
    """Scan the SAME chapter's numbered native stock keys; preserve scope."""

    def __init__(self, source: dict):
        self.units_by_chapter = defaultdict(list)
        self.all_units = {}
        for chapter, items in source.items():
            for item in items:
                if item["tag"] != "p":
                    continue
                words = SOURCE_WORD_RE.findall(item["text"])
                if not words or len(words) > MAX_SOURCE_P_WORDS:
                    raise PilotError("Chapter source p text is outside reviewed word bound")
                ref = item["source_reference_sha256"]
                txt = item["source_sibling_sha256"]
                if (not HEX_SHA.fullmatch(ref) or not HEX_SHA.fullmatch(txt)
                        or not isinstance(item["source_line"], int)):
                    raise PilotError("Unpinned chapter paragraph source identity")
                identity = (ref, txt)
                if identity in self.all_units:
                    raise PilotError("Duplicate source paragraph hash identity is ambiguous")
                unit = {
                    "chapter": chapter,
                    "source_line": item["source_line"],
                    "ref_sha": ref, "text_sha": txt,
                    "words": words,
                    "neighbor_tag_counts": item["source_sibling_direct_child_tag_counts"],
                    "neighbor_next_tag": item["source_sibling_next_tag"],
                    "neighbor_parent_tag": item["source_sibling_parent_tag"],
                    "private_original_scripRef_labels": item["private_source_scripRef_labels"],
                    "selected_scripRef_label_result": None,
                    "best": 0, "best_keys": 0, "best_key_sha256": None,
                    "source_anchor_start": None, "stock_anchor_start": None,
                    "stock_anchor_occurrences_at_selected_key": 0,
                    "source_words_also_present_in_selected_stock_multiset": 0,
                }
                self.all_units[identity] = unit
                self.units_by_chapter[chapter].append(unit)
        if not self.all_units or len(self.all_units) > MAX_SAFE_SOURCE_P:
            raise PilotError("No source chapter paragraphs or too many source p units")
        self.stock_slots = 0
        self.stock_xml_parse_errors = 0

    def observe(self, kind: str, key: str, raw: bytes, decode_raw) -> None:
        if kind != "K":
            return
        chapter = key.rsplit(".", 1)[0]
        units = self.units_by_chapter.get(chapter)
        if not units:
            return
        self.stock_slots += 1
        native = decode_raw(raw)
        if native is None:
            self.stock_xml_parse_errors += 1
            return
        stock_words = SOURCE_WORD_RE.findall(native)
        if len(stock_words) > MAX_STOCK_ENTRY_WORDS:
            raise PilotError("Source chapter SWORD raw entry exceeds word bound")
        stock_word_occurrences = Counter(stock_words)
        for unit in units:
            original_words = unit["words"]
            n = longest_common_contiguous_word_run(original_words, stock_words)
            if n < unit["best"]:
                continue
            if n == unit["best"]:
                if n:
                    unit["best_keys"] += 1
                continue
            unit["best"] = n
            unit["best_keys"] = 1
            unit["best_key_sha256"] = sha256(key.encode("ascii")).hexdigest()
            unit["selected_scripRef_label_result"] = link_label_location(
                unit["private_original_scripRef_labels"], raw
            )
            start, stock_start, occurrences = anchor_window(original_words, stock_words, n)
            unit["source_anchor_start"] = start
            unit["stock_anchor_start"] = stock_start
            unit["stock_anchor_occurrences_at_selected_key"] = occurrences
            unit["source_words_also_present_in_selected_stock_multiset"] = sum(
                (Counter(original_words) & stock_word_occurrences).values()
            )

    def report(self, previous_alternative: dict, previous_partial: dict) -> dict:
        cases = [r for r in previous_alternative["bounded_originally_unlocated_line_hash_only_cases"]
                 if r["alternative_stock_location_class"] == "not_found_in_other_same_book_stock_slots"
                 and r["original_neighbor_tag"] == "p"]
        prior = previous_partial["unlocated_original_p_line_hash_only_best_contiguous_word_spans"]
        if len(cases) > MAX_REVIEW_CASES or len(prior) != len(cases):
            raise PilotError("Previously unresolved chapter p paragraphs were not fully inventoried")
        expected = {
            (r["original_reference_sha256"], r["original_neighbor_text_sha256"]):
            r for r in prior
        }
        receipt = []
        for case in cases:
            identity = (case["original_reference_sha256"], case["original_neighbor_text_sha256"])
            unit = self.all_units.get(identity)
            baseline = expected.get(identity)
            if unit is None or baseline is None or unit["source_line"] != case["source_line"]:
                raise PilotError("Original previously unlocated chapter paragraph identity changed")
            observed_best = baseline["largest_identical_case_word_span_by_slot_scope"]["same_chapter_numbered"]
            if unit["best"] != observed_best or observed_best < 1:
                raise PilotError("Independent longest original chapter word-run scanner disagrees")
            words = unit["words"]
            start = unit["source_anchor_start"]
            length = unit["best"]
            if start is None or start < 0 or start + length > len(words):
                raise PilotError("Source paragraph word-run alignment invalid")
            if unit["source_words_also_present_in_selected_stock_multiset"] < length:
                raise PilotError("Stock shared word multiset shorter than exact lexical run")
            if unit["best_keys"] > self.stock_slots or not HEX_SHA.fullmatch(unit["best_key_sha256"] or ""):
                raise PilotError("Stock best-match key evidence missing")
            receipt.append({
                "source_line": unit["source_line"],
                "source_reference_sha256": unit["ref_sha"],
                "original_paragraph_sha256": unit["text_sha"],
                "original_word_tokens": len(words),
                "best_same_chapter_contiguous_word_run": length,
                "original_tokens_before_shared_run": start,
                "original_tokens_after_shared_run": len(words) - start - length,
                "selected_stock_run_start_token_offset": unit["stock_anchor_start"],
                "stock_key_slots_tied_for_best_word_run": unit["best_keys"],
                "matching_native_key_sha256": unit["best_key_sha256"],
                "repeated_identical_word_run_windows_in_selected_stock_key":
                    unit["stock_anchor_occurrences_at_selected_key"],
                "original_word_token_multiset_occurrences_in_selected_stock_key":
                    unit["source_words_also_present_in_selected_stock_multiset"],
                "source_paragraph_direct_child_element_counts":
                    unit["neighbor_tag_counts"],
                "original_next_sibling_tag": unit["neighbor_next_tag"],
                "original_parent_element_tag": unit["neighbor_parent_tag"],
                "selected_stock_scripRef_label_diagnostics":
                    unit["selected_scripRef_label_result"],
            })
        if len(receipt) != len(cases):
            raise PilotError("Original unresolved chapter p paragraph boundary report incomplete")
        return {
            "original_chapter_adjacent_p_total": len(self.all_units),
            "previously_unlocated_p_examined": len(receipt),
            "same_chapter_numbered_native_keys_scanned": self.stock_slots,
            "stock_strict_xml_parse_failures": self.stock_xml_parse_errors,
            "source_paragraph_word_run_boundary_cases": receipt,
            "selected_native_key_is_lexical_witness_not_authored_paragraph_proof": True,
            "word_multiset_occurrence_does_not_prove_original_word_order": True,
            "no_original_words_or_stock_xml_or_unhashed_references_reported": True,
            "source_text_annotation_and_stock_binary_modified": False,
            "full_original_to_stock_authorial_paragraph_parity_proven": False,
        }
