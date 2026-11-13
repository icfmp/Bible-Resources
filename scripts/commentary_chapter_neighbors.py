#!/usr/bin/env python3
"""Private, source-neutral ThML chapter-marker ↔ native intro witness.

This measures only the text in the immediate *original source sibling* after
each explicit chapter scripCom marker. It cannot certify an entire authorial
chapter introduction, an edition, structure or a SWORD module's faithfulness.
Neither original source text nor original compiled entry bytes are reported.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re

from lxml import etree

from commentary_text_delta import _contiguous_offset
from commentary_xml_witness import _parse_reference, WORK_REF
from pilot_preflight import PilotError

MAX_MARKERS = 20000
MAX_SIBLING_CHARS = 2 * 1024 * 1024


def original_chapter_neighbors(xml_bytes: bytes) -> tuple[dict, dict]:
    """Extract explicitly marked chapter-neighbor units, never infer books."""
    try:
        root = etree.fromstring(xml_bytes, parser=etree.XMLParser(
            resolve_entities=False, no_network=True, load_dtd=False,
            recover=False, huge_tree=False, remove_blank_text=False,
        ))
    except (ValueError, etree.XMLSyntaxError):
        raise PilotError("Original chapter source XML cannot be parsed safely") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise PilotError("Unresolved original XML entities block chapter comparison")
    observed = {}
    tag_counts = Counter()
    ordered = sha256()
    count = 0
    for node in root.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "scripCom":
            continue
        original_ref = node.get("osisRef", "")
        kind, _book = _parse_reference(original_ref)
        if kind != "work_qualified_chapter":
            continue
        count += 1
        if count > MAX_MARKERS:
            raise PilotError("Original chapter marker count exceeds safe bounds")
        match = WORK_REF.fullmatch(original_ref)
        if not match:
            raise PilotError("Original chapter marker no longer has reviewed syntax")
        key = match.group(2)
        sibling = node.getnext()
        tag = (sibling.tag.rsplit("}", 1)[-1]
               if sibling is not None and isinstance(sibling.tag, str) else "")
        if tag not in {"h2", "p"}:
            raise PilotError("Original chapter marker has an unreviewed next sibling")
        if node.tail and node.tail.strip():
            raise PilotError("Original chapter marker has intervening unassigned text")
        body = "".join(sibling.itertext())
        if not body.strip() or len(body) > MAX_SIBLING_CHARS:
            raise PilotError("Original chapter sibling text empty or oversized")
        original_bytes = body.encode("utf-8")
        ref_bytes = original_ref.encode("utf-8")
        ordered.update(len(ref_bytes).to_bytes(4, "big") + ref_bytes)
        ordered.update(tag.encode("ascii") + b"\0" + sha256(original_bytes).digest())
        observed.setdefault(key, []).append({"tag": tag, "text": body})
        tag_counts[tag] += 1
    return observed, {
        "explicit_chapter_source_marker_count": count,
        "distinct_explicit_chapter_source_start_keys": len(observed),
        "original_chapter_adjacent_sibling_tag_counts": dict(sorted(tag_counts.items())),
        "original_chapter_sibling_ordered_sha256": ordered.hexdigest(),
        "source_marker_to_adjacent_element_is_not_entire_chapter_unit": True,
    }


def compare_chapter_neighbors(source: dict, stocked_intros: dict,
                              decode_raw) -> dict:
    """Compare exact known intro positions, reporting only bounded classes."""
    outcomes = Counter()
    source_tags = Counter()
    evaluated = 0
    for key, items in source.items():
        # Exact native intro references win only when unambiguous.
        candidates = [x for x in (key, key + ".0") if x in stocked_intros]
        for item in items:
            evaluated += 1
            tag, text = item["tag"], item["text"]
            if tag not in {"h2", "p"} or not text.strip():
                raise PilotError("Unreviewed or empty chapter sibling")
            source_tags[tag] += 1
            if not candidates:
                category = "no_native_intro_at_explicit_source_key"
            elif len(candidates) > 1:
                category = "ambiguous_two_occupied_intro_key_spellings"
            else:
                native = decode_raw(stocked_intros[candidates[0]])
                if native is None:
                    category = "stock_intro_raw_xml_not_strictly_parseable"
                elif native == text:
                    category = "exact_unicode_text"
                elif native.strip() == text.strip():
                    category = "only_outer_whitespace_differs"
                elif text in native:
                    category = "original_sibling_exact_substring_of_stock_intro"
                else:
                    source_words = re.findall(r"\w+", text)
                    stock_words = re.findall(r"\w+", native)
                    if source_words and source_words == stock_words:
                        category = "same_unicode_word_tokens_nonword_characters_differ"
                    elif source_words and _contiguous_offset(source_words, stock_words) is not None:
                        category = "source_words_contiguous_inside_larger_stock_intro"
                    else:
                        category = "different_text_or_selection_requires_review"
            outcomes[category] += 1
    if sum(outcomes.values()) != sum(map(len, source.values())) or evaluated == 0:
        raise PilotError("Original chapter source marker comparison incomplete")
    if sum(source_tags.values()) != evaluated:
        raise PilotError("Original chapter sibling tag accounting incomplete")
    return {
        "original_chapter_source_siblings_compared": evaluated,
        "source_chapter_sibling_tags": dict(sorted(source_tags.items())),
        "source_chapter_sibling_to_occupied_native_intro_classes":
            dict(sorted(outcomes.items())),
        "full_original_chapter_body_compared": False,
        "unmarked_source_divisions_compared": False,
        "chapter_source_neighbor_matching_does_not_prove_intro_content_or_layout_parity": True,
        "no_original_text_or_raw_stock_xml_in_report": True,
    }


class ChapterNeighborNumberedProbe:
    """Bounded read-only search at independently observed SAME-CHAPTER K keys.

    Finds possible text location only. A K slot can repeat another range entry,
    and neither containment nor word order establishes authorial provenance.
    """

    def __init__(self, source: dict):
        self.units_by_chapter = {}
        self.marker_units = []
        for chapter, items in source.items():
            units = []
            for item in items:
                original = item["text"]
                words = re.findall(r"\w+", original)
                state = {"text": original, "words": words, "exact": False,
                         "words_found": False, "stock_numbered_keys": 0}
                units.append(state)
                self.marker_units.append(state)
            self.units_by_chapter[chapter] = units
        self.chapter_numbered_keys = Counter()
        self.strict_xml_parse_failures = 0
        self.numbered_entries_scanned = 0

    def observe(self, kind: str, key: str, raw: bytes, decode_raw) -> None:
        if kind != "K":
            return
        chapter_key = key.rsplit(".", 1)[0]
        items = self.units_by_chapter.get(chapter_key)
        if not items:
            return
        self.numbered_entries_scanned += 1
        self.chapter_numbered_keys[chapter_key] += 1
        native_text = decode_raw(raw)
        if native_text is None:
            self.strict_xml_parse_failures += 1
            return
        native_words = None
        for item in items:
            item["stock_numbered_keys"] += 1
            if item["text"] in native_text:
                item["exact"] = True
                item["words_found"] = True
                continue
            if item["words"] and not item["words_found"]:
                if native_words is None:
                    native_words = re.findall(r"\w+", native_text)
                if _contiguous_offset(item["words"], native_words) is not None:
                    item["words_found"] = True

    def report(self) -> dict:
        if not self.marker_units or self.numbered_entries_scanned == 0:
            raise PilotError("Chapter numbered-slot witness lacks source or stock coverage")
        outcome = Counter()
        for item in self.marker_units:
            if item["exact"]:
                outcome["original_sibling_exact_unicode_contained_in_same_chapter_numbered_slot"] += 1
            elif item["words_found"]:
                outcome["original_sibling_word_tokens_contiguous_in_same_chapter_numbered_slot"] += 1
            elif item["stock_numbered_keys"]:
                outcome["original_sibling_not_found_in_same_chapter_numbered_slots"] += 1
            else:
                outcome["no_strictly_parsed_same_chapter_numbered_slot"] += 1
        if sum(outcome.values()) != len(self.marker_units):
            raise PilotError("Same-chapter stock text location audit lost original chapter markers")
        return {
            "original_chapter_source_markers_evaluated": len(self.marker_units),
            "same_chapter_numbered_stock_slots_scanned": self.numbered_entries_scanned,
            "explicit_chapter_keys_with_any_numbered_stock_slot":
                len(self.chapter_numbered_keys),
            "strict_xml_unparseable_stock_numbered_slots": self.strict_xml_parse_failures,
            "source_sibling_location_in_original_stock_same_chapter_numbered_slots":
                dict(sorted(outcome.items())),
            "word_contiguity_is_not_unicode_punctuation_or_markup_parity": True,
            "numbered_slots_may_repeat_same_range_comment": True,
            "no_original_text_or_sword_entry_bytes_reported": True,
            "no_chapter_or_book_attribution_invented": True,
            "full_source_to_stock_chapter_section_parity_verified": False,
        }
