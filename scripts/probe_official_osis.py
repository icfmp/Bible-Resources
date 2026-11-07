#!/usr/bin/env python3
"""Inspect CrossWire's official OSIS XSD without trusting a live schema for import.

Reports SHA-256, structural dependencies and offline XMLSchema compilation.
Does NOT update the reviewed policy or authorize publication automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlsplit
from lxml import etree

from guard_osis import MAX_SCHEMA_BYTES, parse_xml, StructureFailure, ROOT

SCHEMA_URL = "https://www.crosswire.org/~dmsmith/osis/osisCore.2.1.1-cw-latest.xsd"
XML_SCHEMA_URL = "https://www.w3.org/2001/xml.xsd"
XSD_NS = "{http://www.w3.org/2001/XMLSchema}"


def inspect_bytes(raw: bytes, *, origin: str = "official-signed-url") -> dict:
    if not raw or len(raw) > MAX_SCHEMA_BYTES:
        raise ValueError("Official OSIS XSD is missing or too large")
    # Parse in memory without remote DTD, external entity or import access.
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True,
                             recover=False, huge_tree=False)
    node = etree.fromstring(raw, parser)
    if node.tag != XSD_NS + "schema":
        raise ValueError("Not an XML Schema document")
    deps = [{
        "kind": e.tag.split("}")[-1],
        "namespace": e.get("namespace"),
        "schema_location": e.get("schemaLocation"),
        "line": e.sourceline
    } for e in node.iter()
        if e.tag in {XSD_NS + t for t in ("import", "include", "redefine", "override")}]
    result = {
        "schema_url": SCHEMA_URL,
        "origin": origin,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "target_namespace": node.get("targetNamespace"),
        "schema_dependencies": deps,
        "can_use_existing_guard_without_dependency_review": not deps,
        "ready_to_pin": False,
    }
    if not deps:
        try:
            etree.XMLSchema(etree.ElementTree(node))
        except etree.XMLSchemaParseError as exc:
            result["compilation_error"] = str(exc).splitlines()[0]
        else:
            result["ready_to_pin"] = True
    else:
        result["reason"] = "Referenced schemas need separately reviewed and pinned dependency copies"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--url", default=SCHEMA_URL,
                        help="For tests only; production review always requires exact CrossWire URL")
    args = parser.parse_args(argv)
    if args.url != SCHEMA_URL:
        print("Only the reviewed CrossWire schema URL is allowed", file=sys.stderr)
        return 2
    try:
        request = urllib.request.Request(args.url, headers={
            "User-Agent": "BibleResources-OSIS-SchemaReview/1.0"})
        with urllib.request.urlopen(request, timeout=40) as response:
            if urlsplit(response.url).scheme != "https" or urlsplit(response.url).hostname != "www.crosswire.org":
                raise ValueError("Unexpected schema download redirect")
            raw = response.read(MAX_SCHEMA_BYTES + 1)
        report = inspect_bytes(raw, origin="https://www.crosswire.org (read-only)")
        # Inspect the single W3C dependency explicitly. No source validation is
        # authorized until the two hashes are manually reviewed and pinned.
        if (len(report["schema_dependencies"]) == 1
                and report["schema_dependencies"][0]["kind"] == "import"
                and report["schema_dependencies"][0]["namespace"] ==
                    "http://www.w3.org/XML/1998/namespace"
                and report["schema_dependencies"][0]["schema_location"] ==
                    "http://www.w3.org/2001/xml.xsd"):
            dependency_request = urllib.request.Request(XML_SCHEMA_URL, headers={
                "User-Agent": "BibleResources-OSIS-SchemaReview/1.0"})
            with urllib.request.urlopen(dependency_request, timeout=40) as response:
                if urlsplit(response.url).scheme != "https" or urlsplit(response.url).hostname != "www.w3.org":
                    raise ValueError("Unexpected W3C dependency download redirect")
                content = response.read(MAX_SCHEMA_BYTES + 1)
            dependency = inspect_bytes(content, origin="https://www.w3.org (read-only)")
            report["official_xml_dependency"] = {
                "url": XML_SCHEMA_URL,
                "sha256": dependency["sha256"],
                "bytes": dependency["size_bytes"],
                "target_namespace": dependency["target_namespace"],
                "dependencies": dependency["schema_dependencies"],
                "standalone_compiles": dependency["ready_to_pin"],
            }
        report["status"] = "schema_inspected_not_approved"
    except (OSError, ValueError, etree.XMLSyntaxError) as exc:
        report = {"status": "blocked", "error": str(exc), "ready_to_pin": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
