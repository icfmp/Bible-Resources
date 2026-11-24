#!/usr/bin/env python3
"""Read-only structural BRNP draft pilot; not an OSIS XSD or release gate.

No source rewriting, guessed reference mappings or published content output.
Official schema and guard_osis/guard_commentary checks remain mandatory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import re
from pathlib import Path
import sys

from lxml import etree

from guard_osis import StructureFailure, _schema, parse_xml, require_regular_file, MAX_SOURCE_BYTES, POLICY_PATH
from guard_commentary import _check_reference as check_commentary_reference

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "osis-policy.json"
NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MAX_BYTES = 128 * 1024 * 1024
VERSION = "0.3-draft"
# OSIS 2.1.1 constructs already encountered in independently XSD-valid
# resources. Preserve structured tables/lists and historical source metadata.
# This is not a supplier-specific allowlist or permission to drop content.
STANDARD_STRUCTURAL = frozenset({
    "cell", "date", "description", "identifier", "item", "language", "list",
    "refSystem", "revisionDesc", "rights", "row", "table", "type",
})



def paired_commentary_scopes(root) -> tuple[int, int, list[dict]]:
    """Check standard verse-delimited commentary without flattening prose.

    Called only for a commentary containing verse elements. No supplier ID
    or expected resource count participates. Actual XML scope, not the
    printed label or arbitrary pairing ID, determines canonical ownership.
    Separate native versification/reader proof is still required.
    """
    member_pattern = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")
    chapter_pattern = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\Z")
    errors = []
    books = []
    chapters = []
    seen_members = set()
    seen_pairs = set()
    active = None
    completed = 0

    def fail(code, node):
        errors.append({"code": code, "line": node.sourceline or 1})

    for event, node in etree.iterwalk(root, events=("start", "end")):
        if not isinstance(node.tag, str):
            continue
        tag = node.tag
        if tag == NS + "div" and node.get("type") == "book":
            if event == "start":
                if node.get("sID") or node.get("eID") or books or active:
                    fail("COMMENTARY_MILESTONE_BOOK_BOUNDARY", node)
                books.append((node, node.get("osisID")))
            else:
                if active or chapters:
                    fail("COMMENTARY_MILESTONE_BOOK_BOUNDARY", node)
                if books:
                    books.pop()
        elif tag == NS + "chapter":
            sid, eid, ident = node.get("sID"), node.get("eID"), node.get("osisID")
            if event == "start":
                if active:
                    fail("COMMENTARY_MILESTONE_CHAPTER_BOUNDARY", node)
                if eid:
                    if not chapters or chapters[-1][0] != eid:
                        fail("COMMENTARY_MILESTONE_CHAPTER_PAIR", node)
                    else:
                        chapters.pop()
                else:
                    if (chapters or len(books) != 1 or not ident
                            or not chapter_pattern.fullmatch(ident)
                            or ident.rsplit(".", 1)[0] != books[-1][1]):
                        fail("COMMENTARY_MILESTONE_CHAPTER_SCOPE", node)
                    chapters.append((sid, ident, node))
            elif not sid and not eid:
                if active:
                    fail("COMMENTARY_MILESTONE_CHAPTER_BOUNDARY", node)
                if not chapters or chapters[-1][2] is not node:
                    fail("COMMENTARY_MILESTONE_CHAPTER_PAIR", node)
                else:
                    chapters.pop()
        elif event == "start" and tag == NS + "verse":
            sid, eid, ident = node.get("sID"), node.get("eID"), node.get("osisID")
            if sid and not eid:
                members = (ident or "").split()
                valid = bool(members) and all(member_pattern.fullmatch(k) for k in members)
                if (not valid or len(set(members)) != len(members)
                        or seen_members.intersection(members)):
                    fail("COMMENTARY_MILESTONE_MEMBER_ID", node)
                if sid in seen_pairs:
                    fail("COMMENTARY_MILESTONE_PAIR_ID", node)
                if active is not None:
                    fail("COMMENTARY_MILESTONE_OVERLAP", node)
                if (len(books) != 1 or len(chapters) != 1 or not valid
                        or any(k.rsplit(".", 1)[0] != chapters[-1][1]
                               or k.split(".")[0] != books[-1][1] for k in members)):
                    fail("COMMENTARY_MILESTONE_SCOPE", node)
                if valid and [int(k.rsplit(".", 1)[1]) for k in members] != sorted(
                        int(k.rsplit(".", 1)[1]) for k in members):
                    fail("COMMENTARY_MILESTONE_MEMBER_ORDER", node)
                if len(node) or (node.text or "").strip():
                    fail("COMMENTARY_MILESTONE_NONEMPTY_MARKER", node)
                seen_pairs.add(sid)
                seen_members.update(members)
                active = (sid, tuple(books), tuple(chapters))
            elif eid and not sid and not ident:
                if len(node) or (node.text or "").strip():
                    fail("COMMENTARY_MILESTONE_NONEMPTY_MARKER", node)
                if active is None or active[0] != eid:
                    fail("COMMENTARY_MILESTONE_PAIR", node)
                else:
                    if active[1:] != (tuple(books), tuple(chapters)):
                        fail("COMMENTARY_MILESTONE_SCOPE", node)
                    completed += 1
                    active = None
            else:
                fail("COMMENTARY_MILESTONE_FORM", node)
    if active is not None:
        errors.append({"code": "COMMENTARY_MILESTONE_UNCLOSED", "line": 1})
    return completed, len(seen_members), errors


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
    allowed = set(policy["supported_elements"]) | STANDARD_STRUCTURAL
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
    chapters_seen = set()  # canonical chapter osisIDs
    chapter_pair_ids = set()
    books_seen = set()  # real book containers, not paired milestones
    book_pair_ids = set()
    books_active = []
    annotations = 0
    verse_ids = set()  # canonical OSIS IDs, never milestone pairing keys
    verse_pair_ids = set()
    verse_member_ids = set()  # individual canonical members in Bible compound IDs
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
        if tag == "language":
            parent = element.getparent()
            if (parent is None or parent.tag != NS + "work"
                    or parent.getparent() is None
                    or parent.getparent().tag != NS + "header"):
                errors.append({"code": "INVALID_STRUCTURAL_PARENT",
                               "line": line, "element": tag})
        if tag == "div" and element.get("type") == "book":
            book_id = element.get("osisID")
            start_id, end_id = element.get("sID"), element.get("eID")
            containing_book = any(
                ancestor.tag == NS + "div" and ancestor.get("type") == "book"
                and not ancestor.get("sID") and not ancestor.get("eID")
                for ancestor in element.iterancestors()
            )
            if start_id and end_id:
                errors.append({"code": "MIXED_BOOK_MILESTONE", "line": line})
            elif start_id:
                if not book_id:
                    errors.append({"code": "BOOK_MILESTONE_MISSING_CANONICAL_ID",
                                   "line": line})
                if start_id in book_pair_ids:
                    errors.append({"code": "DUPLICATE_BOOK_MILESTONE_KEY",
                                   "line": line})
                book_pair_ids.add(start_id)
                books_active.append(start_id)
                if containing_book:
                    errors.append({"code": "BOOK_MILESTONE_WITHIN_CONTAINER",
                                   "line": line})
            elif end_id:
                if not books_active or books_active[-1] != end_id:
                    errors.append({"code": "BOOK_END_PAIR", "line": line})
                else:
                    books_active.pop()
            else:
                if not book_id or book_id in books_seen:
                    errors.append({"code": "BOOK_ID" if kind == "bible"
                                   else "COMMENTARY_REPEATED_BOOK_DIVISION",
                                   "line": line})
                else:
                    books_seen.add(book_id)
                if containing_book:
                    errors.append({"code": "NESTED_BOOK", "line": line})
        # The official XSD checks much more; these non-negotiable local
        # relationships must also hold in a schema-less pilot run.
        parent = element.getparent()
        parent_tag = parent.tag if parent is not None else None
        expected_parent = {"row": "table", "cell": "row", "item": "list"}
        if tag in expected_parent and parent_tag != NS + expected_parent[tag]:
            errors.append({"code": "INVALID_STRUCTURAL_PARENT", "line": line,
                           "element": tag, "expected": expected_parent[tag]})
        if tag in {"chapter", "verse"} and kind == "bible":
            book_ancestors = [
                ancestor.get("osisID") for ancestor in element.iterancestors()
                if ancestor.tag == NS + "div" and ancestor.get("type") == "book"
            ]
            if len(book_ancestors) != 1:
                errors.append({"code": "BOOK_SCOPE", "line": line, "element": tag})
            else:
                # Compound OSIS identifiers must retain their established
                # original versification; every member belongs to this book.
                canonical = element.get("osisID")
                if canonical and not all(
                    part.startswith(book_ancestors[0] + ".")
                    for part in canonical.split()
                ):
                    errors.append({"code": "REFERENCE_BOOK_SCOPE", "line": line,
                                   "element": tag})
            if tag == "verse" and element.get("osisID"):
                chapter_containers = [
                    ancestor.get("osisID") for ancestor in element.iterancestors()
                    if ancestor.tag == NS + "chapter" and ancestor.get("osisID")
                       and not ancestor.get("sID") and not ancestor.get("eID")
                ]
                if len(chapter_containers) == 1:
                    chapter_id = chapter_containers[0]
                    if not all(part.startswith(chapter_id + ".")
                               for part in element.get("osisID").split()):
                        errors.append({"code": "REFERENCE_CHAPTER_SCOPE", "line": line})
                elif not chapter_containers and chapters_active:
                    chapter_id = chapters_active[-1][2]
                    if chapter_id and not all(
                        part.startswith(chapter_id + ".")
                        for part in element.get("osisID").split()
                    ):
                        errors.append({"code": "REFERENCE_CHAPTER_SCOPE", "line": line})
        if tag == "chapter":
            start, end, identifier = element.get("sID"), element.get("eID"), element.get("osisID")
            if (start and end) or (end and identifier):
                errors.append({"code": "MIXED_CHAPTER_MILESTONE", "line": line})
            elif start:
                if not identifier or identifier in chapters_seen or start in chapter_pair_ids:
                    errors.append({"code": "CHAPTER_START_ID", "line": line})
                chapters_active.append((start, line, identifier))
                chapter_pair_ids.add(start)
                if identifier:
                    chapters_seen.add(identifier)
            elif end:
                if not chapters_active or chapters_active[-1][0] != end:
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
                members = identifier.split() if identifier else []
                duplicates = [m for m in members if kind == "bible" and
                              m in verse_member_ids]
                if (not identifier or identifier in verse_ids or start in verse_pair_ids
                        or len(members) != len(set(members)) or duplicates):
                    reason = ("missing_osisID" if not identifier else
                              "duplicate_osisID" if identifier in verse_ids or duplicates
                              or len(members) != len(set(members)) else "duplicate_sID")
                    errors.append({"code": "VERSE_START_ID", "line": line, "reason": reason})
                active.append(start)
                verse_pair_ids.add(start)
                if identifier:
                    verse_ids.add(identifier)
                    if kind == "bible":
                        verse_member_ids.update(members)
            elif end:
                if not active or active[-1] != end:
                    errors.append({"code": "VERSE_END_PAIR", "line": line})
                else:
                    active.pop()
            elif (not identifier or identifier in verse_ids
                  or (kind == "bible" and (
                      len(identifier.split()) != len(set(identifier.split()))
                      or any(m in verse_member_ids for m in identifier.split())))):
                errors.append({"code": "VERSE_CONTAINER_ID", "line": line})
            else:
                verse_ids.add(identifier)
                if kind == "bible":
                    verse_member_ids.update(identifier.split())
        if tag == "div" and element.get("annotateType") == "commentary":
            annotations += 1
            if kind != "commentary":
                errors.append({"code": "ANNOTATION_KIND", "line": line})
            reference = element.get("annotateRef")
            if not reference or not reference.strip():
                errors.append({"code": "ANNOTATE_REF", "line": line})
            else:
                try:
                    # Reuse the already-reviewed commentary grammar; do not
                    # invent a second looser parser for the same references.
                    check_commentary_reference(path, element, reference)
                except StructureFailure as exc:
                    errors.append({"code": "COMMENTARY_REFERENCE_INVALID",
                                   "line": line, "guard_code": exc.code})
        if tag == "div" and element.get("annotateRef") and element.get("annotateType") != "commentary":
            errors.append({"code": "ANNOTATION_TYPE", "line": line})
        if tag == "reference":
            # A printed reference label is not a verified OSIS target.
            # Report missing/unreviewed destinations; never guess one.
            target = element.get("osisRef")
            if not target or not target.strip():
                if (element.get("type") == "annotateRef"
                        and element.get("subType") == "x-origin"):
                    # Origin is a reference *source*, not a link destination.
                    # Its transport-specific markup still needs reviewed
                    # canonical mapping; it is not a missing link target.
                    code = "NONCANONICAL_REFERENCE_ORIGIN"
                elif element.get("subType") == "x-introduction":
                    code = "UNRESOLVED_INTRODUCTION_SPAN"
                else:
                    code = "UNRESOLVED_REFERENCE_TARGET"
                errors.append({"code": code, "line": line})
            elif target != target.strip():
                errors.append({"code": "REFERENCE_TARGET_WHITESPACE", "line": line})
        if tag == "l" and not any(
            ancestor.tag == NS + "lg" for ancestor in element.iterancestors()
        ):
            errors.append({"code": "POETRY_LINE_OUTSIDE_GROUP", "line": line})
    if books_active:
        errors.append({"code": "UNCLOSED_BOOK_MILESTONE", "count": len(books_active)})
    if active:
        errors.append({"code": "UNCLOSED_VERSE_MILESTONE", "count": len(active)})
    if chapters_active:
        errors.append({"code": "UNCLOSED_CHAPTER_MILESTONE", "count": len(chapters_active),
                       "line": chapters_active[-1][1]})
    if kind == "bible" and not books_seen:
        errors.append({"code": "NO_BOOK_DIVISIONS"})
    paired_entries = 0
    paired_members = 0
    representation = "annotated_divisions" if kind == "commentary" else "bible"
    if kind == "commentary" and next(root.iter(NS + "verse"), None) is not None:
        representation = "paired_verse_milestones"
        paired_entries, paired_members, scope_errors = paired_commentary_scopes(root)
        errors.extend(scope_errors)
        if annotations:
            errors.append({"code": "COMMENTARY_MIXED_REPRESENTATIONS"})
    if kind == "commentary" and not annotations and not paired_entries:
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
        "status": ("findings_need_review" if errors else
                   "draft_subset_no_findings" if official is not None else
                   "diagnostic_only_schema_not_checked"),
        "brnp_conformance_certified": False,
        "element_counts": dict(sorted(counts.items())),
        "commentary_entry_count": annotations + paired_entries,
        "commentary_representation": representation,
        "annotated_commentary_entry_count": annotations,
        "paired_commentary_entry_count": paired_entries,
        "paired_commentary_member_count": paired_members,
        "verse_identifier_count": len(verse_ids),
        "verse_pair_identifier_count": len(verse_pair_ids),
        "book_identifier_count": len(books_seen),
        "book_milestone_pair_identifier_count": len(book_pair_ids), "chapter_identifier_count": len(chapters_seen),
        "chapter_pair_identifier_count": len(chapter_pair_ids),
        "bible_verse_member_count": len(verse_member_ids),
        "findings": errors[:100], "finding_count": len(errors),
        "finding_examples_by_code": {
            code: next(item for item in errors if item["code"] == code)
            for code in sorted({item["code"] for item in errors})
        },
        "finding_codes": dict(sorted(Counter(e["code"] for e in errors).items())),
        "unreviewed_elements": dict(sorted(Counter(
            e["element"] for e in errors if e["code"] == "UNREVIEWED_ELEMENT"
        ).items())),
        "verse_start_reasons": dict(sorted(Counter(
            e["reason"] for e in errors if e["code"] == "VERSE_START_ID"
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
