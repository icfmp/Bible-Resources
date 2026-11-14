#!/usr/bin/env python3
"""Explore original native *introduction* OSIS transport in temporary SWORD only.

Only original SHA-pinned K/I/U stream material may be passed by the verified
audit caller. This is NOT a complete translator or distributable edition.
Two alternate standards-compatible book/chapter wrappers are tested without
editing *one byte* inside the original I XML fragment. Failure is evidence
to address, not permission to delete or normalize original I structure.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
import re
import subprocess

from lxml import etree

from commentary_osis_transport_probe import (
    _strict_parser, _source_visible_text, classify_native_osis_roundtrip_delta,
    WORK, OSIS_NS
)
from sword_native_raw_corpus_inventory import parse_native_raw_corpus


def make_unmodified_intro_osis(chapter: str, original_intro_raw: bytes,
                               *, mode: str, work_id: str) -> bytes:
    if (not isinstance(chapter, str)
            or re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*", chapter) is None
            or mode not in ("chapter_wrapper", "book_direct")
            or not WORK.fullmatch(work_id)):
        raise ValueError("Unreviewed original I transport target or mode")
    if (not isinstance(original_intro_raw, bytes)
            or b"\x00" in original_intro_raw
            or len(original_intro_raw) > 2 * 1024 * 1024):
        raise ValueError("Invalid original I bytes")
    _source_visible_text(original_intro_raw)
    book = chapter.split(".", 1)[0]
    source = [
        b'<?xml version="1.0" encoding="UTF-8"?>',
        f'<osis xmlns="{OSIS_NS}">'.encode(),
        f'<osisText osisIDWork="{work_id}" osisRefWork="Commentary" xml:lang="en" canonical="true">'.encode(),
        (f'<header><work osisWork="{work_id}"><title>Private temporary I transport'
         f' sample</title><identifier type="OSIS">{work_id}</identifier>'
         '<refSystem>Bible.KJV</refSystem></work></header>').encode(),
        b'<div type="bookGroup">',
        f'<div type="book" osisID="{book}">'.encode(),
    ]
    if mode == "chapter_wrapper":
        source.append(f'<div type="chapter" osisID="{chapter}">'.encode())
    source.append(original_intro_raw)
    if mode == "chapter_wrapper":
        source.append(b"</div>")
    source += [b"</div>", b"</div>", b"</osisText>", b"</osis>"]
    xml = b"".join(source)
    try:
        node = etree.fromstring(xml, parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original I embedded unchanged has no valid OSIS wrapper") from None
    if any(isinstance(el, etree._Entity) for el in node.iter()):
        raise ValueError("Original intro OSIS wrapper has an unresolved entity")
    if original_intro_raw not in xml:
        raise ValueError("Original I source was not preserved verbatim in temporary OSIS")
    return xml


def probe_original_intro_transport(chapter: str, original_intro_raw: bytes,
                                   *, scratch: Path, native_raw_binary: Path,
                                   osis2mod_binary="osis2mod") -> dict:
    """Compile and read two independent test-only I transport candidates."""
    if (not scratch.is_dir() or scratch.is_symlink()
            or not native_raw_binary.is_file() or native_raw_binary.is_symlink()):
        raise ValueError("Original intro transport scratch/reader not authorized")
    results = []
    for index, mode in enumerate(("chapter_wrapper", "book_direct"), start=1):
        work_id = f"BRIntroProbe{index}"
        xml = make_unmodified_intro_osis(
            chapter, original_intro_raw, mode=mode, work_id=work_id
        )
        root = scratch / f"private-intro-{index}"
        if root.exists() or root.is_symlink():
            raise ValueError("Refusing to overwrite existing private intro test")
        dst = root / "modules" / "comments" / "zcom" / work_id
        conf = root / "mods.d" / (work_id + ".conf")
        dst.mkdir(parents=True)
        conf.parent.mkdir()
        (root / "source-private.xml").write_bytes(xml)
        try:
            compile_result = subprocess.run(
                [str(osis2mod_binary), str(dst), str(root / "source-private.xml"),
                 "-z", "z", "-b", "3", "-v", "KJV"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=root, timeout=100, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            results.append({"mode": mode, "status": "COMPILER_UNAVAILABLE_OR_TIMEOUT"})
            continue
        if compile_result.returncode:
            results.append({"mode": mode, "status": "COMPILER_REJECTED_ORIGINAL_I_WRAPPER"})
            continue
        conf.write_text(
            f"[{work_id}]\nDataPath=./modules/comments/zcom/{work_id}\n"
            "ModDrv=zCom\nCompressType=ZIP\nBlockType=CHAPTER\n"
            "SourceType=OSIS\nVersification=KJV\nLang=en\n"
            "Description=Private original intro transport probe only\n",
            encoding="utf-8"
        )
        try:
            reader = subprocess.run(
                [str(native_raw_binary), work_id],
                env=dict(os.environ, SWORD_PATH=str(root)),
                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=70, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            results.append({"mode": mode, "status": "NATIVE_READBACK_UNAVAILABLE"})
            continue
        if reader.returncode or len(reader.stdout) > 15 * 1024 * 1024:
            results.append({"mode": mode, "status": "NATIVE_READBACK_FAILED"})
            continue
        intro, K, top = {}, [], []
        def observe(kind, key, raw):
            if kind == "I":
                intro[key] = raw
            elif kind == "K":
                K.append(key)
            elif kind == "U":
                top.append(key)
        parse_native_raw_corpus(BytesIO(reader.stdout), on_entry=observe)
        case = {
            "mode": mode,
            "status": "TEMPORARY_NATIVE_I_READBACK_NOT_PROVEN_EDITION_PARITY",
            "original_intro_target_key": chapter,
            "original_intro_key_present": chapter in intro,
            "compiled_all_I_key_count": len(intro),
            "compiled_I_key_names": sorted(intro),
            "compiled_numbered_K_count": len(K),
            "compiled_opaque_TOP_count": len(top),
            "source_original_intro_xml_modified": False,
            "source_intro_text_or_scope_approved": False,
            "publication_authorized": False,
        }
        if chapter in intro:
            delta = classify_native_osis_roundtrip_delta(
                original_intro_raw, intro[chapter]
            )
            case.update({
                "source_original_intro_unicode_words_preserved_in_exact_order":
                    delta["word_sequence_relation"] == "EXACT_ORIGINAL_WORD_SEQUENCE",
                "source_original_intro_whitespace_normalized_visible_text_identical":
                    delta["normalized_whitespace_visible_unicode_equal"],
                "source_original_intro_reference_attribute_values_preserved":
                    delta["reference_attribute_values_in_original_document_order_preserved"],
                "source_original_intro_nondiv_attribute_order_preserved":
                    delta["non_div_element_order_and_exact_attribute_values_preserved"],
                "source_original_intro_div_attribute_multiset_preserved":
                    delta["original_div_elements_exact_attribute_multiset_preserved"],
                "compiled_intro_contains_only_additional_div_names":
                    delta["only_div_element_count_added_not_other_element_names"],
                "source_original_intro_visible_word_count":
                    delta["source_original_unicode_word_tokens"],
                "compiled_original_intro_visible_word_count":
                    delta["compiled_unicode_word_tokens"],
            })
        results.append(case)
    return {
        "status": "TWO_ISOLATED_ORIGINAL_I_OSIS_TRANSPORT_EXPERIMENTS_ONLY",
        "original_native_intro_key": chapter,
        "test_only_modes": results,
        "source_intro_bytes_changed": False,
        "original_module_unchanged": True,
        "original_K_I_U_full_parity_proven": False,
        "publication_authorized": False,
    }
