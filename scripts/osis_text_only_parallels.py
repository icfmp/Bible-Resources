#!/usr/bin/env python3
"""Reversibly represent text-only parallel headings without fake SWORD links.

Some standard USFM->OSIS converters wrap *unresolved* parallel-passage
heading text in <reference type="parallel">, with NO osisRef. This makes
frontends style editorial prose as a clickable Bible reference even when
the source did not provide a machine target. Standard OSIS <seg> with an
explicit x- type preserves the authorial parallel-reference meaning
without making an invented hyperlink.

Scope is generic: any reference lacking osisRef directly inside
<title type="parallel">. Other references and all authored content are
untouched; unexpected reference metadata causes a hard failure.
The exact original XML tree is restorable by a mechanical inverse of this
single, documented tag/type change, verified byte-exact in canonical XML.

The original publisher USFM/USFX and generated OSIS are immutable.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from lxml import etree

from pilot_preflight import PilotError

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
UNLINKED_SEG_TYPE="x-unlinked-parallel-reference"


def _parser():
    return etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,
        recover=False,huge_tree=False)


def _c14n(root) -> bytes:
    return etree.tostring(root,method="c14n")


def convert_unresolved_parallel_headings(
    generated_osis:Path, output:Path, *, schema_proof
) -> dict:
    """Apply one safe, reversible OSIS annotation-only presentation fix."""
    if (generated_osis==output or output.exists() or output.is_symlink()
            or not generated_osis.is_file()
            or not output.parent.is_dir() or output.parent.is_symlink()):
        raise PilotError("Unsafe parallel heading candidate output path")
    original=generated_osis.read_bytes()
    if b"<!DOCTYPE" in original.upper():
        raise PilotError("Untrusted OSIS source declares a DOCTYPE")
    root=etree.fromstring(original,parser=_parser())
    pristine=_c14n(root)
    candidate=etree.fromstring(original,parser=_parser())
    changes=0
    title_count=0
    original_refs=0
    for title in candidate.iter(OSIS+"title"):
        if title.get("type")!="parallel":
            continue
        title_count+=1
        for ref in title.iter(OSIS+"reference"):
            if ref.get("osisRef") is not None:
                continue
            if ref.getparent() is not title:
                raise PilotError("Unresolved nested parallel reference requires review")
            if dict(ref.attrib)!={"type":"parallel"}:
                raise PilotError("Unresolved parallel reference has unsupported metadata")
            if ref.get("sID") is not None or ref.get("eID") is not None:
                raise PilotError("Cannot remap milestoned parallel reference")
            original_refs+=1
            ref.tag=OSIS+"seg"
            ref.attrib.clear()
            ref.set("type",UNLINKED_SEG_TYPE)
            changes+=1
    if changes!=original_refs:
        raise PilotError("Unresolved parallel reference count changed")
    clone=etree.fromstring(etree.tostring(candidate),parser=_parser())
    for seg in clone.iter(OSIS+"seg"):
        if seg.get("type")!=UNLINKED_SEG_TYPE:
            continue
        if (seg.getparent() is None
                or seg.getparent().tag!=OSIS+"title"
                or seg.getparent().get("type")!="parallel"
                or dict(seg.attrib)!={"type":UNLINKED_SEG_TYPE}):
            raise PilotError("Unrecognized reversible parallel reference marker")
        seg.tag=OSIS+"reference"
        seg.attrib.clear()
        seg.set("type","parallel")
    if _c14n(clone)!=pristine:
        raise PilotError("Parallel heading transformation is not reversible")
    with output.open("xb") as writer:
        writer.write(etree.tostring(candidate,encoding="utf-8",
                                    xml_declaration=True))
    if generated_osis.read_bytes()!=original:
        raise PilotError("Unmodified OSIS source changed during repair")
    validation=schema_proof(output)
    if (validation.get("xsd_status")!="validated"
            or validation.get("policy_status")!="validated"):
        output.unlink(missing_ok=True)
        raise PilotError("Reversible parallel-heading candidate violates OSIS XSD")
    return {
        "status":"reversible_unresolved_parallel_heading_markup_verified",
        "total_source_parallel_titles":title_count,
        "text_only_parallel_reference_elements_retyped":changes,
        "source_osis_sha256":sha256(original).hexdigest(),
        "retyped_osis_sha256":sha256(output.read_bytes()).hexdigest(),
        "inverse_reconstruction_canonical_xml_byte_equal":True,
        "original_source_unchanged":True,
        "heading_text_punctuation_and_order_unchanged":True,
        "explicit_osisref_targets_removed":0,
        "machine_bible_links_invented":0,
        "no_publication":True,
        "visual_reader_approval_pending":True,
    }
