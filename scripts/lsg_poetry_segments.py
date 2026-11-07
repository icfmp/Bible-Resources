#!/usr/bin/env python3
"""Attribute poetic-line content to the *verse owning its text* (USFX/OSIS).

An XML line may open before a verse milestone or span two milestones. Counting
only the active verse at the <q>/<l> opening is incorrect in those cases.
Use an ordered, text-event traversal instead; preserve original XML unchanged.

This is a structural diagnostic, not approval to change editorial formatting.
No Scripture or line text appears in JSON reports (counts and hashes only).
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import re
import unicodedata

from lxml import etree
from pilot_preflight import PilotError
from lsg_sword_compare import NON_VERSE_TEXT_ELEMENTS, NON_VERSE_PARAGRAPH_STYLES

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SKIP_TARGET=frozenset(("title","header","note","revisionDesc","description"))
SKIP_SOURCE=frozenset(NON_VERSE_TEXT_ELEMENTS)


def _name(node):
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _no_space(text):
    return "".join(unicodedata.normalize("NFC",text).split())


POETRY_STYLES=re.compile(r"^(?:q[1-4]?|qm[1-4]?|qr|qc|qd)$")


def _source_poetry_style(node):
    """A poetic paragraph is identified by USFX marker/style, never guesswork."""
    name=_name(node)
    marker=node.get("sfm") or node.get("style") or name
    if name not in {"q","qr","qc","qd","qm","p"}:
        return None
    if not POETRY_STYLES.fullmatch(marker):
        if name in {"q","qr","qc","qd","qm"} or marker.startswith("q"):
            raise PilotError("Unreviewed source poetry paragraph style")
        return None
    if marker in {"qr","qc","qd"}:
        return {"qr":"right","qc":"center","qd":"hebrew-end"}[marker]
    embedded=marker.startswith("qm")
    level=marker[2:] if embedded else marker[1:]
    return ("embedded" if embedded else "indent") + ":" + (level or "1")


def _candidate_poetry_style(node):
    kind=node.get("type")
    if kind in {"x-right","x-center","x-usfm-qd"}:
        return {"x-right":"right","x-center":"center",
                "x-usfm-qd":"hebrew-end"}[kind]
    if kind not in (None,"x-embedded"):
        return "unsupported-type:"+kind
    level=node.get("level")
    if not level or not level.isdecimal():
        return "unsupported-level:"+str(level)
    return ("embedded" if kind=="x-embedded" else "indent")+":"+level


def _read(root, *, source):
    """Read line text as XML events; verse ownership changes at milestones."""
    expected="usfx" if source else "osis"
    if _name(root)!=expected:
        raise PilotError(f"Poetry segment audit expected {expected} XML")
    book_iterator=root.iter("book") if source else (
        node for node in root.iter(OSIS+"div") if node.get("type")=="book")
    assigned=defaultdict(list)
    total_nodes=0
    with_text_unowned=0
    empty_nodes=0
    multiverse_nodes=0
    styles=Counter()
    for book in book_iterator:
        code=book.get("id") if source else book.get("osisID")
        if not code:
            raise PilotError("Unreviewed book identity in poetry segment audit")
        chapter=None
        current=None
        active_lines=[]

        def emit(value):
            nonlocal with_text_unowned
            if not value or not value.strip() or not active_lines:
                return
            line=active_lines[-1]
            if current is None:
                line["unowned_text"]+=len(_no_space(value))
            else:
                line["parts"][current].append(value)

        def walk(node):
            nonlocal chapter,current,total_nodes,empty_nodes,multiverse_nodes,with_text_unowned
            if isinstance(node,etree._Comment):
                return
            if not isinstance(node.tag,str):
                raise PilotError("Unexpected non-element in poetry segmentation")
            kind=_name(node)
            if source:
                if kind=="c":
                    val=node.get("id")
                    if not val or not val.isdecimal():
                        raise PilotError("Unreviewed USFX chapter for poetry")
                    chapter=int(val)
                elif kind=="v":
                    val=node.get("id")
                    if not val or not val.isdecimal() or chapter is None:
                        raise PilotError("Unreviewed USFX verse for poetry")
                    current=(code,chapter,int(val))
                elif kind=="ve":
                    if current is None:
                        raise PilotError("USFX orphan verse close in poetry audit")
                    current=None
                if (kind in SKIP_SOURCE or
                        (kind=="p" and (node.get("sfm") or node.get("style"))
                         in NON_VERSE_PARAGRAPH_STYLES)):
                    return
            else:
                if kind=="verse":
                    start=node.get("osisID") or node.get("sID")
                    end=node.get("eID")
                    if start:
                        if current is not None:
                            raise PilotError("Overlapping OSIS verse in poetry segment audit")
                        current=start
                    elif end:
                        if current!=end:
                            raise PilotError("Mismatched OSIS verse ending in poetry segment audit")
                        current=None
                    else:
                        raise PilotError("Unknown OSIS verse marker in poetry segment audit")
                if kind in SKIP_TARGET:
                    return
            style=_source_poetry_style(node) if source else (
                _candidate_poetry_style(node) if kind=="l" else None)
            is_poetic_line=(style is not None)
            if is_poetic_line:
                if active_lines:
                    raise PilotError("Nested poetry line nodes require editorial review")
                total_nodes+=1
                styles[style]+=1
                active_lines.append({"level":style,
                                     "parts":defaultdict(list),"unowned_text":0})
            emit(node.text)
            for child in node:
                walk(child)
                emit(child.tail)
            if is_poetic_line:
                line=active_lines.pop()
                if not line["parts"] and not line["unowned_text"]:
                    empty_nodes+=1
                if line["unowned_text"]:
                    with_text_unowned+=1
                if len(line["parts"])>1:
                    multiverse_nodes+=1
                for ref, text_parts in line["parts"].items():
                    body="".join(text_parts)
                    compact=_no_space(body)
                    if not compact:
                        continue
                    assigned[ref].append({
                        "level":line["level"],
                        "text_sha256":_hash(compact),
                        "chars":len(compact),
                    })
        walk(book)
        if active_lines:
            raise PilotError("Open poetry line in source XML")
        if not source and current is not None:
            raise PilotError("Open OSIS verse at end of poetry audit book")
    return assigned, {
        "all_poetry_line_nodes":total_nodes,
        "line_nodes_containing_nonverse_text":with_text_unowned,
        "empty_poetry_line_nodes":empty_nodes,
        "line_nodes_spanning_multiple_verses":multiverse_nodes,
        "poetry_line_style_counts":dict(sorted(styles.items())),
    }


def audit_segments(source_root, candidate_root, mapping, source_keys):
    if isinstance(candidate_root,etree._ElementTree):
        candidate_root=candidate_root.getroot()
    authored,source_meta=_read(source_root,source=True)
    converted,target_meta=_read(candidate_root,source=False)
    hist=Counter()
    mismatching_books=Counter()
    discrepancies=Counter()
    first=[]
    equal_counts=equal_text=equal_levels=0
    for book,chapter,verse in source_keys:
        key=(book,chapter,verse)
        target_key=f"{mapping[book]}.{chapter}.{verse}"
        a=authored.get(key,())
        b=converted.get(target_key,())
        delta=len(b)-len(a)
        hist[delta]+=1
        same_count=(delta==0)
        same_text=(same_count and
                   [x["text_sha256"] for x in a]==
                   [x["text_sha256"] for x in b])
        known_levels=all(x["level"] is not None for x in (*a,*b))
        same_levels=(same_count and known_levels
                     and [x["level"] for x in a]==[x["level"] for x in b])
        equal_counts+=same_count
        equal_text+=same_text
        equal_levels+=same_levels
        if same_text and same_levels:
            continue
        mismatching_books[book]+=1
        if not same_count:
            discrepancies["line_count"]+=1
        if not same_text:
            discrepancies["line_text_or_segmentation"]+=1
        if not same_levels:
            discrepancies["indentation_unknown_or_different"]+=1
        if len(first)<80:
            first.append({
                "reference":f"{book}.{chapter}.{verse}",
                "source_lines":len(a),"candidate_lines":len(b),
                "count_equal":same_count,
                "line_text_equal_ignoring_whitespace":same_text,
                "indentation_levels_equal":same_levels,
                "source_levels":[x["level"] for x in a],
                "candidate_levels":[x["level"] for x in b],
                "source_line_hashes":[x["text_sha256"] for x in a],
                "candidate_line_hashes":[x["text_sha256"] for x in b],
            })
    missing_source_keys=len(set(authored)-set(source_keys))
    allowed_target={f"{mapping[c]}.{ch}.{v}" for c,ch,v in source_keys}
    unexpected_target_keys=len(set(converted)-allowed_target)
    total=len(source_keys)
    return {
        "total_compared_verse_keys":total,
        "source_poetry":source_meta,
        "candidate_poetry":target_meta,
        "matching_verse_line_counts_with_text_ownership":equal_counts,
        "matching_verse_line_text_sequences_ignoring_whitespace":equal_text,
        "matching_verse_line_indentation_levels":equal_levels,
        "line_delta_histogram":dict(sorted(hist.items())),
        "mismatching_books":dict(sorted(mismatching_books.items())),
        "difference_categories":dict(sorted(discrepancies.items())),
        "source_poetry_keys_outside_verse_index":missing_source_keys,
        "candidate_poetry_keys_outside_verse_index":unexpected_target_keys,
        "first_differences":first,
        "all_poetry_segments_and_levels_verified":(
            equal_counts==equal_text==equal_levels==total
            and not missing_source_keys and not unexpected_target_keys
            and not source_meta["line_nodes_containing_nonverse_text"]
            and not target_meta["line_nodes_containing_nonverse_text"]
        ),
        "full_editorial_poetry_layout_verified":False,
        "limitation":"Independent content-owner audit handles lines spanning milestones. "
                     "Line grouping (<lg>), blank stanzas, headings and presentation "
                     "must still be reviewed; no original body text is exported.",
    }
