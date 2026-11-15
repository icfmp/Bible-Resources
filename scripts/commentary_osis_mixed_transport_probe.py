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
import zipfile

from lxml import etree
from pilot_preflight import PilotError

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





def probe_native_original_link_identity(
        *, installed_candidate_root: Path, module_id: str,
        inspector_binary: Path, original_numbered: dict[str,bytes],
        provisional_aliases: dict[str,dict]) -> dict:
    """Independently inspect actual libSWORD isLinked (never raw-text equality).

    This is vital for discontinuous annotation: a nonadjacent verse may be
    linked to an earlier authorial unit even if another different unit lies
    between them. Distinct authored units with identical words cannot safely
    be identified by a plain-text hash.
    """
    if (not installed_candidate_root.is_dir() or installed_candidate_root.is_symlink()
            or not inspector_binary.is_file() or inspector_binary.is_symlink()
            or not WORK.fullmatch(module_id) or not provisional_aliases
            or len(provisional_aliases)>3000):
        raise ValueError("Untrusted native link-identity comparison inputs")
    def inspect(master,target):
        try:
            proc=subprocess.run(
                [str(inspector_binary),module_id,"--is-linked",master,target],
                env=dict(os.environ,SWORD_PATH=str(installed_candidate_root)),
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                timeout=8,check=False
            )
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise ValueError("Native SWORD isLinked inspector unavailable") from exc
        expected=f"L\t{master}\t{target}\t"
        if (proc.returncode or len(proc.stdout)>512
                or not proc.stdout.startswith(expected.encode("ascii"))
                or proc.stdout not in (
                    (expected+"1\n").encode("ascii"),
                    (expected+"0\n").encode("ascii"),
                )):
            raise ValueError("Unexpected native SWORD link response")
        return proc.stdout.endswith(b"1\n")
    all_positive=[]
    for target,claim in sorted(provisional_aliases.items()):
        all_positive.append((target,inspect(claim["link_to"],target)))
    # One explicit negative per chapter where a *different authored original*
    # entry exists; do not equate source content hashes with authored identity.
    controls=[]
    tested=set()
    for target,claim in sorted(provisional_aliases.items()):
        master=claim["link_to"]
        chapter=master.rsplit(".",1)[0]
        if chapter in tested:
            continue
        tested.add(chapter)
        alternate=next((
            key for key,raw in sorted(original_numbered.items())
            if key.startswith(chapter+".") and raw!=original_numbered[master]
        ),None)
        if alternate:
            controls.append({
                "chapter":chapter,"first":master,"second":alternate,
                "different_original_authorial_section_was_linked":
                    inspect(master,alternate)
            })
    return {
        "status":"REAL_LIBSWORD_NATIVE_NONADJACENT_LINK_IDENTITY",
        "proposed_key_count":len(provisional_aliases),
        "all_original_master_to_proposed_target_pairs_are_native_linked":
            all(x[1] for x in all_positive),
        "native_linked_alias_count":sum(x[1] for x in all_positive),
        "non_linked_proposed_pairs":[x[0] for x in all_positive if not x[1]],
        "negative_distinct_section_controls":len(controls),
        "all_independently_distinct_section_controls_unlinked":
            all(not x["different_original_authorial_section_was_linked"] for x in controls),
        "linked_discontinuous_sections_reported_without_bridging_gaps":True,
        "source_text_and_xml_never_logged":True,
        "candidate_not_published":True,
    }


def _word_tokens_for_reader_comparison(rendered: bytes) -> list[str]:
    """Decode only private bounded UTF-8 reader output, never log its words."""
    if not isinstance(rendered, bytes) or not 1 <= len(rendered) <= 4*1024*1024:
        raise ValueError("Unbounded reader content in chapter-duplication probe")
    try:
        value = rendered.decode("utf-8")
    except UnicodeError:
        raise ValueError("Independent reader output is not UTF-8") from None
    return re.findall(r"\w+", value.casefold())


def classify_chapter_reader_repetition(master: bytes, chapter: bytes,
                                       *, width: int = 20) -> dict:
    """Count repeated *source prose*, not repeated verse numbers/headings.

    For a definitive result, independently sampled unique source windows
    must all occur the same positive number of times in a chapter rendering.
    Otherwise the result is explicitly inconclusive. The exact words never
    leave this bounded in-memory diagnostic.
    """
    if type(width) is not int or not 12 <= width <= 40:
        raise ValueError("Unreviewed exact-prose window size")
    words = _word_tokens_for_reader_comparison(master)
    in_chapter = _word_tokens_for_reader_comparison(chapter)
    if len(words) < width * 3 or len(in_chapter) > 700_000:
        return {"classification": "INSUFFICIENT_UNIQUE_ORIGINAL_PROSE",
                "reliable_count": None, "unique_master_windows_used": 0}
    offsets = sorted({
        width, max(width, len(words)//3),
        max(width, len(words)*2//3),
        max(width, len(words)-2*width)
    })
    counts = []
    for offset in offsets:
        needle = words[offset:offset+width]
        if len(needle) < width:
            continue
        def occurrences(haystack):
            return sum(haystack[i:i+width] == needle
                       for i in range(len(haystack)-width+1))
        if occurrences(words) != 1:
            continue
        counts.append(occurrences(in_chapter))
    if len(counts) < 2 or any(c != counts[0] for c in counts) or counts[0] == 0:
        return {"classification": "INCONCLUSIVE_CHAPTER_CONTENT_OR_WINDOW_COUNTS",
                "reliable_count": None, "unique_master_windows_used": len(counts)}
    return {
        "classification": (
            "EXACT_COMMENTARY_EXCERPT_APPEARS_ONCE"
            if counts[0] == 1 else "REPEATED_EXACT_COMMENTARY_EXCERPT"
        ),
        "reliable_count": counts[0],
        "unique_master_windows_used": len(counts),
    }


def probe_private_chapter_reader_repetition(
        original_root: Path, candidate_root: Path,
        original_module_id: str, candidate_module_id: str,
        proposed_aliases: dict[str, dict], *, max_chapters: int = 4) -> dict:
    """Compare original and proposed chapter-wide CLI render duplication.

    A native alias is correct as an index entry without proving whole-chapter
    deduplication in the application. Report increases as blockers, never
    erase a truthful source association merely to silence duplicate prose.
    """
    from collections import Counter
    from pilot_subprocess import query, present_key
    if (not original_root.is_dir() or original_root.is_symlink()
            or not candidate_root.is_dir() or candidate_root.is_symlink()
            or not proposed_aliases or not 1 <= max_chapters <= 6):
        raise ValueError("Untrusted private original/candidate chapter probe")
    chapters = {}
    for target, claim in proposed_aliases.items():
        chapter = target.rsplit(".", 1)[0]
        section = claim["link_to"]
        chapters.setdefault(chapter, Counter())[section] += 1
    ranked = sorted(
        chapters, key=lambda c: (-sum(chapters[c].values()), c)
    )[:max_chapters]
    cases = []
    for chapter in ranked:
        master = sorted(chapters[chapter],
                        key=lambda x: (-chapters[chapter][x], x))[0]
        book, number = chapter.rsplit(".", 1)
        _, _, verse = master.split(".")
        passage = f"{book} {number}:{verse}"
        chapter_query = f"{book} {number}"
        old_m, old_master = query(original_module_id, passage, fmt="plain",
                                  root=original_root, timeout=35, limit=512*1024)
        new_m, new_master = query(candidate_module_id, passage, fmt="plain",
                                  root=candidate_root, timeout=35, limit=512*1024)
        old_c, old_chapter = query(original_module_id, chapter_query,
                                    fmt="plain",root=original_root,timeout=35,limit=4*1024*1024)
        new_c, new_chapter = query(candidate_module_id, chapter_query,
                                    fmt="plain",root=candidate_root,timeout=35,limit=4*1024*1024)
        if not all((
            present_key(passage, old_master, old_m),
            present_key(passage, new_master, new_m),
            present_key(chapter_query, old_chapter, old_c),
            present_key(chapter_query, new_chapter, new_c),
        )):
            cases.append({
                "chapter":chapter, "master":master,
                "status":"ONE_OR_MORE_REAL_READER_QUERIES_UNAVAILABLE",
                "original_repetition": None, "proposed_repetition": None
            })
            continue
        old = classify_chapter_reader_repetition(old_master,old_chapter)
        new = classify_chapter_reader_repetition(new_master,new_chapter)
        old_count, new_count = old["reliable_count"],new["reliable_count"]
        delta = (
            "INCONCLUSIVE_NATIVE_CHAPTER_TEXT_PRESENTATION"
            if old_count is None or new_count is None else
            "NEW_ALIAS_CHAPTER_REPETITION_INCREASE"
            if new_count > old_count else
            "NO_INCREASE_IN_CLI_CHAPTER_REPETITION"
        )
        cases.append({
            "chapter":chapter,"master":master,
            "proposed_additional_aliases_for_master":chapters[chapter][master],
            "status":delta,
            "original_repetition":old,
            "proposed_repetition":new,
            "both_original_and_candidate_queried_in_actual_diatheke":True,
        })
    return {
        "status":"GENERIC_NATIVE_COMMENTARY_CLI_CHAPTER_REPEAT_COMPARISON_NOT_GUI_APPROVAL",
        "case_count":len(cases),
        "cases":cases,
        "chapters_with_proven_increased_repeat_count":sum(
            c["status"]=="NEW_ALIAS_CHAPTER_REPETITION_INCREASE" for c in cases
        ),
        "chapter_deduplication_in_Xiphos_or_Bible_verified":False,
        "no_source_text_logged_or_published":True,
        "publication_authorized":False,
    }




def _observe_real_xiphos_full_chapter_excerpt(
        env: dict, chapter: str, master_plain: bytes,
        independent_section_plain: bytes) -> dict:
    """One conservative actual-GTK whole-chapter attempt, no screenshots.

    Requires both a repeated-link section and an independent chapter section
    to be copied from the *same visible GUI selection* before calling a
    single occurrence a meaningful chapter-level dedup observation.
    """
    import time
    from commentary_xiphos_dual_reader import (
        _x11, _main_xiphos_window, _commentary_pane_focus_points,
        _seed_x11_clipboard
    )
    try:
        window = _main_xiphos_window(env)
        if window is None or not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*",chapter):
            raise ValueError("Xiphos whole chapter identity/window not verifiable")
        book, chapter_number = chapter.rsplit(".",1)
        reference=f"{book} {chapter_number}"
        _x11(["xdotool","windowfocus","--sync",window],env)
        for command in (
            ["xdotool","key","--clearmodifiers","ctrl+l"],
            ["xdotool","type","--clearmodifiers","--delay","25",reference],
            ["xdotool","key","Return"],
            ["xdotool","key","--clearmodifiers","alt+c"]
        ):
            _x11(command,env)
        time.sleep(1.5)
        results=[]
        for x,y in _commentary_pane_focus_points(env,window):
            _x11(["xdotool","mousemove",str(x),str(y),"click","1"],env)
            time.sleep(0.6)
            _seed_x11_clipboard(env)
            _x11(["xdotool","key","--clearmodifiers","ctrl+a"],env)
            _x11(["xdotool","key","--clearmodifiers","ctrl+c"],env)
            time.sleep(0.8)
            selection=_x11(["xclip","-selection","clipboard","-o"],env)
            if b"XIPHOS_PRIVATE_CLIPBOARD_SENTINEL_NOT_SOURCE_TEXT" in selection:
                continue
            main=classify_chapter_reader_repetition(master_plain,selection)
            other=classify_chapter_reader_repetition(independent_section_plain,selection)
            results.append({
                "main":main,"independent_section":other,
                "same_real_GTK_clipboard_from_commentary_pane":True,
            })
        for observation in results:
            count=observation["main"]["reliable_count"]
            separate=observation["independent_section"]["reliable_count"]
            if count is not None and separate is not None:
                return {
                    "status": (
                        "XIPHOS_CHAPTER_MULTIPLE_SECTIONS_SEEN_ONCE_EACH"
                        if count == separate == 1 else
                        "XIPHOS_CHAPTER_REPEATED_PROSE_DETECTED"
                        if count > 1 or separate > 1
                        else "INCONCLUSIVE_REAL_GUI_CHAPTER_COPY"
                    ),
                    "linked_section_observed_occurrences":count,
                    "independent_commentary_section_observed_occurrences":separate,
                    "two_original_distinct_section_bodies_visible":True,
                    "source_prose_or_screenshot_uploaded":False,
                }
        return {
            "status":"INCONCLUSIVE_REAL_GUI_CHAPTER_COPY_NOT_WHOLE_CHAPTER",
            "linked_section_observed_occurrences":None,
            "independent_commentary_section_observed_occurrences":None,
            "two_original_distinct_section_bodies_visible":False,
            "source_prose_or_screenshot_uploaded":False,
        }
    except (PilotError, ValueError, UnicodeError) as error:
        # Only exception *class* is logged, never UI/OS error strings
        # that might embed private authorial text.
        return {
            "status":"REAL_GUI_CHAPTER_COPY_UNAVAILABLE",
            "exception_kind":type(error).__name__,
            "linked_section_observed_occurrences":None,
            "independent_commentary_section_observed_occurrences":None,
            "two_original_distinct_section_bodies_visible":False,
            "source_prose_or_screenshot_uploaded":False,
        }


def _probe_private_alias_real_xiphos(root: Path, module_id: str, aliases: dict,
                                    compiled_K: dict[str, bytes]) -> dict:
    """Bounded real-reader experiment; never claim window == rendered passage.

    Reuses the already existing independently verified Bible + Xiphos helper.
    Only metadata/booleans are returned, never commentary words or screenshots.
    """
    from collections import defaultdict
    from commentary_xiphos_dual_reader import (
        verify_and_install_reviewed_bible, _run_real_gui, BIBLE_MODULE
    )
    from pilot_subprocess import query, present_key

    if not aliases or not root.is_dir() or root.is_symlink():
        raise ValueError("Real-reader preview requires a private alias candidate")
    by_master = defaultdict(list)
    for target, claim in aliases.items():
        by_master[claim["link_to"]].append(target)
    # Reuse a scope-neutral selection: one large multi-verse group and two
    # other books. No MHCC-specific hardcoded verse used to pass a test.
    largest = sorted(by_master, key=lambda k: (-len(by_master[k]), k))[0]
    selected = [sorted(by_master[largest])[0]]
    seen_books = {selected[0].split(".", 1)[0]}
    for target in sorted(aliases):
        book = target.split(".", 1)[0]
        if book not in seen_books:
            selected.append(target)
            seen_books.add(book)
        if len(selected) == 3:
            break
    bible = verify_and_install_reviewed_bible(root)
    if bible["module_id"] != BIBLE_MODULE:
        raise ValueError("Private reader Bible verification failed")
    comparisons = {}
    shared_runs = {}
    for key in selected:
        book, chapter, verse = key.split(".")
        passage = f"{book} {chapter}:{verse}"
        master_key = aliases[key]["link_to"]
        mbook, mchapter, mverse = master_key.split(".")
        master_passage = f"{mbook} {mchapter}:{mverse}"
        first_code, alias_plain = query(
            module_id, passage, fmt="plain", root=root, timeout=25,
            limit=256*1024,
        )
        master_code, master_plain = query(
            module_id, master_passage, fmt="plain", root=root, timeout=25,
            limit=256*1024,
        )
        bible_code, bible_plain = query(
            BIBLE_MODULE, passage, fmt="plain", root=root, timeout=25,
            limit=256*1024,
        )
        if (not present_key(passage,alias_plain,first_code)
                or not present_key(master_passage,master_plain,master_code)
                or not present_key(passage,bible_plain,bible_code)):
            raise ValueError("Real independent reader failed to navigate proposed alias")
        master_words = re.findall(r"\w+",master_plain.decode("utf-8").casefold())
        alias_words = re.findall(r"\w+",alias_plain.decode("utf-8").casefold())
        if (not 30 <= len(alias_words) <= 30000
                or not 30 <= len(master_words) <= 30000):
            raise ValueError("Independent alias output is empty or oversized")
        # 25 source words in a row rules out incidental shared scripture
        # references and formatting-only "success".
        window = 25
        master_windows = {
            tuple(master_words[i:i+window])
            for i in range(len(master_words) - window + 1)
        }
        has_shared_source = any(
            tuple(alias_words[i:i+window]) in master_windows
            for i in range(len(alias_words) - window + 1)
        )
        if not has_shared_source:
            raise ValueError("Independent reader alias/master prose does not match")
        shared_runs[passage] = window
        comparisons[passage] = {
            "commentary": alias_plain,
            "bible": bible_plain,
            "commentary_internal": compiled_K[key],
        }
    chapter = largest.rsplit(".",1)[0]
    other_original_section = next((
        key for key,raw in compiled_K.items()
        if key.startswith(chapter+".")
        and raw != compiled_K[largest]
        and key not in aliases
    ),None)
    def chapter_readback(env):
        if other_original_section is None:
            return {"whole_chapter_Xiphos_GTK_proof":{
                "status":"NO_INDEPENDENT_SECTION_WITNESS_IN_CHAPTER",
                "two_original_distinct_section_bodies_visible":False,
                "source_prose_or_screenshot_uploaded":False
            }}
        b,c,v=other_original_section.split(".")
        code,other_plain=query(module_id,f"{b} {c}:{v}",fmt="plain",
                               root=root,timeout=25,limit=256*1024)
        if not present_key(f"{b} {c}:{v}",other_plain,code):
            return {"whole_chapter_Xiphos_GTK_proof":{
                "status":"INDEPENDENT_SECTION_READBACK_UNAVAILABLE",
                "two_original_distinct_section_bodies_visible":False,
                "source_prose_or_screenshot_uploaded":False
            }}
        bm,cm,vm=largest.split(".")
        main_code,main_plain=query(module_id,f"{bm} {cm}:{vm}",fmt="plain",
                                   root=root,timeout=25,limit=256*1024)
        if not present_key(f"{bm} {cm}:{vm}",main_plain,main_code):
            raise ValueError("Master original commentary reader unavailable")
        return {"whole_chapter_Xiphos_GTK_proof":
            _observe_real_xiphos_full_chapter_excerpt(
                env,chapter,main_plain,other_plain
            )}
    gui = _run_real_gui(
        root, comparisons, seconds=6, commentary_module_id=module_id,
        on_gui_ready=chapter_readback
    )
    return {
        "status": "PRIVATE_XIPHOS_REAL_GUI_EXPERIMENT_NOT_PRESENTATION_APPROVAL",
        "sample_count": len(comparisons),
        "sample_keys": sorted(comparisons),
        "diatheke_alias_master_shared_run_minimum": min(shared_runs.values()),
        "real_xiphos_executable_started_and_visible":
            gui["real_xiphos_executable_started_and_visible"],
        "actual_passage_commands_accepted":
            gui["actual_passage_commands_accepted"],
        "commentary_clipboard_match_by_passage":
            gui["commentary_clipboard_match_by_passage"],
        "independent_gui_commentary_excerpt_match_count":
            gui["independent_gui_commentary_excerpt_match_count"],
        "whole_chapter_Xiphos_GTK_proof":
            gui["whole_chapter_Xiphos_GTK_proof"],
        "whole_chapter_commentary_deduplication_proven": False,
        "entire_edition_reader_presentation_approved": False,
        "source_prose_or_screenshot_uploaded": False,
        "published": False,
    }



def verify_private_versioned_commentary_conf_delta(
        published_conf_template: bytes, staged_conf: bytes, *,
        previous_version: str, proposed_version: str,
        installed_native_data_size: int) -> dict:
    """Fail closed if a private SWORD update changes unreviewed metadata.

    Native .conf lineage is checked *byte for byte*, apart from Version,
    compression block type, measured InstallSize and the appended history.
    Inherited source attribution/About/license remain source claims, not
    a curator's independent endorsement of print-edition accuracy.
    This is a staging guard, never editorial or release approval.
    """
    if (not isinstance(published_conf_template, bytes)
            or not isinstance(staged_conf, bytes)
            or not 0 < len(published_conf_template) <= 128*1024
            or not 0 < len(staged_conf) <= 128*1024
            or b"\x00" in published_conf_template or b"\x00" in staged_conf
            or not isinstance(installed_native_data_size, int)
            or isinstance(installed_native_data_size, bool)
            or not 0 < installed_native_data_size <= 64*1024*1024
            or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", previous_version)
            or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", proposed_version)
            or previous_version == proposed_version):
        raise ValueError("Unsafe SWORD commentary metadata comparison")
    try:
        before = published_conf_template.decode("utf-8")
        after = staged_conf.decode("utf-8")
    except UnicodeError:
        raise ValueError("Unreviewed SWORD commentary metadata encoding") from None

    def one(conf: str, name: str) -> str:
        values = re.findall(
            rf"^{re.escape(name)}=([^\r\n]*)$", conf, flags=re.M)
        if len(values) != 1 or not values[0].strip():
            raise ValueError("Missing or ambiguous SWORD commentary metadata")
        return values[0]

    # Exact line-based source fields must be present before staged
    # metadata can be accepted; never replace an upstream licence with CC0.
    for key in ("DistributionLicense", "ModDrv", "SourceType", "DataPath",
                "Versification", "Version", "BlockType", "InstallSize"):
        one(before, key)
        one(after, key)
    if (one(before, "Version") != previous_version
            or one(after, "Version") != proposed_version
            or one(before, "BlockType") not in ("BOOK", "CHAPTER")
            or one(after, "BlockType") != "CHAPTER"
            or not one(before, "InstallSize").isdigit()
            or one(after, "InstallSize") != str(installed_native_data_size)):
        raise ValueError("Incorrect versioned commentary packaging metadata")
    if re.search(rf"^History_{re.escape(proposed_version)}=", before, re.M):
        raise ValueError("Release history already exists in original commentary")
    history = (
        f"\nHistory_{proposed_version}=Index-only section navigation corrections; "
        "original commentary words and source references retained\n"
    )
    if not after.endswith(history):
        raise ValueError("Unreviewed new commentary release history")
    restored = after[:-len(history)]
    replacements = (
        ("Version", one(before, "Version")),
        ("BlockType", one(before, "BlockType")),
        ("InstallSize", one(before, "InstallSize")),
    )
    for key, old_value in replacements:
        restored, n = re.subn(
            rf"^{re.escape(key)}=[^\r\n]*$",
            lambda _: f"{key}={old_value}", restored,
            count=1, flags=re.M)
        if n != 1:
            raise ValueError("Expected original SWORD metadata key missing")
    if restored != before:
        raise ValueError("Unreviewed metadata or upstream provenance altered")
    return {
        "private_metadata_exact_reviewed_delta_only": True,
        "only_changed_original_fields": ["BlockType", "InstallSize", "Version"],
        "only_added_metadata_field": f"History_{proposed_version}",
        "original_distribution_license_textsource_about_and_date_unchanged": True,
        "installed_native_bytes_used_for_install_size": True,
        "original_about_print_claim_is_inherited_not_independently_certified": True,
        "public_release_or_new_revision_date_authorized": False,
    }


def privately_stage_versioned_zcom_zip(
        *, compiler_root: Path, compiled_module_id: str,
        package_module_id: str, previous_version: str, proposed_version: str,
        published_conf_template: bytes, scratch: Path,
        native_raw_binary: Path,
        provisional_index_aliases: dict[str,dict] | None = None,
        test_with_real_xiphos: bool = False) -> dict:
    """Privately package an official-compiler zCom under its curated identity.

    Reuses the *compiled native bytes* without patching them. ZIP is created
    inside an auto-removed research directory, installed independently and
    re-read with released libSWORD. Never uploads, releases or edits the
    published module. This staging is intentionally not a distribution gate.
    """
    allowed_id=re.compile(r"[A-Za-z][A-Za-z0-9_]{0,79}")
    version=re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
    if test_with_real_xiphos and not provisional_index_aliases:
        raise ValueError("Xiphos needs independently source-reviewed alias links")
    if (not allowed_id.fullmatch(compiled_module_id)
            or not allowed_id.fullmatch(package_module_id)
            or compiled_module_id==package_module_id
            or not version.fullmatch(previous_version)
            or not version.fullmatch(proposed_version)
            or proposed_version==previous_version
            or not isinstance(published_conf_template,bytes)
            or len(published_conf_template)>128*1024
            or b"\0" in published_conf_template
            or not scratch.is_dir() or scratch.is_symlink()
            or not native_raw_binary.is_file()
            or native_raw_binary.is_symlink()):
        raise ValueError("Unsafe original commentary private package identity")
    source=compiler_root/"modules"/"comments"/"zcom"/compiled_module_id
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Standard compiler zCom data unavailable")
    files=sorted(source.iterdir(),key=lambda p:p.name)
    if (not 2<=len(files)<=32 or any(
            not p.is_file() or p.is_symlink()
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}",p.name)
            or p.stat().st_size>30*1024*1024 for p in files)):
        raise ValueError("Unreviewed compiler zCom output")
    try: conf=published_conf_template.decode("utf-8")
    except UnicodeError:
        raise ValueError("Unreviewed published SWORD metadata encoding") from None
    if (conf.count(f"[{package_module_id}]")!=1
            or conf.count(f"Version={previous_version}")!=1
            or conf.count("ModDrv=zCom")!=1
            or conf.count("SourceType=OSIS")!=1
            or conf.count("Versification=KJV")!=1
            or len(re.findall(r"^BlockType=(?:BOOK|CHAPTER)$",conf,re.M))!=1):
        raise ValueError("Published reference configuration is not the approved source")
    data_path=re.findall(r"^DataPath=(.*)$",conf,re.M)
    target_path=f"./modules/comments/zcom/{package_module_id.lower()}/"
    if len(data_path)!=1 or data_path[0]!=target_path:
        raise ValueError("Published source configuration has an unexpected native path")
    # -b 3 is the standard compiler's CHAPTER block type. Reusing
    # the published BOOK header would misdescribe the *new* compiled bytes.
    conf=conf.replace(f"Version={previous_version}",f"Version={proposed_version}")
    conf=re.sub(r"^BlockType=(?:BOOK|CHAPTER)$","BlockType=CHAPTER",conf,
                count=1,flags=re.M)
    total_size=sum(p.stat().st_size for p in files)
    if re.search(r"^InstallSize=\d+$",conf,re.M):
        conf=re.sub(r"^InstallSize=\d+$",f"InstallSize={total_size}",
                    conf,count=1,flags=re.M)
    else:
        conf+=f"\nInstallSize={total_size}\n"
    if f"History_{proposed_version}=" in conf:
        raise ValueError("Proposed version already exists in published source history")
    conf+=(
        f"\nHistory_{proposed_version}=Index-only section navigation corrections; "
        "original commentary words and source references retained\n"
    )
    if conf.count(f"Version={proposed_version}")!=1:
        raise ValueError("Staging metadata version collision")
    metadata_guard = verify_private_versioned_commentary_conf_delta(
        published_conf_template, conf.encode("utf-8"),
        previous_version=previous_version, proposed_version=proposed_version,
        installed_native_data_size=total_size)
    members={f"mods.d/{package_module_id.lower()}.conf":conf.encode("utf-8")}
    members.update({
        f"modules/comments/zcom/{package_module_id.lower()}/{p.name}":
        p.read_bytes()
        for p in files
    })
    if sum(map(len,members.values()))>64*1024*1024:
        raise ValueError("Oversize unpublished SWORD package content")
    package=scratch/f"{package_module_id}-{proposed_version}.zip"
    # Distinct HOME parent: two real GTK/Xiphos probes in the same audit
    # must never reuse each other's isolated GUI state.
    installed=scratch/"curated-package-stage"/"isolated-package-install"
    if package.exists() or installed.exists():
        raise ValueError("Refuse to overwrite earlier private SWORD staging")
    def fixed_zip_item(name):
        info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
        info.compress_type=zipfile.ZIP_STORED
        info.create_system=3
        info.external_attr=0o100644<<16
        return info
    with zipfile.ZipFile(package,"w") as archive:
        for name,payload in sorted(members.items()):
            archive.writestr(fixed_zip_item(name),payload)
    installed.parent.mkdir()
    installed.mkdir()
    with zipfile.ZipFile(package) as archive:
        if sorted(archive.namelist())!=sorted(members):
            raise ValueError("Private package entry inventory differs from source")
        for info in archive.infolist():
            if (info.filename not in members or
                    archive.read(info)!=members[info.filename]):
                raise ValueError("Private SWORD package cannot be reproduced")
            dest=installed/info.filename
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(archive.read(info))
    inventories={}
    installed_reader_K={}
    for id_,root in (
            (compiled_module_id,compiler_root),
            (package_module_id,installed)):
        run=subprocess.run(
            [str(native_raw_binary),id_],
            env=dict(os.environ,SWORD_PATH=str(root)),
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            timeout=240,check=False
        )
        if run.returncode or len(run.stdout)>512*1024*1024:
            raise ValueError("Native installed commentary package readback failed")
        observed={"I":{},"K":{},"U":[]}
        def collect(kind,key,raw):
            if kind=="U":observed["U"].append(sha256(raw).digest())
            else:
                observed[kind][key]=sha256(raw).digest()
                if (id_==package_module_id and kind=="K"
                        and test_with_real_xiphos):
                    installed_reader_K[key]=raw
        parse_native_raw_corpus(BytesIO(run.stdout),on_entry=collect)
        inventories[id_]=observed
    before=inventories[compiled_module_id]
    after=inventories[package_module_id]
    if (before!=after or not before["K"]
            or not before["I"] or not before["U"]):
        raise ValueError("Private curated-identity installation changed native source records")
    curated_reader_probe = (
        _probe_private_alias_real_xiphos(
            installed,package_module_id,
            provisional_index_aliases,installed_reader_K
        ) if test_with_real_xiphos else None
    )
    return {
        "private_versioned_curated_module_real_xiphos_selected_verse_probe":
            curated_reader_probe,
        "status":"PRIVATE_VERSIONED_SWORD_ZCOM_ZIP_ISOLATED_INSTALL_PARITY_NOT_PUBLICATION",
        "curated_module_id":package_module_id,
        "proposed_version":proposed_version,
        "source_compiled_module_identity_changed_only_in_package":True,
        "native_compiled_files_copied_without_recompression_or_byte_edits":True,
        "compiled_file_count":len(files),
        "private_conf_metadata_exact_delta_receipt": metadata_guard,
        "staged_package_zip_sha256":sha256(package.read_bytes()).hexdigest(),
        "staged_package_size_bytes":package.stat().st_size,
        "original_native_I_count":len(before["I"]),
        "original_and_alias_native_K_count":len(before["K"]),
        "original_opaque_TOP_count":len(before["U"]),
        "installed_package_I_K_U_raw_bytes_equal_to_private_compiled_source":True,
        "source_annotations_and_words_modified":False,
        "source_sword_zip_or_0_1_0_package_overwritten":False,
        "package_saved_as_public_artifact":False,
        "release_authorized":False,
        "published":False,
    }


def probe_complete_original_transport(
        original_intros: dict[str, bytes],
        original_numbered: dict[str, list[tuple[str, bytes]]],
        original_TOP: list[bytes], *,
        scratch: Path, native_raw_binary: Path,
        osis2mod_binary: str = "osis2mod",
        provisional_index_aliases: dict[str, dict] | None = None,
        test_preview_in_xiphos: bool = False,
        original_stock_sword_root: Path | None = None,
        original_stock_module_id: str = "MHCC",
        native_index_binary: Path | None = None) -> dict:
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
    conf = root / "mods.d" / (module_id.lower() + ".conf")
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
    link_identity = None
    if aliases and native_index_binary is not None:
        if not (indexed_checks and alias_identical and top_exact):
            raise ValueError("Refuse native identity check on changed original content")
        link_identity = probe_native_original_link_identity(
            installed_candidate_root=root, module_id=module_id,
            inspector_binary=native_index_binary,
            original_numbered=original_K, provisional_aliases=aliases
        )
    chapter_repeat = None
    if aliases and original_stock_sword_root is not None:
        if not (indexed_checks and alias_identical and top_exact):
            raise ValueError("Refuse chapter comparison for unreconciled alias source")
        chapter_repeat = probe_private_chapter_reader_repetition(
            original_stock_sword_root, root,
            original_stock_module_id, module_id, aliases
        )
    gui = None
    if test_preview_in_xiphos:
        if not aliases or not (indexed_checks and alias_identical and top_exact):
            raise ValueError("Refuse Xiphos on an unreconciled private preview")
        gui = _probe_private_alias_real_xiphos(
            root, module_id, aliases, rebuilt["K"]
        )
    return {
        **source,
        "private_real_xiphos_alias_navigation_probe": gui,
        "private_original_vs_alias_cli_chapter_repetition_probe": chapter_repeat,
        "private_native_original_and_provisional_alias_link_identity": link_identity,
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
