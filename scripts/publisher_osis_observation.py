#!/usr/bin/env python3
"""Observe an explicitly reviewed publisher's unpinned official OSIS XML.

This independent, read-only source intake records metadata only. An observed
hash is never silently accepted as a reviewed source pin, full source parity
certificate, transformation authorization or publication permission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import ssl
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, HTTPSHandler

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 128 * 1024 * 1024
SAFE_RESOURCE = re.compile(r"[a-z0-9][a-z0-9-]{1,48}\Z")
ALLOWLIST_HOSTS = frozenset({"cdn.editeurbpc.com"})
SAFE_TYPES = frozenset({"book", "chapter", "paragraph", "section", "x-p", "crossReference", "translation", "study", "variant", "x-unknown"})


class PublisherOSISObservationError(ValueError):
    """The source is unreviewed, ambiguous, unavailable or unsafe."""


def _verified_url(raw):
    if not isinstance(raw, str):
        raise PublisherOSISObservationError("Unreviewed publisher URL")
    parsed = urlsplit(raw)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWLIST_HOSTS
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not parsed.path.endswith(".xml")
            or ".." in parsed.path.split("/")):
        raise PublisherOSISObservationError("Publisher URL is not reviewed HTTPS OSIS")
    return raw


class _ReviewedRedirect(HTTPRedirectHandler):
    def __init__(self):
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        if self.count > 3:
            raise PublisherOSISObservationError("Excessive publisher redirects")
        _verified_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _source_config(resource_id):
    if not isinstance(resource_id, str) or not SAFE_RESOURCE.fullmatch(resource_id):
        raise PublisherOSISObservationError("Invalid research resource ID")
    file = ROOT / "config" / "publisher-osis" / f"{resource_id}.json"
    if not file.is_file() or file.is_symlink():
        raise PublisherOSISObservationError("No reviewed official OSIS source candidate")
    try:
        cfg = json.loads(file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise PublisherOSISObservationError("Invalid reviewed OSIS candidate manifest") from exc
    if (not isinstance(cfg, dict) or set(cfg) != {
            "resource_id", "edition", "official_source_url", "status"}
            or cfg.get("resource_id") != resource_id
            or cfg.get("status") != "research_only"
            or not isinstance(cfg.get("edition"), str)
            or not 2 <= len(cfg["edition"]) <= 128):
        raise PublisherOSISObservationError("Unsafe official OSIS candidate manifest")
    _verified_url(cfg["official_source_url"])
    return cfg


def _download(url, *, opener=None):
    opener = opener or build_opener(_ReviewedRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    req = Request(url, headers={"User-Agent": "BibleResources-ReadOnlyPublisherOSISResearch/1.0",
                                "Accept": "application/xml, text/xml, application/octet-stream"})
    try:
        with opener.open(req, timeout=90) as response:
            actual = response.geturl()
            _verified_url(actual)
            size = 0
            fragments = []
            while True:
                block = response.read(min(256 * 1024, MAX_BYTES + 1 - size))
                if not block:
                    break
                size += len(block)
                if size > MAX_BYTES:
                    raise PublisherOSISObservationError("Official OSIS is too large")
                fragments.append(block)
    except PublisherOSISObservationError:
        raise
    except (OSError, TimeoutError) as exc:
        raise PublisherOSISObservationError("Official OSIS acquisition failed") from exc
    if size < 128:
        raise PublisherOSISObservationError("Official OSIS is unexpectedly short")
    return b"".join(fragments)


def _name(node):
    return etree.QName(node).localname if isinstance(node.tag, str) else ""


def inspect_official_osis(xml):
    if not isinstance(xml, bytes) or not 128 <= len(xml) <= MAX_BYTES:
        raise PublisherOSISObservationError("Invalid official OSIS size")
    if re.search(rb"<!DOCTYPE\b|<!ENTITY\b", xml, flags=re.IGNORECASE):
        raise PublisherOSISObservationError("Original source contains a DTD or entity declaration")
    try:
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                 no_network=True, recover=False, huge_tree=False)
        root = etree.fromstring(xml, parser)
    except (ValueError, etree.XMLSyntaxError) as exc:
        raise PublisherOSISObservationError("Publisher source is not strict OSIS XML") from exc
    if _name(root) != "osis" or any(isinstance(n, etree._Entity) for n in root.iter()):
        raise PublisherOSISObservationError("Unexpected publisher OSIS structure")
    elements = Counter()
    attributes = Counter()
    note_markers = Counter()
    note_types = Counter()
    for node in root.iter():
        tag = _name(node)
        if not tag:
            continue
        elements[tag] += 1
        attributes.update(etree.QName(a).localname for a in node.attrib)
        if tag == "note":
            n = node.get("n")
            if n is None or n == "":
                note_markers["absent"] += 1
            elif len(n) == 1 and "a" <= n <= "z":
                note_markers["single_lowercase_ascii_letter"] += 1
            elif len(n) == 1 and "A" <= n <= "Z":
                note_markers["single_uppercase_ascii_letter"] += 1
            elif n.isascii() and n.isdecimal():
                note_markers["ascii_decimal"] += 1
            elif len(n) == 1 and not n.isalnum():
                note_markers["single_symbol"] += 1
            else:
                note_markers["other_unreviewed_literal"] += 1
            typ = node.get("type")
            note_types[typ if typ in SAFE_TYPES else "unknown_or_unspecified"] += 1
    if not elements["osisText"] or not elements["verse"]:
        raise PublisherOSISObservationError("No usable official OSIS Scripture structure")
    return {
        "schema_version":1,
        "status":"official_publisher_osis_observed_unreviewed",
        "publisher_osis_xml_sha256":sha256(xml).hexdigest(),
        "publisher_osis_xml_bytes":len(xml),
        "source_element_counts":dict(sorted(elements.items())),
        "source_attribute_name_counts":dict(sorted(attributes.items())),
        "source_note_caller_shape_counts":dict(sorted(note_markers.items())),
        "source_note_type_allowlisted_counts":dict(sorted(note_types.items())),
        "strict_osis_xml_parsed":True,
        "edition_source_comparison_verified":False,
        "source_note_labels_equal_to_usfx_verified":False,
        "source_main_text_or_versification_equal_to_ebible_verified":False,
        "source_note_text_or_reference_targets_equal_verified":False,
        "source_rights_and_publication_approved":False,
        "no_bible_scripture_notes_or_untrusted_attributes_in_report":True,
    }


def observe(resource_id, *, opener=None):
    cfg = _source_config(resource_id)
    xml = _download(cfg["official_source_url"], opener=opener)
    report = inspect_official_osis(xml)
    report["resource_id"] = cfg["resource_id"]
    report["official_source_url"] = cfg["official_source_url"]
    report["declared_edition"] = cfg["edition"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        parser.error("Report file must be new in an existing directory")
    try:
        receipt=observe(args.resource_id)
    except PublisherOSISObservationError as exc:
        parser.error(str(exc))
    args.report.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Official OSIS observed (UNREVIEWED):",receipt["resource_id"])
    print("SHA-256:",receipt["publisher_osis_xml_sha256"])
    print("Bytes:",receipt["publisher_osis_xml_bytes"])
    print("Note caller categories:",json.dumps(receipt["source_note_caller_shape_counts"],sort_keys=True))
    print("Never auto-accept edition, editor rights, text or notes.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
