#!/usr/bin/env python3
"""Compare original SWORD commentary links with draft markers without source export.

This reads exact original native XML *privately* through the project's existing
complete real-SWORD stream reader, fails closed on the pinned corpus SHA, and
reports only predeclared link identity hashes/booleans. It never infers links
from verse positions or changes an existing authorial source reference.
It is NOT a semantic or final OSIS source-link preservation approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus

_SHA = re.compile(r"^[a-f0-9]{64}$")
_REF = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]{0,2}\.[1-9][0-9]{0,2}$")


def canonical_only_for_comparison(target: str) -> str:
    """Validate the comparison spelling; do not rewrite source XML."""
    if not isinstance(target, str) or not target:
        raise ValueError("Original osisRef is missing or invalid")
    if target.startswith("Bible:"):
        target = target[6:]
    if not _REF.fullmatch(target):
        raise ValueError("Unrecognized original reference syntax; manual review needed")
    return target


def _original_reference_targets(raw: bytes) -> list[str]:
    try:
        node = ET.fromstring(b"<source>" + raw + b"</source>")
    except ET.ParseError as exc:
        raise ValueError("Original native XML is malformed; do not guess links") from exc
    references = []
    for element in node.iter():
        if isinstance(element.tag,str) and element.tag.rsplit("}",1)[-1] == "reference":
            literal = element.attrib.get("osisRef")
            references.append(canonical_only_for_comparison(literal))
    return references


class SourceReferenceGate:
    def __init__(self, *, source_map: dict, expected_refs: dict, candidate: str):
        self.source_map = source_map
        self.chapter = source_map.get("scope")
        units = source_map.get("sections")
        if not isinstance(units,list) or not units:
            raise ValueError("Source-native unit map missing")
        self.units = {x["first_key"]: x for x in units}
        if len(self.units)!=len(units):
            raise ValueError("Duplicate original native unit key")
        if (not isinstance(expected_refs,dict)
                or set(expected_refs)!=set(self.units)):
            raise ValueError("Every source section must have an explicit reference expectation")
        self.expected=expected_refs
        self.candidate=candidate
        self.seen={}
        intro_rows=source_map.get("introductions",[])
        if not isinstance(intro_rows,list):
            raise ValueError("Original chapter/book introduction list invalid")
        self.intro_units={row["native_key"]:row for row in intro_rows}
        if len(self.intro_units)!=len(intro_rows):
            raise ValueError("Duplicate original introduction native key")
        self.intros_seen={}
        for key,entries in expected_refs.items():
            if not isinstance(entries,list):
                raise ValueError("Expected source references must be a list")
            for entry in entries:
                if (not isinstance(entry,dict)
                        or not _REF.fullmatch(entry.get("canonical_target",""))
                        or not isinstance(entry.get("modern_text_marker"),str)
                        or not entry["modern_text_marker"]):
                    raise ValueError("Malformed verified original reference expectation")
                if entry["modern_text_marker"] not in candidate:
                    raise ValueError("Modern draft has not retained expected reference: "+key)

    def observe(self, kind: str, key: str, raw: bytes):
        if kind == "I" and key in self.intro_units:
            original=self.intro_units[key]
            digest=hashlib.sha256(raw).hexdigest()
            if digest != original.get("source_sha256") or key in self.intros_seen:
                raise ValueError("Native book/chapter intro differs from the pinned original")
            try:
                node=ET.fromstring(b"<source>" + raw + b"</source>")
            except ET.ParseError as exc:
                raise ValueError("Original introduction XML invalid") from exc
            visible=" ".join(node.itertext())
            self.intros_seen[key]={
                "source_raw_sha256":digest,
                "source_visible_word_count":len(re.findall(r"\b[\w’-]+\b",visible)),
                "has_visible_text":bool(visible.strip()),
                "source_introduction_still_not_semantically_approved":True
            }
            return
        if kind != "K" or key not in self.units:
            return
        if key in self.seen:
            raise ValueError("Source reader duplicated first native section key")
        unit=self.units[key]
        digest=hashlib.sha256(raw).hexdigest()
        if not _SHA.fullmatch(unit["source_sha256"]) or unit["source_sha256"]!=digest:
            raise ValueError("Source first native section changed from pinned SHA")
        original=_original_reference_targets(raw)
        expected=[i["canonical_target"] for i in self.expected[key]]
        if original != expected:
            raise ValueError("Original reference destinations diverge from predeclared native expectations")
        markup=unit.get("markup_census",{})
        source_count=markup.get("tag_counts",{}).get("reference",0)
        if len(original)!=source_count:
            raise ValueError("Exact source-native XML reference count differs from structural inventory")
        self.seen[key]={"reference_count":len(original),
                        "source_raw_sha256":digest,
                        "source_original_reference_identity_sha256":[
                            hashlib.sha256(r.encode("utf-8")).hexdigest()
                            for r in original],
                        "draft_marker_present":True}

    def report(self, raw_source_report: dict) -> dict:
        pin=self.source_map.get("verified_entire_native_corpus_sha256")
        if not isinstance(pin,str) or not _SHA.fullmatch(pin):
            raise ValueError("Invalid signed source-native corpus pin")
        if raw_source_report.get("all_native_raw_entries_ordered_sha256")!=pin:
            raise ValueError("Whole native source changed from approved corpus")
        if set(self.seen)!=set(self.units):
            raise ValueError("Some original first source units were not visited")
        if set(self.intros_seen)!=set(self.intro_units):
            raise ValueError("Some original book/chapter introduction keys not visited")
        return {
            "status":"EXACT_ORIGINAL_REFERENCE_ATTRIBUTES_MATCH_EXPECTATIONS_NOT_LINK_SERIALIZATION_ACCEPTANCE",
            "chapter":self.chapter,
            "full_published_native_corpus_sha256":pin,
            "source_unique_units_checked":len(self.units),
            "original_reference_links_checked":sum(x["reference_count"] for x in self.seen.values()),
            "per_source_unit":self.seen,
            "original_intro_units_found":len(self.intros_seen),
            "per_intro_unit":self.intros_seen,
            "original_prose_or_reference_labels_exported":False,
            "original_osisRef_literal_values_exported":False,
            "original_source_rewritten":False,
            "new_modern_osis_reference_targets_embedded":False,
            "independent_semantic_review_approved":False
        }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-reader",required=True,type=Path)
    p.add_argument("--module-directory",required=True,type=Path)
    p.add_argument("--module-id",required=True)
    p.add_argument("--source-map",required=True,type=Path)
    p.add_argument("--expected-references",required=True,type=Path)
    p.add_argument("--modern-candidate",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    if not a.native_reader.is_file() or not a.module_directory.is_dir():
        p.error("Trusted real native reader and installed source module directory required")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}",a.module_id):
        p.error("Unexpected SWORD module ID")
    source=json.loads(a.source_map.read_text(encoding="utf-8"))
    expectation=json.loads(a.expected_references.read_text(encoding="utf-8"))
    gate=SourceReferenceGate(source_map=source,expected_refs=expectation,
                             candidate=a.modern_candidate.read_text(encoding="utf-8"))
    env=os.environ.copy()
    env["SWORD_PATH"]=str(a.module_directory.resolve())
    proc=subprocess.Popen([str(a.native_reader.resolve()),a.module_id],
                           env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Missing native source stream")
        summary,*_=parse_native_raw_corpus(proc.stdout,on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=25)!=0:
            raise ValueError("Native stock-SWORD reader did not complete successfully")
        report=gate.report(summary)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("SOURCE-NATIVE REFERENCE IDENTITY PASS: "+
              str(report["source_unique_units_checked"])+" source units; "+
              str(report["original_reference_links_checked"])+" links; "+
              "raw labels/targets kept private; no derivative approval")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


if __name__=="__main__":
    raise SystemExit(main())
