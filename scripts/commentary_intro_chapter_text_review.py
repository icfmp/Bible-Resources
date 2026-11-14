#!/usr/bin/env python3
"""Source-neutral read-only intro-vs-numbered-commentary text location audit.

Never transforms, publishes, copies into a report or silently reallocates a
single word of the original introduction. Original libSWORD I and K frames
are always from a pinned independent complete native source scan.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re

from lxml import etree

MAX_RAW_BYTES = 2 * 1024 * 1024
MAX_CHAPTER_NUMBERED_BODIES = 256
WORD = re.compile(r"\w+", re.UNICODE)


def _original(raw: bytes):
    if not isinstance(raw, bytes) or len(raw) > MAX_RAW_BYTES or b"\x00" in raw:
        raise ValueError("Invalid original intro/commentary text")
    try:
        root = etree.fromstring(
            b"<entry>" + raw + b"</entry>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False
            )
        )
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original native entry is not strict XML") from None
    if any(isinstance(el, etree._Entity) for el in root.iter()):
        raise ValueError("Unresolved original XML entity")
    return root


def _visible(root):
    return "".join(root.itertext())


def _normal(value):
    return " ".join(value.casefold().split())


def review_original_intro_against_numbered_chapter(
        intro_key: str, intro_raw: bytes,
        occupied_numbered: list[tuple[str, bytes]]) -> dict:
    """Compare original visible intro spans with same-chapter K bodies.

    Preserves I/K separation. Matches only exact normalized Unicode sequences
    for feasibility diagnostics; cannot decide that copying/deleting a body
    would be an editorial correction.
    """
    if (not isinstance(intro_key, str)
            or re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", intro_key) is None
            or not isinstance(occupied_numbered, list)
            or len(occupied_numbered) > MAX_CHAPTER_NUMBERED_BODIES):
        raise ValueError("Unreviewed original chapter introduction comparison")
    root = _original(intro_raw)
    intro_text = _normal(_visible(root))
    if not intro_text:
        raise ValueError("No visible text to locate in original introduction")
    seen = set()
    bodies = {}
    for key, raw in occupied_numbered:
        if (not isinstance(key, str) or not key.startswith(intro_key + ".")
                or re.fullmatch(re.escape(intro_key) + r"\.[1-9]\d*", key) is None
                or key in seen):
            raise ValueError("Numbered body not independently in intro chapter")
        seen.add(key)
        digest = sha256(raw).hexdigest()
        if digest not in bodies:
            bodies[digest] = _normal(_visible(_original(raw)))
    originals = list(bodies.values())
    full_intro_in_K = any(intro_text in stock for stock in originals)
    full_K_in_intro = sum(bool(stock) and stock in intro_text for stock in originals)
    runs = []
    for child in root.iter():
        if child is root:
            continue
        local = (child.tag.rsplit("}", 1)[-1]
                 if isinstance(child.tag, str) else "_non_element")
        for location, text in (("text", child.text), ("tail", child.tail)):
            if text and WORD.search(text):
                words = WORD.findall(text)
                if len(words) >= 3:
                    normalized = _normal(text)
                    runs.append((local, location, len(words), normalized))
    matched_runs = [row for row in runs if any(row[3] in stock for stock in originals)]
    not_matched = [row for row in runs if row not in matched_runs]
    # A source intro may have original editorial text unwrapped in a title,
    # as well as commentary prose in a tail. Both must remain at the I key
    # unless a separately reviewed source attribution proves otherwise.
    return {
        "status": "ORIGINAL_INTRO_TEXT_COVERAGE_NOT_AUTHORIAL_ATTRIBUTION",
        "original_native_intro_key": intro_key,
        "numbered_keys_present_in_original_chapter": len(occupied_numbered),
        "distinct_numbered_raw_bodies_in_original_chapter": len(bodies),
        "original_intro_unicode_word_count": len(WORD.findall(_visible(root))),
        "full_original_intro_visible_text_in_a_numbered_body": full_intro_in_K,
        "numbered_bodies_contained_wholly_inside_intro": full_K_in_intro,
        "original_intro_text_runs_of_at_least_three_words": len(runs),
        "runs_exactly_repeated_in_numbered_body": len(matched_runs),
        "runs_not_exactly_repeated_in_numbered_body": len(not_matched),
        "words_in_original_intro_runs_not_exactly_matched":
            sum(row[2] for row in not_matched),
        "unmatched_intro_text_owning_element_classes":
            dict(sorted(Counter(
                f"{tag}_{location}" for tag, location, _, _ in not_matched
            ).items())),
        "original_intro_text_deleted_or_reassigned": False,
        "original_full_chapter_commentary_coverage_proven": False,
        "source_or_candidate_published": False,
    }
