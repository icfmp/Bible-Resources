#!/usr/bin/env python3
"""Audit explicit source- and edition-bound temporary SWORD verse merges.

Do not rewrite biblical text, infer permissions or create general exceptions
from an importer warning. A reviewed merge must first be independently proven
to contain the original adjacent verse strings in the original order.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree
from pilot_preflight import PilotError

KEY = re.compile(r"^([A-Z0-9]{3})\.([1-9][0-9]*)\.([1-9][0-9]*)$")
OSISKEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)$")
SHA = re.compile(r"^[0-9a-f]{64}$")
OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

def key_parts(reference: str, pattern=KEY) -> tuple[str,int,int]:
    if not isinstance(reference,str) or not (m:=pattern.fullmatch(reference)):
        raise PilotError("Malformed authored or compiled verse reference")
    return (m[1],int(m[2]),int(m[3]))

def load_reviewed_merges(path: Path, *, source_digest: str,
                         source_keys: list[tuple[str,int,int]],
                         versification: str) -> tuple[list[dict],str]:
    """Explicit authorization tied to original source bytes and SWORD v11n."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size>100_000:
        raise PilotError("Unsafe or missing reviewed-verse-merges policy")
    raw=path.read_bytes()
    try:
        doc=json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise PilotError("Malformed reviewed-verse-merges policy") from exc
    if (not isinstance(doc,dict) or doc.get("schema_version")!=1
        or doc.get("policy")!="approved_explicit_temporary_adjacent_verse_index_merge"
        or doc.get("versification")!=versification
        or not isinstance(source_digest,str) or not SHA.fullmatch(source_digest)
        or doc.get("source_document_sha256")!=source_digest):
        raise PilotError("Review policy is stale or targets another source/registry")
    approval=doc.get("authorization")
    if (not isinstance(approval,dict)
        or approval.get("who")!="Bible Resources project owner"
        or not isinstance(approval.get("record"),str)
        or not approval.get("scope") or not approval.get("date")):
        raise PilotError("Explicit project-owner authorization missing")
    entries=doc.get("allowed_merges")
    if not isinstance(entries,list) or not entries or len(entries)>200:
        raise PilotError("No reviewed merge entries or implausibly many entries")
    original=set(source_keys)
    if len(original)!=len(source_keys):
        raise PilotError("Source verse inventory contains duplicate keys")
    decisions=[]
    seen=set()
    for e in entries:
        if not isinstance(e,dict):
            raise PilotError("Malformed verse-merge policy entry")
        src=key_parts(e.get("authorial_source_key"))
        dest=key_parts(e.get("reader_source_key"))
        osis_src=key_parts(e.get("osis_source_key"),OSISKEY)
        osis_dest=key_parts(e.get("osis_reader_key"),OSISKEY)
        if (src in seen or src not in original or dest not in original
            or src[:2]!=dest[:2] or src[2]!=dest[2]+1
            or osis_src[:2]!=osis_dest[:2]
            or osis_src[2]!=osis_dest[2]+1
            or e.get("source_content_preserved") is not True
            or e.get("independent_reference_access_lost") is not True
            or e.get("reversible") is not True
            or e.get("status")!="temporarily_authorized_versification_compromise"):
            raise PilotError("Unreviewed, nonadjacent or unsupported source verse merge")
        # If source has any later verse within the same chapter then this
        # is not the documented SWORD end-of-canonical-chapter append.
        if any(b==src[0] and ch==src[1] and v>src[2]
               for b,ch,v in original):
            raise PilotError("Merge does not end a source-authored chapter")
        label=e.get("preferred_display_label")
        if (not isinstance(label,str)
            or label!=f"{dest[2]}–{src[2]}"):
            raise PilotError("Merge label disagrees with reviewed verse keys")
        if not isinstance(e.get("reason"),str) or len(e["reason"])<20:
            raise PilotError("No reviewed reason for merge")
        seen.add(src)
        decisions.append({
            "authorial_source_key":e["authorial_source_key"],
            "reader_source_key":e["reader_source_key"],
            "osis_source_key":e["osis_source_key"],
            "osis_reader_key":e["osis_reader_key"],
            "preferred_display_label":label,
            "source_verse_content_preserved":True,
            "separate_verse_key_not_available_in_stock_sword":True,
        })
    return decisions,sha256(raw).hexdigest()

def assess_reviewed_merges(
        decisions: list[dict],policy_sha256: str,assessment: dict) -> dict:
    """Audit exact *observed* source→reader merger; never trust config alone."""
    if (assessment.get("status")!="stock_segond_limitations_classified_not_approved"
        or assessment.get("all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks") is not True
        or assessment.get("all_reference_differences_explained") is not True
        or assessment.get("original_source_modified") is not False
        or assessment.get("full_compiled_notes_poetry_markup_verified") is not False):
        raise PilotError("Full stock SWORD body/slot readback is unverified")
    actual=assessment.get("appended_source_keys")
    if (not isinstance(actual,list)
        or len(actual)!=len(decisions)
        or assessment.get("source_only_verse_count")!=len(decisions)):
        raise PilotError("Unexpected out-of-v11n verse merges were not authorized")
    proposed={
        (d["authorial_source_key"],d["reader_source_key"])
        for d in decisions
    }
    observed={
        (f"{v['book']}.{v['chapter']}.{v['source_verse']}",
         f"{v['book']}.{v['chapter']}.{v['compiled_verse']}")
        for v in actual
        if isinstance(v,dict)
        and v.get("distinct_original_reference_unavailable") is True
    }
    if proposed!=observed or len(observed)!=len(actual):
        raise PilotError("Observed SWORD index merge differs from reviewed source map")
    if not SHA.fullmatch(policy_sha256):
        raise PilotError("Missing exact review policy digest")
    return {
        "status":"source_bound_owner_authorized_index_compromise",
        "policy_sha256":policy_sha256,
        "authorized_merge_count":len(decisions),
        "observed_source_to_reader_keys_exactly_match_authorization":True,
        "full_original_chapter_characters_retained":True,
        "reviewed_merges":decisions,
        "source_scripture_modified":False,
        "versification_index_not_exact":True,
        "full_compiled_markup_not_yet_verified":True,
        "module_approved_for_publication":False,
        "module_published":False,
    }

def annotate_editorial_label(source: Path, target: Path,
                             decisions: list[dict], *, schema_proof) -> dict:
    """Add OSIS 'n' *metadata* to verse opener on an isolated cloned candidate.

    Stock osis2mod typically removes verse tags. This does not promise
    visible 52–53 in every reader; never add fake inline Scripture words.
    """
    if target.exists() or target.is_symlink() or source==target:
        raise PilotError("Refusing to overwrite source or existing label candidate")
    base=source.read_bytes()
    root=etree.fromstring(base,parser=etree.XMLParser(
        no_network=True,load_dtd=False,resolve_entities=False,recover=False))
    starts={}
    for v in root.iter(OSIS+"verse"):
        ident=v.get("sID") or v.get("osisID")
        if ident and (v.get("sID") or v.get("osisID")):
            starts.setdefault(ident,[]).append(v)
    for d in decisions:
        ident=d["osis_reader_key"]
        verse=starts.get(ident,[])
        existing=verse[0].get("n") if len(verse)==1 else None
        expected_base=str(key_parts(ident,OSISKEY)[2])
        if len(verse)!=1 or existing not in (None, expected_base,
                                                d["preferred_display_label"]):
            raise PilotError(
                f"Cannot safely attach editorial range label to {ident}: "
                f"opening_milestones={len(verse)}, existing_n={existing!r}"
            )
        verse[0].set("n",d["preferred_display_label"])
    with target.open("xb") as f:
        f.write(etree.tostring(root,encoding="utf-8",xml_declaration=True))
    proof=schema_proof(target)
    if proof.get("xsd_status")!="validated" or proof.get("policy_status")!="validated":
        raise PilotError("OSIS label metadata is not accepted by official schema")
    if sha256(source.read_bytes()).digest()!=sha256(base).digest():
        raise PilotError("Original source candidate was modified")
    return {
        "status":"source_text_unchanged_osis_label_metadata_candidate",
        "input_sha256":sha256(base).hexdigest(),
        "output_sha256":sha256(target.read_bytes()).hexdigest(),
        "labeled_verse_entries":len(decisions),
        "osis_n_label_is_authorial_text":False,
        "labels_rendered_by_all_sword_readers":False,
        "official_osis_xsd_validated":True,
        "no_inline_label_added_to_scripture":True,
    }
