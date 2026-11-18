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


def _source_reference_literals(raw: bytes) -> list[str]:
    """Return exact literal original link targets IN MEMORY ONLY."""
    try:
        node = ET.fromstring(b"<source>" + raw + b"</source>")
    except ET.ParseError as exc:
        raise ValueError("Original native XML is malformed; do not guess links") from exc
    references=[]
    for element in node.iter():
        if isinstance(element.tag,str) and element.tag.rsplit("}",1)[-1] == "reference":
            literal=element.attrib.get("osisRef")
            canonical_only_for_comparison(literal)
            references.append(literal)
    return references


def _original_reference_targets(raw: bytes) -> list[str]:
    return [canonical_only_for_comparison(value)
            for value in _source_reference_literals(raw)]


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
        self._private_literal_links={}
        intro_rows=source_map.get("introductions",[])
        if not isinstance(intro_rows,list):
            raise ValueError("Original chapter/book introduction list invalid")
        self.intro_units={row["native_key"]:row for row in intro_rows}
        if len(self.intro_units)!=len(intro_rows):
            raise ValueError("Duplicate original introduction native key")
        self.intros_seen={}
        self.composite_expectations=source_map.get("intro_provenance_expectations")
        if self.composite_expectations is not None and not isinstance(self.composite_expectations,dict):
            raise ValueError("Unstructured original composite intro evidence")
        self.composite_verified=self.composite_expectations is None
        self._private_original_composite_tree=None
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
        literals=_source_reference_literals(raw)
        original=[canonical_only_for_comparison(value) for value in literals]
        expected=[i["canonical_target"] for i in self.expected[key]]
        if original != expected:
            raise ValueError("Original reference destinations diverge from predeclared native expectations")
        markup=unit.get("markup_census",{})
        source_count=markup.get("tag_counts",{}).get("reference",0)
        if len(original)!=source_count:
            raise ValueError("Exact source-native XML reference count differs from structural inventory")
        compound=self.composite_expectations
        if compound and key==compound.get("original_first_numbered_key"):
            try:
                source=ET.fromstring(b"<source>"+raw+b"</source>")
            except ET.ParseError as exc:
                raise ValueError("Invalid original composite first numbered XML") from exc
            visible=re.sub(r"\s+"," "," ".join(source.itertext())).strip()
            for field in ("expected_original_book_intro_start",
                          "expected_original_exposition_start"):
                phrase=compound.get(field)
                if not isinstance(phrase,str) or not phrase or phrase not in visible:
                    raise ValueError("First numbered original source does not contain declared book-intro/exposition boundary")
            counts={}
            for node in source.iter():
                if node is source or not isinstance(node.tag,str):
                    continue
                name=node.tag.rsplit("}",1)[-1]
                counts[name]=counts.get(name,0)+1
            for field,tag in (("expected_original_chapter_outline_row_count","row"),
                              ("expected_original_chapter_outline_table_count","table"),
                              ("expected_original_chapter_outline_title_count","title")):
                if type(compound.get(field)) is not int or counts.get(tag,0)!=compound[field]:
                    raise ValueError("Original composite source editorial outline structure has drifted")
            self.composite_verified=True
            self._private_original_composite_tree=source
        self._private_literal_links[key]=literals
        self.seen[key]={"reference_count":len(original),
                        "source_raw_sha256":digest,
                        "source_original_reference_identity_sha256":[
                            hashlib.sha256(r.encode("utf-8")).hexdigest()
                            for r in original],
                        "draft_marker_present":True}

    def original_composite_outline_tree_after_verified_source(self, raw_source_report: dict):
        """Use only for private source-identity-preserving introductory layout."""
        self.report(raw_source_report)
        if self._private_original_composite_tree is None:
            raise ValueError("Composite first native K source not independently attested")
        return self._private_original_composite_tree

    def exact_source_link_literals_after_verified_source(self, raw_source_report: dict):
        """Use only inside an isolated builder, never serialize the returned dict."""
        self.report(raw_source_report)
        return {key:list(values) for key,values in self._private_literal_links.items()}

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
        if not self.composite_verified:
            raise ValueError("Book intro/outline origin in original first K was never attested")
        if self.composite_expectations and any(
                row["source_visible_word_count"]!=0
                for row in self.intros_seen.values()):
            raise ValueError("Source I placeholders unexpectedly acquired prose; manual reindex review needed")
        return {
            "status":"EXACT_ORIGINAL_REFERENCE_ATTRIBUTES_MATCH_EXPECTATIONS_NOT_LINK_SERIALIZATION_ACCEPTANCE",
            "chapter":self.chapter,
            "full_published_native_corpus_sha256":pin,
            "source_unique_units_checked":len(self.units),
            "original_reference_links_checked":sum(x["reference_count"] for x in self.seen.values()),
            "per_source_unit":self.seen,
            "original_intro_units_found":len(self.intros_seen),
            "original_book_intro_and_outline_owned_by_first_numbered_K_attested":bool(self.composite_expectations and self.composite_verified),
            "per_intro_unit":self.intros_seen,
            "original_prose_or_reference_labels_exported":False,
            "original_osisRef_literal_values_exported":False,
            "original_source_rewritten":False,
            "new_modern_osis_reference_targets_embedded":False,
            "independent_semantic_review_approved":False
        }



class WholeCanonOriginalLinkIdentityReceipt:
    """Attest every published original-K link and its order, without exporting prose.

    The pre-existing whole-canon source receipt supplies immutable group hashes,
    occupied verse keys and counts. This independent traversal validates them
    against the *same complete* SHA-pinned real SWORD raw stream. Link targets,
    linked display text and source XML are hashed in private memory only.
    This class does not match a translated word, inject a link, or build a module.
    """

    STATUS = "SOURCE_NATIVE_ALL_K_REFERENCE_IDENTITIES_NOT_MODERN_LINK_PARITY"

    def __init__(self, native: dict):
        if (native.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL"
                or native.get("source_prose_or_original_markup_exported") is not False
                or native.get("semantic_translation_independently_approved") is not False):
            raise ValueError("Whole-canon source receipt is not an admissible original")
        pin = native.get("original_compiled_corpus_sha256")
        if not isinstance(pin, str) or not _SHA.fullmatch(pin):
            raise ValueError("Missing pinned original full SWORD corpus SHA")
        chapters = native.get("chapters")
        if not isinstance(chapters, dict) or not chapters:
            raise ValueError("Original chapter inventory is empty")
        self.corpus_sha = pin
        self.units: dict[str, dict] = {}
        self.keys: dict[str, str] = {}
        self.seen_keys: set[str] = set()
        self.seen_first: set[str] = set()
        self.linked_units: dict[str, dict] = {}
        self.link_count = 0
        for chapter, contents in chapters.items():
            groups = contents.get("original_units")
            if not isinstance(groups, list):
                raise ValueError("Original source chapter groups missing: " + chapter)
            for group in groups:
                first = group.get("first_key")
                keys = group.get("keys")
                sha = group.get("source_unit_sha256")
                tags = group.get("markup", {}).get("tag_counts", {})
                count = tags.get("reference", 0)
                if (not isinstance(first, str) or not isinstance(keys, list)
                        or not keys or keys[0] != first or first in self.units
                        or not isinstance(sha, str) or not _SHA.fullmatch(sha)
                        or type(count) is not int or count < 0):
                    raise ValueError("Unreliable original source group record: " + chapter)
                if not isinstance(tags, dict) or group["markup"].get(
                        "strict_xml_fragment") is not True:
                    raise ValueError("Original K group has not passed strict XML parsing")
                self.units[first] = {"sha": sha, "ref_count": count,
                                     "last": keys[-1]}
                for key in keys:
                    if (not isinstance(key, str) or not key.startswith(chapter + ".")
                            or key in self.keys):
                        raise ValueError("Repeated or foreign original K address")
                    self.keys[key] = first
        if not self.units or not self.keys:
            raise ValueError("No authentic original numbered commentary entries")

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        if kind != "K":
            return
        owner = self.keys.get(key)
        if owner is None or key in self.seen_keys:
            raise ValueError("Unexpected or duplicate original numbered SWORD key: " + key)
        group = self.units[owner]
        if hashlib.sha256(raw).hexdigest() != group["sha"]:
            raise ValueError("Original K alias and source SHA differ: " + key)
        self.seen_keys.add(key)
        if key != owner:
            return
        if owner in self.seen_first:
            raise ValueError("Duplicate first original K group key")
        self.seen_first.add(owner)
        try:
            node = ET.fromstring(b"<original>" + raw + b"</original>")
        except ET.ParseError as exc:
            raise ValueError("Original link-bearing K XML is malformed: " + owner) from exc
        targets = []
        labels = []
        for element in node.iter():
            if not isinstance(element.tag, str) or element.tag.rsplit("}", 1)[-1] != "reference":
                continue
            literal = element.attrib.get("osisRef")
            if (not isinstance(literal, str) or not literal or len(literal) > 2048
                    or any(ord(char) < 32 for char in literal)):
                raise ValueError("Original reference has missing/unsafe literal target: " + owner)
            # Preserve exact literal attribute spelling and occurrence order.
            # Do not impose the restricted single-verse parser from the Gen.1 pilot.
            targets.append(hashlib.sha256(literal.encode("utf-8")).hexdigest())
            labels.append(hashlib.sha256(
                "".join(element.itertext()).encode("utf-8")).hexdigest())
        if len(targets) != group["ref_count"]:
            raise ValueError("Original XML reference count differs from authenticated census: "
                             + owner)
        self.link_count += len(targets)
        if targets:
            self.linked_units[owner] = {
                "first_key": owner,
                "last_key": group["last"],
                "source_raw_sha256": group["sha"],
                "reference_count": len(targets),
                "original_osisRef_sha256_in_document_order": targets,
                "original_visible_link_label_sha256_in_document_order": labels,
            }

    def report(self, reader_report: dict) -> dict:
        if reader_report.get("all_native_raw_entries_ordered_sha256") != self.corpus_sha:
            raise ValueError("Full original native SWORD SHA does not match pinned edition")
        if (self.seen_keys != set(self.keys)
                or self.seen_first != set(self.units)):
            raise ValueError("Original K keys or source body groups were not completely read")
        return {
            "status": self.STATUS,
            "whole_native_source_sha256": self.corpus_sha,
            "original_numbered_K_keys_verified": len(self.seen_keys),
            "original_unique_K_bodies_verified": len(self.seen_first),
            "original_reference_elements_verified": self.link_count,
            "original_link_bearing_K_bodies": len(self.linked_units),
            "source_link_groups": [
                self.linked_units[k] for k in sorted(self.linked_units)
            ],
            "original_link_destinations_only_sha256_not_exported": True,
            "original_visible_link_text_only_sha256_not_exported": True,
            "original_source_prose_or_XML_exported": False,
            "modern_manuscript_reference_presence_approved": False,
            "modern_osisRef_targets_or_order_verified": False,
            "translated_link_display_text_reviewed": False,
            "source_original_mutated": False,
            "modern_module_built_or_published": False,
        }


def run_whole_native_link_identity(*, reader: Path, root: Path,
                                    module_id: str, native_receipt: Path) -> dict:
    native = json.loads(native_receipt.read_text(encoding="utf-8"))
    gate = WholeCanonOriginalLinkIdentityReceipt(native)
    env = os.environ.copy()
    env["SWORD_PATH"] = str(root.resolve())
    proc = subprocess.Popen([str(reader.resolve()), module_id], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Original native raw stream is unavailable")
        complete, *_ = parse_native_raw_corpus(proc.stdout, on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=30) != 0:
            raise ValueError("Original native raw reader failed")
        return gate.report(complete)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-reader",required=True,type=Path)
    p.add_argument("--module-directory",required=True,type=Path)
    p.add_argument("--module-id",required=True)
    p.add_argument("--source-map",type=Path)
    p.add_argument("--expected-references",type=Path)
    p.add_argument("--modern-candidate",type=Path)
    p.add_argument("--whole-native-receipt",type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    if not a.native_reader.is_file() or not a.module_directory.is_dir():
        p.error("Trusted real native reader and installed source module directory required")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}",a.module_id):
        p.error("Unexpected SWORD module ID")
    if a.whole_native_receipt is not None:
        if any(x is not None for x in
               (a.source_map, a.expected_references, a.modern_candidate)):
            p.error("Whole-canon original-only mode cannot claim modern marker parity")
        result = run_whole_native_link_identity(
            reader=a.native_reader, root=a.module_directory,
            module_id=a.module_id, native_receipt=a.whole_native_receipt)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("SOURCE-NATIVE COMPLETE ORIGINAL LINK IDENTITY PASS: groups=" +
              str(result["original_unique_K_bodies_verified"]) +
              ", native links=" + str(result["original_reference_elements_verified"]) +
              "; destination and label hashes only; zero modern link approval")
        return 0
    if any(x is None for x in
           (a.source_map, a.expected_references, a.modern_candidate)):
        p.error("Pilot mode requires --source-map, --expected-references and --modern-candidate")
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
