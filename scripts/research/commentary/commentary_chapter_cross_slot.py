#!/usr/bin/env python3
"""Private same-book alternative-slot witness for source chapter-adjacent text.

A stage-4 *locator*, not proof of the authorial chapter body, valid section
mapping or any absent stock content. No source words, SWORD XML, or references
leave the temporary runner; only source line numbers and SHA-256 identifiers
are retained for bounded unresolved examples.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from commentary_text_delta import _contiguous_offset
from pilot_preflight import PilotError

MAX_PRIVATE_DIAGNOSTICS = 12


class ChapterNeighborSameBookAlternativeProbe:
    """Review stock K/I slots outside each source marker's own numbered chapter."""

    SCOPE_ORDER = (
        "same_chapter_intro",
        "other_chapter_numbered",
        "other_chapter_intro",
        "book_intro",
    )

    def __init__(self, original: dict):
        self.by_book = defaultdict(list)
        self.by_chapter = {}
        self.all_units = []
        for chapter, items in original.items():
            book = chapter.split(".", 1)[0]
            if "." not in chapter:
                raise PilotError("Original source chapter marker key not reviewed")
            units = []
            for item in items:
                text = item["text"]
                words = re.findall(r"\w+", text)
                if not text.strip() or not words:
                    raise PilotError("Original chapter neighbor has no searchable words")
                if (not isinstance(item.get("source_line"), int)
                        or item["source_line"] < 1
                        or not re.fullmatch(r"[a-f0-9]{64}", item.get("source_reference_sha256", ""))
                        or not re.fullmatch(r"[a-f0-9]{64}", item.get("source_sibling_sha256", ""))):
                    raise PilotError("Original neighbor line/hash witness not independently pinned")
                unit = {
                    "chapter": chapter, "source_line": item["source_line"],
                    "source_reference_sha256": item["source_reference_sha256"],
                    "source_sibling_sha256": item["source_sibling_sha256"],
                    "original_sibling_tag": item["tag"],
                    "original_unicode_characters": len(text),
                    "original_unicode_word_tokens": len(words),
                    "text": text, "words": words,
                    "scope_exact": set(), "scope_word": set(),
                    "matching_native_key_sha256": {},
                }
                self.by_book[book].append(unit)
                self.all_units.append(unit)
                units.append(unit)
            self.by_chapter[chapter] = units
        if not self.all_units or len(self.all_units) > 20000:
            raise PilotError("Original chapter sibling locator exceeds safe bounds")
        self.read_stock_slots_by_kind = Counter()
        self.strict_xml_errors = Counter()

    @staticmethod
    def _scope(unit: dict, kind: str, key: str, book: str) -> str | None:
        if kind == "K":
            chapter = key.rsplit(".", 1)[0]
            return None if chapter == unit["chapter"] else "other_chapter_numbered"
        if kind != "I":
            return None
        if key in (unit["chapter"], unit["chapter"] + ".0"):
            return "same_chapter_intro"
        if key == book or key in (book + ".0", book + ".0.0"):
            return "book_intro"
        return "other_chapter_intro"

    def observe(self, kind: str, key: str, raw: bytes, decode_raw) -> None:
        if kind not in {"K", "I"}:
            return
        book = key.split(".", 1)[0]
        items = self.by_book.get(book)
        if not items:
            return
        candidates = []
        for unit in items:
            scope = self._scope(unit, kind, key, book)
            # An exact match for one scope needs no extra repeated range slots.
            if scope and scope not in unit["scope_exact"]:
                candidates.append((unit, scope))
        if not candidates:
            return
        self.read_stock_slots_by_kind[kind] += 1
        native = decode_raw(raw)
        if native is None:
            self.strict_xml_errors[kind] += 1
            return
        stock_words = None
        for unit, scope in candidates:
            if unit["text"] in native:
                unit["scope_exact"].add(scope)
                unit["matching_native_key_sha256"].setdefault(scope, sha256(key.encode("ascii")).hexdigest())
            elif scope not in unit["scope_word"] and unit["words"][0] in native:
                if stock_words is None:
                    stock_words = re.findall(r"\w+", native)
                if _contiguous_offset(unit["words"], stock_words) is not None:
                    unit["scope_word"].add(scope)
                    unit["matching_native_key_sha256"].setdefault(scope, sha256(key.encode("ascii")).hexdigest())

    def report(self, same_chapter_probe) -> dict:
        results = Counter()
        original_unlocated = 0
        bounded = []
        if len(same_chapter_probe.marker_units) != len(self.all_units):
            raise PilotError("Original markers do not align to independent same-chapter scanner")
        for chapter, units in self.by_chapter.items():
            same = same_chapter_probe.units_by_chapter.get(chapter)
            if same is None or len(units) != len(same):
                raise PilotError("Source chapter marker membership diverged")
            for unit, same_unit in zip(units, same):
                if same_unit["exact"]:
                    results["previously_found_exact_in_same_chapter_numbered_slot"] += 1
                    continue
                if same_unit["words_found"]:
                    results["previously_found_words_in_same_chapter_numbered_slot"] += 1
                    continue
                original_unlocated += 1
                matched = None
                for scope in self.SCOPE_ORDER:
                    if scope in unit["scope_exact"]:
                        matched = scope + "_exact_unicode_containment"
                        break
                    if scope in unit["scope_word"]:
                        matched = scope + "_contiguous_unicode_word_tokens_only"
                        break
                category = matched or "not_found_in_other_same_book_stock_slots"
                results[category] += 1
                if len(bounded) < MAX_PRIVATE_DIAGNOSTICS:
                    bounded.append({
                        "source_line": unit["source_line"],
                        "original_reference_sha256": unit["source_reference_sha256"],
                        "original_neighbor_text_sha256": unit["source_sibling_sha256"],
                        "original_neighbor_tag": unit["original_sibling_tag"],
                        "original_unicode_characters": unit["original_unicode_characters"],
                        "original_unicode_word_token_count": unit["original_unicode_word_tokens"],
                        "alternative_stock_location_class": category,
                        "matching_native_key_sha256":
                            unit["matching_native_key_sha256"].get(category.split("_exact_unicode_containment")[0]
                                .split("_contiguous_unicode_word_tokens_only")[0])
                            if matched else None,
                    })
        if (sum(results.values()) != len(self.all_units)
                or original_unlocated + results[
                    "previously_found_exact_in_same_chapter_numbered_slot"
                ] + results["previously_found_words_in_same_chapter_numbered_slot"] != len(self.all_units)):
            raise PilotError("Source chapter alternative location accounting incomplete")
        return {
            "original_source_chapter_siblings_evaluated": len(self.all_units),
            "previously_not_found_in_same_chapter_numbered_slots": original_unlocated,
            "native_same_book_other_slot_reads_by_kind": dict(sorted(self.read_stock_slots_by_kind.items())),
            "stock_xml_strict_parse_failures_by_kind": dict(sorted(self.strict_xml_errors.items())),
            "source_sibling_locations_in_alternative_same_book_slots": dict(sorted(results.items())),
            "bounded_originally_unlocated_line_hash_only_cases": bounded,
            "per_marker_detail_cap": MAX_PRIVATE_DIAGNOSTICS,
            "unmatched_samples_may_be_truncated": original_unlocated > MAX_PRIVATE_DIAGNOSTICS,
            "same_book_other_slots_are_not_source_authorized_annotation_ranges": True,
            "repeated_stock_slot_payloads_do_not_prove_distinct_authorial_sections": True,
            "not_found_in_same_book_is_not_proof_missing_from_all_stock_entries": True,
            "authorial_edition_and_exact_text_structure_parity_proven": False,
            "original_words_or_compiled_xml_in_report": False,
        }
