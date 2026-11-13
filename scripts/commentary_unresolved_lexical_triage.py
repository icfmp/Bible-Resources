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
from commentary_chapter_ref_labels import link_label_location
from commentary_nonlink_words import compare_words_outside_links
from commentary_nonlink_word_alignment import plain_word_alignment
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


def marked_word_token_indices(element, marker_tag: str, expected_text: str) -> list[int]:
    """Map original and compiled inline-link labels to real *word token offsets*.

    Uses the original XML's own text/tail stream; never guesses labels from
    reference strings or substring search. No word token or label is returned.
    """
    if marker_tag not in {"scripRef", "reference"}:
        raise PilotError("Unreviewed inline source/stock tag requested")
    fragments = []
    spans = []
    cursor = 0

    def emit(value: str | None):
        nonlocal cursor
        if value:
            fragments.append(value)
            cursor += len(value)

    def walk(node):
        emit(node.text)
        for child in node:
            if isinstance(child.tag, str):
                start = cursor
                walk(child)
                end = cursor
                if child.tag.rsplit("}", 1)[-1] == marker_tag:
                    spans.append((start, end))
            emit(child.tail)

    walk(element)
    if "".join(fragments) != expected_text:
        raise PilotError("Original XML inline reference text offsets cannot be authenticated")
    found = []
    for n, word in enumerate(WORD.finditer(expected_text)):
        if any(start < word.end() and word.start() < end for start, end in spans):
            found.append(n)
    return found


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
        self.original_changed_link_token_presence = Counter()
        self.stock_changed_link_token_presence = Counter()
        self.original_and_stock_changed_link_token_overlap = Counter()
        self.one_word_link_overlap = Counter()
        self.original_to_compiled_reference_target_classes = Counter()
        self.original_reference_label_location_classes = Counter()
        self.source_scripRef_attribute_name_occurrences = Counter()
        self.source_stock_reference_element_count_relationships = Counter()
        self.original_reference_total = 0
        self.stock_reference_total = 0
        self.source_nonempty_targets_total = 0
        self.stock_nonempty_targets_total = 0
        self.raw_exact_target_multiset_matches_total = 0
        self.literal_work_qualifier_only_target_matches_total = 0
        self.no_stock_reference_cases = []
        self.nonlink_word_relationships = Counter()
        self.nonlink_relation_by_stock_reference_markup = {}
        self.nonlink_word_relationships_by_original_lexical_shape = {}
        self.original_plain_word_bins = Counter()
        self.stock_plain_word_bins = Counter()
        self.nonlink_attention_cases = []
        self.nonlink_alignment_classes = Counter()
        self.nonlink_alignment_unmatched_source_bins = Counter()
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
        original_link_indices = source.get("private_original_scripRef_word_indices")
        if (not isinstance(original_link_indices, list)
                or any(type(k) is not int or k < 0 for k in original_link_indices)):
            raise PilotError("Original source link-word offset witness absent")
        try:
            stock_root = etree.fromstring(
                b"<stock>" + raw + b"</stock>",
                parser=etree.XMLParser(
                    resolve_entities=False, no_network=True, load_dtd=False,
                    recover=False, huge_tree=False, remove_blank_text=False,
                ),
            )
        except (ValueError, etree.XMLSyntaxError):
            raise PilotError("Stock reference inline markup cannot be mapped") from None
        stock_link_indices = marked_word_token_indices(stock_root,"reference",compiled)
        source_words = WORD.findall(original)
        stock_words = WORD.findall(compiled)
        plain_witness = compare_words_outside_links(
            source_words, stock_words, original_link_indices, stock_link_indices
        )
        nonlink_category = plain_witness["outside_link_word_relation"]
        self.nonlink_word_relationships[nonlink_category] += 1
        self.nonlink_word_relationships_by_original_lexical_shape.setdefault(
            delta["lexical_middle_shape"],Counter()
        )[nonlink_category] += 1
        self.original_plain_word_bins[self._bucket(plain_witness["original_plain_word_tokens"])] += 1
        self.stock_plain_word_bins[self._bucket(plain_witness["stock_plain_word_tokens"])] += 1
        if nonlink_category in {
            "plain_word_order_or_selection_requires_editorial_review",
            "same_plain_word_multiset_but_different_order",
            "source_plain_words_only_after_removing_stock_scripture_labels",
        }:
            plain_original = [w for i,w in enumerate(source_words)
                              if i not in set(original_link_indices)]
            plain_compiled = [w for i,w in enumerate(stock_words)
                              if i not in set(stock_link_indices)]
            alignment = plain_word_alignment(plain_original, plain_compiled)
            if (alignment["original_plain_word_tokens"] !=
                plain_witness["original_plain_word_tokens"] or
                alignment["stock_plain_word_tokens"] !=
                plain_witness["stock_plain_word_tokens"]):
                raise PilotError("Original source/stock alignment did not preserve verified plain word counts")
            alignment_type = alignment["exact_unicode_ordered_alignment_class"]
            self.nonlink_alignment_classes[alignment_type] += 1
            if alignment["original_plain_words_not_matched_in_exact_order"] is None:
                self.nonlink_alignment_unmatched_source_bins["unreviewed_large_alignment"] += 1
            else:
                self.nonlink_alignment_unmatched_source_bins[
                    self._bucket(alignment["original_plain_words_not_matched_in_exact_order"])
                ] += 1
            self.nonlink_attention_cases.append({
                "original_source_line":source["original_source_line"],
                "original_full_reference_sha256":source["original_full_reference_sha256"],
                "original_body_sha256":source["original_text_sha256"],
                "stock_raw_sha256":sha256(raw).hexdigest(),
                "original_plain_word_tokens":plain_witness["original_plain_word_tokens"],
                "stock_plain_word_tokens":plain_witness["stock_plain_word_tokens"],
                "shared_plain_word_multiset_occurrences":
                    plain_witness["shared_plain_word_multiset_occurrences"],
                "outside_link_word_relation":nonlink_category,
                "exact_plain_word_alignment":alignment,
                "original_source_p_element_count":
                    original_tags.get("p",0),
                "original_source_note_element_count":
                    original_tags.get("note",0),
                "original_source_scripRef_element_count":
                    original_tags.get("scripRef",0),
                "stock_p_element_count":stock_tags.get("p",0),
                "stock_note_element_count":stock_tags.get("note",0),
                "stock_reference_element_count":stock_tags.get("reference",0),
                "stock_title_element_count":stock_tags.get("title",0),
                "stock_table_element_count":stock_tags.get("table",0),
            })
        orig_head = delta["common_start_word_tokens"]
        orig_tail = len(source_words) - delta["common_end_word_tokens"]
        stock_head = orig_head
        stock_tail = len(stock_words) - delta["common_end_word_tokens"]
        source_changed_link = sum(
            orig_head <= idx < orig_tail for idx in original_link_indices
        )
        stock_changed_link = sum(
            stock_head <= idx < stock_tail for idx in stock_link_indices
        )
        source_changed = delta["source_changed_middle_words"]
        stock_changed = delta["stock_changed_middle_words"]
        if source_changed_link > source_changed or stock_changed_link > stock_changed:
            raise PilotError("Reference label words exceed known differing middle span")
        stock_links = stock_tags.get("reference", 0)
        self.nonlink_relation_by_stock_reference_markup.setdefault(
            "stock_has_reference" if stock_links else "stock_no_reference",Counter()
        )[nonlink_category] += 1
        original_ref_links = source.get("private_original_scripRef_links")
        if not isinstance(original_ref_links, list) or len(original_ref_links) != orig_links:
            raise PilotError("Original scripRef source labels and target inventory inconsistent")
        ref_witness = link_label_location(original_ref_links, raw)
        if (ref_witness["original_scripRef_label_count"] != orig_links or
                ref_witness["selected_stock_reference_element_count"] != stock_links):
            raise PilotError("Original-source and stock-reference independent tag counts diverge")
        exact_targets = ref_witness[
            "original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"
        ]
        qualifier_targets = ref_witness[
            "original_scripRef_osisRef_work_qualifier_only_matches_in_stock"
        ]
        if stock_links == 0:
            ref_class = "no_stock_reference_markup"
        elif ref_witness["source_and_selected_stock_reference_targets_exact_ordered_match"]:
            ref_class = "all_osisRef_values_identical_in_order"
        elif ref_witness["source_and_stock_targets_only_literal_bible_work_qualifier_ordered_match"]:
            ref_class = "all_osisRef_values_ordered_sole_literal_Bible_work_qualifier_difference"
        elif (orig_links == stock_links and
              exact_targets + qualifier_targets == orig_links):
            ref_class = "all_targets_multiset_correspond_but_order_or_mixed_format_unverified"
        elif exact_targets + qualifier_targets > 0:
            ref_class = "some_targets_correspond_but_not_all"
        else:
            ref_class = "no_exact_or_literal_qualifier_only_target_correspondence"
        if any(type(n) is not int or n < 0 for n in original_tags.values()):
            raise PilotError("Invalid original source tag count")
        self.total += 1
        self.original_to_compiled_reference_target_classes[ref_class] += 1
        self.original_reference_label_location_classes.update(ref_witness[
            "original_scripRef_to_stock_text_location_classes"
        ])
        self.source_scripRef_attribute_name_occurrences.update(ref_witness[
            "original_scripRef_attribute_name_occurrences"
        ])
        self.original_reference_total += orig_links
        self.stock_reference_total += stock_links
        self.source_nonempty_targets_total += ref_witness[
            "original_scripRef_with_nonempty_osisRef_target_count"
        ]
        self.stock_nonempty_targets_total += ref_witness[
            "selected_stock_reference_elements_with_osisRef_attribute"
        ]
        self.raw_exact_target_multiset_matches_total += exact_targets
        self.literal_work_qualifier_only_target_matches_total += qualifier_targets
        self.source_stock_reference_element_count_relationships[
            "same_reference_tag_count" if orig_links == stock_links
            else ("more_original_scripRef_than_stock_reference"
                  if orig_links > stock_links
                  else "more_stock_reference_than_original_scripRef")
        ] += 1
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
        source_context = ("all_source_changed_words_in_scripRef"
                          if source_changed > 0 and source_changed_link == source_changed
                          else ("some_source_changed_words_in_scripRef"
                                if source_changed_link else "no_source_changed_words_in_scripRef"))
        stock_context = ("all_stock_changed_words_in_reference"
                         if stock_changed > 0 and stock_changed_link == stock_changed
                         else ("some_stock_changed_words_in_reference"
                               if stock_changed_link else "no_stock_changed_words_in_reference"))
        self.original_changed_link_token_presence[source_context] += 1
        self.stock_changed_link_token_presence[stock_context] += 1
        self.original_and_stock_changed_link_token_overlap[
            ("source_link_overlap" if source_changed_link else "source_no_link_overlap")
            + "_"
            + ("stock_ref_overlap" if stock_changed_link else "stock_no_ref_overlap")
        ] += 1
        if source_changed == stock_changed == 1:
            self.one_word_link_overlap[
                ("source_within_scripRef" if source_changed_link else "source_outside_scripRef")
                + "_"
                + ("stock_within_reference" if stock_changed_link else "stock_outside_reference")
            ] += 1
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
            "original_to_stock_reference_target_relationship": ref_class,
            "original_source_scripRef_target_nonempty_count": ref_witness[
                "original_scripRef_with_nonempty_osisRef_target_count"
            ],
            "stock_reference_osisRef_present_count": ref_witness[
                "selected_stock_reference_elements_with_osisRef_attribute"
            ],
            "source_stock_reference_raw_target_exact_multiset_matches": exact_targets,
            "source_stock_reference_literal_work_qualifier_only_target_matches": qualifier_targets,
            "changed_source_middle_words_in_scripRef": source_changed_link,
            "changed_stock_middle_words_in_reference": stock_changed_link,
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
        if not stock_links:
            self.no_stock_reference_cases.append({
                "source_line":source["original_source_line"],
                "original_reference_sha256":source["original_full_reference_sha256"],
                "original_body_sha256":source["original_text_sha256"],
                "stock_raw_sha256":sha256(raw).hexdigest(),
                "original_scripRef_count":orig_links,
                "original_scripRef_target_nonempty_count":ref_witness[
                    "original_scripRef_with_nonempty_osisRef_target_count"
                ],
                "source_label_location_classes_in_unmarked_stock_text":dict(sorted(
                    ref_witness["original_scripRef_to_stock_text_location_classes"].items()
                )),
                "no_original_stock_reference_or_text_assigned_as_equivalent":True,
            })
        return delta

    def report(self) -> dict:
        if self.total != len(self.candidates) or self.total == 0:
            raise PilotError("Original uncommented lexical discrepancies not fully counted")
        for category in (
            self.category, self.one_word, self.alignments, self.source_link_marked,
            self.stock_link_marked, self.stock_title_or_table_marked,
            self.original_changed_link_token_presence, self.stock_changed_link_token_presence,
            self.original_and_stock_changed_link_token_overlap,
            self.stock_link_and_source_link,
            self.original_to_compiled_reference_target_classes,
            self.source_stock_reference_element_count_relationships,
            self.original_middle_bins, self.stock_middle_bins, self.changed_middle_overlap,
            self.nonlink_word_relationships, self.original_plain_word_bins,
            self.stock_plain_word_bins
        ):
            if sum(category.values()) != self.total:
                raise PilotError("Original source/stock mismatch diagnostic accounting incomplete")
        if (sum(sum(v.values()) for v in self.nonlink_relation_by_stock_reference_markup.values())
                != self.total or
                sum(self.nonlink_relation_by_stock_reference_markup.get(
                    "stock_has_reference",Counter()).values()) !=
                    self.stock_link_marked["stock_has_reference"] or
                sum(self.nonlink_relation_by_stock_reference_markup.get(
                    "stock_no_reference",Counter()).values()) !=
                    self.stock_link_marked["stock_no_reference"] or
                sum(sum(v.values()) for v in self.nonlink_word_relationships_by_original_lexical_shape.values())
                != self.total or
                sum(self.nonlink_word_relationships_by_original_lexical_shape.get(
                    "one_to_one_middle_word_substitution",Counter()).values()) !=
                    self.category["one_to_one_middle_word_substitution"] or
                sum(self.nonlink_word_relationships_by_original_lexical_shape.get(
                    "middle_partial_shared_word_occurrences",Counter()).values()) !=
                    self.category["middle_partial_shared_word_occurrences"]):
            raise PilotError("Original nonlink word relation census does not reconcile")
        if (sum(self.original_reference_label_location_classes.values()) !=
                self.original_reference_total or
                self.source_nonempty_targets_total > self.original_reference_total or
                self.stock_nonempty_targets_total > self.stock_reference_total or
                self.raw_exact_target_multiset_matches_total +
                self.literal_work_qualifier_only_target_matches_total >
                min(self.source_nonempty_targets_total, self.stock_nonempty_targets_total)):
            raise PilotError("Original scripture-target and label totals not fully reconciled")
        if len(self.no_stock_reference_cases) != self.stock_link_marked["stock_no_reference"]:
            raise PilotError("Missing compiled reference cases lack source-bound identities")
        if (sum(self.nonlink_alignment_classes.values()) != len(self.nonlink_attention_cases)
                or sum(self.nonlink_alignment_unmatched_source_bins.values())
                    != len(self.nonlink_attention_cases)):
            raise PilotError("Original plain-word alignment census incomplete")
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
            "original_prose_outside_link_word_relation_counts":
                dict(sorted(self.nonlink_word_relationships.items())),
            "original_prose_outside_link_relations_by_original_lexical_difference":{
                kind:dict(sorted(classes.items()))
                for kind,classes in sorted(self.nonlink_word_relationships_by_original_lexical_shape.items())
            },
            "original_prose_outside_link_relations_by_compiled_reference_markup":{
                scope:dict(sorted(values.items()))
                for scope,values in sorted(self.nonlink_relation_by_stock_reference_markup.items())
            },
            "original_plain_word_token_count_bins":dict(sorted(self.original_plain_word_bins.items())),
            "stock_plain_word_token_count_bins":dict(sorted(self.stock_plain_word_bins.items())),
            "bounded_plain_word_alignment_classes":dict(sorted(self.nonlink_alignment_classes.items())),
            "bounded_plain_word_alignment_unmatched_source_count_buckets":
                dict(sorted(self.nonlink_alignment_unmatched_source_bins.items())),
            "bounded_plain_word_nontrivial_differences_line_and_hash_cases":sorted(
                self.nonlink_attention_cases,
                key=lambda item:(
                    item["shared_plain_word_multiset_occurrences"],
                    -max(item["original_plain_word_tokens"],item["stock_plain_word_tokens"]),
                    item["original_source_line"],
                )
            )[:MAX_PRIVATE_CASES],
            "plain_word_extraction_does_not_prove_original_paragraph_or_punctuation_parity":True,
            "source_scripRef_x_stock_reference_presence": dict(sorted(self.stock_link_and_source_link.items())),
            "stock_title_or_table_presence": dict(sorted(self.stock_title_or_table_marked.items())),
            "original_scripRef_total_across_unresolved_entries":self.original_reference_total,
            "stock_reference_total_across_unresolved_entries":self.stock_reference_total,
            "original_nonempty_scripRef_osisRef_target_count":self.source_nonempty_targets_total,
            "stock_reference_elements_with_osisRef_attribute_count":self.stock_nonempty_targets_total,
            "raw_exact_osisRef_target_multiset_match_count":self.raw_exact_target_multiset_matches_total,
            "literal_Bible_work_qualifier_only_osisRef_target_multiset_match_count":
                self.literal_work_qualifier_only_target_matches_total,
            "original_scripRef_vs_stock_reference_tag_count_relationships":
                dict(sorted(self.source_stock_reference_element_count_relationships.items())),
            "original_vs_stock_target_correspondence_classes":
                dict(sorted(self.original_to_compiled_reference_target_classes.items())),
            "original_scripRef_display_label_location_in_stock_text_classes":
                dict(sorted(self.original_reference_label_location_classes.items())),
            "original_scripRef_attribute_name_occurrences":
                dict(sorted(self.source_scripRef_attribute_name_occurrences.items())),
            "all_missing_stock_reference_entry_source_line_hash_only_cases":sorted(
                self.no_stock_reference_cases,key=lambda c:(
                    c["source_line"],c["original_reference_sha256"]
                )
            ),
            "original_changed_word_tokens_in_source_scripRef": dict(
                sorted(self.original_changed_link_token_presence.items())),
            "stock_changed_word_tokens_in_stock_reference": dict(
                sorted(self.stock_changed_link_token_presence.items())),
            "source_scripRef_and_stock_reference_changed_word_overlap": dict(
                sorted(self.original_and_stock_changed_link_token_overlap.items())),
            "one_to_one_middle_word_changes_inside_source_and_stock_references": dict(
                sorted(self.one_word_link_overlap.items())),
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
