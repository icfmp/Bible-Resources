#!/usr/bin/env python3
"""Read-only OSIS editorial audit; structural diagnostics are NOT proposed edits.

Input can be any well-formed OSIS XML, including a source rejected by the
stricter reviewed structure gate. Do not conflate an audit with XSD approval.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from guard_osis import parse_xml, require_regular_file, MAX_SOURCE_BYTES, StructureFailure, write_report

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
SIMPLE_REF = re.compile(
    r"^(?:[A-Za-z0-9_-]+:)?[1-4]?[A-Za-z][A-Za-z0-9]*"
    r"(?:\.\d+(?:\.\d+)?)?(?:-(?:[1-4]?[A-Za-z][A-Za-z0-9]*"
    r"(?:\.\d+(?:\.\d+)?)?))?$"
)
VERSE_MARKER = re.compile(r"(?<!\d)(?:[1-9]\d{0,2})(?=\s|\u00a0|[.:])")
RISKS = {
    "long_bold_range": "typography",
    "upper_case_paragraph": "typography",
    "suspicious_heading": "typography",
    "excessive_styling": "typography",
    "unknown_style": "typography",
    "introductory_scripture_candidate": "quotation_candidate",
    "unreviewed_cross_reference": "reference_candidate",
    "invalid_cross_reference": "reference_error",
    "duplicate_verse_id": "structure_error",
    "duplicate_commentary_reference": "structure_candidate",
    "empty_verse_identifier": "structure_error",
    "verse_key_out_of_sequence": "structure_candidate",
}


def _tag(element) -> str:
    return element.tag[len(NS):] if isinstance(element.tag, str) and element.tag.startswith(NS) else str(element.tag)


def _where(node) -> dict:
    tree = node.getroottree()
    return {
        "xml_xpath": tree.getpath(node),
        "original_xml_line": node.sourceline,
    }


def _entry(source, node, code, *, reason, details=None):
    return dict(code=code, category=RISKS[code], severity=(
        "error" if code in {"duplicate_verse_id", "invalid_cross_reference", "empty_verse_identifier"}
        else "review"
    ), source_path=str(source), **_where(node), reason=reason,
        **({"details": details} if details else {}))


def _reference_token(value: str) -> bool:
    return bool(value and SIMPLE_REF.fullmatch(value))


def _verse_key(value: str):
    match = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return match[1], int(match[2]), int(match[3])


def audit_osis(path: Path, *, kind: str = "bible") -> dict:
    if kind not in {"bible", "commentary"}:
        raise ValueError("Only Bible/commentary OSIS sources are supported")
    path = Path(path).absolute()
    raw = require_regular_file(path, MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
    if re.search(rb"<!DOCTYPE\b", raw, flags=re.IGNORECASE):
        raise StructureFailure(path, 1, "DOCTYPE_UNREVIEWED", "DOCTYPE declarations must not be parsed")
    document = parse_xml(path, raw, "MALFORMED_XML")
    if document.getroot().tag != NS + "osis":
        raise StructureFailure(path, document.getroot().sourceline or 1,
                               "UNEXPECTED_ROOT", "Expected an OSIS document")
    findings = []
    counts = Counter()
    verses = {}
    annotations = defaultdict(list)
    paragraph_count = 0
    previous_verse = None

    for node in document.iter():
        if not isinstance(node.tag, str):
            continue
        name = _tag(node)
        counts[name] += 1
        content = "".join(node.itertext())
        if name == "hi" and node.get("type") in {"bold", "bolditalic"}:
            if len(content) >= 170:
                findings.append(_entry(path,node,"long_bold_range",
                    reason="Long emphasized span; inspect whether an authorial heading or formatting was flattened",
                    details={"characters": len(content)}))
        if name == "p":
            paragraph_count += 1
            letters = [x for x in content if x.isalpha()]
            if len(letters) >= 80 and sum(x.isupper() for x in letters) / len(letters) >= 0.8:
                findings.append(_entry(path,node,"upper_case_paragraph",
                    reason="All-caps paragraph candidate; preserve possible authorial emphasis",
                    details={"letters": len(letters)}))
            if len(content) >= 1800:
                findings.append(_entry(path,node,"excessive_styling",
                    reason="Very long paragraph candidate; investigate printed edition before splitting",
                    details={"characters": len(content)}))
        if name == "title" and (len(content) >= 190 or
                                (len(content) >= 40 and content.isupper())):
            findings.append(_entry(path,node,"suspicious_heading",
                reason="Unusually long or uppercase heading; do not rewrite without editorial review",
                details={"characters": len(content)}))
        attrs = set(node.attrib)
        styles = sorted(x for x in attrs if x.lower() in
                        {"color", "font", "style", "font-family", "font-size", "background"})
        if styles:
            findings.append(_entry(path,node,"unknown_style",
                reason="Non-standard presentation attribute needs schema and publisher review",
                details={"attributes": styles}))
        if name == "seg" and node.get("type", "").lower().startswith(("font-size", "color", "font")):
            findings.append(_entry(path,node,"unknown_style",
                reason="Presentation-only segment; verify OSIS semantics and rendering",
                details={"segment_type": node.get("type", "")[:100]}))
        if name == "reference":
            reference = node.get("osisRef")
            if not reference or not reference.strip():
                findings.append(_entry(path,node,"invalid_cross_reference",
                    reason="Reference element lacks a usable osisRef"))
            else:
                # Complex OSIS work references and discontinuous ranges can be
                # legitimate; never mark them invalid without canonical v11n.
                parts = reference.split()
                if any(not _reference_token(piece) for piece in parts):
                    findings.append(_entry(path,node,"unreviewed_cross_reference",
                        reason="Cross reference needs a verified OSIS grammar/versification check",
                        details={"osis_ref": reference[:150]}))
        if name == "verse":
            ref = node.get("osisID") or node.get("sID")
            if not ref and not node.get("eID"):
                findings.append(_entry(path,node,"empty_verse_identifier",
                    reason="Verse has no OSIS identifier or milestone key"))
            if ref:
                if ref in verses:
                    findings.append(_entry(path,node,"duplicate_verse_id",
                        reason="Repeated verse opening/key; check actual SWORD verse indexes",
                        details={"osis_ref": ref, "first_xml_line": verses[ref]}))
                else:
                    verses[ref] = node.sourceline
                key = _verse_key(ref)
                if previous_verse and key and key[0] == previous_verse[0] and (
                    key[1], key[2]) < (previous_verse[1], previous_verse[2]):
                    findings.append(_entry(path,node,"verse_key_out_of_sequence",
                        reason="Source-order verse keys decrease within a book; validate against module versification",
                        details={"osis_ref": ref}))
                if key:
                    previous_verse = key
        if kind == "commentary" and name == "div" and node.get("annotateType") == "commentary":
            reference = node.get("annotateRef")
            if reference:
                if reference in annotations:
                    findings.append(_entry(path,node,"duplicate_commentary_reference",
                        reason="Multiple commentary entries share an annotation key; may be intentional separate sections",
                        details={"annotate_ref":reference[:150],
                                 "other_entries":len(annotations[reference])}))
                annotations[reference].append(node.sourceline)

        # A likely Bible quotation repeated in commentary is NOT automatically
        # removable. Limit to styled segments/paragraphs with several numbered
        # verse markers; this is a deliberately conservative candidate signal.
        if kind == "commentary" and name in {"p", "seg"} and len(content) >= 200:
            if name == "seg" and any(_tag(parent) == "seg" for parent in node.iterancestors()):
                continue
            number_hits = len(VERSE_MARKER.findall(content))
            if number_hits >= 5 and (
                name == "p" and not any(_tag(x) == "seg" for x in node)
                or name == "seg" and node.get("type", "").startswith("font-size")
            ):
                findings.append(_entry(path,node,"introductory_scripture_candidate",
                    reason="Numbered Bible-text block candidate; retain until excerpt boundaries and role are verified",
                    details={"numbered_markers":number_hits}))

    findings.sort(key=lambda x: (x["original_xml_line"] or 0, x["code"], x["xml_xpath"]))
    return {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "source_path": str(path),
        "kind": kind,
        "status": "audited_not_normalized",
        "source_schema_validated": False,
        "findings": findings,
        "summary": {
            "elements": dict(sorted(counts.items())),
            "verse_keys": len(verses),
            "commentary_reference_keys": len(annotations),
            "paragraphs": paragraph_count,
            "finding_counts": dict(sorted(Counter(x["code"] for x in findings).items())),
        },
        "no_content_changes": True,
        "requires_editorial_review": bool(findings),
        "caveat": "Syntactic source audit, not SWORD-versification proof, compiled-index audit, or publication approval.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--kind", choices=("bible", "commentary"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_osis(args.source, kind=args.kind)
        code = 0
    except (OSError, ValueError, StructureFailure) as exc:
        diagnostic = exc.as_dict() if isinstance(exc, StructureFailure) else {"detail":str(exc)}
        result = {"status": "blocked", "diagnostic": diagnostic, "no_content_changes": True}
        code = 1
    write_report(args.report, result)
    print(f"Source audit: {result['status']}; report: {args.report}")
    return code


if __name__ == "__main__":
    sys.exit(main())
