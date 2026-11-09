#!/usr/bin/env python3
"""Read-only comparison of actual SWORD footnote bodies with source OSIS notes.

The trusted C++ reader writes *private*, hex-encoded SWORD entry attributes to
an isolated temporary directory. The file is destroyed before CI uploads
metadata-only JSON: note counts, equality checks, source reference, hashes.
No actual note or biblical text may appear in diagnostics or logs.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unicodedata

from lxml import etree

from lsg_note_parity import _collect_osis
from lsg_stock_lemma_parity import ordered_lemma_reader_plan
from lsg_osis_parity import OSIS
from pilot_preflight import PilotError

_MAX_PRIVATE_BYTES=120_000_000


def _text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _space(value: str) -> str:
    return " ".join(_text(value).split())


def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _body_text(body: str) -> tuple[str | None,str | None]:
    try:
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,recover=False,huge_tree=False)
        root=etree.fromstring(("<root>"+body+"</root>").encode("utf-8"),parser)
    except (etree.XMLSyntaxError,UnicodeError,ValueError):
        return None,None
    raw="".join(root.itertext())
    return _text(raw),_space(raw)


def _note_ids(items: dict[str,dict]) -> tuple[list[str],bool]:
    if all(name.isascii() and name.isdecimal() for name in items):
        return sorted(items,key=lambda n:int(n)),True
    return sorted(items),False


def load_private_note_rows(rows: list[str], valid_books: set[str]) -> dict:
    """Parse short-lived note attribute records; never serialize their values."""
    records=defaultdict(dict)
    for row in rows:
        cols=row.split("\t")
        if len(cols)!=5 or cols[0] not in valid_books:
            raise PilotError("Untrusted SWORD footnote attribute record")
        book,ref,encoded_id,encoded_name,encoded_value=cols
        if not ref or len(ref)>120:
            raise PilotError("Invalid compiled SWORD note reference")
        try:
            note_id=bytes.fromhex(encoded_id).decode("utf-8")
            name=bytes.fromhex(encoded_name).decode("utf-8")
            value=bytes.fromhex(encoded_value).decode("utf-8")
        except (UnicodeError,ValueError) as exc:
            raise PilotError("Malformed temporary SWORD note attribute hex") from exc
        if not note_id or len(note_id)>120 or not name or len(name)>120:
            raise PilotError("Unsupported empty or oversized SWORD note attribute")
        attributes=records[(book,ref)].setdefault(note_id,{})
        if name in attributes:
            raise PilotError("Duplicate compiled SWORD note attribute")
        attributes[name]=value
    return records


def compare_compiled_notes(candidate: Path,
                           aliases: list[tuple[str,str]],
                           decisions: list[dict],
                           rows: list[str]) -> dict:
    plan,books=ordered_lemma_reader_plan(candidate,aliases)
    allowed={(book,ref) for ref,book,_intro in plan}
    original=etree.parse(str(candidate),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    source,outside=_collect_osis(original)
    mapping=dict(aliases)
    remap={}
    for decision in decisions:
        a=decision["osis_source_key"]
        b=decision["osis_reader_key"]
        if a in remap or a==b or b not in mapping:
            raise PilotError("Unreviewed source-to-reader note merge")
        remap[a]=b
    expected=defaultdict(list)
    for original_key,notes in source.items():
        key=remap.get(original_key,original_key)
        if key not in mapping:
            raise PilotError("Note source key lost from stock SWORD reader index")
        book=key.split(".",1)[0]
        expected[(book,mapping[key])].extend(notes)
    compiled=load_private_note_rows(rows,{b.get("osisID") for b in books})
    if set(compiled)-allowed:
        raise PilotError("Compiled note payload uses unexpected stock SWORD reader key")
    source_count=sum(map(len,expected.values()))
    target_count=sum(map(len,compiled.values()))
    normalized_matches=raw_matches=0
    total_pairs=0
    parse_errors=0
    nonnumeric_id_groups=0
    missing_body_count=0
    attribute_names=Counter()
    whitespace_classes=Counter()
    source_type_slots=matching_type_slots=0
    source_caller_slots=matching_caller_slots=0
    compiled_nonempty_ref_lists=0
    metadata_differences=[]
    count_mismatches=[]
    text_mismatches=[]
    for location in sorted(set(expected)|set(compiled)):
        notes=expected.get(location,[])
        targets=compiled.get(location,{})
        ordered,ids_numeric=_note_ids(targets)
        nonnumeric_id_groups += len(ordered)>1 and not ids_numeric
        if len(notes)!=len(ordered) and len(count_mismatches)<60:
            count_mismatches.append({
                "book":location[0],"reader_reference":location[1],
                "source_notes":len(notes),"compiled_notes":len(ordered)})
        for index,(note,identifier) in enumerate(zip(notes,ordered),1):
            total_pairs+=1
            attrs=targets[identifier]
            # Counter.update(mapping) would COPY attribute VALUES into the
            # report; only count non-sensitive attribute NAMES, never bodies.
            attribute_names.update(attrs.keys())
            original_note=note["_xml_node"]
            source_type=original_note.get("type")
            source_caller=note["caller"]
            if source_type is not None:
                source_type_slots+=1
                matching_type_slots+=source_type==attrs.get("type")
            if source_caller is not None:
                source_caller_slots+=1
                matching_caller_slots+=source_caller==attrs.get("n")
            compiled_nonempty_ref_lists+=bool(attrs.get("refList"))
            if ((source_type is not None and source_type!=attrs.get("type"))
                or (source_caller is not None and source_caller!=attrs.get("n"))):
                if len(metadata_differences)<60:
                    metadata_differences.append({
                        "book":location[0],"reader_reference":location[1],
                        "note_ordinal":index,
                        "type_matches":source_type==attrs.get("type"),
                        "caller_matches":source_caller==attrs.get("n"),
                        "source_type_sha256":_sha(source_type or ""),
                        "compiled_type_sha256":_sha(attrs.get("type") or ""),
                        "source_caller_sha256":_sha(source_caller or ""),
                        "compiled_caller_sha256":_sha(attrs.get("n") or ""),
                    })
            body=attrs.get("body")
            if not body:
                missing_body_count+=1
                continue
            rendered_raw,rendered_norm=_body_text(body)
            if rendered_norm is None:
                parse_errors+=1
                if len(text_mismatches)<60:
                    text_mismatches.append({
                        "book":location[0],
                        "reader_reference":location[1],
                        "note_ordinal":index,
                        "diagnostic":"unparseable_compiled_note_body",
                        "compiled_payload_sha256":_sha(body),
                    })
                continue
            original_raw=_text("".join(note["_xml_node"].itertext()))
            original_norm=_space(original_raw)
            raw_matches+=original_raw==rendered_raw
            normalized_matches+=original_norm==rendered_norm
            if original_raw==rendered_raw:
                whitespace_classes["exact"]+=1
            elif original_raw.strip()==rendered_raw.strip():
                whitespace_classes["leading_or_trailing_only"]+=1
            elif original_norm==rendered_norm:
                whitespace_classes["internal_whitespace_only"]+=1
            else:
                whitespace_classes["not_only_whitespace"]+=1
            if original_norm!=rendered_norm and len(text_mismatches)<60:
                text_mismatches.append({
                    "book":location[0],
                    "reader_reference":location[1],
                    "note_ordinal":index,
                    "diagnostic":"normalized_note_body_mismatch",
                    "original_normalized_sha256":_sha(original_norm),
                    "compiled_normalized_sha256":_sha(rendered_norm),
                })
    equal=(source_count==target_count==total_pairs
           and outside==0 and not count_mismatches
           and normalized_matches==source_count and parse_errors==0
           and missing_body_count==0 and not nonnumeric_id_groups)
    return {
        "status":("compiled_note_normalized_body_text_verified_only" if equal
                  else "blocked_or_unresolved_compiled_note_text_parity"),
        "source_note_count":source_count,
        "compiled_note_count":target_count,
        "source_notes_outside_verses":outside,
        "paired_note_count":total_pairs,
        "matching_normalized_note_body_text":normalized_matches,
        "matching_raw_note_body_text":raw_matches,
        "body_xml_fragment_parse_failures":parse_errors,
        "missing_or_empty_note_bodies":missing_body_count,
        "reader_groups_with_non_numeric_ambiguous_note_ids":nonnumeric_id_groups,
        "first_note_count_mismatches":count_mismatches,
        "first_normalized_text_or_parse_mismatches":text_mismatches,
        "compiled_footnote_attribute_names":dict(sorted(attribute_names.items())),
        "raw_text_difference_categories":dict(sorted(whitespace_classes.items())),
        "source_notes_with_explicit_type":source_type_slots,
        "matching_compiled_note_type_values":matching_type_slots,
        "source_notes_with_caller":source_caller_slots,
        "matching_compiled_note_caller_values":matching_caller_slots,
        "compiled_nonempty_sword_ref_lists":compiled_nonempty_ref_lists,
        "first_type_or_caller_metadata_differences":metadata_differences,
        "available_note_type_and_caller_values_match":(
            source_type_slots==matching_type_slots and
            source_caller_slots==matching_caller_slots and
            source_type_slots+source_caller_slots>0),
        "note_kind_caller_and_anchor_fidelity_verified":False,
        "reference_target_resolution_verified":False,
        "original_whitespace_identity_verified":raw_matches==source_count,
        "published":False,
    }


def audit_compiled_note_bodies(candidate: Path, aliases: list[tuple[str,str]],
                               decisions: list[dict], *, sword_root: Path,
                               module_id: str, inspector: Path) -> dict:
    if not inspector.is_file() or inspector.is_symlink():
        raise PilotError("Private compiled SWORD note inspector missing")
    plan,_=ordered_lemma_reader_plan(candidate,aliases)
    with tempfile.TemporaryDirectory(prefix="private-sword-note-values-") as tmp:
        root=Path(tmp)
        refs=root/"ref-plan.tsv"
        private=root/"notes.hex.tsv"
        refs.write_text("".join("\t".join(ref)+"\n" for ref in plan),
                        encoding="utf-8")
        try:
            process=subprocess.run([str(inspector),module_id,str(refs),
                                    str(private),"--private-note-attributes"],
                capture_output=True,text=True,check=False,timeout=240,
                env=dict(os.environ,SWORD_PATH=str(sword_root)))
        except subprocess.TimeoutExpired:
            return {"status":"note_content_inspector_timed_out",
                    "full_note_text_and_targets_verified":False,
                    "published":False}
        if (process.returncode or process.stdout or process.stderr
                or not private.is_file()):
            return {
                "status":"note_content_inspector_unavailable",
                "probe_exit_code":process.returncode,
                "probe_stderr_bytes":len(process.stderr),
                "full_note_text_and_targets_verified":False,
                "published":False}
        if private.stat().st_size>_MAX_PRIVATE_BYTES:
            raise PilotError("Temporary SWORD note values exceed hard size bound")
        rows=private.read_text(encoding="utf-8").splitlines()
        report=compare_compiled_notes(candidate,aliases,decisions,rows)
    report["reader_entries_inspected"]=len(plan)
    report["source_modified"]=False
    return report
