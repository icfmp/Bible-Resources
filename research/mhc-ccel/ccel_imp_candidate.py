#!/usr/bin/env python3
"""Private, fail-closed CCEL ThML -> SWORD IMP feasibility probe.

This is NOT an approved conversion: only verse/range-linked <scripCom> body
siblings are imported. Chapter/book introductions and all other source text
are deliberately marked unhandled. Input and generated IMP must never be
committed, uploaded as a CI artifact, or published without rights approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree

OSIS_REF = re.compile(r"^Bible:([1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*)(?:\.([1-9][0-9]*)(?:-([1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*))?)?$")
SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_XML = 32 * 1024 * 1024


def _tag(node) -> str:
    return node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else "#non-element"


def _original_tree(data: bytes, expected_sha: str):
    if (not SHA.fullmatch(expected_sha) or not 1000 <= len(data) <= MAX_XML
            or sha256(data).hexdigest() != expected_sha):
        raise ValueError("Original XML digest/size not independently verified")
    parser = etree.XMLParser(resolve_entities=False, no_network=True,
                             load_dtd=False, recover=False,
                             remove_blank_text=False, remove_comments=False,
                             strip_cdata=False)
    try:
        root = etree.fromstring(data, parser)
    except (etree.XMLSyntaxError, ValueError):
        raise ValueError("Source XML cannot be safely parsed") from None
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise ValueError("Unresolved source entity")
    return root


def extract_volume(data: bytes, expected_sha: str):
    """Yield verbatim-body IMP records plus explicitly unhandled source scopes.

    Never infer chapter introductions from a marker followed by another marker.
    An original source div is serialized into one XML line to keep the SWORD
    IMP separator unambiguous. XML character references preserve source LF/CR.
    """
    root = _original_tree(data, expected_sha)
    bodies = []
    stats = Counter()
    seen_start = set()
    digest = sha256()
    for marker in root.iter():
        if _tag(marker) != "scripCom":
            continue
        stats["markers"] += 1
        original_ref = marker.get("osisRef", "")
        match = OSIS_REF.fullmatch(original_ref)
        if not match:
            raise ValueError("Unclassified original scripture marker (cannot invent mapping)")
        chapter, verse, ending = match.groups()
        following = marker.getnext()
        if verse is None:
            if _tag(following) != "scripCom":
                raise ValueError("Unexpected chapter marker ownership")
            stats["chapter_markers_unhandled"] += 1
            continue
        if (_tag(following) != "div" or (marker.tail and marker.tail.strip())):
            raise ValueError("Original verse/range marker lacks exact adjacent body div")
        if ending is not None and ending.split(".")[0] != chapter.split(".")[0]:
            raise ValueError("Cross-book source range requires separate review")
        start = f"{chapter}.{verse}"
        if start in seen_start:
            raise ValueError("Collision at original source start address")
        seen_start.add(start)
        # Retain original source body markup and visible text, including notes,
        # inline scripture references and ordered paragraphs. No normalizer.
        original_xml = etree.tostring(following, encoding="unicode", with_tail=False)
        one_line = original_xml.replace("\r", "&#13;").replace("\n", "&#10;")
        try:
            parsed = etree.fromstring(one_line.encode("utf-8"))
        except etree.XMLSyntaxError:
            raise ValueError("IMP body failed XML round-trip validation") from None
        if ("".join(parsed.itertext()) != "".join(following.itertext())
                or etree.tostring(parsed, method="c14n") != etree.tostring(following, method="c14n")):
            raise ValueError("Serialized original ThML subtree differs after XML round-trip")
        key = start + ("-" + ending if ending is not None else "")
        # This first candidate excludes parent/chapter content, even though it
        # can contain authentic exposition. It MUST NOT be accepted as complete.
        raw_bytes = original_xml.encode("utf-8")
        digest.update(len(key).to_bytes(4, "big") + key.encode("utf-8")
                      + len(raw_bytes).to_bytes(8, "big") + raw_bytes)
        bodies.append((key, one_line))
        stats["verse_or_range_bodies"] += 1
        if not "".join(following.itertext()).strip():
            stats["empty_original_bodies_preserved"] += 1
    return bodies, dict(stats), digest.hexdigest()



def inspect_volume_start_collisions(data: bytes, expected_sha: str) -> dict:
    """Closed census of genuine CCEL duplicate verse-start ownership.

    Count all authentic annotated source bodies before choosing any SWORD
    encoding. Do not expose original refs or texts or automatically merge.
    """
    root = _original_tree(data, expected_sha)
    seen = {}
    duplicate_starts = set()
    same_ref_extra = 0
    changed_ref_extra = 0
    same_body_extra = 0
    changed_body_extra = 0
    total_sections = 0
    for marker in root.iter():
        if _tag(marker) != "scripCom":
            continue
        match = OSIS_REF.fullmatch(marker.get("osisRef", ""))
        if match is None:
            raise ValueError("Original reference unclassified in collision census")
        chapter, verse, ending = match.groups()
        if verse is None:
            continue
        following = marker.getnext()
        if _tag(following) != "div" or (marker.tail and marker.tail.strip()):
            raise ValueError("Original body adjacency unverified in collision census")
        total_sections += 1
        start = chapter + "." + verse
        original_ref = marker.get("osisRef", "")
        # Only hashes of original text are compared in memory, never logged.
        body_hash = sha256(etree.tostring(following, encoding="utf-8",
                                         with_tail=False)).hexdigest()
        previous = seen.setdefault(start, [])
        if previous:
            duplicate_starts.add(start)
            same_ref_extra += int(any(ref == original_ref for ref, _ in previous))
            changed_ref_extra += int(not any(ref == original_ref for ref, _ in previous))
            same_body_extra += int(any(digest == body_hash for _, digest in previous))
            changed_body_extra += int(not any(digest == body_hash for _, digest in previous))
        previous.append((original_ref, body_hash))
    extra = sum(len(group) - 1 for group in seen.values())
    if extra != same_ref_extra + changed_ref_extra or extra != same_body_extra + changed_body_extra:
        raise ValueError("Collision census internal contradiction")
    return {
        "original_verse_or_range_sections": total_sections,
        "distinct_original_start_addresses": len(seen),
        "duplicated_original_start_groups": len(duplicate_starts),
        "additional_sections_sharing_original_start": extra,
        "additional_sections_same_full_ref": same_ref_extra,
        "additional_sections_different_full_ref": changed_ref_extra,
        "additional_sections_identical_markup_body_to_prior": same_body_extra,
        "additional_sections_different_markup_body_to_prior": changed_body_extra,
        "largest_same_start_group": max(map(len, seen.values()), default=0),
        "safe_to_write_one_section_per_sword_key": extra == 0,
        "original_sections_reordered_or_merged": False,
        "source_text_or_references_in_report": False,
    }


def build_original_collision_census(manifest: dict, source_directory: Path) -> dict:
    volumes = manifest.get("commentary_source", {}).get("xml_witness_volumes", [])
    if len(volumes) != 6 or sorted(v["number"] for v in volumes) != list(range(1, 7)):
        raise ValueError("Exactly six reviewed volume pins required")
    receipt = []
    for volume in sorted(volumes, key=lambda v: v["number"]):
        path = source_directory / f'mhc{volume["number"]}.xml'
        if path.is_symlink() or not path.is_file():
            raise ValueError("Original source file missing/unsafe")
        observed = inspect_volume_start_collisions(path.read_bytes(), volume["sha256"])
        receipt.append({"volume": volume["number"], "original_xml_sha256": volume["sha256"],
                        **observed})
    return {
        "status": "ORIGINAL_START_COLLISION_CENSUS_ONLY",
        "volumes": receipt,
        "all_authored_sections_preserved_in_census": True,
        "all_source_text_accounted_for": False,
        "any_unresolved_duplicate_starts": any(
            x["additional_sections_sharing_original_start"] for x in receipt),
        "source_text_or_references_exported": False,
        "redistribution_authorized": False,
        "published": False,
    }


def build_private_candidate(manifest: dict, source_directory: Path, output: Path):
    volumes = manifest.get("commentary_source", {}).get("xml_witness_volumes", [])
    if (len(volumes) != 6 or sorted(v["number"] for v in volumes) != list(range(1, 7))):
        raise ValueError("Exactly six reviewed volume pins required")
    receipts = []
    all_entries = []
    keys = set()
    for volume in sorted(volumes, key=lambda v: v["number"]):
        number = volume["number"]
        path = source_directory / f"mhc{number}.xml"
        if path.is_symlink() or not path.is_file():
            raise ValueError("Original source file missing/unsafe")
        entries, stats, digest = extract_volume(path.read_bytes(), volume["sha256"])
        for key, value in entries:
            if key in keys:
                raise ValueError("Identical original source ranges overlap volumes")
            keys.add(key)
            all_entries.append((key, value))
        receipts.append({"volume": number, "original_xml_sha256": volume["sha256"],
                         "ordered_source_bodies_sha256": digest, **stats})
    if not all_entries or any(row["chapter_markers_unhandled"] == 0 for row in receipts):
        raise ValueError("Source structural marker census unexpected")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for key, body in all_entries:
            stream.write("$$$" + key + "\n" + body + "\n")
    return {"status": "INCOMPLETE_PRIVATE_VERSE_BODY_FEASIBILITY_ONLY",
            "volumes": receipts,
            "source_body_entry_count": len(all_entries),
            "unhandled_chapter_markers": sum(r["chapter_markers_unhandled"] for r in receipts),
            "all_source_text_accounted_for": False,
            "imp_roundtrip_against_native": "NOT_TESTED",
            "redistribution_authorized": False,
            "published": False}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--private-output", type=Path)
    ap.add_argument("--collision-census", action="store_true")
    args = ap.parse_args(argv)
    manifest = json.loads(args.manifest.read_text("utf-8"))
    if args.collision_census:
        if args.private_output is not None:
            ap.error("--private-output is not used for the collision census")
        report = build_original_collision_census(manifest, args.source_dir)
    else:
        if args.private_output is None:
            ap.error("--private-output is required for private IMP generation")
        report = build_private_candidate(manifest, args.source_dir, args.private_output)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
