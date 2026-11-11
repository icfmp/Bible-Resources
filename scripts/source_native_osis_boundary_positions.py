#!/usr/bin/env python3
"""Private original OSIS vs native SWORD structural nonspace-boundary screen.

Book text and generated XML stay in memory. The receipt contains only counts
and bounded canonical book IDs. This does not certify exact whitespace,
typography, title contents, independent reader rendering or publication.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

from native_milestone_pair_audit import _strict_root
from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY
from sword_native_inventory import INTRO

BOOK = re.compile(r"(?:[1-4])?[A-Za-z][A-Za-z0-9]{0,39}\Z")
SKIP = frozenset({"note", "header", "title"})
KINDS = ("p", "l", "lg")
ENDPOINTS = ("open", "close")
MAX_TEXT = 5_000_000
MAX_EVENTS = 70_000
MAX_EXAMPLES = 18


class BoundaryScreenError(ValueError):
    """Untrustworthy source/native structure or scope."""


class _Stream:
    def __init__(self):
        self.hash = sha256()
        self.chars = 0
        self.events = defaultdict(list)
        self.num_events = 0
        self.titles = []  # private (nonspace position, title digest, character count)

    def append(self, string):
        if string:
            nonspace = "".join(x for x in string if not x.isspace())
            self.chars += len(nonspace)
            if self.chars > MAX_TEXT:
                raise BoundaryScreenError("Oversized private body text stream")
            self.hash.update(nonspace.encode("utf-8"))

    def mark(self, name, endpoint):
        if name not in KINDS or endpoint not in ENDPOINTS:
            raise BoundaryScreenError("Unknown structural event")
        key=name+"_"+endpoint
        self.events[key].append(self.chars)
        self.num_events += 1
        if self.num_events > MAX_EVENTS:
            raise BoundaryScreenError("Too many private structural events")

    def digest(self):
        return self.hash.hexdigest()


def _local(node):
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _walk(node,stream,mode):
    name=_local(node)
    if name == "title":
        prose="".join(node.itertext())
        chars="".join(x for x in prose if not x.isspace())
        if len(chars)>MAX_TEXT or len(stream.titles)>=MAX_EVENTS:
            raise BoundaryScreenError("Oversized authored or native title")
        stream.titles.append((stream.chars,sha256(chars.encode("utf-8")).hexdigest(),len(chars)))
        return  # Title is editorial metadata, not part of the main-body stream.
    if name in SKIP:
        return  # Parent still processes node.tail, as authored.
    event = None
    container = False
    if mode == "source" and node.tag in {OSIS+"p",OSIS+"l",OSIS+"lg"}:
        if node.get("sID") is not None or node.get("eID") is not None:
            raise BoundaryScreenError("Unsupported original source structural milestone")
        event=name
        container=True
    elif mode == "native":
        if name=="div" and node.get("type")=="x-p":
            event="p"
        elif name in {"l","lg"}:
            event=name
        if event:
            sid,eid=node.get("sID"),node.get("eID")
            if sid is not None and eid is not None:
                raise BoundaryScreenError("Ambiguous native structural milestone")
            if sid is not None:
                if not sid:
                    raise BoundaryScreenError("Empty native opening ID")
                stream.mark(event,"open")
            elif eid is not None:
                if not eid:
                    raise BoundaryScreenError("Empty native closing ID")
                stream.mark(event,"close")
            else:
                if name=="div":
                    raise BoundaryScreenError("Unpaired native paragraph div")
                container=True
    if container:
        stream.mark(event,"open")
    stream.append(node.text)
    for child in node:
        _walk(child,stream,mode)
        stream.append(child.tail)
    if container:
        stream.mark(event,"close")


def authorial_book_streams(xml: bytes):
    root=_source_tree(xml)
    books=[n for n in root.iter(OSIS+"div") if n.get("type")=="book"]
    if not books or len(books)>250:
        raise BoundaryScreenError("Unsupported authorial source book scope")
    result={}
    for book in books:
        name=book.get("osisID")
        if not name or not BOOK.fullmatch(name) or name in result:
            raise BoundaryScreenError("Ambiguous authored book ID")
        if any(a.tag==OSIS+"div" and a.get("type")=="book"
               for a in book.iterancestors()):
            raise BoundaryScreenError("Nested authored book")
        stream=_Stream()
        _walk(book,stream,"source")
        result[name]=stream
    return result


class NativeBookStreams:
    """Process actual native K/I/U frames in the independent reader order."""
    def __init__(self):
        self.books={}
        self.top_nonspace=0
        self.frames=Counter()

    def observe(self,kind,ref,raw):
        if kind not in {"K","I","U"}:
            raise BoundaryScreenError("Unrecognized native record kind")
        if kind=="K" and not KEY.fullmatch(ref):
            raise BoundaryScreenError("Malformed native numbered ref")
        if kind=="I" and not INTRO.fullmatch(ref):
            raise BoundaryScreenError("Malformed native intro ref")
        root=_strict_root(raw)
        self.frames[kind]+=1
        if kind=="U":
            top=_Stream()
            _walk(root,top,"native")
            self.top_nonspace+=top.chars
            return
        book=ref.split(".",1)[0]
        if not BOOK.fullmatch(book):
            raise BoundaryScreenError("Malformed native book key")
        stream=self.books.setdefault(book,_Stream())
        _walk(root,stream,"native")


def compare_book_boundary_positions(original: dict, compiled: NativeBookStreams):
    if not original or set(original)!=set(compiled.books):
        raise BoundaryScreenError("Full source/native book scope not verified")
    counts=Counter()
    samples=[]
    for book in sorted(original):
        src,nat=original[book],compiled.books[book]
        counts["books_compared"]+=1
        same_text=(src.chars==nat.chars and src.digest()==nat.digest())
        if same_text:
            counts["books_with_identical_full_nonspace_body_stream"]+=1
        else:
            counts["books_with_unmatched_full_body_stream"]+=1
            if len(samples)<MAX_EXAMPLES:
                samples.append({"book":book,"kind":"body_nonspace_stream_differs",
                                "source_nonspace_length":src.chars,
                                "compiled_nonspace_length":nat.chars})
        counts["source_title_events"]+=len(src.titles)
        counts["native_title_events"]+=len(nat.titles)
        if src.titles==nat.titles:
            counts["title_prose_and_nonspace_positions_equal"]+=len(src.titles)
        else:
            counts["books_with_title_position_or_text_differences"]+=1
            if len(samples)<MAX_EXAMPLES:
                idx=next((i for i in range(min(len(src.titles),len(nat.titles)))
                          if src.titles[i]!=nat.titles[i]),
                         min(len(src.titles),len(nat.titles)))
                samples.append({"book":book,"kind":"title_content_or_position_difference",
                                "one_based_title":idx+1,
                                "source_title_count":len(src.titles),
                                "native_title_count":len(nat.titles)})
        for kind in KINDS:
            for endpoint in ENDPOINTS:
                key=kind+"_"+endpoint
                x,y=src.events[key],nat.events[key]
                counts["source_"+key+"_events"]+=len(x)
                counts["native_"+key+"_events"]+=len(y)
                if same_text and x==y:
                    counts["boundary_event_positions_equal"]+=len(x)
                else:
                    counts["boundary_event_groups_unverified_or_different"]+=1
                    if len(samples)<MAX_EXAMPLES:
                        idx=next((i for i in range(min(len(x),len(y)))
                                  if x[i]!=y[i]),min(len(x),len(y)))
                        samples.append({"book":book,"kind":key,
                                        "one_based_event":idx+1,
                                        "source_event_count":len(x),
                                        "native_event_count":len(y),
                                        "source_nonspace_position":x[idx] if idx<len(x) else None,
                                        "native_nonspace_position":y[idx] if idx<len(y) else None})
    verified=(counts["books_compared"]==len(original)
              and not counts["books_with_unmatched_full_body_stream"]
              and not counts["boundary_event_groups_unverified_or_different"]
              and not counts["books_with_title_position_or_text_differences"]
              and compiled.top_nonspace==0)
    return {
        "status":("source_native_body_boundary_nonspace_positions_equal"
                  if verified else "body_or_boundary_positions_require_review"),
        "counts":dict(sorted(counts.items())),
        "native_anonymous_top_nonspace_body_characters":compiled.top_nonspace,
        "native_frame_counts":dict(sorted(compiled.frames.items())),
        "bounded_reference_only_findings":samples,
        "all_book_body_nonspace_and_boundary_events_equal":verified,
        "literal_whitespace_or_exact_typography_verified":False,
        "all_title_text_and_nonspace_placement_equal": (
            not counts["books_with_title_position_or_text_differences"]
            and counts["source_title_events"]==counts["native_title_events"]
        ),
        "source_title_prose_and_verse_zero_semantics_verified":False,
        "independent_reader_visual_signoff":False,
        "published":False,
    }
