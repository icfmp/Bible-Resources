#!/usr/bin/env python3
"""Reversibly represent text-only headings without fake SWORD links.

Some standard USFM->OSIS converters wrap *unresolved* parallel-passage
or section-scope heading text in <reference> with NO osisRef. This makes
frontends style editorial prose as a clickable Bible reference even when
the source did not provide a machine target. Standard OSIS <seg> with an
explicit x- type preserves editorial semantics without inventing a link.

Scope is generic: direct references without osisRef inside
<title type="parallel"> or <title type="scope">, with only the
respectively expected source attributes. All authored content is untouched;
unexpected metadata causes a hard failure.
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
UNLINKED_SCOPE_SEG_TYPE="x-unlinked-scope-reference"
# Only source-attested, targetless heading references are safe to retype.
# Never infer that generic note/cross-reference links are mere decoration.
_RULES={
    "parallel": ({"type":"parallel"},UNLINKED_SEG_TYPE),
    "scope": ({},UNLINKED_SCOPE_SEG_TYPE),
}


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
    titles_by_type={kind:0 for kind in _RULES}
    elements_by_type={kind:0 for kind in _RULES}
    reserved_types={rule[1] for rule in _RULES.values()}
    # A generated source must not already use our reserved synthetic types:
    # otherwise the inverse could alter an editorial annotation we did
    # not create, even if the resulting text were identical.
    if any(seg.get("type") in reserved_types
           for seg in candidate.iter(OSIS+"seg")):
        raise PilotError("Original OSIS already uses a reserved heading segment type")
    for title in candidate.iter(OSIS+"title"):
        title_type=title.get("type")
        if title_type not in _RULES:
            continue
        titles_by_type[title_type]+=1
        expected_attrs,segment_type=_RULES[title_type]
        for ref in title.iter(OSIS+"reference"):
            if ref.get("osisRef") is not None:
                continue
            if ref.getparent() is not title:
                raise PilotError("Unresolved nested heading reference requires review")
            if dict(ref.attrib)!=expected_attrs:
                raise PilotError("Unresolved heading reference has unsupported metadata")
            ref.tag=OSIS+"seg"
            ref.attrib.clear()
            ref.set("type",segment_type)
            elements_by_type[title_type]+=1
            changes+=1
    clone=etree.fromstring(etree.tostring(candidate),parser=_parser())
    inverse_rules={seg:(kind,attrs)
                   for kind,(attrs,seg) in _RULES.items()}
    reversed_count=0
    for seg in clone.iter(OSIS+"seg"):
        seg_type=seg.get("type")
        if seg_type not in inverse_rules:
            continue
        title_type,reference_attrs=inverse_rules[seg_type]
        if (seg.getparent() is None
                or seg.getparent().tag!=OSIS+"title"
                or seg.getparent().get("type")!=title_type
                or dict(seg.attrib)!={"type":seg_type}):
            raise PilotError("Unrecognized reversible heading reference marker")
        seg.tag=OSIS+"reference"
        seg.attrib.clear()
        seg.attrib.update(reference_attrs)
        reversed_count+=1
    if reversed_count!=changes:
        raise PilotError("Not all modified text-only heading references were reversed")
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
        "total_source_parallel_titles":titles_by_type["parallel"],
        "total_source_scope_titles":titles_by_type["scope"],
        "text_only_parallel_reference_elements_retyped":elements_by_type["parallel"],
        "text_only_scope_reference_elements_retyped":elements_by_type["scope"],
        "total_text_only_heading_references_retyped":changes,
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
