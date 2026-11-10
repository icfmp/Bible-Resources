#!/usr/bin/env python3
"""Bounded metadata-only triage of real source vs SWORD whitespace at p/q boundaries.

This classifies differences in *original source verse text* versus actual
stock SWORD verse text at non-whitespace character gaps, using the separately
proved source structural p/q starts/ends as coordinates. It does NOT certify
that any newline is deliberate poetry, that spaces were preserved, or that
native layout visually renders the author's intent. Neither source/native
prose nor actual whitespace sequences leave private memory.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json

from stable_sword_refs import KEY

MAX_SAMPLES = 24
MAX_SAMPLES_PER_CATEGORY = 3


class StructuralWhitespaceError(ValueError):
    """Original/native whitespace cannot be safely compared in this scope."""


def _runs_by_nonspace_offset(text: str) -> tuple[str, dict[int, str]]:
    if not isinstance(text, str):
        raise StructuralWhitespaceError("Untrusted source/native verse content")
    content = []
    gaps = defaultdict(list)
    count = 0
    for character in text:
        if character.isspace():
            gaps[count].append(character)
        else:
            content.append(character)
            count += 1
    return "".join(content), {key:"".join(items) for key,items in gaps.items()}


def _type_of_gap(source: str, native: str) -> str:
    """Descriptive only: normalization is never an automatic correction."""
    original_lf = any(c in source for c in "\r\n\u2028\u2029")
    compiled_lf = any(c in native for c in "\r\n\u2028\u2029")
    if original_lf and not compiled_lf:
        return "source_newline_not_present_in_compiled_verse_text"
    if compiled_lf and not original_lf:
        return "compiled_newline_not_present_in_source_verse_text"
    if original_lf and compiled_lf:
        return "both_have_newline_but_whitespace_run_differs"
    if not source and native:
        return "only_compiled_has_whitespace_run"
    if source and not native:
        return "only_source_has_whitespace_run"
    return "spacing_or_unicode_space_run_differs"


def _structural_category(positions: set[str]) -> str:
    if "q_open" in positions:
        return "at_original_poetry_line_opening"
    if "p_open" in positions:
        return "at_original_paragraph_opening"
    if "q_close" in positions:
        return "at_original_poetry_line_closing"
    if "p_close" in positions:
        return "at_original_paragraph_closing"
    return "without_original_p_q_marker_at_that_character_boundary"


class MainTextStructuralWhitespaceTriage:
    """Streaming verse analyzer; no full compiled Bible stored or exposed."""

    def __init__(self, source_verses: dict[str, str], source_boundaries: dict):
        if not source_verses or not source_boundaries:
            raise StructuralWhitespaceError("Missing original indexed source or p/q evidence")
        self._source = source_verses
        self._seen = set()
        self._ranges = {}
        self._positions = defaultdict(lambda: defaultdict(set))
        self._counts = Counter()
        self._category_samples = defaultdict(list)
        self._fingerprint = sha256()
        book_offsets = Counter()
        book_last = {}
        for ref, text in source_verses.items():
            match = KEY.fullmatch(ref)
            if match is None or not isinstance(text, str):
                raise StructuralWhitespaceError("Untrusted authored source index")
            book = match.group(1)
            key = (int(match.group(2)), int(match.group(3)))
            if key <= book_last.get(book, (0, 0)):
                raise StructuralWhitespaceError("Authored verse entries are not in book order")
            book_last[book] = key
            start = book_offsets[book]
            characters, _gaps = _runs_by_nonspace_offset(text)
            book_offsets[book] += len(characters)
            self._ranges[ref] = (book, start, len(characters))
        if set(book_offsets) != set(source_boundaries):
            raise StructuralWhitespaceError("Original structure and text book sets differ")
        for book,(words,events) in source_boundaries.items():
            if not isinstance(words,list) or not isinstance(events,list):
                raise StructuralWhitespaceError("Untrusted authorial source structural receipt")
            for event in events:
                kind = event.get("kind")
                if kind not in {"p","q"}:
                    raise StructuralWhitespaceError("Unsupported original structural event")
                for endpoint in ("open","close"):
                    point = event.get(endpoint)
                    if not isinstance(point, dict):
                        raise StructuralWhitespaceError("Missing original opening/closing boundary")
                    number = point.get("nonwhitespace_codepoint_ordinal")
                    if (type(number) is not int or number < 0
                            or number > book_offsets[book]):
                        raise StructuralWhitespaceError("Invalid original punctuation-relative coordinate")
                    self._positions[book][number].add(f"{kind}_{endpoint}")

    def observe(self, ref: str, native_verse_text: str) -> None:
        if ref not in self._source or ref in self._seen:
            raise StructuralWhitespaceError("Missing, duplicate or unmapped original/native verse")
        self._seen.add(ref)
        book, start, length = self._ranges[ref]
        original_content, authored_gaps = _runs_by_nonspace_offset(self._source[ref])
        compiled_content, compiled_gaps = _runs_by_nonspace_offset(native_verse_text)
        if original_content != compiled_content or length != len(compiled_content):
            self._counts["verses_with_nonwhitespace_difference_blocking_layout_triage"] += 1
            return
        self._counts["indexed_verses_checked"] += 1
        changed = False
        for position in sorted(set(authored_gaps) | set(compiled_gaps)):
            before = authored_gaps.get(position, "")
            after = compiled_gaps.get(position, "")
            if before == after:
                continue
            changed = True
            self._counts["changed_whitespace_runs"] += 1
            global_ordinal = start + position
            positions = self._positions[book].get(global_ordinal,set())
            structure = _structural_category(positions)
            layout = _type_of_gap(before, after)
            scope = ("verse_start" if position == 0
                     else "verse_end" if position == length
                     else "verse_internal")
            self._counts[f"structure_{structure}"] += 1
            self._counts[f"change_{layout}"] += 1
            self._counts[f"scope_{scope}"] += 1
            if "q_open" in positions:
                self._counts["changed_runs_touching_source_q_open"] += 1
            if "p_open" in positions:
                self._counts["changed_runs_touching_source_p_open"] += 1
            if layout == "source_newline_not_present_in_compiled_verse_text":
                self._counts["source_newline_runs_absent_in_native_verse_text"] += 1
                if "q_open" in positions:
                    self._counts["source_newline_absent_at_q_open_candidate"] += 1
                elif not positions:
                    self._counts["source_newline_absent_without_p_q_marker_review"] += 1
            payload = json.dumps(
                [ref,position,structure,layout,scope],
                ensure_ascii=True,separators=(",",":")).encode()
            self._fingerprint.update(len(payload).to_bytes(4,"big")+payload)
            label = f"{structure}:{layout}:{scope}"
            if (len(self._category_samples[label]) < MAX_SAMPLES_PER_CATEGORY
                    and sum(map(len,self._category_samples.values())) < MAX_SAMPLES):
                self._category_samples[label].append({
                    "reference":ref,
                    "original_verse_nonspace_codepoint_gap":position,
                    "original_book_nonspace_codepoint_gap":global_ordinal,
                    "structure_at_gap":structure,
                    "change_category":layout,
                    "record_boundary":scope,
                })
        if changed:
            self._counts["numbered_verses_with_whitespace_differences"] += 1
        else:
            self._counts["numbered_verses_with_exact_source_native_whitespace"] += 1

    def finish(self) -> dict:
        if self._seen != set(self._source):
            raise StructuralWhitespaceError("Incomplete original/native numbered verse coverage")
        self._counts.setdefault("verses_with_nonwhitespace_difference_blocking_layout_triage",0)
        self._counts.setdefault("changed_whitespace_runs",0)
        self._counts.setdefault("source_newline_runs_absent_in_native_verse_text",0)
        self._counts.setdefault("source_newline_absent_without_p_q_marker_review",0)
        return {
            "schema_version":1,
            "status": ("whitespace_differences_classified_not_editorially_approved"
                       if not self._counts["verses_with_nonwhitespace_difference_blocking_layout_triage"]
                       else "blocked_nonwhitespace_source_native_text_difference"),
            "source_native_original_whitespace_gap_counts":dict(sorted(self._counts.items())),
            "first_whitespace_gap_metadata_references_only":[
                row for label in sorted(self._category_samples)
                for row in self._category_samples[label]][:MAX_SAMPLES],
            "whitespace_gap_classification_sha256":self._fingerprint.hexdigest(),
            "source_original_newline_provenance_vs_xml_serialization_unverified":True,
            "native_poetry_milestone_semantics_are_independent_of_raw_newlines":True,
            "matching_p_q_nonspace_anchor_is_prerequisite_not_full_whitespace_parity":True,
            "source_native_original_whitespace_layout_verified":False,
            "no_bible_text_note_content_or_raw_whitespace_in_report":True,
            "originals_unchanged_and_publication_not_approved":True,
        }
