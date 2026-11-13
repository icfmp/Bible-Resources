#!/usr/bin/env python3
"""Private native SWORD cross-slot scripture target and raw-payload topology.

A repeated raw payload or matching cited target at another native key does NOT
prove original commentary placement, authorial edition, verse range or rights.
Only closed-set counts, line numbers and SHA-256 identifiers leave the runner.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

from pilot_preflight import PilotError
from commentary_chapter_ref_labels import link_label_location

MAX_NATIVE_STOCK_KEYS = 45000
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_SOURCE_REFERENCE_LABELS = 250000
MAX_UNRESOLVED_MARKERS = 20000
MAX_PRIVATE_RECEIPTS = 20
SHA_RE = re.compile(r"[0-9a-f]{64}")


def actual_stock_osisref_targets(raw: bytes) -> list[str]:
    """Do not interpret source text or strip any actual stock attribute value."""
    if len(raw) > MAX_XML_BYTES or b"\x00" in raw:
        raise PilotError("Native stock fragment is outside reviewed reference bounds")
    try:
        root = etree.fromstring(
            b"<stock>" + raw + b"</stock>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False,
            ),
        )
    except (etree.XMLSyntaxError, ValueError):
        raise PilotError("Native stock reference fragment cannot be strictly parsed") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise PilotError("Native stock contains an unreviewed entity")
    return [
        node.get("osisRef", "") for node in root.iter()
        if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "reference"
    ]


def _private_target_counts(links: list[dict], stock_targets: list[str]):
    """Pair actual target occurrences, exact first, then literal Bible: only."""
    source = Counter(link["private_original_osisRef_target"] for link in links)
    stock = Counter(stock_targets)
    exact = source & stock
    orig_remaining = source - exact
    stock_remaining = stock - exact
    work = Counter()
    for source_target, occurrences in list(orig_remaining.items()):
        if source_target.startswith("Bible:") and len(source_target) > len("Bible:"):
            stripped = source_target[len("Bible:"):]
            n = min(occurrences, stock_remaining.get(stripped, 0))
            if n:
                work[source_target] = n
                stock_remaining[stripped] -= n
                if stock_remaining[stripped] == 0:
                    del stock_remaining[stripped]
                orig_remaining[source_target] -= n
                if orig_remaining[source_target] == 0:
                    del orig_remaining[source_target]
    return orig_remaining, stock_remaining, sum(exact.values()), sum(work.values())


def original_link_target_match_statuses(links: list[dict], stock_targets: list[str]) -> list[str]:
    """Pair original occurrence targets exact first, then literal Bible: only.

    The statuses are diagnostic labels, never source or stock modifications.
    """
    available = Counter(stock_targets)
    statuses = ["unpaired_original_target"] * len(links)
    for i, link in enumerate(links):
        target = link["private_original_osisRef_target"]
        if available[target] > 0:
            statuses[i] = "raw_target_exact_match"
            available[target] -= 1
    for i, link in enumerate(links):
        if statuses[i] != "unpaired_original_target":
            continue
        target = link["private_original_osisRef_target"]
        if target.startswith("Bible:") and len(target) > len("Bible:"):
            unqualified = target[len("Bible:"):]
            if available[unqualified] > 0:
                statuses[i] = "literal_Bible_work_prefix_only_match"
                available[unqualified] -= 1
    return statuses


class ReferenceCrossSlotTopology:
    """Read every occupied original native slot once and compare only 156 cases."""

    def __init__(self, original: dict):
        self.original_chapters_for_target = defaultdict(set)
        self.expected_stock_targets_by_book = defaultdict(set)
        self.books = set()
        link_total = 0
        for start, items in original.items():
            if "." not in start:
                raise PilotError("Original source annotation key is not a numbered passage")
            book, chapter = start.split(".", 1)[0], start.rsplit(".", 1)[0]
            self.books.add(book)
            for item in items:
                links = item.get("private_original_scripRef_links")
                if not isinstance(links, list):
                    raise PilotError("Original commentary link target inventory missing")
                link_total += len(links)
                for link in links:
                    target = link.get("private_original_osisRef_target")
                    if not isinstance(target, str) or len(target) > 2048:
                        raise PilotError("Original scripture reference target not bounded")
                    if target.startswith("Bible:") and len(target) > len("Bible:"):
                        suffix = target[len("Bible:"):]
                        self.expected_stock_targets_by_book[book].add(suffix)
                        self.original_chapters_for_target[(book, suffix)].add(chapter)
                    elif target:
                        self.expected_stock_targets_by_book[book].add(target)
                        self.original_chapters_for_target[(book, target)].add(chapter)
        if not self.books or link_total > MAX_SOURCE_REFERENCE_LABELS:
            raise PilotError("Original reference-link inventory exceeds reviewed bounds")
        self.native_keys_scanned = 0
        self.native_reference_bearing_keys = 0
        self.native_reference_tag_count = 0
        self.strict_xml_reference_parse_failures = 0
        self.stock_positions = defaultdict(set)
        self.identical_raw_counts_by_book = defaultdict(Counter)
        self.private_unresolved = []

    def observe_stock(self, kind: str, key: str, raw: bytes) -> None:
        """Actual independently indexed native K/I, no inferred verse expansion."""
        if kind not in {"K", "I"}:
            return
        book = key.split(".", 1)[0]
        if book not in self.books:
            return
        self.native_keys_scanned += 1
        if self.native_keys_scanned > MAX_NATIVE_STOCK_KEYS:
            raise PilotError("Original native key count exceeds safe review bounds")
        digest = sha256(raw).hexdigest()
        self.identical_raw_counts_by_book[(book, digest)][kind] += 1
        if b"reference" not in raw:
            return
        try:
            values = actual_stock_osisref_targets(raw)
        except PilotError:
            self.strict_xml_reference_parse_failures += 1
            return
        if not values:
            return
        self.native_reference_bearing_keys += 1
        self.native_reference_tag_count += len(values)
        tracked = self.expected_stock_targets_by_book[book]
        for value in set(values):
            if value in tracked:
                self.stock_positions[(book, value)].add(
                    (kind, key, digest)
                )

    def observe_unresolved(self, start: str, original: dict, raw: bytes) -> None:
        """Called ONLY from the existing authenticated unresolved-body classifier."""
        if raw is None:
            raise PilotError("Cannot locate absent compiled original reference body")
        if len(self.private_unresolved) >= MAX_UNRESOLVED_MARKERS:
            raise PilotError("Unreviewed number of lexical cases")
        if (not SHA_RE.fullmatch(original.get("original_full_reference_sha256", ""))
                or not SHA_RE.fullmatch(original.get("original_text_sha256", ""))
                or type(original.get("original_source_line")) is not int):
            raise PilotError("Original annotation lacks independently pinned line/hash")
        self.private_unresolved.append((start, original, raw))

    @staticmethod
    def _stock_target_scope(book: str, chapter: str, start: str,
                            target: str, positions: set) -> str:
        if any(kind == "K" and key != start and key.rsplit(".", 1)[0] == chapter
               for kind, key, _ in positions):
            return "target_witnessed_in_other_numbered_key_same_chapter"
        if any(kind == "I" and key in (chapter, chapter + ".0")
               for kind, key, _ in positions):
            return "target_witnessed_in_same_chapter_intro_key"
        if positions:
            return "target_witnessed_elsewhere_in_same_book"
        return "target_not_witnessed_in_other_same_book_stock_reference_markup"

    def report(self, expected: dict) -> dict:
        if len(self.private_unresolved) != expected[
            "source_vs_stock_unresolved_word_selection_cases"
        ]:
            raise PilotError("Cross-slot original source word differences do not reconcile")
        source_categories = Counter()
        compiled_categories = Counter()
        marker_census = Counter()
        no_stock_cases = []
        priority_cases = []
        total_original_links = 0
        total_stock_links = 0
        exact_matches = 0
        literal_qualifier_matches = 0
        for start, item, raw in self.private_unresolved:
            book, chapter = start.split(".", 1)[0], start.rsplit(".", 1)[0]
            orig = item["private_original_scripRef_links"]
            selected_stock_targets = actual_stock_osisref_targets(raw)
            remain_source, remain_stock, exact, qualifier = _private_target_counts(
                orig, selected_stock_targets
            )
            total_original_links += len(orig)
            total_stock_links += len(selected_stock_targets)
            exact_matches += exact
            literal_qualifier_matches += qualifier
            selected_values = Counter(selected_stock_targets)
            source_values = Counter(
                link["private_original_osisRef_target"] for link in orig
            )
            this_source = Counter()
            this_stock = Counter()
            for target, occurrences in remain_source.items():
                if target in selected_values or (
                    target.startswith("Bible:") and target[len("Bible:"):] in selected_values
                ):
                    category = "same_entry_reference_target_multiplicity_shortfall"
                elif target.startswith("Bible:") and len(target) > len("Bible:"):
                    category = self._stock_target_scope(
                        book, chapter, start, target[len("Bible:"):],
                        self.stock_positions.get((book, target[len("Bible:"):]), set())
                    )
                elif not target:
                    category = "original_source_target_is_empty"
                else:
                    category = "original_target_not_literal_Bible_work_qualified_unreviewed"
                source_categories[category] += occurrences
                this_source[category] += occurrences
            for target, occurrences in remain_stock.items():
                if target in source_values or "Bible:" + target in source_values:
                    category = "same_entry_original_target_multiplicity_shortfall"
                else:
                    chapters = self.original_chapters_for_target.get((book, target), set())
                    if chapter in chapters:
                        category = "target_witnessed_in_other_original_source_unit_same_chapter"
                    elif chapters:
                        category = "target_witnessed_in_other_original_source_chapter_same_book"
                    else:
                        category = "stock_target_not_in_any_original_verse_range_link_same_book"
                compiled_categories[category] += occurrences
                this_stock[category] += occurrences
            case_key = (book, sha256(raw).hexdigest())
            repeated = self.identical_raw_counts_by_book[case_key]
            if not repeated:
                raise PilotError("Original selected stock raw entry absent from complete native stream")
            if not selected_stock_targets:
                marker_census["source_marker_with_no_compiled_reference_tag"] += 1
            else:
                marker_census["source_marker_with_compiled_reference_tag"] += 1
            receipt = {
                "original_source_line":item["original_source_line"],
                "original_full_reference_sha256":item["original_full_reference_sha256"],
                "original_body_sha256":item["original_text_sha256"],
                "compiled_stock_raw_sha256":case_key[1],
                "unpaired_original_reference_targets":sum(remain_source.values()),
                "unpaired_stock_reference_targets":sum(remain_stock.values()),
                "unpaired_original_target_scope_counts":dict(sorted(this_source.items())),
                "unpaired_compiled_target_source_scope_counts":dict(sorted(this_stock.items())),
                "same_book_numbered_native_keys_with_identical_selected_raw":repeated["K"],
                "same_book_intro_native_keys_with_identical_selected_raw":repeated["I"],
                "native_payload_repetition_is_not_source_range_or_commentary_parity":True,
            }
            if not selected_stock_targets:
                no_stock_cases.append(receipt)
            priority_cases.append(receipt)
        if (total_original_links != expected[
                "original_scripRef_total_across_unresolved_entries"
            ] or total_stock_links != expected[
                "stock_reference_total_across_unresolved_entries"
            ] or exact_matches != expected[
                "raw_exact_osisRef_target_multiset_match_count"
            ] or literal_qualifier_matches != expected[
                "literal_Bible_work_qualifier_only_osisRef_target_multiset_match_count"
            ] or sum(source_categories.values()) != total_original_links-exact_matches-literal_qualifier_matches
              or sum(compiled_categories.values()) != total_stock_links-exact_matches-literal_qualifier_matches
              or sum(marker_census.values()) != len(self.private_unresolved)
              or len(no_stock_cases) != expected["stock_reference_presence"].get("stock_no_reference", 0)):
            raise PilotError("Cross-entry lexical reference census disagrees with original full stock audit")
        # Keep no-reference cases complete, and only the 20 largest unresolved
        # source target counts otherwise. Never emit any target or verse name.
        if len(no_stock_cases) > MAX_PRIVATE_RECEIPTS:
            raise PilotError("No-reference original cases exceed bounded metadata output")
        priority = sorted(
            priority_cases,
            key=lambda row: (
                -row["unpaired_original_reference_targets"],
                -row["unpaired_stock_reference_targets"],
                row["original_source_line"],
                row["original_full_reference_sha256"],
            ),
        )[:MAX_PRIVATE_RECEIPTS]
        return {
            "source_markers_with_lexically_unresolved_reference_issues":len(self.private_unresolved),
            "original_scripRef_target_occurrences":total_original_links,
            "stock_reference_target_occurrences":total_stock_links,
            "source_and_stock_raw_exact_target_matches":exact_matches,
            "source_and_stock_literal_Bible_work_prefix_only_matches":literal_qualifier_matches,
            "source_unpaired_target_occurrence_location_classes":dict(sorted(source_categories.items())),
            "stock_unpaired_target_occurrence_source_classes":dict(sorted(compiled_categories.items())),
            "original_source_markers_with_or_without_stock_reference_markup":dict(sorted(marker_census.items())),
            "complete_native_K_and_I_keys_inspected_for_target_witnesses":self.native_keys_scanned,
            "native_keys_with_at_least_one_reference_element":self.native_reference_bearing_keys,
            "stock_reference_elements_in_all_scanned_native_keys":self.native_reference_tag_count,
            "reference_markup_strict_xml_parse_failures":self.strict_xml_reference_parse_failures,
            "bounded_all_no_stock_reference_case_line_fullhash_topology":sorted(
                no_stock_cases, key=lambda r:(r["original_source_line"],r["original_full_reference_sha256"])
            ),
            "bounded_highest_unpaired_source_target_line_fullhash_topology":priority,
            "reviewed_metadata_line_hash_only_case_cap":MAX_PRIVATE_RECEIPTS,
            "original_target_at_other_key_is_only_a_location_witness_not_source_annotation_parity":True,
            "same_raw_in_many_native_keys_may_reflect_range_propagation_not_distinct_comments":True,
            "all_same_book_negative_findings_are_scope_limited":True,
            "original_target_text_and_reference_labels_never_disclosed":True,
            "authorial_original_to_stock_text_markup_or_edition_parity_verified":False,
        }
