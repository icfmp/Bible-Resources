#!/usr/bin/env python3
"""Temporary source-linked modern commentary OSIS *candidate* preview.

Generic for any independently pinned chapter/metadata pair. The input is
trusted original *compiled* native SWORD data read in isolated storage. Keep
all original reference attributes PRIVATE until inserting them into this
temporary, unshipped derivative. The output is NOT an accepted translation:
no independent semantic signoff, no original print-edition authority and no
authorization to publish. Source-introduction placement and original outline
semantics are explicitly reported as provisional.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

from commentary_modern_draft_osis_preview import generate,NS
from commentary_modern_reference_gate import SourceReferenceGate
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

_REF_MARKER = re.compile(r"^[^\x00-\x1f]+$")
_XML_REF = f"{{{NS}}}reference"


def _inject_reference_at_exact_marker(section: ET.Element, *, marker: str,
                                      literal_osisref: str) -> None:
    """Retain actual original osisRef: no canonical target construction."""
    if not marker or not _REF_MARKER.fullmatch(marker) or not literal_osisref:
        raise ValueError("Invalid source link marker or original literal osisRef")
    matches=[]
    for para in section.findall(f"{{{NS}}}p"):
        def visit(parent):
            if parent.text and marker in parent.text:
                matches.extend([("text",parent,None)]*parent.text.count(marker))
            for i,child in enumerate(parent):
                visit(child)
                if child.tail and marker in child.tail:
                    matches.extend([("tail",parent,i)]*child.tail.count(marker))
        visit(para)
    if len(matches)!=1:
        raise ValueError("Source reference marker must occur exactly once in its own section")
    kind,parent,index=matches[0]
    ref=ET.Element(_XML_REF,{"osisRef":literal_osisref})
    ref.text=marker
    if kind=="text":
        before,after=parent.text.split(marker,1)
        parent.text=before
        ref.tail=after
        parent.insert(0,ref)
    else:
        child=parent[index]
        before,after=child.tail.split(marker,1)
        child.tail=before
        ref.tail=after
        parent.insert(index+1,ref)


def read_book_intro_candidate(path: Path, *, book: str,
                              source_zip_sha: str,
                              source_corpus_sha: str) -> list[str]:
    raw=path.read_text(encoding="utf-8")
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise ValueError("Separate book introduction has no valid frontmatter")
    header,body=raw[4:].split("\n---\n",1)
    fields={}
    for line in header.splitlines():
        if not line.strip():
            continue
        if ": " not in line or line.count('": "')>0:
            raise ValueError("Malformed book introduction field")
        key,value=line.split(": ",1)
        fields[key]=value.strip('"')
    if (fields.get("book_osis")!=book
            or fields.get("status")!="PRODUCTION CANDIDATE — NOT VALIDATED"
            or fields.get("source_zip_sha256")!=source_zip_sha
            or fields.get("source_native_corpus_sha256")!=source_corpus_sha):
        raise ValueError("Book intro candidate does not match SHA-pinned source")
    if "\n---\n" not in body:
        raise ValueError("Separate book introduction lacks commentary/review boundary")
    prose=body.split("\n---\n",1)[0]
    lines=prose.splitlines()
    if not lines or not any(line.startswith("# ") for line in lines):
        raise ValueError("Book intro lacks its own heading")
    paras=[p.strip().replace("\n"," ") for p in re.split(r"\n\s*\n",prose) if p.strip()]
    paras=[p for p in paras if not p.startswith("# ")]
    if not paras or sum(len(p.split()) for p in paras)<30:
        raise ValueError("Empty/truncated modern book intro")
    return paras


def _source_map_ledger(raw: dict) -> dict:
    scope=raw.get("scope")
    units=raw.get("sections")
    if not isinstance(scope,str) or "." not in scope or not isinstance(units,list) or not units:
        raise ValueError("Invalid source-native chapter/section mapping")
    return {
        "package_sha256":raw["published_zip_sha256"],
        "whole_native_source_sha256":raw["verified_entire_native_corpus_sha256"],
        "semantic_translation_review_approved":False,
        "chapters":{
            scope:{"units":[{"native_keys":u["native_keys"],
                             "raw_sha256":u["source_sha256"]}
                            for u in units]}
        }
    }


def build_verified_preview(*, root: Path, source_map: dict, expected_refs: dict,
                           gate: SourceReferenceGate, complete_raw_report: dict,
                           candidate_book_intro: Path, temp_id: str):
    """Return private disposable OSIS and review receipt, never source XML."""
    literal=gate.exact_source_link_literals_after_verified_source(complete_raw_report)
    intro_proof=gate.report(complete_raw_report)
    if (intro_proof["original_book_intro_and_outline_owned_by_first_numbered_K_attested"] is not True
            or not gate.intros_seen
            or any(row["source_visible_word_count"]!=0 for row in gate.intros_seen.values())):
        raise ValueError("Do not relocate original book introduction without first-K ownership and empty original I placeholders")
    ledger=_source_map_ledger(source_map)
    osis_bytes,report=generate(root,ledger,work_id=temp_id,include_candidates=True)
    doc=ET.fromstring(osis_bytes)
    chapters=doc.findall(f".//{{{NS}}}chapter")
    if len(chapters)!=1 or chapters[0].get("osisID")!=source_map["scope"]:
        raise ValueError("Missing or wrong uniquely bounded candidate chapter")
    chapter=chapters[0]
    sections=chapter.findall(f"{{{NS}}}div[@annotateType='commentary']")
    expected_units=source_map["sections"]
    if len(sections)!=len(expected_units):
        raise ValueError("Original source sections not preserved")
    linked=0
    for section,unit in zip(sections,expected_units):
        key=unit["first_key"]
        if key not in literal or key not in expected_refs:
            raise ValueError("Unattested original source-link section")
        spec=expected_refs[key]
        if len(spec)!=len(literal[key]):
            raise ValueError("Source links not covered one-for-one")
        for entry,target in zip(spec,literal[key]):
            _inject_reference_at_exact_marker(
                section,marker=entry["modern_text_marker"],
                literal_osisref=target)
            linked+=1
    embedded=[e.get("osisRef") for e in chapter.iter() if e.tag==_XML_REF]
    originals=[v for u in expected_units for v in literal[u["first_key"]]]
    if embedded!=originals:
        raise ValueError("Final preview inline link targets not exactly original")
    book=chapter.getparent() if hasattr(chapter,"getparent") else None
    # xml.etree does not expose parent pointers: locate matching book explicitly.
    book_code=source_map["scope"].split(".",1)[0]
    books=doc.findall(f".//{{{NS}}}div[@type='book']")
    selected=[b for b in books if b.get("osisID")==book_code and chapter in list(b)]
    if len(selected)!=1:
        raise ValueError("Modern chapter has no unique book container")
    book=selected[0]
    intro=read_book_intro_candidate(candidate_book_intro,book=book_code,
        source_zip_sha=source_map["published_zip_sha256"],
        source_corpus_sha=source_map["verified_entire_native_corpus_sha256"])
    node=ET.Element(f"{{{NS}}}div",{
        "type":"introduction","resp":"BibleResourcesModernEditorial",
        "annotateType":"commentary","annotateRef":book_code})
    ET.SubElement(node,f"{{{NS}}}title",{
        "type":"main","resp":"BibleResourcesModernEditorial"}).text=book_code+" — Book introduction"
    for paragraph in intro:
        ET.SubElement(node,f"{{{NS}}}p").text=paragraph
    book.insert(0,node)
    all_count=sum(1 for x in doc.iter() if x.tag==_XML_REF)
    if all_count!=linked:
        raise ValueError("Unaccounted link markup in private generated preview")
    result=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(result)
    report.update({
        "status":"DISPOSABLE_SOURCE_LINKED_CANDIDATE_LAYOUT_NOT_EDITORIALLY_APPROVED",
        "source_witness_chapter":source_map["scope"],
        "original_source_link_targets_embedded_exactly":True,
        "original_source_link_target_count":linked,
        "original_book_intro_source_owner_first_numbered_K":source_map["sections"][0]["first_key"],
        "original_book_intro_first_K_ownership_attested":bool(
            gate.report(complete_raw_report)["original_book_intro_and_outline_owned_by_first_numbered_K_attested"]),
        "original_I_placeholder_keys_are_empty":all(
            item["source_visible_word_count"]==0
            for item in gate.intros_seen.values()),
        "modern_book_introduction_editorially_moved_out_of_first_K":True,
        "modern_book_introduction_paragraphs_included":len(intro),
        "original_chapter_outline_tables_preserved":False,
        "original_chapter_intro_native_markup_preserved":False,
        "source_original_book_intro_raw_markup_preserved":False,
        "semantic_translation_independently_approved":False,
        "sword_publication_authorized":False
    })
    return result,report


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--source-map",type=Path,required=True)
    p.add_argument("--expected-references",type=Path,required=True)
    p.add_argument("--book-intro-candidate",type=Path,required=True)
    p.add_argument("--chapter-candidate",type=Path,required=True)
    p.add_argument("--native-reader",type=Path,required=True)
    p.add_argument("--module-directory",type=Path,required=True)
    p.add_argument("--module-id",required=True)
    p.add_argument("--temp-module-id",default="MHCCGENP")
    p.add_argument("--osis",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    source=json.loads(a.source_map.read_text(encoding="utf-8"))
    refs=json.loads(a.expected_references.read_text(encoding="utf-8"))
    if (not a.native_reader.is_file() or not a.module_directory.is_dir()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}",a.module_id)):
        raise ValueError("Trusted source-native SWORD reader/module required")
    gate=SourceReferenceGate(source_map=source,expected_refs=refs,
                             candidate=a.chapter_candidate.read_text(encoding="utf-8"))
    env=os.environ.copy()
    env["SWORD_PATH"]=str(a.module_directory.resolve())
    proc=subprocess.Popen([str(a.native_reader.resolve()),a.module_id],
                          env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("No original source reader stream")
        complete,*_=parse_native_raw_corpus(proc.stdout,on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=25):
            raise ValueError("Original reader incomplete")
        osis,receipt=build_verified_preview(
            root=a.root,source_map=source,expected_refs=refs,gate=gate,
            complete_raw_report=complete,
            candidate_book_intro=a.book_intro_candidate,temp_id=a.temp_module_id)
        a.osis.parent.mkdir(parents=True,exist_ok=True)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.osis.write_bytes(osis)
        a.report.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("Private source-linked modern candidate OSIS preview PASS: "+
              str(receipt["annotated_commentary_sections"])+" source units, "+
              str(receipt["original_source_link_target_count"])+" exact original links, "+
              str(receipt["modern_book_introduction_paragraphs_included"])+" book intro paragraphs; "+
              "native chapter intro/outline and semantic approval PENDING")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


if __name__=="__main__":
    raise SystemExit(main())
