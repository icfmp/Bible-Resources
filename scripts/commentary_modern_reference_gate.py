#!/usr/bin/env python3
"""Compare original SWORD commentary links with draft markers without source export.

This reads exact original native XML *privately* through the project's existing
complete real-SWORD stream reader, fails closed on the pinned corpus SHA, and
reports only predeclared link identity hashes/booleans. It never infers links
from verse positions or changes an existing authorial source reference.
It is NOT a semantic or final OSIS source-link preservation approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus

from research.commentary.commentary_link_disposition_review import (
    validate_proposed_link_dispositions,
)

from research.commentary.commentary_original_link_identity import (
    _SHA, _REF, canonical_only_for_comparison,
    SourceReferenceGate, WholeCanonOriginalLinkIdentityReceipt,
)


def run_whole_native_link_identity(*, reader: Path, root: Path,
                                    module_id: str, native_receipt: Path) -> dict:
    native = json.loads(native_receipt.read_text(encoding="utf-8"))
    gate = WholeCanonOriginalLinkIdentityReceipt(native)
    env = os.environ.copy()
    env["SWORD_PATH"] = str(root.resolve())
    proc = subprocess.Popen([str(reader.resolve()), module_id], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Original native raw stream is unavailable")
        complete, *_ = parse_native_raw_corpus(proc.stdout, on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=30) != 0:
            raise ValueError("Original native raw reader failed")
        return gate.report(complete)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()



def _wrap_exact_authored_modern_text(section: ET.Element, *, anchor: str,
                                      display: str, occurrence: str,
                                      target: str) -> None:
    """Insert one reviewed Bible link without changing ANY modern visible prose.

    One full authored citation anchor must be present in exactly one XML text
    slot of one source-indexed section. No fuzzy search, source-word rewriting,
    markup flattening or implicit verse guessing is permitted.
    """
    if (not isinstance(anchor, str) or not anchor or len(anchor) > 512
            or not isinstance(display, str) or not display
            or display not in anchor or occurrence not in ("first", "last")
            or not _allowed_source_link_target(target)):
        raise ValueError("Invalid reviewed modern citation/text placement")
    positions = []
    for node in section.iter():
        # A source body can legitimately contain several distinct hyperlinks.
        # Existing reference *text* is protected against nested wrapping;
        # its trailing text is ordinary modern prose and can hold a next link.
        already_ref = node.tag.rsplit("}", 1)[-1] == "reference"
        for kind in ("text", "tail"):
            if already_ref and kind == "text":
                continue
            slot = getattr(node, kind)
            if isinstance(slot, str) and anchor in slot:
                for _ in range(slot.count(anchor)):
                    positions.append((node, kind, slot))
    if len(positions) != 1:
        raise ValueError("Reviewed modern citation anchor is missing or ambiguous")
    node, kind, original = positions[0]
    anchor_start = original.find(anchor)
    inner_at = (anchor.rfind(display) if occurrence == "last"
                else anchor.find(display))
    if inner_at < 0:
        raise ValueError("Reviewed linked text missing inside its full anchor")
    start = anchor_start + inner_at
    end = start + len(display)
    before, after = original[:start], original[end:]
    old_prose = "".join(section.itertext())
    ref = ET.Element("{http://www.bibletechnologies.net/2003/OSIS/namespace}reference",
                     {"osisRef": target})
    ref.text = display
    ref.tail = after
    if kind == "text":
        node.text = before
        node.insert(0, ref)
    else:
        parent = next((p for p in section.iter() if node in list(p)), None)
        if parent is None:
            raise ValueError("Reviewed citation tail has no XML parent")
        node.tail = before
        parent.insert(list(parent).index(node) + 1, ref)
    if "".join(section.itertext()) != old_prose:
        raise ValueError("Link insertion must not modify modern authorial visible text")


# This generic concordance is a *recognition* aid, not a replacement for
# authored Scripture references. Only exact, full "Book chapter:verse" forms
# inside one real modern commentary K body can be auto-attached to an
# authenticated original osisRef. Ranges and ellipses are NEVER guessed.
_ENGLISH_CANONICAL_NAMES = (
    "Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    "1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|"
    "Ezra|Nehemiah|Esther|Job|Psalm|Proverbs|Ecclesiastes|Song of Solomon|"
    "Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|"
    "Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|"
    "Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|"
    "Galatians|Ephesians|Philippians|Colossians|1 Thessalonians|"
    "2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|Hebrews|James|"
    "1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation"
).split("|")
from commentary_modern_draft_osis_preview import _CANON as _ORIGINAL_CANON
if len(_ENGLISH_CANONICAL_NAMES) != len(_ORIGINAL_CANON):
    raise RuntimeError("Canonical Bible book-name mapping cannot be trusted")
_ENGLISH_NAME_BY_OSIS = dict(zip(_ORIGINAL_CANON, _ENGLISH_CANONICAL_NAMES))
_ENGLISH_NAME_BY_OSIS["Ps"] = "Psalm"
# Exact, conventional, period-terminated English book abbreviations can be
# matched only inside the already authenticated source-owned K exposition.
# Do not accept unpunctuated lookalikes or infer any abbreviated verse numbers.
_AUTO_ALIASES = {
    "Gen": ("Genesis", "Gen."),
    "Exod": ("Exodus", "Exod.", "Ex."),
    "Lev": ("Leviticus", "Lev."),
    "Num": ("Numbers", "Num."),
    "Deut": ("Deuteronomy", "Deut."),
    "Josh": ("Joshua", "Josh."),
    "Judg": ("Judges", "Judg."),
    "1Sam": ("1 Samuel", "1 Sam."),
    "2Sam": ("2 Samuel", "2 Sam."),
    "1Kgs": ("1 Kings", "1 Kgs."),
    "2Kgs": ("2 Kings", "2 Kgs."),
    "1Chr": ("1 Chronicles", "1 Chr."),
    "2Chr": ("2 Chronicles", "2 Chr."),
    "Neh": ("Nehemiah", "Neh."),
    "Esth": ("Esther", "Esth."),
    "Ps": ("Psalm", "Psalms", "Ps."),
    "Prov": ("Proverbs", "Prov."),
    "Eccl": ("Ecclesiastes", "Eccl."),
    "Song": ("Song of Solomon", "Song of Songs"),
    "Isa": ("Isaiah", "Isa."),
    "Jer": ("Jeremiah", "Jer."),
    "Ezek": ("Ezekiel", "Ezek."),
    "Dan": ("Daniel", "Dan."),
    "Hos": ("Hosea", "Hos."),
    "Zech": ("Zechariah", "Zech."),
    "Matt": ("Matthew", "Matt."),
    "Mark": ("Mark", "Mk."),
    "Luke": ("Luke", "Lk."),
    "John": ("John", "Jn."),
    "Acts": ("Acts", "Acts."),
    "Rom": ("Romans", "Rom."),
    "1Cor": ("1 Corinthians", "1 Cor."),
    "2Cor": ("2 Corinthians", "2 Cor."),
    "Gal": ("Galatians", "Gal."),
    "Eph": ("Ephesians", "Eph."),
    "Phil": ("Philippians", "Phil."),
    "Col": ("Colossians", "Col."),
    "1Thess": ("1 Thessalonians", "1 Thess."),
    "2Thess": ("2 Thessalonians", "2 Thess."),
    "1Tim": ("1 Timothy", "1 Tim."),
    "2Tim": ("2 Timothy", "2 Tim."),
    "Heb": ("Hebrews", "Heb."),
    "Jas": ("James", "Jas."),
    "1Pet": ("1 Peter", "1 Pet."),
    "2Pet": ("2 Peter", "2 Pet."),
    "1John": ("1 John", "1 Jn."),
    "2John": ("2 John", "2 Jn."),
    "3John": ("3 John", "3 Jn."),
    "Rev": ("Revelation", "Rev."),
}


def _unambiguous_explicit_modern_verse(section: ET.Element, target: str):
    """Find one literal English full-name single-verse citation, otherwise None.

    No source XML or modern prose is changed by this recognition function.
    In particular it deliberately rejects 3:16–17, 3:16,17, ambiguous
    repetitions, existing links and citations that cross markup boundaries.
    """
    canonical = canonical_only_for_comparison(target)
    book, chapter, verse = canonical.rsplit(".", 2)
    names = _AUTO_ALIASES.get(book, (_ENGLISH_NAME_BY_OSIS.get(book),))
    if any(not x for x in names):
        return None
    candidates = []
    for name in names:
        regex = re.compile(r"(?<![A-Za-z0-9])" + re.escape(name) +
                           r"\s+" + re.escape(chapter) + ":" +
                           re.escape(verse) + r"(?![0-9])", re.I)
        for paragraph in section.iter():
            if paragraph.tag.rsplit("}",1)[-1] != "p":
                continue
            for node in paragraph.iter():
                if not isinstance(node.tag, str):
                    continue
                # Never overwrite existing reviewed links, but allow tails.
                for part in ("text", "tail"):
                    if part == "text" and node.tag.rsplit("}", 1)[-1] == "reference":
                        continue
                    value = getattr(node, part)
                    if not isinstance(value, str):
                        continue
                    for hit in regex.finditer(value):
                        suffix = value[hit.end():]
                        prefix = value[:hit.start()]
                        # "John 3:16" must not match inside "1 John 3:16".
                        if (book == "John" and
                                re.search(r"(?:^|[^A-Za-z0-9])[1-3]\s+$", prefix)):
                            continue
                        if re.match(r"\s*[-–—,]\s*\d", suffix):
                            continue
                        candidates.append(hit[0])
    return candidates[0] if len(candidates) == 1 else None



_SOURCE_FULL_RANGE = re.compile(
    r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)-"
    r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)$")


def _source_same_chapter_verse_range(literal: str):
    """Parse ONLY original full OSIS ranges with one book and chapter.

    Preserve the source literal in the final XML, including any work prefix.
    This is no general conversion of OSIS expression syntax or versification.
    """
    if not isinstance(literal, str):
        return None
    raw = literal[6:] if literal.startswith("Bible:") else literal
    hit = _SOURCE_FULL_RANGE.fullmatch(raw)
    if not hit:
        return None
    book, chapter, start, end_book, end_chapter, end = hit.groups()
    if (book != end_book or chapter != end_chapter
            or book not in _ENGLISH_NAME_BY_OSIS
            or not 1 <= int(start) < int(end) <= 200):
        return None
    if any(s.startswith("0") for s in (chapter, start, end)):
        return None
    return book, chapter, start, end



def _allowed_source_link_target(target: str) -> bool:
    try:
        canonical_only_for_comparison(target)
        return True
    except ValueError:
        return _source_same_chapter_verse_range(target) is not None


def _unambiguous_explicit_modern_range(section: ET.Element, literal: str):
    """Return one explicit same-book same-chapter modern 3:16–18, else None."""
    parsed = _source_same_chapter_verse_range(literal)
    if parsed is None:
        return None
    book, chapter, first, last = parsed
    names = _AUTO_ALIASES.get(book, (_ENGLISH_NAME_BY_OSIS.get(book),))
    matches=[]
    for name in names:
        if not name:
            continue
        rex=re.compile(r"(?<![A-Za-z0-9])" + re.escape(name) + r"\s+" +
                       re.escape(chapter) + ":" + re.escape(first) +
                       r"\s*[-–—]\s*" + re.escape(last) + r"(?![0-9])", re.I)
        for para in section.iter():
            if para.tag.rsplit("}",1)[-1] != "p":
                continue
            for node in para.iter():
                if not isinstance(node.tag,str):
                    continue
                for field in ("text","tail"):
                    if field=="text" and node.tag.rsplit("}",1)[-1]=="reference":
                        continue
                    slot=getattr(node,field)
                    if not isinstance(slot,str):
                        continue
                    for match in rex.finditer(slot):
                        prefix,suffix=slot[:match.start()],slot[match.end():]
                        if book=="John" and re.search(
                            r"(?:^|[^A-Za-z0-9])[1-3]\s+$",prefix):
                            continue
                        if re.match(r"\s*[-–—,]\s*\d",suffix):
                            continue
                        matches.append(match[0])
    return matches[0] if len(matches)==1 else None


def _source_range_section_ownership(*, literal: str, label: str,
                                    source_chapter: str, keys: list[str],
                                    section: ET.Element) -> dict[str, bool]:
    """Diagnostic only: does a genuine source self-range own a modern heading?

    Exact authored K key occupancy is decisive. A source cross-reference to
    another passage must never be silently relocated to an editorial heading.
    This classifier returns no text and does not add a hyperlink.
    """
    parsed = _source_same_chapter_verse_range(literal)
    if parsed is None:
        return {"same_chapter":False,"exact_K_scope":False,
                "matching_modern_heading":False,"source_label_is_verse_span":False}
    book, chapter, first, last = parsed
    same=source_chapter==book+"."+chapter
    from commentary_modern_draft_osis_preview import NS, _range
    target=literal[6:] if literal.startswith("Bible:") else literal
    exact=same and target==_range(keys)
    names=[v for v in section.findall(f"./{{{NS}}}title") if
           v.get("type")=="sub"]
    pattern=re.compile(r"\bverses?\s+"+re.escape(first)+
                       r"\s*[-–—]\s*"+re.escape(last)+r"\b", re.I)
    title=exact and len(names)==1 and bool(pattern.search(
        "".join(names[0].itertext())))
    source_label=re.fullmatch(
        r"(?:v(?:erses?)?\.?\s*)?"+re.escape(first)+r"\s*[-–—]\s*"+
        re.escape(last)+r"\.?", label.strip(), re.I)
    return {"same_chapter":same,"exact_K_scope":exact,
            "matching_modern_heading":bool(title),
            "source_label_is_verse_span":bool(source_label)}




def _find_exact_modern_original_outline_range_cell(
        modern_chapter: ET.Element, literal: str) -> ET.Element | None:
    """The ONE manuscript outline-table verse cell matching a source OSIS span.

    This does not infer new ranges, transpose chapter order or rewrite any
    authorial text; it returns None on missing, ambiguous or decorated cells.
    """
    parsed=_source_same_chapter_verse_range(literal)
    if parsed is None:
        return None
    book,chapter,start,end=parsed
    if modern_chapter.get("osisID")!=book+"."+chapter:
        return None
    from commentary_modern_draft_osis_preview import NS
    matches=[]
    for intro in modern_chapter.findall(f"./{{{NS}}}div[@type='introduction']"):
        titles=intro.findall(f"./{{{NS}}}title")
        if len(titles)!=1 or titles[0].text!="Original chapter outline":
            continue
        tables=intro.findall(f"./{{{NS}}}table")
        if len(tables)!=1:
            continue
        rows=tables[0].findall(f"./{{{NS}}}row")
        if len(rows)<2:
            continue
        header=rows[0].findall(f"./{{{NS}}}cell")
        if (len(header)!=2 or
                "".join(header[0].itertext()).strip()!="Original outline" or
                "".join(header[1].itertext()).strip()!="Verses"):
            continue
        for row in rows[1:]:
            cells=row.findall(f"./{{{NS}}}cell")
            if len(cells)!=2:
                continue
            text="".join(cells[1].itertext()).strip()
            if re.fullmatch(re.escape(start)+r"\s*[-–—]\s*"+re.escape(end),text):
                matches.append(cells[1])
    return matches[0] if len(matches)==1 else None

def _source_first_K_outline_row_evidence(*, literal: str, label: str,
                                         first_key: str, native_chapter: dict,
                                         modern_chapter: ET.Element) -> dict[str,bool]:
    """Classify authenticated original chapter-outline links without editing.

    Original cross-references must not be conflated with source-K outline
    navigation, which is often carried inside the first original K body but
    is represented by a separate original-outline table in modern manuscripts.
    """
    result={"source_first_K_owns_link":False,
            "unique_modern_outline_row_matches_source_target":False,
            "original_visible_label_explicitly_names_same_verse_span":False}
    parsed=_source_same_chapter_verse_range(literal)
    if parsed is None:
        return result
    book, chapter, first, last=parsed
    if modern_chapter.get("osisID")!=book+"."+chapter:
        return result
    units=native_chapter.get("original_units",[])
    if not units or units[0]["first_key"]!=first_key:
        return result
    result["source_first_K_owns_link"]=True
    result["unique_modern_outline_row_matches_source_target"]=(
        _find_exact_modern_original_outline_range_cell(
            modern_chapter,literal) is not None)
    # No arbitrary source prose: the original visible link's numeric chapter
    # and verse span must agree too (e.g., "Is. 1:1-9").
    result["original_visible_label_explicitly_names_same_verse_span"]=bool(
        re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z .]{0,28}\s+"+
                     re.escape(chapter)+":"+re.escape(first)+
                     r"\s*[-–—]\s*"+re.escape(last),label.strip()))
    return result



_AUTHENTIC_SINGLE_VERSE_LABEL = re.compile(
    r"^((?:[1-4]\s*)?[A-Za-z][A-Za-z. ]{0,27}?)\s+"
    r"([1-9][0-9]{0,2}):([1-9][0-9]{0,2})\.?$")


def _unique_authentic_original_visible_label(
        section: ET.Element, literal: str, label: str) -> str | None:
    """Match the *source-owned* printed single-verse citation, unchanged.

    A fallback for abbreviations already authored in both editions; it cannot
    invent a target, modern wording, link location, a Bible book identity or a
    range. The exact original osisRef and link-label hashes are authenticated
    separately by the full original native SWORD reader.
    """
    try:
        book, chapter, verse = canonical_only_for_comparison(literal).rsplit(".", 2)
    except ValueError:
        return None
    name = _ENGLISH_NAME_BY_OSIS.get(book)
    raw = label.strip()
    match = _AUTHENTIC_SINGLE_VERSE_LABEL.fullmatch(raw)
    if not name or match is None or match[2] != chapter or match[3] != verse:
        return None
    def norm(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.casefold())
    permitted = {norm(book), norm(re.sub(r"^([1-4])([A-Z])", r"\1 \2", book)),
                 norm(name)}
    if book=="Ps":
        permitted.update(("ps", "psalm", "psalms"))
    if book=="Song":
        permitted.update(("songofsolomon", "songofsongs"))
    if norm(match[1]) not in permitted:
        return None
    instances=[]
    from commentary_modern_draft_osis_preview import NS
    for p in section.iter():
        if p.tag!=f"{{{NS}}}p":
            continue
        for node in p.iter():
            for field in ("text","tail"):
                if field=="text" and node.tag==f"{{{NS}}}reference":
                    continue
                value=getattr(node,field)
                if not isinstance(value,str):
                    continue
                at=0
                while True:
                    i=value.find(raw,at)
                    if i<0:
                        break
                    j=i+len(raw)
                    if ((i==0 or not value[i-1].isalnum()) and
                            (j==len(value) or not value[j].isalnum())):
                        instances.append(raw)
                    at=i+1
    return instances[0] if len(instances)==1 else None


def _full_endpoint_source_range_rejection(literal: str) -> str:
    """Explain why an original two-endpoint range needs manual review.

    This is a source-literal grammar diagnostic only. In particular,
    cross-book/chapter intervals are not automatically made navigable;
    canonical book identity and versification must be reviewed separately.
    No source target spelling or prose is returned.
    """
    if not isinstance(literal, str):
        return "NOT_TWO_ENDPOINT_RANGE"
    raw = literal[6:] if literal.startswith("Bible:") else literal
    match = _SOURCE_FULL_RANGE.fullmatch(raw)
    if match is None:
        return "NOT_TWO_ENDPOINT_RANGE"
    book, chapter, first, end_book, end_chapter, last = match.groups()
    if book not in _ENGLISH_NAME_BY_OSIS or end_book not in _ENGLISH_NAME_BY_OSIS:
        return "UNRECOGNIZED_BOOK_CODE"
    if book != end_book:
        return "CROSS_BOOK_RANGE"
    if chapter != end_chapter:
        return "CROSS_CHAPTER_RANGE"
    if any(s.startswith("0") for s in (chapter, first, last)):
        return "ZERO_OR_NONCANONICAL_NUMERIC_SPELLING"
    if int(first) == int(last):
        return "DEGENERATE_SAME_VERSE_RANGE"
    if int(first) > int(last):
        return "REVERSED_SAME_CHAPTER_RANGE"
    if int(last) > 200:
        return "OUTSIDE_BOUNDED_VERSE_RANGE"
    return "VALID_SAME_CHAPTER_RANGE_UNEXPECTEDLY_UNPLACED"


def _unrecognized_original_ref_class(literal: str) -> str:
    """Only classify syntax in metadata; never emit literal source osisRef."""
    raw = literal[6:] if literal.startswith("Bible:") else literal
    atom = r"[1-4]?[A-Za-z][A-Za-z0-9]*\.\d+\.\d+"
    if re.fullmatch(atom + "-" + atom, raw):
        return "full_verse_range"
    if re.fullmatch(atom + r"-\d+", raw):
        return "abbreviated_verse_range"
    if re.fullmatch(atom + r"\s+" + atom + r"(?:\s+" + atom + ")*", raw):
        return "space_joined_verses"
    if re.fullmatch(atom + r"[;,]\s*" + atom + r"(?:[;,]\s*" + atom + ")*", raw):
        return "punctuation_joined_verses"
    if re.match(atom + r"-", raw):
        return "other_range_syntax"
    if re.search(r"[\s;,]", raw):
        return "other_compound_syntax"
    return "other_original_syntax"


def _auto_single_verse_placements(*, private_original: dict, groups: dict,
                                  modern_chapters: dict, native: dict,
                                  blocked: set, corrections: dict,
                                  include_ranges: bool = False,
                                  include_outline_links: bool = False,
                                  include_authentic_labels: bool = False):
    """Return conservative placements plus classified counts, no private text."""
    from commentary_modern_draft_osis_preview import NS, _range
    found = []
    skipped = {"already_reviewed": 0, "proposed_original_correction": 0,
               "unsupported_original_reference_syntax": 0,
               "unrecognized_format_full_verse_range":0,
               "unrecognized_format_abbreviated_verse_range":0,
               "unrecognized_format_space_joined_verses":0,
               "unrecognized_format_punctuation_joined_verses":0,
               "unrecognized_format_other_range_syntax":0,
               "unrecognized_format_other_compound_syntax":0,
               "unrecognized_format_other_original_syntax":0,
               "repeated_original_target": 0, "unverified_or_single_digit_label": 0,
               "no_unique_full_modern_verse_citation": 0,
               "no_unique_full_modern_verse_range_citation":0,
               "matching_unique_authenticated_original_visible_label":0,
               "source_range_spans_chapters_or_has_unsafe_bounds":0,
               "unmatched_source_range_same_chapter":0,
               "unmatched_source_range_exact_original_K_scope":0,
               "unmatched_source_range_exact_K_scope_with_modern_heading":0,
               "unmatched_source_range_source_label_matches_scope":0,
               "unmatched_source_range_first_K_owns_chapter_outline_link":0,
               "unmatched_source_range_unique_modern_outline_row":0,
               "unmatched_source_range_outline_row_and_source_label_match":0}
    for first, links in private_original.items():
        chapter = first.rsplit(".", 1)[0]
        units = native["chapters"][chapter]["original_units"]
        ordinal = next(i for i, u in enumerate(units) if u["first_key"] == first)
        sections = modern_chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(units):
            raise ValueError("Source-group count changed during automatic citation lookup")
        section = sections[ordinal]
        if section.get("annotateRef") != _range(units[ordinal]["keys"]):
            raise ValueError("Auto lookup cannot use a non-original commentary scope")
        targets=[]
        for literal, _ in links:
            try:
                targets.append(canonical_only_for_comparison(literal))
            except ValueError:
                # Full original range syntax remains an immutable source
                # literal. Never infer abbreviated or cross-chapter spans.
                parsed=(_source_same_chapter_verse_range(literal)
                        if include_ranges else None)
                if parsed is not None:
                    targets.append("RANGE:"+
                        (literal[6:] if literal.startswith("Bible:") else literal))
                else:
                    targets.append(None)
        for pos, (literal, label) in enumerate(links, 1):
            key = (first, pos)
            if key in blocked:
                skipped["already_reviewed"] += 1
                continue
            if key in corrections:
                skipped["proposed_original_correction"] += 1
                continue
            canon = targets[pos-1]
            if canon is None:
                skipped["unsupported_original_reference_syntax"] += 1
                syntax = _unrecognized_original_ref_class(literal)
                skipped["unrecognized_format_"+syntax] += 1
                continue
            if targets.count(canon) != 1:
                skipped["repeated_original_target"] += 1
                continue
            if not label.strip() or re.fullmatch(r"[1-9]", label.strip()):
                skipped["unverified_or_single_digit_label"] += 1
                continue
            is_range=canon.startswith("RANGE:")
            if is_range:
                display=_unambiguous_explicit_modern_range(section,literal)
            else:
                display=_unambiguous_explicit_modern_verse(section,literal)
            if display is None and not is_range and include_authentic_labels:
                # Distinct source links sharing an identical printed marker
                # cannot be disambiguated by a unique modern text occurrence.
                original_label_occurrences=sum(
                    old_label.strip()==label.strip()
                    for _,old_label in links)
                authentic=(_unique_authentic_original_visible_label(
                    section,literal,label)
                    if original_label_occurrences==1 else None)
                if authentic is not None:
                    skipped["matching_unique_authenticated_original_visible_label"]+=1
                    found.append({
                        "modern_chapter": chapter,
                        "source_first_key": first,
                        "original_link_ordinal": pos,
                        "action": "AUTO_UNIQUE_AUTHENTIC_ORIGINAL_SINGLE_VERSE_LABEL",
                        "expected_modern_target": canon,
                        "modern_anchor": authentic,
                        "linked_display_text": authentic,
                        "display_occurrence": "last",
                    })
                    continue
            if display is None:
                if is_range:
                    ownership=_source_range_section_ownership(
                        literal=literal,label=label,source_chapter=chapter,
                        keys=units[ordinal]["keys"],section=section)
                    for field,category in (
                        ("same_chapter","unmatched_source_range_same_chapter"),
                        ("exact_K_scope","unmatched_source_range_exact_original_K_scope"),
                        ("matching_modern_heading",
                         "unmatched_source_range_exact_K_scope_with_modern_heading"),
                        ("source_label_is_verse_span",
                         "unmatched_source_range_source_label_matches_scope")):
                        if ownership[field]:
                            skipped[category]+=1
                    outline=_source_first_K_outline_row_evidence(
                        literal=literal,label=label,first_key=first,
                        native_chapter=native["chapters"][chapter],
                        modern_chapter=modern_chapters[chapter])
                    if outline["source_first_K_owns_link"]:
                        skipped["unmatched_source_range_first_K_owns_chapter_outline_link"]+=1
                    if outline["unique_modern_outline_row_matches_source_target"]:
                        skipped["unmatched_source_range_unique_modern_outline_row"]+=1
                    if (outline["unique_modern_outline_row_matches_source_target"]
                            and outline["original_visible_label_explicitly_names_same_verse_span"]):
                        skipped["unmatched_source_range_outline_row_and_source_label_match"]+=1
                        if include_outline_links and outline["source_first_K_owns_link"]:
                            cell=_find_exact_modern_original_outline_range_cell(
                                modern_chapters[chapter],literal)
                            if cell is None:
                                raise ValueError("Source-attested outline range cell vanished")
                            cell_text="".join(cell.itertext()).strip()
                            found.append({
                                "modern_chapter":chapter,
                                "source_first_key":first,
                                "original_link_ordinal":pos,
                                "action":"AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE",
                                "expected_modern_target":canon,
                                "modern_anchor":cell_text,
                                "linked_display_text":cell_text,
                                "display_occurrence":"last",
                            })
                            continue
                skipped["no_unique_full_modern_verse_range_citation" if is_range
                        else "no_unique_full_modern_verse_citation"] += 1
                continue
            found.append({
                "modern_chapter": chapter,
                "source_first_key": first,
                "original_link_ordinal": pos,
                "action": ("AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE"
                          if is_range else
                          "AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_VERSE"),
                "expected_modern_target": canon,
                "modern_anchor": display,
                "linked_display_text": display,
                "display_occurrence": "last",
            })
    return found, skipped



def _original_reference_table_ownership(fragment: ET.Element) -> list[bool]:
    """Source-native reference ancestry, in exact original document order.

    Tables and their nested XML containers are tracked without exporting
    original prose, headings, link labels or raw OSIS reference values.
    """
    result=[]
    def visit(node: ET.Element, in_table: bool) -> None:
        if not isinstance(node.tag,str):
            return
        tag=node.tag.rsplit("}",1)[-1]
        current=in_table or tag=="table"
        if tag=="reference":
            result.append(current)
        for child in node:
            visit(child,current)
    visit(fragment,False)
    return result



def _original_reference_title_ownership(fragment: ET.Element) -> list[bool]:
    """Track authentic title-contained hyperlinks, never source text."""
    flags=[]
    def walk(node: ET.Element, inside_title: bool) -> None:
        if not isinstance(node.tag,str):
            return
        tag=node.tag.rsplit("}",1)[-1]
        inside=inside_title or tag=="title"
        if tag=="reference":
            flags.append(inside)
        for child in node:
            walk(child,inside)
    walk(fragment,False)
    return flags



def _original_label_in_modern_k(section: ET.Element, label: str) -> str:
    """Classify verbatim printed-label presence without exporting source words.

    A non-distinctive one-digit or bare-number label is never treated as
    evidence of a biblical citation. A unique match is *diagnostic only*:
    its presence does not establish correct target, scope or link placement.
    """
    from commentary_modern_draft_osis_preview import NS

    needle = label.strip()
    if (len(needle) < 5 or not re.search(r"[A-Za-z]", needle)
            or not re.search(r"[0-9]", needle)):
        return "NON_DISTINCTIVE_NOT_SCANNED"
    count = 0
    for paragraph in section.iter():
        if paragraph.tag != f"{{{NS}}}p":
            continue
        for node in paragraph.iter():
            if not isinstance(node.tag, str):
                continue
            for field in ("text", "tail"):
                if (field == "text"
                        and node.tag == f"{{{NS}}}reference"):
                    continue
                fragment = getattr(node, field)
                if not isinstance(fragment, str):
                    continue
                for hit in re.finditer(re.escape(needle), fragment):
                    start, end = hit.span()
                    # A source "John 3:16" label must not match inside
                    # "1 John 3:16" (or 2/3 John); nor may any unnumbered
                    # book label inherit a preceding numbered-book prefix.
                    prefix = fragment[:start]
                    numbered_book_prefix = (
                        not re.match(r"^[1-4]\s", needle)
                        and bool(re.search(
                            r"(?:^|[^A-Za-z0-9])[1-4]\s+$", prefix)))
                    if (not numbered_book_prefix
                            and (start == 0
                                 or not fragment[start - 1].isalnum())
                            and (end == len(fragment)
                                 or not fragment[end].isalnum())):
                        count += 1
                        if count > 1:
                            return "REPEATED_NOT_UNIQUE"
    return "UNIQUE_VERBATIM" if count == 1 else "ABSENT_VERBATIM"


def _unplaced_original_link_review_ledger(*, original: dict, insertions: list,
                                           corrections: dict,
                                           source_table_ownership: dict | None = None,
                                           source_title_ownership: dict | None = None,
                                           modern_chapters: dict | None = None,
                                           native: dict | None = None) -> dict:
    """Account for every original hyperlink without exporting source text.

    The optional authenticated K/ordinal context adds source-ancestry and
    exact label-correspondence diagnostics. Neither diagnostic grants
    automatic placement or editorial approval, and no source literal leaves
    the isolated native-SWORD workflow.
    """
    context = (source_table_ownership, source_title_ownership,
               modern_chapters, native)
    if any(value is not None for value in context) and any(
            value is None for value in context):
        raise ValueError("Original link review context must be complete")
    with_context = all(value is not None for value in context)
    section_by_first = {}
    if with_context:
        from commentary_modern_draft_osis_preview import NS, _range
        if set(original) != set(source_table_ownership) or set(original) != set(
                source_title_ownership):
            raise ValueError("Original source link ancestry K inventory changed")
        for first, links in original.items():
            if (len(source_table_ownership[first]) != len(links)
                    or len(source_title_ownership[first]) != len(links)
                    or any(type(flag) is not bool for flag in
                           source_table_ownership[first] + source_title_ownership[first])):
                raise ValueError("Original source link ordinal ancestry changed")
            chapter = first.rsplit(".", 1)[0]
            units = native["chapters"][chapter]["original_units"]
            index = next((i for i, unit in enumerate(units)
                          if unit["first_key"] == first), None)
            if index is None:
                raise ValueError("Original source section missing for link review")
            sections = modern_chapters[chapter].findall(
                f"./{{{NS}}}div[@annotateType='commentary']")
            if (len(sections) != len(units)
                    or sections[index].get("annotateRef") != _range(units[index]["keys"])):
                raise ValueError("Modern section/source-K ownership changed")
            section_by_first[first] = sections[index]
    placed={}
    for row in insertions:
        ordinal=row.get("original_link_ordinal")
        if ordinal is None:
            continue  # separately supported authored witness, not original markup
        key=(row["original_source_first_key"],ordinal)
        if key in placed:
            raise ValueError("Original source link was independently placed twice")
        placed[key]=row["placement_action"]
    seen=set()
    omitted=[]
    pending=[]
    for first,links in sorted(original.items()):
        for ordinal,(target,label) in enumerate(links,1):
            key=(first,ordinal)
            if key in seen:
                raise ValueError("Duplicate source link occurrence in original inventory")
            seen.add(key)
            if key in placed:
                continue
            correction=corrections.get(key)
            if correction is not None:
                if correction.get("disposition")!="OMIT_SPURIOUS_ENUMERATOR_LINK":
                    raise ValueError("Documented original link correction was never applied")
                status="EXPLICITLY_OMITTED_SPURIOUS_NATIVE_HYPERLINK"
            else:
                try:
                    canonical_only_for_comparison(target)
                    status="UNPLACED_SINGLE_VERSE_REFERENCE"
                except ValueError:
                    if _source_same_chapter_verse_range(target):
                        status="UNPLACED_SAME_CHAPTER_VERSE_RANGE"
                    else:
                        status="UNPLACED_OTHER_OR_COMPOSITE_OSIS_TARGET"
            item={
                "source_first_key":first,
                "source_reference_ordinal":ordinal,
                "original_osisRef_sha256":hashlib.sha256(
                    target.encode("utf-8")).hexdigest(),
                "original_visible_label_sha256":hashlib.sha256(
                    label.encode("utf-8")).hexdigest(),
                "disposition":status
            }
            if with_context:
                in_table = source_table_ownership[first][ordinal - 1]
                in_title = source_title_ownership[first][ordinal - 1]
                item["native_markup_location"] = (
                    "TABLE_AND_TITLE" if in_table and in_title else
                    "TABLE" if in_table else "TITLE" if in_title else
                    "EXPOSITION_OR_OTHER")
                item["original_target_grammar"] = (
                    "SINGLE_VERSE" if status == "UNPLACED_SINGLE_VERSE_REFERENCE"
                    else "SAME_CHAPTER_FULL_RANGE"
                    if status == "UNPLACED_SAME_CHAPTER_VERSE_RANGE"
                    else _unrecognized_original_ref_class(target))
                if item["original_target_grammar"] == "full_verse_range":
                    item["full_range_rejection_reason"] = (
                        _full_endpoint_source_range_rejection(target))
                item["verbatim_original_label_in_modern_K"] = (
                    _original_label_in_modern_k(section_by_first[first], label))
            (omitted if correction is not None else pending).append(item)
    if set(placed)-seen:
        raise ValueError("Linked source occurrence is not in original pinned SWORD")
    if sum(map(len,original.values()))!=len(seen):
        raise ValueError("Original linked element tally inconsistent")
    if len(placed)+len(omitted)+len(pending)!=len(seen):
        raise ValueError("Whole-source hyperlink audit disposition incomplete")
    status_counts={}
    for row in pending+omitted:
        state=row["disposition"]
        status_counts[state]=status_counts.get(state,0)+1
    return {
        "status":"SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
        "original_native_reference_elements":len(seen),
        "source_link_occurrences_verified_in_derived_osis":len(placed),
        "source_spurious_link_occurrences_explicitly_omitted":len(omitted),
        "source_original_links_still_requiring_placement_review":len(pending),
        "pending_and_omitted_by_disposition":status_counts,
        "source_reference_labels_or_literal_targets_exported":False,
        "publication_authorized":False,
        "pending":pending,
        "documented_omitted":omitted,
    }



def validate_pending_source_reference_errata(*, manifest: dict,
                                              ledger: dict,
                                              native: dict) -> dict:
    """Validate reversible proposed source-link errata against native receipts.

    The caller must first authenticate the complete native SWORD source and
    original K/ordinal hyperlink ledger. This function does not inspect prose,
    edit source links, or mark a proposed canonical destination as approved.
    Its return value contains no original source target or printed label.
    """
    if (manifest.get("status") !=
            "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or manifest.get("original_source") != "MHCC 0.1.1 SWORD"
            or manifest.get("original_native_corpus_sha256") !=
            native.get("original_compiled_corpus_sha256")
            or any(manifest.get(flag) is not False for flag in (
                "original_sword_changed", "modern_prose_changed",
                "modern_osis_links_automatically_changed",
                "editorial_target_corrections_approved", "redistributed"))):
        raise ValueError("Untrusted native-link errata proposal or source SHA")
    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("source_reference_labels_or_literal_targets_exported")
                is not False
            or ledger.get("publication_authorized") is not False):
        raise ValueError("Source-link errata need a private original receipt")
    pending = {
        (row["source_first_key"], row["source_reference_ordinal"]): row
        for row in ledger.get("pending", [])
    }
    if len(pending) != len(ledger.get("pending", [])):
        raise ValueError("Duplicate original hyperlink identity in review queue")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Original-link errata review list is empty")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Invalid original-link errata row")
        first, ordinal = case.get("source_first_key"), case.get(
            "original_reference_ordinal")
        key = (first, ordinal)
        if (not isinstance(first, str) or type(ordinal) is not int
                or key in seen or key not in pending
                or case.get("approval") is not False):
            raise ValueError("Source-link proposal is duplicated, unbound or approved")
        seen.add(key)
        original_target = case.get("original_target")
        label_hash = case.get("original_visible_label_sha256")
        actual = pending[key]
        if (not isinstance(original_target, str) or not original_target
                or not isinstance(label_hash, str) or not _SHA.fullmatch(label_hash)
                or hashlib.sha256(original_target.encode("utf-8")).hexdigest()
                    != actual.get("original_osisRef_sha256")
                or case.get("original_target_sha256")
                    != actual.get("original_osisRef_sha256")
                or label_hash != actual.get("original_visible_label_sha256")):
            raise ValueError("Proposed erratum does not match original K/ordinal")
        chapter = first.rsplit(".", 1)[0]
        chapters = native.get("chapters", {})
        groups = chapters.get(chapter, {}).get("original_units", [])
        source = next((row for row in groups
                       if row.get("first_key") == first), None)
        if (source is None or case.get("original_native_unit_sha256")
                != source.get("source_unit_sha256")):
            raise ValueError("Original authorial K prose SHA changed")
        if case.get("finding") == "INVALID_CROSS_CHAPTER_NAVIGATION_IN_ORIGINAL_OSISREF":
            if (_full_endpoint_source_range_rejection(original_target)
                    != "CROSS_CHAPTER_RANGE"
                    or actual.get("full_range_rejection_reason")
                        != "CROSS_CHAPTER_RANGE"
                    or not _source_same_chapter_verse_range(
                        case.get("candidate_fragment"))):
                raise ValueError("Proposed malformed range lacks source-bound evidence")
        elif case.get("finding") == "ORIGINAL_DIGITAL_WITNESS_POINTS_TO_WRONG_VERSE":
            candidate = case.get("proposed_corrected_target")
            if (not _REF.fullmatch(candidate or "")
                    or not canonical_only_for_comparison(original_target)
                    or candidate == canonical_only_for_comparison(original_target)):
                raise ValueError("Proposed wrong-verse correction is not distinct")
        else:
            raise ValueError("Unrecognized original-link editorial finding")
    return {
        "status": "SOURCE_PINNED_PROPOSALS_VERIFIED_NOT_APPLIED_OR_APPROVED",
        "original_link_occurrences_reconciled": len(cases),
        "source_link_edits_applied": 0,
        "modern_prose_edits_applied": 0,
        "original_source_target_or_label_exported": False,
        "publication_authorized": False,
    }



def _source_link_supplement_display(literal: str) -> str:
    """Readable normalized index label, NOT an original printed source label."""
    try:
        canonical = canonical_only_for_comparison(literal)
    except ValueError:
        parsed = _source_same_chapter_verse_range(literal)
        if parsed is None:
            raise ValueError("Private supplement cannot index malformed source link")
        book, chapter, first, last = parsed
        return (_ENGLISH_NAME_BY_OSIS[book] + " " + chapter + ":" +
                first + "–" + last)
    book, chapter, verse = canonical.rsplit(".", 2)
    name = _ENGLISH_NAME_BY_OSIS.get(book)
    if name is None:
        raise ValueError("Private supplement requires canonical book identity")
    return name + " " + chapter + ":" + verse


def build_private_source_reference_supplement(
        *, linked_osis: bytes, ledger: dict, original: dict,
        native: dict, errata: dict) -> tuple[bytes, dict]:
    """Safely PARK unplaced original links in separate, flagged OSIS notes.

    The modern commentary remains untouched and its existing inline
    hyperlinks retain their destinations, labels and ordering. Notes store
    unmodified, source-hashed original target literals, but intentionally
    display *normalized derived index labels*, not original linked words.
    Unverified or visibly wrong links are explicitly excluded by a pinned
    review manifest; they are not silently retargeted. This is a private
    alternate reader candidate, NOT an inline authorial link reconstruction
    or permission to publish.
    """
    from commentary_modern_draft_osis_preview import NS, _range

    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("source_reference_labels_or_literal_targets_exported")
                is not False
            or ledger.get("publication_authorized") is not False
            or errata.get("status") !=
            "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or errata.get("original_native_corpus_sha256") !=
            native.get("original_compiled_corpus_sha256")
            or any(errata.get(k) is not False for k in (
                "original_sword_changed", "modern_prose_changed",
                "modern_osis_links_automatically_changed",
                "editorial_target_corrections_approved", "redistributed"))):
        raise ValueError("Private original-link supplement requires sealed receipts")
    cases=errata.get("cases")
    if not isinstance(cases,list) or not cases:
        raise ValueError("Private source-note preview needs explicit errata blockers")
    blocked={(x.get("source_first_key"),x.get("original_reference_ordinal"))
             for x in cases}
    if len(blocked)!=len(cases) or any(x.get("approval") is not False
                                     for x in cases):
        raise ValueError("Cannot silently approve or duplicate source errata")
    pending=ledger.get("pending")
    if (not isinstance(pending,list)
            or len(pending)!=ledger.get(
                "source_original_links_still_requiring_placement_review")):
        raise ValueError("Private supplement requires complete native pending ledger")
    available={(row["source_first_key"],row["source_reference_ordinal"]):row
               for row in pending}
    if len(available)!=len(pending) or not blocked<=set(available):
        raise ValueError("Unverified pending reference identity or errata exclusion")
    doc=ET.fromstring(linked_osis)
    before="".join(doc.itertext())
    chapters={c.get("osisID"):c for c in doc.iter()
              if c.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters", {})):
        raise ValueError("Modern commentary native-chapter inventory changed")
    expected=[]
    count=0
    for first in sorted({key[0] for key in available}):
        chapter=first.rsplit(".",1)[0]
        units=native["chapters"][chapter]["original_units"]
        positions=[i for i,u in enumerate(units) if u["first_key"]==first]
        if len(positions)!=1 or first not in original:
            raise ValueError("Source first-K section missing in private link notes")
        sections=chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        i=positions[0]
        if (len(sections)!=len(units)
                or sections[i].get("annotateRef") != _range(units[i]["keys"])):
            raise ValueError("Source-owned modern note location changed")
        section=sections[i]
        eligible=[(n,row) for (owner,n),row in sorted(available.items())
                  if owner==first and (owner,n) not in blocked]
        if not eligible:
            continue
        note=ET.SubElement(section,f"{{{NS}}}note",{
            "type":"crossReference",
            "resp":"BibleResourcesPrivateSourceOnlyLinkSupplement",
        })
        note.text="Unplaced links from original edition (not translated citations): "
        hashes=[]
        for j,(ordinal,row) in enumerate(eligible):
            if not 1 <= ordinal <= len(original[first]):
                raise ValueError("Original source link ordinal out of bounds")
            literal,label=original[first][ordinal-1]
            target_sha=hashlib.sha256(literal.encode("utf-8")).hexdigest()
            label_sha=hashlib.sha256(label.encode("utf-8")).hexdigest()
            if (row.get("original_osisRef_sha256")!=target_sha
                    or row.get("original_visible_label_sha256")!=label_sha
                    or not _allowed_source_link_target(literal)):
                raise ValueError("Original note target/label SHA or grammar changed")
            display=_source_link_supplement_display(literal)
            reference=ET.SubElement(note,f"{{{NS}}}reference",{"osisRef":literal})
            reference.text=display
            reference.tail="; " if j<len(eligible)-1 else "."
            hashes.append({
                "source_reference_ordinal":ordinal,
                "source_original_literal_target_sha256":target_sha,
                "supplement_display_sha256":hashlib.sha256(
                    display.encode("utf-8")).hexdigest(),
            })
            count+=1
        expected.append({"source_first_key":first,
                         "original_source_reference_hashes":hashes})
    if (count!=len(pending)-len(blocked)
            or len(expected)!=len({
                r["source_first_key"] for r in pending
                if (r["source_first_key"],r["source_reference_ordinal"])
                   not in blocked})):
        raise ValueError("Incomplete original source-note representation")
    def without_supplement(node: ET.Element) -> str:
        pieces=[]
        if node.text:
            pieces.append(node.text)
        for child in node:
            if (child.tag!=f"{{{NS}}}note" or child.get("resp") !=
                    "BibleResourcesPrivateSourceOnlyLinkSupplement"):
                pieces.append(without_supplement(child))
            if child.tail:
                pieces.append(child.tail)
        return "".join(pieces)
    if without_supplement(doc)!=before:
        raise ValueError("Modern commentary visible prose changed in source note preview")
    serialized=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(serialized)
    return serialized, {
        "status":"PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY",
        "original_native_corpus_sha256":
            native["original_compiled_corpus_sha256"],
        "modern_source_text_and_existing_links_unchanged":True,
        "original_link_occurrences_preserved_only_in_separate_source_notes":count,
        "source_first_K_sections_with_note":len(expected),
        "malformed_or_wrong_original_links_excluded_for_review":len(blocked),
        "source_link_supplement_not_authorial_or_inline":True,
        "published_or_distributed":False,
        "editorial_relocation_approved":False,
        "note_source_K_reference_hashes_for_private_native_readback":expected,
    }




# Private, conservative recovery of link context. These are not authorial
# inline labels and never rewrite a translated sentence.
_CONTEXT_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_CONTEXT_COMMON = frozenset((
    "about after again also among because before being between could every "
    "first from given great have having into itself more must neither other "
    "shall should since some such than that their them there these those "
    "through thus under until upon very were when where which while whose "
    "with would your they this what then been himself herself themselves "
    "therefore indeed only make made many might much once over even every "
    "people things words said says says one two three that those whose"
).split())


def _original_source_link_contexts(raw: bytes) -> list[tuple[str, str]]:
    """In-memory prose immediately before/after each original reference.

    The caller authenticates the entire native K raw SHA and original link
    ordinals before using these contexts; no original prose is exported.
    """
    source = ET.fromstring(b"<source>" + raw + b"</source>")
    fragments: list[str] = []
    positions: list[tuple[int, int]] = []
    current = 0

    def emit(value: str | None) -> None:
        nonlocal current
        if value:
            fragments.append(value)
            current += len(value)

    def walk(node: ET.Element) -> None:
        emit(node.text)
        for child in node:
            if isinstance(child.tag, str) and child.tag.rsplit("}", 1)[-1] == "reference":
                positions.append((current, len("".join(child.itertext()))))
            walk(child)
            emit(child.tail)

    walk(source)
    prose = "".join(fragments)
    return [(prose[max(0, start-180):start],
             prose[start+label_length:start+label_length+180])
            for start, label_length in positions]


def _source_context_unique_paragraph_anchor(
        section: ET.Element, context: tuple[str, str]):
    """Find a uniquely preserved, non-generic ORIGINAL nearby phrase.

    This finds proximity, not the original position of the linked label.
    Therefore the link can only become a visibly tagged source-only note,
    never a falsely attributed hyperlink wrapping Henry's modernized words.
    """
    from commentary_modern_draft_osis_preview import NS
    candidates = []
    for side, part in enumerate(context):
        words = [m.group().casefold() for m in _CONTEXT_WORD.finditer(part)]
        # In the following source context allow up to two leading tokens of
        # punctuation/citation residue; stay close to the original reference.
        for offset in (0, 1, 2):
            for length in (8, 7, 6, 5):
                subset = (words[-offset-length:len(words)-offset or None]
                          if side == 0 else words[offset:offset+length])
                if len(subset) != length:
                    continue
                meaningful = {w for w in subset
                              if len(w) >= 5 and w not in _CONTEXT_COMMON}
                if len(meaningful) < 3:
                    continue
                candidates.append((length, -offset, -side, tuple(subset)))

    if not candidates:
        return None
    placements = []
    for para in section.findall(f"{{{NS}}}p"):
        value = para.text or ""
        tokens = [(m.group().casefold(), m.start(), m.end())
                  for m in _CONTEXT_WORD.finditer(value)]
        for length, proximity, side_priority, phrase in candidates:
            for i in range(len(tokens)-length+1):
                if tuple(t[0] for t in tokens[i:i+length]) == phrase:
                    placements.append((length, proximity, side_priority, id(para),
                                       tokens[i+length-1][2], para))
    if not placements:
        # Exact multiword prose almost never survives a substantive
        # modernization verbatim. A second, explicitly weaker *paragraph*
        # candidate requires many distinctive lexical anchors from one
        # side of the original reference. It NEVER claims the original
        # linked word or exact inline location. Its note belongs only at
        # the end of a uniquely supported modern paragraph.
        def root(word: str) -> str:
            word = word.casefold()
            if len(word) >= 8 and word.endswith("ing"):
                return word[:-3]
            if len(word) >= 7 and word.endswith("ed"):
                return word[:-2]
            if len(word) >= 6 and word.endswith("s") and not word.endswith("ss"):
                return word[:-1]
            return word

        def significant(words: str) -> set[str]:
            common = _CONTEXT_COMMON | {
                "god", "lord", "christ", "jesus", "believe", "believer",
                "faith", "chapter", "verse", "verses", "scripture",
                "heaven", "earth", "children", "father", "spirit",
                "which", "their", "those", "these", "given", "shall"}
            return {root(m.group()) for m in _CONTEXT_WORD.finditer(words)
                    if len(m.group()) >= 5 and m.group().casefold() not in common}

        proposals=[]
        for side, original_window in enumerate(context):
            source_terms=significant(original_window)
            if not 7 <= len(source_terms) <= 45:
                continue
            for para in section.findall(f"{{{NS}}}p"):
                modern_terms=significant("".join(para.itertext()))
                shared=len(source_terms & modern_terms)
                overlap=shared/len(source_terms)
                if shared >= 6 and overlap >= 0.64:
                    proposals.append((shared,overlap,side,para))
        if not proposals:
            return None
        proposals.sort(key=lambda row:(row[0],row[1]),reverse=True)
        best_score,coverage,_,chosen=proposals[0]
        # Multiple qualifying paragraphs or source-side windows naming
        # different paragraphs are not a verified contextual placement.
        if any(row[3] is not chosen for row in proposals[1:]):
            return None
        return chosen,-1  # Paragraph-end SOURCE-ONLY note, never inline parity.
    # A unique largest exact preserved phrase. Different positions with the
    # same maximal strength are ambiguous and MUST remain at section level.
    highest = max(row[:3] for row in placements)
    best = {(row[3], row[4]): row for row in placements if row[:3] == highest}
    if len(best) != 1:
        return None
    selected = next(iter(best.values()))
    return selected[-1], selected[-2]  # (paragraph node, character offset)



def _source_owned_ordered_alignment(raw: bytes, section: ET.Element) -> dict:
    """Align ORIGINAL authenticated full-K word order with modern K paragraphs.

    No source prose is exported, no target is guessed, and no citation is
    automatically embedded in translated wording. Only unique, ordered,
    distinctive anchors on both sides of a source hyperlink can establish
    a tentative position for a visibly tagged provenance note.
    """
    from difflib import SequenceMatcher
    from bisect import bisect_right
    from commentary_modern_draft_osis_preview import NS

    root = ET.fromstring(b"<source>" + raw + b"</source>")
    raw_parts = []
    original_positions = []
    length = 0

    def append(value):
        nonlocal length
        if value:
            raw_parts.append(value)
            length += len(value)

    def walk(node):
        append(node.text)
        for child in node:
            if isinstance(child.tag, str) and child.tag.rsplit("}",1)[-1] == "reference":
                original_positions.append(length)
            walk(child)
            append(child.tail)

    walk(root)
    text = "".join(raw_parts)
    if not original_positions:
        return {"original_link_offsets":[],"suggestions":{}}

    def stem(word):
        word = word.casefold()
        if len(word) >= 8 and word.endswith("ing"):
            return word[:-3]
        if len(word) >= 7 and word.endswith("ed"):
            return word[:-2]
        if len(word) >= 6 and word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def tokens(value):
        return [(stem(m.group()),m.start(),m.end())
                for m in _CONTEXT_WORD.finditer(value)]

    old = tokens(text)
    paras = section.findall(f"{{{NS}}}p")
    modern = []
    # Source notes, if present, cannot be used as authored modern anchors.
    for para in paras:
        for w,a,b in tokens(para.text or ""):
            modern.append((w,para,a,b))
    if not old or not modern:
        return {"original_link_offsets":original_positions,"suggestions":{}}
    blocks = SequenceMatcher(None,[t[0] for t in old],
                             [t[0] for t in modern],
                             autojunk=False).get_matching_blocks()
    common = _CONTEXT_COMMON | {
        "god","lord","christ","jesus","spirit","faith","grace","children",
        "therefore","indeed","people","believe","believer","heaven","earth"
    }
    strong=[]
    for b in blocks:
        if b.size < 3:
            continue
        meaningful={old[n][0] for n in range(b.a,b.a+b.size)
                    if len(old[n][0])>=5 and old[n][0] not in common}
        if len(meaningful)<2:
            continue
        strong.append(b)

    suggestions={}
    for ordinal,position in enumerate(original_positions,1):
        src_token=bisect_right([x[1] for x in old], position)
        before=[b for b in strong if b.a+b.size<=src_token
                and src_token-(b.a+b.size)<=75]
        after=[b for b in strong if b.a>=src_token
               and b.a-src_token<=75]
        if not before or not after:
            continue
        left=max(before,key=lambda b:b.a+b.size)
        right=min(after,key=lambda b:b.a)
        if left.b+left.size>right.b or right.b-(left.b+left.size)>85:
            continue
        leftEnd=modern[left.b+left.size-1]
        rightStart=modern[right.b]
        if leftEnd[1] is not rightStart[1]:
            continue
        para=leftEnd[1]
        prose=para.text or ""
        start,end=leftEnd[3],rightStart[2]
        if start>=end or end>len(prose):
            continue
        # A citation may occupy the gap between the two source-verified
        # anchors; prefer an actual modern sentence boundary in that gap.
        punctuation=[m.end() for m in re.finditer(r"[.!?](?=\s|$)",prose[start:end])]
        if not punctuation:
            continue
        if len(punctuation)!=1:
            continue
        mark=start+punctuation[0]
        if not (start<mark<=end):
            continue
        suggestions[ordinal]=(para,mark)
    return {"original_link_offsets":original_positions,
            "suggestions":suggestions}



def build_private_contextual_source_note_preview(
        *, source_note_osis: bytes, ledger: dict, native: dict,
        original_contexts: dict, errata: dict,
        original_ordered_anchors: dict | None = None) -> tuple[bytes, dict]:
    """Relocate only proven same-K source notes adjacent to exact prose context.

    An unchanged *separate* source-note SWORD candidate remains authoritative
    for whatever source links remain unplaced in this edition. The separate candidate is NOT approved or
    publishable; it does not invent original inline link locations.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS, _range

    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("source_reference_labels_or_literal_targets_exported") is not False
            or ledger.get("publication_authorized") is not False
            or native.get("source_prose_or_original_markup_exported") is not False):
        raise ValueError("Context location requires an authenticated native ledger")
    doc = ET.fromstring(source_note_osis)
    chapters = {x.get("osisID"):x for x in doc.iter()
                if x.tag == f"{{{NS}}}chapter"}
    pending = ledger["pending"]
    original_errata = errata.get("cases")
    if (errata.get("status") != "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or errata.get("original_native_corpus_sha256") !=
               native.get("original_compiled_corpus_sha256")
            or not isinstance(original_errata,list) or len(original_errata)!=4
            or any(c.get("approval") is not False for c in original_errata)):
        raise ValueError("Unapproved defective original source references were not pinned")
    blocked_keys = {(c["source_first_key"], c["original_reference_ordinal"])
                    for c in original_errata}
    if len(blocked_keys)!=4:
        raise ValueError("Four source errors must remain distinct")
    if len(pending) != ledger["source_original_links_still_requiring_placement_review"]:
        raise ValueError("Original source pending ledger was truncated")

    def authored_text_without_source_notes(root: ET.Element) -> str:
        parts = []
        def walk(node):
            if node.text:
                parts.append(node.text)
            for child in node:
                if (child.tag != f"{{{NS}}}note"
                        or child.get("resp") not in (
                            "BibleResourcesPrivateSourceOnlyLinkSupplement",
                            "BibleResourcesPrivateContextSourceLink")):
                    walk(child)
                if child.tail:
                    parts.append(child.tail)
        walk(root)
        return "".join(parts)

    def source_note_links(root):
        return Counter((ref.get("osisRef"), ref.text or "")
            for note in root.iter() if note.tag == f"{{{NS}}}note"
            and note.get("resp") in (
                "BibleResourcesPrivateSourceOnlyLinkSupplement",
                "BibleResourcesPrivateContextSourceLink")
            for ref in note if ref.tag == f"{{{NS}}}reference")

    original_authored = authored_text_without_source_notes(doc)
    before_links = source_note_links(doc)
    notes_by_first = {}
    for chapter, node in chapters.items():
        units = native["chapters"][chapter]["original_units"]
        if not units:
            # Leviticus 19 and Psalm 108 have only whole-chapter I source
            # material, never a numbered original K reference group.
            continue
        sections = node.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(units):
            raise ValueError("Modern chapter/source group count drift")
        for source, section in zip(units, sections):
            if section.get("annotateRef") != _range(source["keys"]):
                raise ValueError("Original commentary K scope drift")
            group_notes = [x for x in section
                           if x.tag == f"{{{NS}}}note" and x.get("resp") ==
                           "BibleResourcesPrivateSourceOnlyLinkSupplement"]
            if group_notes:
                if len(group_notes) != 1:
                    raise ValueError("Duplicate section-level original source note")
                notes_by_first[source["first_key"]] = (section, group_notes[0])

    candidates = {}
    blocked = set(blocked_keys)
    for row in pending:
        first, ordinal = row["source_first_key"], row["source_reference_ordinal"]
        if first not in notes_by_first:
            blocked.add((first, ordinal))
            continue
        contexts = original_contexts.get(first)
        if contexts is None or not 1 <= ordinal <= len(contexts):
            raise ValueError("Source context unavailable for authenticated original K")
        section, note = notes_by_first[first]
        found = _source_context_unique_paragraph_anchor(section, contexts[ordinal-1])
        if found is not None:
            candidates[(first, ordinal)] = (*found,
                ("UNIQUE_EXACT_SOURCE_NEAR_PHRASE" if found[1]>=0 else
                 "CONSERVATIVE_UNIQUE_PARAGRAPH_LEXICAL_MATCH"))
        elif original_ordered_anchors is not None:
            aligned = original_ordered_anchors.get(first,{}).get("suggestions",{}).get(ordinal)
            if aligned is not None:
                candidates[(first, ordinal)] = (*aligned,
                    "TWO_SIDED_ORDERED_SOURCE_K_ALIGNMENT")

    # A shared anchor is not proof that two original citations belong there.
    repeats = Counter((id(p), end) for p, end, _ in candidates.values())
    for key, (p, end, basis) in list(candidates.items()):
        if repeats[(id(p),end)] > 1:
            candidates.pop(key)

    moved = []
    para_inserts = []
    for first, (section, group_note) in notes_by_first.items():
        eligible = [row for row in pending if row["source_first_key"] == first
                    and (first, row["source_reference_ordinal"]) not in blocked]
        source_refs = [x for x in group_note
                       if x.tag == f"{{{NS}}}reference"]
        if len(source_refs) != len(eligible):
            raise ValueError("Original source note order/count changed")
        group_note[:] = []
        remaining = []
        for ref, row in zip(source_refs, eligible):
            literal = ref.get("osisRef")
            if (not isinstance(literal, str) or
                    hashlib.sha256(literal.encode("utf-8")).hexdigest() !=
                        row["original_osisRef_sha256"] or
                    ref.text != _source_link_supplement_display(literal)):
                raise ValueError("A candidate changed the authenticated source target")
            ordinal = row["source_reference_ordinal"]
            key = (first, ordinal)
            if key not in candidates:
                remaining.append(ref)
                continue
            p, end, basis = candidates[key]
            local = ET.Element(f"{{{NS}}}note",{
                "type":"crossReference",
                "resp":"BibleResourcesPrivateContextSourceLink"})
            local.text = ("Original-edition reference (nearby context matches; "
                          "original link placement not certified): ")
            ref.tail = "."
            local.append(ref)
            para_inserts.append((p, end, local))
            moved.append({
                "source_first_key":first,
                "source_reference_ordinal":ordinal,
                "placement_basis":basis,
                "source_literal_target_sha256":row["original_osisRef_sha256"],
                "original_label_sha256":row["original_visible_label_sha256"]})
        if remaining:
            group_note.text = ("Unplaced links from original edition "
                               "(not translated citations): ")
            for i, r in enumerate(remaining):
                r.tail = "; " if i < len(remaining)-1 else "."
                group_note.append(r)
        else:
            section.remove(group_note)

    # Descending offsets maintain original paragraph ordering when more than
    # one different, verified context lands in the same modern paragraph.
    for para, end, note in sorted(para_inserts, key=lambda x:(id(x[0]), -x[1])):
        if end == -1:
            para.append(note)  # Explicitly non-authorial paragraph-local note.
            continue
        text = para.text or ""
        if not (0 < end <= len(text)):
            raise ValueError("A previous insertion moved a context anchor")
        para.text = text[:end]
        note.tail = text[end:]
        para.insert(0, note)

    if authored_text_without_source_notes(doc) != original_authored:
        raise ValueError("Contextual notes changed translated commentary words")
    total_source_notes=len(pending)-len(blocked_keys)
    if (source_note_links(doc)!=before_links or
            sum(before_links.values())!=total_source_notes):
        raise ValueError("Contextual notes lost/duplicated original source links")
    output=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(output)
    return output, {
        "status":"PRIVATE_EXACT_CONTEXT_PROXIMITY_REVIEW_NOT_AUTHORIAL_INLINE_PARITY",
        "source_note_occurrences_total":total_source_notes,
        "source_notes_moved_to_authored_paragraphs":len(moved),
        "source_notes_still_grouped_by_K":total_source_notes-len(moved),
        "exact_phrase_proximity_count":sum(x["placement_basis"] ==
            "UNIQUE_EXACT_SOURCE_NEAR_PHRASE" for x in moved),
        "paragraph_lexical_context_proximity_count":sum(x["placement_basis"] ==
            "CONSERVATIVE_UNIQUE_PARAGRAPH_LEXICAL_MATCH" for x in moved),
        "ordered_source_alignment_count":sum(x["placement_basis"] ==
            "TWO_SIDED_ORDERED_SOURCE_K_ALIGNMENT" for x in moved),
        "whole_original_K_ownership_retained":True,
        "source_prose_or_modern_authored_text_modified":False,
        "original_source_target_and_label_identities_preserved":True,
        "context_match_is_not_original_inline_placement_approval":True,
        "published_or_distributed":False,
        "context_relocations":moved,
    }





def build_private_compact_original_crossrefs(
        *, linked_osis: bytes, ledger: dict, original: dict,
        native: dict, errata: dict) -> tuple[bytes,dict,dict]:
    """Recover exact source-linked *verse tokens* inside compressed citations.

    e.g. the authored "(1 John 4:8, 16)" supplies distinct printed '8'
    and '16' anchors for authenticated original 1John.4.8/.16 links.
    This is NOT fuzzy semantic interpolation: only an unambiguous, explicit
    book+chapter+verse token within the very same source-owned modern K is
    eligible. No modern prose or original source wording changes.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS, _range

    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("source_reference_labels_or_literal_targets_exported") is not False
            or ledger.get("publication_authorized") is not False
            or native.get("source_prose_or_original_markup_exported") is not False
            or errata.get("original_native_corpus_sha256") !=
                native.get("original_compiled_corpus_sha256")
            or errata.get("status") !=
                "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"):
        raise ValueError("Compact citation recovery lacks original SHA evidence")
    blocked={(c["source_first_key"],c["original_reference_ordinal"])
             for c in errata["cases"]}
    if len(blocked)!=4 or any(c.get("approval") is not False
                             for c in errata["cases"]):
        raise ValueError("Four bad original target identities remain blocked")
    doc=ET.fromstring(linked_osis)
    authored_before="".join(doc.itertext())
    chapters={n.get("osisID"):n for n in doc.iter()
              if n.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Original canonical chapter inventory changed")

    k_sections={}
    for chapter, node in chapters.items():
        units=native["chapters"][chapter]["original_units"]
        sections=node.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if not units:
            continue
        if len(units)!=len(sections):
            raise ValueError("Original K groups changed before compact link repair")
        for src,sec in zip(units,sections):
            if sec.get("annotateRef")!=_range(src["keys"]):
                raise ValueError("Original modern K section scope changed")
            k_sections[src["first_key"]]=sec

    # A slot is one actual XML text/tail field, not normalized XML itertext.
    # In particular, previously linked labels are not eligible a second time.
    def slots(section):
        for node in section.iter():
            if node.tag==f"{{{NS}}}reference":
                if node.tail:
                    yield node,"tail",node.tail
                continue
            # Source link recovery must never refer to existing notes.
            if node.tag==f"{{{NS}}}note":
                continue
            if node.text:
                yield node,"text",node.text
            if node.tail:
                yield node,"tail",node.tail

    def projected_slots(paragraph):
        """Read one authored paragraph, retaining exact XML text-slot offsets.

        Existing hyperlinks supply *context* but their own verse digits are
        never eligible for a second, nested link.
        """
        chunks=[]
        parts=[]
        cursor=0

        def emit(node, attr, linked):
            nonlocal cursor
            val=getattr(node,attr)
            if isinstance(val,str) and val:
                chunks.append((cursor,cursor+len(val),node,attr,linked,val))
                parts.append(val)
                cursor+=len(val)
        def walk(node, inside_link=False):
            own_link=(node.tag==f"{{{NS}}}reference")
            emit(node,"text",inside_link or own_link)
            for child in node:
                walk(child,inside_link or own_link)
                emit(child,"tail",inside_link)
        walk(paragraph)
        return "".join(parts),chunks

    def inherited_book_verse_candidates(section,*,book,chapter,verse,names):
        # Chapters 1-verse texts of genuinely single-chapter canonical books
        # may be authored as "Jude 15", not "Jude 1:15".
        single_chapter={"Obad","Phlm","2John","3John","Jude"}
        aliases="|".join(re.escape(x) for x in sorted(names,key=len,reverse=True))
        # A semicolon separates *chapters* in abbreviated multichapter
        # citations; it MUST NOT be greedily mistaken for a verse comma.
        # Allow an isolated chapter with a visible 13–14 span as well.
        full=re.compile(
            r"(?<![A-Za-z0-9])(?:"+aliases+r")\s+"
            r"\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*"
            r"(?:\s*;\s*\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*)*",
            flags=re.IGNORECASE)
        solitary=(re.compile(r"(?<![A-Za-z0-9])(?:"+aliases+
                             r")\s+("+re.escape(verse)+r")(?![\d:])",
                             flags=re.IGNORECASE)
                  if book in single_chapter and chapter=="1" else None)
        out=[]
        for paragraph in section.findall(f"{{{NS}}}p"):
            projected,chunks=projected_slots(paragraph)
            for hit in full.finditer(projected):
                excerpt=hit.group()
                # Chapter numbers and verse numbers have distinct scope:
                # Psalms 114:3; 106:9; 136:13 and Job 31:13–14 both
                # retain an exact written chapter and an explicit target
                # verse digit. We link ONLY that printed digit, never an
                # unprinted intervening verse in a numerical range.
                for candidate in re.finditer(
                        r"(?<!\d)(\d+)\s*:\s*(\d+)"
                        r"((?:\s*[,\u2013\u2014-]\s*\d+)*)",excerpt):
                    if candidate[1]!=chapter:
                        continue
                    numbers=[(candidate[2],candidate.start(2),
                              candidate.end(2))]
                    trailer=candidate[3]
                    numbers.extend((m.group(),candidate.start(3)+m.start(),
                                    candidate.start(3)+m.end())
                                   for m in re.finditer(r"\d+",trailer))
                    for printed,a0,b0 in numbers:
                        if printed!=verse:
                            continue
                        start,end=hit.start()+a0,hit.start()+b0
                        out.extend((node,attr,value,start-a,end-a)
                            for a,b,node,attr,linked,value in chunks
                            if not linked and a<=start and end<=b)
            if solitary is not None:
                for hit in solitary.finditer(projected):
                    start,end=hit.start(1),hit.end(1)
                    out.extend((node,attr,value,start-a,end-a)
                               for a,b,node,attr,linked,value in chunks
                               if not linked and a<=start and end<=b)
        return out

    chosen={}
    grouped={}
    unmatched=[]
    for row in ledger["pending"]:
        first,ordinal=row["source_first_key"],row["source_reference_ordinal"]
        key=(first,ordinal)
        if key in blocked:
            continue
        if first not in original or not 1<=ordinal<=len(original[first]):
            raise ValueError("Pending source ref lacks original K/ordinal evidence")
        literal,label=original[first][ordinal-1]
        if (hashlib.sha256(literal.encode()).hexdigest()!=row["original_osisRef_sha256"]
                or hashlib.sha256(label.encode()).hexdigest()!=
                    row["original_visible_label_sha256"]):
            raise ValueError("Original exact source link receipt changed")
        try:
            book,chapter,verse=canonical_only_for_comparison(literal).rsplit(".",2)
        except ValueError:
            unmatched.append(key)
            continue
        names=set(_AUTO_ALIASES.get(book,()))
        names.add(_ENGLISH_NAME_BY_OSIS[book])
        # Canonical full English names and standard recognized abbreviations.
        aliases="|".join(re.escape(x) for x in sorted(names,key=len,reverse=True))
        expression=re.compile(
            r"(?<![A-Za-z0-9])(?:"+aliases+r")\s+"+re.escape(chapter)+
            r"\s*:\s*\d+(?:\s*[,;–-]\s*\d+)*",
            flags=re.IGNORECASE)
        candidates=[]
        for node,attr,value in slots(k_sections[first]):
            for match in expression.finditer(value):
                rel=match.group()
                colon=rel.find(":")
                if colon<0:
                    raise ValueError("Invalid normalized Scripture chapter:verse citation")
                rest=rel[colon+1:]
                nums=[m for m in re.finditer(r"\d+",rest)]
                if len(nums)!=len({int(m.group()) for m in nums}):
                    continue  # repeated verse tokens are not distinctive.
                for number in nums:
                    if number.group()!=verse:  # require exact canonical numeric spelling
                        continue
                    a=match.start()+colon+1+number.start()
                    b=match.start()+colon+1+number.end()
                    candidates.append((node,attr,value,a,b))
        match_type="EXPLICIT_FULL_BOOK_CHAPTER_WITH_VERSE_TOKENS"
        if not candidates:
            candidates=inherited_book_verse_candidates(
                k_sections[first],book=book,chapter=chapter,verse=verse,
                names=names)
            match_type="EXPLICIT_INHERITED_BOOK_OR_SINGLE_CHAPTER_REFERENCE"
        if len(candidates)!=1:
            unmatched.append(key)
            continue
        node,attr,value,start,end=candidates[0]
        slotid=(id(node),attr)
        chosen[key]={"source_first_key":first,"source_reference_ordinal":ordinal,
                     "original_literal_target_sha256":row["original_osisRef_sha256"],
                     "original_visible_label_sha256":row["original_visible_label_sha256"],
                     "linked_visible_token_sha256":hashlib.sha256(
                         value[start:end].encode()).hexdigest(),
                     "source_target":literal,"slotid":slotid,"match_type":match_type,
                     "node":node,"attr":attr,"value":value,"start":start,"end":end}
        grouped.setdefault(slotid,[]).append(key)

    # No distinct original links may claim the same character interval.
    collisions=set()
    for keys in grouped.values():
        offsets=Counter((chosen[k]["start"],chosen[k]["end"]) for k in keys)
        collisions.update(k for k in keys if offsets[
            (chosen[k]["start"],chosen[k]["end"])]!=1)
    for key in collisions:
        old=chosen.pop(key)
        unmatched.append(key)
        grouped[old["slotid"]].remove(key)
    if len(set(unmatched))+len(chosen)+len(blocked)!=len(ledger["pending"]):
        raise ValueError("Incomplete original source K/ordinal compact citation disposition")

    # Reconstruct each original literal XML text slot only once, retaining
    # its exact visible text, sibling order, punctuation, whitespace and
    # full original target spelling. Previously linked text is untouched.
    for slotid,keys in grouped.items():
        if not keys:
            continue
        entries=sorted([chosen[k] for k in keys],key=lambda v:v["start"])
        node,attr,value=entries[0]["node"],entries[0]["attr"],entries[0]["value"]
        if any(e["value"]!=value or e["node"] is not node or
               e["attr"]!=attr for e in entries):
            raise ValueError("Compact source citation slot disagreement")
        prev=0
        built=[]
        for entry in entries:
            if entry["start"]<prev:
                raise ValueError("Overlapping source-literal citation spans")
            link=ET.Element(f"{{{NS}}}reference",{"osisRef":entry["source_target"]})
            link.text=value[entry["start"]:entry["end"]]
            built.append((value[prev:entry["start"]],link))
            prev=entry["end"]
        trailing=value[prev:]
        if attr=="text":
            node.text=built[0][0]
            for i,(prefix,ref) in enumerate(built):
                ref.tail=(built[i+1][0] if i+1<len(built) else trailing)
                node.insert(i,ref)
        else:
            parent=next((p for p in k_sections[entries[0]["source_first_key"]].iter()
                         if node in list(p)),None)
            if parent is None:
                raise ValueError("Original compact tail reference lost parent")
            node.tail=built[0][0]
            index=list(parent).index(node)+1
            for i,(prefix,ref) in enumerate(built):
                ref.tail=(built[i+1][0] if i+1<len(built) else trailing)
                parent.insert(index+i,ref)
    if "".join(doc.itertext())!=authored_before:
        raise ValueError("Compact source links changed modern commentary visible prose")

    moved=[{
        "source_first_key":x["source_first_key"],
        "source_reference_ordinal":x["source_reference_ordinal"],
        "original_literal_target_sha256":x["original_literal_target_sha256"],
        "original_visible_label_sha256":x["original_visible_label_sha256"],
        "linked_visible_token_sha256":x["linked_visible_token_sha256"],
        "placement_basis":x["match_type"],
    } for _,x in sorted(chosen.items())]
    remainder=[x for x in ledger["pending"]
               if (x["source_first_key"],x["source_reference_ordinal"]) not in chosen]
    revised={**ledger,
        "source_link_occurrences_verified_in_derived_osis":
            ledger["source_link_occurrences_verified_in_derived_osis"]+len(moved),
        "source_original_links_still_requiring_placement_review":len(remainder),
        "pending":remainder,
        "publication_authorized":False}
    if (revised["source_link_occurrences_verified_in_derived_osis"]+
        ledger["source_spurious_link_occurrences_explicitly_omitted"]+
        len(remainder)!=ledger["original_native_reference_elements"]):
        raise ValueError("All original hyperlink identities must still be accounted for")
    result=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(result)
    return result,revised,{
        "status":"PRIVATE_EXACT_BOOK_CHAPTER_VERSE_COMPACT_SOURCE_LINK_RECONSTRUCTION",
        "original_native_corpus_sha256":native["original_compiled_corpus_sha256"],
        "original_unplaced_valid_links_considered":
            len(ledger["pending"])-len(blocked),
        "original_exact_compact_verse_links_restored":len(moved),
        "original_valid_link_positions_still_unplaced":len(remainder)-len(blocked),
        "original_defective_link_proposals_never_retargeted":len(blocked),
        "all_original_k_text_in_derived_osis_unchanged":True,
        "original_crossreference_literal_targets_and_labels_sha_verified":True,
        "source_only_note_fallback_available":True,
        "released_or_distributed":False,
        "placements":moved,
    }




def build_private_owned_K_heading_range_links(
        *, compact_osis: bytes, ledger: dict, original: dict, native: dict,
        errata: dict) -> tuple[bytes, dict, dict]:
    """Attach authenticated original SAME-CHAPTER complete K ranges to their heading.

    An original link may end the PRECEDING K body as a section navigation
    hint; only the single source-owned NEXT (or current/future) K section
    whose original native verse occupancy exactly equals the range may
    receive it. The displayed modern heading must explicitly name those
    same verse endpoints. This is a provenance-marked EDITORIAL heading
    relocation, not a claim about Henry's original inline words.
    """
    from commentary_modern_draft_osis_preview import NS, _range
    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("publication_authorized") is not False
            or ledger.get("source_reference_labels_or_literal_targets_exported") is not False
            or native.get("source_prose_or_original_markup_exported") is not False
            or errata.get("status") !=
                "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or errata.get("original_native_corpus_sha256") !=
                native.get("original_compiled_corpus_sha256")):
        raise ValueError("Authentic source K and errata receipts required for range headings")
    blocked={(case["source_first_key"],case["original_reference_ordinal"])
             for case in errata["cases"]}
    if len(blocked)!=4 or any(case["approval"] is not False for case in errata["cases"]):
        raise ValueError("Unapproved original target errors must remain blocked")
    doc=ET.fromstring(compact_osis)
    original_prose="".join(doc.itertext())
    chapters={x.get("osisID"):x for x in doc.iter() if x.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Source/modern chapter coverage mismatch for heading link repair")
    original_groups={}
    for chapter,ch in chapters.items():
        units=native["chapters"][chapter]["original_units"]
        sections=ch.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if not units:
            continue
        if len(units)!=len(sections):
            raise ValueError("Original K and modern section count differs")
        original_groups[chapter]=(units,sections)
        for unit,section in zip(units,sections):
            if section.get("annotateRef") != _range(unit["keys"]):
                raise ValueError("Original K verse occupancy drift")

    # Multiple source links must not be silently attached to the same
    # derived verse-heading text. Restore neither if ambiguous.
    candidates={}
    for row in ledger["pending"]:
        first,ordinal=row["source_first_key"],row["source_reference_ordinal"]
        key=(first,ordinal)
        if key in blocked:
            continue
        if first not in original or not 1<=ordinal<=len(original[first]):
            raise ValueError("Missing original link K/ordinal")
        literal,label=original[first][ordinal-1]
        if (hashlib.sha256(literal.encode()).hexdigest()!=row["original_osisRef_sha256"]
                or hashlib.sha256(label.encode()).hexdigest()!=
                row["original_visible_label_sha256"]):
            raise ValueError("Unpinned original link target/printed label")
        parsed=_source_same_chapter_verse_range(literal)
        if parsed is None:
            continue
        book,chapter,start,end=parsed
        source_chapter=first.rsplit(".",1)[0]
        if source_chapter!=book+"."+chapter or source_chapter not in original_groups:
            continue
        if re.search(
                r"(?<![0-9])"+re.escape(chapter)+r"\s*:\s*"+
                re.escape(start)+r"\s*[-–—]\s*"+re.escape(end)+r"(?!\d)",
                label) is None:
            continue
        units,sections=original_groups[source_chapter]
        source_index=next((i for i,u in enumerate(units)
                           if u["first_key"]==first),None)
        raw_target=literal[6:] if literal.startswith("Bible:") else literal
        owning=[i for i,u in enumerate(units)
                if _range(u["keys"])==raw_target]
        if source_index is None:
            continue
        label_pattern=re.compile(
            r"\bverses?\s+"+re.escape(start)+r"\s*[-–—]\s*"+
            re.escape(end)+r"\b", re.I)
        matches=[]
        placement_basis=None
        target_index=source_index
        if len(owning)==1 and owning[0]>=source_index:
            target_index=owning[0]
            # Exact source K occupancy is the only safe heading transport.
            for title in sections[target_index].findall(
                    f"./{{{NS}}}title[@type='sub']"):
                if len(title)!=0 or not isinstance(title.text,str):
                    continue
                for m in label_pattern.finditer(title.text):
                    matches.append((title,m.start(),m.end()))
            if len(matches)==1:
                placement_basis="EXACT_ORIGINAL_K_SECTION_HEADING"
        if not matches:
            # A complete original cross-reference may span SOME verses inside
            # one source-owned K, rather than the K's complete heading.
            # A genuinely single first-verse-indexed original K (Isa 12/15)
            # is eligible only with the original same-chapter link and a
            # unique, explicitly printed modern verse range.
            own=units[source_index]
            own_keys=set(own["keys"])
            source_cover=all(f"{book}.{chapter}.{v}" in own_keys
                             for v in range(int(start),int(end)+1))
            underindexed_single_K=(len(units)==1 and
                own["first_key"]==f"{book}.{chapter}.1")
            if source_cover or underindexed_single_K:
                target_index=source_index
                matches=[]
                # Authored Markdown emphasis creates distinct XML <hi> nodes.
                # Search the full rendered paragraph for the EXACT explicit
                # original chapter's verse span, then wrap only the visible
                # numeric token inside ONE physical XML text slot. No
                # flattening, deletion, duplicated text or ref nesting.
                number_pattern=re.compile(
                    re.escape(start)+r"\s*[-–—]\s*"+re.escape(end))
                for p in sections[source_index].findall(f"./{{{NS}}}p"):
                    slots=[]
                    fragments=[]
                    offset=0
                    def emit(node,attr,blocked=False):
                        nonlocal offset
                        value=getattr(node,attr)
                        if isinstance(value,str) and value:
                            slots.append((offset,offset+len(value),
                                          node,attr,blocked,value))
                            fragments.append(value)
                            offset+=len(value)
                    def walk(node,in_link=False):
                        if node.tag==f"{{{NS}}}note":
                            return
                        current_link=in_link or node.tag==f"{{{NS}}}reference"
                        emit(node,"text",current_link)
                        for child in node:
                            walk(child,current_link)
                            emit(child,"tail",current_link)
                    walk(p)
                    rendered="".join(fragments)
                    for hit in label_pattern.finditer(rendered):
                        numeric=number_pattern.search(hit.group())
                        if numeric is None:
                            continue
                        a=hit.start()+numeric.start()
                        b=hit.start()+numeric.end()
                        matches.extend((node,a-first_pos,b-first_pos)
                          for first_pos,last_pos,node,attr,blocked,value in slots
                          if not blocked and attr=="text"
                          and first_pos<=a and b<=last_pos)
                if len(matches)==1:
                    placement_basis="UNIQUE_SOURCE_SAME_CHAPTER_RANGE_IN_AUTHORED_K_PROSE"
        if len(matches)!=1 or placement_basis is None:
            continue
        element,start_pos,end_pos=matches[0]
        candidates[key]={
            "source_first_key":first,"source_reference_ordinal":ordinal,
            "target_native_first_key":units[target_index]["first_key"],
            "original_literal_target_sha256":row["original_osisRef_sha256"],
            "original_visible_label_sha256":row["original_visible_label_sha256"],
            "source_literal":literal,
            "anchor_node":element,"start":start_pos,"end":end_pos,
            "placement_basis":placement_basis,
        }

    from collections import Counter
    counts=Counter(id(x["anchor_node"]) for x in candidates.values())
    candidates={k:v for k,v in candidates.items() if counts[id(v["anchor_node"])]==1}
    for key,x in candidates.items():
        anchor=x["anchor_node"]
        original_text=anchor.text
        display=original_text[x["start"]:x["end"]]
        if not display or len(anchor):
            raise ValueError("Source K heading/prose anchor changed during link mapping")
        link=ET.Element(f"{{{NS}}}reference",{
            "osisRef":x["source_literal"],
            "resp":("BibleResourcesOriginalSourceRangeInModernSectionHeading"
                    if x["placement_basis"]=="EXACT_ORIGINAL_K_SECTION_HEADING"
                    else "BibleResourcesOriginalSourceRangeInModernKProse")})
        link.text=display
        link.tail=original_text[x["end"]:]
        anchor.text=original_text[:x["start"]]
        anchor.insert(0,link)
        x["linked_display_sha256"]=hashlib.sha256(display.encode()).hexdigest()
    if "".join(doc.itertext())!=original_prose:
        raise ValueError("Source range heading link changed modern visible prose")
    remaining=[r for r in ledger["pending"]
               if (r["source_first_key"],r["source_reference_ordinal"]) not in candidates]
    revised={**ledger,
        "source_link_occurrences_verified_in_derived_osis":
            ledger["source_link_occurrences_verified_in_derived_osis"]+len(candidates),
        "source_original_links_still_requiring_placement_review":len(remaining),
        "pending":remaining,
        "publication_authorized":False}
    if (revised["source_link_occurrences_verified_in_derived_osis"]+
            ledger["source_spurious_link_occurrences_explicitly_omitted"]+
            len(remaining)!=ledger["original_native_reference_elements"]):
        raise ValueError("Source original reference inventory changed")
    result=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(result)
    receipt={
        "status":"PRIVATE_SOURCE_OWNED_EXACT_K_HEADING_RANGE_NAVIGATION_NOT_RELEASE",
        "original_native_corpus_sha256":native["original_compiled_corpus_sha256"],
        "source_original_links_restored_to_matching_modern_K_headings":sum(
            x["placement_basis"]=="EXACT_ORIGINAL_K_SECTION_HEADING"
            for x in candidates.values()),
        "source_original_partial_ranges_restored_in_K_exposition":sum(
            x["placement_basis"]=="UNIQUE_SOURCE_SAME_CHAPTER_RANGE_IN_AUTHORED_K_PROSE"
            for x in candidates.values()),
        "source_valid_references_still_in_section_notes":len(remaining)-len(blocked),
        "original_defective_references_remain_blocked":len(blocked),
        "original_text_and_authored_modern_prose_modified":False,
        "heading_relocation_is_an_editorial_transport_not_original_inline_parity":True,
        "publication_authorized":False,
        "placements":[{
            "source_first_key":v["source_first_key"],
            "source_reference_ordinal":v["source_reference_ordinal"],
            "target_native_first_key":v["target_native_first_key"],
            "placement_basis":v["placement_basis"],
            "original_literal_target_sha256":v["original_literal_target_sha256"],
            "original_visible_label_sha256":v["original_visible_label_sha256"],
            "modern_heading_reference_display_sha256":v["linked_display_sha256"],
            "modern_reference_display_sha256":v["linked_display_sha256"],
        } for _,v in sorted(candidates.items())],
    }
    return result,revised,receipt




def build_private_same_chapter_verse_mentions(
        *, source_osis: bytes, ledger: dict, original: dict, native: dict,
        errata: dict) -> tuple[bytes, dict, dict]:
    """Recover original one-verse K-local references on exact authored 'verse N'.

    This does NOT match contextual numbers in unrelated Scripture citations.
    The original source link must resolve to the original commentary chapter,
    the target verse must lie inside the attested native K range, and exactly
    one modern paragraph must explicitly print it as 'verse N' or part of
    'verses N-M' / 'verses N and M'. Only printed numeric tokens are linked,
    never inferred middle verses or a paraphrased quotation.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS, _range
    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("source_reference_labels_or_literal_targets_exported") is not False
            or ledger.get("publication_authorized") is not False
            or native.get("source_prose_or_original_markup_exported") is not False
            or errata.get("status") !=
               "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or errata.get("original_native_corpus_sha256") !=
               native.get("original_compiled_corpus_sha256")):
        raise ValueError("Source-native K/ordinal proof is required for local verse labels")
    blocked={(c["source_first_key"],c["original_reference_ordinal"])
             for c in errata["cases"]}
    if len(blocked)!=4 or any(c.get("approval") is not False
                             for c in errata["cases"]):
        raise ValueError("Unapproved source link errors must stay separate")
    root=ET.fromstring(source_osis)
    modern_visible_before="".join(root.itertext())
    chapters={x.get("osisID"):x for x in root.iter()
              if x.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Unexpected source chapter inventory during local verse recovery")
    sections={}
    source_units={}
    for chapter,node in chapters.items():
        units=native["chapters"][chapter]["original_units"]
        if not units:
            continue
        modern_sections=node.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if len(units)!=len(modern_sections):
            raise ValueError("Original authored K topology changed")
        for unit,section in zip(units,modern_sections):
            if section.get("annotateRef")!=_range(unit["keys"]):
                raise ValueError("Unexpected original native K scope")
            first=unit["first_key"]
            sections[first]=section
            source_units[first]=(unit,len(units))

    # A full reference may already exist inside a <p>; it is a
    # recognition context but must NEVER be linked again. Source labels
    # are sought only in authored paragraph visible text, not notes/headings.
    def paragraph_slots(p):
        pieces=[]
        slots=[]
        index=0
        def emit(node,field,in_link):
            nonlocal index
            value=getattr(node,field)
            if isinstance(value,str) and value:
                slots.append((index,index+len(value),node,field,in_link,value))
                pieces.append(value)
                index+=len(value)
        def walk(node,in_link=False):
            if node.tag==f"{{{NS}}}note":
                return
            linked=in_link or node.tag==f"{{{NS}}}reference"
            emit(node,"text",linked)
            for child in node:
                walk(child,linked)
                emit(child,"tail",in_link)
        walk(p)
        return "".join(pieces),slots

    verse_phrase=re.compile(
        r"\bverses?\s+(\d{1,3})(?:\s*(?:[,;]|and|or|[-–—])"
        r"\s*\d{1,3}){0,8}(?!\d)",re.I)
    by_slot={}
    recoveries={}
    for row in ledger["pending"]:
        first,ordinal=row["source_first_key"],row["source_reference_ordinal"]
        key=(first,ordinal)
        if key in blocked:
            continue
        if first not in sections or first not in original:
            raise ValueError("Missing original K/ordinal in local verse analysis")
        if not (1<=ordinal<=len(original[first])):
            raise ValueError("Original link source ordinal out of bounds")
        literal,label=original[first][ordinal-1]
        if (hashlib.sha256(literal.encode()).hexdigest()!=row["original_osisRef_sha256"]
            or hashlib.sha256(label.encode()).hexdigest()!=
               row["original_visible_label_sha256"]):
            raise ValueError("Original single-verse source label/target not preserved")
        try:
            book,chapter,verse=canonical_only_for_comparison(literal).rsplit(".",2)
        except ValueError:
            continue
        if first.rsplit(".",1)[0]!=f"{book}.{chapter}":
            continue
        unit,count=source_units[first]
        # A single source K marked as verse 1 is an attested underindexed
        # chapter-long authorial body (e.g. Isaiah 15). It does NOT justify
        # synthesizing new K keys.
        if (f"{book}.{chapter}.{verse}" not in unit["keys"]
                and not (count==1 and
                         unit["first_key"]==f"{book}.{chapter}.1")):
            continue
        # The printed original link label itself must name the target verse:
        # e.g. 'Ezek 18:26', '27', 'Is. 15:1'. No silent discrepancy repair.
        if verse not in re.findall(r"\b\d{1,3}\b",label):
            continue
        eligible=[]
        for p in sections[first].findall(f"./{{{NS}}}p"):
            visible,slots=paragraph_slots(p)
            for hit in verse_phrase.finditer(visible):
                numeric_parts=list(re.finditer(r"\d{1,3}",hit.group()))
                for num in numeric_parts:
                    if num.group()!=verse:
                        continue
                    a=hit.start()+num.start()
                    b=hit.start()+num.end()
                    eligible.extend((node,field,value,a-start,b-start)
                        for start,end,node,field,in_link,value in slots
                        if not in_link and start<=a and b<=end)
        if len(eligible)!=1:
            continue
        node,field,value,start,end=eligible[0]
        slot=(id(node),field)
        item={
            "source_first_key":first,"source_reference_ordinal":ordinal,
            "source_target":literal,"source_original_literal_target_sha256":
                row["original_osisRef_sha256"],
            "source_original_label_sha256":row["original_visible_label_sha256"],
            "modern_visible_verse_token_sha256":
                hashlib.sha256(value[start:end].encode()).hexdigest(),
            "node":node,"field":field,"value":value,"start":start,"end":end,
            "slot":slot}
        recoveries[key]=item
        by_slot.setdefault(slot,[]).append(key)
    # Two original source link occurrences must not claim the very same
    # visible number. Ambiguous references remain labelled source notes.
    collision=set()
    for keys in by_slot.values():
        intervals=Counter((recoveries[k]["start"],recoveries[k]["end"])
                          for k in keys)
        for k in keys:
            x=recoveries[k]
            if intervals[(x["start"],x["end"])]>1:
                collision.add(k)
    for k in collision:
        recoveries.pop(k)
    for slot,keys in by_slot.items():
        entries=sorted((recoveries[k] for k in keys if k in recoveries),
                       key=lambda x:x["start"])
        if not entries:
            continue
        node,field,value=entries[0]["node"],entries[0]["field"],entries[0]["value"]
        if any(x["node"] is not node or x["field"]!=field or
               x["value"]!=value for x in entries):
            raise ValueError("Local verse target changed original XML text slot")
        offsets=[]
        pos=0
        for x in entries:
            if x["start"]<pos:
                raise ValueError("Overlapping local original source links")
            ref=ET.Element(f"{{{NS}}}reference",{"osisRef":x["source_target"]})
            ref.text=value[x["start"]:x["end"]]
            offsets.append((value[pos:x["start"]],ref))
            pos=x["end"]
        leftover=value[pos:]
        if field=="text":
            node.text=offsets[0][0]
            for i,(prefix,ref) in enumerate(offsets):
                ref.tail=offsets[i+1][0] if i+1<len(offsets) else leftover
                node.insert(i,ref)
        else:
            section=sections[entries[0]["source_first_key"]]
            parent=next((p for p in section.iter() if node in list(p)),None)
            if parent is None:
                raise ValueError("Local verse tail has no OSIS parent")
            node.tail=offsets[0][0]
            idx=list(parent).index(node)+1
            for i,(prefix,ref) in enumerate(offsets):
                ref.tail=offsets[i+1][0] if i+1<len(offsets) else leftover
                parent.insert(idx+i,ref)
    if "".join(root.itertext())!=modern_visible_before:
        raise ValueError("Reattached local verse links changed modern wording")
    remaining=[r for r in ledger["pending"]
               if (r["source_first_key"],r["source_reference_ordinal"])
                  not in recoveries]
    revised={**ledger,
        "source_link_occurrences_verified_in_derived_osis":
            ledger["source_link_occurrences_verified_in_derived_osis"]+
            len(recoveries),
        "source_original_links_still_requiring_placement_review":len(remaining),
        "pending":remaining,
        "publication_authorized":False}
    if (revised["source_link_occurrences_verified_in_derived_osis"]+
        ledger["source_spurious_link_occurrences_explicitly_omitted"]+
        len(remaining)!=ledger["original_native_reference_elements"]):
        raise ValueError("Original native link inventory not conserved")
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(xml)
    return xml,revised,{
        "status":"PRIVATE_UNIQUE_SOURCE_K_LOCAL_VERSE_NUMBER_LINKS_NOT_RELEASE",
        "source_native_corpus_sha256":native["original_compiled_corpus_sha256"],
        "local_verse_references_recovered_in_authored_modern_prose":
            len(recoveries),
        "unplaced_valid_original_links_still_in_source_only_notes":
            len(remaining)-len(blocked),
        "original_defective_link_occurrences_still_excluded":len(blocked),
        "modern_authored_visible_text_modified":False,
        "original_source_or_native_K_scope_modified":False,
        "independent_editorial_approval":False,
        "publication_authorized":False,
        "placements":[{
           "source_first_key":x["source_first_key"],
           "source_reference_ordinal":x["source_reference_ordinal"],
           "source_original_literal_target_sha256":
               x["source_original_literal_target_sha256"],
           "original_visible_label_sha256":x["source_original_label_sha256"],
           "modern_visible_verse_token_sha256":
               x["modern_visible_verse_token_sha256"],
           "placement_basis":"UNIQUE_SAME_CHAPTER_AUTHORIAL_K_EXPLICIT_VERSE_NUMBER",
        } for _,x in sorted(recoveries.items())],
    }




def build_private_first_K_outline_verse_tokens(
        *, source_osis: bytes, ledger: dict, original: dict, native: dict,
        errata: dict) -> tuple[bytes,dict,dict]:
    """Expose exact original source chapter-outline *single-verse* links.

    The original MHCC 0.1.1 first-K owner carries introductory Scripture
    navigation. Original verse identities and printed labels MUST agree, as
    must the unique verse number in the structurally preserved "Original
    chapter outline" *Verses* cell. Adds no fabricated authorial K body,
    modifies no words, and does not claim original in-sentence placement.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS, _range
    if (ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("publication_authorized") is not False
            or ledger.get("source_reference_labels_or_literal_targets_exported") is not False
            or native.get("source_prose_or_original_markup_exported") is not False
            or errata.get("status") !=
                "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED"
            or errata.get("original_native_corpus_sha256") !=
                native.get("original_compiled_corpus_sha256")):
        raise ValueError("Missing original source K metadata for outline navigational links")
    blocked={(x["source_first_key"],x["original_reference_ordinal"])
             for x in errata["cases"]}
    if len(blocked)!=4 or any(x.get("approval") is not False
                             for x in errata["cases"]):
        raise ValueError("Bad original source links must not be recovered by outline")
    root=ET.fromstring(source_osis)
    authored_before="".join(root.itertext())
    chapters={x.get("osisID"):x for x in root.iter()
              if x.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Original SWORD chapter coverage drift")
    outline_by_chapter={}
    for chapter, ch in chapters.items():
        units=native["chapters"][chapter]["original_units"]
        if not units:
            continue
        sections=ch.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections)!=len(units) or any(
                section.get("annotateRef")!=_range(unit["keys"])
                for unit,section in zip(units,sections)):
            raise ValueError("Original native K section ownership changed")
        intros=[i for i in ch.findall(f"./{{{NS}}}div[@type='introduction']")
                if i.find(f"./{{{NS}}}title") is not None and
                i.find(f"./{{{NS}}}title").text=="Original chapter outline"]
        if len(intros)!=1:
            continue
        tables=intros[0].findall(f"./{{{NS}}}table")
        if len(tables)!=1:
            continue
        rows=tables[0].findall(f"./{{{NS}}}row")
        if len(rows)<2:
            continue
        header=rows[0].findall(f"./{{{NS}}}cell")
        if len(header)!=2 or [("".join(x.itertext())).strip() for x in header]!=[
                "Original outline","Verses"]:
            continue
        candidate_cells=[]
        for row in rows[1:]:
            cells=row.findall(f"./{{{NS}}}cell")
            if len(cells)!=2:
                continue
            cell=cells[1]
            # Only original unlinked, literal number-list cells are eligible.
            if len(cell)!=0 or not isinstance(cell.text,str):
                continue
            printed=cell.text.strip()
            if not re.fullmatch(r"\d{1,3}(?:\s*[,;]\s*\d{1,3}){0,12}",printed):
                continue
            digits=list(re.finditer(r"\d{1,3}",cell.text))
            if len({int(m.group()) for m in digits})!=len(digits):
                continue
            for m in digits:
                candidate_cells.append((m.group(),cell,m.start(),m.end()))
        outline_by_chapter[chapter]=(units,candidate_cells)

    candidates={}
    for row in ledger["pending"]:
        first,ordinal=row["source_first_key"],row["source_reference_ordinal"]
        if (first,ordinal) in blocked:
            continue
        if first not in original or not 1<=ordinal<=len(original[first]):
            raise ValueError("Original source K ordinal is missing from canonical ledger")
        literal,label=original[first][ordinal-1]
        if (hashlib.sha256(literal.encode()).hexdigest()!=row["original_osisRef_sha256"]
                or hashlib.sha256(label.encode()).hexdigest()!=
                row["original_visible_label_sha256"]):
            raise ValueError("Source K original link/label identity mismatch")
        try:
            book,chapter,verse=canonical_only_for_comparison(literal).rsplit(".",2)
        except ValueError:
            continue
        chapter_id=f"{book}.{chapter}"
        if first.rsplit(".",1)[0]!=chapter_id or chapter_id not in outline_by_chapter:
            continue
        units,cells=outline_by_chapter[chapter_id]
        if units[0]["first_key"]!=first:
            continue
        # Original labels such as 'Is. 21:11', '12' must agree with
        # exactly the same target verse. Cross-book numeric collisions
        # are impossible because first owner and target chapter agree.
        if verse not in re.findall(r"\b\d{1,3}\b",label):
            continue
        options=[(cell,a,b) for number,cell,a,b in cells if number==verse]
        if len(options)!=1:
            continue
        cell,a,b=options[0]
        candidates[(first,ordinal)]={
            "source_first_key":first,"source_reference_ordinal":ordinal,
            "source_target":literal,"source_target_sha256":row["original_osisRef_sha256"],
            "original_label_sha256":row["original_visible_label_sha256"],
            "cell":cell,"a":a,"b":b,
        }
    # Multiple original links cannot claim the same digit in an outline
    # cell; such collisions are editorially unresolved, not silently linked.
    counts=Counter((id(x["cell"]),x["a"],x["b"]) for x in candidates.values())
    candidates={k:x for k,x in candidates.items()
                if counts[(id(x["cell"]),x["a"],x["b"])]==1}
    by_cell={}
    for key,x in candidates.items():
        by_cell.setdefault(id(x["cell"]),[]).append(x)
    for elements in by_cell.values():
        cell=elements[0]["cell"]
        before=cell.text
        elements.sort(key=lambda x:x["a"])
        if any(x["cell"] is not cell for x in elements):
            raise ValueError("Original outline source cell identity changed")
        pos=0
        cell.text=before[:elements[0]["a"]]
        for i,x in enumerate(elements):
            if x["a"]<pos:
                raise ValueError("Overlapping original outline verse link positions")
            if i>0:
                elements[i-1]["ref"].tail=before[pos:x["a"]]
            ref=ET.Element(f"{{{NS}}}reference",{
                "osisRef":x["source_target"],
                "resp":"BibleResourcesSourceFirstKOriginalOutlineVerseNavigation"})
            ref.text=before[x["a"]:x["b"]]
            x["visible_token_sha256"]=hashlib.sha256(ref.text.encode()).hexdigest()
            cell.insert(i,ref)
            x["ref"]=ref
            pos=x["b"]
        elements[-1]["ref"].tail=before[pos:]
    if "".join(root.itertext())!=authored_before:
        raise ValueError("Original modern outline navigation changed visible manuscript")
    remaining=[row for row in ledger["pending"]
               if (row["source_first_key"],row["source_reference_ordinal"])
                  not in candidates]
    revised={**ledger,
        "source_link_occurrences_verified_in_derived_osis":
            ledger["source_link_occurrences_verified_in_derived_osis"]+len(candidates),
        "source_original_links_still_requiring_placement_review":len(remaining),
        "pending":remaining,"publication_authorized":False}
    if (revised["source_link_occurrences_verified_in_derived_osis"]+
        ledger["source_spurious_link_occurrences_explicitly_omitted"]+
        len(remaining)!=ledger["original_native_reference_elements"]):
        raise ValueError("Reconstructed source outline lost an original hyperlink identity")
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(xml)
    return xml,revised,{
        "status":"PRIVATE_SOURCE_FIRST_K_EXACT_OUTLINE_VERSE_NAVIGATION_NOT_ORIGINAL_INLINE",
        "source_native_corpus_sha256":native["original_compiled_corpus_sha256"],
        "source_first_K_outline_verse_links_recovered":len(candidates),
        "valid_original_source_references_still_in_separate_K_notes":
            len(remaining)-len(blocked),
        "original_defective_link_occurrences_remain_excluded":len(blocked),
        "original_modern_visible_text_modified":False,
        "source_K_structure_or_original_link_target_modified":False,
        "placement_is_editorial_outline_navigation_not_authorial_inline":True,
        "publication_authorized":False,
        "placements":[{
            "source_first_key":v["source_first_key"],
            "source_reference_ordinal":v["source_reference_ordinal"],
            "original_literal_target_sha256":v["source_target_sha256"],
            "original_visible_label_sha256":v["original_label_sha256"],
            "modern_outline_verse_number_sha256":v["visible_token_sha256"]
        } for _,v in sorted(candidates.items())]
    }



def build_private_source_preface_verse_links(
        *, preface_osis: bytes, source_note_receipt: dict,
        source_review_packet: dict, preface_proof: dict,
        native: dict) -> tuple[bytes,dict]:
    """Place source-K book-preface citations on exact modern prefaced verse tokens.

    This separate private alternative is a *documented editorial navigation*
    from authenticated source-first K into separately restored modern book
    prefaces. It is NOT original authorial inline-location proof. Moving a
    reference removes its duplicate K source-only note; original K, literal
    source target, translated prose and metadata are otherwise untouched.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS
    corpus=native.get("original_compiled_corpus_sha256")
    if (corpus is None
            or source_note_receipt.get("status") !=
                "PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY"
            or source_note_receipt.get("original_native_corpus_sha256")!=corpus
            or source_note_receipt.get("source_link_supplement_not_authorial_or_inline") is not True
            or source_note_receipt.get("published_or_distributed") is not False
            or source_review_packet.get("status")!=
                "EPHEMERAL_EXCERPTS_PRIVATE_EDITORIAL_REVIEW_ONLY"
            or source_review_packet.get("source_pinned_corpus_sha256")!=corpus
            or source_review_packet.get("original_full_K_prose_or_markup_exported") is not False
            or source_review_packet.get("original_link_placement_approved") is not False
            or preface_proof.get("status") !=
                "PRIVATE_SOURCE_K_BOOK_PREFACE_RESTORATION_NOT_EDIT_OR_RELEASE"
            or preface_proof.get("original_native_corpus_sha256")!=corpus
            or preface_proof.get("original_K_section_and_existing_links_unchanged") is not True
            or preface_proof.get("publication_authorized") is not False):
        raise ValueError("Source-linked first-K book prefaces require private pinned receipts")
    refs_by_K={}
    for row in source_note_receipt["note_source_K_reference_hashes_for_private_native_readback"]:
        first=row["source_first_key"]
        if first in refs_by_K:
            raise ValueError("Duplicate original first-K notes in receipt")
        refs_by_K[first]=row["original_source_reference_hashes"]
    if (sum(len(x) for x in refs_by_K.values()) !=
            source_note_receipt["original_link_occurrences_preserved_only_in_separate_source_notes"]):
        raise ValueError("Truncated original K source-only reference receipt")
    review={}
    for row in source_review_packet["references"]:
        key=(row["source_first_key"],row["source_reference_ordinal"])
        if key in review:
            raise ValueError("Duplicate original source K/ordinal")
        review[key]=row
    proof_by_book={case["book"]:case for case in preface_proof["cases"]}
    if len(proof_by_book)!=len(preface_proof["cases"]):
        raise ValueError("Duplicate source book-preface witnesses")
    root=ET.fromstring(preface_osis)
    chapters={n.get("osisID"):n for n in root.iter()
              if n.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Original source K chapter inventory changed in book preface")
    source_note_nodes={}
    for chapter,chapter_node in chapters.items():
        first_units=native["chapters"][chapter]["original_units"]
        secs=chapter_node.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if len(first_units)!=len(secs):
            if not first_units:
                continue
            raise ValueError("Original K group count changed in modern preface preview")
        for unit,sec in zip(first_units,secs):
            first=unit["first_key"]
            if first not in refs_by_K:
                continue
            notes=[n for n in sec if n.tag==f"{{{NS}}}note" and
                   n.get("resp")=="BibleResourcesPrivateSourceOnlyLinkSupplement"]
            if len(notes)!=1:
                raise ValueError("Exact original source K note missing from book-preface candidate")
            noted=[n for n in notes[0] if n.tag==f"{{{NS}}}reference"]
            if len(noted)!=len(refs_by_K[first]):
                raise ValueError("Original source K reference note cardinality drift")
            for ref,item in zip(noted,refs_by_K[first]):
                if (hashlib.sha256(ref.get("osisRef").encode()).hexdigest()!=
                        item["source_original_literal_target_sha256"]
                    or hashlib.sha256("".join(ref.itertext()).encode()).hexdigest()!=
                        item["supplement_display_sha256"]):
                    raise ValueError("Book-preface original source K target/display hash drift")
            source_note_nodes[first]=(sec,notes[0],noted)

    # The same anchored modern book-preface prose is already authenticated
    # by the independently validated original native first-K book-preface
    # passage receipt. Never draw candidate prose from other books/chapters.
    book_intros={}
    for book,case in proof_by_book.items():
        if case["source_K_intro_disposition"] not in (
                "INSERTED_SEPARATE_MODERN_INTRO_FROM_VERIFIED_ORIGINAL_K",
                "PRESENT_IN_MODERN_FIRST_CHAPTER_EXACT_NO_DUPLICATION"):
            continue
        chapter=book+".1"
        if chapter not in chapters or not native["chapters"][chapter]["original_units"]:
            continue
        first=native["chapters"][chapter]["original_units"][0]["first_key"]
        if case["original_source_first_K"]!=first or first not in source_note_nodes:
            continue
        intros=[d for d in chapters[chapter].findall(
                    f"./{{{NS}}}div[@type='introduction']")
                if d.find(f"./{{{NS}}}title") is not None and
                "book introduction" in (
                    "".join(d.find(f"./{{{NS}}}title").itertext()).casefold())]
        if len(intros)!=1:
            continue
        book_intros[first]=intros[0]

    def authored_without_supplement(doc):
        parts=[]
        def walk(n):
            if n.tag==f"{{{NS}}}note" and n.get("resp")==(
                    "BibleResourcesPrivateSourceOnlyLinkSupplement"):
                if n.tail:
                    parts.append(n.tail)
                return
            if n.text:
                parts.append(n.text)
            for child in n:
                walk(child)
                if child.tail and not (
                    child.tag==f"{{{NS}}}note" and child.get("resp")==
                    "BibleResourcesPrivateSourceOnlyLinkSupplement"):
                    parts.append(child.tail)
        walk(doc)
        return "".join(parts)
    authored_before=authored_without_supplement(root)

    def projected(p):
        chunks=[]
        fragments=[]
        current=0
        def emit(node,attr,inside_ref):
            nonlocal current
            val=getattr(node,attr)
            if isinstance(val,str) and val:
                chunks.append((current,current+len(val),node,attr,inside_ref,val))
                fragments.append(val)
                current+=len(val)
        def walk(node,inside_ref=False):
            if node.tag==f"{{{NS}}}note":
                return
            is_ref=inside_ref or node.tag==f"{{{NS}}}reference"
            emit(node,"text",is_ref)
            for child in node:
                walk(child,is_ref)
                emit(child,"tail",inside_ref)
        walk(p)
        return "".join(fragments),chunks

    chosen={}
    for first,intro in book_intros.items():
        for hashrow in refs_by_K[first]:
            ordinal=hashrow["source_reference_ordinal"]
            source=review.get((first,ordinal))
            if source is None:
                raise ValueError("Original-K note has no authenticated original-source witness")
            literal=source["original_literal_osisRef"]
            if (hashlib.sha256(literal.encode()).hexdigest()!=
                    hashrow["source_original_literal_target_sha256"]
                or source["source_literal_target_sha256"] !=
                    hashrow["source_original_literal_target_sha256"]
                or hashlib.sha256(source["original_printed_link_label"].encode()).hexdigest()!=
                    source["original_visible_label_sha256"]):
                raise ValueError("Original book preface link target/label not authenticated")
            try:
                book,chapter,verse=canonical_only_for_comparison(literal).rsplit(".",2)
            except ValueError:
                continue
            if (verse not in re.findall(r"\b\d{1,3}\b",
                        source["original_printed_link_label"])):
                continue
            names=set(_AUTO_ALIASES.get(book,()))
            names.add(_ENGLISH_NAME_BY_OSIS[book])
            if not all(isinstance(n,str) and n for n in names):
                continue
            aliases="|".join(re.escape(n) for n in sorted(names,key=len,reverse=True))
            full=re.compile(
                r"(?<![A-Za-z0-9])(?:"+aliases+r")\s+"
                r"\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*"
                r"(?:\s*;\s*\d+\s*:\s*\d+(?:\s*[,\u2013\u2014-]\s*\d+)*)*",
                re.IGNORECASE)
            spots=[]
            for p in intro.findall(f"./{{{NS}}}p"):
                rendered,chunks=projected(p)
                for hit in full.finditer(rendered):
                    printed=hit.group()
                    for pair in re.finditer(
                            r"(?<!\d)(\d+)\s*:\s*(\d+)"
                            r"((?:\s*[,\u2013\u2014-]\s*\d+)*)",printed):
                        if pair[1]!=chapter:
                            continue
                        nums=[(pair[2],pair.start(2),pair.end(2))]
                        nums.extend((m.group(),pair.start(3)+m.start(),
                                     pair.start(3)+m.end())
                                    for m in re.finditer(r"\d+",pair[3]))
                        for number,a,b in nums:
                            if number!=verse:
                                continue
                            start,end=hit.start()+a,hit.start()+b
                            spots.extend((node,attr,val,start-offset,end-offset)
                                for offset,last,node,attr,linked,val in chunks
                                if not linked and offset<=start and end<=last)
            if len(spots)!=1:
                continue
            node,attr,val,a,b=spots[0]
            chosen[(first,ordinal)]={
                "source_first_key":first,"source_reference_ordinal":ordinal,
                "original_source_literal_target_sha256":
                    hashrow["source_original_literal_target_sha256"],
                "source_printed_label_sha256":
                    source["original_visible_label_sha256"],
                "original_source_supplement_display_sha256":
                    hashrow["supplement_display_sha256"],
                "modern_verse_token_sha256":
                    hashlib.sha256(val[a:b].encode()).hexdigest(),
                "target":literal,
                "node":node,"attr":attr,"value":val,"a":a,"b":b,
            }
    overlaps=Counter((id(v["node"]),v["attr"],v["a"],v["b"])
                     for v in chosen.values())
    chosen={k:v for k,v in chosen.items()
            if overlaps[(id(v["node"]),v["attr"],v["a"],v["b"])]==1}
    slots={}
    for v in chosen.values():
        slots.setdefault((id(v["node"]),v["attr"]),[]).append(v)
    for entries in slots.values():
        entries.sort(key=lambda x:x["a"])
        n,attr,val=entries[0]["node"],entries[0]["attr"],entries[0]["value"]
        if any(v["node"] is not n or v["attr"]!=attr or
               v["value"]!=val for v in entries):
            raise ValueError("Unexpected modern preface verse slot drift")
        pos=0
        pieces=[]
        for entry in entries:
            if entry["a"]<pos:
                raise ValueError("Overlapping original book-preface citation targets")
            link=ET.Element(f"{{{NS}}}reference",{
                "osisRef":entry["target"],
                "resp":"BibleResourcesOriginalFirstKSourceLinkedModernBookPreface"})
            link.text=val[entry["a"]:entry["b"]]
            pieces.append((val[pos:entry["a"]],link))
            pos=entry["b"]
        trailing=val[pos:]
        if attr=="text":
            n.text=pieces[0][0]
            for index,(_,link) in enumerate(pieces):
                link.tail=(pieces[index+1][0] if index+1<len(pieces) else trailing)
                n.insert(index,link)
        else:
            parent=next((p for intro in book_intros.values() for p in intro.iter()
                         if n in list(p)),None)
            if parent is None:
                raise ValueError("No modern preface parent for trailing source token")
            n.tail=pieces[0][0]
            index=list(parent).index(n)+1
            for i,(_,link) in enumerate(pieces):
                link.tail=(pieces[i+1][0] if i+1<len(pieces) else trailing)
                parent.insert(index+i,link)

    # The sole original source note is authoritative until its printed
    # modern-book-preface alternative has been independently pinned.
    remaining={}
    for first,(section,note,refs) in source_note_nodes.items():
        original_hashes=refs_by_K[first]
        retain=[(ref,h) for ref,h in zip(refs,original_hashes)
                if (first,h["source_reference_ordinal"]) not in chosen]
        if len(retain)==len(refs):
            remaining[first]=original_hashes
            continue
        if not retain:
            section.remove(note)
            continue
        note[:]=[]
        for index,(ref,h) in enumerate(retain):
            ref.tail="; " if index<len(retain)-1 else "."
            note.append(ref)
        remaining[first]=[h for ref,h in retain]
    if authored_without_supplement(root)!=authored_before:
        raise ValueError("Private original book-intro citation placement changed modern prose")
    if sum(map(len,remaining.values()))+len(chosen)!=sum(
            map(len,refs_by_K.values())):
        raise ValueError("Private modern book-introduction link inventory changed")
    output=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(output)
    return output,{
        "status":"PRIVATE_SOURCE_FIRST_K_BOOK_INTRO_EXACT_CITATION_RELOCATION_NOT_APPROVED",
        "original_native_corpus_sha256":corpus,
        "original_source_link_occurrences_moved_to_modern_book_intro":len(chosen),
        "original_K_source_only_note_occurrences_remaining":sum(
            map(len,remaining.values())),
        "original_K_and_modern_authored_visible_prose_modified":False,
        "original_source_target_and_label_sha_verified":True,
        "source_to_modern_book_preface_placement_is_editorial_navigation":True,
        "no_original_inline_placement_claim":True,
        "original_source_module_modified":False,
        "publication_authorized":False,
        "placements":[{
            "source_first_key":v["source_first_key"],
            "source_reference_ordinal":v["source_reference_ordinal"],
            "source_literal_target_sha256":
                v["original_source_literal_target_sha256"],
            "source_original_label_sha256":v["source_printed_label_sha256"],
            "modern_verse_token_sha256":v["modern_verse_token_sha256"],
        } for _,v in sorted(chosen.items())],
        "remaining_notes_by_original_first_K":[{
            "source_first_key":first,
            "source_note_reference_hashes":values,
        } for first,values in sorted(remaining.items())],
    }



def build_private_inline_original_reference_index(
        *, source_note_osis: bytes, source_receipt: dict,
        native: dict) -> tuple[bytes,dict]:
    """Expose all source-owned unplaced links visibly in their K section.

    This is a *separate unpublished reader alternative*, not a repair of the
    original in-prose position. Every source link is usable immediately,
    while its unproven precise prose placement stays explicitly labelled.
    """
    from collections import Counter
    from commentary_modern_draft_osis_preview import NS, _range
    if (source_receipt.get("status") !=
            "PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY"
            or not isinstance(source_receipt.get("original_link_occurrences_preserved_only_in_separate_source_notes"),int)
            or source_receipt["original_link_occurrences_preserved_only_in_separate_source_notes"] <= 0
            or source_receipt.get("source_link_supplement_not_authorial_or_inline") is not True
            or source_receipt.get("published_or_distributed") is not False
            or source_receipt.get("original_native_corpus_sha256") !=
            native.get("original_compiled_corpus_sha256")):
        raise ValueError("Cannot promote unsourced original notes into inline index")

    root=ET.fromstring(source_note_osis)
    authored_before=[]
    original_links=[]
    original_groups={}
    chapters={x.get("osisID"):x for x in root.iter()
              if x.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Original chapter coverage changed in inline index")
    expected_groups={x["source_first_key"]:x
                     for x in source_receipt["note_source_K_reference_hashes_for_private_native_readback"]}
    if len(expected_groups)!=source_receipt["source_first_K_sections_with_note"]:
        raise ValueError("Source reference K group identity duplicated")
    for chapter, ch in chapters.items():
        units=native["chapters"][chapter]["original_units"]
        if not units:
            continue
        sections=ch.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections)!=len(units):
            raise ValueError("Different K authorial section count")
        for source,sec in zip(units,sections):
            if sec.get("annotateRef")!=_range(source["keys"]):
                raise ValueError("SWORD K section identity changed")
            notes=[n for n in sec if n.tag==f"{{{NS}}}note"
                   and n.get("resp")=="BibleResourcesPrivateSourceOnlyLinkSupplement"]
            first=source["first_key"]
            if first not in expected_groups:
                if notes:
                    raise ValueError("Unexpected original link appendix")
                continue
            if len(notes)!=1:
                raise ValueError("Missing source-pinned original link appendix")
            source_note=notes[0]
            ref_nodes=[x for x in source_note
                       if x.tag==f"{{{NS}}}reference"]
            hashes=expected_groups[first]["original_source_reference_hashes"]
            if len(ref_nodes)!=len(hashes):
                raise ValueError("Unplaced original hyperlinks lost on transfer")
            for n,receipt in zip(ref_nodes,hashes):
                literal=n.get("osisRef")
                visible="".join(n.itertext())
                if (not isinstance(literal,str)
                        or hashlib.sha256(literal.encode()).hexdigest()!=
                        receipt["source_original_literal_target_sha256"]
                        or hashlib.sha256(visible.encode()).hexdigest()!=
                        receipt["supplement_display_sha256"]):
                    raise ValueError("Original link target or label drift in inline index")
                original_links.append((first,literal,visible))
            p=ET.Element(f"{{{NS}}}p",{
                "resp":"BibleResourcesOriginalSourceReferenceIndexOnly",
            })
            p.text=("Original-edition Bible references for this commentary "
                    "section (exact original sentence locations unverified): ")
            # Move the SAME XML hyperlink nodes, without replacement,
            # normalization, coalescing, or rerouting.
            for n in ref_nodes:
                source_note.remove(n)
                p.append(n)
            index=list(sec).index(source_note)
            sec.remove(source_note)
            sec.insert(index,p)
            original_groups[first]=len(ref_nodes)
    if set(original_groups)!=set(expected_groups):
        raise ValueError("Missing original K groups in visible source-reference index")
    original_note_total=source_receipt["original_link_occurrences_preserved_only_in_separate_source_notes"]
    if (len(original_links)!=original_note_total or
            sum(original_groups.values())!=original_note_total or
            sum(len(x["original_source_reference_hashes"])
                for x in expected_groups.values())!=original_note_total):
        raise ValueError("Not all source-attested original reference notes are visible")
    if any(n.get("resp")=="BibleResourcesPrivateSourceOnlyLinkSupplement"
           for n in root.iter() if n.tag==f"{{{NS}}}note"):
        raise ValueError("An old hidden source-only note survived")

    output=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(output)
    return output,{
        "status":"PRIVATE_SOURCE_REFERENCES_VISIBLE_IN_K_NOT_EXACT_AUTHORIAL_INLINE",
        "original_native_corpus_sha256":native["original_compiled_corpus_sha256"],
        "original_unplaced_valid_references_visible_in_commentary":len(original_links),
        "original_K_groups_with_reference_index":len(original_groups),
        "original_literal_targets_and_displays_reused_without_rewriting":True,
        "original_text_or_modern_authored_prose_edited":False,
        "precise_original_sentence_locations_proven":False,
        "published_or_distributed":False,
        "reference_index_by_source_first_key":[{
            "source_first_key":first,"reference_count":original_groups[first],
            "original_reference_target_display_hashes":[{
                "target_sha256":hashlib.sha256(literal.encode()).hexdigest(),
                "display_sha256":hashlib.sha256(label.encode()).hexdigest(),
            } for key,literal,label in original_links if key==first]
        } for first in sorted(original_groups)],
    }


def build_unapproved_source_errata_notes_preview(
        *, source_note_osis: bytes, ledger: dict,
        native: dict, errata: dict) -> tuple[bytes, dict]:
    """A *third* private preview of proposed fixes, never source-native links.

    Four wrong original target identities are SHA authenticated by the
    separate source-only validation. Candidate Scripture destinations come
    from an explicitly versioned secondary-witness editorial manifest.
    Proposed links are never substituted into authorial modern text or the
    unchanged original source note candidate.
    """
    from commentary_modern_draft_osis_preview import NS, _range

    validate_pending_source_reference_errata(
        manifest=errata, ledger=ledger, native=native)
    if (errata.get("proposed_navigation_note_status") !=
            "UNAPPROVED_SEPARATE_EDITORIAL_REPAIR_PREVIEW_NOT_IN_ORIGINAL_SOURCE"
            or errata.get("proposed_navigation_note_publication_authorized")
                is not False):
        raise ValueError("Proposed source-link repair is not an unpublished review")
    cases=errata.get("cases")
    if not isinstance(cases,list) or not cases:
        raise ValueError("Source errata review has no canonical cases")
    doc=ET.fromstring(source_note_osis)
    before="".join(doc.itertext())
    chapters={ch.get("osisID"):ch for ch in doc.iter()
              if ch.tag==f"{{{NS}}}chapter"}
    if set(chapters)!=set(native.get("chapters",{})):
        raise ValueError("Private errata preview chapter source inventory changed")
    receipts=[]
    n=0
    for case in cases:
        first=case["source_first_key"]
        ordinal=case["original_reference_ordinal"]
        chapter=first.rsplit(".",1)[0]
        units=native["chapters"][chapter]["original_units"]
        indices=[i for i,u in enumerate(units) if u["first_key"]==first]
        if len(indices)!=1:
            raise ValueError("No unique K owner for original link repair")
        sections=chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        idx=indices[0]
        if (len(sections)!=len(units)
                or sections[idx].get("annotateRef")!=_range(units[idx]["keys"])):
            raise ValueError("Unapproved repair cannot change modern source scope")
        proposed=case.get("proposed_navigation_targets_for_unpublished_review")
        if (not isinstance(proposed,list) or not proposed
                or len(proposed)!=len(set(proposed))
                or any(not isinstance(x,str) or not _allowed_source_link_target(x)
                       for x in proposed)
                or not isinstance(case.get("proposed_navigation_witness_class"),str)):
            raise ValueError("Malformed proposed repair candidate navigation")
        if (case.get("finding")=="ORIGINAL_DIGITAL_WITNESS_POINTS_TO_WRONG_VERSE"
                and proposed!=[case.get("proposed_corrected_target")]):
            raise ValueError("Wrong-verse repair does not match witnessed correction")
        if (case.get("finding")=="INVALID_CROSS_CHAPTER_NAVIGATION_IN_ORIGINAL_OSISREF"
                and case.get("candidate_fragment") not in proposed):
            raise ValueError("Composite original repair omits verified initial span")
        section=sections[idx]
        note=ET.SubElement(section,f"{{{NS}}}note",{
            "type":"crossReference",
            "resp":"BibleResourcesPrivateUnapprovedOriginalErrataPreview",
        })
        note.text=(
            "Proposed editorial repair of a faulty original-edition link "
            "(unapproved; not an original authorial link): ")
        spans=[]
        for i,literal in enumerate(proposed):
            display=_source_link_supplement_display(literal)
            ref=ET.SubElement(note,f"{{{NS}}}reference",{"osisRef":literal})
            ref.text=display
            ref.tail="; " if i<len(proposed)-1 else "."
            spans.append({
                "candidate_target_sha256":hashlib.sha256(
                    literal.encode("utf-8")).hexdigest(),
                "candidate_derived_display_sha256":hashlib.sha256(
                    display.encode("utf-8")).hexdigest()
            })
            n+=1
        receipts.append({
            "source_first_key":first,
            "source_original_link_ordinal":ordinal,
            "original_source_literal_target_sha256":case["original_target_sha256"],
            "candidate_references":spans
        })
    if (len(receipts)!=errata.get("proposed_navigation_source_links_repaired_in_editorial_preview")
            or n!=errata.get("proposed_navigation_note_count")):
        raise ValueError("Editorial repair proposed link candidate count drift")
    def original_without_repairs(node):
        parts=[node.text or ""]
        for child in node:
            if (child.tag!=f"{{{NS}}}note" or child.get("resp")!=
                    "BibleResourcesPrivateUnapprovedOriginalErrataPreview"):
                parts.append(original_without_repairs(child))
            parts.append(child.tail or "")
        return "".join(parts)
    if original_without_repairs(doc)!=before:
        raise ValueError("Unapproved errata preview changed prior modern/source-note text")
    output=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(output)
    return output,{
        "status":"PRIVATE_UNAPPROVED_ORIGINAL_ERRATA_NAVIGATION_PREVIEW_NOT_SOURCE_OR_RELEASE",
        "original_source_link_occurrences_provisionally_repaired":len(receipts),
        "derived_navigation_links_from_corroborating_witnesses":n,
        "original_and_modern_edition_text_unchanged":True,
        "prior_source_only_notes_unchanged":True,
        "original_invalid_source_targets_retained_in_source_errata_evidence":True,
        "editorial_approval":False,
        "public_distribution":False,
        "original_source_K_ordinal_proposed_navigation_hashes":receipts,
    }


def build_private_additional_source_errata_preview(
        *, prior_private_osis: bytes, manifest: dict,
        ledger: dict, native: dict) -> tuple[bytes, dict]:
    """Keep further bad source links in a separate, *unapproved* navigation preview.

    Check each original native K, its literal destination and printed label by
    SHA before rendering secondary-witness destinations only as marked notes.
    Neither source notes nor the modern commentator's visible prose are
    rewritten. This is not editorial or public-distribution approval.
    """
    from commentary_modern_draft_osis_preview import NS, _range

    if (manifest.get("status") !=
            "ORIGINAL_DIGITAL_SOURCE_LINK_DISCREPANCIES_REVIEW_ONLY_NOT_APPLIED"
            or manifest.get("edition") != "MHCC 0.1.1 pinned compiled SWORD"
            or manifest.get("original_corpus_sha256") !=
            native.get("original_compiled_corpus_sha256")
            or manifest.get("private_review_candidate_only") is not True
            or manifest.get("private_review_note_status") !=
            "PRIVATE_PROPOSED_SECONDARY_WITNESS_LINK_NAVIGATION_NOT_SOURCE_OR_RELEASE"
            or any(manifest.get(k) is not False for k in (
                "original_source_modified", "modern_chapter_prose_modified",
                "proposed_navigation_approved", "publication_authorized"))
            or ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or ledger.get("publication_authorized") is not False):
        raise ValueError("Additional errata require original source/receipt and private review status")

    cases = manifest.get("cases")
    if (not isinstance(cases, list) or len(cases) != 11
            or manifest.get("proposed_navigation_source_links_for_private_review")
                != len(cases)):
        raise ValueError("Expected eleven explicit original-link discrepancies")

    pending_rows = ledger.get("pending", [])
    pending = {(r["source_first_key"], r["source_reference_ordinal"]): r
               for r in pending_rows}
    if len(pending) != len(pending_rows):
        raise ValueError("Ambiguous original K and ordinal identity")

    doc = ET.fromstring(prior_private_osis)
    original_bytes = ET.tostring(doc, encoding="utf-8")
    chapters = {ch.get("osisID"): ch for ch in doc.iter()
                if ch.tag == f"{{{NS}}}chapter"}
    if set(chapters) != set(native.get("chapters", {})):
        raise ValueError("Original native chapter census differs from private modern OSIS")

    seen = set()
    receipts = []
    total_targets = 0
    for case in cases:
        first, ordinal = (case.get("source_first_key"),
                          case.get("source_reference_ordinal"))
        key = (first, ordinal)
        source_row = pending.get(key)
        if (key in seen or source_row is None or
                type(ordinal) is not int or case.get("approval") is not False):
            raise ValueError("Additional source error is duplicated, already placed or unbound")
        seen.add(key)
        original_literal = case.get("original_osisRef")
        original_label = case.get("original_link_label")
        if (not isinstance(original_literal, str)
                or not isinstance(original_label, str)
                or hashlib.sha256(original_literal.encode("utf-8")).hexdigest()
                    != case.get("original_target_sha256")
                or hashlib.sha256(original_label.encode("utf-8")).hexdigest()
                    != case.get("original_label_sha256")
                or source_row.get("original_osisRef_sha256") !=
                    case["original_target_sha256"]
                or source_row.get("original_visible_label_sha256") !=
                    case["original_label_sha256"]):
            raise ValueError("Original source-link target/printed-label fingerprints differ")

        chapter = first.rsplit(".", 1)[0]
        native_units = native["chapters"][chapter]["original_units"]
        indices = [i for i, u in enumerate(native_units)
                   if u.get("first_key") == first and
                   u.get("source_unit_sha256") ==
                   case.get("original_native_unit_sha256")]
        if len(indices) != 1:
            raise ValueError("Additional source-error native authorial K SHA differs")
        sections = chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if (len(sections) != len(native_units) or
                sections[indices[0]].get("annotateRef") !=
                _range(native_units[indices[0]]["keys"])):
            raise ValueError("Modern section does not retain original K ownership")

        proposals = case.get("proposed_destinations")
        context = case.get("proposed_navigation_context")
        allowed_contexts = {
            "DIGITAL_LINK_TARGET_MISMATCH_VS_PRINTED_SOURCE",
            "SOURCE_SECTION_NAVIGATION_NOT_AUTHORIAL_SENTENCE",
            "ORIGINAL_PRINTED_REFERENCE_DISCREPANCY_NOT_SILENTLY_CORRECTED",
        }
        if (not isinstance(proposals, list) or not proposals or
                len(proposals) != len(set(proposals))
                or any(not isinstance(v, str) or
                       not _allowed_source_link_target(v) for v in proposals)
                or context not in allowed_contexts):
            raise ValueError("Additional preview has unsupported navigation or context")
        if (first == "Num.29.1") != (
                context == "ORIGINAL_PRINTED_REFERENCE_DISCREPANCY_NOT_SILENTLY_CORRECTED"):
            raise ValueError("Printed-source erratum was not distinguished")
        if first == "Jude.1.8" and context != (
                "SOURCE_SECTION_NAVIGATION_NOT_AUTHORIAL_SENTENCE"):
            raise ValueError("Jude's ambiguous printed Jud label must stay a transition")

        note = ET.SubElement(sections[indices[0]], f"{{{NS}}}note", {
            "type": "crossReference",
            "resp": "BibleResourcesPrivateUnapprovedAdditionalLinkReview",
        })
        note.text = (
            "Unapproved source-printed citation correction (not the original text): "
            if context == "ORIGINAL_PRINTED_REFERENCE_DISCREPANCY_NOT_SILENTLY_CORRECTED"
            else "Unapproved proposed section-navigation correction (not an original in-sentence link): "
            if context == "SOURCE_SECTION_NAVIGATION_NOT_AUTHORIAL_SENTENCE"
            else "Unapproved digital-link destination correction (secondary witness): ")
        candidate_hashes = []
        for i, target in enumerate(proposals):
            display = _source_link_supplement_display(target)
            ref = ET.SubElement(note, f"{{{NS}}}reference", {"osisRef": target})
            ref.text = display
            ref.tail = "; " if i < len(proposals) - 1 else "."
            candidate_hashes.append({
                "candidate_target_sha256":
                    hashlib.sha256(target.encode("utf-8")).hexdigest(),
                "candidate_derived_display_sha256":
                    hashlib.sha256(display.encode("utf-8")).hexdigest(),
            })
            total_targets += 1
        receipts.append({
            "source_first_key": first,
            "source_original_link_ordinal": ordinal,
            "original_source_literal_target_sha256":
                case["original_target_sha256"],
            "original_source_label_sha256": case["original_label_sha256"],
            "original_source_K_body_sha256":
                case["original_native_unit_sha256"],
            "proposed_context": context,
            "candidate_references": candidate_hashes,
        })

    if total_targets != manifest.get("proposed_derived_navigation_note_count"):
        raise ValueError("Proposed review-only destination count changed")
    output = ET.tostring(doc, encoding="utf-8", xml_declaration=True)
    restored = ET.fromstring(output)
    for ch in restored.iter():
        for note in list(ch):
            if (note.tag == f"{{{NS}}}note" and note.get("resp") ==
                    "BibleResourcesPrivateUnapprovedAdditionalLinkReview"):
                ch.remove(note)
    if ET.tostring(restored, encoding="utf-8") != original_bytes:
        raise ValueError("Additional editorial preview changed prior modern/source-notes document")
    return output, {
        "status": "PRIVATE_ADDITIONAL_SOURCE_LINK_REVIEW_NOT_EDITED_OR_RELEASED",
        "original_source_link_occurrences_provisionally_reviewed": len(receipts),
        "secondary_witness_proposed_navigation_targets": total_targets,
        "original_and_modern_edition_text_unchanged": True,
        "prior_private_note_and_link_structure_unchanged": True,
        "editorial_approval": False,
        "public_distribution": False,
        "original_source_K_ordinal_proposed_navigation_hashes": receipts,
    }


def build_private_primary_source_strict_quarantine(
        *, conservative_osis: bytes, manifest: dict,
        native: dict) -> tuple[bytes, dict]:
    """Build an *unreleased* exact-source-only alternative without deleting drafts.

    Exclude only documented CCEL-exclusive *modern leaf blocks* that have no
    authored equivalent in the published original K body. This is an isolated
    presentation candidate, not a source correction or publication decision.
    All original notes, K mappings and Scripture links are preserved.
    """
    from commentary_modern_draft_osis_preview import NS, _range

    if (manifest.get("status") !=
            "PRIVATE_PRIMARY_PUBLISHED_MHCC_0_1_1_ONLY_PREVIEW_NOT_RELEASE"
            or manifest.get("source_module") != "MHCC 0.1.1"
            or manifest.get("source_native_corpus_sha256") !=
            native.get("original_compiled_corpus_sha256")
            or any(manifest.get(field) is not False for field in (
                "source_original_changed", "modern_manuscripts_changed",
                "ccel_only_additions_redistribution_approved",
                "public_release_authorized"))):
        raise ValueError("Untrusted primary-source-only preview provenance")
    cases = manifest.get("cases")
    if (not isinstance(cases, list) or len(cases) != 2 or
            {row.get("chapter") for row in cases} != {"1Sam.25", "Ps.95"}):
        raise ValueError("Source-strict preview only supports two attested source gaps")
    root = ET.fromstring(conservative_osis)
    chapters = {node.get("osisID"): node for node in root.iter()
                if node.tag == f"{{{NS}}}chapter"}
    if set(chapters) != set(native.get("chapters", {})):
        raise ValueError("Primary-source strict preview chapter identity changed")

    def existing_links():
        return [(node.get("osisRef"), "".join(node.itertext()))
                for node in root.iter() if node.tag == f"{{{NS}}}reference"]
    originals = existing_links()
    original_sections = [(node.get("annotateRef"), node.get("annotateType"))
                         for node in root.iter()
                         if node.tag == f"{{{NS}}}div" and
                         node.get("annotateType") == "commentary"]
    receipts = []
    for case in cases:
        chapter = case["chapter"]
        first = case["original_source_first_K"]
        last = case["original_source_last_K"]
        originals_for_chapter = native["chapters"][chapter]["original_units"]
        indices = [i for i, unit in enumerate(originals_for_chapter)
                   if unit["first_key"] == first and unit["keys"][-1] == last
                   and unit["source_unit_sha256"] ==
                   case["original_source_K_raw_sha256"]]
        if len(indices) != 1:
            raise ValueError("Quarantined section is not owned by exact published source K")
        sections = chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(originals_for_chapter):
            raise ValueError("Source-strict modern chapter altered original K unit count")
        section = sections[indices[0]]
        if section.get("annotateRef") != _range(
                originals_for_chapter[indices[0]]["keys"]):
            raise ValueError("Source-strict modern original K linked span changed")
        children = list(section)
        subheadings = [(i, child) for i, child in enumerate(children)
                       if child.tag == f"{{{NS}}}title" and
                       child.get("type") == "sub"]
        if (len(subheadings) != 2 or
                subheadings[0][1].text != case["keep_original_source_matched_heading"]
                or subheadings[1][1].text != case["quarantined_ccel_only_heading"]):
            raise ValueError("CCEL-only leaf heading or segment order differs from review")
        index = subheadings[1][0]
        removed = 0
        kept_source_notes = 0
        for child in children[index:]:
            if child.tag == f"{{{NS}}}note" and (
                    child.get("resp") or "").startswith("BibleResources"):
                kept_source_notes += 1
                continue
            if any(node.tag == f"{{{NS}}}reference" for node in child.iter()):
                raise ValueError("Refuse to discard any Bible link while quarantining text")
            if child.tag != f"{{{NS}}}title":
                removed += 1
            section.remove(child)
        remaining = [node for node in section
                     if node.tag == f"{{{NS}}}title" and node.get("type") == "sub"]
        if removed < 1 or len(remaining) != 1 or (
                remaining[0].text != case["keep_original_source_matched_heading"]):
            raise ValueError("Quarantine removed authentic authorial text or no paragraphs")
        receipts.append({
            "chapter": chapter,
            "source_first_K": first,
            "source_last_K": last,
            "original_source_K_sha256": case["original_source_K_raw_sha256"],
            "quarantined_secondary_witness_blocks": 1,
            "quarantined_modern_reading_elements": removed,
            "unchanged_authentic_source_note_nodes": kept_source_notes,
        })
    if existing_links() != originals:
        raise ValueError("Source-strict preview lost or retargeted modern or original Bible links")
    if ([(node.get("annotateRef"), node.get("annotateType"))
         for node in root.iter()
         if node.tag == f"{{{NS}}}div" and node.get("annotateType") == "commentary"]
            != original_sections):
        raise ValueError("Source-strict preview altered K ownership or chapter topology")
    output = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)
    return output, {
        "status": "PRIVATE_PRIMARY_SOURCE_ONLY_TWO_WITNESS_BLOCKS_EXCLUDED_NOT_RELEASE",
        "source_native_corpus_sha256": manifest["source_native_corpus_sha256"],
        "original_K_body_groups_and_verse_aliases_unchanged": True,
        "original_and_authentic_derivative_scripture_links_unchanged": True,
        "published_source_or_accepted_modern_manuscripts_changed": False,
        "CCEL_only_modern_blocks_quarantined_in_alternative": len(receipts),
        "editorial_or_publication_approval": False,
        "cases": receipts,
    }


def prepare_private_source_strict_release_candidate(
        *, strict_osis: bytes, native: dict, ledger: dict,
        erroneous_links: dict, candidate: dict,
        strict_receipt: dict) -> tuple[bytes, dict]:
    """Prepare an *unshipped* distinct-ID SWORD work from exact-source draft.

    Suspected original digital/printed links remain visible as unlinked, marked
    original-reference index text. They may NEVER be silently re-targeted to
    secondary-witness guesses or propagated as clickable wrong destinations.
    """
    from commentary_modern_draft_osis_preview import NS

    corpus = native.get("original_compiled_corpus_sha256")
    if (candidate.get("status") !=
            "PRIVATE_SOURCE_STRICT_MODERN_SWORD_CANDIDATE_NOT_APPROVED"
            or candidate.get("candidate_sword_id") != "MHCCMODRC"
            or candidate.get("candidate_version") != "0.0.0"
            or candidate.get("source_module") != "MHCC 0.1.1"
            or candidate.get("selected_full_display_name") !=
                "Henry's Modern Concise Commentary"
            or candidate.get("selected_short_display_name") != "HMCC Modern"
            or candidate.get("candidate_sword_abbreviation") != "HMCCModern"
            or candidate.get("selected_names_approved_by_owner") is not True
            or candidate.get("final_public_sword_id_approved") is not False
            or candidate.get("original_native_corpus_sha256") != corpus
            or strict_receipt.get("status") !=
            "PRIVATE_PRIMARY_SOURCE_ONLY_TWO_WITNESS_BLOCKS_EXCLUDED_NOT_RELEASE"
            or strict_receipt.get("source_native_corpus_sha256") != corpus
            or strict_receipt.get("CCEL_only_modern_blocks_quarantined_in_alternative") != 2
            or erroneous_links.get("status") !=
            "ORIGINAL_DIGITAL_SOURCE_LINK_DISCREPANCIES_REVIEW_ONLY_NOT_APPLIED"
            or erroneous_links.get("original_corpus_sha256") != corpus
            or ledger.get("status") !=
            "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL"
            or any(candidate.get(flag) is not False for flag in (
                "source_original_edited", "modern_chapter_manuscripts_edited",
                "unapproved_link_retargeting_applied",
                "separately_edited_ccel_only_additions_included",
                "rights_and_redistribution_approved",
                "independent_editorial_signoff", "xiphos_gui_accepted",
                "andbible_gui_accepted", "publishing_authorized"))
            or any(erroneous_links.get(flag) is not False for flag in (
                "original_source_modified", "modern_chapter_prose_modified",
                "proposed_navigation_approved", "publication_authorized"))
            or ledger.get("publication_authorized") is not False):
        raise ValueError("Private candidate/primary source/rights status is not authenticated")
    if (candidate.get("expected_chapters") != 1189
            or candidate.get("expected_compiled_authored_groups") != 4049
            or candidate.get("expected_numbered_verse_keys") != 28792
            or candidate.get("expected_source_attested_book_introductions") != 56
            or candidate.get("source_note_digital_or_printed_wrong_targets_disabled") != 11
            or candidate.get("ccel_only_leaf_blocks_withheld") != 2
            or candidate.get("source_native_earlier_malformed_targets_excluded") != 4
            or candidate.get("source_native_spurious_markup_links_excluded") != 9
            or candidate.get("candidate_work_id_is_temporary") is not True
            or candidate.get("candidate_distribution") !=
            "PRIVATE_CI_TEMPORARY_NO_PUBLIC_ARTIFACT_NO_CATALOGUE"):
        raise ValueError("Private candidate release policy or structural ledger changed")
    cases = erroneous_links.get("cases")
    if (not isinstance(cases, list) or len(cases) != 11
            or any(c.get("approval") is not False for c in cases)):
        raise ValueError("Private candidate needs precisely 11 unapproved source links")
    by_identity = {
        (row["source_first_key"], row["source_reference_ordinal"]): row
        for row in ledger.get("pending", [])
    }
    if len(by_identity) != len(ledger.get("pending", [])):
        raise ValueError("Source original K reference ordinal collision")

    root = ET.fromstring(strict_osis)
    osis_texts = root.findall(f"./{{{NS}}}osisText")
    if len(osis_texts) != 1:
        raise ValueError("Private candidate must originate in one canonical OSIS work")
    osis = osis_texts[0]
    header = osis.find(f"{{{NS}}}header")
    work = header.find(f"{{{NS}}}work") if header is not None else None
    if (work is None or work.get("osisWork") != osis.get("osisIDWork")
            or not (osis.get("osisIDWork") or "").startswith("MHCC")):
        raise ValueError("Cannot bind a foreign source work to the private candidate")
    chap_nodes = {node.get("osisID"): node for node in root.iter()
                  if node.tag == f"{{{NS}}}chapter"}
    if len(chap_nodes) != 1189 or set(chap_nodes) != set(native.get("chapters", {})):
        raise ValueError("Private release candidate has wrong canonical chapter inventory")
    sections = {
        chapter: chap.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        for chapter, chap in chap_nodes.items()
    }
    if sum(map(len, sections.values())) != 4049:
        raise ValueError("Private SWORD candidate lost a source-authored section")
    chapter_text_before = {
        name: "".join(chap.itertext()) for name, chap in chap_nodes.items()
    }
    references_before = [r for r in root.iter() if r.tag == f"{{{NS}}}reference"]
    included_before = [(r.get("osisRef"), "".join(r.itertext()))
                       for r in references_before]

    removed = set()
    proof = []
    seen_keys = set()
    for case in cases:
        first = case.get("source_first_key")
        ordinal = case.get("source_reference_ordinal")
        key = (first, ordinal)
        source_row = by_identity.get(key)
        if (key in seen_keys or not isinstance(first, str)
                or type(ordinal) is not int or source_row is None):
            raise ValueError("Wrong source hyperlink not in signed original review queue")
        seen_keys.add(key)
        target = case.get("original_osisRef")
        label = case.get("original_link_label")
        if (not isinstance(target, str) or not isinstance(label, str)
                or hashlib.sha256(target.encode()).hexdigest() !=
                    case.get("original_target_sha256")
                or hashlib.sha256(label.encode()).hexdigest() !=
                    case.get("original_label_sha256")
                or source_row.get("original_osisRef_sha256") !=
                    case.get("original_target_sha256")
                or source_row.get("original_visible_label_sha256") !=
                    case.get("original_label_sha256")):
            raise ValueError("Source original hyperlink target/label SHA drift")
        chapter = first.rsplit(".", 1)[0]
        groups = native["chapters"][chapter]["original_units"]
        positions = [i for i, group in enumerate(groups)
                     if group["first_key"] == first and
                     group["source_unit_sha256"] ==
                     case.get("original_native_unit_sha256")]
        if len(positions) != 1 or len(groups) != len(sections[chapter]):
            raise ValueError("Private candidate K ownership or raw native SHA changed")
        section = sections[chapter][positions[0]]
        original_note = [child for child in section
                         if child.tag == f"{{{NS}}}note"
                         and child.get("resp") ==
                         "BibleResourcesPrivateSourceOnlyLinkSupplement"]
        if len(original_note) != 1:
            raise ValueError("Unreviewed bad source link was moved from its K note")
        expected_display = _source_link_supplement_display(target)
        matches = [r for r in original_note[0]
                   if r.tag == f"{{{NS}}}reference" and
                   r.get("osisRef") == target and
                   "".join(r.itertext()) == expected_display]
        if len(matches) != 1:
            raise ValueError("Source note target/display not uniquely present at its K")
        node = matches[0]
        if id(node) in removed:
            raise ValueError("Original wrong target was reused by a second ordinal")
        removed.add(id(node))
        node.tag = f"{{{NS}}}seg"
        node.attrib.clear()
        node.set("type", "x-original-link-target-quarantined")
        node.set("resp", "BibleResourcesOriginalLinkTargetUnapproved")
        proof.append({
            "source_first_K": first,
            "source_link_ordinal": ordinal,
            "published_original_K_sha256": case["original_native_unit_sha256"],
            "original_target_sha256": case["original_target_sha256"],
            "original_label_sha256": case["original_label_sha256"],
            "candidate_non_navigable_display_sha256":
                hashlib.sha256(expected_display.encode()).hexdigest(),
        })

    expected_refs = [(r.get("osisRef"), "".join(r.itertext()))
                     for r in references_before if id(r) not in removed]
    after_refs = [(r.get("osisRef"), "".join(r.itertext()))
                  for r in root.iter() if r.tag == f"{{{NS}}}reference"]
    if (len(removed) != 11 or len(included_before) - len(after_refs) != 11
            or after_refs != expected_refs
            or {name: "".join(node.itertext()) for name, node in chap_nodes.items()}
               != chapter_text_before):
        raise ValueError("Candidate quarantine changed prose or any unrelated reference")
    osis.set("osisIDWork", "MHCCMODRC")
    work.set("osisWork", "MHCCMODRC")
    identifiers = work.findall(f"{{{NS}}}identifier")
    titles = work.findall(f"{{{NS}}}title")
    descriptions = work.findall(f"{{{NS}}}description")
    if len(identifiers) != 1 or len(titles) != 1 or len(descriptions) != 1:
        raise ValueError("Private candidate source OSIS work metadata incomplete")
    identifiers[0].text = "MHCCMODRC"
    titles[0].text = candidate["selected_full_display_name"] + " (private proof)"
    descriptions[0].text = (
        "Private unpublished source-strict technical release candidate; "
        "original source-link errors disabled, editorial/rights/reader "
        "acceptance and public distribution NOT authorized.")
    serial = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(serial)
    return serial, {
        "status": "PRIVATE_MODERN_SWORD_PREFLIGHT_NOT_RELEASE",
        "candidate_sword_id": "MHCCMODRC",
        "candidate_full_display_name": candidate["selected_full_display_name"],
        "candidate_short_display_name": candidate["selected_short_display_name"],
        "candidate_sword_abbreviation": candidate["candidate_sword_abbreviation"],
        "published_original_corpus_sha256": corpus,
        "modern_canonical_chapters": len(chap_nodes),
        "native_K_and_I_only_authored_sections": sum(map(len, sections.values())),
        "disabled_suspect_original_link_occurrences": len(removed),
        "nonquarantined_literal_target_and_display_list_unchanged": True,
        "all_modern_visible_chapter_text_unchanged": True,
        "CCEL_only_modern_expositions_excluded": 2,
        "public_distribution": False,
        "editorial_approval": False,
        "rights_approval": False,
        "quarantined_source_K_link_identity_hashes": proof,
    }


def overlay_reviewed_private_links(*, base_osis: bytes, placements: dict,
                                    native: dict, identities: dict,
                                    dispositions: dict, repo_root: Path,
                                    reader: Path, module_directory: Path,
                                    module_id: str,
                                    auto_single_verse: bool = False,
                                    auto_ranges: bool = False,
                                    auto_outline_links: bool = False,
                                    auto_authentic_labels: bool = False,
                                    source_notes_output: Path | None = None,
                                    errata_review: dict | None = None,
                                    errata_proposals_output: Path | None = None,
                                    context_notes_output: Path | None = None,
                                    inline_source_index_output: Path | None = None,
                                    editorial_review_output: Path | None = None,
                                    compact_source_osis_output: Path | None = None,
                                    compact_source_notes_output: Path | None = None,
                                    heading_source_osis_output: Path | None = None,
                                    heading_source_notes_output: Path | None = None,
                                    implicit_verses_osis_output: Path | None = None,
                                    implicit_verses_notes_output: Path | None = None,
                                    outline_verse_osis_output: Path | None = None,
                                    outline_verse_notes_output: Path | None = None) -> tuple[bytes, dict]:
    """Authenticate and place an explicitly bounded set of source-backed links.

    Real original SWORD attributes stay in private memory/isolated new OSIS,
    never in logs or metadata-only CI artifacts. This is one technical batch;
    it does not assert the 1,204 original source links have been transferred.
    """
    from commentary_modern_draft_osis_preview import NS, _range
    if auto_ranges and not auto_single_verse:
        raise ValueError("Range mapping requires source-matched single-verse mode")
    if auto_outline_links and not auto_ranges:
        raise ValueError("Outline mapping requires original source range validation")
    if auto_authentic_labels and not auto_single_verse:
        raise ValueError("Original-label matching needs authenticated singleton source mode")
    if source_notes_output is not None and (not auto_single_verse
                                           or errata_review is None):
        raise ValueError("Source notes require full native inventory and errata exclusions")
    if errata_proposals_output is not None and source_notes_output is None:
        raise ValueError("Private errata proposals require separate source-note candidate")
    if context_notes_output is not None and source_notes_output is None:
        raise ValueError("Context placement requires separate source-note alternative")
    if inline_source_index_output is not None and source_notes_output is None:
        raise ValueError("Visible source reference index requires original source notes")
    if editorial_review_output is not None and source_notes_output is None:
        raise ValueError("Editorial review excerpts require pinned source and review ledger")
    if (compact_source_osis_output is None) != (compact_source_notes_output is None):
        raise ValueError("Compact source-linked OSIS and fallback notes must be built together")
    if compact_source_osis_output is not None and source_notes_output is None:
        raise ValueError("Compact source links require pinned original link ledger")
    if (heading_source_osis_output is None) != (heading_source_notes_output is None):
        raise ValueError("Source heading-links and remaining notes must travel together")
    if heading_source_osis_output is not None and compact_source_osis_output is None:
        raise ValueError("Heading source navigation requires compiled compact candidate")
    if (implicit_verses_osis_output is None) != (implicit_verses_notes_output is None):
        raise ValueError("Local source verse links and remainder notes must travel together")
    if implicit_verses_osis_output is not None and heading_source_osis_output is None:
        raise ValueError("Local source verse recovery requires prior heading range candidate")
    if (outline_verse_osis_output is None) != (outline_verse_notes_output is None):
        raise ValueError("First K source outline navigation and remaining notes must travel together")
    if outline_verse_osis_output is not None and implicit_verses_osis_output is None:
        raise ValueError("Original outline source links require local verse candidate")
    if (placements.get("status") !=
            "PRIVATE_REVIEWED_BOUNDED_LINK_PLACEMENT_NOT_FINAL_EDIT_OR_RELEASE"
            or placements.get("published_source_module") != "MHCC 0.1.1"
            or any(placements.get(k) is not False for k in
                ("source_original_changed", "modern_prose_modified",
                 "independent_semantic_and_link_review_approved",
                 "publication_authorized"))):
        raise ValueError("Link placement manifest may not declare approval")
    pin = placements.get("published_source_corpus_sha256")
    if (pin != native.get("original_compiled_corpus_sha256")
            or pin != identities.get("whole_native_source_sha256")
            or pin != "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"
            or native.get("source_prose_or_original_markup_exported") is not False
            or identities.get("status") != WholeCanonOriginalLinkIdentityReceipt.STATUS
            or identities.get("original_reference_elements_verified") != 1204):
        raise ValueError("Missing complete authenticated original native reference source")
    correction_receipt = validate_proposed_link_dispositions(
        manifest=dispositions, native=native, identities=identities,
        repository_root=repo_root)
    if (not correction_receipt["source_link_target_and_label_hashes_checked_in_original_order"]
            or correction_receipt["original_link_proposal_actions_reviewed"] != 17):
        raise ValueError("Existing proposed error corrections not source-attested")
    proposed = placements.get("placements")
    if not isinstance(proposed, list) or not 1 <= len(proposed) <= 40:
        raise ValueError("Private bounded link placement list missing")
    groups = {r["first_key"]: r for r in identities["source_link_groups"]}
    requested = set(groups) if auto_single_verse else set()
    seen = set()
    correction_by_key = {
        (case["source_first_key"], edit["source_link_ordinal"]):
        edit for case in dispositions["cases"]
        for edit in case["corrections"]
    }
    addition_by_key = {
        (case["source_first_key"], item["target"]): item
        for case in dispositions["cases"]
        for item in case.get("modern_witness_links", [])
    }
    counted = {"COPY_EXACT_AUTHENTIC_SOURCE": 0,
               "CORRECT_AUTHENTIC_WRONG_TARGET": 0,
               "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS": 0}
    for row in proposed:
        chapter = row.get("modern_chapter")
        first = row.get("source_first_key")
        action = row.get("action")
        dest = row.get("expected_modern_target")
        ordinal = row.get("original_link_ordinal")
        if (not isinstance(chapter, str) or not isinstance(first, str)
                or not first.startswith(chapter+".") or action not in counted
                or not isinstance(dest, str) or not _REF.fullmatch(dest)
                or not isinstance(row.get("modern_anchor"), str)
                or not isinstance(row.get("linked_display_text"), str)):
            raise ValueError("Malformed source-owned modern link placement")
        key = (first, ordinal, dest)
        if key in seen:
            raise ValueError("Duplicate modern link placement from original source")
        seen.add(key)
        units = native["chapters"].get(chapter, {}).get("original_units", [])
        source_unit = next((g for g in units if g["first_key"] == first), None)
        identity = groups.get(first)
        if (source_unit is None or identity is None
                or identity["source_raw_sha256"] != source_unit["source_unit_sha256"]):
            raise ValueError("Unattested original K group for modern link placement")
        if action == "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS":
            if "original_link_ordinal" in row:
                raise ValueError("Cannot invent an original linked-element ordinal")
            witness = addition_by_key.get((first, dest))
            if (witness is None or
                    witness.get("modern_text_marker") != row["modern_anchor"]):
                raise ValueError("Added link lacks actual independent source witness disposition")
        else:
            if type(ordinal) is not int or not 1 <= ordinal <= identity["reference_count"]:
                raise ValueError("Original link placement lacks exact source occurrence ordinal")
            correction = correction_by_key.get((first, ordinal))
            if action == "COPY_EXACT_AUTHENTIC_SOURCE" and correction is not None:
                raise ValueError("Never copy a known wrong/spurious original hyperlink")
            if action == "CORRECT_AUTHENTIC_WRONG_TARGET":
                if (correction is None or correction.get("disposition") !=
                        "RETARGET_VERIFIED_CONTINUATION_REFERENCE"
                        or correction.get("corrected_target") != dest):
                    raise ValueError("Proposed corrected target is not independently documented")
        requested.add(first)
        counted[action] += 1
    if not reader.is_file() or not module_directory.is_dir() or module_id != "MHCC":
        raise ValueError("Only isolated published MHCC original SWORD reader is supported")
    private_original = {}
    private_original_contexts = {}
    private_original_raw_K = {}
    private_table_ownership = {}
    private_title_ownership = {}
    env = os.environ.copy()
    env["SWORD_PATH"] = str(module_directory.resolve())
    def observe(kind: str, key: str, raw: bytes):
        if kind != "K" or key not in requested:
            return
        if key in private_original:
            raise ValueError("Original first-K raw source repeated")
        chapter = key.rsplit(".", 1)[0]
        original_unit = next(r for r in native["chapters"][chapter]["original_units"]
                             if r["first_key"] == key)
        identity = groups[key]
        if hashlib.sha256(raw).hexdigest() != original_unit["source_unit_sha256"]:
            raise ValueError("Original K body failed source-pinned SHA verification")
        refs = []
        node = ET.fromstring(b"<original>" + raw + b"</original>")
        for element in node.iter():
            if isinstance(element.tag, str) and element.tag.rsplit("}",1)[-1] == "reference":
                literal = element.attrib.get("osisRef")
                if not isinstance(literal, str) or not literal:
                    raise ValueError("Invalid original source-native hyperlink target")
                label = "".join(element.itertext())
                refs.append((literal, label))
        table_context=_original_reference_table_ownership(node)
        title_context=_original_reference_title_ownership(node)
        if (len(refs) != identity["reference_count"]
                or len(table_context)!=len(refs) or len(title_context)!=len(refs)):
            raise ValueError("Original link/authorial title-table ancestry count mismatch")
        for n, (literal, label) in enumerate(refs):
            if (hashlib.sha256(literal.encode("utf-8")).hexdigest() !=
                    identity["original_osisRef_sha256_in_document_order"][n]
                    or hashlib.sha256(label.encode("utf-8")).hexdigest() !=
                    identity["original_visible_link_label_sha256_in_document_order"][n]):
                raise ValueError("Original link identity or order differs from authenticated ledger")
        private_original[key] = refs
        if context_notes_output is not None:
            private_original_contexts[key] = _original_source_link_contexts(raw)
            private_original_raw_K[key] = raw
            if len(private_original_contexts[key]) != len(refs):
                raise ValueError("Original context/ref inventory mismatch")
        private_table_ownership[key] = table_context
        private_title_ownership[key] = title_context
    proc = subprocess.Popen([str(reader.resolve()), module_id], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("No private full-original source stream")
        source_report, *_ = parse_native_raw_corpus(proc.stdout, on_entry=observe)
        proc.stdout.close()
        if proc.wait(timeout=45) != 0:
            raise ValueError("Original native SWORD stream failed to complete")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    if (source_report["all_native_raw_entries_ordered_sha256"] != pin
            or set(private_original) != requested):
        raise ValueError("Unverified original whole corpus SHA or missing original source K")
    doc = ET.fromstring(base_osis)
    if any(x.tag == f"{{{NS}}}reference" for x in doc.iter()):
        raise ValueError("Source-link overlay accepts only the fully UNLINKED candidate")
    modern_chapters = {
        node.attrib["osisID"]: node for node in doc.iter()
        if node.tag == f"{{{NS}}}chapter"
    }
    if len(modern_chapters) != 1189:
        raise ValueError("Source-linked OSIS needs all 1189 modern chapters")
    original_visible = "".join(doc.itertext())
    inserted = []
    auto_counts = {"automatically_inserted":0,
                   "automatically_inserted_ranges":0,
                   "automatically_inserted_outline_links":0,
                   "automatically_inserted_source_labels":0}
    for row in proposed:
        chapter, first = row["modern_chapter"], row["source_first_key"]
        units = native["chapters"][chapter]["original_units"]
        nth = next(i for i, item in enumerate(units) if item["first_key"] == first)
        sections = modern_chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(units):
            raise ValueError("Modern OSIS original authorial section count drift")
        section = sections[nth]
        if section.attrib.get("annotateRef") != _range(units[nth]["keys"]):
            raise ValueError("Modern OSIS commentary verse scope differs from native source")
        ordinal = row.get("original_link_ordinal")
        action = row["action"]
        if action == "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS":
            actual_target = row["expected_modern_target"]
        else:
            original_literal = private_original[first][ordinal-1][0]
            original_canon = canonical_only_for_comparison(original_literal)
            if action == "COPY_EXACT_AUTHENTIC_SOURCE":
                if original_canon != row["expected_modern_target"]:
                    raise ValueError("Original link copy target differs from native literal")
                actual_target = original_literal
            else:
                correction = correction_by_key[(first, ordinal)]
                if original_canon != correction["original_target"]:
                    raise ValueError("Correction original link was not its attested literal")
                actual_target = row["expected_modern_target"]
        _wrap_exact_authored_modern_text(
            section, anchor=row["modern_anchor"],
            display=row["linked_display_text"],
            occurrence=row["display_occurrence"], target=actual_target)
        inserted.append({"chapter": chapter, "original_source_first_key": first,
                         "original_link_ordinal": ordinal,
                         "placement_action": action,
                         "derived_target_sha256": hashlib.sha256(
                            actual_target.encode("utf-8")).hexdigest()})
    if auto_single_verse:
        already={(row["source_first_key"],row["original_link_ordinal"])
                 for row in proposed if row.get("original_link_ordinal") is not None}
        automatic, skips = _auto_single_verse_placements(
            private_original=private_original, groups=groups,
            modern_chapters=modern_chapters, native=native,
            blocked=already, corrections=correction_by_key,
            include_ranges=auto_ranges,
            include_outline_links=auto_outline_links,
            include_authentic_labels=auto_authentic_labels)
        # The original raw source and its complete identity hashes are already
        # validated by observe(). Retain original literal osisRef unchanged.
        for row in automatic:
            first=row["source_first_key"]
            chapter=row["modern_chapter"]
            units=native["chapters"][chapter]["original_units"]
            nth=next(i for i,u in enumerate(units) if u["first_key"]==first)
            section=modern_chapters[chapter].findall(
                f"./{{{NS}}}div[@annotateType='commentary']")[nth]
            literal=private_original[first][row["original_link_ordinal"]-1][0]
            is_outline=(row["action"]==
                        "AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE")
            if row["action"]=="AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE" or is_outline:
                normalized="RANGE:"+(literal[6:] if literal.startswith("Bible:")
                                      else literal)
                if (_source_same_chapter_verse_range(literal) is None or
                        normalized!=row["expected_modern_target"]):
                    raise ValueError("Source range autolink failed exact original target")
            elif canonical_only_for_comparison(literal)!=row["expected_modern_target"]:
                raise ValueError("Autolink changed original authenticated destination")
            location=section
            if is_outline:
                source_label=private_original[first][row["original_link_ordinal"]-1][1]
                confirmed=_source_first_K_outline_row_evidence(
                    literal=literal,label=source_label,first_key=first,
                    native_chapter=native["chapters"][chapter],
                    modern_chapter=modern_chapters[chapter])
                if not (confirmed["source_first_K_owns_link"] and
                        confirmed["unique_modern_outline_row_matches_source_target"] and
                        confirmed["original_visible_label_explicitly_names_same_verse_span"]):
                    raise ValueError("Original chapter-outline link cannot be relocated safely")
                location=_find_exact_modern_original_outline_range_cell(
                    modern_chapters[chapter],literal)
                if location is None or "".join(location.itertext()).strip()!=row["modern_anchor"]:
                    raise ValueError("Original outline verse table cell changed after review")
            _wrap_exact_authored_modern_text(
                location, anchor=row["modern_anchor"],
                display=row["linked_display_text"],
                occurrence="last", target=literal)
            inserted.append({
                "chapter":chapter,
                "original_source_first_key":first,
                "original_link_ordinal":row["original_link_ordinal"],
                "placement_action":row["action"],
                "derived_target_sha256":hashlib.sha256(
                    literal.encode("utf-8")).hexdigest(),
            })
        auto_counts = {"automatically_inserted":len(automatic),
                       "automatically_inserted_source_labels":sum(
                           row["action"]=="AUTO_UNIQUE_AUTHENTIC_ORIGINAL_SINGLE_VERSE_LABEL"
                           for row in automatic),
                       "automatically_inserted_ranges":sum(
                           row["action"]=="AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE"
                           for row in automatic),
                       "automatically_inserted_outline_links":sum(
                           row["action"]=="AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE"
                           for row in automatic),
                       **skips}
        proposed = list(proposed)+automatic
    if "".join(doc.itertext()) != original_visible:
        raise ValueError("Modern commentary wording changed while adding source links")
    # Diagnose authorial source outline-table references separately. A text
    # range in the original chapter outline must NOT be treated as a
    # passage cited by Henry inside modern explanatory paragraphs.
    context_count={"all_original_references":0,
                   "source_links_in_original_tables":0,
                   "source_links_outside_original_tables":0,
                   "source_links_in_original_titles":0,
                   "source_links_outside_original_titles":0,
                   "source_full_verse_ranges_inside_original_titles":0,
                   "source_full_verse_ranges_outside_original_titles":0,
                   "unplaced_full_verse_ranges_inside_original_titles":0,
                   "unplaced_full_verse_ranges_outside_original_titles":0,
                   "source_full_verse_ranges_inside_original_tables":0,
                   "source_full_verse_ranges_outside_original_tables":0,
                   "unplaced_full_verse_ranges_inside_original_tables":0,
                   "unplaced_full_verse_ranges_outside_original_tables":0}
    placed={(row["original_source_first_key"],row.get("original_link_ordinal"))
            for row in inserted if row.get("original_link_ordinal") is not None}
    for first,links in private_original.items():
        flags=private_table_ownership[first]
        title_flags=private_title_ownership[first]
        for i,((literal,_),in_table,in_title) in enumerate(
                zip(links,flags,title_flags),1):
            context_count["all_original_references"]+=1
            context_count["source_links_in_original_tables" if in_table else
                          "source_links_outside_original_tables"]+=1
            context_count["source_links_in_original_titles" if in_title else
                          "source_links_outside_original_titles"]+=1
            if _unrecognized_original_ref_class(literal)=="full_verse_range":
                context_count["source_full_verse_ranges_inside_original_titles" if in_title
                              else "source_full_verse_ranges_outside_original_titles"]+=1
                if (first,i) not in placed:
                    context_count["unplaced_full_verse_ranges_inside_original_titles" if in_title
                                  else "unplaced_full_verse_ranges_outside_original_titles"]+=1
                context_count["source_full_verse_ranges_inside_original_tables" if in_table
                              else "source_full_verse_ranges_outside_original_tables"]+=1
                if (first,i) not in placed:
                    context_count["unplaced_full_verse_ranges_inside_original_tables" if in_table
                                  else "unplaced_full_verse_ranges_outside_original_tables"]+=1
    if auto_single_verse and context_count["all_original_references"]!=1204:
        raise ValueError("Source table ancestry audit did not cover all source K hyperlinks")
    embedded = [x for x in doc.iter() if x.tag == f"{{{NS}}}reference"]
    if len(embedded) != len(proposed):
        raise ValueError("Wrong source-anchored link count after modern OSIS insertion")
    # Capture exact derived order after all insertions. Modern English placement
    # may legitimately differ from source-XML order, and one K body may contain
    # multiple independent links (including the duplicated 1 Cor. 5:7 source).
    # No literal original source targets or linked words enter this receipt.
    modern_groups = []
    outline_action="AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE"
    K_placements=[row for row in proposed if row["action"]!=outline_action]
    I_placements=[row for row in proposed if row["action"]==outline_action]
    linked_keys={row["source_first_key"] for row in K_placements}
    for first in sorted(linked_keys):
        ch = first.rsplit(".",1)[0]
        units = native["chapters"][ch]["original_units"]
        nth = next(i for i,u in enumerate(units) if u["first_key"]==first)
        scope = modern_chapters[ch].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")[nth]
        nodes = [v for v in scope.iter()
                 if v.tag == f"{{{NS}}}reference"]
        targets = [v.attrib.get("osisRef") for v in nodes]
        labels = ["".join(v.itertext()) for v in nodes]
        expected_count = sum(row["source_first_key"] == first for row in K_placements)
        if (len(targets)!=expected_count or
                any(not isinstance(t,str) or not t for t in targets)
                or any(not label for label in labels)):
            raise ValueError("Grouped modern source-linked occurrence count changed")
        modern_groups.append({
            "original_source_first_key":first,
            "source_linked_modern_osisRef_hashes_in_actual_document_order":[
                hashlib.sha256(t.encode("utf-8")).hexdigest() for t in targets],
            "source_linked_modern_label_hashes_in_actual_document_order":[
                hashlib.sha256(label.encode("utf-8")).hexdigest() for label in labels],
            "modern_link_occurrences":len(targets)
        })
    if sum(r["modern_link_occurrences"] for r in modern_groups) != len(K_placements):
        raise ValueError("Modern K-owned linked group count differs from source review")
    intro_groups=[]
    outline_chapters={row["modern_chapter"] for row in I_placements}
    for chapter in sorted(outline_chapters):
        root=modern_chapters[chapter]
        sources=[v for v in root.findall(f"./{{{NS}}}div[@type='introduction']")
                 if len(v.findall(f"./{{{NS}}}title"))==1 and
                 v.find(f"./{{{NS}}}title").text=="Original chapter outline"]
        if len(sources)!=1:
            raise ValueError("Source-owned original chapter outline introduction is ambiguous")
        nodes=[v for v in sources[0].iter() if v.tag==f"{{{NS}}}reference"]
        expected_count=sum(row["modern_chapter"]==chapter for row in I_placements)
        if (len(nodes)!=expected_count or
                any(not v.get("osisRef") or not "".join(v.itertext()) for v in nodes)):
            raise ValueError("Original chapter outline link count or placement changed")
        intro_groups.append({
            "modern_chapter":chapter,
            "modern_intro_osisRef_hashes_in_actual_document_order":[
                hashlib.sha256(v.get("osisRef").encode("utf-8")).hexdigest()
                for v in nodes],
            "modern_intro_label_hashes_in_actual_document_order":[
                hashlib.sha256("".join(v.itertext()).encode("utf-8")).hexdigest()
                for v in nodes],
            "modern_link_occurrences":len(nodes),
            "source_ownership":"ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RELOCATED_TO_MODERN_CHAPTER_I",
        })
    if (sum(r["modern_link_occurrences"] for r in modern_groups)+
            sum(r["modern_link_occurrences"] for r in intro_groups)!=len(proposed)):
        raise ValueError("Modern K and chapter-I source-link counts differ from original")
    source_link_ledger=(
        _unplaced_original_link_review_ledger(
            original=private_original,
            insertions=inserted,
            corrections=correction_by_key,
            source_table_ownership=private_table_ownership,
            source_title_ownership=private_title_ownership,
            modern_chapters=modern_chapters,
            native=native)
        if auto_single_verse else None)
    output = ET.tostring(doc, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)
    if editorial_review_output is not None:
        # Deliberate ephemeral, bounded, human-readable private editorial
        # packet; NEVER included in the metadata-only audit report, logs, or
        # committed prose. No original raw K bodies or markup are exported.
        if not auto_single_verse or source_link_ledger is None or errata_review is None:
            raise ValueError("Source-checked editorial review ledger required")
        blocked_errata = {(c["source_first_key"],c["original_reference_ordinal"])
                          for c in errata_review["cases"]}
        rows=[]
        for item in source_link_ledger["pending"]:
            first,ord_ = item["source_first_key"],item["source_reference_ordinal"]
            if (first,ord_) in blocked_errata:
                continue
            refs=private_original[first]
            contexts=private_original_contexts.get(first)
            if contexts is None or len(contexts)!=len(refs):
                raise ValueError("Missing original contextual source witnesses")
            target,label=refs[ord_-1]
            chapter=first.rsplit(".",1)[0]
            units=native["chapters"][chapter]["original_units"]
            index=next(i for i,x in enumerate(units) if x["first_key"]==first)
            sec=modern_chapters[chapter].findall(
                f"./{{{NS}}}div[@annotateType='commentary']")[index]
            # Modern prose is the already-public branch manuscript, not the
            # historical raw original source. Limit it to the owning K group.
            modern_paragraphs=[
                "".join(p.itertext()) for p in sec.findall(f"{{{NS}}}p")
            ]
            rows.append({
                "source_first_key":first,
                "source_reference_ordinal":ord_,
                "original_literal_osisRef":target,
                "original_printed_link_label":label,
                "original_text_before_link":contexts[ord_-1][0],
                "original_text_after_link":contexts[ord_-1][1],
                "modern_K_paragraphs":modern_paragraphs,
                "source_literal_target_sha256":item["original_osisRef_sha256"],
                "original_visible_label_sha256":item["original_visible_label_sha256"],
                "disposition":"HUMAN_REVIEW_REQUIRED_NOT_SOURCE_LINK_EDIT",
            })
        if len(rows)!=len(source_link_ledger["pending"])-len(blocked_errata):
            raise ValueError("Unplaced original source reference review packet incomplete")
        editorial_review_output.parent.mkdir(parents=True,exist_ok=True)
        editorial_review_output.write_text(json.dumps({
            "status":"EPHEMERAL_EXCERPTS_PRIVATE_EDITORIAL_REVIEW_ONLY",
            "source_pinned_corpus_sha256":pin,
            "original_full_K_prose_or_markup_exported":False,
            "original_source_changed":False,
            "original_link_placement_approved":False,
            "citation_count":len(rows),
            "references":rows,
        },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    outline_verse_receipt = None
    outline_notes_receipt = None
    implicit_verse_receipt = None
    implicit_verse_notes_receipt = None
    heading_receipt = None
    heading_notes_receipt = None
    compact_receipt = None
    compact_notes_receipt = None
    notes_receipt = None
    context_receipt = None
    inline_source_index_receipt = None
    errata_preview_receipt = None
    if source_notes_output is not None:
        if source_link_ledger is None:
            raise ValueError("Source note preview requires full original link ledger")
        validate_pending_source_reference_errata(
            manifest=errata_review, ledger=source_link_ledger, native=native)
        notes_osis, notes_receipt = build_private_source_reference_supplement(
            linked_osis=output, ledger=source_link_ledger,
            original=private_original, native=native, errata=errata_review)
        source_notes_output.parent.mkdir(parents=True,exist_ok=True)
        source_notes_output.write_bytes(notes_osis)
        if compact_source_osis_output is not None:
            compact_osis,compact_ledger,compact_receipt=build_private_compact_original_crossrefs(
                linked_osis=output,ledger=source_link_ledger,
                original=private_original,native=native,errata=errata_review)
            compact_notes_osis,compact_notes_receipt=build_private_source_reference_supplement(
                linked_osis=compact_osis,ledger=compact_ledger,
                original=private_original,native=native,errata=errata_review)
            compact_source_osis_output.parent.mkdir(parents=True,exist_ok=True)
            compact_source_notes_output.parent.mkdir(parents=True,exist_ok=True)
            compact_source_osis_output.write_bytes(compact_osis)
            compact_source_notes_output.write_bytes(compact_notes_osis)
            if heading_source_osis_output is not None:
                heading_osis,heading_ledger,heading_receipt=(
                    build_private_owned_K_heading_range_links(
                        compact_osis=compact_osis,ledger=compact_ledger,
                        original=private_original,native=native,
                        errata=errata_review))
                heading_notes_osis,heading_notes_receipt=(
                    build_private_source_reference_supplement(
                        linked_osis=heading_osis,ledger=heading_ledger,
                        original=private_original,native=native,
                        errata=errata_review))
                heading_source_osis_output.parent.mkdir(parents=True,exist_ok=True)
                heading_source_notes_output.parent.mkdir(parents=True,exist_ok=True)
                heading_source_osis_output.write_bytes(heading_osis)
                heading_source_notes_output.write_bytes(heading_notes_osis)
                if implicit_verses_osis_output is not None:
                    implicit_osis,implicit_ledger,implicit_verse_receipt=(
                        build_private_same_chapter_verse_mentions(
                            source_osis=heading_osis,ledger=heading_ledger,
                            original=private_original,native=native,
                            errata=errata_review))
                    implicit_note_osis,implicit_verse_notes_receipt=(
                        build_private_source_reference_supplement(
                            linked_osis=implicit_osis,ledger=implicit_ledger,
                            original=private_original,native=native,
                            errata=errata_review))
                    implicit_verses_osis_output.parent.mkdir(parents=True,exist_ok=True)
                    implicit_verses_notes_output.parent.mkdir(parents=True,exist_ok=True)
                    implicit_verses_osis_output.write_bytes(implicit_osis)
                    implicit_verses_notes_output.write_bytes(implicit_note_osis)
                    if outline_verse_osis_output is not None:
                        outline_osis,outline_ledger,outline_verse_receipt=(
                            build_private_first_K_outline_verse_tokens(
                                source_osis=implicit_osis,ledger=implicit_ledger,
                                original=private_original,native=native,
                                errata=errata_review))
                        outline_notes_osis,outline_notes_receipt=(
                            build_private_source_reference_supplement(
                                linked_osis=outline_osis,ledger=outline_ledger,
                                original=private_original,native=native,
                                errata=errata_review))
                        outline_verse_osis_output.parent.mkdir(parents=True,exist_ok=True)
                        outline_verse_notes_output.parent.mkdir(parents=True,exist_ok=True)
                        outline_verse_osis_output.write_bytes(outline_osis)
                        outline_verse_notes_output.write_bytes(outline_notes_osis)
        if inline_source_index_output is not None:
            inlined,index_receipt=build_private_inline_original_reference_index(
                source_note_osis=notes_osis,source_receipt=notes_receipt,
                native=native)
            inline_source_index_output.parent.mkdir(parents=True,exist_ok=True)
            inline_source_index_output.write_bytes(inlined)
            inline_source_index_receipt=index_receipt
        if context_notes_output is not None:
            # Build the extra ordered alignment only inside the isolated,
            # source-hash-verified native reader. No original prose is exported.
            ordered_anchors={}
            notes_doc=ET.fromstring(notes_osis)
            note_chapters={c.get("osisID"):c for c in notes_doc.iter()
                           if c.tag==f"{{{NS}}}chapter"}
            for first,source_raw in private_original_raw_K.items():
                chapter=first.rsplit(".",1)[0]
                original_units=native["chapters"][chapter]["original_units"]
                nth=next(i for i,u in enumerate(original_units)
                         if u["first_key"]==first)
                sections=note_chapters[chapter].findall(
                    f"./{{{NS}}}div[@annotateType='commentary']")
                ordered_anchors[first]=_source_owned_ordered_alignment(
                    source_raw,sections[nth])
                if len(ordered_anchors[first]["original_link_offsets"]) != len(
                        private_original[first]):
                    raise ValueError("Full original link alignment ordinal drift")
            context_osis, context_receipt = build_private_contextual_source_note_preview(
                source_note_osis=notes_osis, ledger=source_link_ledger,
                native=native, original_contexts=private_original_contexts,
                errata=errata_review,original_ordered_anchors=ordered_anchors)
            context_notes_output.parent.mkdir(parents=True,exist_ok=True)
            context_notes_output.write_bytes(context_osis)
        if errata_proposals_output is not None:
            proposals_osis, errata_preview_receipt = (
                build_unapproved_source_errata_notes_preview(
                    source_note_osis=notes_osis, ledger=source_link_ledger,
                    native=native, errata=errata_review))
            errata_proposals_output.parent.mkdir(parents=True,exist_ok=True)
            errata_proposals_output.write_bytes(proposals_osis)
    return output, {
        "status":"PRIVATE_REVIEWED_LINKED_FULL_CANON_OSIS_CANDIDATE_NOT_RELEASED",
        "full_original_native_corpus_sha256":pin,
        "modern_chapters_preserved":1189,
        "source_pinned_original_K_bodies_revisited":len(requested),
        "source_K_groups_with_links_inserted":len(linked_keys),
        "modern_chapter_I_outline_groups_with_links":len(outline_chapters),
        "modern_original_outline_links_inserted":len(I_placements),
        "modern_inline_links_inserted":len(embedded),
        "automatic_source_matched_references":auto_counts,
        "source_original_hyperlink_table_ownership_census":context_count,
        "actual_original_links_copied_without_correction":counted[
            "COPY_EXACT_AUTHENTIC_SOURCE"],
        "documented_wrong_original_links_retargeted":counted[
            "CORRECT_AUTHENTIC_WRONG_TARGET"],
        "source_witness_authored_missing_original_link_added":counted[
            "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS"],
        "source_prose_modified":False,
        "modern_visible_prose_modified":False,
        "original_source_link_identity_hashes_and_order_verified":True,
        "modern_linked_osis_sha256":hashlib.sha256(output).hexdigest(),
        "published_source_1204_links_fully_transferred":False,
        "remaining_source_links_require_individual_placement_review":True,
        "source_original_link_review_ledger":source_link_ledger,
        "private_source_note_alternative":notes_receipt,
        "private_contextual_note_relocation_preview":context_receipt,
        "private_visible_source_reference_index_preview":inline_source_index_receipt,
        "private_exact_compact_reference_recovery":compact_receipt,
        "private_compact_remaining_source_notes":compact_notes_receipt,
        "private_source_owned_heading_range_recovery":heading_receipt,
        "private_heading_range_remaining_source_notes":heading_notes_receipt,
        "private_implicit_original_K_verse_mentions":implicit_verse_receipt,
        "private_implicit_verse_remaining_source_notes":implicit_verse_notes_receipt,
        "private_first_K_outline_verse_navigation":outline_verse_receipt,
        "private_first_K_outline_verse_remaining_notes":outline_notes_receipt,
        "private_unapproved_errata_navigation_preview":errata_preview_receipt,
        "modern_SWORD_readback_verified":False,
        "independent_editorial_semantic_signoff":False,
        "publication_authorized":False,
        "linked_source_K_groups_with_exact_derived_target_order":modern_groups,
        "linked_modern_chapter_I_outline_groups_with_exact_derived_order":intro_groups,
        "insertions":inserted,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-reader",required=True,type=Path)
    p.add_argument("--module-directory",required=True,type=Path)
    p.add_argument("--module-id",required=True)
    p.add_argument("--source-map",type=Path)
    p.add_argument("--expected-references",type=Path)
    p.add_argument("--modern-candidate",type=Path)
    p.add_argument("--whole-native-receipt",type=Path)
    p.add_argument("--disposition-manifest",type=Path)
    p.add_argument("--original-link-identity-report",type=Path)
    p.add_argument("--native-receipt",type=Path)
    p.add_argument("--repository-root",type=Path)
    p.add_argument("--base-unlinked-osis",type=Path)
    p.add_argument("--reviewed-link-placement-manifest",type=Path)
    p.add_argument("--auto-source-matched-single-verses",action="store_true")
    p.add_argument("--auto-source-matched-same-chapter-ranges",action="store_true")
    p.add_argument("--auto-original-first-K-outline-links",action="store_true")
    p.add_argument("--auto-authenticated-original-printed-single-verses",action="store_true")
    p.add_argument("--source-notes-osis",type=Path)
    p.add_argument("--context-source-notes-osis",type=Path)
    p.add_argument("--visible-source-reference-index-osis",type=Path)
    p.add_argument("--ephemeral-editorial-review-json",type=Path)
    p.add_argument("--compact-source-linked-osis",type=Path)
    p.add_argument("--compact-source-notes-osis",type=Path)
    p.add_argument("--source-K-heading-range-linked-osis",type=Path)
    p.add_argument("--source-K-heading-range-notes-osis",type=Path)
    p.add_argument("--same-K-implicit-verses-osis",type=Path)
    p.add_argument("--same-K-implicit-verse-notes-osis",type=Path)
    p.add_argument("--source-first-K-outline-verse-osis",type=Path)
    p.add_argument("--source-first-K-outline-verse-notes-osis",type=Path)
    p.add_argument("--source-notes-errata-manifest",type=Path)
    p.add_argument("--source-errata-proposals-osis",type=Path)
    p.add_argument("--linked-osis",type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    if ((a.source_notes_osis is None) !=
            (a.source_notes_errata_manifest is None)):
        p.error("Private source notes and original errata manifest must be supplied together")
    if a.source_notes_osis is not None and a.reviewed_link_placement_manifest is None:
        p.error("Private source notes need original full-canon linked preview")
    if a.source_errata_proposals_osis is not None and a.source_notes_osis is None:
        p.error("Private source errata proposals require original source notes")
    if a.context_source_notes_osis is not None and a.source_notes_osis is None:
        p.error("Private context relocation needs the source-note alternative")
    if a.visible_source_reference_index_osis is not None and a.source_notes_osis is None:
        p.error("Visible inline index needs original source note alternative")
    if a.ephemeral_editorial_review_json is not None and a.source_notes_osis is None:
        p.error("Review excerpts require original source notes and pinned inventory")
    if not a.native_reader.is_file() or not a.module_directory.is_dir():
        p.error("Trusted real native reader and installed source module directory required")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}",a.module_id):
        p.error("Unexpected SWORD module ID")
    if a.reviewed_link_placement_manifest is not None:
        if (any(x is not None for x in (
                a.whole_native_receipt, a.source_map, a.expected_references,
                a.modern_candidate)) or any(x is None for x in (
                a.base_unlinked_osis, a.linked_osis, a.disposition_manifest,
                a.native_receipt, a.original_link_identity_report,
                a.repository_root))):
            p.error("Full-canon linked OSIS needs authentic source, identity, "
                    "documented corrections and private source reader")
        osis, result = overlay_reviewed_private_links(
            base_osis=a.base_unlinked_osis.read_bytes(),
            placements=json.loads(a.reviewed_link_placement_manifest.read_text(
                encoding="utf-8")),
            native=json.loads(a.native_receipt.read_text(encoding="utf-8")),
            identities=json.loads(a.original_link_identity_report.read_text(
                encoding="utf-8")),
            dispositions=json.loads(a.disposition_manifest.read_text(
                encoding="utf-8")),
            repo_root=a.repository_root, reader=a.native_reader,
            module_directory=a.module_directory, module_id=a.module_id,
            auto_single_verse=a.auto_source_matched_single_verses,
            auto_ranges=a.auto_source_matched_same_chapter_ranges,
            auto_outline_links=a.auto_original_first_K_outline_links,
            auto_authentic_labels=a.auto_authenticated_original_printed_single_verses,
            source_notes_output=a.source_notes_osis,
            errata_review=(json.loads(a.source_notes_errata_manifest.read_text(
                encoding="utf-8")) if a.source_notes_errata_manifest is not None
                else None),
            errata_proposals_output=a.source_errata_proposals_osis,
            context_notes_output=a.context_source_notes_osis,
            inline_source_index_output=a.visible_source_reference_index_osis,
            editorial_review_output=a.ephemeral_editorial_review_json,
            compact_source_osis_output=a.compact_source_linked_osis,
            compact_source_notes_output=a.compact_source_notes_osis,
            heading_source_osis_output=a.source_K_heading_range_linked_osis,
            heading_source_notes_output=a.source_K_heading_range_notes_osis,
            implicit_verses_osis_output=a.same_K_implicit_verses_osis,
            implicit_verses_notes_output=a.same_K_implicit_verse_notes_osis,
            outline_verse_osis_output=a.source_first_K_outline_verse_osis,
            outline_verse_notes_output=a.source_first_K_outline_verse_notes_osis)
        a.linked_osis.parent.mkdir(parents=True,exist_ok=True)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.linked_osis.write_bytes(osis)
        a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
        print("BOUNDED SOURCE-LINKED MODERN MHCC OSIS PASS: " +
              str(result["modern_inline_links_inserted"]) +
              " source-verified inline links (" +
              str(result["automatic_source_matched_references"]["automatically_inserted"]) +
              " exact matches, including " +
              str(result["modern_original_outline_links_inserted"]) +
              " original first-K chapter outline links) across all 1189 chapters; " +
              "unmatched original hyperlinks still need editorial placement; NO release")
        return 0
    if ((a.auto_source_matched_single_verses or
         a.auto_source_matched_same_chapter_ranges or
         a.auto_original_first_K_outline_links or
         a.auto_authenticated_original_printed_single_verses) and
            a.reviewed_link_placement_manifest is None):
        p.error("Automatic source-linked citation lookup needs reviewed base manifests")
    if any(x is not None for x in (
            a.base_unlinked_osis, a.linked_osis)):
        p.error("Full-canon OSIS arguments require reviewed placement manifest")
    if a.disposition_manifest is not None:
        if (any(x is not None for x in (a.whole_native_receipt,
                                        a.source_map,
                                        a.expected_references,
                                        a.modern_candidate))
                or any(x is None for x in (
                    a.original_link_identity_report, a.native_receipt,
                    a.repository_root))):
            p.error("Correction disposition mode requires separate original receipts and root")
        result = validate_proposed_link_dispositions(
            manifest=json.loads(a.disposition_manifest.read_text(encoding="utf-8")),
            native=json.loads(a.native_receipt.read_text(encoding="utf-8")),
            identities=json.loads(a.original_link_identity_report.read_text(encoding="utf-8")),
            repository_root=a.repository_root)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("MHCC MODERN PROPOSED SOURCE LINK CORRECTIONS VERIFIED: original=" +
              str(result["reviewed_original_hyperlink_elements_in_groups"]) +
              " omitted=" + str(result["source_links_proposed_to_omit"]) +
              " retarget=" + str(result["source_links_proposed_to_retarget"]) +
              " added=" + str(result["secondary_witness_links_proposed_to_add"]) +
              "; no derivative link compilation or editorial publication approval")
        return 0
    if a.whole_native_receipt is not None:
        if any(x is not None for x in
               (a.source_map, a.expected_references, a.modern_candidate)):
            p.error("Whole-canon original-only mode cannot claim modern marker parity")
        result = run_whole_native_link_identity(
            reader=a.native_reader, root=a.module_directory,
            module_id=a.module_id, native_receipt=a.whole_native_receipt)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("SOURCE-NATIVE COMPLETE ORIGINAL LINK IDENTITY PASS: groups=" +
              str(result["original_unique_K_bodies_verified"]) +
              ", native links=" + str(result["original_reference_elements_verified"]) +
              "; destination and label hashes only; zero modern link approval")
        return 0
    if any(x is None for x in
           (a.source_map, a.expected_references, a.modern_candidate)):
        p.error("Pilot mode requires --source-map, --expected-references and --modern-candidate")
    source=json.loads(a.source_map.read_text(encoding="utf-8"))
    expectation=json.loads(a.expected_references.read_text(encoding="utf-8"))
    gate=SourceReferenceGate(source_map=source,expected_refs=expectation,
                             candidate=a.modern_candidate.read_text(encoding="utf-8"))
    env=os.environ.copy()
    env["SWORD_PATH"]=str(a.module_directory.resolve())
    proc=subprocess.Popen([str(a.native_reader.resolve()),a.module_id],
                           env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Missing native source stream")
        summary,*_=parse_native_raw_corpus(proc.stdout,on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=25)!=0:
            raise ValueError("Native stock-SWORD reader did not complete successfully")
        report=gate.report(summary)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("SOURCE-NATIVE REFERENCE IDENTITY PASS: "+
              str(report["source_unique_units_checked"])+" source units; "+
              str(report["original_reference_links_checked"])+" links; "+
              "raw labels/targets kept private; no derivative approval")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


if __name__=="__main__":
    raise SystemExit(main())
