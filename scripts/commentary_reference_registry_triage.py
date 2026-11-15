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


class OriginalCommentaryReferenceRegistryTriage:
    """Source-neutral exact native K/I XML observer, never a correction engine."""

    def __init__(self):
        self._by_hash = {}
        self.native_count = Counter()

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
        for el in root.iter():
            if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "reference":
                targets.append(el.get("osisRef", ""))
        # Literal original targets remain only in this private in-memory object,
        # not in logs, attached reports, test artifacts or source control.
        self._by_hash[digest] = (kind, key, targets)

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
