#!/usr/bin/env python3
"""Read-only native commentary editorial topology triage, source-neutral.

Independently of source-witness heading heuristics, cross-check numeric XML
titles, occupied native verse locations and reused exact raw payload bodies.
A shared block, suspicious title or disjoint reuse is an observation, NEVER
proof of an editorial mistake or authorization to add/merge SWORD aliases.

Only fixed-class counters, native verse references and bounded integers leave
the private original SWORD runner. No original prose, title string, XML,
authorial annotation attribute or source fragment is emitted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

VERSE_KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\\.([1-9]\\d*)\\.([1-9]\\d*)$")
# Numeric XML title starts are stronger *location* evidence than citations
# found anywhere in the full visible prose. Still not authorial scope approval.
TITLE_NUMBERS = re.compile(
    r"^\\s*Verses?\\s+(\\d{1,3}(?:\\s*[-–,]\\s*\\d{1,3}){0,8})(?!\\d)",
    flags=re.IGNORECASE,
)
MAX_RAW = 2 * 1024 * 1024
MAX_CASES_PER_CLASS = 80
MAX_UNIQUE_BODIES = 40000
MAX_OCCUPIED_K = 150000


def _heading_span(value: str) -> tuple[int, ...] | None:
    match = TITLE_NUMBERS.match(value)
    if not match:
        return None
    literal = match.group(1)
    parts = []
    for portion in literal.split(","):
        m = re.fullmatch(r"\\s*(\\d{1,3})(?:\\s*[-–]\\s*(\\d{1,3}))?\\s*", portion)
        if m is None:
            return None
        start = int(m.group(1))
        stop = int(m.group(2) or start)
        if start <= 0 or stop < start or stop > 176:
            return None
        parts.extend(range(start, stop + 1))
    if not parts or parts != sorted(set(parts)):
        return None
    return tuple(parts)


class NativeCommentaryEditorialTopology:
    """Observe exact original K bodies once; report suspicious topology.

    By design no authorial text is stored after parsing an entry. Native key
    addresses alone identify review cases, not claimed mistakes.
    """

    def __init__(self):
        self.bodies = {}
        self.occupied = defaultdict(lambda: defaultdict(list))
        self.nonopaque_count = 0
        self.numbered_count = 0
        self.original_I_count = 0
        self.original_U_count = 0
        self.unique_titles = Counter()

    def observe(self, kind: str, key: str, raw: bytes):
        if kind == "U":
            self.original_U_count += 1
            return
        if kind == "I":
            self.original_I_count += 1
            return
        m = VERSE_KEY.fullmatch(key) if isinstance(key, str) else None
        if (kind != "K" or m is None or not isinstance(raw, bytes)
                or len(raw) > MAX_RAW or b"\\x00" in raw
                or self.numbered_count >= MAX_OCCUPIED_K):
            raise ValueError("Untrusted native commentary topology input")
        self.numbered_count += 1
        chapter = f"{m.group(1)}.{m.group(2)}"
        verse = int(m.group(3))
        digest = sha256(raw).hexdigest()
        profile = self.bodies.get(digest)
        if profile is None:
            if len(self.bodies) >= MAX_UNIQUE_BODIES:
                raise ValueError("Unbounded distinct original commentary bodies")
            try:
                root = etree.fromstring(
                    b"<entry>" + raw + b"</entry>",
                    parser=etree.XMLParser(
                        resolve_entities=False, no_network=True, load_dtd=False,
                        recover=False, huge_tree=False, remove_blank_text=False
                    )
                )
            except (etree.XMLSyntaxError, ValueError):
                raise ValueError("Unparseable original native body in topology triage") from None
            if any(isinstance(x, etree._Entity) for x in root.iter()):
                raise ValueError("Unresolved XML entity in original commentary body")
            titles = []
            for child in root.iter():
                if (isinstance(child.tag, str)
                        and child.tag.rsplit("}", 1)[-1] in
                        {"title", "h1", "h2", "h3", "h4", "h5", "h6"}):
                    titles.append(_heading_span("".join(child.itertext())))
            spans = tuple(x for x in titles if x is not None)
            profile = {
                "numeric_xml_title_spans": spans,
                "all_xml_title_count": len(titles),
                "has_conflicting_numeric_title_scopes": len(set(spans)) > 1,
            }
            self.bodies[digest] = profile
            self.unique_titles["distinct_bodies_with_numbered_xml_title"] += bool(spans)
            self.unique_titles["distinct_bodies_without_numbered_xml_title"] += not bool(spans)
            self.unique_titles["distinct_bodies_with_multiple_numbered_titles"] += len(spans) > 1
        self.occupied[chapter][digest].append(verse)

    def report(self, chapter_maximums: dict[str, int]) -> dict:
        if not isinstance(chapter_maximums, dict):
            raise ValueError("Original native chapter registry required")
        candidates = defaultdict(list)
        counts = Counter()
        seen = 0
        per_digest_chapters = defaultdict(list)
        for chapter, blocks in sorted(self.occupied.items()):
            limit = chapter_maximums.get(chapter)
            if not isinstance(limit, int) or not 1 <= limit <= 176:
                raise ValueError("Missing trusted chapter verse limit")
            for digest, positions in sorted(blocks.items(), key=lambda kv: min(kv[1])):
                seen += len(positions)
                positions = sorted(positions)
                if len(set(positions)) != len(positions) or positions[-1] > limit:
                    raise ValueError("Invalid duplicate or out-of-range original occupied verse")
                per_digest_chapters[digest].append(chapter)
                profile = self.bodies[digest]
                titles = profile["numeric_xml_title_spans"]
                first = positions[0]
                # One original raw body can be deliberately linked to two
                # non-contiguous passage spans. Never auto-fill their gap.
                islands = 1 + sum(
                    b != a + 1 for a, b in zip(positions, positions[1:])
                )
                if islands > 1:
                    counts["disconnected_same_body_within_chapter"] += 1
                    candidates["disconnected_same_body_within_chapter"].append({
                        "first_native_key": f"{chapter}.{first}",
                        "native_slot_count": len(positions),
                        "separate_native_runs": islands,
                    })
                if profile["has_conflicting_numeric_title_scopes"]:
                    counts["distinct_numbered_xml_titles_in_same_body"] += 1
                    candidates["distinct_numbered_xml_titles_in_same_body"].append({
                        "first_native_key": f"{chapter}.{first}",
                        "different_numbered_title_count": len(set(titles)),
                    })
                if titles and titles[0][0] != first:
                    counts["first_numeric_title_vs_first_native_slot_disagree"] += 1
                    candidates["first_numeric_title_vs_first_native_slot_disagree"].append({
                        "first_native_key": f"{chapter}.{first}",
                        "numbered_title_starts_at": titles[0][0],
                    })
                if titles and any(max(span) > limit for span in titles):
                    counts["numbered_title_outside_native_chapter_verse_limit"] += 1
                    candidates["numbered_title_outside_native_chapter_verse_limit"].append({
                        "first_native_key": f"{chapter}.{first}",
                        "chapter_verse_limit": limit,
                    })
        if seen != self.numbered_count:
            raise ValueError("Incomplete original native K key topology")
        for digest, chapters in per_digest_chapters.items():
            if len(chapters) > 1:
                counts["identical_raw_body_reused_in_multiple_chapters"] += 1
                candidates["identical_raw_body_reused_in_multiple_chapters"].append({
                    "first_native_chapter": chapters[0],
                    "different_native_chapter_count": len(chapters),
                })
        return {
            "status": "COMPLETE_ORIGINAL_NATIVE_EDITORIAL_TOPOLOGY_TRIAGE_NOT_APPROVAL",
            "original_native_K_rows_seen": self.numbered_count,
            "original_native_I_rows_seen": self.original_I_count,
            "original_native_TOP_rows_seen": self.original_U_count,
            "distinct_original_K_raw_bodies": len(self.bodies),
            "unique_original_body_numeric_title_classes": dict(sorted(self.unique_titles.items())),
            "candidate_counts": dict(sorted(counts.items())),
            "candidate_samples": {
                kind: sorted(rows, key=lambda x: tuple(str(v) for v in x.values()))[:MAX_CASES_PER_CLASS]
                for kind, rows in sorted(candidates.items())
            },
            "sample_overflow_counts": {
                kind: max(0, len(rows) - MAX_CASES_PER_CLASS)
                for kind, rows in sorted(candidates.items())
            },
            "all_original_native_K_rows_examined": True,
            "candidate_is_not_an_editorial_defect_verdict": True,
            "authorial_prose_reference_targets_and_source_xml_unchanged": True,
            "original_words_or_xml_in_report": False,
            "release_authorized": False,
        }
