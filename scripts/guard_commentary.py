#!/usr/bin/env python3
"""Fail-closed OSIS commentary annotation gate; never rewrites a source.

An OSIS commentary uses <div annotateType="commentary" annotateRef="...">.
This checker supplements the generic official-XSD OSIS guard with the
specific annotation structure documented by CrossWire. Unreviewed forms
stop with the original XML file and line, never a guessed SWORD verse key.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from guard_osis import (POLICY_PATH, MAX_SOURCE_BYTES, StructureFailure,
                        inspect as inspect_osis, parse_xml,
                        require_regular_file, write_report)

ROOT = Path(__file__).resolve().parents[1]
COMMENTARY_POLICY = ROOT / "config/commentary-policy.json"
OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

# This is an explicitly reviewed *subset* of the OSIS commentary osisRef
# grammar, not a replacement for OSIS schema validation. Unknown legal
# forms are blocked for a new reviewed rule rather than partially parsed.
SIMPLE_REF = re.compile(
    r"^(?P<book>[1-4]?[A-Za-z][A-Za-z0-9]*)"
    r"(?:\.(?P<chapter>[0-9]+)(?:\.(?P<verse>[0-9]+))?)?$"
)


def _error(source: Path, element, code: str, detail: str) -> None:
    raise StructureFailure(source, element.sourceline or 1, code, detail)


def _ref_parts(source: Path, element, value: str) -> tuple:
    if ":" in value:
        _error(source, element, "COMMENTARY_WORK_PREFIX",
               "Commentary annotateRef must not contain a work prefix such as Bible:; consult CrossWire OSIS Commentaries")
    match = SIMPLE_REF.fullmatch(value)
    if not match:
        _error(source, element, "COMMENTARY_REFERENCE_UNREVIEWED",
               f"Unreviewed commentary reference {value[:120]!r}; do not guess a verse or silently rewrite the reference")
    book, chapter, verse = match.group("book", "chapter", "verse")
    if chapter is not None and int(chapter) < 1 or verse is not None and int(verse) < 1:
        _error(source, element, "COMMENTARY_REFERENCE_UNREVIEWED",
               f"Zero-based commentary key {value[:120]!r} needs a reviewed introduction/versification rule")
    return (book, int(chapter) if chapter is not None else None,
            int(verse) if verse is not None else None)


def _check_reference(source: Path, element, ref: str) -> None:
    if not ref or ref != ref.strip():
        _error(source, element, "COMMENTARY_REFERENCE_UNREVIEWED",
               "Empty or surrounding-whitespace annotateRef requires review")
    tokens = ref.split()
    if not tokens:
        _error(source, element, "COMMENTARY_REFERENCE_UNREVIEWED", "Empty annotateRef")
    for token in tokens:
        if "-" not in token:
            _ref_parts(source, element, token)
            continue
        endpoints = token.split("-")
        if len(endpoints) != 2:
            _error(source, element, "COMMENTARY_REFERENCE_UNREVIEWED",
                   f"Unexpected range syntax {token[:120]!r}")
        first, last = (_ref_parts(source, element, part) for part in endpoints)
        if first[0] != last[0]:
            _error(source, element, "COMMENTARY_CROSS_BOOK_RANGE_UNREVIEWED",
                   f"Cross-book range {token[:120]!r} requires verified canonical book order")
        if first[1] is None or last[1] is None or first[2] is None or last[2] is None:
            _error(source, element, "COMMENTARY_RANGE_UNREVIEWED",
                   f"Range {token[:120]!r} needs fully qualified verse references")
        if first[1:] > last[1:]:
            _error(source, element, "COMMENTARY_REVERSED_RANGE",
                   f"Reversed commentary reference range {token[:120]!r}")


def _policy(path: Path) -> tuple[dict, str]:
    try:
        data = json.loads(require_regular_file(path, 512 * 1024, "COMMENTARY_POLICY_MISSING").decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise StructureFailure(path, 1, "COMMENTARY_POLICY_INVALID", str(exc)) from exc
    if not isinstance(data, dict) or (
        data.get("schema_version") != 1 or
        data.get("annotation_element") != "div" or
        data.get("annotation_type") != "commentary" or
        data.get("annotation_attribute") != "annotateRef" or
        data.get("unknown_or_ambiguous") != "block_with_file_and_line" or
        data.get("cross_book_ranges") != "require_reviewed_versification_order" or
        data.get("work_prefixes") != "forbidden_by_current_SWORD_commentary_importer"
    ):
        raise StructureFailure(path, 1, "COMMENTARY_POLICY_INVALID",
                               "Unsupported commentary mapping policy; an explicit reviewed implementation is required")
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return data, digest


def inspect_commentary(source_path: Path, schema_path: Path,
                       osis_policy: Path = POLICY_PATH,
                       commentary_policy: Path = COMMENTARY_POLICY) -> dict:
    """Validate official OSIS and CrossWire commentary-entry semantics."""
    source = Path(source_path).absolute()
    _, commentary_hash = _policy(Path(commentary_policy).absolute())
    # Do the official XSD and reviewed source structure checks *first*.
    result = inspect_osis(source, schema_path, osis_policy)
    raw = require_regular_file(source, MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
    document = parse_xml(source, raw, "MALFORMED_XML")
    entries = 0
    reference_digest = hashlib.sha256()
    structure = Counter()
    for element in document.iter():
        if not isinstance(element.tag, str):
            continue  # The shared OSIS guard has already rejected this node.
        annotated = "annotateType" in element.attrib or "annotateRef" in element.attrib
        if not annotated:
            continue
        tag = element.tag
        if tag != OSIS_NS + "div":
            _error(source, element, "COMMENTARY_ANNOTATION_UNREVIEWED",
                   f"Annotation on {tag!r} is not a reviewed CrossWire commentary entry")
        if element.get("annotateType") != "commentary":
            _error(source, element, "COMMENTARY_ANNOTATION_TYPE",
                   "An entry needs annotateType=\"commentary\" as required by CrossWire's OSIS commentary importer")
        ref = element.get("annotateRef")
        if not ref:
            _error(source, element, "COMMENTARY_REFERENCE_MISSING",
                   "An annotated commentary section needs a nonempty annotateRef")
        _check_reference(source, element, ref)
        entries += 1
        reference_digest.update(ref.encode("utf-8"))
        reference_digest.update(b"\x00")
        structure["annotated_sections"] += 1
        structure["reference_groups"] += len(ref.split())

    if not entries:
        root = document.getroot()
        _error(source, root, "COMMENTARY_NO_ENTRIES",
               "No <div annotateType=\"commentary\" annotateRef=\"...\"> found; cannot build a commentary module")

    result.update(
        source_kind="commentary",
        commentary_policy_sha256=commentary_hash,
        annotation_count=entries,
        annotation_reference_sha256=reference_digest.hexdigest(),
        annotation_counts=dict(sorted(structure.items())),
        no_transformation_performed=True,
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--schema", type=Path, required=True,
                        help="Reviewed locally pinned official OSIS XSD")
    parser.add_argument("--osis-policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--commentary-policy", type=Path, default=COMMENTARY_POLICY)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_commentary(args.source, args.schema,
                                    args.osis_policy, args.commentary_policy)
        code = 0
        print(f"{args.source}: OSIS commentary annotations validated; no changes written")
    except StructureFailure as exc:
        result = {"status": "blocked", "diagnostic": exc.as_dict(),
                  "source_kind": "commentary", "no_transformation_performed": True}
        code = 1
        print(exc, file=sys.stderr)
    if args.report:
        write_report(args.report, result)
    return code


if __name__ == "__main__":
    sys.exit(main())
