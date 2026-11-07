#!/usr/bin/env python3
"""Compare scoped SWORD chapter output against its eBible USFX authored text.

Conservative diagnostic only. It never rewrites a Bible verse, fabricates
missing keys, or declares blank verses absent merely because extraction failed.
It explicitly separates text fidelity from punctuation/whitespace presentation
and from annotations/versification checks.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import unicodedata
import zipfile
from lxml import etree

from pilot_preflight import PilotError,inspect_archive
from pilot_subprocess import query,present_key
from lsg_source_compare import read_source_xml,scan_usfx

# Reviewed sample coverage, not a claim to scan all Bible verses.
SAMPLES = {
    "GEN":("Gen",[1]),
    "PSA":("Ps",[23,119]),
    "MAT":("Matt",[18]),
    "MRK":("Mark",[16]),
    "JHN":("John",[5]),
    "ACT":("Acts",[8]),
    "ROM":("Rom",[8]),
    "REV":("Rev",[22]),
}
BOOK_ALIASES_PATH = Path(__file__).resolve().parents[1] / "config/diatheke-usfm-book-aliases.json"

def chapter_plan(all_keys, *, full: bool) -> dict[str,tuple[str,list[int]]]:
    if not full:
        return SAMPLES
    config=json.loads(BOOK_ALIASES_PATH.read_text(encoding="utf-8"))
    aliases=config.get("aliases")
    if config.get("schema_version")!=1 or not isinstance(aliases,dict) or len(aliases)!=66:
        raise PilotError("Unreviewed 66-book SWORD query alias table")
    found=defaultdict(set)
    for code,chapter,verse in all_keys:
        if code not in aliases:
            raise PilotError(f"Unknown USFM-to-SWORD book alias: {code}")
        found[code].add(chapter)
    if set(found)!=set(aliases):
        raise PilotError("Publisher USFX book list changed; do not infer omitted books")
    return {code:(aliases[code],sorted(chapters))
            for code,chapters in found.items()}


HEADER = re.compile(r"(?m)^(?P<book>[1-4]?[A-Za-z][A-Za-z0-9 .'-]{0,75}) (?P<chapter>\d+):(?P<verse>\d+):[ \t]*")
FOOTER = re.compile(r"\n\([A-Za-z][A-Za-z0-9_]*\)\s*\Z")
# These are original authoring *apparatus*, not part of a verse's canonical
# spoken text. They stay in the original USFX archive and must be checked
# separately for preservation in the compiled SWORD module. In Acts 8:1,
# eBible places chapter/section headings and cross-reference headings after
# the first verse marker; blindly joining all XML text yielded a false alarm.
NON_VERSE_TEXT_ELEMENTS={"x","f","fig","s","r","toc","h","id"}
# USFX represents USFM section references such as \r in a generic
# <p sfm="r" style="r">, not in a separate <r> element. Preserve those
# paragraphs as apparatus, never append them to adjacent verse words.
NON_VERSE_PARAGRAPH_STYLES={"r","s","s1","s2","s3","s4","sr","h","toc1","toc2","toc3"}


def plain(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC",value).split())


def hash_text(value:str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def explain_wrapper(reference_text: str, sword_text: str) -> str | None:
    """Only match an exact complete *visual* wrapper; never normalize arbitrary *.

    This is diagnostic equivalence, not authorization to mutate original
    Scripture, metadata or compiled SWORD bytes.
    """
    if reference_text and "*" not in reference_text and sword_text == "* " + reference_text + " *":
        return "sword_balanced_asterisk_emphasis"
    return None


def usfx_text_by_verse(source:bytes, *, filter_books: set[str]) -> tuple[dict, dict]:
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                            no_network=True,recover=False,huge_tree=False)
    doc=etree.fromstring(source,parser=parser)
    if etree.QName(doc).localname!="usfx":
        raise PilotError("Expected verified eBible USFX document, not OSIS")
    result={}
    features={}
    for book in doc.iter():
        if not isinstance(book.tag,str) or etree.QName(book).localname!="book":
            continue
        code=book.get("id")
        if code not in filter_books: continue
        chapter=None
        current=None
        chunks={}
        counts=Counter()
        keys=set()
        def walk(node):
            nonlocal chapter,current
            name=etree.QName(node).localname
            if name=="c":
                try:
                    chapter=int(node.get("id"))
                except (ValueError,TypeError):
                    raise PilotError(f"Unexpected chapter marker in USFX book {code}")
            if name=="v":
                if chapter is None or not node.get("id") or not node.get("id").isdigit():
                    raise PilotError(f"Unreviewed USFX verse format in {code}")
                key=(code,chapter,int(node.get("id")))
                if key in chunks:
                    raise PilotError(f"Duplicate USFX verse opening: {key}")
                current=key
                chunks[key]=[]
                keys.add(key)
            if name=="ve":
                current=None
            if name in {"w","x","q","p","s","d","note","reference"} and current:
                counts[(current,name)]+=1
            skip=(name in NON_VERSE_TEXT_ELEMENTS or
                  (name=="p" and (node.get("sfm") or node.get("style")) in NON_VERSE_PARAGRAPH_STYLES))
            if not skip and current is not None and node.text:
                chunks[current].append(node.text)
            if not skip:
                for child in node:
                    walk(child)
                    if current is not None and child.tail:
                        chunks[current].append(child.tail)
            # Within a note, ignore both its text and descendants but not
            # its own *tail*, which is handled by the parent element.
        walk(book)
        for key,value in chunks.items():
            result[key]=plain("".join(value))
            features[key]={name:counts[(key,name)] for name in ("w","x","q","p","s","d")}
    return result,features


def parse_sword_chapter(data:bytes, expected_chapter:int, module_id:str) -> dict[int,str]:
    if not data.strip() or not data.decode("utf-8",errors="replace"):
        raise PilotError("Empty SWORD chapter text")
    decoded=data.decode("utf-8")
    decoded=FOOTER.sub("",decoded)
    matches=list(HEADER.finditer(decoded))
    if not matches:
        raise PilotError("SWORD output has no per-verse headings; cannot compare this chapter")
    if decoded[:matches[0].start()].strip():
        raise PilotError("Unexpected non-verse text before SWORD first verse")
    verses={}
    for i,match in enumerate(matches):
        if int(match.group("chapter"))!=expected_chapter:
            raise PilotError(f"Unexpected SWORD chapter {match.group('chapter')}")
        verse=int(match.group("verse"))
        if verse in verses:
            raise PilotError(f"Duplicate SWORD verse printed in chapter {expected_chapter}:{verse}")
        end=matches[i+1].start() if i+1<len(matches) else len(decoded)
        verses[verse]=plain(decoded[match.end():end])
    return verses


def run(sword_archive:Path,usfx_archive:Path,*,diatheke="diatheke",full:bool=False) -> dict:
    inspected=inspect_archive(sword_archive,source_kind="sword",
                                expected_module_id="fraLSG1910eb",
                                expected_category="bible")
    if inspected["sword_conf"]["versification"]!="NRSV":
        raise PilotError("LSG SWORD v11n changed; must review sample reference mapping")
    raw,source_meta=read_source_xml(usfx_archive,source_format="usfx")
    usfx_structure,all_keys=scan_usfx(raw)
    planned=chapter_plan(all_keys,full=full)
    authored,authored_features=usfx_text_by_verse(raw,filter_books=set(planned))
    chapters=[]
    totals=Counter()
    differences=[]
    books_text={}
    display_wrappers=[]
    with tempfile.TemporaryDirectory(prefix="bible-lsg-sword-source-") as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(sword_archive) as source_zip:
            for item in inspected["members"]:
                name=item["name"]
                if name.endswith("/"): continue
                dest=root/PurePosixPath(name)
                if not dest.resolve().is_relative_to(root.resolve()):
                    raise PilotError("Extracted SWORD archive path escapes temporary directory")
                dest.parent.mkdir(parents=True,exist_ok=True)
                with source_zip.open(name) as inp,dest.open("xb") as out:
                    shutil.copyfileobj(inp,out,length=262144)
        for code,(alias,numbers) in planned.items():
            source_parts=[]
            sword_parts=[]
            sword_parts_without_exact_wrappers=[]
            for chapter in numbers:
                ref=f"{alias} {chapter}"
                ret,body=query("fraLSG1910eb",ref,fmt="plain",root=root,exe=diatheke)
                if not present_key(ref,body,ret):
                    raise PilotError(f"SWORD chapter cannot be read: {ref}")
                sword=parse_sword_chapter(body,chapter,"fraLSG1910eb")
                expected={v:text for (b,c,v),text in authored.items()
                          if b==code and c==chapter}
                source_parts.extend(expected[v] for v in sorted(expected))
                sword_parts.extend(sword[v] for v in sorted(sword))
                for v in sorted(sword):
                    reference_text = expected.get(v)
                    applied = explain_wrapper(reference_text, sword[v]) if reference_text is not None else None
                    if applied:
                        display_wrappers.append({
                            "reference":f"{code}.{chapter}.{v}",
                            "classification":applied,
                        })
                        sword_parts_without_exact_wrappers.append(reference_text)
                    else:
                        sword_parts_without_exact_wrappers.append(sword[v])
                missing=sorted(set(expected)-set(sword))
                extra=sorted(set(sword)-set(expected))
                common=sorted(set(expected)&set(sword))
                equal=[v for v in common if expected[v]==sword[v]]
                altered=[v for v in common if expected[v]!=sword[v]]
                for verse in altered:
                    if len(differences)>=60:break
                    left,right=expected[verse],sword[verse]
                    differences.append({
                        "reference":f"{code}.{chapter}.{verse}",
                        "source_characters":len(left),
                        "sword_characters":len(right),
                        "source_normalized_sha256":hash_text(left),
                        "sword_normalized_sha256":hash_text(right),
                        "editorial_decision":"not_made",
                    })
                totals.update({"chapters":1,"verses_source":len(expected),
                               "verses_sword":len(sword),
                               "verse_keys_missing_in_sword":len(missing),
                               "verse_keys_unexpected_in_sword":len(extra),
                               "normalized_text_equal":len(equal),
                               "normalized_text_different":len(altered)})
                chapters.append({
                    "source_book":code,"source_chapter":chapter,
                    "sword_key":ref,
                    "verses_source":len(expected),
                    "verses_sword":len(sword),
                    "identical_normalized_text":len(equal),
                    "different_normalized_text":len(altered),
                    "source_only_keys":[f"{code}.{chapter}.{v}" for v in missing[:25]],
                    "sword_only_keys":[f"{code}.{chapter}.{v}" for v in extra[:25]],
                    "source_word_annotations":sum(authored_features.get((code,chapter,v),{}).get("w",0)
                                                  for v in expected),
                    "source_cross_reference_annotations":sum(authored_features.get((code,chapter,v),{}).get("x",0)
                                                             for v in expected),
                })
            full_source=plain(" ".join(source_parts))
            full_sword=plain(" ".join(sword_parts))
            full_sword_visual=plain(" ".join(sword_parts_without_exact_wrappers))
            books_text[code]={
                "source_normalized_characters":len(full_source),
                "sword_normalized_characters":len(full_sword),
                "text_equal_when_verse_boundaries_ignored":full_source==full_sword,
                "text_equal_after_verified_display_wrappers_removed":full_source==full_sword_visual,
                "source_normalized_sha256":hash_text(full_source),
                "sword_normalized_sha256":hash_text(full_sword),
                "sword_display_wrapper_stripped_sha256":hash_text(full_sword_visual),
                "interpretation":"Text equality is separate from reference/verse index correctness. Headings, notes and other USFX apparatus are checked separately.",
            }
    return {
        "schema_version":1,"status":("full_chapter_text_scan_completed_not_published"
                                           if full else "sample_comparison_requires_review"),
        "source":"eBible fraLSG USFX (original)",
        "source_xml_sha256":source_meta["sha256"],
        "source_archive_sha256":source_meta["archive_sha256"],
        "sword_module":"fraLSG1910eb",
        "sword_archive_sha256":inspected["archive_sha256"],
        "sword_versification":"NRSV",
        "authored_verse_keys_all_books":len(all_keys),
        "sample_totals":dict(totals),
        "sample_chapters":chapters,
        "book_content_checks":books_text,
        "books_with_identical_continuous_scripture_text":
            sum(item["text_equal_when_verse_boundaries_ignored"] for item in books_text.values()),
        "books_with_equivalent_continuous_scripture_text_after_verified_display_wrappers":
            sum(item["text_equal_after_verified_display_wrappers_removed"] for item in books_text.values()),
        "verified_exact_sword_display_wrappers":len(display_wrappers),
        "display_wrapper_examples":display_wrappers[:80],
        "first_text_differences":differences,
        "source_unmodified":True,
        "sword_unmodified":True,
        "all_original_chapters_scanned":full and totals["chapters"]==1189 and totals["verses_source"]==len(all_keys),
        "source_to_sword_reference_numbers_exactly_match":
            totals["verse_keys_missing_in_sword"]==0 and totals["verse_keys_unexpected_in_sword"]==0,
        "annotations_compared_to_sword":False,
        "published":False,
        "notes":[
            "Text is compared after NFC and whitespace collapsing; raw punctuation remains significant. Verified balanced asterisk wrappers are classified as display-only and source + SWORD digests retained.",
            "USFX headings, section references, footnotes and apparatus are retained in the source but excluded from plain-verse word comparison; their compiled preservation is audited separately.",
            "A mismatch is a diagnostic, not permission to edit or relocate Scripture.",
        ],
    }


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sword-zip",type=Path,required=True)
    p.add_argument("--usfx-zip",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--full",action="store_true",help="Run all 66 books and all original source chapters")
    args=p.parse_args(argv)
    try:
        result=run(args.sword_zip,args.usfx_zip,full=args.full)
        status=0
    except (OSError,ValueError,zipfile.BadZipFile,etree.XMLSyntaxError) as exc:
        result={"status":"blocked","reason":str(exc),"published":False}
        status=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                           encoding="utf-8")
    print("Source-vs-SWORD chapter comparison:",result["status"])
    if status:print(result["reason"])
    return status


if __name__=="__main__":
    raise SystemExit(main())
