#!/usr/bin/env python3
"""Observe and optionally verify the original eBible USFX XSD, without rewriting.

A remote URL is mutable. Only an independently observed, reviewed SHA-256
in config/usfx-schema-policy.json can authorize using the XSD as a gate.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.request import Request, build_opener

from lxml import etree
from bible_intake import ProviderRedirects, ROOT, _safe_url

XSD_URL = "https://ebible.org/usfx.xsd"
MAX_XSD = 2 * 1024 * 1024
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSD_POLICY = ROOT / "config/usfx-schema-policy.json"


class USFXSchemaError(ValueError):
    """Schema provenance or validation could not be independently established."""


def read_official_xsd(*, opener=None) -> bytes:
    _safe_url(XSD_URL, "ebible")
    opener = opener or build_opener(ProviderRedirects("ebible"))
    req = Request(XSD_URL, headers={"User-Agent": "BibleResources-USFXSchemaAudit/1.0"})
    with closing(opener.open(req, timeout=45)) as response:
        _safe_url(response.geturl(), "ebible")
        data = response.read(MAX_XSD + 1)
    if not 0 < len(data) <= MAX_XSD:
        raise USFXSchemaError("Missing or oversized official USFX XSD")
    return data


def examine_schema(data: bytes) -> tuple[etree.XMLSchema, dict]:
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_XSD:
        raise USFXSchemaError("Invalid original XSD bytes")
    if re.search(rb"<!DOCTYPE\b|<!ENTITY\b", data, flags=re.IGNORECASE):
        raise USFXSchemaError("XSD contains DTD or entity declarations")
    try:
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                 no_network=True, recover=False, huge_tree=False)
        doc = etree.ElementTree(etree.fromstring(data, parser=parser))
        if (doc.docinfo.doctype or doc.docinfo.internalDTD or
                doc.docinfo.externalDTD or doc.getroot().tag !=
                f"{{{XSD_NS}}}schema"):
            raise USFXSchemaError("Unexpected schema XML root or DTD")
        dependencies = [
            etree.QName(node).localname
            for node in doc.getroot().iter()
            if isinstance(node.tag, str)
            and node.tag in {
                f"{{{XSD_NS}}}include", f"{{{XSD_NS}}}import",
                f"{{{XSD_NS}}}redefine", f"{{{XSD_NS}}}override"
            }
        ]
        if dependencies:
            raise USFXSchemaError("Unreviewed XSD dependency requires a separately pinned source")
        compiled = etree.XMLSchema(doc)
    except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as exc:
        raise USFXSchemaError("Official USFX schema cannot be parsed or compiled offline") from exc
    return compiled, {
        "official_xsd_sha256": sha256(data).hexdigest(),
        "official_xsd_bytes": len(data),
        "offline_compiled_without_external_dependencies": True,
        "schema_language": "W3C XML Schema 1.0",
    }


def observe_schema(data: bytes) -> dict:
    compiled, result = examine_schema(data)
    return {
        **result,
        "status": "observed_unreviewed_official_schema",
        "publisher_url": XSD_URL,
        "not_a_fidelity_or_publication_certificate": True,
        "no_bible_source_downloaded": True,
        "schema_pinned_and_reviewed": False,
    }


def validate_source_with_pinned_schema(xml: bytes, schema: bytes, policy: dict) -> dict:
    if (policy.get("schema_status") != "reviewed"
            or policy.get("download_url") != XSD_URL
            or not re.fullmatch(r"[a-f0-9]{64}", str(policy.get("sha256", "")))
            or sha256(schema).hexdigest() != policy["sha256"]):
        raise USFXSchemaError("Unapproved or drifting official USFX XSD")
    compiled, evidence = examine_schema(schema)
    from source_usfx_structure import audit_source_usfx
    # Basic XML structural checks independently reject DTD and invalid content.
    inventory = audit_source_usfx(xml)
    if inventory["source_structural_issues"]:
        return {
            **evidence, "status": "blocked_source_structural_findings",
            "official_usfx_schema_validated": False,
            "source_xml_sha256": inventory["original_xml_sha256"],
            "source_structural_issues": inventory["source_structural_issues"],
        }
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    doc = etree.ElementTree(etree.fromstring(xml, parser=parser))
    passed = compiled.validate(doc)
    # XSD validator diagnostics may include publisher content. Never expose
    # messages or original XML to the public stage report.
    findings = [
        {"line": x.line, "type": x.type_name, "domain": x.domain_name}
        for x in list(compiled.error_log)[:20]
    ]
    return {
        **evidence,
        "status": "official_usfx_xsd_validated" if passed else "blocked_official_usfx_xsd",
        "official_usfx_schema_validated": passed,
        "source_xml_sha256": inventory["original_xml_sha256"],
        "source_book_count": inventory["source_book_count"],
        "source_numbered_reference_count": inventory["numbered_source_reference_count"],
        "schema_errors_no_scripture": findings,
        "no_source_text_in_report": True,
        "source_mutated": False,
        "published": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--observe-only", action="store_true")
    mode.add_argument("--download-pinned", action="store_true")
    p.add_argument("--directory", type=Path)
    args = p.parse_args(argv)
    if args.download_pinned and args.directory is None:
        p.error("--directory is required for pinned download")
    raw = read_official_xsd()
    if args.observe_only:
        report = observe_schema(raw)
    else:
        policy = json.loads(XSD_POLICY.read_text(encoding="utf-8"))
        if (policy.get("schema_status") != "reviewed" or
                policy.get("download_url") != XSD_URL or
                sha256(raw).hexdigest() != policy.get("sha256")):
            raise USFXSchemaError("Official USFX XSD digest not reviewed or drifted")
        _, evidence = examine_schema(raw)
        if args.directory.is_symlink():
            raise USFXSchemaError("Refusing symlink XSD output directory")
        args.directory.mkdir(parents=True, exist_ok=True)
        target = args.directory / "usfx.xsd"
        if target.exists() or target.is_symlink():
            raise USFXSchemaError("Refusing to overwrite reviewed schema")
        target.write_bytes(raw)
        report = {**evidence, "status":"pinned_official_usfx_xsd_acquired"}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
