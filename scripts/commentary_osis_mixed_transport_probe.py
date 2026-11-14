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



_COVERAGE_FIELDS = (
    "source_keys_present",
    "source_words_preserved_in_exact_order",
    "source_whitespace_normalized_visible_text_identical",
    "original_nondiv_element_order_and_attributes_preserved",
    "original_div_attribute_multiset_preserved",
    "original_reference_attribute_values_preserved",
)


def mixed_transport_checks_pass(*, expected_intro_keys: int,
                                expected_numbered_keys: int,
                                intro_coverage: dict,
                                numbered_coverage: dict,
                                missing_intro_keys: list[str],
                                missing_numbered_keys: list[str],
                                extra_intro_keys: list[str],
                                extra_numbered_keys: list[str]) -> bool:
    """Fail closed when even one original I/K text, attribute or key check fails.

    This proves selected-entry transport only, NOT original raw-byte identity,
    complete edition fidelity, user-facing layout, or TOP-position parity.
    """
    if (type(expected_intro_keys) is not int or expected_intro_keys != 2
            or type(expected_numbered_keys) is not int
            or expected_numbered_keys < 1
            or missing_intro_keys or missing_numbered_keys
            or extra_intro_keys or extra_numbered_keys):
        return False
    return all(
        type(coverage.get(field)) is int and coverage[field] == expected
        for coverage, expected in (
            (intro_coverage, expected_intro_keys),
            (numbered_coverage, expected_numbered_keys),
        )
        for field in _COVERAGE_FIELDS
    )


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
    intro_coverage = summarize(compared_I)
    numbered_coverage = summarize(compared_K)
    missing_I = sorted(set(originals_I) - set(rebuilt_I))
    missing_K = sorted(set(originals_K) - set(rebuilt_K))
    extra_I = sorted(set(rebuilt_I) - set(originals_I))
    extra_K = sorted(set(rebuilt_K) - set(originals_K))
    checks_passed = mixed_transport_checks_pass(
        expected_intro_keys=len(originals_I),
        expected_numbered_keys=len(originals_K),
        intro_coverage=intro_coverage,
        numbered_coverage=numbered_coverage,
        missing_intro_keys=missing_I,
        missing_numbered_keys=missing_K,
        extra_intro_keys=extra_I,
        extra_numbered_keys=extra_K,
    )
    return {
        **source,
        "status":"TEMPORARY_MIXED_ORIGINAL_I_K_REBUILT_NOT_EDITION_PARITY",
        "readback_completed":True,
        "source_original_intro_I_coverage":intro_coverage,
        "source_original_K_coverage":numbered_coverage,
        "original_I_keys_missing_from_compiled":missing_I,
        "original_K_keys_missing_from_compiled":missing_K,
        "unexpected_compiled_I_keys":extra_I,
        "unexpected_compiled_K_keys":extra_K,
        "selected_original_I_K_text_markup_reference_checks_passed":checks_passed,
        "compiled_I_key_count":len(rebuilt_I),
        "compiled_K_key_count":len(rebuilt_K),
        "compiled_TOP_key_count":len(rebuilt_U),
        "raw_source_edition_parity_proven":False,
        "entire_original_native_corpus_preserved":False,
        "published":False,
    }




def validate_private_index_alias_preview(
        original_numbered: dict[str, list[tuple[str, bytes]]],
        proposed_aliases: dict[str, dict]) -> dict[str, list[str]]:
    """Accept only vacant same-chapter aliases to exact unchanged source K keys.

    These are *unapproved* experimental index targets; the caller must not
    present a compilation as an editorial correction or publish it.
    """
    if (not isinstance(proposed_aliases, dict)
            or len(proposed_aliases) > 3000):
        raise ValueError("Unbounded proposed index-only aliases")
    occupied = {
        key: raw
        for chapter in original_numbered.values()
        for key, raw in chapter
    }
    out = {}
    for target, claim in proposed_aliases.items():
        if (not isinstance(target, str) or KEY.fullmatch(target) is None
                or target in occupied or not isinstance(claim, dict)):
            raise ValueError("Untrusted or occupied proposed index target")
        master = claim.get("link_to")
        digest = claim.get("source_raw_sha256")
        if (not isinstance(master, str) or KEY.fullmatch(master) is None
                or master not in occupied or not isinstance(digest, str)
                or digest != sha256(occupied[master]).hexdigest()
                or master.rsplit(".", 1)[0] != target.rsplit(".", 1)[0]
                or int(target.rsplit(".", 1)[1]) > 1000):
            raise ValueError("Alias master absent, changed, or outside native chapter")
        out.setdefault(master, []).append(target)
    return out


def _native_same_chapter_ranges(keys: list[str]) -> str:
    """Produce standard, unambiguous OSIS segments without bridging gaps."""
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("Empty or overlapping native section keys")
    chapter = keys[0].rsplit(".", 1)[0]
    if any(key.rsplit(".", 1)[0] != chapter for key in keys):
        raise ValueError("Commentary section alias crosses a chapter")
    numbers = sorted(int(key.rsplit(".", 1)[1]) for key in keys)
    runs = []
    start = end = numbers[0]
    for number in numbers[1:]:
        if number == end + 1:
            end = number
        else:
            runs.append((start, end))
            start = end = number
    runs.append((start, end))
    return " ".join(
        f"{chapter}.{a}" if a == z else f"{chapter}.{a}-{chapter}.{z}"
        for a, z in runs
    )

def build_complete_original_transport(
        original_intros: dict[str, bytes],
        original_numbered: dict[str, list[tuple[str, bytes]]],
        *, work_id: str,
        provisional_index_aliases: dict[str, dict] | None = None
        ) -> tuple[bytes, dict]:
    """Build *unmodified* original I/K XML into a private whole-module OSIS.

    By default this does not add index targets. Optional, explicitly
    PROVISIONAL alias records may alter only standard annotateRef coverage
    after every master/raw digest and target vacancy is checked; this is
    never a source-scope or publication approval. Original words and XML
    fragments are unchanged. The original two TOP positions are separately
    recompiled/read back by the caller, not manually synthesized.
    """
    chapter_pattern = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*")
    book_pattern = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*")
    if (not WORK.fullmatch(work_id) or not isinstance(original_intros, dict)
            or not isinstance(original_numbered, dict)
            or not 2 <= len(original_intros) <= 10000):
        raise ValueError("Invalid original complete I/K corpus")
    books = {}
    chapters = {}
    for ref, raw in original_intros.items():
        if not isinstance(ref, str) or not isinstance(raw, bytes):
            raise ValueError("Invalid original introduction frame")
        _source_visible_text(raw)
        if book_pattern.fullmatch(ref):
            books[ref] = raw
        elif chapter_pattern.fullmatch(ref):
            chapters[ref] = raw
        else:
            raise ValueError("Unexpected original introduction key")
    if not books or not chapters or len(books) > 100 or len(chapters) > 3000:
        raise ValueError("Unbounded or incomplete original book/chapter inventory")
    if any(chapter.split(".", 1)[0] not in books for chapter in chapters):
        raise ValueError("Original chapter intro without original book intro")
    if any(chapter not in chapters for chapter in original_numbered):
        raise ValueError("Numbered commentary without original chapter intro")
    if not any(original_numbered.values()):
        raise ValueError("Original complete source has no numbered commentary")
    parts = [
        b'<?xml version="1.0" encoding="UTF-8"?>',
        f'<osis xmlns="{OSIS_NS}"><osisText osisIDWork="{work_id}" osisRefWork="Commentary" xml:lang="en" canonical="true">'.encode(),
        (f'<header><work osisWork="{work_id}"><title>Private full original I/K transport</title>'
         f'<identifier type="OSIS">{work_id}</identifier><refSystem>Bible.KJV</refSystem>'
         '</work></header><div type="bookGroup">').encode(),
    ]
    source_alias_claims = provisional_index_aliases or {}
    alias_by_master = validate_private_index_alias_preview(
        original_numbered, source_alias_claims
    )
    original_K_count = 0
    original_group_count = 0
    for book, original_book_intro in books.items():
        parts.extend((f'<div type="book" osisID="{book}">'.encode(),
                      original_book_intro))
        book_chapters = [
            (chapter, original_chapter_intro)
            for chapter, original_chapter_intro in chapters.items()
            if chapter.split(".", 1)[0] == book
        ]
        book_chapters.sort(key=lambda x: int(x[0].rsplit(".", 1)[1]))
        for chapter, original_chapter_intro in book_chapters:
            parts.extend((f'<div type="chapter" osisID="{chapter}">'.encode(),
                          original_chapter_intro))
            groups = []
            last_verse = 0
            seen_verses = set()
            for ref, raw in original_numbered.get(chapter, ()):
                if not isinstance(ref, str) or KEY.fullmatch(ref) is None:
                    raise ValueError("Invalid original numbered verse identity")
                if ref.rsplit(".", 1)[0] != chapter or not isinstance(raw, bytes):
                    raise ValueError("Original verse is outside its chapter")
                verse = int(ref.rsplit(".", 1)[1])
                if verse <= last_verse or verse in seen_verses:
                    raise ValueError("Nonmonotonic or duplicate native verse")
                _source_visible_text(raw)
                digest = sha256(raw).digest()
                if groups and groups[-1]["digest"] == digest and groups[-1]["end"] + 1 == verse:
                    groups[-1]["end"] = verse
                    groups[-1]["original_keys"].append(ref)
                else:
                    groups.append({"start": verse, "end": verse, "digest": digest,
                                   "raw": raw, "original_keys": [ref]})
                last_verse = verse
                seen_verses.add(verse)
                original_K_count += 1
            for group in groups:
                start = f"{chapter}.{group['start']}"
                end = f"{chapter}.{group['end']}"
                extras = [
                    alias for original_key in group["original_keys"]
                    for alias in alias_by_master.get(original_key, ())
                ]
                target = _native_same_chapter_ranges(
                    group["original_keys"] + extras
                )
                parts.extend((
                    f'<div type="section" annotateType="commentary" annotateRef="{target}">'.encode(),
                    group["raw"], b"</div>"
                ))
            original_group_count += len(groups)
            parts.append(b"</div>")
        parts.append(b"</div>")
    parts.extend((b"</div>", b"</osisText>", b"</osis>"))
    xml = b"".join(parts)
    if len(xml) > 512 * 1024 * 1024:
        raise ValueError("Original full OSIS XML exceeds safety bound")
    try:
        etree.fromstring(xml, parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Unmodified whole-original OSIS is not strict XML") from None
    return xml, {
        "status": "COMPLETE_ORIGINAL_I_K_WRAPPED_FOR_PRIVATE_REBUILD_NOT_APPROVAL",
        "source_book_intro_count": len(books),
        "source_chapter_intro_count": len(chapters),
        "source_numbered_key_count": original_K_count,
        "source_numbered_group_count": original_group_count,
        "provisional_index_alias_count": len(source_alias_claims),
        "provisional_index_aliases_not_editorially_approved": True,
        "original_I_K_raw_markup_not_rewritten": True,
        "original_TOP_positions_not_yet_reconstructed": True,
        "original_source_published": False,
    }


def probe_complete_original_transport(
        original_intros: dict[str, bytes],
        original_numbered: dict[str, list[tuple[str, bytes]]],
        original_TOP: list[bytes], *,
        scratch: Path, native_raw_binary: Path,
        osis2mod_binary: str = "osis2mod",
        provisional_index_aliases: dict[str, dict] | None = None) -> dict:
    """Attempt full private SWORD readback and compare EVERY original native key.

    This is diagnostic and cannot authorize a release. TOP is separately
    reconciled and never silently omitted merely because it contains no words.
    """
    if (not scratch.is_dir() or scratch.is_symlink()
            or not native_raw_binary.is_file() or native_raw_binary.is_symlink()
            or len(original_TOP) > 10 or not all(isinstance(x, bytes) for x in original_TOP)):
        raise ValueError("Untrusted complete original transport test input")
    aliases = provisional_index_aliases or {}
    validate_private_index_alias_preview(original_numbered, aliases)
    module_id = "BRIndexProbe" if aliases else "BRFullProbe"
    xml, source = build_complete_original_transport(
        original_intros, original_numbered, work_id=module_id,
        provisional_index_aliases=aliases
    )
    root = scratch / "complete-original-private-candidate"
    if root.exists() or root.is_symlink():
        raise ValueError("Refuse to overwrite private complete source candidate")
    data = root / "modules" / "comments" / "zcom" / module_id
    conf = root / "mods.d" / (module_id + ".conf")
    data.mkdir(parents=True)
    conf.parent.mkdir()
    (root / "source-original-private.osis.xml").write_bytes(xml)
    try:
        run = subprocess.run([
            str(osis2mod_binary), str(data),
            str(root / "source-original-private.osis.xml"),
            "-z", "z", "-b", "3", "-v", "KJV"
        ], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
           timeout=360, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {**source, "status": "COMPLETE_ORIGINAL_COMPILER_UNAVAILABLE",
                "readback_completed": False, "published": False}
    if run.returncode:
        return {**source, "status": "COMPLETE_ORIGINAL_COMPILER_REJECTED",
                "readback_completed": False, "published": False}
    conf.write_text(
        f"[{module_id}]\nDataPath=./modules/comments/zcom/{module_id}\n"
        "ModDrv=zCom\nCompressType=ZIP\nBlockType=CHAPTER\n"
        "SourceType=OSIS\nVersification=KJV\nLang=en\n"
        "Description=Private whole-original text transport only\n",
        encoding="utf-8"
    )
    try:
        scan = subprocess.run(
            [str(native_raw_binary), module_id],
            cwd=root, env=dict(os.environ, SWORD_PATH=str(root)),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=300, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return {**source, "status": "COMPLETE_ORIGINAL_NATIVE_READBACK_UNAVAILABLE",
                "readback_completed": False, "published": False}
    if scan.returncode or len(scan.stdout) > 512 * 1024 * 1024:
        return {**source, "status": "COMPLETE_ORIGINAL_NATIVE_READBACK_FAILED",
                "readback_completed": False, "published": False}
    rebuilt = {"I": {}, "K": {}, "U": []}
    def collect(kind, key, raw):
        if kind == "U":
            rebuilt["U"].append(raw)
        else:
            rebuilt[kind][key] = raw
    parse_native_raw_corpus(BytesIO(scan.stdout), on_entry=collect)
    original_K = {
        key: raw
        for chapter in original_numbered.values()
        for key, raw in chapter
    }
    original_I = original_intros
    absent_I = sorted(set(original_I) - set(rebuilt["I"]))
    absent_K = sorted(set(original_K) - set(rebuilt["K"]))
    extra_I = sorted(set(rebuilt["I"]) - set(original_I))
    extra_K = sorted(set(rebuilt["K"]) - set(original_K))
    cache = {}
    summaries = {}
    names = (
        ("source_keys_present", None),
        ("source_words_preserved_in_exact_order", "word_sequence_relation"),
        ("source_whitespace_normalized_visible_text_identical", "normalized_whitespace_visible_unicode_equal"),
        ("original_nondiv_element_order_and_attributes_preserved", "non_div_element_order_and_exact_attribute_values_preserved"),
        ("original_div_attribute_multiset_preserved", "original_div_elements_exact_attribute_multiset_preserved"),
        ("original_reference_attribute_values_preserved", "reference_attribute_values_in_original_document_order_preserved"),
    )
    for kind, originals in (("I", original_I), ("K", original_K)):
        counts = dict.fromkeys((name for name, _ in names), 0)
        for key, raw in originals.items():
            compiled = rebuilt[kind].get(key)
            if compiled is None:
                continue
            counts["source_keys_present"] += 1
            identity = (sha256(raw).digest(), sha256(compiled).digest())
            delta = cache.get(identity)
            if delta is None:
                delta = classify_native_osis_roundtrip_delta(raw, compiled)
                cache[identity] = delta
            for name, field in names[1:]:
                passed = (
                    delta[field] == "EXACT_ORIGINAL_WORD_SEQUENCE"
                    if field == "word_sequence_relation" else delta[field] is True
                )
                counts[name] += int(passed)
        summaries[kind] = counts
    def complete(kind, original):
        return all(summaries[kind][name] == len(original) for name, _ in names)
    indexed_checks = (
        not any((absent_I, absent_K, extra_I))
        and set(extra_K) == set(aliases)
        and complete("I", original_I) and complete("K", original_K)
    )
    alias_identical = (
        set(extra_K) == set(aliases)
        and all(
            rebuilt["K"].get(target) is not None
            and rebuilt["K"].get(target) == rebuilt["K"].get(claim["link_to"])
            for target, claim in aliases.items()
        )
    )
    top_exact = (
        len(original_TOP) == len(rebuilt["U"])
        and all(a == b for a, b in zip(original_TOP, rebuilt["U"]))
    )
    return {
        **source,
        "status": "COMPLETE_ORIGINAL_PRIVATE_I_K_U_COMPILED_READBACK_NOT_APPROVAL",
        "readback_completed": True,
        "source_intro_I_coverage": summaries["I"],
        "source_numbered_K_coverage": summaries["K"],
        "missing_I_count": len(absent_I),
        "missing_K_count": len(absent_K),
        "extra_I_count": len(extra_I),
        "extra_K_count": len(extra_K),
        "missing_I_first_ten": absent_I[:10],
        "missing_K_first_ten": absent_K[:10],
        "extra_I_first_ten": extra_I[:10],
        "extra_K_first_ten": extra_K[:10],
        "planned_extra_index_keys": len(aliases),
        "all_proposed_new_aliases_same_compiled_raw_as_original_master": alias_identical,
        "proposed_aliases_have_no_independent_editorial_approval": True,
        "source_TOP_count": len(original_TOP),
        "compiled_TOP_count": len(rebuilt["U"]),
        "all_original_TOP_positions_exact_raw_bytes": top_exact,
        "original_indexed_I_K_text_markup_reference_checks_passed": indexed_checks,
        "full_original_K_I_U_native_entry_parity_proven":
            indexed_checks and top_exact and alias_identical,
        "original_raw_entry_bytes_all_identical": False,
        "historical_print_edition_parity_proven": False,
        "reader_layout_parity_proven": False,
        "corrections_or_publication_authorized": False,
        "published": False,
    }
