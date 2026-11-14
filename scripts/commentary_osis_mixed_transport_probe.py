#!/usr/bin/env python3
"""Private, source-faithful mixed original SWORD I+K transport experiment.

The original pinned module is NEVER modified. This builds only a temporary
single-chapter synthetic-identity zCom from verbatim original book I, chapter I
and selected occupied K raw fragments and compares native SWORD readback.

Not a complete commentary or an approved editorial conversion: the other
books, chapters, TOP positions, source version, missing verse-index repairs
and authoritative commentary scope remain outside this experiment.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import re
import subprocess

from lxml import etree

from commentary_osis_transport_probe import (
    KEY, WORK, OSIS_NS, _strict_parser, _source_visible_text,
    classify_native_osis_roundtrip_delta
)
from sword_native_raw_corpus_inventory import parse_native_raw_corpus


def build_mixed_original_transport(chapter: str, book_intro: bytes,
                                   chapter_intro: bytes,
                                   numbered: list[tuple[str, bytes]],
                                   *, work_id: str) -> tuple[bytes, dict]:
    if (not WORK.fullmatch(work_id) or
            re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", chapter) is None
            or not numbered or len(numbered) > 200):
        raise ValueError("Invalid original I+K sample identity")
    book=chapter.rsplit(".",1)[0]
    for raw in (book_intro,chapter_intro):
        if not isinstance(raw,bytes) or not raw or len(raw)>2*1024*1024:
            raise ValueError("Unverified original I bytes")
        _source_visible_text(raw)
    grouped = []
    occupied = {}
    last_verse = 0
    for key, raw in numbered:
        m=KEY.fullmatch(key) if isinstance(key,str) else None
        if m is None or key.rsplit(".",1)[0]!=chapter:
            raise ValueError("K original does not belong to I chapter")
        verse=int(key.rsplit(".",1)[1])
        if verse<=last_verse or not isinstance(raw,bytes):
            raise ValueError("Repeated/out-of-order original native verse")
        _source_visible_text(raw)
        occupied[key]=raw
        digest=sha256(raw).hexdigest()
        if (grouped and grouped[-1]["digest"]==digest
                and grouped[-1]["end"]+1==verse):
            grouped[-1]["end"]=verse
        else:
            grouped.append({"start":verse,"end":verse,"raw":raw,"digest":digest})
        last_verse=verse
    parts=[
        b'<?xml version="1.0" encoding="UTF-8"?>',
        f'<osis xmlns="{OSIS_NS}">'.encode(),
        f'<osisText osisIDWork="{work_id}" osisRefWork="Commentary" xml:lang="en" canonical="true">'.encode(),
        (f'<header><work osisWork="{work_id}"><title>Private mixed original I+K '
         f'transport</title><identifier type="OSIS">{work_id}</identifier>'
         '<refSystem>Bible.KJV</refSystem></work></header>').encode(),
        b'<div type="bookGroup">',
        f'<div type="book" osisID="{book}">'.encode(),
        book_intro,
        f'<div type="chapter" osisID="{chapter}">'.encode(),
        chapter_intro,
    ]
    for group in grouped:
        start=f"{chapter}.{group['start']}"
        end=f"{chapter}.{group['end']}"
        ref=start if start==end else f"{start}-{end}"
        parts.append(
            f'<div type="section" annotateType="commentary" annotateRef="{ref}">'.encode()
        )
        parts.append(group["raw"])
        parts.append(b"</div>")
    parts.extend([b"</div>",b"</div>",b"</div>",b"</osisText>",b"</osis>"])
    xml=b"".join(parts)
    if len(xml)>35*1024*1024 or book_intro not in xml or chapter_intro not in xml:
        raise ValueError("Original mixed source not retained in bounded OSIS")
    try:
        parsed=etree.fromstring(xml,parser=_strict_parser())
    except (ValueError,etree.XMLSyntaxError):
        raise ValueError("Original mixed I+K wrapped OSIS is not safe XML") from None
    if any(isinstance(node,etree._Entity) for node in parsed.iter()):
        raise ValueError("Unresolved original XML entity")
    return xml,{
        "status":"SOURCE_ORIGINAL_I_AND_K_VERBATIM_WRAPPED_FOR_PRIVATE_TEST",
        "chapter":chapter,
        "numbered_source_keys":len(occupied),
        "numbered_source_groups":len(grouped),
        "source_intro_raw_modified":False,
        "source_k_raw_modified":False,
        "source_published":False
    }


def probe_original_mixed_transport(chapter: str, book_intro: bytes,
                                   chapter_intro: bytes,
                                   numbered: list[tuple[str, bytes]], *,
                                   scratch: Path, native_raw_binary: Path,
                                   osis2mod_binary="osis2mod") -> dict:
    if (not scratch.is_dir() or scratch.is_symlink()
            or not native_raw_binary.is_file()
            or native_raw_binary.is_symlink()):
        raise ValueError("Untrusted native mixed original probe path")
    module_id="BRMixedProbe"
    xml, source=build_mixed_original_transport(
        chapter,book_intro,chapter_intro,numbered,work_id=module_id
    )
    root=scratch/"mixed-private-candidate"
    if root.exists() or root.is_symlink():
        raise ValueError("Refuse to overwrite private mixed candidate")
    data=root/"modules"/"comments"/"zcom"/module_id
    conf=root/"mods.d"/(module_id+".conf")
    data.mkdir(parents=True)
    conf.parent.mkdir()
    inp=root/"source-original-private.osis.xml"
    inp.write_bytes(xml)
    try:
        compiled=subprocess.run(
            [str(osis2mod_binary),str(data),str(inp),
             "-z","z","-b","3","-v","KJV"],
            cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=100,check=False
        )
    except (OSError,subprocess.TimeoutExpired):
        return {**source,"status":"MIXED_ORIGINAL_COMPILER_UNAVAILABLE",
                "readback_completed":False,"published":False}
    if compiled.returncode:
        return {**source,"status":"MIXED_ORIGINAL_COMPILER_REJECTED_SOURCE",
                "readback_completed":False,"published":False}
    conf.write_text(
        f"[{module_id}]\nDataPath=./modules/comments/zcom/{module_id}\n"
        "ModDrv=zCom\nCompressType=ZIP\nBlockType=CHAPTER\n"
        "SourceType=OSIS\nVersification=KJV\nLang=en\n"
        "Description=Private mixed-original I and K transport only\n",
        encoding="utf-8"
    )
    try:
        scan=subprocess.run(
            [str(native_raw_binary),module_id],
            cwd=root,env=dict(os.environ,SWORD_PATH=str(root)),
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False,timeout=90
        )
    except (OSError,subprocess.TimeoutExpired):
        return {**source,"status":"MIXED_ORIGINAL_NATIVE_READBACK_UNAVAILABLE",
                "readback_completed":False,"published":False}
    if scan.returncode or len(scan.stdout)>20*1024*1024:
        return {**source,"status":"MIXED_ORIGINAL_NATIVE_READBACK_FAILED",
                "readback_completed":False,
                "native_reader_exit_code":scan.returncode,
                "published":False}
    rebuilt_I,rebuilt_K,rebuilt_U={}, {}, {}
    def collect(kind,key,raw):
        if kind=="I":rebuilt_I[key]=raw
        if kind=="K":rebuilt_K[key]=raw
        if kind=="U":rebuilt_U[key]=raw
    parse_native_raw_corpus(BytesIO(scan.stdout),on_entry=collect)
    book=chapter.rsplit(".",1)[0]
    originals_I={book:book_intro,chapter:chapter_intro}
    originals_K=dict(numbered)
    compared_I={}
    for key,raw in originals_I.items():
        if key in rebuilt_I:
            compared_I[key]=classify_native_osis_roundtrip_delta(
                raw,rebuilt_I[key]
            )
    compared_K={}
    for key,raw in originals_K.items():
        if key in rebuilt_K:
            compared_K[key]=classify_native_osis_roundtrip_delta(
                raw,rebuilt_K[key]
            )
    def summarize(compared):
        return {
            "source_keys_present":len(compared),
            "source_words_preserved_in_exact_order":sum(
                case["word_sequence_relation"]=="EXACT_ORIGINAL_WORD_SEQUENCE"
                for case in compared.values()),
            "source_whitespace_normalized_visible_text_identical":sum(
                case["normalized_whitespace_visible_unicode_equal"]
                for case in compared.values()),
            "original_nondiv_element_order_and_attributes_preserved":sum(
                case["non_div_element_order_and_exact_attribute_values_preserved"]
                for case in compared.values()),
            "original_div_attribute_multiset_preserved":sum(
                case["original_div_elements_exact_attribute_multiset_preserved"]
                for case in compared.values()),
            "original_reference_attribute_values_preserved":sum(
                case["reference_attribute_values_in_original_document_order_preserved"]
                for case in compared.values()),
        }
    return {
        **source,
        "status":"TEMPORARY_MIXED_ORIGINAL_I_K_REBUILT_NOT_EDITION_PARITY",
        "readback_completed":True,
        "source_original_intro_I_coverage":summarize(compared_I),
        "source_original_K_coverage":summarize(compared_K),
        "original_I_keys_missing_from_compiled":sorted(
            set(originals_I)-set(rebuilt_I)),
        "original_K_keys_missing_from_compiled":sorted(
            set(originals_K)-set(rebuilt_K)),
        "unexpected_compiled_K_keys":sorted(
            set(rebuilt_K)-set(originals_K)),
        "compiled_I_key_count":len(rebuilt_I),
        "compiled_K_key_count":len(rebuilt_K),
        "compiled_TOP_key_count":len(rebuilt_U),
        "raw_source_edition_parity_proven":False,
        "entire_original_native_corpus_preserved":False,
        "published":False,
    }
