#!/usr/bin/env python3
"""Read-only original OSIS commentary reference targets versus native registry.

Independent from the reference-shape census: validate *only unambiguous*
single-book, chapter, verse and verse-range endpoint forms against the real
source-pinned libSWORD versification registry. Never guess for multi-target,
extended, work-qualified-other-than-literal-Bible or exotic OSIS grammar.

A valid target may still be an authorially wrong citation. An unrecognized or
out-of-range target may reflect source edition/versification conventions. This
reports metadata-only research candidates and NEVER rewrites annotations.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

MAX_ENTRY_BYTES = 2 * 1024 * 1024
MAX_DISTINCT_BODIES = 40000
MAX_CANDIDATE_ROWS = 80
BOOK = r"[1-4]?[A-Za-z][A-Za-z0-9]*"
CHAPTER = rf"{BOOK}\.[1-9][0-9]*"
VERSE = rf"{CHAPTER}\.[1-9][0-9]*"
SINGLE_VERSE = re.compile(rf"^{VERSE}$")
SINGLE_CHAPTER = re.compile(rf"^{CHAPTER}$")
BOOK_ONLY = re.compile(rf"^{BOOK}$")
VERSE_RANGE = re.compile(rf"^({VERSE})-({VERSE}|[1-9][0-9]*)$")


def classify_original_reference_target(
        target: str, *, canonical_verses: set[str],
        canonical_chapters: dict[str, int]) -> str:
    """No free-form original string escapes to the diagnostic receipt."""
    if not isinstance(target, str) or len(target) > 2048:
        return "UNSAFE_OR_OVERSIZE_LITERAL_TARGET"
    if not target:
        return "EMPTY_OR_MISSING_OSISREF_ATTRIBUTE"
    candidate = target[len("Bible:"):] if target.startswith("Bible:") else target
    if SINGLE_VERSE.fullmatch(candidate):
        return ("EXACT_SINGLE_VERSE_IN_REGISTRY" if candidate in canonical_verses
                else "SIMPLE_SINGLE_VERSE_NOT_IN_REGISTRY")
    match = VERSE_RANGE.fullmatch(candidate)
    if match:
        first, last = match.groups()
        if last.isdecimal():
            chapter = first.rsplit(".", 1)[0]
            last = chapter + "." + last
        if first.rsplit(".", 1)[0] == last.rsplit(".", 1)[0]:
            if int(first.rsplit(".", 1)[1]) > int(last.rsplit(".", 1)[1]):
                return "REVERSED_SAME_CHAPTER_VERSE_RANGE"
        return ("EXACT_VERSE_RANGE_ENDPOINTS_IN_REGISTRY"
                if first in canonical_verses and last in canonical_verses
                else "SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY")
    if SINGLE_CHAPTER.fullmatch(candidate):
        return ("EXACT_CHAPTER_IN_REGISTRY" if candidate in canonical_chapters
                else "SIMPLE_CHAPTER_NOT_IN_REGISTRY")
    if BOOK_ONLY.fullmatch(candidate):
        return "BOOK_ONLY_NOT_VERSE_VALIDATED"
    return "COMPLEX_OR_EXTENDED_OSIS_TARGET_UNREVIEWED"


def _unambiguous_verse_range_endpoints(target: str) -> tuple[str, str] | None:
    """Resolve only explicit literal verse ranges; never repair original text."""
    if not isinstance(target, str) or len(target) > 2048:
        return None
    candidate = target[len("Bible:"):] if target.startswith("Bible:") else target
    match = VERSE_RANGE.fullmatch(candidate)
    if match is None:
        return None
    first, last = match.groups()
    if last.isdecimal():
        last = first.rsplit(".", 1)[0] + "." + last
    return first, last


def _literal_reference_label_reversed(label: str, first: str, last: str) -> bool:
    """Observe original rendered numeric label without disclosing its words."""
    if not isinstance(label, str) or len(label) > 2048:
        return False
    start = first.rsplit(".", 1)[-1]
    end = last.rsplit(".", 1)[-1]
    # The textual label may contain a book/chapter prefix and whitespace.
    # Require an actual bounded numeric range, not incidental citations.
    return re.search(
        rf"(?<!\d){re.escape(start)}\s*[-–]\s*{re.escape(end)}(?!\d)",
        label
    ) is not None


class OriginalCommentaryReferenceRegistryTriage:
    """Source-neutral exact native K/I XML observer, never a correction engine."""

    def __init__(self):
        self._by_hash = {}
        self.native_count = Counter()
        self._reference_labels_by_hash = {}

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        if kind == "U":
            self.native_count[kind] += 1
            return
        if (kind not in {"K", "I"} or not isinstance(key, str)
                or not isinstance(raw, bytes)
                or len(raw) > MAX_ENTRY_BYTES or b"\x00" in raw):
            raise ValueError("Untrusted original commentary reference record")
        self.native_count[kind] += 1
        digest = sha256(raw).hexdigest()
        if digest in self._by_hash:
            return
        if len(self._by_hash) >= MAX_DISTINCT_BODIES:
            raise ValueError("Unbounded original commentary reference profiles")
        try:
            root = etree.fromstring(
                b"<entry>" + raw + b"</entry>",
                parser=etree.XMLParser(resolve_entities=False, no_network=True,
                                       load_dtd=False, recover=False,
                                       huge_tree=False, remove_blank_text=False)
            )
        except (etree.XMLSyntaxError, ValueError):
            raise ValueError("Malformed original reference-bearing SWORD XML") from None
        if any(isinstance(el, etree._Entity) for el in root.iter()):
            raise ValueError("Unresolved original reference-bearing XML entity")
        targets = []
        labels = []
        for el in root.iter():
            if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "reference":
                targets.append(el.get("osisRef", ""))
                labels.append("".join(el.itertext()))
        self._reference_labels_by_hash[digest] = labels
        # Literal original targets remain only in this private in-memory object,
        # not in logs, attached reports, test artifacts or source control.
        self._by_hash[digest] = (kind, key, targets)


    def triangulate_reversed_ranges_against_independent_witness(
            self, document, *, canonical_verses: set[str],
            native_section_spans: dict[str, tuple[int, ...]]) -> dict:
        """Triangulate original malformed range against a separately pinned XML.

        CCEL scripRef is a digital witness to the *same typo*, not proof of
        historical printed accuracy. A distinct source scripCom may suggest
        the intended endpoint. A native independently numbered heading is a
        separate third measurement, not an instruction to rewrite.
        """
        if not isinstance(document, (etree._ElementTree, etree._Element)):
            raise ValueError("Independent XML witness unavailable")
        if not isinstance(canonical_verses, set) or not canonical_verses:
            raise ValueError("No independent canonical verse registry")
        if not isinstance(native_section_spans, dict):
            raise ValueError("Original native section labels unavailable")
        source_ref_counts = Counter()
        source_com_counts = Counter()
        source_com_single_start_counts = Counter()
        source_ref_labels = defaultdict(list)
        root = document.getroot() if isinstance(document, etree._ElementTree) else document
        for element in root.iter():
            if not isinstance(element.tag, str):
                continue
            tag = element.tag.rsplit("}", 1)[-1]
            if tag not in ("scripRef", "scripCom"):
                continue
            value = element.get("osisRef", "")
            stripped = value[len("Bible:"):] if value.startswith("Bible:") else value
            if tag == "scripCom" and SINGLE_VERSE.fullmatch(stripped):
                source_com_single_start_counts[stripped] += 1
            endpoints = _unambiguous_verse_range_endpoints(value)
            if endpoints is None:
                continue
            if tag == "scripRef":
                source_ref_counts[endpoints] += 1
                source_ref_labels[endpoints].append("".join(element.itertext()))
            else:
                source_com_counts[endpoints] += 1
        cases = []
        for digest, (kind, key, targets) in self._by_hash.items():
            if digest not in self._reference_labels_by_hash:
                raise ValueError("Original source reference label not retained privately")
            labels = self._reference_labels_by_hash[digest]
            if len(labels) != len(targets):
                raise ValueError("Original link labels and targets lost correspondence")
            for target, original_label in zip(targets, labels):
                endpoints = _unambiguous_verse_range_endpoints(target)
                if endpoints is None:
                    continue
                first, last = endpoints
                if (first.rsplit(".", 1)[0] != last.rsplit(".", 1)[0]
                        or int(first.rsplit(".", 1)[1])
                           <= int(last.rsplit(".", 1)[1])):
                    continue
                chapter = first.rsplit(".", 1)[0]
                intended = []
                for (source_first, source_last), count in source_com_counts.items():
                    if (source_first == first and count >= 1
                            and source_first in canonical_verses
                            and source_last in canonical_verses
                            and source_last.rsplit(".", 1)[0] == chapter
                            and int(source_last.rsplit(".", 1)[1])
                                >= int(first.rsplit(".", 1)[1])):
                        intended.append((source_last, count))
                native_scope = native_section_spans.get(first)
                native_scope_exists = (
                    native_scope is not None and len(native_scope) >= 2
                    and native_scope[0] == int(first.rsplit(".", 1)[1]))
                expected_native_end = (
                    chapter + "." + str(native_scope[-1])
                    if native_scope_exists else None
                )
                # A source scripCom can mark just a start verse rather than
                # a whole authored range. Require a separate matching source
                # scripRef to corroborate its end in that representation.
                full_source_matches_native = (
                    expected_native_end is not None and
                    source_com_counts[(first, expected_native_end)] > 0
                )
                source_start_matches_native = (
                    expected_native_end is not None and
                    source_com_single_start_counts[first] > 0 and
                    source_ref_counts[(first, expected_native_end)] > 0
                )
                witness_bad = source_ref_counts[endpoints]
                label_match = any(
                    label.strip().casefold() == original_label.strip().casefold()
                    for label in source_ref_labels[endpoints]
                )
                numeric_label_match = any(
                    _literal_reference_label_reversed(label, first, last)
                    for label in source_ref_labels[endpoints]
                )
                # A digital witness may have only scripRef links, with no
                # scripCom authorial-range marker. This weaker concordance
                # still requires (a) the very same malformed digital citation
                # and numeric label, (b) another *valid* source range with
                # identical start, and (c) the independently indexed native
                # numbered section agreeing on its end. It only suggests a
                # candidate: scripRef is NOT an authorial section anchor.
                citation_and_native_concordance = (
                    native_scope_exists
                    and witness_bad > 0 and numeric_label_match
                    and _literal_reference_label_reversed(original_label, first, last)
                    and expected_native_end is not None
                    and source_ref_counts[(first, expected_native_end)] > 0
                )
                source_corresponding_count = (
                    1 if (full_source_matches_native
                          or source_start_matches_native
                          or citation_and_native_concordance) else 0
                )
                result = {
                    "original_native_entry": key,
                    "original_entry_kind": kind,
                    "native_original_target_is_reversed": True,
                    "original_link_display_text_contains_reversed_numeric_span":
                        _literal_reference_label_reversed(original_label, first, last),
                    "independent_source_same_bad_range_scripref_count": witness_bad,
                    "independent_source_same_display_label_literal_match": label_match,
                    "independent_source_same_reversed_numeric_label_present":
                        numeric_label_match,
                    "independent_source_full_range_scripcom_same_start_count":
                        sum(count for _, count in intended),
                    "independent_source_single_verse_scripcom_same_start_count":
                        source_com_single_start_counts[first],
                    "independent_source_valid_range_scripref_matching_native_count":
                        source_ref_counts[(first, expected_native_end)]
                        if expected_native_end is not None else 0,
                    "original_native_numbered_heading_at_range_start_exists":
                        native_scope_exists,
                    "original_native_numbered_heading_last_verse":
                        native_scope[-1] if native_scope_exists else None,
                    "independent_source_and_native_heading_matching_candidate_count":
                        source_corresponding_count,
                    "candidate_evidence_class": (
                        "INDEPENDENT_SCRIPCOM_FULL_RANGE_AND_ORIGINAL_NATIVE_HEADING"
                        if full_source_matches_native else
                        "INDEPENDENT_SCRIPCOM_START_AND_SCRIPREF_RANGE_WITH_NATIVE_HEADING"
                        if source_start_matches_native else
                        "TWO_INDEPENDENT_SCRIPREF_CITATIONS_AND_NATIVE_HEADING_NOT_SECTION_PROOF"
                        if citation_and_native_concordance else
                        "UNRESOLVED_SOURCE_NATIVE_CORROBORATION"
                    ),
                    "source_scripref_is_not_a_proven_authorial_section_anchor": True,
                    "candidate_end_verse_if_both_witnesses_agree":
                        native_scope[-1] if source_corresponding_count else None,
                    "original_source_target_or_label_exported": False,
                    "source_text_edited": False,
                    "editorial_approval": False,
                }
                cases.append(result)
        return {
            "status": "SOURCE_NATIVE_AND_INDEPENDENT_DIGITAL_REVERSED_REFERENCE_REVIEW_ONLY",
            "source_original_distinct_body_reversed_reference_count": len(cases),
            "case_rows": cases,
            "source_text_xml_or_original_reference_target_exported": False,
            "original_edition_changed": False,
            "print_edition_equivalence_proven": False,
            "correction_authorized": False,
            "release_authorized": False,
        }

    def report(self, *, canonical_verses: set[str],
               canonical_chapters: dict[str, int]) -> dict:
        if (not isinstance(canonical_verses, set)
                or not canonical_verses
                or not isinstance(canonical_chapters, dict)
                or not canonical_chapters):
            raise ValueError("Native SWORD reference-validation registry missing")
        counts = Counter()
        cases = defaultdict(list)
        all_refs = 0
        manual_classes = {
            "UNSAFE_OR_OVERSIZE_LITERAL_TARGET",
            "EMPTY_OR_MISSING_OSISREF_ATTRIBUTE",
            "SIMPLE_SINGLE_VERSE_NOT_IN_REGISTRY",
            "SIMPLE_VERSE_RANGE_ENDPOINT_NOT_IN_REGISTRY",
            "REVERSED_SAME_CHAPTER_VERSE_RANGE",
            "SIMPLE_CHAPTER_NOT_IN_REGISTRY",
        }
        for kind, location, targets in self._by_hash.values():
            for target in targets:
                all_refs += 1
                category = classify_original_reference_target(
                    target,
                    canonical_verses=canonical_verses,
                    canonical_chapters=canonical_chapters,
                )
                counts[category] += 1
                if category in manual_classes:
                    cases[category].append({
                        "original_entry_kind": kind,
                        "original_native_entry_locator": location,
                        "original_target_text_disclosed": False,
                    })
        return {
            "status": "FULL_ORIGINAL_NATIVE_REFERENCE_REGISTRY_TRIAGE_NOT_EDITORIAL_CORRECTION",
            "original_native_K_seen": self.native_count["K"],
            "original_native_I_seen": self.native_count["I"],
            "original_native_TOP_seen": self.native_count["U"],
            "original_distinct_K_I_payload_bodies": len(self._by_hash),
            "distinct_body_reference_elements_classified": all_refs,
            "reference_target_classes": dict(sorted(counts.items())),
            "manual_review_candidate_counts": {
                name: counts[name] for name in sorted(manual_classes) if counts[name]
            },
            "manual_review_samples": {
                name: rows[:MAX_CANDIDATE_ROWS] for name, rows in sorted(cases.items())
            },
            "manual_review_unlisted_counts": {
                name: max(0, len(rows) - MAX_CANDIDATE_ROWS)
                for name, rows in sorted(cases.items())
            },
            "complex_target_not_classified_as_error": True,
            "in_range_reference_correctness_is_not_semantically_proven": True,
            "original_reference_targets_or_prose_exported": False,
            "original_reference_targets_or_prose_changed": False,
            "publication_authorized": False,
        }
