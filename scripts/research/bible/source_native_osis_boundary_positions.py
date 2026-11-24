#!/usr/bin/env python3
"""Private original OSIS vs native SWORD structural nonspace-boundary screen.

Book text and generated XML stay in memory. The receipt contains only counts
and bounded canonical book IDs. This does not certify exact whitespace,
typography, title contents, independent reader rendering or publication.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from bisect import bisect_right
from hashlib import sha256
import re
import json

from lxml import etree

from research.bible.native_milestone_pair_audit import _strict_root
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
        self.refs = []  # private source verse anchors (nonspace position, ID)
        self.titles = []  # private (nonspace position, title digest, character count)
        self.editorial = _EditorialStream()
        self.word_hash = sha256()
        self.word_count = 0
        self.annotated_word_count = 0
        self.excluded_word_count = 0

    def mark_word(self, node, start):
        # Attribute order is XML serialization, not lexical meaning. Do not
        # normalize values, sort lemma tokens or discard unfamiliar attributes.
        attributes = sorted(node.attrib.items())
        if any(_local(c) == 'w' for c in node.iterdescendants()):
            raise BoundaryScreenError('Nested lexical word element')
        if node.get('sID') is not None or node.get('eID') is not None:
            raise BoundaryScreenError('Unsupported lexical word milestone')
        if self.chars <= start:
            raise BoundaryScreenError('Empty lexical word span')
        data = json.dumps([start, self.chars, attributes], ensure_ascii=False,
                          separators=(',', ':')).encode('utf-8')
        self.word_hash.update(len(data).to_bytes(8, 'big'))
        self.word_hash.update(data)
        self.word_count += 1
        self.annotated_word_count += bool(attributes)

    def exclude_words(self, node):
        self.excluded_word_count += sum(_local(n) == 'w' for n in node.iterdescendants())

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
    # XML comments and processing instructions are not authored body text.
    # The caller still includes their tails in the surrounding body stream.
    if not isinstance(node.tag, str):
        return
    name=_local(node)
    if mode == "source" and node.tag == OSIS+"verse" and node.get("osisID"):
        ref = node.get("osisID")
        if not KEY.fullmatch(ref):
            raise BoundaryScreenError("Invalid source verse anchor")
        stream.refs.append((stream.chars, ref))
    if name == "title":
        stream.exclude_words(node)
        prose="".join(node.itertext())
        chars="".join(x for x in prose if not x.isspace())
        if len(chars)>MAX_TEXT or len(stream.titles)>=MAX_EVENTS:
            raise BoundaryScreenError("Oversized authored or native title")
        stream.titles.append((stream.chars,sha256(chars.encode("utf-8")).hexdigest(),len(chars)))
        return  # Title is editorial metadata, not part of the main-body stream.
    if name in SKIP:
        stream.exclude_words(node)
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
    word_start = stream.chars if name == "w" else None
    stream.append(node.text)
    for child in node:
        _walk(child,stream,mode)
        stream.append(child.tail)
    if word_start is not None:
        stream.mark_word(node, word_start)
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
        stream.editorial.visit(book,"source")
        result[name]=stream
    return result


def authorial_outside_book_titles(xml: bytes):
    """Title signatures outside book scopes (typically testament headings).

    Their recorded authored order must equal the SWORD TOP title order. Title
    contents are never included in the report; book headings remain separate.
    """
    root = _source_tree(xml)
    result=[]
    for node in root.iter(OSIS+"title"):
        parents=list(node.iterancestors())
        if any(p.tag in {OSIS+"header",OSIS+"note"} for p in parents):
            continue
        if any(p.tag==OSIS+"div" and p.get("type")=="book" for p in parents):
            continue
        prose="".join(node.itertext())
        chars="".join(c for c in prose if not c.isspace())
        if len(chars)>MAX_TEXT or len(result)>=MAX_EVENTS:
            raise BoundaryScreenError("Excessive authored outside-book title")
        result.append((sha256(chars.encode("utf-8")).hexdigest(),len(chars)))
    return result


class NativeBookStreams:
    """Process actual native K/I/U frames in the independent reader order."""
    def __init__(self):
        self.books={}
        self.top_nonspace=0
        self.top_titles=[]  # original order, private content digests only
        self.top_word_count=0
        self.top_excluded_word_count=0
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
            self.top_word_count+=top.word_count
            self.top_excluded_word_count+=top.excluded_word_count
            self.top_titles.extend((digest,length) for _position,digest,length in top.titles)
            return
        book=ref.split(".",1)[0]
        if not BOOK.fullmatch(book):
            raise BoundaryScreenError("Malformed native book key")
        stream=self.books.setdefault(book,_Stream())
        _walk(root,stream,"native")
        stream.editorial.visit(root,"native")


def _paragraph_spans(stream):
    """Compare complete non-nested paragraph spans, not shifted ordinal pairs."""
    starts, ends = stream.events["p_open"], stream.events["p_close"]
    if (len(starts) != len(ends)
            or any(a > b for a, b in zip(starts, ends))
            or any(b > a for b, a in zip(ends, starts[1:]))):
        raise BoundaryScreenError("Paragraph spans are unpaired or overlapping")
    return Counter(zip(starts, ends))


def _paragraph_differences(book, src, nat, counts, findings):
    """When full book text agrees, locate missing/extra spans by source anchors."""
    expected, actual = _paragraph_spans(src), _paragraph_spans(nat)
    offsets = [position for position, _ in src.refs]
    for category, spans in (("source_only", expected-actual),
                            ("native_only", actual-expected)):
        for (start, end), multiplicity in sorted(spans.items()):
            counts[category+"_paragraph_spans"] += multiplicity
            if start == end:
                counts[category+"_zero_nonspace_paragraph_spans"] += multiplicity
            else:
                counts[category+"_nonempty_paragraph_spans"] += multiplicity
            if len(findings) < MAX_EXAMPLES:
                index = bisect_right(offsets, start)-1
                findings.append({"book": book, "kind": category,
                                 "preceding_or_coincident_source_verse": src.refs[index][1] if index >= 0 else None,
                                 "next_source_verse": src.refs[index+1][1] if index+1 < len(src.refs) else None,
                                 "start_nonspace": start, "end_nonspace": end,
                                 "multiplicity": multiplicity})
    counts["identical_paragraph_spans"] += sum((expected & actual).values())


def compare_book_boundary_positions(original: dict, compiled: NativeBookStreams,
                                    original_outside_titles=None):
    if not original or set(original)!=set(compiled.books):
        raise BoundaryScreenError("Full source/native book scope not verified")
    counts=Counter()
    samples=[]
    paragraph_counts=Counter()
    paragraph_findings=[]
    lexical=Counter()
    lexical_findings=[]
    for book in sorted(original):
        src,nat=original[book],compiled.books[book]
        counts["books_compared"]+=1
        same_text=(src.chars==nat.chars and src.digest()==nat.digest())
        if same_text:
            counts["books_with_identical_full_nonspace_body_stream"]+=1
            _paragraph_differences(book,src,nat,paragraph_counts,paragraph_findings)
        else:
            counts["books_with_unmatched_full_body_stream"]+=1
            if len(samples)<MAX_EXAMPLES:
                samples.append({"book":book,"kind":"body_nonspace_stream_differs",
                                "source_nonspace_length":src.chars,
                                "compiled_nonspace_length":nat.chars})
        lexical["source_body_word_elements"] += src.word_count
        lexical["native_body_word_elements"] += nat.word_count
        lexical["source_body_word_elements_with_attributes"] += src.annotated_word_count
        lexical["native_body_word_elements_with_attributes"] += nat.annotated_word_count
        lexical["source_excluded_note_title_header_word_elements"] += src.excluded_word_count
        lexical["native_excluded_note_title_header_word_elements"] += nat.excluded_word_count
        if same_text and src.word_count == nat.word_count and src.word_hash.digest() == nat.word_hash.digest():
            lexical["books_with_identical_word_spans_and_attributes"] += 1
        else:
            lexical["books_with_unverified_or_different_word_associations"] += 1
            if len(lexical_findings) < MAX_EXAMPLES:
                lexical_findings.append({"book": book, "source_word_elements": src.word_count,
                    "native_word_elements": nat.word_count,
                    "full_body_nonspace_equal": same_text,
                    "ordered_span_attribute_digest_equal": src.word_hash.digest() == nat.word_hash.digest()})
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
    outside_titles_proved=False
    if original_outside_titles is not None:
        counts["source_outside_book_title_events"]=len(original_outside_titles)
        counts["native_TOP_title_events"]=len(compiled.top_titles)
        outside_titles_proved=(original_outside_titles==compiled.top_titles)
        if outside_titles_proved:
            counts["outside_book_title_text_and_order_equal"]=len(original_outside_titles)
        else:
            counts["outside_book_title_text_or_order_requires_review"]+=1
            if len(samples)<MAX_EXAMPLES:
                samples.append({"kind":"outside_book_title_content_or_order_differs",
                                "source_count":len(original_outside_titles),
                                "compiled_count":len(compiled.top_titles)})
    verified=(counts["books_compared"]==len(original)
              and not counts["books_with_unmatched_full_body_stream"]
              and not counts["boundary_event_groups_unverified_or_different"]
              and not counts["books_with_title_position_or_text_differences"]
              and outside_titles_proved
              and compiled.top_nonspace==0)
    return {
        "status":("source_native_body_boundary_nonspace_positions_equal"
                  if verified else "body_or_boundary_positions_require_review"),
        "counts":dict(sorted(counts.items())),
        "native_anonymous_top_nonspace_body_characters":compiled.top_nonspace,
        "native_frame_counts":dict(sorted(compiled.frames.items())),
        "bounded_reference_only_findings":samples,
        "book_editorial_inline_diagnostic": _compare_editorial_streams(
            {book: stream.editorial for book, stream in original.items()},
            {book: stream.editorial for book, stream in compiled.books.items()}),
        "body_lexical_association_diagnostic": {
            "counts": dict(sorted(lexical.items())),
            "bounded_book_only_findings": lexical_findings,
            "all_book_body_word_spans_and_attributes_equal": (
                lexical["books_with_identical_word_spans_and_attributes"] == len(original)
                and compiled.top_word_count == 0),
            "native_TOP_body_word_elements": compiled.top_word_count,
            "native_TOP_excluded_word_elements": compiled.top_excluded_word_count,
            "scope": "book body including addressable introductions; excludes title, note, header, outside-book source",
            "exact_attribute_values_compared": True,
            "original_publisher_to_cleaned_source_lexical_parity_verified": False,
            "excluded_scopes_certified": False,
            "mandatory_release_gate": False,
        },
        "paragraph_span_diagnostic": {
            "counts": dict(sorted(paragraph_counts.items())),
            "bounded_reference_only_findings": paragraph_findings,
            "scope": "books_with_identical_full_nonspace_body_stream",
            "zero_nonspace_spans_not_automatically_waived": True,
        },
        "all_book_body_nonspace_and_boundary_events_equal":verified,
        "literal_whitespace_or_exact_typography_verified":False,
        "all_title_text_and_nonspace_placement_equal": (
            not counts["books_with_title_position_or_text_differences"]
            and counts["source_title_events"]==counts["native_title_events"]
            and outside_titles_proved
        ),
        "source_title_prose_and_verse_zero_semantics_verified":False,
        "independent_reader_visual_signoff":False,
        "published":False,
    }


def _editorial_require(condition):
    if not condition:
        raise BoundaryScreenError('Unsupported or unpaired editorial span')

# These explicit OSIS constructs have matching source/native representations
# in the real-edition census. Unsupported milestone shapes fail visibly.
_EDITORIAL_INLINE={"w","q","hi","lb","reference","seg","foreign","name","divineName","transChange"}
def _editorial_digest(value):
    return sha256(json.dumps(value,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
class _EditorialStream:
    def __init__(self):
        self.pos=0
        self.text=sha256()
        self.events=defaultdict(list)
        self.intros=[]
        self.open_intros={}
        self.scopes=defaultdict(list)
        self.scope_word_count=Counter()
        self.order=[]
    def append(self,value):
        v="".join(c for c in (value or "") if not c.isspace())
        self.pos+=len(v)
        self.text.update(v.encode())
    def signature(self):
        _editorial_require(not self.open_intros)
        return (self.pos,self.text.hexdigest(),[(tag,len(rows),_editorial_digest(rows)) for tag,rows in sorted(self.events.items())],self.intros,_editorial_digest(self.order))
    def visit(self,node,mode,allow_scopes=True):
        tag=_local(node)
        if not tag or tag=="header": return
        if tag in {"note","title"} and allow_scopes:
            nested=_EditorialStream()
            nested.visit(node,mode,False)
            # Body anchor + ordered scoped text digest and word/markup spans.
            self.scopes[tag].append((self.pos,nested.signature()))
            self.scope_word_count[tag]+=len(nested.events["w"])
            return
        start=self.pos
        attrs=tuple(sorted(node.attrib.items()))
        is_intro=tag=="div" and node.get("type")=="introduction"
        if is_intro:
            sid,eid=node.get("sID"),node.get("eID")
            _editorial_require(not(sid and eid))
            stable=tuple((k,v) for k,v in attrs if k not in {"sID","eID"})
            if sid:
                _editorial_require(mode=="native" and sid not in self.open_intros)
                self.open_intros[sid]=len(self.intros)
                self.intros.append([start,None,stable])
            elif eid:
                _editorial_require(mode=="native" and eid in self.open_intros)
                idx=self.open_intros.pop(eid)
                _editorial_require(self.intros[idx][2]==stable)
                self.intros[idx][1]=start
            else:
                idx=len(self.intros)
                self.intros.append([start,None,stable])
        tracked = tag in _EDITORIAL_INLINE and (tag != "w" or not allow_scopes)
        if tracked:
            _editorial_require(node.get("sID") is None and node.get("eID") is None)
            # Reserve event order before recursion to handle nested formatting.
            self.order.append((tag,"open",start))
            ordinal=len(self.events[tag])
            self.events[tag].append(None)
        self.append(node.text)
        for child in node:
            self.visit(child,mode,allow_scopes)
            self.append(child.tail)
        if tracked:
            self.events[tag][ordinal]=(start,self.pos,attrs)
            self.order.append((tag,"close",self.pos))
        if is_intro and not(sid or eid):
            self.intros[idx][1]=self.pos
def _compare_editorial_streams(src,nat):
    counts=Counter()
    findings=[]
    for book in sorted(set(src)|set(nat)):
        if book not in src or book not in nat:
            findings.append({"book":book,"kind":"missing_book_scope"})
            continue
        a,b=src[book],nat[book]
        _editorial_require(not a.open_intros and not b.open_intros)
        text_equal=(a.pos,a.text.digest())==(b.pos,b.text.digest())
        counts["books"]+=1
        counts["body_text_equal"]+=text_equal
        for tag in sorted(_EDITORIAL_INLINE-{"w"}):
            x,y=a.events[tag],b.events[tag]
            counts["source_body_"+tag]+=len(x)
            counts["native_body_"+tag]+=len(y)
            if text_equal and x==y: counts["matched_body_"+tag]+=len(x)
            else: findings.append({"book":book,"kind":"body_"+tag,"source_count":len(x),"native_count":len(y)})
        if a.order!=b.order:
            findings.append({"book":book,"kind":"cross_tag_inline_order"})
        counts["source_intro_spans"]+=len(a.intros)
        counts["native_intro_spans"]+=len(b.intros)
        if text_equal and a.intros==b.intros: counts["matched_intro_spans"]+=len(a.intros)
        else: findings.append({"book":book,"kind":"intro_spans","source_count":len(a.intros),"native_count":len(b.intros)})
        for tag in ("note","title"):
            x,y=a.scopes[tag],b.scopes[tag]
            counts["source_"+tag+"_word_elements"]+=a.scope_word_count[tag]
            counts["native_"+tag+"_word_elements"]+=b.scope_word_count[tag]
            counts["source_"+tag+"_scopes"]+=len(x)
            counts["native_"+tag+"_scopes"]+=len(y)
            if text_equal and x==y: counts["matched_"+tag+"_scopes"]+=len(x)
            else: findings.append({"book":book,"kind":tag+"_scopes","source_count":len(x),"native_count":len(y)})
    return {"counts":dict(sorted(counts.items())),"finding_count":len(findings),"bounded_findings":findings[:30],"all_compared_scopes_equal":bool(src) and not findings,"scope":"book body selected inline elements and introduction spans, anchored book note/title inner content; body word spans separately verified","outer_note_title_attributes_and_outside_book_scopes_certified":False,"exact_whitespace_or_visual_rendering_certified":False}
