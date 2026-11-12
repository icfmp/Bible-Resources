#!/usr/bin/env python3
"""Compile repaired private publisher OSIS with pinned SWORD; NEVER release.

The correction plan and output are temporary, source-SHA-bound and byte-text
safe. An actual native libSWORD readback verifies full numbered text/notes.
All originals, compiled binaries, and compiler log stay private/discarded.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile

from publisher_osis_observation import read_pinned_publisher_osis
from repair_osis_note_links import propose as propose_links
from repair_osis_inline_markup import propose as propose_inline
from publisher_osis_sword_candidate import (
    _candidate_result, _compile_osis, _create_candidate_layout, _read_native_frames,
)
from publisher_osis_usfx_parity import original_osis_verses_and_notes
from source_osis_inventory import source_inventory
from source_native_osis_structure_screen import (
    authorial_structures, authorial_body_opening_sequences,
)
from source_native_osis_boundary_positions import (
    authorial_book_streams, authorial_outside_book_titles,
)
from guard_osis import _schema, parse_xml
from source_osis_inventory import _source_tree
from source_native_ordered_body import compare_ordered_body_openings
from native_milestone_pair_audit import NativeMilestonePairAudit
from lxml import etree

SOURCE_HASH = "2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3"
LINK_SHA = "23b6225cf4f827f6f84e321ed60fedb55ec42c3bc2b5cf58747942bd32f6ad8d"
REPAIRED_SHA = "89b67a1007547b113c0049a2df8912b66716a406d19237f036d5dad71f7771c8"
MODULE = "JND2024RepairResearch"
V11N = "Luther"


class PrivateRepairedProbeError(ValueError):
    pass


def sha(value: bytes) -> str:
    return sha256(value).hexdigest()


def _source_notes_equal_except_targets(before, after) -> bool:
    if before.keys() != after.keys():
        return False
    return all(
        len(before[key]) == len(after[key]) and all(
            {k: v for k, v in old.items() if k != "targets"} ==
            {k: v for k, v in new.items() if k != "targets"}
            for old, new in zip(before[key], after[key])
        ) for key in before
    )


def _diagnose_temporary_body_order(tool: Path, reader: Path, scratch: Path,
                                   source: bytes, label: str) -> dict:
    """Inspect a wholly separate transient research compilation by structural kinds only."""
    work = scratch / ("debug-" + label)
    work.mkdir()
    _payload, output = _create_candidate_layout(work, MODULE + "Debug" + label, V11N)
    source_file = scratch / ("debug-" + label + ".xml")
    source_file.write_bytes(source)
    _compile_osis(tool, source_file, output, V11N,
                  scratch / ("debug-" + label + ".compiler-private.log"))
    milestones = NativeMilestonePairAudit()
    for kind, ref, raw in _read_native_frames(reader, MODULE + "Debug" + label,
                                              work / "payload"):
        milestones.observe(kind, ref, raw)
    milestones.finish()
    expected, expected_counts = authorial_body_opening_sequences(source)
    result = compare_ordered_body_openings(
        expected, milestones.private_ordered_body_openings(), expected_counts)
    return {
        "variant": label,
        "body_order_equal": result["same_order_and_kind_in_every_mapped_book"],
        "kinds_only": result["source_native_body_opening_kind_counts"],
        "first_differences_only": result["first_mismatch_book_references_no_scripture"][:2],
        "no_scripture_notes_or_binary_exposed": True,
    }


def probe(*, osis2mod: Path, native_index: Path, native_raw: Path,
          diatheke: Path, schema: Path, link_plan: Path, inline_plan: Path) -> dict:
    original = read_pinned_publisher_osis("frajnd-2024")
    if sha(original) != SOURCE_HASH:
        raise PrivateRepairedProbeError("Exact publisher original source drifted")
    a = json.loads(link_plan.read_text(encoding="utf-8"))
    b = json.loads(inline_plan.read_text(encoding="utf-8"))
    link, link_result = propose_links(original, a)
    if sha(link) != LINK_SHA or link_result["change_count"] != 11:
        raise PrivateRepairedProbeError("Research link source fingerprint disagrees")
    corrected, inline_result = propose_inline(link, b)
    if sha(corrected) != REPAIRED_SHA or inline_result["edit_count"] != 2:
        raise PrivateRepairedProbeError("Research inline source fingerprint disagrees")
    original_keys, original_index = source_inventory(original)
    corrected_keys, corrected_index = source_inventory(corrected)
    if original_keys != corrected_keys or corrected_index["source_verse_count"] != 31166:
        raise PrivateRepairedProbeError("Authored Scripture index changed")
    source_verses, source_notes, _original_meta = original_osis_verses_and_notes(original)
    final_verses, final_notes, _final_meta = original_osis_verses_and_notes(corrected)
    if (source_verses != final_verses or
            not _source_notes_equal_except_targets(source_notes, final_notes) or
            sum(map(len, final_notes.values())) != 6340):
        raise PrivateRepairedProbeError("Original Scripture or note content/anchors were changed")
    if original_index["source_verse_count"] != corrected_index["source_verse_count"]:
        raise PrivateRepairedProbeError("Verse count changed")
    policy = json.loads((Path(__file__).resolve().parents[1] / "config/osis-policy.json").read_text(encoding="utf-8"))
    validator, schema_sha = _schema(policy, schema)
    with tempfile.TemporaryDirectory(prefix="private-darby-repaired-sword-") as root:
        scratch = Path(root)
        source_file = scratch / "corrected-source-only.xml"
        source_file.write_bytes(corrected)
        doc = parse_xml(source_file, corrected, "PRIVATE_SOURCE_XML_INVALID")
        if not validator.validate(doc):
            raise PrivateRepairedProbeError("Corrected private source fails pinned official OSIS XSD")
        work = scratch / "module"
        work.mkdir()
        payload, output_dir = _create_candidate_layout(work, MODULE, V11N)
        compiler = _compile_osis(osis2mod, source_file, output_dir, V11N,
                                 scratch / "private-compiler.log")
        metrics = _candidate_result(
            native_index, native_raw, work, MODULE, V11N, final_verses, final_notes,
            authorial_structures(corrected),
            *authorial_body_opening_sequences(corrected),
            authorial_book_streams(corrected),
            authorial_outside_book_titles(corrected),
        )
        if metrics["candidate_status"] != "full_numbered_text_and_note_preflight_equal_not_approved":
            # Emit aggregate category counts and boolean structural outcomes only:
            # no Scripture, note body, raw XML, native binary, or original target text.
            counts = metrics["source_to_compiled_counts"]
            problems = {
                key: value for key, value in counts.items()
                if value and any(marker in key for marker in (
                    "different", "differs", "moved", "unverified",
                    "source_only", "native_only", "invalid",
                ))
            }
            body = metrics["original_to_compiled_body_opening_order"]
            positions = metrics["source_native_body_boundary_positions"]
            flags = {
                "ordered_body_same": body.get("same_order_and_kind_in_every_mapped_book"),
                "body_boundaries_same": positions.get("all_book_body_nonspace_and_boundary_events_equal"),
                "total_notes_compared": counts.get("note_pairs_compared"),
                "indexed_keys": counts.get("official_source_verse_count"),
            }
            print("RESEARCH-ONLY safe native mismatch categories:",
                  json.dumps({"aggregate_problem_counts": problems,
                              "structural_flags": flags,
                              "body_opening_kind_counts": body.get("source_native_body_opening_kind_counts"),
                              "first_body_mismatch_host_references_only":
                                  body.get("first_mismatch_book_references_no_scripture", [])[:4]}, sort_keys=True))
            # Compilers sometimes treat serially identical XML differently.
            # Isolate serialization from LINK and INLINE changes; never
            # normalize away a reported missing original poetry marker.
            from source_osis_inventory import _source_tree
            reserialized_original = etree.tostring(
                _source_tree(original), encoding="UTF-8", xml_declaration=True)
            if "".join(_source_tree(original).itertext()) != "".join(
                    _source_tree(reserialized_original).itertext()):
                raise PrivateRepairedProbeError("Original-only XML serialization changed text")
            scenarios = [
                ("Original", original),
                ("Reserialized", reserialized_original),
                ("LinksOnly", link),
            ]
            diagnoses = []
            for label, data in scenarios:
                try:
                    diagnoses.append(_diagnose_temporary_body_order(
                        osis2mod, native_raw, scratch, data, label))
                except Exception as exc:
                    diagnoses.append({"variant": label, "status": "private_diagnostic_failed",
                                     "exception_type": type(exc).__name__})
            print("RESEARCH-ONLY source serialization and attribute isolation:",
                  json.dumps(diagnoses, sort_keys=True))
            raise PrivateRepairedProbeError("Corrected candidate full native fidelity gate did not pass")
        env = dict(os.environ, SWORD_PATH=str(payload.resolve()))
        passages = (
            "Genesis 1:1", "Psalms 23:1", "Matthew 1:1",
            "John 3:16", "Ezekiel 4:11", "Romans 16:25",
            "Revelation 22:21",
        )
        smoke = []
        for reference in passages:
            cmd = [str(diatheke), "-b", MODULE, "-f", "plain", "-m", "1", "-k", reference]
            result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=40, check=False)
            if result.returncode != 0 or len(result.stdout.strip()) < 15 or len(result.stdout) > 200000:
                raise PrivateRepairedProbeError("Private SWORD text readback failed")
            smoke.append({"reference": reference, "reader_status": "readable"})
        if sha(source_file.read_bytes()) != REPAIRED_SHA:
            raise PrivateRepairedProbeError("Private source mutated during compiler invocation")
    return {
        "schema_version": 1,
        "status": "repaired_osis_to_native_sword_full_text_notes_research_passed",
        "publisher_original_sha256": SOURCE_HASH,
        "private_link_repaired_sha256": LINK_SHA,
        "private_full_repaired_osis_sha256": REPAIRED_SHA,
        "official_crosswire_schema_sha256": schema_sha,
        "source_key_count": 31166,
        "source_note_count": 6340,
        "machine_note_targets_replaced": 8,
        "nonexistent_source_verse_link_targets_disabled": 3,
        "invalid_inline_osis_elements_replaced": 2,
        "original_notes_unchanged_except_approved_navigation_targets": True,
        "original_verse_words_and_punctuation_equal": True,
        "official_osis_xsd_conforming": True,
        "native_result": metrics,
        "real_sword_readbacks": smoke,
        "compiler_diagnostic_category_counts": compiler["diagnostic_categories"],
        "candidate_binary_sha256_not_public_release": metrics["compiled_payload_sha256"],
        "original_or_compiled_binary_uploaded": False,
        "xiphos_gui_links_tested": False,
        "published_or_editorially_approved": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("osis2mod", "native-index", "native-raw", "diatheke", "schema",
                 "link-plan", "inline-plan", "report"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    if args.report.is_symlink() or args.report.exists() or not args.report.parent.is_dir():
        p.error("Output must be a fresh metadata-only report")
    report = probe(
        osis2mod=args.osis2mod, native_index=args.native_index,
        native_raw=args.native_raw, diatheke=args.diatheke, schema=args.schema,
        link_plan=args.link_plan, inline_plan=args.inline_plan)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print("Exact private repaired source/native reader gate passed; no release made")


if __name__ == "__main__":
    main()
