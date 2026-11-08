#!/usr/bin/env python3
"""Fail-closed integrity and official OSIS validation of an unsaved dry-run clone.

The only permitted difference from the original generated OSIS is ASCII space
insertion at positions attested independently by publisher USFX markers.
No candidate/source changes, publishing, or acceptance follows this check.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from lxml import etree

from guard_osis import inspect as inspect_osis, StructureFailure
from pilot_preflight import PilotError


def _root(value):
    return value.getroot() if isinstance(value, etree._ElementTree) else value


def _added_ascii_spaces(before: str | None, after: str | None) -> int | None:
    """Return inserted-space count; reject every replacement/removal.

    Two-pointer subsequence comparison handles repeated spaces without
    confusing a whitespace-only replacement with an insertion.
    """
    left=before or ""
    right=after or ""
    i=j=0
    inserted=0
    while j<len(right):
        if i<len(left) and left[i]==right[j]:
            i+=1
            j+=1
        elif right[j]==" ":
            inserted+=1
            j+=1
        else:
            return None
    return inserted if i==len(left) else None


def inspect_space_only_clone(original, clone) -> dict:
    """Verify identical XML nodes and attributes, plus inserted ASCII spaces only.

    This audit is independent of verse-text normalization. Original XML
    comments, notes, Strong attributes, poetry, headings and milestones
    must have exactly the same identity and order in both trees.
    """
    left_nodes=list(_root(original).iter())
    right_nodes=list(_root(clone).iter())
    if len(left_nodes)!=len(right_nodes):
        raise PilotError("Modeled clone changed the OSIS element count")
    changed=Counter()
    inserted=0
    for index,(left,right) in enumerate(zip(left_nodes,right_nodes),1):
        if (left.tag!=right.tag or
                dict(left.attrib)!=dict(right.attrib) or
                left.nsmap!=right.nsmap):
            raise PilotError(f"Modeled clone changed XML structure or attributes at node {index}")
        for field in ("text","tail"):
            delta=_added_ascii_spaces(getattr(left,field),getattr(right,field))
            if delta is None:
                raise PilotError(f"Modeled clone altered non-space XML {field} at node {index}")
            inserted+=delta
            if delta:
                changed[field+"_nodes"]+=1
                changed[field+"_insertions"]+=delta
    return {
        "xml_node_count_unchanged":len(left_nodes),
        "total_inserted_ascii_spaces":inserted,
        "changed_node_fields":dict(sorted(changed.items())),
        "no_element_attribute_or_nonspace_text_mutation":True,
        "all_original_candidate_markup_preserved":True,
        "caveat":"Inserted spaces are a separate source-attested display model; raw authoring whitespace is not certified.",
    }


def validate_modeled_clone(original, clone, clone_path: Path,
                           schema_path: Path | None) -> dict:
    """Validate existing temporary clone, not original source/candidate files."""
    mutations=inspect_space_only_clone(original,clone)
    output={
        "status":"not_validated_no_pinned_schema",
        "modeled_clone_validation":mutations,
        "official_schema_and_policy_validated":False,
        "original_candidate_rewritten":False,
        "approved_for_publication":False,
    }
    if schema_path is None:
        return output
    path=Path(clone_path)
    # File was created only inside TemporaryDirectory by caller.
    if not path.is_file() or path.is_symlink():
        raise PilotError("Missing or unsafe temporary modeled OSIS file")
    from_disk=etree.parse(str(path),parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    if etree.tostring(from_disk.getroot(),encoding="utf-8") != etree.tostring(
            _root(clone),encoding="utf-8"):
        raise PilotError("Temporary modeled OSIS bytes do not match audited clone")
    output["simulated_osis_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        checked=inspect_osis(path,Path(schema_path))
    except StructureFailure as exc:
        output.update({
            "status":"modeled_clone_schema_or_policy_blocked",
            "failure_code":exc.code,
        })
        return output
    output.update({
        "status":"modeled_clone_schema_and_policy_validated_only",
        "official_schema_and_policy_validated":True,
        "schema_sha256":checked["schema_sha256"],
    })
    return output
