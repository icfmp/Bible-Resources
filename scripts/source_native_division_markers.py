#!/usr/bin/env python3
"""Full source-to-native audit of non-displayed editorial division metadata.

Generic and read-only: inspect exact corrected OSIS and actual native SWORD
frames, never invent missing markers or print Scripture. This distinguishes
source-only preservation from preservation in the distributed reader module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json

from lxml import etree
from native_milestone_pair_audit import _strict_root
from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY

KINDS = frozenset({
    "x-subject-division", "x-major-subject-division", "x-stanza-division",
})
LEVELS = frozenset({
    "x-original-ascii-star-1",
    "x-original-ascii-star-2",
    "x-original-ascii-star-3",
})
MAX_MARKS = 100_000


class NativeDivisionAuditError(ValueError):
    pass


def _validation(node):
    kind, level = node.get("type"), node.get("subType")
    if kind not in KINDS or level not in LEVELS or node.get("marker") is not None:
        raise NativeDivisionAuditError("Unreviewed or displayable division metadata")
    return kind, level


def source_divisions(source: bytes):
    root = _source_tree(source)
    current = None
    rows = defaultdict(list)
    n = 0
    for node in root.iter():
        if node.tag == OSIS + "verse":
            sid, eid = node.get("sID"), node.get("eID")
            if eid:
                if eid != current:
                    raise NativeDivisionAuditError("Source verse milestone mispaired")
                current = None
            else:
                current = sid or node.get("osisID")
                if not isinstance(current, str) or KEY.fullmatch(current) is None:
                    raise NativeDivisionAuditError("Unrecognized authored verse key")
        if node.tag == OSIS + "milestone" and node.get("type") in KINDS:
            if not current:
                raise NativeDivisionAuditError("Division marker outside numbered verse")
            rows[current].append(_validation(node))
            n += 1
            if n > MAX_MARKS:
                raise NativeDivisionAuditError("Unbounded source markers")
    if current is not None or not rows:
        raise NativeDivisionAuditError("Source verse scope unfinished or no divisions")
    return dict(rows)


class NativeDivisionAudit:
    def __init__(self, original_source: bytes):
        self.expected = source_divisions(original_source)
        self.observed = defaultdict(list)
        self.frames = Counter()
        self.markers = 0

    def observe(self, kind: str, ref: str, raw: bytes):
        if kind not in {"K", "I", "U"}:
            raise NativeDivisionAuditError("Unsupported native SWORD frame kind")
        self.frames[kind] += 1
        if (b"x-subject-division" not in raw and b"x-major-subject-division" not in raw
                and b"x-stanza-division" not in raw):
            return
        if kind != "K" or KEY.fullmatch(ref) is None:
            raise NativeDivisionAuditError("Editorial marker moved to non-numbered frame")
        root = _strict_root(raw)
        for node in root.iter():
            if not isinstance(node.tag, str) or etree.QName(node).localname != "milestone":
                continue
            if node.get("type") not in KINDS:
                continue
            self.observed[ref].append(_validation(node))
            self.markers += 1
            if self.markers > MAX_MARKS:
                raise NativeDivisionAuditError("Unbounded native markers")

    def finish(self):
        observed = dict(self.observed)
        missing = [k for k in self.expected if self.expected[k] != observed.get(k, [])]
        unexpected = [k for k in observed if k not in self.expected]
        if missing or unexpected:
            raise NativeDivisionAuditError(
                "Source-to-native division metadata unequal at refs " +
                repr((missing + unexpected)[:8]))
        by_type = Counter(x[0] for rows in observed.values() for x in rows)
        by_level = Counter(x[1] for rows in observed.values() for x in rows)
        if sum(by_type.values()) != self.markers:
            raise NativeDivisionAuditError("Native count disagrees with source fingerprint")
        fingerprint = sha256(json.dumps(
            [(ref, rows) for ref, rows in sorted(observed.items())],
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8")).hexdigest()
        return {
            "schema_version": 1,
            "status": "exact_source_and_native_non_display_editorial_markers_equal",
            "source_marker_count": sum(map(len, self.expected.values())),
            "native_marker_count": self.markers,
            "source_host_verse_count": len(self.expected),
            "native_host_verse_count": len(observed),
            "by_type": dict(sorted(by_type.items())),
            "by_non_display_subtype": dict(sorted(by_level.items())),
            "source_and_native_all_marker_types_levels_and_host_verses_equal": True,
            "all_displayable_marker_attributes_absent": True,
            "native_frame_types_read": dict(sorted(self.frames.items())),
            "ordered_marker_host_fingerprint_sha256": fingerprint,
            "source_or_module_modified": False,
            "actual_reader_visual_acceptance": False,
            "release_approval": False,
        }
