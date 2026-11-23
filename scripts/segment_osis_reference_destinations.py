#!/usr/bin/env python3
"""Convert complete, source-verified OSIS cross-reference groups to distinct links.

This is a *separate candidate* on top of normalize_bible_references.py. It
re-types only a pre-existing, source-witnessed, fully resolved cross-reference
label, creating one reference per actually printed citation. Every printed
character stays in original order, including abbreviations, separators and
whitespace. A failed or incomplete parse blocks that entire label.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
import os

from lxml import etree

from normalize_bible_references import (
    BOOK_CITATION, SAME_BOOK_CITATION, NAMED_ONE_CHAPTER_VERSE,
    VERSES_ONLY, OPEN_REFERENCE,
    OSIS, ReviewError, _bytes, _parse, _crosswalk, _usfx_bytes,
    _printed_book_aliases, _complete_printed_destinations,
)

MAX_INPUT = 128 * 1024 * 1024
MAX_PARTS = 128


def _exact_reference_spans(label: str, aliases: dict,
                           verse_ids: set[str],
                           disambiguated_chapter_commas: bool = False,
                           named_single_chapter_refs: bool = False
                           ) -> list[tuple[int, int, str]]:
    """Parse every source character, yielding raw display offsets + OSIS keys.

    The existing, separately tested canonical full-label parser is an
    independent oracle: the ordered targets MUST agree exactly.
    """
    start_padding = len(label) - len(label.lstrip())
    label = label.strip()
    expected, reason, _ = _complete_printed_destinations(
        label, aliases, verse_ids,
        disambiguated_chapter_commas=disambiguated_chapter_commas,
        named_single_chapter_refs=named_single_chapter_refs)
    if expected is None:
        raise ReviewError(f"Cannot split incompletely parsed original label: {label[:120]!r}, reason={reason}")
    position = 0
    book = None
    chapter = None
    repeat_book = False
    spans = []
    while position < len(label):
        direct = BOOK_CITATION.match(label, position)
        if direct:
            book = aliases.get(" ".join(direct["alias"].split()))
            if book is None:
                raise ReviewError("Unverified book alias in source segmentation")
            chapter = int(direct["chapter"])
            verse = int(direct["verse"])
            start = position
            position = direct.end()
        elif (named_single_chapter_refs and
                (named := NAMED_ONE_CHAPTER_VERSE.match(label, position)) and
                not (position == 0 and label.endswith(".") and
                     named.end() == len(label) - 1)):
            book = aliases.get(" ".join(named["alias"].split()))
            if not book:
                raise ReviewError("Unverified one-chapter book alias in source segmentation")
            chapters = {key.split(".")[1] for key in verse_ids
                        if key.startswith(book + ".")}
            if chapters != {"1"}:
                raise ReviewError("Source segmentation may only infer the unique attested chapter")
            chapter = 1
            verse = int(named["verse"])
            start = position
            position = named.end()
        elif repeat_book and book:
            carried = SAME_BOOK_CITATION.match(label, position)
            if carried is None:
                raise ReviewError("Unrecognized semicolon context in source segmentation")
            chapter = int(carried["chapter"])
            verse = int(carried["verse"])
            start = position
            position = carried.end()
        else:
            raise ReviewError("Unrecognized original citation position")
        repeat_book = False
        end = position
        while position < len(label) and label[position].isspace():
            position += 1
        first = f"{book}.{chapter}.{verse}"
        if position < len(label) and label[position] in "-–":
            position += 1
            while position < len(label) and label[position].isspace():
                position += 1
            last = VERSES_ONLY.match(label, position)
            if last is None:
                raise ReviewError("Incomplete source verse range")
            target = first + "-" + f"{book}.{chapter}.{int(last.group())}"
            position = last.end()
            end = position
        else:
            target = first
            position = end
        spans.append((start, end, target))
        while True:
            j = position
            while j < len(label) and label[j].isspace():
                j += 1
            if j == len(label) or label[j] != ",":
                break
            j += 1
            while j < len(label) and label[j].isspace():
                j += 1
            extra = VERSES_ONLY.match(label, j)
            if extra is None:
                raise ReviewError("Incomplete source comma verse")
            current = f"{book}.{chapter}.{int(extra.group())}"
            if current not in verse_ids and disambiguated_chapter_commas:
                k = extra.end()
                while k < len(label) and label[k].isspace():
                    k += 1
                if k < len(label) and label[k] == ",":
                    k += 1
                    while k < len(label) and label[k].isspace():
                        k += 1
                    second = VERSES_ONLY.match(label, k)
                    if second:
                        next_key = f"{book}.{int(extra.group())}.{int(second.group())}"
                        if next_key in verse_ids:
                            chapter = int(extra.group())
                            spans.append((extra.start(), second.end(), next_key))
                            position = second.end()
                            continue
            spans.append((extra.start(), extra.end(), current))
            position = extra.end()
        while position < len(label) and label[position].isspace():
            position += 1
        if position >= len(label):
            raise ReviewError("Original citation missing terminal punctuation")
        separator = label[position]
        position += 1
        if separator == ".":
            if position == len(label):
                break
            while position < len(label) and label[position].isspace():
                position += 1
            book, repeat_book = None, False
        elif separator == ";":
            while position < len(label) and label[position].isspace():
                position += 1
            repeat_book = True
        else:
            raise ReviewError("Unexpected separator in attested original citation")
        if len(spans) > MAX_PARTS:
            raise ReviewError("Source reference group exceeds accepted size")
    if (len(spans) < 1 or len(spans) > MAX_PARTS or
            " ".join(part[2] for part in spans) != expected or
            any(a >= b or (n and a < spans[n - 1][1])
                for n, (a, b, _value) in enumerate(spans)) or
            any(target not in verse_ids and
                not (target.count("-") == 1 and
                     all(x in verse_ids for x in target.split("-")))
                for _a, _b, target in spans)):
        raise ReviewError("Independent canonical-target or offset validation failed")
    return [(a + start_padding, b + start_padding, target)
            for a, b, target in spans]


def _patched_reference(label: str, spans: list[tuple[int, int, str]]) -> bytes:
    """Generate only new markup; concatenate source slices verbatim."""
    pieces = []
    position = 0
    recovered = []
    for index,(start, end, target) in enumerate(spans):
        pieces.append(label[position:start])
        pieces.append(f'<reference osisRef="{target}">')
        # SWORD's native OSIS importer retains a trailing blank following
        # the final in-reference full stop differently from a blank outside
        # </reference>. Keep the exact source tail *inside* the last link
        # only for that original-attested punctuation+whitespace form.
        # No character is added, removed, normalized or reordered.
        if index == len(spans)-1 and re.fullmatch(r"\.\s+",label[end:]):
            end = len(label)
        pieces.append(label[start:end])
        pieces.append("</reference>")
        recovered.append(label[start:end])
        position = end
    pieces.append(label[position:])
    if not all(a <= b for a, b, _ in spans):
        raise ReviewError("Invalid source slice")
    return "".join(pieces).encode("utf-8")


def segment_candidate(input_xml: bytes, aliases: dict,
                      disambiguated_chapter_commas: bool = False,
                      named_single_chapter_refs: bool = False
                      ) -> tuple[bytes, dict]:
    root = _parse(input_xml)
    if root.tag != OSIS + "osis":
        raise ReviewError("Expected canonical OSIS input")
    verse_ids = {part for e in root.iter(OSIS + "verse")
                 for part in (e.get("osisID") or "").split()}
    notes = [e for e in root.iter(OSIS + "note")
             if e.get("type") == "crossReference"]
    references = list(root.iter(OSIS + "reference"))
    opening = list(OPEN_REFERENCE.finditer(input_xml))
    if len(references) != len(opening):
        raise ReviewError("Parsed and serialized OSIS reference inventories disagree")
    patches = []
    counts = Counter()
    for i, (node, start) in enumerate(zip(references, opening, strict=True)):
        if node.getparent() is None or node.getparent().tag != OSIS + "note":
            continue
        if node.getparent().get("type") != "crossReference":
            continue
        target = node.get("osisRef")
        if not target or node.get("type") is not None or node.get("subType") is not None:
            continue
        parts = target.split()
        counts["already_linked_destination_labels"] += 1
        if len(parts) <= 1:
            continue
        if dict(node.attrib) != {"osisRef": target} or len(node):
            raise ReviewError("Compound reference contains unexpected authorial attributes or nested children")
        close = input_xml.find(b"</reference>", start.end())
        if close < 0 or (i + 1 < len(opening) and
                         close >= opening[i + 1].start()):
            raise ReviewError("Non-atomic destination reference source span")
        raw_label = input_xml[start.end():close]
        # XML escaped content or embedded markup is not source-safe to re-type
        # by raw positional edits; leave it unchanged but explicitly report it.
        try:
            source_label = raw_label.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReviewError("Invalid original source UTF-8") from exc
        if source_label != (node.text or ""):
            counts["unsegmented_escaped_or_complex_source_labels"] += 1
            continue
        spans = _exact_reference_spans(
            source_label, aliases, verse_ids,
            disambiguated_chapter_commas=disambiguated_chapter_commas,
            named_single_chapter_refs=named_single_chapter_refs)
        if len(spans) != len(parts) or [x[2] for x in spans] != parts:
            raise ReviewError("Printed citation segmentation differs from original source-verified target list")
        fragment = _patched_reference(source_label, spans)
        patches.append((start.start(), close + len(b"</reference>"), fragment))
        counts["segmented_destination_labels"] += 1
        if named_single_chapter_refs and NAMED_ONE_CHAPTER_VERSE.search(source_label):
            counts["named_one_chapter_compound_labels_segmented"] += 1
        counts["individual_reference_elements_created"] += len(spans)
        counts["new_reference_elements"] += len(spans) - 1
    cursor = 0
    combined = []
    for left, right, replacement in patches:
        if left < cursor or left >= right:
            raise ReviewError("Source reference replacements overlap")
        combined.extend([input_xml[cursor:left], replacement])
        cursor = right
    combined.append(input_xml[cursor:])
    result = b"".join(combined)
    after = _parse(result)
    old_notes = [e for e in root.iter(OSIS + "note")
                 if e.get("type") == "crossReference"]
    new_notes = [e for e in after.iter(OSIS + "note")
                 if e.get("type") == "crossReference"]
    if len(old_notes) != len(new_notes):
        raise ReviewError("Cross-reference note count changed")
    for old, new in zip(old_notes, new_notes, strict=True):
        if (dict(old.attrib) != dict(new.attrib) or
                "".join(old.itertext()) != "".join(new.itertext())):
            raise ReviewError("Original cross-reference note text or metadata changed")
        old_anchors = [(x.get("osisRef") or "") for x in old
                       if x.tag == OSIS + "reference" and
                       x.get("type") == "annotateRef"]
        new_anchors = [(x.get("osisRef") or "") for x in new
                       if x.tag == OSIS + "reference" and
                       x.get("type") == "annotateRef"]
        old_targets = [token for x in old
                       if x.tag == OSIS + "reference" and
                       x.get("type") is None
                       for token in (x.get("osisRef") or "").split()]
        new_targets = [token for x in new
                       if x.tag == OSIS + "reference" and
                       x.get("type") is None
                       for token in (x.get("osisRef") or "").split()]
        if old_anchors != new_anchors or old_targets != new_targets:
            raise ReviewError("Original note anchor or target sequence changed")
    # Crucial: the entire document's text and verse identifiers are identical,
    # not merely the displayed text in selected samples.
    if "".join(root.itertext()) != "".join(after.itertext()):
        raise ReviewError("Whole Bible text including notes and punctuation changed")
    before_keys = [(x.get("osisID"), x.get("sID"), x.get("eID"))
                   for x in root.iter(OSIS + "verse")]
    after_keys = [(x.get("osisID"), x.get("sID"), x.get("eID"))
                  for x in after.iter(OSIS + "verse")]
    if before_keys != after_keys:
        raise ReviewError("Original Scripture verse identity or order changed")
    if len(list(after.iter(OSIS + "reference"))) != (
            len(references) + counts["new_reference_elements"]):
        raise ReviewError("Serialized reference element cardinality mismatch")
    receipt = {
        "kind": "source_verified_individual_reference_candidate",
        "input_sha256": sha256(input_xml).hexdigest(),
        "output_sha256": sha256(result).hexdigest(),
        "original_note_text_and_punctuation_identical": True,
        "entire_bible_text_and_verse_order_identical": True,
        "source_bytes_outside_replaced_reference_elements_unchanged": True,
        "source_original_destinations_and_order_identical": True,
        "original_sword_releases_unchanged": True,
        "no_publication_approval": True,
        **dict(counts),
    }
    return result, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--original-usfx", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--alias-witness", type=Path, required=True)
    parser.add_argument("--disambiguated-chapter-commas", action="store_true",
                        help="Segment uniquely attested comma chapter,verse references too")
    parser.add_argument("--named-single-chapter-refs", action="store_true",
                        help="Segment exact source-attested one-chapter book v. verse tokens")
    parser.add_argument("--expected-input-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    protected = [args.input, args.original_usfx, args.crosswalk, args.alias_witness]
    if (args.output.resolve() in {p.resolve() for p in protected+[args.report]} or
            args.report.resolve() in {p.resolve() for p in protected}):
        parser.error("Output and receipt must not overwrite any original/source")
    try:
        source = _bytes(args.input, MAX_INPUT)
        if sha256(source).hexdigest() != args.expected_input_sha256:
            raise ReviewError("Pinned input hash mismatch")
        zipped = _bytes(args.original_usfx, MAX_INPUT)
        original = _parse(_usfx_bytes(args.original_usfx))
        aliases, alias_sha = _printed_book_aliases(
            args.alias_witness, _crosswalk(args.crosswalk),
            sha256(zipped).hexdigest(), original)
        result, receipt = segment_candidate(
            source, aliases,
            disambiguated_chapter_commas=args.disambiguated_chapter_commas,
            named_single_chapter_refs=args.named_single_chapter_refs)
        receipt["source_provider_usfx_zip_sha256"] = sha256(zipped).hexdigest()
        receipt["printed_alias_witness_sha256"] = alias_sha
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".individual-links-",dir=args.output.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(result)
            os.replace(temp, args.output)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",
                               encoding="utf-8")
        print("Isolated individual-reference structural candidate:",
              receipt.get("segmented_destination_labels",0),
              "notes split into",
              receipt.get("individual_reference_elements_created",0),
              "individually targeted links")
        return 0
    except (OSError, ValueError, etree.XMLSyntaxError) as exc:
        parser.exit(2, f"Source-preserving segmentation blocked: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
