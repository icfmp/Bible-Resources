#!/usr/bin/env python3
"""Private bounded chapter-adjacent paragraph word-span research.

Only original ThML p siblings immediately after explicit chapter scripCom
markers are candidates. A longest shared contiguous token span is NOT a
quotation, paragraph, reference, authorial edition, or content parity test.
No source text, token, SWORD XML or unhashed reference leaves private memory.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from pilot_preflight import PilotError

MAX_SOURCE_P_WORDS = 512
MAX_STOCK_ENTRY_WORDS = 50000
MAX_PER_MARKER_HASH_RECEIPTS = 12
SOURCE_WORD_RE = re.compile(r"\w+")


def longest_common_contiguous_word_run(source: list[str], stock: list[str]) -> int:
    """Exact token-window intersection, binary search; no heuristic similarity."""
    if not source or not stock:
        return 0
    if len(source) > MAX_SOURCE_P_WORDS or len(stock) > MAX_STOCK_ENTRY_WORDS:
        raise PilotError("Unreviewed chapter/stock word stream exceeds comparison bound")
    # Any shared length-n run implies shorter shared runs. Never mask edits
    # using fuzzy matching, stemming, loose punctuation or inferred tokens.
    low, high = 0, min(len(source), len(stock))
    while low < high:
        n = (low + high + 1) // 2
        original_runs = {
            tuple(source[i:i+n]) for i in range(len(source)-n+1)
        }
        found = any(
            tuple(stock[i:i+n]) in original_runs
            for i in range(len(stock)-n+1)
        )
        if found:
            low = n
        else:
            high = n-1
    return low


class OriginalChapterParagraphSpanProbe:
    """Check actual same-book native K/I content for every explicit source p."""

    SCOPES = (
        "same_chapter_numbered",
        "other_chapter_numbered",
        "same_chapter_intro",
        "other_intro",
    )

    def __init__(self, source: dict):
        self.by_book = defaultdict(list)
        self.by_hash = {}
        for chapter, items in source.items():
            book = chapter.split(".", 1)[0]
            for item in items:
                if item["tag"] != "p":
                    continue
                words = SOURCE_WORD_RE.findall(item["text"])
                if not words or len(words) > MAX_SOURCE_P_WORDS:
                    raise PilotError("Original chapter-adjacent paragraph is not within review bounds")
                ref_sha = item.get("source_reference_sha256")
                txt_sha = item.get("source_sibling_sha256")
                if not (isinstance(ref_sha, str) and re.fullmatch("[0-9a-f]{64}", ref_sha)
                        and isinstance(txt_sha, str) and re.fullmatch("[0-9a-f]{64}", txt_sha)):
                    raise PilotError("Original chapter paragraph has no independently source-bound identity")
                ident = (ref_sha, txt_sha)
                if ident in self.by_hash:
                    raise PilotError("Duplicate original chapter paragraph identity requires source review")
                unit = {
                    "chapter":chapter, "source_line":item["source_line"],
                    "source_reference_sha256":ref_sha,
                    "source_sibling_sha256":txt_sha,
                    "word_count":len(words),
                    "tokens":words,
                    "casefolded_tokens":[word.casefold() for word in words],
                    "best_exact":{scope:0 for scope in self.SCOPES},
                    "best_casefold":{scope:0 for scope in self.SCOPES},
                    "best_key_sha":{},
                }
                self.by_book[book].append(unit)
                self.by_hash[ident] = unit
        if not self.by_hash or len(self.by_hash)>20000:
            raise PilotError("No reviewable source chapter-adjacent p units")
        self.stock_scans_by_kind = Counter()
        self.strict_xml_failures_by_kind = Counter()

    @staticmethod
    def scope(unit:dict, kind:str, key:str, book:str)->str:
        if kind == "K":
            return ("same_chapter_numbered" if key.rsplit(".",1)[0]==unit["chapter"]
                    else "other_chapter_numbered")
        return ("same_chapter_intro" if key in (unit["chapter"],unit["chapter"]+".0")
                else "other_intro")

    def observe(self, kind:str, key:str, raw:bytes, decode_raw)->None:
        if kind not in {"K","I"}:
            return
        book = key.split(".",1)[0]
        units = self.by_book.get(book)
        if not units:
            return
        self.stock_scans_by_kind[kind] += 1
        value = decode_raw(raw)
        if value is None:
            self.strict_xml_failures_by_kind[kind] += 1
            return
        stock_words = SOURCE_WORD_RE.findall(value)
        if len(stock_words)>MAX_STOCK_ENTRY_WORDS:
            raise PilotError("Native stock entry text exceeds bounded paragraph span scanner")
        stock_casefold = [word.casefold() for word in stock_words]
        for unit in units:
            scope = self.scope(unit,kind,key,book)
            matched = longest_common_contiguous_word_run(unit["tokens"],stock_words)
            folded = longest_common_contiguous_word_run(unit["casefolded_tokens"],stock_casefold)
            if folded < matched or matched > unit["word_count"] or folded > unit["word_count"]:
                raise PilotError("Case-folded word span cannot be less than original exact-case span")
            if matched > unit["best_exact"][scope]:
                unit["best_exact"][scope] = matched
                unit["best_key_sha"][scope] = sha256(key.encode("ascii")).hexdigest()
            if folded > unit["best_casefold"][scope]:
                unit["best_casefold"][scope] = folded

    def report(self, previously_unlocated:dict)->dict:
        cases=previously_unlocated.get("bounded_originally_unlocated_line_hash_only_cases",[])
        total_unlocated=previously_unlocated.get("previously_not_found_in_same_chapter_numbered_slots",0)
        if not isinstance(cases,list) or len(cases)>MAX_PER_MARKER_HASH_RECEIPTS:
            raise PilotError("Previous source-line/hash receipt exceeded reviewed bound")
        reviewed=[]
        for item in cases:
            if item.get("alternative_stock_location_class") != "not_found_in_other_same_book_stock_slots":
                continue
            ident=(item.get("original_reference_sha256"), item.get("original_neighbor_text_sha256"))
            unit=self.by_hash.get(ident)
            if unit is None:
                # Non-paragraph source siblings may be explicitly outside scope.
                if item.get("original_neighbor_tag") != "p":
                    continue
                raise PilotError("Original chapter p paragraph disappeared from source-native inventory")
            if unit["source_line"]!=item["source_line"]:
                raise PilotError("Source line of original p paragraph no longer matches pinned evidence")
            reviewed.append({
                "source_line":unit["source_line"],
                "original_reference_sha256":unit["source_reference_sha256"],
                "original_neighbor_text_sha256":unit["source_sibling_sha256"],
                "original_word_token_count":unit["word_count"],
                "largest_identical_case_word_span_by_slot_scope":unit["best_exact"],
                "largest_casefolded_word_span_by_slot_scope":unit["best_casefold"],
                "longest_run_is_not_proof_of_exact_content_or_relocation":True,
            })
        if len(reviewed)>MAX_PER_MARKER_HASH_RECEIPTS or len(reviewed)>total_unlocated:
            raise PilotError("Private unlocated original paragraph report exceeded bound")
        stats=Counter()
        for unit in self.by_hash.values():
            stats["original_chapter_p_sibling_count"] += 1
            if max(unit["best_exact"].values()) == unit["word_count"]:
                stats["source_p_words_fully_contiguous_in_some_same_book_stock_slot"] += 1
            else:
                stats["source_p_words_not_fully_contiguous_in_same_book_stock_slots"] += 1
        if (stats["original_chapter_p_sibling_count"] !=
                stats["source_p_words_fully_contiguous_in_some_same_book_stock_slot"]+
                stats["source_p_words_not_fully_contiguous_in_same_book_stock_slots"]):
            raise PilotError("Original source p paragraph scan accounting diverged")
        return {
            "original_explicit_chapter_marker_adjacent_p_count":len(self.by_hash),
            "stock_original_same_book_K_and_I_slots_read_by_kind":dict(sorted(self.stock_scans_by_kind.items())),
            "strict_raw_xml_parse_failures_by_kind":dict(sorted(self.strict_xml_failures_by_kind.items())),
            "all_original_p_word_span_fidelity_classes":dict(sorted(stats.items())),
            "unlocated_original_p_line_hash_only_best_contiguous_word_spans":reviewed,
            "original_source_p_word_case_preserved_during_exact_case_comparison":True,
            "casefolded_scanner_is_diagnostic_only":True,
            "no_source_words_or_native_stock_text_exposed":True,
            "no_source_to_stock_full_chapter_or_edition_parity_proven":True,
        }
