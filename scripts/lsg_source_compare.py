#!/usr/bin/env python3
"""Audit the actual eBible LSG USFM, USFX and optional OSIS authoring archives.

No normalized source is created. Do not confuse an authoring source archive
with the compiled SWORD module, or a successful XML parse with OSIS approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

from lxml import etree

from pilot_preflight import inspect_archive, PilotError
from guard_osis import ROOT, MAX_SOURCE_BYTES, StructureFailure, inspect as inspect_osis

OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
USFM_ID = re.compile(r"(?m)^\\id\s+(\S+)")
USFM_C = re.compile(r"(?m)^\\c\s+(\d+)")
USFM_V = re.compile(r"(?m)^\\v\s+([0-9]+(?:-[0-9]+)?)\b")
USFM_STRUCTURE = re.compile(r"(?m)^\\(q[0-9]*|p|m|pi[0-9]*|s[0-9]*|cl|d)\b")
REF = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)$")
COMPONENT_NAMES = {"lg", "l", "p", "title", "note", "reference", "hi", "q", "verse", "chapter", "div", "w"}


def read_source_xml(archive_path: Path, *, source_format: str = "osis") -> tuple[bytes, dict]:
    validated = inspect_archive(archive_path, source_kind="authored")
    candidate_names = []
    with zipfile.ZipFile(archive_path) as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            lower = member.filename.casefold()
            if lower.endswith((".xml", ".osis", ".usfx")):
                candidate_names.append(member.filename)
        if source_format == "usfx":
            # eBible USFX archives also contain BookNames, metadata and
            # publication parameter XML: none of those are Scripture sources.
            candidate_names = [name for name in candidate_names
                               if Path(name).name.casefold().endswith("_usfx.xml")]
        elif source_format != "osis":
            raise PilotError("Unreviewed XML source format selector")
        if not candidate_names:
            raise PilotError(f"No actual {source_format} Scripture source in publisher archive")
        if len(candidate_names) != 1:
            raise PilotError(f"Multiple {source_format} source candidates ({len(candidate_names)}): {candidate_names[:20]!r}")
        name = candidate_names[0]
        info = z.getinfo(name)
        if info.file_size > MAX_SOURCE_BYTES:
            raise PilotError("Original authoring XML exceeds reviewed parser size limit")
        source = z.read(info)
    return source, {"path":name,"bytes":len(source),
                     "sha256":hashlib.sha256(source).hexdigest(),
                     "archive_sha256":validated["archive_sha256"],
                     "all_archive_member_count":validated["member_count"]}


def scan_osis(raw: bytes) -> tuple[dict, list]:
    if re.search(rb"<!DOCTYPE\b", raw, re.IGNORECASE):
        raise PilotError("DOCTYPE is forbidden for untrusted authoring source")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    root = etree.fromstring(raw, parser=parser)
    if root.tag != OSIS_NS+"osis":
        raise PilotError(f"Unexpected original XML root {root.tag!r}; not an OSIS document")
    tags = Counter()
    attrs = Counter()
    book_ids = []
    verse_keys = Counter()
    spans = Counter()
    bad_verse_ids = []
    poetry_lines_by_book = Counter()
    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue
        name = etree.QName(elem).localname
        tags[name] += 1
        if name not in COMPONENT_NAMES and len(tags) <= 1000:
            pass
        for key in elem.attrib:
            attrs[etree.QName(key).localname] += 1
        if name == "div" and elem.get("type") == "book":
            book_ids.append(elem.get("osisID"))
        if name == "verse":
            ref = elem.get("osisID") or elem.get("sID")
            if ref:
                for part in ref.split():
                    if REF.fullmatch(part):
                        verse_keys[part] += 1
                    else:
                        bad_verse_ids.append(part[:100])
            if elem.get("eID"):
                spans["verse_end_milestones"] += 1
            if elem.get("sID"):
                spans["verse_start_milestones"] += 1
        if name == "l":
            for ancestor in elem.iterancestors():
                if ancestor.tag == OSIS_NS+"div" and ancestor.get("type") == "book":
                    poetry_lines_by_book[ancestor.get("osisID")] += 1
                    break
    duplicates = sorted(k for k,n in verse_keys.items() if n>1)
    result = {
        "root":etree.QName(root).localname,
        "namespaces":sorted(str(v) for v in root.nsmap.values() if v),
        "root_schema_location":root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"),
        "original_books":book_ids,
        "book_count":len(book_ids),
        "unique_verse_keys":len(verse_keys),
        "verse_openings":sum(verse_keys.values()),
        "duplicate_verse_ids":duplicates[:40],
        "nonstandard_verse_identifiers":bad_verse_ids[:30],
        "source_elements":dict(sorted(tags.items())),
        "source_attribute_names":dict(sorted(attrs.items())),
        "verse_milestones":dict(spans),
        "poetry_line_counts_by_book":dict(sorted(poetry_lines_by_book.items())),
    }
    return result, list(verse_keys)


def scan_usfx(raw: bytes) -> tuple[dict, list[tuple[str,int,int]]]:
    """Read USFX verse openings; USFX is *not* an OSIS XML document."""
    if re.search(rb"<!DOCTYPE\b", raw, re.IGNORECASE):
        raise PilotError("Untrusted authoring XML includes a DOCTYPE")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                            no_network=True,recover=False,huge_tree=False)
    root=etree.fromstring(raw,parser)
    if etree.QName(root).localname!="usfx":
        raise PilotError(f"Unexpected USFX source root: {root.tag!r}")
    books=[]
    per_book={}
    keys=[]
    tags=Counter()
    attributes=Counter()
    bad=[]
    duplicates=[]
    for book in root.iter():
        if not isinstance(book.tag,str) or etree.QName(book).localname!="book":
            continue
        code=book.get("id")
        if not code or code in books:
            raise PilotError(f"Missing or duplicate USFX book ID: {code!r}")
        books.append(code)
        chapter=None
        seen=set()
        for node in book.iter():
            if not isinstance(node.tag,str):
                continue
            kind=etree.QName(node).localname
            tags[kind]+=1
            attributes.update(etree.QName(k).localname for k in node.attrib)
            if kind=="c":
                value=node.get("id")
                if not value or not value.isdigit() or int(value)<1:
                    raise PilotError(f"Unexpected USFX chapter key: {code}:{value}")
                chapter=int(value)
            elif kind=="v":
                value=node.get("id")
                if not chapter or not value:
                    raise PilotError(f"USFX verse before chapter or no key in {code}")
                match=re.fullmatch(r"(\d+)(?:-(\d+))?",value)
                if not match:
                    bad.append(f"{code}.{chapter}.{value}"[:100])
                    continue
                start=int(match[1]);stop=int(match[2] or start)
                if not start or stop<start or stop-start>50:
                    raise PilotError(f"Invalid USFX verse range {code}.{chapter}.{value}")
                for verse in range(start,stop+1):
                    key=(code,chapter,verse)
                    if key in seen:
                        duplicates.append(f"{code}.{chapter}.{verse}")
                    seen.add(key)
                    keys.append(key)
        per_book[code]=len(seen)
    return {
        "root":etree.QName(root).localname,
        "version":root.get("version"),
        "original_books":books,
        "book_count":len(books),
        "verse_openings":len(keys),
        "verse_keys_by_book":per_book,
        "source_elements":dict(sorted(tags.items())),
        "source_attribute_names":dict(sorted(attributes.items())),
        "duplicate_verse_ids":duplicates[:50],
        "nonstandard_verse_identifiers":bad[:50],
        "warning":"Valid XML/USFX structure is not itself a validated CrossWire OSIS source.",
    },keys


def compare_usfm_usfx(usfm:dict,usfx:dict,keys:list[tuple[str,int,int]]) -> dict:
    if len(usfm["_book_order"])!=len(usfx["original_books"]):
        return {"status":"books_do_not_align",
                "usfm_books":len(usfm["_book_order"]),
                "usfx_books":len(usfx["original_books"])}
    if usfm["_book_order"]!=usfx["original_books"]:
        return {"status":"book_order_or_identifier_mismatch",
                "pairs":[{"usfm":a,"usfx":b} for a,b in zip(usfm["_book_order"],usfx["original_books"])]}
    usfx_by_book={}
    for book,chap,verse in keys:
        usfx_by_book.setdefault(book,set()).add((chap,verse))
    differences=[]
    for i,book in enumerate(usfm["_book_order"]):
        left=usfm["_keys"][i]
        right=usfx_by_book.get(book,set())
        if left!=right:
            differences.append({
                "book":book,
                "usfm_only_count":len(left-right),
                "usfx_only_count":len(right-left),
                "usfm_only_first_30":[f"{book}.{a}.{b}" for a,b in sorted(left-right)[:30]],
                "usfx_only_first_30":[f"{book}.{a}.{b}" for a,b in sorted(right-left)[:30]],
            })
    return {
        "status":"verse_key_sets_equal" if not differences else "verse_key_difference_needs_review",
        "books_compared":len(usfm["_book_order"]),
        "books_with_different_verse_keys":differences,
        "limitation":"Same chapter/verse indices do not prove identical text, punctuation, notes or binary fidelity."
    }


def run_usfx(usfx_zip:Path,usfm_zip:Path) -> dict:
    raw,source=read_source_xml(usfx_zip,source_format="usfx")
    usfx,keys=scan_usfx(raw)
    usfm=scan_usfm(usfm_zip)
    return {
        "schema_version":1,
        "resource":"Louis Segond 1910 (eBible fraLSG)",
        "status":"read_only_authoring_source_comparison",
        "usfx_source":source,
        "usfx_structure":usfx,
        "usfm_source":{
            "archive_sha256":usfm["archive_sha256"],
            "book_count":usfm["book_count"],
            "totals":usfm["summary"],
            "books":usfm["books"],
            "duplicate_verse_keys":usfm["duplicate_verse_keys"],
        },
        "usfm_usfx_verse_keys":compare_usfm_usfx(usfm,usfx,keys),
        "source_content_unchanged":True,
        "authoring_source_osis_schema_validated":False,
        "source_vs_compiled_sword_full_text_checked":False,
        "approved_for_publication":False,
        "caveat":"USFX source is compared as USFX, not falsely submitted as OSIS to the CrossWire XSD."
    }


def scan_usfm(archive_path: Path) -> dict:
    validated=inspect_archive(archive_path, source_kind="authored")
    books=[]
    total=Counter()
    duplicates=[]
    sequence_by_book=[]
    source_books=[]
    with zipfile.ZipFile(archive_path) as archive:
        for entry in sorted(archive.infolist(),key=lambda m:m.filename):
            if entry.is_dir() or not entry.filename.casefold().endswith((".sfm",".usfm")):
                continue
            raw=archive.read(entry)
            content=raw.decode("utf-8-sig")
            match=USFM_ID.search(content)
            if not match:
                raise PilotError(f"USFM file missing \\id: {entry.filename}")
            book=match[1]
            source_books.append(book)
            events=re.finditer(r"(?m)^\\(c|v)\s+([0-9]+(?:-[0-9]+)?)",content)
            chapter=None
            verse_set=set()
            summary=Counter()
            for ev in events:
                if ev[1]=="c":
                    chapter=int(ev[2]);summary["chapters"]+=1
                else:
                    if chapter is None:
                        raise PilotError(f"Verse before chapter in {entry.filename}")
                    value=ev[2]
                    if "-" in value:
                        start,end=map(int,value.split("-"))
                        if start> end or end-start>50:
                            raise PilotError(f"Unreviewed USFM verse range {book} {chapter}:{value}")
                        parts=range(start,end+1)
                        summary["verse_ranges"]+=1
                    else:
                        parts=[int(value)]
                    for v in parts:
                        key=(chapter,v)
                        if key in verse_set:
                            duplicates.append(f"{book}.{chapter}.{v}")
                        verse_set.add(key)
                    summary["verse_markers"]+=1
            summary.update({str(k):v for k,v in Counter(USFM_STRUCTURE.findall(content)).items()})
            books.append({"code":book,"file":entry.filename,
                          "chapters":summary["chapters"],
                          "unique_verse_keys":len(verse_set),
                          "verse_ranges":summary["verse_ranges"],
                          "poetry_markers":sum(v for k,v in summary.items() if k.startswith("q")),
                          "paragraph_markers":summary.get("p",0)+summary.get("m",0),
                          "section_headers":sum(v for k,v in summary.items() if k.startswith("s")),
                          "source_sha256":hashlib.sha256(raw).hexdigest()})
            total.update({"chapters":summary["chapters"],
                         "verse_markers":summary["verse_markers"],
                         "verse_keys":len(verse_set),
                         "poetry_markers":books[-1]["poetry_markers"],
                         "paragraph_markers":books[-1]["paragraph_markers"],
                         "section_headers":books[-1]["section_headers"],
                         "verse_ranges":summary["verse_ranges"]})
            sequence_by_book.append(verse_set)
    if len(books)!=66 or len(set(source_books))!=len(books):
        raise PilotError(f"LSG USFM has {len(books)} books; expected exactly 66 unique books")
    return {"archive_sha256":validated["archive_sha256"],
            "books":books,"book_count":len(books),
            "summary":dict(total),
            "duplicate_verse_keys":duplicates[:60],
            "_book_order":source_books,
            "_keys":sequence_by_book}


def compare_originals(usfm:dict,osis:dict,osis_keys:list[str]) -> dict:
    # Independent canonical IDs are verified before comparing any keys.
    if len(usfm["_book_order"])!=len(osis["original_books"]):
        return {"status":"books_do_not_align",
                "detail":"Compare edition/versification and book list before judging missing verses"}
    if len(set(osis["original_books"])) != len(osis["original_books"]):
        return {"status":"duplicate_osis_books"}
    osis_by_book={}
    for ref in osis_keys:
        match=REF.fullmatch(ref)
        if match:
            osis_by_book.setdefault(match[1],set()).add((int(match[2]),int(match[3])))
    results=[]
    for i,(book,osis_book) in enumerate(zip(usfm["_book_order"],osis["original_books"])):
        from_usfm=usfm["_keys"][i]
        from_osis=osis_by_book.get(osis_book,set())
        lost=sorted(from_usfm-from_osis)
        added=sorted(from_osis-from_usfm)
        if lost or added:
            results.append({
                "usfm_book":book,"osis_book":osis_book,
                "usfm_only_count":len(lost),"osis_only_count":len(added),
                "usfm_only_first_20":[f"{osis_book}.{a}.{b}" for a,b in lost[:20]],
                "osis_only_first_20":[f"{osis_book}.{a}.{b}" for a,b in added[:20]],
            })
    return {
        "status":"verse_key_sets_equal" if not results else "verse_key_difference_needs_review",
        "book_order_compared":len(usfm["_book_order"]),
        "book_code_pairs":[{"usfm":u,"osis":o}
                           for u,o in zip(usfm["_book_order"],osis["original_books"])],
        "books_with_different_verse_keys":results,
        "limitations":"USFM and OSIS may be distinct edition revisions; same chapter/verse indices do not prove same text, punctuation, notes or SWORD binary fidelity."
    }


def run(osis_zip: Path, usfm_zip: Path, schema_dir: Path) -> dict:
    raw,source=read_source_xml(osis_zip)
    osis,osis_keys=scan_osis(raw)
    usfm=scan_usfm(usfm_zip)
    comparison=compare_originals(usfm,osis,osis_keys)
    # OSIS source validation is independent of XML parsability. Never
    # relax the reviewed guard to get a green pilot report.
    schema_path=Path(schema_dir)/"osisCore.2.1.1-cw-latest.xsd"
    with tempfile.TemporaryDirectory(prefix="lsg-authored-source-") as tmp:
        original=Path(tmp)/"original.osis.xml"
        original.write_bytes(raw)
        try:
            validation=inspect_osis(original,schema_path)
        except StructureFailure as exc:
            gate={"status":"blocked",
                  "code":exc.code,"line":exc.line,
                  "message":exc.message[:300]}
        else:
            gate={"status":"validated", "schema_sha256":validation["schema_sha256"],
                  "source_sha256":validation["source_sha256"]}
    report={
        "schema_version":1,"resource":"Louis Segond 1910, eBible fraLSG",
        "status":"read_only_source_comparison",
        "osis_source":source,
        "osis_structure":osis,
        "usfm_source":{
            "archive_sha256":usfm["archive_sha256"],
            "book_count":usfm["book_count"],
            "totals":usfm["summary"],
            "books":usfm["books"],
            "duplicate_verse_keys":usfm["duplicate_verse_keys"],
        },
        "usfm_osis_verse_keys":comparison,
        "official_osis_schema_gate":gate,
        "source_content_unchanged":True,
        "source_vs_compiled_sword_full_text_checked":False,
        "approved_for_publication":False,
    }
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--osis-zip",type=Path)
    group.add_argument("--usfx-zip",type=Path)
    p.add_argument("--usfm-zip",type=Path,required=True)
    p.add_argument("--schema-dir",type=Path)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        if args.usfx_zip:
            result=run_usfx(args.usfx_zip,args.usfm_zip)
        elif args.schema_dir:
            result=run(args.osis_zip,args.usfm_zip,args.schema_dir)
        else:
            raise PilotError("Official pinned schema directory required for original OSIS")
        status=0 if result["status"].startswith("read_only_") else 1
    except (OSError,ValueError,zipfile.BadZipFile,etree.XMLSyntaxError) as exc:
        result={"status":"blocked","reason":str(exc),
                "source_content_unchanged":True,"approved_for_publication":False}
        status=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"Publisher authoring source comparison: {result['status']}; {args.report}")
    if status:
        print(result["reason"],file=sys.stderr)
    return status


if __name__=="__main__":
    sys.exit(main())
