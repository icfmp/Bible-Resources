#!/usr/bin/env python3
"""Read-only structural BRNP v0.1 pilot; not an OSIS XSD or release gate.

No source rewriting, guessed reference mappings or published content output.
Official schema and guard_osis/guard_commentary checks remain mandatory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from lxml import etree

from guard_osis import StructureFailure, _schema, parse_xml, require_regular_file, MAX_SOURCE_BYTES, POLICY_PATH

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "osis-policy.json"
NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MAX_BYTES = 128 * 1024 * 1024
VERSION = "0.1"


def check(path: Path, kind: str, *, schema_path: Path | None = None) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("input must be a regular XML file at most 128 MiB")
    # The optional official-XSD check is independent of BRNP's narrower
    # project profile. A BRNP-only result is never a publication certificate.
    official = None
    if schema_path is not None:
        # The pinned XSD and the stricter existing project allowlist are
        # separate checks. Do not mistake unsupported metadata (e.g.
        # revisionDesc) for an XML schema failure.
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        schema, pinned_hash = _schema(policy, schema_path.absolute())
        raw = require_regular_file(path.absolute(), MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
        doc = parse_xml(path.absolute(), raw, "MALFORMED_XML")
        if not schema.validate(doc):
            issue = schema.error_log[0]
            raise StructureFailure(path, issue.line or 1, "OSIS_SCHEMA_INVALID",
                                   issue.message, issue.column or None)
        official = {"schema_sha256": pinned_hash, "source_sha256": sha256(raw).hexdigest()}
    content = path.read_bytes()
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    allowed = set(policy["supported_elements"])
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    root = etree.fromstring(content, parser=parser)
    errors = []
    counts = Counter()
    if root.tag != NS + "osis":
        errors.append({"code": "ROOT", "line": root.sourceline or 1})
    texts = root.findall(NS + "osisText")
    if len(texts) != 1:
        errors.append({"code": "OSIS_TEXT_COUNT", "line": root.sourceline or 1})
    for text in texts:
        if not text.get("osisIDWork") or not text.get("osisRefWork"):
            errors.append({"code": "WORK_IDENTITY", "line": text.sourceline or 1})
    active = []
    chapters_active = []
    chapters_seen = set()
    books_seen = set()
    annotations = 0
    verse_ids = set()
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        line = element.sourceline or 1
        if not element.tag.startswith(NS):
            errors.append({"code": "FOREIGN_NAMESPACE", "line": line})
            continue
        tag = element.tag[len(NS):]
        counts[tag] += 1
        if tag not in allowed:
            errors.append({"code": "UNREVIEWED_ELEMENT", "line": line, "element": tag})
        if tag == "div" and element.get("type") == "book":
            book_id = element.get("osisID")
            if not book_id or book_id in books_seen:
                errors.append({"code": "BOOK_ID", "line": line})
            else:
                books_seen.add(book_id)
        if tag == "chapter":
            start, end, identifier = element.get("sID"), element.get("eID"), element.get("osisID")
            if (start and end) or (end and identifier):
                errors.append({"code": "MIXED_CHAPTER_MILESTONE", "line": line})
            elif start:
                if not identifier or identifier != start or identifier in chapters_seen:
                    errors.append({"code": "CHAPTER_START_ID", "line": line})
                chapters_active.append(start)
                chapters_seen.add(start)
            elif end:
                if not chapters_active or chapters_active[-1] != end:
                    errors.append({"code": "CHAPTER_END_PAIR", "line": line})
                else:
                    chapters_active.pop()
            elif not identifier or identifier in chapters_seen:
                errors.append({"code": "CHAPTER_CONTAINER_ID", "line": line})
            else:
                chapters_seen.add(identifier)
        if tag == "verse":
            start, end, identifier = element.get("sID"), element.get("eID"), element.get("osisID")
            if start and end or (end and identifier):
                errors.append({"code": "MIXED_VERSE_MILESTONE", "line": line})
            elif start:
                if not identifier or start != identifier or start in verse_ids:
                    errors.append({"code": "VERSE_START_ID", "line": line})
                active.append(start)
                verse_ids.add(start)
            elif end:
                if not active or active[-1] != end:
                    errors.append({"code": "VERSE_END_PAIR", "line": line})
                else:
                    active.pop()
            elif not identifier or identifier in verse_ids:
                errors.append({"code": "VERSE_CONTAINER_ID", "line": line})
            else:
                verse_ids.add(identifier)
        if tag == "div" and element.get("annotateType") == "commentary":
            annotations += 1
            if kind != "commentary":
                errors.append({"code": "ANNOTATION_KIND", "line": line})
            if not element.get("annotateRef") or not element.get("annotateRef").strip():
                errors.append({"code": "ANNOTATE_REF", "line": line})
        if tag == "div" and element.get("annotateRef") and element.get("annotateType") != "commentary":
            errors.append({"code": "ANNOTATION_TYPE", "line": line})
        if tag == "reference" and element.get("osisRef") == "":
            errors.append({"code": "EMPTY_REFERENCE", "line": line})
    if active:
        errors.append({"code": "UNCLOSED_VERSE_MILESTONE", "count": len(active)})
    if chapters_active:
        errors.append({"code": "UNCLOSED_CHAPTER_MILESTONE", "count": len(chapters_active)})
    if kind == "bible" and not books_seen:
        errors.append({"code": "NO_BOOK_DIVISIONS"})
    if kind == "commentary" and not annotations:
        errors.append({"code": "NO_COMMENTARY_ENTRIES"})
    if kind == "bible" and not verse_ids:
        errors.append({"code": "NO_NUMBERED_VERSES"})
    return {
        "profile": "BRNP", "profile_version": VERSION,
        "official_osis": ({
            "status": "validated",
            "schema_sha256": official["schema_sha256"],
            "source_sha256": official["source_sha256"],
        } if official is not None else {"status": "not_run"}),
        "publication_approved": False,
        "kind": kind, "sha256": sha256(content).hexdigest(),
        "status": "blocked" if errors else "pilot_structural_checks_passed",
        "element_counts": dict(sorted(counts.items())),
        "commentary_entry_count": annotations, "verse_identifier_count": len(verse_ids),
        "book_identifier_count": len(books_seen), "chapter_identifier_count": len(chapters_seen),
        "findings": errors[:100], "finding_count": len(errors),
        "finding_codes": dict(sorted(Counter(e["code"] for e in errors).items())),
        "unreviewed_elements": dict(sorted(Counter(
            e["element"] for e in errors if e["code"] == "UNREVIEWED_ELEMENT"
        ).items())),
        "limitations": [
            "Official OSIS XSD is checked only when --schema is supplied; neither route proves historical/authorial fidelity",
            "NOT a complete verse hierarchy, reference target, annotation or reader validation",
            "NOT a production or publication approval gate",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--kind", choices=["bible", "commentary"], required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--schema", type=Path,
                        help="Run existing pinned official XSD guard before BRNP; required for joint evidence")
    args = parser.parse_args()
    if args.report.resolve() == args.source.resolve():
        parser.error("report must not overwrite original")
    try:
        result = check(args.source, args.kind, schema_path=args.schema)
    except (ValueError, OSError, etree.XMLSyntaxError, StructureFailure, KeyError) as exc:
        print(f"BRNP pilot blocked: {exc}", file=sys.stderr)
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"BRNP v{VERSION}: {result['status']}; {result['finding_count']} findings")
    return 0 if not result["finding_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
