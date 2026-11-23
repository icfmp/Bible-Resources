#!/usr/bin/env python3
"""Build a source-witness-pinned, byte-reversible OSIS reference candidate.

This is a narrow, generic adapter from the attested USFX <xo>/<xt>/<ior>
structures to OSIS <reference osisRef>. It NEVER guesses destination references
from plain-language <xt> labels or modifies Scripture text, callouts, notes,
paragraphs, poetry, verse keys, or their order. It writes only a separate
candidate, not the existing cleaned master.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile
from lxml import etree

OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MAX_SOURCE = 128 * 1024 * 1024
MAX_USFX = 64 * 1024 * 1024
OPEN_REFERENCE = re.compile(rb"<reference(?=[\s/>])[^<>]*>")
ORIGIN = re.compile(r"(\d+)\.(\d+)")
INTRO = re.compile(r"(\d+)[:.](\d+)(?:\s*[-–—]\s*(?:(\d+)[:.])?(\d+))?")
VERSE_ONLY_RANGE = re.compile(r"(\d+)\s*[-–—]\s*(\d+)")
DIRECT_DESTINATION = re.compile(
    r"(?P<alias>(?:[1-3]\s+)?[A-Za-zÀ-ÿ]{1,12})\s+"
    r"(?P<chapter>[1-9]\d{0,3}):\s*(?P<verse>[1-9]\d{0,3})"
    r"(?:\s*[-–]\s*(?P<last>[1-9]\d{0,3}))?\."
)
DIGEST = re.compile(r"[a-f0-9]{64}")
BOOK_CITATION = re.compile(
    r"(?P<alias>(?:[1-3]\s+)?[A-Za-zÀ-ÿ]{1,12})\s+"
    r"(?P<chapter>[1-9]\d{0,3}):\s*(?P<verse>[1-9]\d{0,3})"
)
SAME_BOOK_CITATION = re.compile(
    r"(?P<chapter>[1-9]\d{0,3}):\s*(?P<verse>[1-9]\d{0,3})"
)
VERSES_ONLY = re.compile(r"[1-9]\d{0,3}")



class ReviewError(ValueError):
    """A source fidelity or non-authorized transformation blocker."""


class UnresolvedSourceTarget(ReviewError):
    """The original printed label is retained, but its target is unverified."""


def _bytes(path: Path, maximum: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ReviewError("Missing, symlinked or oversized source/witness")
    return path.read_bytes()


def _parse(data: bytes):
    if re.search(rb"<!DOCTYPE\b", data, re.IGNORECASE):
        raise ReviewError("Document type declarations are not approved")
    return etree.fromstring(data, parser=etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        recover=False, remove_blank_text=False, huge_tree=False,
    ))


def _label(element) -> str:
    return " ".join("".join(element.itertext()).split())


def _one_child(parent, tag: str):
    found = [e for e in parent if e.tag == tag]
    if len(found) != 1:
        raise ReviewError("Unexpected USFX cross-reference child count")
    return found[0]


def _crosswalk(path: Path) -> dict:
    doc = json.loads(_bytes(path, 256 * 1024).decode("utf-8"))
    entries = doc.get("books", [])
    mapping = {r["usfm"]: r["osis"] for r in entries}
    if not entries or len(mapping) != len(entries) or len(set(mapping.values())) != len(entries):
        raise ReviewError("Missing or ambiguous reviewed USFM/OSIS book crosswalk")
    return mapping


def _printed_book_aliases(path: Path, crosswalk: dict,
                          original_usfx_zip_sha256: str) -> tuple[dict, str]:
    """Keep independently printed aliases distinct from digital-source variants.

    Provider variants are supported only with exact original archive identity,
    explicit provider-specific evidence and the same canonical target as the
    printed edition. Never call a provider spelling a 1910 print abbreviation.
    """
    raw = _bytes(path, 256 * 1024)
    doc = json.loads(raw.decode("utf-8"))
    mapping = doc.get("aliases")
    if (doc.get("schema_version") != 1 or
            doc.get("crosswalk") != "config/standard_usfm_osis_66.json" or
            not isinstance(mapping, dict) or
            len(mapping) != len(crosswalk) or
            set(mapping.values()) != set(crosswalk.values()) or
            not isinstance(doc.get("printed_sources"), list) or
            not doc["printed_sources"] or
            not all(isinstance(url, str) and url.startswith("https://")
                    for url in doc["printed_sources"])):
        raise ReviewError("Missing independently sourced one-to-one printed book aliases")
    for alias, book in mapping.items():
        if (not isinstance(alias, str) or
                re.fullmatch(r"(?:[1-3] )?[A-Za-zÀ-ÿ]{1,12}", alias) is None or
                not isinstance(book, str)):
            raise ReviewError("Invalid printed edition abbreviation")
    result = dict(mapping)
    variants = doc.get("source_attested_digital_variants")
    if variants is not None:
        if (not isinstance(variants, dict) or
                variants.get("status") !=
                    "source_provider_spelling_not_printed_1910_abbreviation" or
                variants.get("witness_usfx_zip_sha256") != original_usfx_zip_sha256 or
                not isinstance(variants.get("evidence"), str) or
                len(variants["evidence"]) < 32 or
                not isinstance(variants.get("aliases"), dict) or
                not variants["aliases"]):
            raise ReviewError("Digital-source alias variants lack pinned original evidence")
        for alias, book in variants["aliases"].items():
            if (not isinstance(alias, str) or
                    re.fullmatch(r"(?:[1-3] )?[A-Za-zÀ-ÿ]{1,12}", alias) is None or
                    alias in result or book not in mapping.values()):
                raise ReviewError("Invalid or ambiguous provider-specific alias")
            result[alias] = book
    return result, sha256(raw).hexdigest()


def _single_explicit_destination(label: str, aliases: dict | None,
                                 verse_ids: set[str]) -> tuple[str | None, str]:
    """Only complete literal one-passage printed labels are machine-linked.

    Multiple books, semicolons, carry-forward chapter references, v. references,
    parenthetical notes and unrecognized aliases are intentionally unlinked.
    A full source reference with no actual source verse is also left unlinked.
    """
    if aliases is None:
        return None, "edition_alias_table_not_requested"
    match = DIRECT_DESTINATION.fullmatch(label)
    if match is None:
        return None, "compound_or_implicit_reference"
    book = aliases.get(" ".join(match["alias"].split()))
    if not book:
        return None, "unverified_printed_book_alias"
    chapter, verse = int(match["chapter"]), int(match["verse"])
    first = f"{book}.{chapter}.{verse}"
    if first not in verse_ids:
        return None, "unattested_reference_start"
    if match["last"] is None:
        return first, "full_explicit_printed_reference"
    last_verse = int(match["last"])
    last = f"{book}.{chapter}.{last_verse}"
    if last_verse < verse or last not in verse_ids:
        return None, "unattested_or_reversed_reference_end"
    return first + "-" + last, "full_explicit_printed_range"


def _complete_printed_destinations(label: str, aliases: dict | None,
                                   verse_ids: set[str]) -> tuple[str | None, str, int]:
    """Consume a complete printed reference list or refuse the whole label.

    Every book alias comes from the independently attested edition table;
    commas carry the explicitly preceding chapter, and semicolons carry the
    book when the following component is a chapter:verse. Full stops require
    a fresh *explicit* book alias. 'etc.', 'v.', nonnumeric terms, unknown books,
    source-absent keys, reversed ranges and any leftover punctuation block.
    Preserve source order, including repetitions, without editing printed text.
    """
    if aliases is None:
        return None, "edition_alias_table_not_requested", 0
    if not label or len(label) > 2048:
        return None, "compound_or_implicit_reference", 0
    pos = 0
    book = None
    chapter = None
    targets = []
    contextual = 0
    can_repeat_book = False
    while pos < len(label):
        direct = BOOK_CITATION.match(label, pos)
        if direct:
            book = aliases.get(" ".join(direct["alias"].split()))
            if not book:
                return None, "unverified_printed_book_alias", 0
            chapter, verse = int(direct["chapter"]), int(direct["verse"])
            pos = direct.end()
        elif can_repeat_book and book:
            carried = SAME_BOOK_CITATION.match(label, pos)
            if not carried:
                return None, "compound_or_implicit_reference", 0
            chapter, verse = int(carried["chapter"]), int(carried["verse"])
            contextual += 1
            pos = carried.end()
        else:
            return None, "compound_or_implicit_reference", 0
        can_repeat_book = False
        first = f"{book}.{chapter}.{verse}"
        if first not in verse_ids:
            return None, "unattested_reference_start", 0

        pos_after_number = pos
        while pos < len(label) and label[pos].isspace():
            pos += 1
        if pos < len(label) and label[pos] in "-–":
            pos += 1
            while pos < len(label) and label[pos].isspace():
                pos += 1
            m = VERSES_ONLY.match(label, pos)
            if m is None:
                return None, "compound_or_implicit_reference", 0
            last_verse = int(m.group())
            last = f"{book}.{chapter}.{last_verse}"
            if last_verse < verse or last not in verse_ids:
                return None, "unattested_or_reversed_reference_end", 0
            targets.append(first + "-" + last)
            pos = m.end()
        else:
            targets.append(first)
            pos = pos_after_number

        # A comma enumerates more verses of the same explicitly established
        # book and chapter. Any unattested verse invalidates the entire list.
        while True:
            j = pos
            while j < len(label) and label[j].isspace():
                j += 1
            if j >= len(label) or label[j] != ",":
                break
            j += 1
            while j < len(label) and label[j].isspace():
                j += 1
            extra = VERSES_ONLY.match(label, j)
            if extra is None:
                return None, "compound_or_implicit_reference", 0
            key = f"{book}.{chapter}.{int(extra.group())}"
            if key not in verse_ids:
                return None, "unattested_reference_start", 0
            targets.append(key)
            pos = extra.end()

        while pos < len(label) and label[pos].isspace():
            pos += 1
        if pos == len(label):
            # The printed reference labels have a terminal full stop; do not
            # silently treat an unfinished fragment as a fully read source.
            return None, "compound_or_implicit_reference", 0
        sep = label[pos]
        pos += 1
        if len(targets) > 128:
            return None, "overlong_printed_reference_sequence", 0
        if sep == ".":
            if pos == len(label):
                return " ".join(targets), "complete_printed_list", contextual
            if not label[pos].isspace():
                return None, "compound_or_implicit_reference", 0
            while pos < len(label) and label[pos].isspace():
                pos += 1
            if pos == len(label):
                return None, "compound_or_implicit_reference", 0
            book = None
            can_repeat_book = False
        elif sep == ";":
            while pos < len(label) and label[pos].isspace():
                pos += 1
            if pos == len(label):
                return None, "compound_or_implicit_reference", 0
            can_repeat_book = True
        else:
            return None, "compound_or_implicit_reference", 0
        if len(targets) > 128:
            return None, "overlong_printed_reference_sequence", 0
    return None, "compound_or_implicit_reference", 0


def _usfx_bytes(archive: Path) -> bytes:
    with ZipFile(archive) as zipped:
        candidates = [item for item in zipped.infolist()
                      if item.filename.lower().endswith("_usfx.xml")]
        if len(candidates) != 1 or candidates[0].file_size > MAX_USFX:
            raise ReviewError("Expected exactly one bounded original USFX scripture document")
        if candidates[0].filename.startswith("/") or ".." in Path(candidates[0].filename).parts:
            raise ReviewError("Unsafe USFX archive member path")
        return zipped.read(candidates[0])


def _origin_target(origin: str, book: str, verse_ids: set[str]) -> str:
    match = ORIGIN.fullmatch(origin)
    if not match:
        raise ReviewError(f"Unrecognized source annotation-origin grammar: {book}, {origin!r}")
    chapter, verse = (int(value) for value in match.groups())
    if chapter < 1 or verse < 1:
        raise ReviewError("Invalid annotation-origin verse")
    target = f"{book}.{chapter}.{verse}"
    if target not in verse_ids:
        raise ReviewError("Annotation origin is not an attested source verse")
    return target


def _intro_target(label: str, book: str, verse_ids: set[str]) -> str | None:
    """Resolve only an entire attested label, never a partial prose fragment.

    USFX introduction pointers can be chapter ranges, single-chapter-book
    verse spans, and occasionally mixed narrative notes. Mixed prose is
    deliberately kept as an unlinked original section label.
    """
    if any(character.isalpha() or character in "()，," for character in label):
        return None
    chapters = {int(part.split(".")[1]) for part in verse_ids
                if part.startswith(book + ".") and len(part.split(".")) == 3}
    if label.isdigit():
        chapter = int(label)
        if chapter < 1 or chapter not in chapters:
            raise UnresolvedSourceTarget("unattested_chapter")
        return f"{book}.{chapter}"
    verse_only = VERSE_ONLY_RANGE.fullmatch(label)
    if verse_only and chapters == {1}:
        first_v, last_v = (int(x) for x in verse_only.groups())
        if first_v < 1 or first_v > last_v:
            raise ReviewError("Reversed or invalid single-chapter introduction range")
        first, last = f"{book}.1.{first_v}", f"{book}.1.{last_v}"
        if first not in verse_ids or last not in verse_ids:
            raise UnresolvedSourceTarget("unattested_single_chapter_endpoint")
        return first + "-" + last
    match = INTRO.fullmatch(label)
    if not match:
        raise ReviewError(f"Unrecognized source introduction-span grammar: {book}, {label!r}")
    chapter, verse = int(match[1]), int(match[2])
    if chapter < 1 or verse < 1:
        raise ReviewError("Invalid introduction start")
    first = f"{book}.{chapter}.{verse}"
    if first not in verse_ids:
        raise UnresolvedSourceTarget("unattested_start")
    if match[4] is None:
        return first
    last_chapter = int(match[3]) if match[3] else chapter
    last_verse = int(match[4])
    if (last_chapter, last_verse) < (chapter, verse):
        raise ReviewError("Reversed introduction range")
    last = f"{book}.{last_chapter}.{last_verse}"
    if last not in verse_ids:
        raise UnresolvedSourceTarget("unattested_end")
    return first + "-" + last

def _source_bindings(cleaned, original, crosswalk: dict,
                     destination_aliases: dict | None = None,
                     complete_lists: bool = False) -> tuple[dict, dict, list, list]:
    """Bind each exact cleaned reference to source-attested USFX semantics.

    Book identity is verified using the independent reviewed USFM->OSIS map.
    Neither the authorial target labels nor the note placement are inferred.
    """
    cbooks = [e for e in cleaned.iter(OSIS + "div")
              if e.get("type") == "book" and not e.get("sID") and not e.get("eID")]
    obooks = [e for e in original.iter() if e.tag == "book"]
    if len(cbooks) != len(obooks) or not obooks:
        raise ReviewError("Different source and cleaned book coverage")
    verse_ids = {part for e in cleaned.iter(OSIS + "verse") for part in
                 (e.get("osisID") or "").split()}
    changes = {}
    counts = Counter()
    unresolved = []
    destination_findings = []
    for obook, cbook in zip(obooks, cbooks, strict=True):
        book = crosswalk.get(obook.get("id"))
        if not book or cbook.get("osisID") != book:
            raise ReviewError("Source/cleaned book identity or order differs")
        original_notes = [x for x in obook.iter("x")]
        clean_notes = [x for x in cbook.iter(OSIS + "note")
                       if x.get("type") == "crossReference"]
        if len(original_notes) != len(clean_notes):
            raise ReviewError("Source/cleaned cross-reference note count mismatch")
        for src, note in zip(original_notes, clean_notes, strict=True):
            xo = _one_child(src, "xo")
            xt = _one_child(src, "xt")
            origin_refs = [e for e in note if
                           e.tag == OSIS + "reference" and
                           e.get("type") == "annotateRef" and
                           e.get("subType") == "x-origin"]
            destination_refs = [e for e in note if
                                e.tag == OSIS + "reference" and
                                e.get("type") is None and
                                e.get("subType") is None]
            if len(origin_refs) != 1 or len(destination_refs) != 1:
                raise ReviewError("Unreviewed cleaned note structure")
            if (note.get("n") != src.get("caller") or
                    _label(origin_refs[0]) != _label(xo) or
                    _label(destination_refs[0]) != _label(xt)):
                raise ReviewError("Mismatch in callout, note origin or printed destination")
            if complete_lists:
                destination_target, status, carried = _complete_printed_destinations(
                    _label(xt), destination_aliases, verse_ids)
                counts["explicit_semicolon_contexts_used"] += carried
            else:
                destination_target, status = _single_explicit_destination(
                    _label(xt), destination_aliases, verse_ids)
            if destination_target is None:
                if destination_refs[0].get("osisRef"):
                    raise ReviewError("Unreviewed printed destination already linked")
                counts["unlinked_original_destination_labels_preserved"] += 1
                counts["unlinked_destination_reason_" + status] += 1
                if (status in {"unverified_printed_book_alias",
                               "unattested_reference_start",
                               "unattested_or_reversed_reference_end"} and
                        len(destination_findings) < 100):
                    destination_findings.append({
                        "book": book, "source_origin": _label(xo),
                        "printed_destination": _label(xt)[:240],
                        "reason": status,
                    })
            else:
                if destination_refs[0].get("osisRef") not in (None, destination_target):
                    raise ReviewError("Printed destination conflicts with source-verified address")
                changes[destination_refs[0]] = destination_target
                counts["resolved_original_destination_labels"] += 1
                targets_in_label = len(destination_target.split())
                counts["resolved_destination_target_tokens"] += targets_in_label
                if targets_in_label > 1:
                    counts["multi_target_reference_labels"] += 1
            target = _origin_target(_label(xo), book, verse_ids)
            if origin_refs[0].get("osisRef") not in (None, target):
                raise ReviewError("Origin conflicts with an existing OSIS destination")
            changes[origin_refs[0]] = target
            counts["original_cross_reference_notes"] += 1

        original_spans = [x for x in obook.iter("ior")]
        clean_spans = [x for x in cbook.iter(OSIS + "reference")
                       if x.get("subType") == "x-introduction"]
        if len(original_spans) != len(clean_spans):
            raise ReviewError("Source/cleaned introduction section span count differs")
        for src, ref in zip(original_spans, clean_spans, strict=True):
            if _label(src) != _label(ref):
                raise ReviewError("Source/cleaned introduction span label differs")
            label = _label(src)
            reason = None
            try:
                target = _intro_target(label, book, verse_ids)
            except UnresolvedSourceTarget as exc:
                target, reason = None, str(exc)
                counts["unattested_introduction_targets_preserved"] += 1
            counts["original_introduction_spans"] += 1
            if target is None:
                if ref.get("osisRef"):
                    raise ReviewError("Unresolved original span already has an unsafe target")
                counts["unlinked_introduction_spans_preserved"] += 1
                unresolved.append({"book": book, "source_label": label,
                                   "reason": reason or "compound_or_narrative"})
                continue
            if ref.get("osisRef") not in (None, target):
                raise ReviewError("Introduction span conflicts with existing target")
            changes[ref] = target
            counts["resolved_introduction_spans"] += 1

    for key in ("original_cross_reference_notes",
                "unlinked_original_destination_labels_preserved",
                "resolved_original_destination_labels",
                "resolved_destination_target_tokens",
                "multi_target_reference_labels",
                "original_introduction_spans", "resolved_introduction_spans",
                "unlinked_introduction_spans_preserved"):
        counts.setdefault(key, 0)
    if len(changes) != (counts["original_cross_reference_notes"] +
                         counts["resolved_original_destination_labels"] +
                         counts["resolved_introduction_spans"]):
        raise ReviewError("Duplicate source witness binding")
    return changes, dict(counts), unresolved, destination_findings


def _patch_exact_start_tags(source: bytes, root, changes: dict) -> tuple[bytes, int]:
    """Insert only validated osisRef attributes; retain all other source bytes."""
    refs = list(root.iter(OSIS + "reference"))
    starts = list(OPEN_REFERENCE.finditer(source))
    if len(refs) != len(starts):
        raise ReviewError("Unexpected serialized reference opening tags")
    result = []
    cursor = 0
    edits = 0
    for node, match in zip(refs, starts, strict=True):
        if node not in changes or node.get("osisRef") == changes[node]:
            continue
        opening = match.group()
        if b"osisRef" in opening or opening.endswith(b"/>"):
            raise ReviewError("Unsafe or already-linked reference opening tag")
        value = changes[node].encode("ascii")
        if not re.fullmatch(rb"[A-Za-z0-9.\- ]+", value):
            raise ReviewError("Unsafe synthesized canonical source address")
        result.extend([source[cursor:match.end() - 1], b' osisRef="', value, b'">'])
        cursor = match.end()
        edits += 1
    result.append(source[cursor:])
    candidate = b"".join(result)
    # Byte reversibility: the only permitted differences are the exact
    # additive attributes, as witnessed by the reconstruction above.
    if candidate == source and edits:
        raise ReviewError("Unexpected empty candidate")
    return candidate, edits


def run(*, cleaned_path: Path, usfx_zip: Path, manifest_path: Path,
        crosswalk_path: Path, output_path: Path | None = None,
        destination_aliases_path: Path | None = None,
        complete_citation_lists: bool = False) -> tuple[bytes, dict]:
    if complete_citation_lists and destination_aliases_path is None:
        raise ReviewError("Complete reference lists require a pinned original-edition abbreviation witness")
    manifest = json.loads(_bytes(manifest_path, 256 * 1024).decode("utf-8"))
    current = _bytes(cleaned_path, MAX_SOURCE)
    zipped = _bytes(usfx_zip, MAX_SOURCE)
    if (sha256(current).hexdigest() != manifest.get("cleaned_osis_sha256") or
            sha256(zipped).hexdigest() != manifest.get("original_usfx_sha256")):
        raise ReviewError("Source/witness bytes differ from their approved manifest")
    source = _parse(current)
    original = _parse(_usfx_bytes(usfx_zip))
    if source.tag != OSIS + "osis" or original.tag != "usfx":
        raise ReviewError("Expected canonical OSIS and original USFX document")
    crosswalk = _crosswalk(crosswalk_path)
    aliases, alias_digest = (
        _printed_book_aliases(destination_aliases_path, crosswalk,
                              sha256(zipped).hexdigest())
        if destination_aliases_path is not None else (None, None)
    )
    changes, counts, unresolved, destination_findings = _source_bindings(
        source, original, crosswalk, aliases,
        complete_lists=complete_citation_lists)
    candidate, edits = _patch_exact_start_tags(current, source, changes)
    # Validate actual candidate XML, every edited target, and the unchanged
    # ordered contents of every text/tail/element. No lossy reserialization.
    after = _parse(candidate)
    before_nodes = list(source.iter())
    after_nodes = list(after.iter())
    if len(before_nodes) != len(after_nodes):
        raise ReviewError("Candidate changed XML node count")
    additions = 0
    for before, new in zip(before_nodes, after_nodes, strict=True):
        if before.tag != new.tag or before.text != new.text or before.tail != new.tail:
            raise ReviewError("Candidate changed XML content or element order")
        expected = dict(before.attrib)
        if before in changes:
            expected["osisRef"] = changes[before]
            if "osisRef" not in before.attrib:
                additions += 1
        if dict(new.attrib) != expected:
            raise ReviewError("Candidate modified another attribute or association")
    if additions != edits:
        raise ReviewError("Candidate attribute insertion count mismatch")
    report = {
        "kind": "source_pinned_structural_reference_candidate",
        "source_sha256": sha256(current).hexdigest(),
        "original_usfx_zip_sha256": sha256(zipped).hexdigest(),
        "candidate_sha256": sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "exact_original_xml_text_and_element_order_preserved": True,
        "only_source_attested_reference_osisRef_attributes_added": True,
        "source_unchanged": True,
        "candidate_additions": additions,
        "unresolved_source_introduction_spans": unresolved,
        "unresolved_explicit_source_destination_findings": destination_findings,
        "existing_attributes_rewritten": 0,
        "unverified_authorial_destinations_guessed": 0,
        "complete_citation_lists_enabled": complete_citation_lists,
        "printed_abbreviation_map_sha256": alias_digest,
        "machine_destinations_interpreted_from_complete_explicit_labels":
            counts["resolved_original_destination_labels"],
        "original_note_text_deleted": 0,
        "original_section_labels_deleted": 0,
        "published_release_approved": False,
        **counts,
    }
    if output_path is not None:
        if output_path.resolve() in {p.resolve() for p in (
                cleaned_path, usfx_zip, manifest_path, crosswalk_path,
                *([destination_aliases_path] if destination_aliases_path else []))}:
            raise ReviewError("Refusing to overwrite cleaned or original source")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".candidate-", dir=output_path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(candidate)
            os.replace(temp, output_path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return candidate, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleaned", type=Path, required=True)
    parser.add_argument("--original-usfx", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--destination-aliases", type=Path,
                        help="Exact edition-printed abbreviation witness, optional")
    parser.add_argument("--complete-citation-lists", action="store_true",
                        help="Parse only fully consumed source-attested citation grammar")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.cleaned.resolve(), args.original_usfx.resolve(),
                                 args.manifest.resolve(), args.crosswalk.resolve(),
                                 args.report.resolve(),
                                 *([args.destination_aliases.resolve()]
                                   if args.destination_aliases else [])}:
        parser.error("All sources, candidate and report must be separate paths")
    try:
        _, report = run(
            cleaned_path=args.cleaned, usfx_zip=args.original_usfx,
            manifest_path=args.manifest, crosswalk_path=args.crosswalk,
            destination_aliases_path=args.destination_aliases,
            complete_citation_lists=args.complete_citation_lists,
            output_path=args.output,
        )
    except (ReviewError, OSError, ValueError, etree.XMLSyntaxError) as exc:
        parser.exit(2, f"Normalization blocked: {exc}\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Candidate only, no publication:", report["candidate_additions"],
          "source-attested OSIS reference associations added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
