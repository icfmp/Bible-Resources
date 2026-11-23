#!/usr/bin/env python3
"""Mark source-attested chapter-opening section titles for SWORD pre-verse import.

OSIS 2.1.1 permits explicit section title types. The stable SWORD osis2mod
compiler otherwise stores an untyped title immediately after a chapter sID in
a chapter intro (verse 0), not with verse 1. That makes it invisible in verse-
indexed readers. This generic, source-pinned candidate overlay adds only
type="section" to *existing* first title tags. No heading text is changed.

Historical original and approved cleaned files are never modified in place.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from xml.etree import ElementTree as ET

SOURCE_LIMIT = 128 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
# Only a milestone with an authorial chapter sID followed *solely* by XML
# whitespace/comments and an UNCLASSIFIED section heading. Already typed
# chapter, main, parallel, section and midchapter titles are untouched.
DIRECT_UNTYPED = re.compile(
    rb'(?P<prefix><chapter\b(?=[^<>]*\bsID="[^"]+")'
    rb'(?=[^<>]*\bosisID="[^"]+")[^<>]*/>'
    rb'(?:\s*<!--[^>]*-->\s*)*)'
    rb'(?P<opening><title\s*>)'
)
CHAPTER_ID = re.compile(rb'\bsID="([^"]+)"')
TITLE_CLOSE = b"</title>"


class PreverseSectionError(ValueError):
    """Inconsistent source, ambiguous title or unsafe candidate output."""


def annotate(source: bytes) -> tuple[bytes, dict]:
    if not isinstance(source, bytes) or len(source) > SOURCE_LIMIT:
        raise PreverseSectionError("Missing, oversized, or invalid original OSIS bytes")
    revisions: list[tuple[int, int, bytes]] = []
    chapters: list[str] = []
    source_sample: list[dict[str, str]] = []
    for match in DIRECT_UNTYPED.finditer(source):
        opening = match.group("opening")
        if opening != b"<title>":
            # Other whitespace within the opening tag is source text, not an
            # arbitrary license to reformat the original markup.
            raise PreverseSectionError("Ambiguous untyped title opening whitespace")
        chapter = CHAPTER_ID.search(match.group("prefix"))
        if chapter is None:
            raise PreverseSectionError("Chapter title lacks a source chapter identifier")
        name = chapter.group(1).decode("ascii")
        if not re.fullmatch(r"[1-4]?[A-Za-z0-9]+\.[1-9][0-9]*", name):
            raise PreverseSectionError("Invalid source chapter identifier")
        if name in chapters:
            raise PreverseSectionError("Duplicate chapter-opening title record")
        start = match.start("opening")
        following = source.find(TITLE_CLOSE, match.end("opening"))
        if following < 0 or b"<" in source[match.end("opening"):following]:
            # The generator intentionally refuses rich/mixed-content titles;
            # it must not accidentally rewrite their nested semantics.
            raise PreverseSectionError("Ambiguous first title structure in " + name)
        label = source[match.end("opening"):following].decode("utf-8")
        if not label.strip():
            raise PreverseSectionError("Empty source heading at " + name)
        revisions.append((start, match.end("opening"), b'<title type="section">'))
        chapters.append(name)
        if len(source_sample) < 12:
            source_sample.append({"chapter": name, "original_title": label})
    if not revisions:
        raise PreverseSectionError("No untyped chapter-opening titles to mark")
    result = bytearray()
    before = 0
    for start, end, replacement in revisions:
        if start < before:
            raise PreverseSectionError("Overlapping source modifications")
        result.extend(source[before:start])
        result.extend(replacement)
        before = end
    result.extend(source[before:])
    candidate = bytes(result)
    # Reversibility by exact byte-span editing; no serialization, whitespace
    # normalization, title duplication, callout or verse mutation occurs.
    undo = candidate
    for start, _end, _replacement in reversed(revisions):
        # Undo coordinates in the output shift after the first inserted token.
        pos = start + len(b' type="section"') * revisions.index(
            next(x for x in revisions if x[0] == start))
        if undo[pos:pos + len(b'<title type="section">')] != b'<title type="section">':
            raise PreverseSectionError("Failed reversible source byte check")
        undo = undo[:pos] + b"<title>" + undo[pos + len(b'<title type="section">'):]
    if undo != source:
        raise PreverseSectionError("Source cannot be restored byte-identically")
    try:
        ET.fromstring(source)
        ET.fromstring(candidate)
    except ET.ParseError as exc:
        raise PreverseSectionError("Source or candidate OSIS is not well-formed") from exc
    return candidate, {
        "schema_version": 1,
        "status": "source_pinned_reversible_section_title_overlay",
        "original_sha256": sha256(source).hexdigest(),
        "candidate_sha256": sha256(candidate).hexdigest(),
        "typed_chapter_first_titles": len(revisions),
        "changed_chapters": chapters,
        "sample": source_sample,
        "only_change": "add type=\"section\" to existing untyped first titles",
        "source_bytes_restorable": True,
        "verse_text_note_callouts_reference_targets_and_original_titles_unchanged": True,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-input-sha256", required=True)
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args()
    if SHA256.fullmatch(args.expected_input_sha256) is None:
        raise SystemExit("Expected SHA-256 must be exact lowercase hex")
    if args.input.resolve() in {args.output.resolve(), args.report.resolve()}:
        raise SystemExit("Output paths must not overwrite their original input")
    if args.output.resolve() == args.report.resolve():
        raise SystemExit("Output and report paths must be distinct")
    source = args.input.read_bytes()
    if sha256(source).hexdigest() != args.expected_input_sha256:
        raise SystemExit("Approved original OSIS SHA-256 does not match")
    output, report = annotate(source)
    if args.expected_count is not None and report["typed_chapter_first_titles"] != args.expected_count:
        raise SystemExit("Unexpected authored chapter-first title count")
    for target, raw in (
        (args.output, output),
        (args.report, (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as tmp:
            tmp.write(raw)
            temp_path = Path(tmp.name)
        os.replace(temp_path, target)
    print("Source-pinned, reversible chapter-opening headings:", report["typed_chapter_first_titles"],
          "candidate SHA-256", report["candidate_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
