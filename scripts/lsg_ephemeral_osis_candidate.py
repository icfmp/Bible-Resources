#!/usr/bin/env python3
"""Build a strictly validated, *temporary* source-attested LSG display candidate.

Only whitespace gaps attested by independently paired USFX notes and speech
spans may be inserted; every existing XML element, attribute and text
codepoint must remain in order. The result must pass the official pinned
OSIS XSD and original verse-by-verse normalized text before any SWORD test.

This is an intermediate work product, not a publication decision or final
claim of original authorial byte/layout identity.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from lxml import etree

from pilot_preflight import PilotError
from lsg_source_compare import scan_usfx
from lsg_sword_compare import usfx_text_by_verse
from lsg_note_parity import audit_notes
from lsg_note_space_dryrun import simulate_source_note_spaces
from lsg_speech_space_dryrun import simulate_source_speech_spaces
from lsg_model_validation import validate_modeled_clone
from lsg_osis_parity import OSIS,_osis_verses


def prepare_ephemeral_source_spaced_osis(
        original_osis: Path,
        publisher_usfx: bytes,
        output: Path,
        pinned_schema: Path) -> dict:
    before=original_osis.read_bytes()
    source_structure,source_keys=scan_usfx(publisher_usfx)
    original=etree.fromstring(
        publisher_usfx,parser=etree.XMLParser(
            resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    converted=etree.parse(str(original_osis),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    codes=source_structure["original_books"]
    osis_codes=[item.get("osisID") for item in converted.iter(OSIS+"div")
                if item.get("type")=="book"]
    if (len(codes)!=len(osis_codes)
            or len(set(codes))!=len(codes)
            or len(set(osis_codes))!=len(osis_codes)
            or not all(osis_codes)):
        raise PilotError("Source-to-OSIS books not bijectively aligned")
    mapping=dict(zip(codes,osis_codes))
    note_audit=audit_notes(original,converted,mapping)
    notes=note_audit["source_note_count"]
    if (notes!=note_audit["candidate_note_count"] or
            note_audit["matching_note_component_text"]!=notes or
            note_audit["matching_note_caller_markers"]!=notes or
            note_audit["matching_note_word_anchors"]!=notes or
            note_audit["matching_note_kinds"]!=notes or
            note_audit["unsupported_note_substructures"]):
        raise PilotError("Cannot materialize a model with unverified notes")
    note_clone,note_report=simulate_source_note_spaces(
        original,converted,mapping)
    final_clone,speech_report=simulate_source_speech_spaces(
        original,note_clone,mapping)
    target=Path(output)
    if target==Path(original_osis) or target.exists() or target.is_symlink():
        raise PilotError("No source overwrite or candidate reuse permitted")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise PilotError("Experimental candidate target must be in a safe temporary folder")
    # Atomic no-overwrite creation; caller controls TemporaryDirectory.
    with target.open("xb") as fp:
        fp.write(etree.tostring(final_clone,encoding="utf-8",xml_declaration=True))
    checked=validate_modeled_clone(converted,final_clone,target,pinned_schema)
    if not checked["official_schema_and_policy_validated"]:
        raise PilotError("Source-attested model failed pinned OSIS schema/policy")
    source_body,_=usfx_text_by_verse(publisher_usfx,filter_books=set(codes))
    compiled_body,_,_,_=_osis_verses(target)
    if len(source_keys)!=len(source_body) or len(compiled_body)!=len(source_keys):
        raise PilotError("Unexpected authored or candidate reference counts")
    matching=sum(source_body[key] == compiled_body.get(
        f"{mapping[key[0]]}.{key[1]}.{key[2]}")
        for key in source_keys)
    if matching!=len(source_keys):
        raise PilotError("Modeled OSIS candidate still differs from authorial verse text")
    if original_osis.read_bytes()!=before:
        raise PilotError("Source OSIS bytes changed during candidate model")
    return {
        "status":"source_attested_ephemeral_candidate_verified_not_published",
        "original_osis_sha256":hashlib.sha256(before).hexdigest(),
        "ephemeral_candidate_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "source_verse_keys":len(source_keys),
        "matching_source_verse_texts":matching,
        "paired_source_notes":notes,
        "note_spaces_inferred_from_publisher":note_report[
            "by_category"]["source_space_modeled_in_memory"],
        "modeled_xml_structure_validation":checked,
        "speech_model_status":speech_report.get("status","not_reported"),
        "original_bytes_preserved":True,
        "schema_and_policy_validated":True,
        "published":False,
        "approved_for_publication":False,
        "formatting_caveat":"Source line breaks represented by visible ASCII "
            "separators; editorial original-byte equivalence not claimed.",
    }
