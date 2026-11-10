#!/usr/bin/env python3
"""Validate *compiled* SWORD sID/eID pairing across occupied native entries.

This is deliberately separate from authored USFX→compiled editorial parity.
Original native XML/IDs/words remain in memory only. The public receipt has
aggregate structural categories, SHA digests and bounded reference IDs.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

from lxml import etree

from sword_native_inventory import INTRO
from stable_sword_refs import KEY

STRUCTURAL = frozenset({"div", "l", "lg", "p", "q", "lb", "milestone"})
UNTRUSTED_ANNOTATION = frozenset({"note", "title"})
MAX_EVENTS = 300_000
MAX_ENTRY = 2 * 1024 * 1024
MAX_EXAMPLES = 12
MAX_IDENTIFIER = 256
TOP = re.compile(r"TOP:[1-9][0-9]*\Z")


class NativeMilestoneAuditError(ValueError):
    """Original native structure cannot be safely inspected."""


def _strict_root(raw: bytes):
    if not isinstance(raw, bytes) or len(raw) > MAX_ENTRY:
        raise NativeMilestoneAuditError("Oversized or invalid original native XML")
    if b"<!DOCTYPE" in raw.upper() or b"<?xml" in raw.lower() or b"<!ENTITY" in raw.upper():
        raise NativeMilestoneAuditError("Unsupported native XML declaration")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(b"<private_root>" + raw + b"</private_root>", parser)
    except (etree.XMLSyntaxError, UnicodeError, ValueError) as exc:
        raise NativeMilestoneAuditError("Original native XML fragment is not well-formed") from exc
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise NativeMilestoneAuditError("Original native XML contains unresolved entity")
    return root


def _events(root):
    """Document-order structural milestones, excluding notes and title bodies."""
    def walk(node):
        if not isinstance(node.tag, str):
            return
        tag = etree.QName(node).localname
        if node is not root and tag in UNTRUSTED_ANNOTATION:
            return
        if node is not root and tag in STRUCTURAL:
            sid, eid = node.get("sID"), node.get("eID")
            if sid is not None or eid is not None:
                yield tag, sid, eid, node.get("type", ""), node.get("subType", "")
        for child in node:
            yield from walk(child)
    yield from walk(root)


class NativeMilestonePairAudit:
    def __init__(self):
        self._active = {}
        self._stack = []
        self._total = Counter()
        self._per_tag = Counter()
        self._classifications = Counter()
        self._bad_refs = {}
        self._seen_refs = set()
        self._sequence = 0
        self._event_hash = sha256()

    def _issue(self, key, ref):
        self._classifications[key] += 1
        examples = self._bad_refs.setdefault(key, [])
        if len(examples) < MAX_EXAMPLES and ref not in examples:
            examples.append(ref)

    def observe(self, kind: str, ref: str, raw: bytes):
        if ((kind == "K" and KEY.fullmatch(ref) is None)
                or (kind == "I" and INTRO.fullmatch(ref) is None)
                or (kind == "U" and TOP.fullmatch(ref) is None)
                or kind not in {"K", "I", "U"}):
            raise NativeMilestoneAuditError("Unexpected original native entry reference")
        if (kind, ref) in self._seen_refs:
            raise NativeMilestoneAuditError("Repeated native entry in milestone pairing audit")
        self._seen_refs.add((kind, ref))
        self._total[f"observed_{kind}_entries"] += 1
        if kind == "U":
            # Anonymous TOP records lack an addressable canonical book; do not
            # pretend a structural marker in one belongs to a known source book.
            self._total["unaddressable_TOP_entries_unverified"] += 1
            return
        book = ref.split(".", 1)[0]
        try:
            root = _strict_root(raw)
        except NativeMilestoneAuditError:
            self._issue("unparseable_native_fragment", ref)
            return
        self._total["parseable_numbered_or_intro_entries"] += 1
        for tag, sid, eid, open_type, subtype in _events(root):
            self._sequence += 1
            if self._sequence > MAX_EVENTS:
                raise NativeMilestoneAuditError("Too many structural events")
            if sid is not None and eid is not None:
                self._issue("both_sID_and_eID_on_one_element", ref)
                continue
            value = sid if sid is not None else eid
            if (not value or len(value) > MAX_IDENTIFIER
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                self._issue("empty_or_unsafe_milestone_identifier", ref)
                continue
            endpoint = "open" if sid is not None else "close"
            self._total[f"{endpoint}_events"] += 1
            self._per_tag[f"{tag}:{endpoint}"] += 1
            data = json.dumps([kind,ref,tag,endpoint,len(value),bool(open_type),bool(subtype)],
                              separators=(",", ":")).encode("ascii")
            self._event_hash.update(len(data).to_bytes(4, "big") + data)
            key = (tag, value)
            if sid is not None:
                if key in self._active:
                    self._issue("duplicate_active_sID", ref)
                    continue
                self._active[key] = (book, ref, kind, open_type, self._sequence)
                self._stack.append(key)
            else:
                opened = self._active.pop(key, None)
                if opened is None:
                    self._issue("orphan_eID_without_matching_active_sID", ref)
                    continue
                from_book, start_ref, from_kind, start_type, start_seq = opened
                self._total["paired_matching_sID_eID"] += 1
                self._per_tag[f"{tag}:paired"] += 1
                if from_book != book:
                    self._issue("matched_id_crosses_books", ref)
                if start_type and open_type and start_type != open_type:
                    self._issue("matched_id_has_conflicting_types", ref)
                if not self._stack or self._stack[-1] != key:
                    self._issue("crossing_or_non_lifo_structural_ranges", ref)
                    if key in self._stack:
                        self._stack.remove(key)
                else:
                    self._stack.pop()
                if from_kind == "I" and kind == "K":
                    self._classifications["intro_to_numbered_verse_pairs"] += 1
                elif from_kind == "K" and kind == "K":
                    self._classifications["numbered_to_numbered_verse_pairs"] += 1
                elif from_kind == "I" and kind == "I":
                    self._classifications["intro_to_intro_pairs"] += 1
                else:
                    self._classifications["other_record_kind_pair"] += 1
                if start_ref == ref:
                    self._classifications["pairs_with_both_ends_in_one_entry"] += 1
                else:
                    self._classifications["pairs_spanning_multiple_entries"] += 1

    def finish(self):
        dangling = Counter(tag for tag, _identifier in self._active)
        for tag, _identifier in self._active:
            # Do not include source-generated IDs in any report.
            self._issue("unclosed_sID_at_end_of_native_corpus", self._active[(tag,_identifier)][1])
        blockers = {
            k:v for k,v in self._classifications.items()
            if k in {
                "both_sID_and_eID_on_one_element",
                "empty_or_unsafe_milestone_identifier",
                "duplicate_active_sID",
                "orphan_eID_without_matching_active_sID",
                "matched_id_crosses_books",
                "matched_id_has_conflicting_types",
                "crossing_or_non_lifo_structural_ranges",
                "unparseable_native_fragment",
                "unclosed_sID_at_end_of_native_corpus",
            } and v
        }
        return {
            "schema_version": 1,
            "status": ("compiled_milestones_have_unresolved_pairing_findings"
                       if blockers or self._total["unaddressable_TOP_entries_unverified"]
                       else "compiled_milestone_pairs_verified_only"),
            "native_numbered_intro_scan_counts": dict(sorted(self._total.items())),
            "native_milestone_tag_counts": dict(sorted(self._per_tag.items())),
            "native_milestone_pair_categories": dict(sorted(self._classifications.items())),
            "native_milestone_pairing_findings": dict(sorted(blockers.items())),
            "source_generated_identifier_values_exposed": False,
            "first_issue_reference_ids_no_scripture": self._bad_refs,
            "remaining_unclosed_milestones_by_tag": dict(sorted(dangling.items())),
            "ordered_native_event_reference_fingerprint_sha256": self._event_hash.hexdigest(),
            "source_to_compiled_same_type_event_order_verified": False,
            "source_relative_word_position_coverage_verified": False,
            "verse_zero_and_numbered_milestones_inspected": True,
            "source_editorial_or_publication_approved": False,
        }
