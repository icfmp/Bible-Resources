#!/usr/bin/env python3
"""Classify text-free, source-visible whitespace changes in compiled footnotes.

The report must never contain note words, raw whitespace strings or XML:
only categorical flags, numeric run lengths and counts. This does NOT
approve changes to authorial line breaks or typography; any non-exact
source-vs-compiled note body remains an editorial-review item.
"""
from __future__ import annotations

import re
import unicodedata


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _runs(value: str) -> tuple[list[str], list[str]]:
    """Words and whitespace gaps, including the leading/trailing gaps."""
    words=re.findall(r"\S+", value)
    gaps=re.split(r"\S+", value)
    if len(gaps)!=len(words)+1:
        raise ValueError("Malformed whitespace segmentation")
    return words,gaps


def _has_non_ascii_space(value: str) -> bool:
    return any(ch.isspace() and ch not in " \t\r\n\v\f" for ch in value)


def classify_note_whitespace(source: str, compiled: str) -> dict:
    """Return strictly non-content diagnostics for one paired note.

    Never use this function to auto-approve line breaks or Unicode spaces.
    """
    source=_nfc(source)
    compiled=_nfc(compiled)
    src_words,src_gaps=_runs(source)
    cmp_words,cmp_gaps=_runs(compiled)
    if src_words!=cmp_words:
        return {
            "class":"non_whitespace_tokens_differ",
            "exact":False,"content_equivalent":False,
        }
    changes=[(a,b,i) for i,(a,b) in
             enumerate(zip(src_gaps,cmp_gaps)) if a!=b]
    if not changes:
        return {
            "class":"exact",
            "exact":True,
            "content_equivalent":True,
            "changed_whitespace_runs":0,
            "changed_internal_runs":0,
            "changed_boundary_runs":0,
            "source_newline_runs_changed":0,
            "compiled_newline_runs_changed":0,
            "source_tab_runs_changed":0,
            "compiled_tab_runs_changed":0,
            "source_unicode_space_runs_changed":0,
            "compiled_unicode_space_runs_changed":0,
            "changed_runs_entirely_ascii_spaces":0,
            "changed_runs_increased_length":0,
            "changed_runs_decreased_length":0,
            "changed_runs_same_length":0,
        }
    count=len(src_words)
    internal=sum(0<i<count for _,_,i in changes)
    boundary=len(changes)-internal
    if internal and boundary:
        category="internal_and_boundary_whitespace_only"
    elif internal:
        category="internal_whitespace_only"
    else:
        category="boundary_whitespace_only"
    return {
        "class":category,
        "exact":False,
        "content_equivalent":True,
        "changed_whitespace_runs":len(changes),
        "changed_internal_runs":internal,
        "changed_boundary_runs":boundary,
        "source_newline_runs_changed":sum("\n" in a or "\r" in a for a,_,_ in changes),
        "compiled_newline_runs_changed":sum("\n" in b or "\r" in b for _,b,_ in changes),
        "source_tab_runs_changed":sum("\t" in a for a,_,_ in changes),
        "compiled_tab_runs_changed":sum("\t" in b for _,b,_ in changes),
        "source_unicode_space_runs_changed":sum(_has_non_ascii_space(a) for a,_,_ in changes),
        "compiled_unicode_space_runs_changed":sum(_has_non_ascii_space(b) for _,b,_ in changes),
        "changed_runs_entirely_ascii_spaces":sum(
            bool(a or b) and all(c==" " for c in a+b) for a,b,_ in changes),
        "changed_runs_increased_length":sum(len(b)>len(a) for a,b,_ in changes),
        "changed_runs_decreased_length":sum(len(b)<len(a) for a,b,_ in changes),
        "changed_runs_same_length":sum(len(a)==len(b) for a,b,_ in changes),
    }
