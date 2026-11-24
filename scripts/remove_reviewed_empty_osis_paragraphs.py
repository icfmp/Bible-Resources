#!/usr/bin/env python3
"""Source-pinned, reversible removal of reviewed redundant OSIS paragraphs.

Only bare, child-free, whitespace-only paragraphs between an existing parallel
title and an existing nonempty paragraph are eligible. No automatic editorial
decision: every next-verse key and the exact input hash must be supplied.
All other bytes, including whitespace and comments, remain unchanged.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree
from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY

EMPTY = re.compile(rb"<p\s*/>|<p>([ \t\r\n]*)</p>")


def clean(source: bytes, expected_sha256: str, reviewed_refs: list[str]):
    if sha256(source).hexdigest() != expected_sha256:
        raise ValueError("Reviewed input hash mismatch")
    if (not reviewed_refs or len(set(reviewed_refs)) != len(reviewed_refs)
            or any(not KEY.fullmatch(ref) for ref in reviewed_refs)):
        raise ValueError("Require distinct reviewed source verse references")
    root = _source_tree(source)
    expected = []
    for p in root.iter(OSIS + "p"):
        if p.attrib or len(p) or (p.text or "").strip():
            continue
        previous, following = p.getprevious(), p.getnext()
        if (previous is None or previous.tag != OSIS + "title"
                or previous.get("type") != "parallel"
                or following is None or following.tag != OSIS + "p"
                or not "".join(following.itertext()).strip()
                or (previous.tail or "").strip() or (p.tail or "").strip()
                or any(a.tag in {OSIS+"note", OSIS+"title", OSIS+"header"}
                       for a in p.iterancestors())):
            raise ValueError("Unreviewed empty paragraph context")
        first = next((v for v in following.iter(OSIS+"verse")
                      if v.get("osisID")), None)
        if first is None or not KEY.fullmatch(first.get("osisID")):
            raise ValueError("Missing following authored verse")
        expected.append((first.get("osisID"), p))
    if [ref for ref, _ in expected] != reviewed_refs:
        raise ValueError("Actual empty paragraph sequence differs from reviewed plan")
    # Exact lexical edits are checked against a separate namespace-aware XML
    # tree projection. A regex hit inside a comment or foreign element fails.
    matches = list(EMPTY.finditer(source))
    if len(matches) != len(expected):
        raise ValueError("Ambiguous lexical paragraph spans")
    pieces = []
    ledger = []
    cursor = 0
    offset = 0
    for (ref, _), match in zip(expected, matches):
        raw = match.group()
        keep = match.group(1) or b""
        pieces.extend((source[cursor:match.start()], keep))
        ledger.append({"next_source_verse": ref, "original_byte_offset": match.start(),
                       "candidate_byte_offset": match.start()-offset,
                       "removed_markup_utf8": raw.decode("utf-8"),
                       "retained_inner_whitespace_utf8": keep.decode("utf-8")})
        offset += len(raw)-len(keep)
        cursor = match.end()
    pieces.append(source[cursor:])
    candidate = b"".join(pieces)
    for _, p in expected:
        previous = p.getprevious()
        previous.tail = (previous.tail or "") + (p.text or "") + (p.tail or "")
        p.getparent().remove(p)
    actual = _source_tree(candidate)
    if etree.tostring(root, method="c14n", with_comments=True) != etree.tostring(actual, method="c14n", with_comments=True):
        raise ValueError("Candidate differs beyond reviewed redundant paragraph nodes")
    restored = candidate
    for row in reversed(ledger):
        pos = row["candidate_byte_offset"]
        keep = row["retained_inner_whitespace_utf8"].encode()
        raw = row["removed_markup_utf8"].encode()
        if restored[pos:pos+len(keep)] != keep:
            raise ValueError("Cannot reverse exact structural edit")
        restored = restored[:pos]+raw+restored[pos+len(keep):]
    if restored != source:
        raise ValueError("Original not byte-identically restorable")
    return candidate, {"source_sha256": expected_sha256,
                       "candidate_sha256": sha256(candidate).hexdigest(),
                       "removed_redundant_empty_paragraphs": len(ledger),
                       "changes": ledger, "exact_inverse_verified": True,
                       "no_other_xml_changes": True, "published": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--expected-input-sha256", required=True)
    p.add_argument("--reviewed-ref", action="append", required=True)
    a = p.parse_args()
    if len({a.input.resolve(), a.output.resolve(), a.report.resolve()}) != 3:
        p.error("Use distinct source, candidate and receipt paths")
    if a.output.exists() or a.report.exists():
        p.error("Candidate and receipt must not already exist")
    candidate, receipt = clean(a.input.read_bytes(), a.expected_input_sha256, a.reviewed_ref)
    a.output.write_bytes(candidate)
    a.report.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print("Reviewed redundant empty paragraphs:", receipt["removed_redundant_empty_paragraphs"],
          "candidate SHA-256:", receipt["candidate_sha256"])


if __name__ == "__main__":
    main()
