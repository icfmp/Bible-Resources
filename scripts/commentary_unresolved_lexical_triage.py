#!/usr/bin/env python3
"""PRIVATE, source-neutral triage of unmatched commentary word selections.

This module records only counts, categories and source-line/hash identifiers.
It does NOT render or repair any source, verse, quotation, punctuation, note,
or SWORD markup. Source/compiled digital edition identity is not assumed.
"""
from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
from hashlib import sha256
import re
import unicodedata

from lxml import etree

from commentary_stock_prefix_topology import unexplained_word_boundary_census
from pilot_preflight import PilotError

WORD = re.compile(r"\w+", flags=re.UNICODE)
MAX_WORDS_PER_STREAM = 100_000
MAX_ALIGNMENT_CELLS = 1_000_000
MAX_PRIVATE_CASES = 20
ALLOWED_STOCK_TAGS = {"reference", "title", "table", "p", "hi", "div",
                      "br", "q", "note", "span"}


def _middle_words(original: str, compiled: str) -> tuple[list[str], list[str], dict]:
    left, right = WORD.findall(original), WORD.findall(compiled)
    if not left or not right or left == right:
        raise PilotError("Lexical audit requires unequal nonempty original and stock word streams")
    if max(len(left), len(right)) > MAX_WORDS_PER_STREAM:
        raise PilotError("Original/stock word stream exceeds safe lexical audit bound")
    boundaries = unexplained_word_boundary_census(original, compiled)
    head = boundaries["common_start_word_tokens"]
    tail = boundaries["common_end_word_tokens"]
    a = left[head:len(left)-tail if tail else len(left)]
    b = right[head:len(right)-tail if tail else len(right)]
    if not a and not b:
        raise PilotError("Original word selection has no differing span")
    return a, b, boundaries


def source_stock_unresolved_words(original: str, compiled: str) -> dict:
    """No word leaves the function; alignment is a hypothesis, never approval."""
    a, b, boundaries = _middle_words(original, compiled)
    intersection = sum((Counter(a) & Counter(b)).values())
    if not a:
        category = "only_stock_middle_words_added"
    elif not b:
        category = "only_source_middle_words_removed"
    elif len(a) == len(b) == 1:
        category = "one_to_one_middle_word_substitution"
    elif a == b:
        # Not possible after stripping common prefix/suffix, unless caller changed.
        raise PilotError("Middle words unexpectedly identical")
    elif len(a) == len(b) and Counter(a) == Counter(b):
        category = "middle_same_word_multiset_different_order"
    elif intersection == 0:
        category = "middle_word_multisets_disjoint"
    else:
        category = "middle_partial_shared_word_occurrences"
    if len(a) == len(b) == 1:
        if a[0].casefold() == b[0].casefold():
            one_word = "same_only_after_unicode_casefold"
        elif unicodedata.normalize("NFKC", a[0]) == unicodedata.normalize("NFKC", b[0]):
            one_word = "same_only_after_nfkc"
        elif a[0].isdecimal() and b[0].isdecimal():
            one_word = "different_decimal_number_words"
        else:
            one_word = "different_case_sensitive_unicode_word"
    else:
        one_word = "not_one_to_one"
    if len(a) * len(b) <= MAX_ALIGNMENT_CELLS:
        # Deterministic, symmetric evidence of distinct matching/edited blocks.
        # autojunk=False avoids silently dropping repeated Bible-commentary words.
        opcodes = SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
        op_counts = Counter(op for op, _, _, _, _ in opcodes)
        shared_blocks = op_counts["equal"]
        nontrivial_edits = sum(op_counts[x] for x in ("replace", "insert", "delete"))
        if nontrivial_edits == 0:
            raise PilotError("Unequal middle had no lexical edits")
        alignment = ("single_edit_block" if nontrivial_edits == 1 else
                     "multiple_distinct_edit_blocks")
        alignment_exact_middle_matching_words = sum(
            i2 - i1 for op, i1, i2, _, _ in opcodes if op == "equal"
        )
    else:
        alignment = "alignment_skipped_under_explicit_safe_cell_limit"
        op_counts = Counter()
        shared_blocks = 0
        nontrivial_edits = 0
        alignment_exact_middle_matching_words = 0
    if intersection > min(len(a), len(b)):
        raise PilotError("Private original stock multiset intersection too large")
    return {
        "lexical_middle_shape": category,
        "one_word_difference_subtype": one_word,
        "source_changed_middle_words": len(a),
        "stock_changed_middle_words": len(b),
        "shared_middle_word_multiset_occurrences": intersection,
        "common_start_word_tokens": boundaries["common_start_word_tokens"],
        "common_end_word_tokens": boundaries["common_end_word_tokens"],
        "middle_alignment_class": alignment,
        "exact_middle_matching_words_in_alignment": alignment_exact_middle_matching_words,
        "exact_middle_word_matching_blocks": shared_blocks,
        "alignment_edit_opcode_count": nontrivial_edits,
        "alignment_opcode_type_counts": dict(sorted(op_counts.items())),
        "matching_word_multiset_does_not_prove_original_order_or_text": True,
        "unresolved_selection_does_not_prove_content_loss_or_edition_equivalence": True,
        "original_words_or_replacements_exposed": False,
    }


def stock_raw_element_counts(raw: bytes) -> dict:
    """Counts actual XML names, strictly; never exposes content/attributes."""
    if len(raw) > 2 * 1024 * 1024 or b"\x00" in raw:
        raise PilotError("Original compiled XML exceeds safe stock markup bound")
    try:
        root = etree.fromstring(
            b"<stock>" + raw + b"</stock>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False,
            ),
        )
    except (ValueError, etree.XMLSyntaxError):
        raise PilotError("Cannot parse actual stock raw XML for lexical audit") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise PilotError("Unresolved stock raw XML entity cannot be compared")
    counts = Counter()
    for node in root.iter():
        if node is root or not isinstance(node.tag, str):
            continue
        counts[node.tag.rsplit("}", 1)[-1]] += 1
    return dict(sorted(counts.items()))


class UnresolvedLexicalSelectionCensus:
    """Full 156-case private inventory, bounded SHA/line-only priority examples."""

    def __init__(self):
        self.total = 0
        self.category = Counter()
        self.one_word = Counter()
        self.alignments = Counter()
        self.source_link_marked = Counter()
        self.stock_link_marked = Counter()
        self.stock_title_or_table_marked = Counter()
        self.edit_ops = Counter()
        self.stock_link_and_source_link = Counter()
        self.original_middle_bins = Counter()
        self.stock_middle_bins = Counter()
        self.changed_middle_overlap = Counter()
        self.by_book = {}
        self.candidates = []

    @staticmethod
    def _bucket(value: int) -> str:
        if value == 0:
            return "0"
        if value == 1:
            return "1"
        if value <= 5:
            return "2_to_5"
        if value <= 20:
            return "6_to_20"
        if value <= 100:
            return "21_to_100"
        return "over_100"

    def observe(self, source: dict, compiled: str, raw: bytes, book: str) -> dict:
        if not isinstance(source.get("original_source_line"), int) or not re.fullmatch(
            r"[a-f0-9]{64}", source.get("original_full_reference_sha256", "")
        ):
            raise PilotError("Missing pinned original commentary line/reference identity")
        original = source["original_text"]
        delta = source_stock_unresolved_words(original, compiled)
        original_tags = source.get("private_original_body_tag_counts")
        if not isinstance(original_tags, dict):
            raise PilotError("Original source body markup not independently inventoried")
        stock_tags = stock_raw_element_counts(raw)
        orig_links = original_tags.get("scripRef", 0)
        stock_links = stock_tags.get("reference", 0)
        if any(type(n) is not int or n < 0 for n in original_tags.values()):
            raise PilotError("Invalid original source tag count")
        self.total += 1
        self.category[delta["lexical_middle_shape"]] += 1
        self.one_word[delta["one_word_difference_subtype"]] += 1
        self.alignments[delta["middle_alignment_class"]] += 1
        self.edit_ops.update(delta["alignment_opcode_type_counts"])
        self.original_middle_bins[self._bucket(delta["source_changed_middle_words"])] += 1
        self.stock_middle_bins[self._bucket(delta["stock_changed_middle_words"])] += 1
        self.changed_middle_overlap[self._bucket(delta["shared_middle_word_multiset_occurrences"])] += 1
        self.source_link_marked["source_has_scripRef" if orig_links else "source_no_scripRef"] += 1
        self.stock_link_marked["stock_has_reference" if stock_links else "stock_no_reference"] += 1
        self.stock_title_or_table_marked[
            "stock_contains_title_or_table" if stock_tags.get("title", 0) or stock_tags.get("table", 0)
            else "stock_no_title_or_table"] += 1
        self.stock_link_and_source_link[
            ("source_link" if orig_links else "no_source_link")
            + "_"
            + ("stock_reference" if stock_links else "no_stock_reference")
        ] += 1
        self.by_book.setdefault(book, Counter())[delta["lexical_middle_shape"]] += 1
        # Sort by the largest changed interval and lowest shared middle word count.
        # This is deterministic and contains no wording, references or glyphs.
        selected = {
            "source_line": source["original_source_line"],
            "original_reference_sha256": source["original_full_reference_sha256"],
            "original_body_sha256": source["original_text_sha256"],
            "stock_raw_sha256": sha256(raw).hexdigest(),
            "source_markup_scripRef_count": orig_links,
            "stock_markup_reference_count": stock_links,
            "stock_markup_title_count": stock_tags.get("title", 0),
            "stock_markup_table_count": stock_tags.get("table", 0),
            "source_middle_word_count": delta["source_changed_middle_words"],
            "stock_middle_word_count": delta["stock_changed_middle_words"],
            "shared_changed_middle_words": delta["shared_middle_word_multiset_occurrences"],
            "same_prefix_words": delta["common_start_word_tokens"],
            "same_suffix_words": delta["common_end_word_tokens"],
            "lexical_shape": delta["lexical_middle_shape"],
            "middle_alignment": delta["middle_alignment_class"],
            "alignment_edit_opcode_count": delta["alignment_edit_opcode_count"],
        }
        self.candidates.append(selected)
        return delta

    def report(self) -> dict:
        if self.total != len(self.candidates) or self.total == 0:
            raise PilotError("Original uncommented lexical discrepancies not fully counted")
        for category in (
            self.category, self.one_word, self.alignments, self.source_link_marked,
            self.stock_link_marked, self.stock_title_or_table_marked,
            self.stock_link_and_source_link, self.original_middle_bins,
            self.stock_middle_bins, self.changed_middle_overlap
        ):
            if sum(category.values()) != self.total:
                raise PilotError("Original source/stock mismatch diagnostic accounting incomplete")
        # Rank most difficult cases first (not only easy 1:1 substitutions).
        priority = sorted(
            self.candidates,
            key=lambda a: (
                -max(a["source_middle_word_count"], a["stock_middle_word_count"]),
                a["shared_changed_middle_words"], a["source_line"],
                a["original_reference_sha256"],
            ),
        )[:MAX_PRIVATE_CASES]
        return {
            "source_vs_stock_unresolved_word_selection_cases": self.total,
            "differing_middle_shape_classes": dict(sorted(self.category.items())),
            "one_word_case_character_classes": dict(sorted(self.one_word.items())),
            "original_middle_word_count_buckets": dict(sorted(self.original_middle_bins.items())),
            "stock_middle_word_count_buckets": dict(sorted(self.stock_middle_bins.items())),
            "shared_middle_word_multiset_occurrence_buckets": dict(sorted(self.changed_middle_overlap.items())),
            "middle_exact_alignment_classes": dict(sorted(self.alignments.items())),
            "bounded_alignment_opcode_types": dict(sorted(self.edit_ops.items())),
            "source_scripRef_presence": dict(sorted(self.source_link_marked.items())),
            "stock_reference_presence": dict(sorted(self.stock_link_marked.items())),
            "source_scripRef_x_stock_reference_presence": dict(sorted(self.stock_link_and_source_link.items())),
            "stock_title_or_table_presence": dict(sorted(self.stock_title_or_table_marked.items())),
            "per_book_source_marker_lexical_middle_shapes": {
                book: dict(sorted(counts.items())) for book, counts in sorted(self.by_book.items())
            },
            "bounded_highest_changed_word_count_line_hash_only_cases": priority,
            "priority_receipt_limit": MAX_PRIVATE_CASES,
            "stock_reference_presence_is_not_source_markup_or_target_parity": True,
            "source_word_stock_word_selection_or_editions_not_automatically_reconciled": True,
            "no_original_words_punctuation_reference_strings_or_stock_xml_in_report": True,
            "original_content_or_stock_module_modified": False,
            "full_original_commentary_authorial_text_parity_approved": False,
        }
