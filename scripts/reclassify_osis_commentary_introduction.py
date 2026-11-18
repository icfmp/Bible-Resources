#!/usr/bin/env python3
"""Private, byte-local OSIS repair for a source-authored chapter introduction.

Only move existing XML boundary tokens and remove a redundant, misleading
verse-milestone pair. All original prose, notes, cross-references, title text,
punctuation and other elements are byte-preserved. No module publication.
This generic source-layout operation does NOT insert invented Bible verses.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import zip_longest
from pathlib import Path
from xml.parsers import expat
import json
import re

from clean_source_osis import _tree, _xml_tag_end, _local


class IntroRepairError(ValueError):
    pass


def repair_private_bytes(raw: bytes, plan: dict) -> tuple[bytes, dict]:
    if (not isinstance(raw, bytes) or not 100 <= len(raw) <= 128 * 1024 * 1024
            or not isinstance(plan, dict)
            or plan.get("schema_version") != 1
            or plan.get("status") != "PRIVATE_REVIEWED_CHAPTER_INTRO_RECLASSIFICATION"
            or plan.get("source_sha256") != sha256(raw).hexdigest()
            or plan.get("source_text_edit_approved") is not False
            or plan.get("chapter_introduction_remapping_approved") is not True):
        raise IntroRepairError("Unpinned or unreviewed chapter-introduction source")

    old = plan.get("old_intro_source_sid")
    following = plan.get("following_commentary_source_sid")
    m = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)", old or "")
    n = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)-([1-9][0-9]*)",
                     following or "")
    if (not m or not n or m.group(1, 2, 3) != n.group(1, 2, 3)
            or int(n.group(4)) <= int(n.group(3))):
        raise IntroRepairError("Unrelated or malformed authored verse sections")
    for field in ("old_intro_opening_line", "old_intro_closing_line",
                  "existing_introduction_div_line", "following_section_opening_line"):
        if type(plan.get(field)) is not int or not 1 <= plan[field] <= 1000000:
            raise IntroRepairError("Missing exact authoring source line witness")

    tree = _tree(raw)
    def find(name, attr, value):
        nodes = [node for node in tree.iter()
                 if isinstance(node.tag, str) and _local(node) == name
                 and node.get(attr) == value]
        if len(nodes) != 1:
            raise IntroRepairError("Original source boundary is not unique")
        return nodes[0]

    begin = find("verse", "sID", old)
    close = find("verse", "eID", old)
    next_open = find("verse", "sID", following)
    next_close = find("verse", "eID", following)
    if (begin.sourceline != plan["old_intro_opening_line"]
            or close.sourceline != plan["old_intro_closing_line"]
            or next_open.sourceline != plan["following_section_opening_line"]
            or begin.get("osisID") != old
            or begin.get("n") != m.group(3)
            or begin.get("eID") is not None
            or close.get("sID") is not None
            or any(len(node) for node in (begin, close, next_open))):
        raise IntroRepairError("Original milestone identity does not match reviewed plan")

    intro_p = close.getparent()
    intro_div = intro_p.getparent()
    leading_p = begin.getparent()
    book = leading_p.getparent()
    if book is None:
        raise IntroRepairError("Unattached source intro")
    book_children=list(book)
    if leading_p not in book_children or intro_div not in book_children:
        raise IntroRepairError("Intro paragraph and division have different owners")
    first=book_children.index(leading_p)
    last=book_children.index(intro_div)
    between=book_children[first+1:last]
    # Source may contain several consecutive introductory paragraphs before
    # its existing div introduction. None may contain an unrelated verse.
    if (last <= first or any(
            not isinstance(n.tag,str) or _local(n)!="p"
            or any(_local(e)=="verse" for e in n.iter()
                   if isinstance(e.tag,str))
            for n in between)):
        raise IntroRepairError("Nonintroductory content divides the original preface")
    if (not all(isinstance(node.tag, str) for node in
                (intro_p, intro_div, leading_p, book))
            or _local(leading_p) != "p"
            or _local(intro_p) != "p"
            or intro_p.get("subType") != "x-introduction"
            or _local(intro_div) != "div"
            or intro_div.get("type") != "introduction"
            or intro_div.sourceline != plan["existing_introduction_div_line"]
            or intro_div.getparent() is not book
            or _local(book) != "div"
            or book.get("type") != "book"
            or book.get("osisID") != m.group(1)
            or len(intro_div) != 1
            or intro_div[0] is not intro_p
            or not len(intro_p)
            or list(intro_p)[-1] is not next_open
            or next_open.getparent() is not intro_p
            or list(intro_p)[-2] is not close
            or next_close.getparent() is intro_div
            or list(leading_p)[0] is not begin):
        raise IntroRepairError("Source introduction cannot be moved without rewriting paragraphs")

    # Source chapter must really start before the special introductory
    # paragraph; the first subsequent numbered milestone must be the
    # approved following section. Do not fabricate a chapter or verse 0.
    chapter = f"{m.group(1)}.{m.group(2)}"
    chapter_starts = [node for node in book
                      if isinstance(node.tag, str) and _local(node) == "chapter"
                      and node.get("sID") == chapter]
    if (len(chapter_starts) != 1
            or list(book).index(chapter_starts[0]) >= list(book).index(leading_p)):
        raise IntroRepairError("No existing chapter boundary for OSIS introduction")

    positions = {}
    elements = (node for node in tree.iter() if isinstance(node.tag, str))
    stack = []
    parser = expat.ParserCreate(namespace_separator="}")
    def begin_element(name, _attributes):
        node = next(elements, None)
        tag = "{" + name if "}" in name else name
        if node is None or node.tag != tag:
            raise IntroRepairError("Lexical/XML parser topology mismatch")
        stack.append(node)
        if node in (leading_p, intro_div, begin, close, next_open):
            pos = parser.CurrentByteIndex
            end = _xml_tag_end(raw, pos)
            token = raw[pos:end]
            positions[("start", node)] = (pos, end, token)
            if node in (begin, close, next_open) and not token.endswith(b"/>"):
                raise IntroRepairError("Expected self-closing source milestone")
    def end_element(_name):
        if not stack:
            raise IntroRepairError("Unbalanced source parser stack")
        node = stack.pop()
        if node is intro_div:
            pos = parser.CurrentByteIndex
            end = _xml_tag_end(raw, pos)
            token = raw[pos:end]
            if not token.startswith(b"</") or not token.endswith(b">"):
                raise IntroRepairError("Existing intro closing tag is not lexical XML")
            positions[("end", intro_div)] = (pos, end, token)
    def deny(*_args):
        raise IntroRepairError("DTD/entities not allowed")
    parser.StartElementHandler = begin_element
    parser.EndElementHandler = end_element
    parser.StartDoctypeDeclHandler = deny
    parser.EntityDeclHandler = deny
    parser.ExternalEntityRefHandler = lambda *_args: 0
    try:
        parser.Parse(raw, True)
    except expat.ExpatError as exc:
        raise IntroRepairError("Private source lexical parse failed") from exc
    if stack or next(elements, None) is not None or len(positions) != 6:
        raise IntroRepairError("Partial source lexical marker coverage")

    intro_open = positions[("start", intro_div)][2]
    next_verse_open = positions[("start", next_open)][2]
    edits = []
    def patch(start: int, end: int, replacement: bytes):
        edits.append((start, end, replacement))
    # Existing intro div encloses the original source intro's second
    # paragraph but not its first. Move its start before the first paragraph.
    patch(positions[("start", leading_p)][0],
          positions[("start", leading_p)][0], intro_open)
    patch(*positions[("start", intro_div)][:2], b"")
    # The old first verse is metadata-only misindexing: it is now a
    # genuine chapter introduction, not verse 1 commentary.
    for marker in (begin, close, next_open):
        patch(*positions[("start", marker)][:2], b"")
    # Move the existing following verse opener OUTSIDE the introduction div.
    patch(positions[("end", intro_div)][1],
          positions[("end", intro_div)][1], next_verse_open)

    edited = bytearray()
    cursor = 0
    for first, last, replacement in sorted(edits, key=lambda x: (x[0], x[1])):
        if not 0 <= cursor <= first <= last <= len(raw):
            raise IntroRepairError("Conflicting lexical intro source edits")
        edited.extend(raw[cursor:first])
        edited.extend(replacement)
        cursor = last
    edited.extend(raw[cursor:])
    result = bytes(edited)
    candidate = _tree(result)
    # Not just equivalent words: the full XML text character stream,
    # punctuation, accents and whitespace must survive unchanged.
    original_text = "".join(tree.itertext())
    revised_text = "".join(candidate.itertext())
    if original_text != revised_text:
        raise IntroRepairError("Authored prose, punctuation or whitespace changed")
    def metadata(t):
        return sorted(((_local(n), tuple(sorted(n.attrib.items())),
                        n.text, n.tail)
                       for n in t.iter()
                       if isinstance(n.tag, str) and _local(n) in
                          {"note", "reference", "title", "hi"}), key=repr)
    if metadata(tree) != metadata(candidate):
        raise IntroRepairError("Original source note/citation/title markup changed")
    new_begin = [x for x in candidate.iter()
                 if isinstance(x.tag, str) and _local(x) == "verse"
                 and x.get("sID") == old]
    new_close = [x for x in candidate.iter()
                 if isinstance(x.tag, str) and _local(x) == "verse"
                 and x.get("eID") == old]
    rewritten_start = [x for x in candidate.iter()
                       if isinstance(x.tag, str) and _local(x) == "verse"
                       and x.get("sID") == following]
    if new_begin or new_close or len(rewritten_start) != 1:
        raise IntroRepairError("Old verse boundary remained or real verse was lost")
    new_intro = next((x for x in candidate.iter()
                      if isinstance(x.tag, str)
                      and _local(x) == "div"
                      and x.get("type") == "introduction"
                      and x.sourceline >= leading_p.sourceline - 2
                      and x.sourceline <= intro_div.sourceline), None)
    if (new_intro is None or len(new_intro) != len(between)+2
            or any(_local(n)!="p" for n in new_intro)
            or rewritten_start[0].getparent() is new_intro
            or new_intro.getparent().get("osisID") != m.group(1)):
        raise IntroRepairError("Semantic introduction still contains verse commentary")

    return result, {
        "status": "PRIVATE_SOURCE_FAITHFUL_CHAPTER_INTRO_RECLASSIFIED_NOT_RELEASED",
        "old_source_sha256": sha256(raw).hexdigest(),
        "candidate_sha256": sha256(result).hexdigest(),
        "original_source_intro_first_line": plan["old_intro_opening_line"],
        "chapter_intro_osis_div_type": "introduction",
        "removed_source_verse_milestone_count": 2,
        "moved_original_xml_tokens_count": 2,
        "all_original_source_text_whitespace_and_punctuation_identical": True,
        "all_original_source_notes_references_and_titles_identical": True,
        "new_chapter_verse_invented": False,
        "published": False,
    }
