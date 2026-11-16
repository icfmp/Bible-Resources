#!/usr/bin/env python3
"""Source-neutral, read-only commentary layout census.

A digital witness is not automatically the editorial master. This census
identifies possible unreadable/mis-encoded paragraphs or headings across an
entire native SWORD commentary. It NEVER claims that an observation is an
authorial mistake and NEVER proposes or applies rewriting.

Only counts and bounded original *native addresses* leave the in-memory
reader. Original words, original markup, references and XML attributes do
not appear in the receipt. Shared SWORD aliases are measured once per exact
raw body, so one long authored section is never counted as many defects.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

KEY = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*\.[1-9]\d*$")
INTRO = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.[1-9]\d*)?$")
VERSE_LEAD = re.compile(r"^\s*Verses?\s+\d{1,3}(?:\s*[-–,]\s*\d{1,3})*", re.I)
WORD = re.compile(r"\w+", re.UNICODE)
MAX_BODY = 2 * 1024 * 1024
MAX_BODIES = 40000
MAX_KEYS = 160000
MAX_SAMPLES = 30

# These are markup structures, *not* a new inferred editorial layout.
PARAGRAPH = {"p", "l", "lg", "lb", "br"}
HEADING = {"title", "head", "h1", "h2", "h3", "h4", "h5", "h6"}
TEXT_CONTAINERS = {"p", "l", "title", "head", "h1", "h2", "h3", "h4", "h5", "h6", "note"}


def _strict_fragment(raw: bytes):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BODY or b"\x00" in raw:
        raise ValueError("Unsafe original commentary source fragment")
    try:
        root = etree.fromstring(b"<entry>" + raw + b"</entry>",
                                parser=etree.XMLParser(
                                    resolve_entities=False, no_network=True,
                                    load_dtd=False, huge_tree=False,
                                    recover=False, remove_blank_text=False))
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original commentary layout XML is unparseable") from None
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise ValueError("Unresolved original commentary XML entity")
    return root


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def layout_profile(raw: bytes) -> dict:
    """Return only structural counts/classes; no original source text or XML."""
    root = _strict_fragment(raw)
    counts = Counter()
    words_in_unwrapped_segments = 0
    max_unwrapped_words = 0
    text_word_total = 0
    paragraph_lengths = []
    empty_paragraphs = 0
    empty_headings = 0

    def visit(node, ancestors):
        nonlocal words_in_unwrapped_segments, max_unwrapped_words, text_word_total
        local = _local(node.tag)
        if node is not root:
            counts[local] += 1
            if local in {"p", "l"}:
                own_text = "".join(node.itertext())
                n = len(WORD.findall(own_text))
                paragraph_lengths.append(n)
                if not n:
                    nonlocal_empty[0] += 1
            if local in HEADING and not WORD.search("".join(node.itertext())):
                nonlocal_empty[1] += 1
        current = ancestors | ({local} if node is not root else set())
        add(node.text, current)
        for child in node:
            if isinstance(child.tag, str):
                visit(child, current)
            # Child tail belongs to the *parent*, not the child node.
            add(child.tail, current)

    nonlocal_empty = [0, 0]

    def add(value, ancestors):
        nonlocal words_in_unwrapped_segments, max_unwrapped_words, text_word_total
        if not value:
            return
        n = len(WORD.findall(value))
        text_word_total += n
        if n and not (ancestors & TEXT_CONTAINERS):
            words_in_unwrapped_segments += n
            max_unwrapped_words = max(max_unwrapped_words, n)

    visit(root, set())
    empty_paragraphs, empty_headings = nonlocal_empty
    # Word totals are measured on original XML .text/.tail fragments,
    # without double-counting nested markup. Flat itertext() may join a
    # title directly to the next paragraph with no intervening XML space,
    # so its apparent lexical token count is NOT an identity invariant.
    visible = "".join(root.itertext())
    leading = visible.lstrip()
    styled_verse_lead = any(
        (label := "".join(node.itertext()).strip())
        and VERSE_LEAD.match(label)
        and leading.startswith(label)
        for node in root.iter()
        if isinstance(node.tag, str) and _local(node.tag) == "hi"
    )
    if sum(counts.values()) > 100000:
        raise ValueError("Unbounded original layout element count")
    paragraphs = counts["p"] + counts["l"]
    return {
        "word_count": text_word_total,
        "paragraph_count": paragraphs,
        "p_count": counts["p"],
        "poetry_line_count": counts["l"],
        "line_break_count": counts["lb"] + counts["br"],
        "heading_count": sum(counts[tag] for tag in HEADING),
        "reference_count": counts["reference"],
        "div_count": counts["div"],
        "table_count": counts["table"],
        "row_count": counts["row"],
        "cell_count": counts["cell"],
        "hi_count": counts["hi"],
        "milestone_count": counts["milestone"],
        "styled_numbered_verse_lead": bool(styled_verse_lead),
        "unwrapped_word_count": words_in_unwrapped_segments,
        "max_unwrapped_segment_words": max_unwrapped_words,
        "longest_paragraph_words": max(paragraph_lengths, default=0),
        "empty_paragraphs": empty_paragraphs,
        "empty_headings": empty_headings,
        "visible_numbered_verse_lead": bool(VERSE_LEAD.match(visible)),
    }


def layout_flags(profile: dict) -> set[str]:
    """Review candidates only. Thresholds are explicitly heuristic."""
    word_count = profile["word_count"]
    paras = profile["paragraph_count"]
    breaks = profile["line_break_count"]
    flags = set()
    # <div> and <table> may already provide the source's meaningful
    # blocks. A naive "no <p> = broken layout" verdict would be wrong.
    # Even a single <div> is allowed as a general wrapper; only a long
    # body with no *internal* structural divisions needs first review.
    if (word_count >= 250 and paras == 0 and breaks == 0
            and profile["div_count"] <= 1 and profile["table_count"] == 0):
        flags.add("long_prose_without_internal_block_markup")
    if word_count >= 300 and paras == 1 and profile["longest_paragraph_words"] >= 250:
        flags.add("long_single_paragraph")
    if (profile["unwrapped_word_count"] >= 80
            and profile["div_count"] == 0 and profile["table_count"] == 0):
        flags.add("substantial_text_without_div_table_p_line_title_note")
    if profile["empty_paragraphs"]:
        flags.add("empty_paragraph_or_poetry_line")
    if profile["empty_headings"]:
        flags.add("empty_heading_markup")
    if (profile["visible_numbered_verse_lead"] and profile["heading_count"] == 0
            and not profile["styled_numbered_verse_lead"]):
        flags.add("visible_verse_lead_without_title_or_hi_markup")
    return flags


class NativeCommentaryLayoutCensus:
    """Stream K/I/TOP records; deduplicate authored raw bodies safely."""

    def __init__(self):
        self.unique = {}
        self.keys = Counter()
        self.chapter_keys = defaultdict(list)
        self.aliases = 0

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        if kind == "U":
            self.keys["U"] += 1
            return
        if kind not in ("K", "I") or (not KEY.fullmatch(key) if kind == "K"
                                  else not INTRO.fullmatch(key)):
            raise ValueError("Malformed commentary native layout key")
        self.keys[kind] += 1
        if self.keys[kind] > MAX_KEYS:
            raise ValueError("Unbounded original native commentary entries")
        if kind == "K":
            self.chapter_keys[key.rsplit(".", 1)[0]].append(key)
        digest = (kind, sha256(raw).hexdigest())
        if digest not in self.unique:
            if len(self.unique) >= MAX_BODIES:
                raise ValueError("Unbounded distinct original commentary layout bodies")
            self.unique[digest] = {"kind": kind, "key": key,
                                   "profile": layout_profile(raw)}
        else:
            # A native K alias shares an authored body, but a structurally
            # different I/K slot is never collapsed across entry kinds.
            self.aliases += 1

    def report(self) -> dict:
        categories = Counter()
        cases = defaultdict(list)
        histogram = Counter()
        original_verse_one_chapters = set()
        for chapter, keys in self.chapter_keys.items():
            if len(keys) == 1 and keys[0].endswith(".1"):
                original_verse_one_chapters.add(chapter)
        chapter_one_profiles = Counter()
        for entry in self.unique.values():
            kind = entry["kind"]
            key = entry["key"]
            profile = entry["profile"]
            flags = layout_flags(profile)
            histogram[f"{kind}_paragraphs_{'0' if profile['paragraph_count']==0 else '1' if profile['paragraph_count']==1 else '2plus'}"] += 1
            histogram[f"{kind}_words_{'0' if profile['word_count']==0 else '1-99' if profile['word_count']<100 else '100-249' if profile['word_count']<250 else '250-499' if profile['word_count']<500 else '500plus'}"] += 1
            histogram[f"{kind}_visible_numbered_verse_lead"] += int(profile["visible_numbered_verse_lead"])
            histogram[f"{kind}_styled_numbered_verse_lead"] += int(profile["styled_numbered_verse_lead"])
            histogram[f"{kind}_divs_{'0' if profile['div_count']==0 else '1' if profile['div_count']==1 else '2plus'}"] += 1
            histogram[f"{kind}_tables_present"] += int(profile["table_count"] > 0)
            histogram[f"{kind}_hi_present"] += int(profile["hi_count"] > 0)
            histogram[f"{kind}_linebreaks_present"] += int(profile["line_break_count"] > 0)
            if kind == "K" and key.rsplit(".", 1)[0] in original_verse_one_chapters:
                chapter_one_profiles[f"single_key_chapter_paragraphs_{'0' if profile['paragraph_count']==0 else '1' if profile['paragraph_count']==1 else '2plus'}"] += 1
                chapter_one_profiles["single_key_chapter_raw_body_count"] += 1
            for flag in sorted(flags):
                categories[f"{kind}_{flag}"] += 1
                cases[flag].append((profile["word_count"], key, kind,
                                    profile["paragraph_count"],
                                    profile["unwrapped_word_count"]))
        samples = {}
        for flag, vals in sorted(cases.items()):
            # Native keys and counts only: never a literal source string.
            values = sorted(vals, key=lambda x: (-x[0], x[1]))[:MAX_SAMPLES]
            samples[flag] = [{"original_native_key": key, "entry_kind": kind,
                              "word_count": words, "paragraph_count": paras,
                              "unwrapped_words": loose}
                             for words, key, kind, paras, loose in values]
        return {
            "status": "COMPLETE_ORIGINAL_COMMENTARY_LAYOUT_HEURISTICS_NOT_EDITORIAL_VERDICT",
            "original_native_K_seen": self.keys["K"],
            "original_native_I_seen": self.keys["I"],
            "original_native_TOP_seen": self.keys["U"],
            "distinct_original_raw_bodies": len(self.unique),
            "repeated_raw_native_aliases": self.aliases,
            "distribution": dict(sorted(histogram.items())),
            "original_verse_one_only_chapters": len(original_verse_one_chapters),
            "single_key_chapter_structure": dict(sorted(chapter_one_profiles.items())),
            "candidate_counts": dict(sorted(categories.items())),
            "candidate_samples": samples,
            "candidate_sample_overflow": {flag: max(0, len(cases[flag])-MAX_SAMPLES)
                                          for flag in sorted(cases)},
            "source_word_text_xml_and_targets_disclosed": False,
            "all_cases_are_unapproved_diagnostic_only": True,
            "original_module_modified": False,
            "publication_authorized": False,
        }
