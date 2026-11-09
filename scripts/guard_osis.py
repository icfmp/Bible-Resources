#!/usr/bin/env python3
"""Fail-closed OSIS source gate. Read-only: never rewrite Scripture or markup.

This is a prerequisite for a future rule-based normalizer, NOT a converter.
OSIS validity is determined by the reviewed, SHA-256-pinned CrossWire XSD;
a separate explicit policy restricts structures we have reviewed so far.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/osis-policy.json"
MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_SCHEMA_BYTES = 8 * 1024 * 1024
SHA256 = re.compile(r"^[a-f0-9]{64}$")


class StructureFailure(Exception):
    """A diagnostic with source path, line and optional column (never guessed)."""

    def __init__(self, file: Path, line: int, code: str, detail: str, column: int | None = None):
        super().__init__(detail)
        self.file = str(file)
        self.line = max(1, int(line))
        self.column = column
        self.code = code
        self.detail = detail

    def __str__(self):
        location = f"{self.file}:{self.line}"
        if self.column is not None:
            location += f":{self.column}"
        return f"{location}: [{self.code}] {self.detail}"

    def as_dict(self):
        result = dict(file=self.file, line=self.line, code=self.code, detail=self.detail)
        if self.column is not None:
            result["column"] = self.column
        return result


def require_regular_file(path: Path, maximum: int, code: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise StructureFailure(path, 1, code, "Expected an existing regular file (not a symlink)")
    if path.stat().st_size > maximum:
        raise StructureFailure(path, 1, code, f"File exceeds {maximum} bytes")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise StructureFailure(path, 1, code, str(exc)) from exc


def parse_xml(path: Path, content: bytes, code: str):
    parser = etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        remove_blank_text=False, remove_comments=False, remove_pis=False,
        recover=False, huge_tree=False,
    )
    try:
        return etree.ElementTree(etree.fromstring(content, parser=parser, base_url=path.as_uri()))
    except etree.XMLSyntaxError as exc:
        line, col = exc.position
        raise StructureFailure(path, line, code, str(exc).split(", line ")[0], col) from exc


def _schema(policy: dict, schema_path: Path):
    if policy.get("schema_status") != "reviewed":
        raise StructureFailure(POLICY_PATH, 1, "SCHEMA_NOT_REVIEWED",
                               "Official OSIS schema and its pinned digest must be reviewed before any real import")
    pinned = policy.get("schema_sha256")
    if not isinstance(pinned, str) or not SHA256.fullmatch(pinned):
        raise StructureFailure(POLICY_PATH, 1, "UNPINNED_SCHEMA",
                               "Pin the reviewed CrossWire OSIS XSD SHA-256 in config/osis-policy.json before processing real sources")
    content = require_regular_file(schema_path, MAX_SCHEMA_BYTES, "SCHEMA_UNAVAILABLE")
    digest = hashlib.sha256(content).hexdigest()
    if digest != pinned:
        raise StructureFailure(schema_path, 1, "SCHEMA_HASH_MISMATCH",
                               f"Schema digest {digest} does not match the reviewed pinned checksum {pinned}")
    document = parse_xml(schema_path, content, "SCHEMA_XML_INVALID")
    # Only explicitly pinned official XSD dependencies can be resolved
    # locally; XMLSchema compilation must never fetch arbitrary import URLs.
    xsd_ns = "{http://www.w3.org/2001/XMLSchema}"
    deps = policy.get("schema_dependencies", [])
    if not isinstance(deps, list):
        raise StructureFailure(POLICY_PATH, 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                               "Schema dependency policy must be a list")
    expected = {}
    for dep in deps:
        if not isinstance(dep, dict):
            raise StructureFailure(POLICY_PATH, 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                                   "Malformed pinned schema dependency")
        location, filename, namespace, pin = (
            dep.get("schema_location"), dep.get("local_filename"),
            dep.get("namespace"), dep.get("sha256")
        )
        if (not isinstance(location, str) or location not in {
                "http://www.w3.org/2001/xml.xsd"
            } or filename != "xml.xsd" or
            namespace != "http://www.w3.org/XML/1998/namespace" or
            not isinstance(pin, str) or not SHA256.fullmatch(pin) or
            location in expected):
            raise StructureFailure(POLICY_PATH, 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                                   "Only the exact reviewed W3C xml.xsd import is allowed")
        local = schema_path.parent / filename
        dep_data = require_regular_file(local, MAX_SCHEMA_BYTES, "SCHEMA_DEPENDENCY_MISSING")
        if hashlib.sha256(dep_data).hexdigest() != pin:
            raise StructureFailure(local, 1, "SCHEMA_DEPENDENCY_HASH_MISMATCH",
                                   "The pinned W3C xml.xsd checksum changed")
        dep_document = parse_xml(local, dep_data, "SCHEMA_DEPENDENCY_XML_INVALID")
        if (dep_document.getroot().tag != xsd_ns + "schema" or
                dep_document.getroot().get("targetNamespace") != namespace):
            raise StructureFailure(local, 1, "SCHEMA_DEPENDENCY_INVALID",
                                   "Unexpected W3C XML schema namespace")
        if any(node.tag in {xsd_ns + n for n in ("import", "include", "redefine", "override")}
               for node in dep_document.iter()):
            raise StructureFailure(local, 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                                   "Nested schema dependency needs separate review")
        expected[location] = local

    actual = []
    for node in document.iter():
        if node.tag in {xsd_ns + n for n in ("import", "include", "redefine", "override")}:
            location = node.get("schemaLocation")
            if (node.tag != xsd_ns + "import" or location not in expected or
                    node.get("namespace") != "http://www.w3.org/XML/1998/namespace"):
                raise StructureFailure(schema_path, node.sourceline or 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                                       "Schema references an unreviewed dependency")
            actual.append(location)
    if set(actual) != set(expected) or len(actual) != len(expected):
        raise StructureFailure(schema_path, 1, "SCHEMA_DEPENDENCY_UNREVIEWED",
                               "Schema imports do not match the pinned dependency manifest")

    class PinnedResolver(etree.Resolver):
        def resolve(self, url, pubid, context):
            if url in expected:
                return self.resolve_filename(str(expected[url]), context)
            raise OSError("Unreviewed XML schema location: " + str(url))

    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    parser.resolvers.add(PinnedResolver())
    try:
        tree = etree.ElementTree(etree.fromstring(content, parser=parser,
                                                base_url=schema_path.as_uri()))
        return etree.XMLSchema(tree), digest
    except etree.XMLSchemaParseError as exc:
        entry = exc.error_log.last_error
        raise StructureFailure(schema_path, entry.line if entry else 1,
                               "SCHEMA_INVALID", str(exc)) from exc


def inspect(source_path: Path, schema_path: Path, policy_path: Path = POLICY_PATH) -> dict:
    """Validate exactly one source or raise at first undecidable construct."""
    source_path = Path(source_path).absolute()
    schema_path = Path(schema_path).absolute()
    policy_path = Path(policy_path).absolute()
    try:
        policy = json.loads(require_regular_file(policy_path, 512 * 1024, "POLICY_MISSING").decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise StructureFailure(policy_path, 1, "POLICY_INVALID", str(exc)) from exc
    if policy.get("version") != 1 or not isinstance(policy.get("supported_elements"), list):
        raise StructureFailure(policy_path, 1, "POLICY_INVALID", "Unsupported OSIS policy version or missing element rules")
    if policy.get("namespace") != "http://www.bibletechnologies.net/2003/OSIS/namespace":
        raise StructureFailure(policy_path, 1, "POLICY_INVALID", "Unexpected OSIS namespace")
    supported = policy["supported_elements"]
    if not supported or len(supported) != len(set(supported)) or not all(
        isinstance(item, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", item) for item in supported
    ):
        raise StructureFailure(policy_path, 1, "POLICY_INVALID", "Invalid reviewed element allowlist")
    schema, schema_hash = _schema(policy, schema_path)
    raw = require_regular_file(source_path, MAX_SOURCE_BYTES, "SOURCE_UNAVAILABLE")
    if re.search(rb"<!DOCTYPE\b", raw, re.IGNORECASE):
        position = re.search(rb"<!DOCTYPE\b", raw, re.IGNORECASE).start()
        raise StructureFailure(source_path, raw[:position].count(b"\n") + 1, "DOCTYPE_UNREVIEWED",
                               "Document types and external entity declarations are not approved")
    doc = parse_xml(source_path, raw, "MALFORMED_XML")
    root = doc.getroot()
    namespace = "{" + policy["namespace"] + "}"
    if root.tag != namespace + "osis":
        raise StructureFailure(source_path, root.sourceline or 1, "UNEXPECTED_ROOT",
                               "Expected an OSIS 2.1.1 <osis> document, not another XML format")
    if not schema.validate(doc):
        issue = schema.error_log[0]
        raise StructureFailure(source_path, issue.line or 1, "OSIS_SCHEMA_INVALID",
                               issue.message, issue.column or None)

    starts = {}
    used = set()
    counts = Counter()
    for elem in doc.iter():
        if isinstance(elem, etree._Comment):
            # Preserve provenance/editorial comments as authored. Processing
            # instructions remain blocked and cannot be treated as comments.
            if len(elem.text or "") > 4096:
                raise StructureFailure(source_path, elem.sourceline or 1,
                                       "UNREVIEWED_COMMENT_SIZE",
                                       "Overlong XML comment requires explicit human review")
            counts["xml_comment"] += 1
            continue
        if not isinstance(elem.tag, str):
            raise StructureFailure(source_path, elem.sourceline or 1, "UNREVIEWED_NODE",
                                   "XML processing instructions or non-element nodes require review")
        if not elem.tag.startswith(namespace):
            raise StructureFailure(source_path, elem.sourceline or 1, "UNREVIEWED_NAMESPACE",
                                   f"Unexpected namespaced element {elem.tag}")
        tag = elem.tag[len(namespace):]
        if tag not in supported:
            raise StructureFailure(source_path, elem.sourceline or 1, "UNREVIEWED_ELEMENT",
                                   f"<{tag}> is valid XML but has no reviewed normalization rule; extend policy and tests first")
        counts[tag] += 1
        if tag == "hi":
            kind = elem.get("type")
            if kind not in policy.get("reviewed_hi_types", []):
                raise StructureFailure(source_path, elem.sourceline or 1, "UNREVIEWED_EMPHASIS",
                                       f"<hi type={kind!r}> requires an explicit reviewed rule")
        if tag == "l" and elem.get("level") is not None:
            level = elem.get("level", "")
            if not re.fullmatch(r"[1-9][0-9]*", level):
                raise StructureFailure(source_path, elem.sourceline or 1, "UNREVIEWED_POETRY_LEVEL",
                                       f"Unrecognized OSIS poetry line level {level!r}")
        sid, eid = elem.get("sID"), elem.get("eID")
        if sid and eid:
            raise StructureFailure(source_path, elem.sourceline or 1, "INVALID_MILESTONE",
                                   f"<{tag}> has both sID and eID")
        if sid:
            if sid in used:
                raise StructureFailure(source_path, elem.sourceline or 1, "DUPLICATE_MILESTONE",
                                       f"Duplicate sID {sid!r}")
            used.add(sid)
            starts[sid] = (tag, elem.sourceline or 1)
        if eid:
            prior = starts.pop(eid, None)
            if prior is None:
                raise StructureFailure(source_path, elem.sourceline or 1, "UNMATCHED_MILESTONE",
                                       f"End marker {eid!r} has no preceding start marker")
            if prior[0] != tag:
                raise StructureFailure(source_path, elem.sourceline or 1, "MILESTONE_TYPE_MISMATCH",
                                       f"End <{tag}> {eid!r} does not match start <{prior[0]}> on line {prior[1]}")
    if starts:
        sid, (tag, line) = next(iter(starts.items()))
        raise StructureFailure(source_path, line, "UNCLOSED_MILESTONE",
                               f"<{tag} sID={sid!r}> has no matching eID")
    return {
        "status": "validated",
        "source_file": str(source_path),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "schema_sha256": schema_hash,
        "policy_sha256": hashlib.sha256(
            json.dumps(policy, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "elements": dict(sorted(counts.items())),
        "no_transformation_performed": True,
    }


def write_report(path: Path, value: dict) -> None:
    """Atomic report replacement, including blocked results (no stale 'success')."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".osis-report-", delete=False) as output:
            name = output.name
            json.dump(value, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--schema", type=Path, required=True,
                        help="Locally reviewed, pinned official OSIS 2.1.1 XSD")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        value = inspect(args.source, args.schema, args.policy)
        exit_code = 0
        print(f"{args.source}: OSIS source validated; original bytes preserved")
    except StructureFailure as exc:
        value = dict(status="blocked", diagnostic=exc.as_dict(), no_transformation_performed=True)
        exit_code = 1
        print(exc, file=sys.stderr)
    if args.report:
        write_report(args.report, value)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
