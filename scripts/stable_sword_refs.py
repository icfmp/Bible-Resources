#!/usr/bin/env python3
"""Fail-closed reference-index screening for stock, released SWORD engines.

Inputs are text-free verse references collected *independently* from the
publisher source and the compiled module's actual resolved reader keys.
Never infer the latter from osis2mod exit status or from a source-key list.
This is not a Bible-text, notes, formatting, or visual fidelity assertion.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.([1-9][0-9]*)$")
SYSTEM = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,31}$")
STABLE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA = re.compile(r"^[a-f0-9]{64}$")


def parse_keys(text: str) -> set[tuple[str, int, int]]:
    result = set()
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty verse-key inventory")
    for number, line in enumerate(lines, 1):
        match = KEY.fullmatch(line)
        if match is None:
            raise ValueError(f"Invalid verse key on line {number}")
        key = (match.group(1), int(match.group(2)), int(match.group(3)))
        if key in result:
            raise ValueError(f"Duplicate verse key on line {number}")
        result.add(key)
    return result


def parse_registry(text: str, system: str) -> dict[tuple[str, int], int]:
    if not SYSTEM.fullmatch(system):
        raise ValueError("Invalid SWORD versification name")
    registry = {}
    for number, line in enumerate(text.splitlines(), 1):
        cells = line.split("\t")
        if len(cells) != 4:
            raise ValueError(f"Malformed installed SWORD registry line {number}")
        name, book, chapter, maximum = cells
        if not SYSTEM.fullmatch(name) or not KEY.fullmatch(f"{book}.{chapter}.{maximum}"):
            raise ValueError(f"Invalid registered SWORD chapter on line {number}")
        if name != system:
            continue
        key = (book, int(chapter))
        if key in registry:
            raise ValueError(f"Duplicate registered SWORD chapter on line {number}")
        registry[key] = int(maximum)
    if not registry:
        raise ValueError(f"Versification {system} is absent from installed SWORD")
    return registry


def module_payload_digest(module_directory: Path) -> str:
    """Bind the report to the entire installed payload, including its .conf."""
    root = module_directory / "payload"
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Missing or linked SWORD payload")
    entries = sorted(root.rglob("*"))
    if not entries or any(p.is_symlink() for p in entries):
        raise ValueError("Empty or linked SWORD payload")
    files = [p for p in entries if p.is_file()]
    if not files:
        raise ValueError("No SWORD module files")
    digest = hashlib.sha256()
    for p in files:
        rel = p.relative_to(root).as_posix().encode("utf-8")
        raw = p.read_bytes()
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def inspect_references(source: set[tuple[str, int, int]],
                       resolved_reader: set[tuple[str, int, int]],
                       registry: dict[tuple[str, int], int],
                       approved_merges: list[tuple[str,str]] | None = None) -> dict:
    """Screen exact source keys or *explicitly reviewed* adjacent merges.

    A source-only, out-of-v11n verse may be appended only to an adjacent
    authored and readable prior verse, and only when separately approved.
    Original Scripture text is audited independently; this index proof
    alone NEVER grants publication.
    """
    outside = sorted(ref for ref in source
                     if ref[2] > registry.get((ref[0], ref[1]), 0))
    missing = sorted(source - resolved_reader)
    unexpected = sorted(resolved_reader - source)
    merge_map = {}
    approvals = approved_merges or []
    if not isinstance(approvals,list):
        raise ValueError("Reviewed SWORD merge manifest must be a list")
    for src,dst in approvals:
        src_parsed = parse_keys(src)
        dst_parsed = parse_keys(dst)
        if len(src_parsed)!=1 or len(dst_parsed)!=1:
            raise ValueError("Malformed reviewed SWORD merge reference")
        sref = next(iter(src_parsed))
        dref = next(iter(dst_parsed))
        if (sref in merge_map or sref not in source or dref not in source
            or dref not in resolved_reader or sref[:2]!=dref[:2]
            or sref[2]!=dref[2]+1
            or registry.get(sref[:2],0)!=dref[2]
            or any(k[0]==sref[0] and k[1]==sref[1] and k[2]>sref[2]
                   for k in source)):
            raise ValueError("Unreviewed, non-final or nonadjacent verse merge")
        merge_map[sref]=dref
    tolerated=set(merge_map)
    valid_merges=(set(missing)==tolerated and set(outside)==tolerated
                  and not unexpected)
    exact=not (outside or missing or unexpected)
    status = ("stable_reference_index_verified" if exact and not merge_map
              else "stable_reference_index_verified_with_reviewed_merges"
              if valid_merges and bool(merge_map) else "blocked")
    occupied = Counter((book, chapter) for book, chapter, verse in source
                       if verse <= registry.get((book, chapter), 0))
    unused_slots = sum(maximum - occupied.get(key, 0)
                       for key, maximum in registry.items())
    return {
        "status": status,
        "reviewed_merge_count":len(merge_map),
        "reviewed_merges":[{"original_osis_ref":"%s.%d.%d" % k,
                            "stock_reader_osis_ref":"%s.%d.%d" % v}
                           for k,v in sorted(merge_map.items())],
        "source_reference_count": len(source),
        "resolved_reader_reference_count": len(resolved_reader),
        "outside_registered_versification_count": len(outside),
        "source_references_unreachable_count": len(missing),
        "unexpected_populated_reader_references_count": len(unexpected),
        "unoccupied_registered_slots_count": unused_slots,
        "first_outside_refs": ["%s.%d.%d" % x for x in outside[:20]],
        "first_unreachable_refs": ["%s.%d.%d" % x for x in missing[:20]],
        "first_unexpected_reader_refs": ["%s.%d.%d" % x for x in unexpected[:20]],
        "exact_reference_key_parity": exact,
        "reviewed_index_compromise_verified":valid_merges and bool(merge_map),
        "text_notes_markup_and_visuals_verified": False,
    }


def proof_errors(module_directory: Path, versification: str,
                 source_osis_sha256: str) -> list[str]:
    """Publication assertion gate; independent CI must produce the report."""
    path = module_directory / "SWORD_COMPATIBILITY.json"
    try:
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError("unsafe/oversize compatibility report")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"{path}: [SWORD_COMPATIBILITY_MISSING] {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: [SWORD_COMPATIBILITY_INVALID] Expected object"]
    errors = []
    exact_mode = (
        data.get("status") == "stable_reference_index_verified"
        and data.get("exact_reference_key_parity") is True
        and data.get("outside_registered_versification_count") == 0
        and data.get("source_references_unreachable_count") == 0
        and data.get("unexpected_populated_reader_references_count") == 0
        and type(data.get("source_reference_count")) is int
        and data["source_reference_count"] > 0
        and data.get("source_reference_count") == data.get("resolved_reader_reference_count")
        and data.get("reviewed_merge_count",0) == 0
    )
    merged_mode = data.get("status") == "stable_reference_index_verified_with_reviewed_merges"
    if merged_mode:
        approved = data.get("reviewed_merges")
        count = data.get("reviewed_merge_count")
        good_count = (
            isinstance(approved,list) and 0 < len(approved) <= 200
            and type(count) is int and count == len(approved)
            and type(data.get("source_reference_count")) is int
            and data["source_reference_count"] > count
            and data.get("resolved_reader_reference_count")
                == data["source_reference_count"] - count
            and data.get("source_references_unreachable_count") == count
            and data.get("outside_registered_versification_count") == count
            and data.get("unexpected_populated_reader_references_count") == 0
            and data.get("reviewed_index_compromise_verified") is True
            and data.get("exact_reference_key_parity") is False
        )
        if not good_count:
            errors.append(f"{path}: [SWORD_MERGE_INDEX_UNVERIFIED] Indexed merge count or reader keys mismatch")
        if (data.get("full_source_chapter_character_streams_verified") is not True
                or type(data.get("full_readback_chapter_count")) is not int
                or data.get("full_readback_chapter_count") < 1
                or not isinstance(data.get("full_readback_evidence_sha256"),str)
                or not SHA.fullmatch(data["full_readback_evidence_sha256"])):
            errors.append(f"{path}: [SWORD_MERGED_BODY_UNVERIFIED] Full independent body readback required")
        policy_path = module_directory / "SOURCE_REFERENCE_MERGES.json"
        try:
            if (policy_path.is_symlink() or not policy_path.is_file()
                    or policy_path.stat().st_size > 100_000):
                raise ValueError("unsafe or missing source-bound approval policy")
            raw = policy_path.read_bytes()
            policy = json.loads(raw)
            hashval = hashlib.sha256(raw).hexdigest()
            if (not isinstance(policy,dict)
                or policy.get("schema_version") != 1
                or policy.get("versification") != versification
                or not isinstance(policy.get("source_document_sha256"),str)
                or not SHA.fullmatch(policy["source_document_sha256"])
                or policy.get("authorization",{}).get("who")
                    != "Bible Resources project owner"
                or policy.get("policy")
                    != "approved_explicit_temporary_adjacent_verse_index_merge"
                or not isinstance(policy.get("allowed_merges"),list)):
                raise ValueError("invalid approved-merge policy metadata")
            expected = sorted(
                (e["osis_source_key"],e["osis_reader_key"])
                for e in policy["allowed_merges"])
            observed = sorted(
                (e["original_osis_ref"],e["stock_reader_osis_ref"])
                for e in approved) if isinstance(approved,list) else []
            if (expected!=observed or len(expected)!=count
                or data.get("reviewed_merge_policy_sha256")!=hashval
                or data.get("original_publisher_document_sha256")
                    !=policy["source_document_sha256"]):
                raise ValueError("reviewed merger differs from recorded source decision")
        except (OSError,ValueError,UnicodeError,KeyError,TypeError,AttributeError) as exc:
            errors.append(f"{path}: [SWORD_MERGE_REVIEW_STALE] {exc}")
    if not exact_mode and not merged_mode:
        errors.append(f"{path}: [SWORD_INDEX_NOT_VERIFIED] Exact keys or source-reviewed merged keys required")
    if (data.get("versification") != versification
            or data.get("reader_engine") != "libsword"
            or not isinstance(data.get("reader_version"), str)
            or not STABLE_VERSION.fullmatch(data["reader_version"])
            or data.get("engine_release") != "stable"
            or data.get("registry_source") != "installed_sword_versification_mgr"):
        errors.append(f"{path}: [SWORD_UNSUPPORTED_RUNTIME] Released standard SWORD registry proof required")
    if (not isinstance(source_osis_sha256, str)
            or not SHA.fullmatch(source_osis_sha256)
            or data.get("source_osis_sha256") != source_osis_sha256):
        errors.append(f"{path}: [SWORD_SOURCE_PROOF_STALE] Source digest does not match validated OSIS")
    try:
        payload_sha = module_payload_digest(module_directory)
    except (OSError, ValueError) as exc:
        errors.append(f"{path}: [SWORD_PAYLOAD_PROOF_INVALID] {exc}")
    else:
        if data.get("module_payload_sha256") != payload_sha:
            errors.append(f"{path}: [SWORD_PAYLOAD_PROOF_STALE] Compiled payload has changed")
    if (not isinstance(data.get("reviewed_by"), str)
            or len(data["reviewed_by"].strip()) < 2
            or data["reviewed_by"].strip().upper() == "PENDING"):
        errors.append(f"{path}: [SWORD_INDEX_REVIEW_MISSING] Reviewer sign-off required")
    return errors


def load_approved_merge_policy(
        path: Path, *, publisher_digest: str, versification: str
) -> tuple[list[tuple[str,str]],str]:
    """Source-bound owner review; source/reader address changes only."""
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size>100_000):
        raise ValueError("Unsafe or missing approved SWORD merge policy")
    raw=path.read_bytes()
    try:
        p=json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Malformed reviewed SWORD merge policy") from exc
    if (not isinstance(p,dict) or p.get("schema_version")!=1
            or p.get("source_document_sha256")!=publisher_digest
            or not isinstance(publisher_digest,str)
            or not SHA.fullmatch(publisher_digest)
            or p.get("versification")!=versification
            or p.get("policy")
               !="approved_explicit_temporary_adjacent_verse_index_merge"
            or not isinstance(p.get("authorization"),dict)
            or p["authorization"].get("who")
               !="Bible Resources project owner"):
        raise ValueError("Publisher source, SWORD registry or authorization differs")
    entries=p.get("allowed_merges")
    if not isinstance(entries,list) or not entries or len(entries)>200:
        raise ValueError("No approved source-bound verse mergers")
    refs=[]
    for item in entries:
        if (not isinstance(item,dict)
            or item.get("source_content_preserved") is not True
            or item.get("independent_reference_access_lost") is not True
            or item.get("reversible") is not True
            or item.get("status")!="temporarily_authorized_versification_compromise"):
            raise ValueError("Invalid source-bound merged verse approval")
        refs.append((item["osis_source_key"],item["osis_reader_key"]))
    return refs,hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-keys", type=Path, required=True)
    parser.add_argument("--resolved-reader-keys", type=Path, required=True)
    parser.add_argument("--registry-tsv", type=Path, required=True)
    parser.add_argument("--versification", required=True)
    parser.add_argument("--reader-version", required=True)
    parser.add_argument("--source-osis-sha256", required=True)
    parser.add_argument("--module-directory", type=Path, required=True)
    parser.add_argument("--reviewed-merge-policy", type=Path,
                        help="Source-bound owner approval; not a publication waiver")
    parser.add_argument("--publisher-document-sha256",
                        help="Independent original publisher USFX digest")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not STABLE_VERSION.fullmatch(args.reader_version):
        parser.error("A released numeric libsword version is required, not HEAD/dev")
    if not SHA.fullmatch(args.source_osis_sha256):
        parser.error("Validated original OSIS SHA-256 is required")
    try:
        src = parse_keys(args.source_keys.read_text(encoding="utf-8"))
        reader = parse_keys(args.resolved_reader_keys.read_text(encoding="utf-8"))
        registry = parse_registry(args.registry_tsv.read_text(encoding="utf-8"),
                                  args.versification)
        payload_hash = module_payload_digest(args.module_directory)
        merge_refs=[]
        review_digest=None
        if args.reviewed_merge_policy is not None:
            if not args.publisher_document_sha256:
                raise ValueError("Publisher source digest required for a merged index")
            expected=(args.module_directory / "SOURCE_REFERENCE_MERGES.json").resolve()
            if args.reviewed_merge_policy.resolve()!=expected:
                raise ValueError("Approved merger must be attached to this module")
            merge_refs,review_digest=load_approved_merge_policy(
                args.reviewed_merge_policy,
                publisher_digest=args.publisher_document_sha256,
                versification=args.versification)
        elif args.publisher_document_sha256 is not None:
            raise ValueError("Publisher digest alone is not a reviewed merger")
    except (ValueError, OSError, UnicodeError,KeyError,TypeError) as exc:
        parser.error(str(exc))
    report = inspect_references(src, reader, registry, merge_refs)
    report.update({
        "versification": args.versification,
        "reader_engine": "libsword",
        "reader_version": args.reader_version,
        "engine_release": "stable",
        "registry_source": "installed_sword_versification_mgr",
        "source_osis_sha256": args.source_osis_sha256,
        "module_payload_sha256": payload_hash,
        "reviewed_by": "PENDING",
        "reviewed_merge_policy_sha256": review_digest,
        "original_publisher_document_sha256": args.publisher_document_sha256,
        # Independent source/body proof must be attached and audited later.
        "full_source_chapter_character_streams_verified": False,
        "full_readback_chapter_count": 0,
        "full_readback_evidence_sha256": None,
    })
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("SWORD stable reference index:", report["status"])
    return 0 if report["status"] in {
        "stable_reference_index_verified",
        "stable_reference_index_verified_with_reviewed_merges",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
