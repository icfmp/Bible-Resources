#!/usr/bin/env python3
"""Read-only, edition-neutral source OSIS -> actual stock SWORD index audit.

Only *index addressability* can pass. Same-edition publisher provenance,
source->OSIS conversion, compiled text/notes/markup, rights and editorial
approval are deliberately NOT inferred. No verse is inserted or renumbered.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from source_osis_inventory import _read_source, source_inventory
from stable_sword_refs import (
    inspect_references, module_payload_digest, parse_keys, parse_registry,
)
from sword_native_inventory import collect_native_inventory, _write_evidence


class SourceNativeIndexError(ValueError):
    """An independent index proof is missing, stale, or contradictory."""


def audit_source_native_index(
    source_path: Path, module_dir: Path, module_id: str, inspector: Path
) -> dict:
    """Use two independent producers, then compare the exact numbered keys.

    The source is *already OSIS*. A publisher's earlier USFM/USFX conversion
    has to be separately verified, never inferred from a matching key list.
    """
    source_bytes = _read_source(source_path)
    source_keys, source_report = source_inventory(source_bytes)
    native_keys, registry_tsv, native_report = collect_native_inventory(
        inspector, module_dir, module_id
    )
    if native_report.get("module_payload_sha256") != module_payload_digest(module_dir):
        raise SourceNativeIndexError("Native reader receipt does not bind to current SWORD payload")
    if native_report.get("native_reader_keys_sha256") != sha256(native_keys.encode("utf-8")).hexdigest():
        raise SourceNativeIndexError("Native receipt and independent reader key stream disagree")
    if native_report.get("native_registry_sha256") != sha256(registry_tsv.encode("utf-8")).hexdigest():
        raise SourceNativeIndexError("Native receipt and installed registry stream disagree")
    if native_report.get("native_occupied_numbered_verse_count") != len(parse_keys(native_keys)):
        raise SourceNativeIndexError("Native occupied key count is not reproducible")
    if source_report.get("source_verse_count") != len(parse_keys(source_keys)):
        raise SourceNativeIndexError("Authored source key count is not reproducible")
    if not isinstance(native_report.get("reader_version"), str) or not native_report["reader_version"]:
        raise SourceNativeIndexError("Native reader engine version is not attested")
    if native_report.get("module_driver") not in ("RawText", "zText"):
        raise SourceNativeIndexError("Native reader driver is not supported")
    system = native_report.get("native_versification")
    if not isinstance(system, str):
        raise SourceNativeIndexError("Native reader versification is not attested")

    comparison = inspect_references(
        parse_keys(source_keys),
        parse_keys(native_keys),
        parse_registry(registry_tsv, system),
    )
    if sha256(_read_source(source_path)).hexdigest() != source_report["source_osis_sha256"]:
        raise SourceNativeIndexError("Source OSIS changed during independent reader audit")
    if module_payload_digest(module_dir) != native_report["module_payload_sha256"]:
        raise SourceNativeIndexError("Native compiled module changed during index comparison")

    exact = comparison["status"] == "stable_reference_index_verified"
    return {
        "schema_version": 1,
        "status": ("source_osis_native_verse_keys_exact_index_only"
                   if exact else "blocked_source_osis_native_verse_key_difference"),
        "source_kind": "already_existing_osis_not_original_usfm_usfx_proof",
        "source_osis_sha256": source_report["source_osis_sha256"],
        "source_verse_keys_sha256": source_report["source_keys_sha256"],
        "source_numbered_verse_count": source_report["source_verse_count"],
        "source_book_count": source_report["source_book_count"],
        "module_id": module_id,
        "module_payload_sha256": native_report["module_payload_sha256"],
        "module_driver": native_report["module_driver"],
        "native_versification": system,
        "reader_engine": "released_stock_libsword",
        "reader_version": native_report["reader_version"],
        "reader_inspector_sha256": native_report["native_inspector_sha256"],
        "native_numbered_verse_keys_sha256": native_report["native_reader_keys_sha256"],
        "native_registry_sha256": native_report["native_registry_sha256"],
        "native_numbered_verse_count": native_report["native_occupied_numbered_verse_count"],
        "native_intro_references": native_report["native_occupied_intro_references"],
        "native_unaddressable_top_count": native_report["native_nonaddressable_populated_top_count"],
        "comparison": comparison,
        "stages": {
            "SOURCE_AUDIT": "osis_numbered_keys_only_original_publisher_identity_unverified",
            "COMPILED_FIDELITY": "native_numbered_keys_only_all_content_unverified",
            "READER_ACCEPTANCE": "not_tested_standalone_and_parallel",
            "RELEASE_RECEIPT": "not_authorized",
        },
        "source_usfm_usfx_to_osis_conversion_verified": False,
        "source_to_compiled_text_punctuation_notes_strong_layout_verified": False,
        "source_intro_content_and_verse_zero_verified": False,
        "same_edition_revision_verified": False,
        "publication_rights_approved": False,
        "human_editorial_approval": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-osis", type=Path, required=True)
    parser.add_argument("--module-directory", type=Path, required=True)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--native-index-binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_source_native_index(
            args.source_osis, args.module_directory, args.module_id,
            args.native_index_binary,
        )
        _write_evidence(
            [(args.report, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))],
            args.module_directory,
        )
    except (OSError, ValueError, UnicodeError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print("Independent source->stock SWORD reference index:", report["status"])
    print("Complete source text, notes, structural and editorial parity NOT verified.")
    return 0 if report["comparison"]["exact_reference_key_parity"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
