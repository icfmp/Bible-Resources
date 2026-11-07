#!/usr/bin/env python3
"""Read-only, source-bound simulation of whitespace after Jesus-speech spans.

The original USFX uses <wj>; the OSIS candidate uses <q who="Jesus">.
A converter may drop the separator after a closing USFM \wj* marker. This
routine only simulates its presence when the source/target spans can be
independently paired by verse, ordinal, word anchor and canonical text.
No original XML is modified. No Scripture text is included in diagnostics.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib

from lxml import etree

from pilot_preflight import PilotError
from lsg_sword_compare import NON_VERSE_TEXT_ELEMENTS, NON_VERSE_PARAGRAPH_STYLES

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SKIP_SOURCE=frozenset(NON_VERSE_TEXT_ELEMENTS)
SKIP_TARGET=frozenset(("note","title","header","description","revisionDesc"))


def _name(node):
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _text_without_notes(node, *, source):
    skip=SKIP_SOURCE if source else SKIP_TARGET
    def walk(child):
        if not isinstance(child.tag,str) or _name(child) in skip:
            return ""
        parts=[child.text or ""]
        for nested in child:
            parts.append(walk(nested))
            parts.append(nested.tail or "")
        return "".join(parts)
    return "".join(walk(node).split())


def _collect(root, *, source):
    by_verse=defaultdict(list)
    outside=0
    if source:
        if _name(root)!="usfx":
            raise PilotError("Speech audit requires USFX original")
        books=root.iter("book")
    else:
        if isinstance(root,etree._ElementTree):
            root=root.getroot()
        if root.tag!=OSIS+"osis":
            raise PilotError("Speech audit requires OSIS candidate")
        books=(x for x in root.iter(OSIS+"div") if x.get("type")=="book")
    for book in books:
        code=book.get("id") if source else book.get("osisID")
        if not code:
            raise PilotError("Unreviewed speech-audit book identifier")
        chapter=None
        current=None
        words=0

        def visit(node):
            nonlocal chapter,current,words,outside
            if isinstance(node,etree._Comment):
                return
            if not isinstance(node.tag,str):
                raise PilotError("Unreviewed node in speech audit")
            kind=_name(node)
            if source:
                if kind=="c":
                    raw=node.get("id")
                    if raw is None or not raw.isdecimal():
                        raise PilotError("Unreviewed original chapter in speech audit")
                    chapter=int(raw)
                elif kind=="v":
                    raw=node.get("id")
                    if chapter is None or raw is None or not raw.isdecimal():
                        raise PilotError("Unreviewed original verse in speech audit")
                    current=(code,chapter,int(raw))
                    words=0
                elif kind=="ve":
                    current=None
                is_speech=kind=="wj"
                skip=(kind in SKIP_SOURCE or
                      (kind=="p" and (node.get("sfm") or node.get("style"))
                       in NON_VERSE_PARAGRAPH_STYLES))
            else:
                if kind=="verse":
                    opening=node.get("osisID") or node.get("sID")
                    closing=node.get("eID")
                    if opening:
                        current=opening
                        words=0
                    elif closing:
                        if current!=closing:
                            raise PilotError("Unpaired OSIS milestone in speech audit")
                        current=None
                    else:
                        raise PilotError("Unreviewed OSIS milestone in speech audit")
                    return
                is_speech=(kind=="q" and node.get("who")=="Jesus"
                           and node.get("marker")=="")
                skip=kind in SKIP_TARGET
            if skip:
                return
            at_entry=current
            anchor=words
            if kind=="w" and current is not None:
                words+=1
            for child in node:
                visit(child)
            if is_speech:
                if at_entry is None or at_entry!=current:
                    outside+=1
                else:
                    by_verse[at_entry].append({
                        "node":node,
                        "word_anchor":anchor,
                        "text_digest":hashlib.sha256(
                            _text_without_notes(node,source=source).encode("utf-8")
                        ).hexdigest(),
                        "trailing_space":bool(node.tail) and node.tail[0].isspace(),
                    })
        visit(book)
    return by_verse,outside


def simulate_source_speech_spaces(source_root, candidate_root, mapping):
    """Return a candidate clone and a bounded, text-free diagnostics report."""
    original_before=etree.tostring(
        candidate_root.getroot() if isinstance(candidate_root,etree._ElementTree)
        else candidate_root,encoding="utf-8")
    source,source_outside=_collect(source_root,source=True)
    clone=deepcopy(candidate_root)
    candidate,candidate_outside=_collect(clone,source=False)
    source_count=sum(map(len,source.values()))
    target_count=sum(map(len,candidate.values()))
    categories=Counter()
    examples=[]
    for (book,chapter,verse),segments in sorted(source.items()):
        if book not in mapping:
            raise PilotError("Unknown speech audit book mapping")
        ref=f"{mapping[book]}.{chapter}.{verse}"
        counterpart=candidate.get(ref,[])
        if len(segments)!=len(counterpart):
            categories["unpaired_verse_speech_segments"]+=1
            continue
        for ordinal,(left,right) in enumerate(zip(segments,counterpart),1):
            if (left["word_anchor"]!=right["word_anchor"] or
                left["text_digest"]!=right["text_digest"]):
                categories["unverified_speech_segment_identity"]+=1
                continue
            if left["trailing_space"] and not right["trailing_space"]:
                tail=right["node"].tail or ""
                right["node"].tail=" "+tail
                categories["source_attested_speech_separator_modeled"]+=1
                if len(examples)<60:
                    examples.append({
                        "reference":f"{book}.{chapter}.{verse}",
                        "segment_ordinal":ordinal,
                        "word_anchor":left["word_anchor"],
                    })
            elif left["trailing_space"]:
                categories["speech_separator_already_present"]+=1
            elif right["trailing_space"]:
                categories["candidate_only_speech_separator_not_removed"]+=1
            else:
                categories["speech_separator_absent_in_both"]+=1
    target_only=set(candidate)-{
        f"{mapping[b]}.{c}.{v}" for b,c,v in source
    }
    categories["speech_segments_outside_verse"]=source_outside+candidate_outside
    if etree.tostring(
        candidate_root.getroot() if isinstance(candidate_root,etree._ElementTree)
        else candidate_root,encoding="utf-8")!=original_before:
        raise PilotError("Speech-spacing simulation modified original OSIS")
    after=etree.tostring(clone,encoding="utf-8")
    return clone,{
        "status":"source_bound_speech_whitespace_dry_run_only",
        "original_candidate_unchanged":True,
        "before_sha256":hashlib.sha256(original_before).hexdigest(),
        "simulated_sha256":hashlib.sha256(after).hexdigest(),
        "source_speech_segments":source_count,
        "candidate_speech_segments":target_count,
        "source_speech_verses":len(source),
        "candidate_speech_verses":len(candidate),
        "candidate_only_speech_verse_count":len(target_only),
        "categories":dict(sorted(categories.items())),
        "first_modeled_separators":examples,
        "approved_for_publication":False,
        "limitation":"Only spans with matching verse, ordinal, word anchor "
                     "and non-whitespace text are modeled. Unmatched spans and "
                     "original editorial whitespace require independent review.",
    }
