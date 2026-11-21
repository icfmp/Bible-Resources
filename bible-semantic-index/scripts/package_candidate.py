#!/usr/bin/env python3
"""Package a checked, keyterm-free BSI v0.1 candidate reproducibly.

The result is an internal release candidate. Publishing is a distinct rights gate.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

VERSION = "0.1.0"
PREFIX = f"BSI-{VERSION}/"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"

README = """# Bible Semantic Index (BSI) 0.1.0

Original-language word-level biblical entity index, anchored to pinned
Macula WLC and SBLGNT word IDs. This edition excludes the entire ACAI
Key Terms category, descriptions, biographies, multilingual content,
speech content and speculative genealogies.

Data files:
- index.json: source-annotation candidates and original-word pointers;
  consult review_status and never infer that a candidate is verified.
- labels-en.json: minimal English labels copied from source ACAI, explicitly
  not reviewed as unique individual identities.
- source.lock.json: immutable source revision and snapshot digest.
- manifest.json: file hashes and distribution coverage.

The source's indirect participant/pronoun links are retained in the index
for provenance, but an application should use explicit-only resolution for
reader-facing results. A name such as 'Mary' may refer to multiple people.

The data is a modified adaptation of ACAI, CC BY-SA 4.0; it is not endorsed
by the original providers. Details in ATTRIBUTION.md.
"""

ATTRIBUTION = """# Attribution, license and changes

Bible Semantic Index (BSI) is an adapted, reduced entity data resource.

ACAI Biblical Entity Data:
- Source: https://github.com/BibleAquifer/ACAI
- Frozen fork: https://github.com/icfmp/ACAI
- Copyright notice in source README: (c) 2025 Mission Mutual
- Source LICENSE.md credits BiblioNexus (c) 2024
- License: Creative Commons Attribution-ShareAlike 4.0 International
  https://creativecommons.org/licenses/by-sa/4.0/

Modifications: deterministic selection of a subset of source attributes,
independent reviewed entity-link corrections and qualified source candidates,
exclusion of all Key Terms and inverse references, removal of descriptions,
multilingual prose, biographies and speeches, and separate minimal English
source labels. The original ACAI snapshot is preserved unchanged.

Original-word identifier editions, verified for existence:
- MACULA Hebrew Linguistic Datasets:
  https://github.com/Clear-Bible/macula-hebrew (CC BY 4.0)
- MACULA Greek Linguistic Datasets:
  https://github.com/Clear-Bible/macula-greek (CC BY 4.0)
The original-language text itself is not redistributed in this archive.

The derivative BSI *data* is distributed under CC BY-SA 4.0. This does not
relicense any independently copyrighted Bible text, lexicon, or software.
No original authors or organizations endorse this derivative.
"""

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def candidate_payload(index: dict, labels: dict, lock: dict) -> dict[str, bytes]:
    if index.get("schema_version") != 1 or labels.get("schema_version") != 1:
        raise ValueError("Unsupported BSI index/label schema")
    profile = index.get("distribution_profile", {})
    if profile.get("name") != "bsi-v0.1-without-keyterms" or profile.get("excluded_kinds") != ["keyterm"]:
        raise ValueError("Only the checked keyterm-free profile may be packaged")
    if labels.get("distribution_profile") != profile["name"]:
        raise ValueError("Label distribution profile mismatch")
    if index["provenance"]["source_snapshot_sha256"] != lock["source_snapshot_sha256"]:
        raise ValueError("Pinned source snapshot does not match the index")
    if labels.get("source_snapshot_sha256") != lock["source_snapshot_sha256"]:
        raise ValueError("Label source fingerprint mismatch")
    ids = {entity["id"] for entity in index["entities"]}
    if any(entity["kind"] == "keyterm" or entity["id"].startswith("keyterm:")
           for entity in index["entities"]):
        raise ValueError("Restricted Key Terms remain in entities")
    if any(entity_id not in ids for entity_id in labels["labels"]):
        raise ValueError("Label for absent distribution entity")
    if set(labels["labels"]) & set(labels.get("missing_ids", [])):
        raise ValueError("Label also listed as missing")
    if set(labels["labels"]) | set(labels.get("missing_ids", [])) != ids:
        raise ValueError("Incomplete label inventory")
    if any(hit["entity_id"] not in ids
           for hits in index["by_word"].values() for hit in hits):
        raise ValueError("Inverse index includes a missing entity")
    # Every trace of excluded Key Terms must be absent from distributed JSON.
    for field in ("entities", "by_word", "quarantined", "unattested_source_words",
                  "unattested_source_verses", "qualified_source_references"):
        def forbidden(value: object) -> bool:
            if isinstance(value, dict):
                return any(forbidden(k) or forbidden(v) for k, v in value.items())
            if isinstance(value, list):
                return any(forbidden(v) for v in value)
            return isinstance(value, str) and value.startswith("keyterm:")
        if forbidden(index.get(field)):
            raise ValueError(f"Key Term identifier leaked in {field}")
    return {
        "index.json": json_bytes(index),
        "labels-en.json": json_bytes(labels),
        "source.lock.json": json_bytes(lock),
        "README.md": README.encode(),
        "ATTRIBUTION.md": ATTRIBUTION.encode(),
    }


def build_archive(index: dict, labels: dict, lock: dict) -> tuple[bytes, dict]:
    files = candidate_payload(index, labels, lock)
    manifest = {
        "name": "Bible Semantic Index",
        "version": VERSION,
        "status": "versioned_distribution",
        "license": "CC BY-SA 4.0",
        "license_url": LICENSE_URL,
        "source_snapshot_sha256": lock["source_snapshot_sha256"],
        "source_revision": lock["source_commit"],
        "distribution_profile": "bsi-v0.1-without-keyterms",
        "record_count": len(index["entities"]),
        "label_count": len(labels["labels"]),
        "missing_label_count": len(labels["missing_ids"]),
        "excluded_categories": ["keyterm"],
        "files_sha256": {name: sha(data) for name, data in sorted(files.items())},
    }
    files["manifest.json"] = json_bytes(manifest)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 << 16)
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    return out.getvalue(), manifest


def verify_archive(raw: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if not names or any(not p.startswith(PREFIX) or ".." in p.split("/")
                            for p in names):
            raise ValueError("Unexpected archive members")
        manifest = json.loads(archive.read(PREFIX + "manifest.json"))
        assert set(names) == {PREFIX + p for p in manifest["files_sha256"]} | {
            PREFIX + "manifest.json"}
        for name, digest in manifest["files_sha256"].items():
            if sha(archive.read(PREFIX + name)) != digest:
                raise ValueError("Archive member checksum mismatch: " + name)
        index = json.loads(archive.read(PREFIX + "index.json"))
        labels = json.loads(archive.read(PREFIX + "labels-en.json"))
        lock = json.loads(archive.read(PREFIX + "source.lock.json"))
        candidate_payload(index, labels, lock)
        if len(index["entities"]) != manifest["record_count"]:
            raise ValueError("Record count mismatch")
        return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(args.output.resolve() == p.resolve()
           for p in (args.index, args.labels, args.lock)):
        parser.error("Output must not overwrite inputs")
    index = json.loads(args.index.read_text(encoding="utf-8"))
    labels = json.loads(args.labels.read_text(encoding="utf-8"))
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    raw, manifest = build_archive(index, labels, lock)
    assert verify_archive(raw) == manifest
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"archive_sha256": sha(raw), **manifest}, sort_keys=True))


if __name__ == "__main__":
    main()
