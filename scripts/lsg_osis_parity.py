#!/usr/bin/env python3
"""Verify actual verse body, word text and note placement: eBible USFX -> OSIS.

This is a read-only comparison of two distinct XML formats. It never
normalizes the authorial punctuation or changes Scripture; only collapses
whitespace and applies NFC for *diagnostic* comparisons. The source and
generated OSIS remain separate provenance layers.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import difflib
import hashlib
from pathlib import Path
import re
import unicodedata

from lxml import etree

from lsg_source_compare import scan_usfx
from lsg_sword_compare import usfx_text_by_verse,plain
from pilot_preflight import PilotError

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _node_name(node) -> str:
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _osis_verses(path: Path) -> tuple[dict,dict,dict,dict]:
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    document=etree.parse(str(path),parser=parser)
    root=document.getroot()
    if root.tag!=OSIS+"osis":
        raise PilotError("Generated verse comparison requires a genuine OSIS document")
    verses={}
    words=defaultdict(list)
    note_counts=Counter()
    poetry_counts=Counter()
    starts=set()
    ends=set()
    books={}
    for book in root.iter(OSIS+"div"):
        if book.get("type")!="book":
            continue
        osis_book=book.get("osisID")
        if not osis_book or osis_book in books:
            raise PilotError("Missing or repeated OSIS book identity")
        books[osis_book]=True
        current=None
        def walk(node):
            nonlocal current
            name=_node_name(node)
            if name=="verse":
                opening=node.get("osisID") or node.get("sID")
                closing=node.get("eID")
                if opening:
                    if opening in starts:
                        raise PilotError(f"Duplicate source verse start {opening}")
                    starts.add(opening)
                    current=opening
                    verses[current]=[]
                elif closing:
                    if not current or closing!=current:
                        raise PilotError(f"Orphan/mismatched converted verse end {closing}")
                    ends.add(closing)
                    current=None
                else:
                    raise PilotError("Converted OSIS has verse without verified sID/eID")
                return
            if name in {"title","header","note","revisionDesc","description"}:
                if name=="note" and current:
                    note_counts[current]+=1
                return
            if current and name=="w":
                words[current].append(plain("".join(node.itertext())))
            if current and name=="l":
                poetry_counts[current]+=1
            if current and node.text:
                verses[current].append(node.text)
            for child in node:
                walk(child)
                if current and child.tail:
                    verses[current].append(child.tail)
        walk(book)
        if current is not None:
            raise PilotError(f"Open verse at end of book: {current}")
    if starts!=ends:
        raise PilotError(f"Converted OSIS contains {len(starts-ends)} unclosed verse milestones")
    return ({key:plain("".join(parts)) for key,parts in verses.items()},
            words,note_counts,poetry_counts)


def _source_words(raw: bytes) -> tuple[dict,dict,dict]:
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)
    root=etree.fromstring(raw,parser=parser)
    if _node_name(root)!="usfx":
        raise PilotError("Expected eBible publisher USFX source")
    words=defaultdict(list)
    notes=Counter()
    poetry=Counter()
    for book in root.iter("book"):
        code=book.get("id")
        chapter=None
        current=None
        def walk(node):
            nonlocal current,chapter
            name=_node_name(node)
            if name=="c":
                chapter=int(node.get("id"))
            elif name=="v":
                if not chapter or not node.get("id") or not node.get("id").isdigit():
                    raise PilotError("Unverified original USFX verse opening")
                current=(code,chapter,int(node.get("id")))
            elif name=="ve":
                current=None
            if current and name=="w":
                words[current].append(plain("".join(node.itertext())))
            if current and name=="x":
                notes[current]+=1
            if current and name=="q":
                poetry[current]+=1
            for child in node:
                # Cross-reference notes are handled as complete objects, not
                # canonical words, but they remain counted for preservation.
                walk(child)
        walk(book)
    return words,notes,poetry


def compare(osis_path: Path, publisher_usfx: bytes) -> dict:
    structure,all_source_keys=scan_usfx(publisher_usfx)
    osis_body,osis_words,osis_notes,osis_lines=_osis_verses(osis_path)
    source_codes=structure["original_books"]
    osis_codes=[]
    doc=etree.parse(str(osis_path),parser=etree.XMLParser(
          resolve_entities=False,load_dtd=False,no_network=True))
    for node in doc.iter(OSIS+"div"):
        if node.get("type")=="book":
            osis_codes.append(node.get("osisID"))
    if len(source_codes)!=66 or len(osis_codes)!=66 or len(set(osis_codes))!=66:
        raise PilotError("Cannot trust conversion book order or duplicate canonical identity")
    mapping=dict(zip(source_codes,osis_codes))
    source_body,_=usfx_text_by_verse(publisher_usfx,filter_books=set(source_codes))
    source_words,source_notes,source_lines=_source_words(publisher_usfx)
    body_equal=0
    word_equal=0
    no_whitespace_equal=0
    notes_equal=0
    poetry_equal=0
    other=Counter()
    differences=[]
    category_samples=defaultdict(list)
    punctuation_diffs=Counter()
    text_edit_kinds=Counter()
    total_source_words=0
    total_osis_words=0
    same_body_except_spaces=Counter()
    source_book_stream=defaultdict(list)
    target_book_stream=defaultdict(list)
    for key in all_source_keys:
        code,chapter,verse=key
        osis_ref=f"{mapping[code]}.{chapter}.{verse}"
        original=source_body.get(key)
        generated=osis_body.get(osis_ref)
        if original is None or generated is None:
            raise PilotError(f"Reference missing from source/OSIS body extraction: {code}.{chapter}.{verse}")
        old_words=source_words.get(key,[])
        new_words=osis_words.get(osis_ref,[])
        original_notes=source_notes[key]
        generated_notes=osis_notes[osis_ref]
        old_lines=source_lines[key]
        new_lines=osis_lines[osis_ref]
        body_equal+=(original==generated)
        same_symbols=("".join(original.split())=="".join(generated.split()))
        no_whitespace_equal+=same_symbols
        source_book_stream[code].append(original)
        target_book_stream[code].append(generated)
        if original != generated and same_symbols:
            same_body_except_spaces["spacing_only_verses"]+=1
        elif original != generated:
            same_body_except_spaces["content_symbols_differ_verses"]+=1
        word_equal+=(old_words==new_words)
        notes_equal+=(original_notes==generated_notes)
        poetry_equal+=(old_lines==new_lines)
        total_source_words+=len(old_words)
        total_osis_words+=len(new_words)
        if (original!=generated or old_words!=new_words or
                original_notes!=generated_notes or old_lines!=new_lines):
            kind_flags={
                "verse_text":original!=generated,
                "word_sequence":old_words!=new_words,
                "note_placement":original_notes!=generated_notes,
                "poetry_line_placement":old_lines!=new_lines,
            }
            detail={
                "reference":f"{code}.{chapter}.{verse}",
                "source_chars":len(original),"generated_chars":len(generated),
                "source_words":len(old_words),"generated_words":len(new_words),
                "source_notes":original_notes,"generated_notes":generated_notes,
                "source_poetry_lines":old_lines,"generated_poetry_lines":new_lines,
            }
            for category,flag in kind_flags.items():
                if flag and len(category_samples[category])<45:
                    category_samples[category].append(detail)
            if original!=generated:
                sequence=difflib.SequenceMatcher(None,original,generated,autojunk=False)
                for tag,i,j,k,l in sequence.get_opcodes():
                    if tag=="equal":
                        continue
                    text_edit_kinds[tag]+=1
                    src,dst=original[i:j],generated[k:l]
                    # Punctuation-only tiny edits can be described without
                    # emitting any source words or full Bible text.
                    if (len(src)<=5 and len(dst)<=5 and
                            not any(x.isalpha() or x.isdigit() for x in src+dst)):
                        punctuation_diffs[(tag,src,dst)]+=1
            if len(differences)<80:
                differences.append({
                    "reference":f"{code}.{chapter}.{verse}",
                    "body_text_equal":original==generated,
                    "source_text_sha256":_hash(original),
                    "generated_text_sha256":_hash(generated),
                    "source_text_length":len(original),
                    "generated_text_length":len(generated),
                    "word_sequence_equal":old_words==new_words,
                    "source_word_markers":len(old_words),
                    "generated_word_markers":len(new_words),
                    "note_counts_equal":original_notes==generated_notes,
                    "source_note_markers":original_notes,
                    "converted_note_markers":generated_notes,
                    "poetry_lines_equal":old_lines==new_lines,
                    "source_poetry_lines":old_lines,
                    "converted_poetry_lines":new_lines,
                })
        if original!=generated:
            other["verse_text_differences"]+=1
        if old_words!=new_words:
            other["word_text_sequence_differences"]+=1
        if original_notes!=generated_notes:
            other["note_count_differences"]+=1
        if old_lines!=new_lines:
            other["poetry_line_count_differences"]+=1
    total=len(all_source_keys)
    return {
        "schema_version":1,
        "status":"real_original_to_converted_osis_diagnostic",
        "total_source_verse_keys":total,
        "total_converted_verse_keys":len(osis_body),
        "exact_normalized_verse_text_matches":body_equal,
        "verse_text_matches_ignoring_only_unicode_whitespace":no_whitespace_equal,
        "source_to_candidate_text_difference_categories":dict(same_body_except_spaces),
        "continuous_book_text_matches_ignoring_all_whitespace":{
          code:"".join("".join(x.split()) for x in source_book_stream[code])==
               "".join("".join(x.split()) for x in target_book_stream[code])
          for code in source_codes
        },
        "exact_normalized_word_sequences":word_equal,
        "matching_verse_note_counts":notes_equal,
        "matching_verse_poetry_line_counts":poetry_equal,
        "source_word_markers":total_source_words,
        "converted_word_markers":total_osis_words,
        "source_cross_reference_note_markers":sum(source_notes.values()),
        "converted_note_markers":sum(osis_notes.values()),
        "source_poetry_line_markers_in_verses":sum(source_lines.values()),
        "converted_poetry_line_markers_in_verses":sum(osis_lines.values()),
        "differences":dict(other),
        "first_per_category":dict(category_samples),
        "text_edit_kinds":dict(text_edit_kinds),
        "punctuation_only_changes":[
            {"kind":key[0],"source_symbols":key[1],"target_symbols":key[2],
             "count":num}
            for key,num in punctuation_diffs.most_common(35)
        ],
        "first_differences":differences,
        "source_text_modified":False,
        "all_note_text_and_reference_targets_verified":False,
        "all_strong_attributes_verified":False,
        "all_source_layout_markup_verified":False,
        "approved_for_publication":False,
        "caveat":"NFC+whitespace verse-body comparison, ordered word text and marker counts; not identity of USFM annotations, intro text, note content, strong IDs or SWORD recompiled module.",
    }
