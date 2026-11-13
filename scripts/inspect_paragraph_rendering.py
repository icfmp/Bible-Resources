#!/usr/bin/env python3
"""Compare paragraph-leading markers in pinned original OSIS and real SWORD.

Read-only. The released binary is never rewritten. Source and native prose
stay in memory; the report contains only safe verse IDs and shape counters.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

from publisher_osis_observation import read_pinned_publisher_osis
from publisher_osis_usfx_parity import original_osis_verses_and_notes, _nonspace
from source_native_maintext_probe import native_raw_main_text
from source_osis_inventory import _source_tree, OSIS
from stable_sword_refs import KEY

MAX_REFERENCES = 24
MAX_NATIVE = 2 * 1024 * 1024
MARKERS = ("**", "*", "#", "\u2020")


class ParagraphRenderingProbeError(ValueError):
    pass


def shape(value: str) -> dict:
    """No words are returned; the leading star is *diagnosed*, not stripped."""
    if not isinstance(value, str):
        raise ParagraphRenderingProbeError("Non-text content")
    prefix = value[:len(value) - len(value.lstrip())]
    remainder = value[len(prefix):]
    marker = next((mark for mark in MARKERS if remainder.startswith(mark)), None)
    after_marker = remainder[len(marker):] if marker else remainder
    return {
        "leading_whitespace_codepoints": len(prefix),
        "leading_ascii_spaces": prefix.count(" "),
        "leading_lf": prefix.count("\n"),
        "leading_cr": prefix.count("\r"),
        "leading_nbsp": prefix.count("\u00a0"),
        "leading_narrow_nbsp": prefix.count("\u202f"),
        "starts_with_editorial_symbol_candidate": marker,
        "space_immediately_after_symbol": bool(marker and after_marker.startswith(" ")),
        "nonspace_codepoint_count": len(_nonspace(value)),
        "trailing_whitespace_codepoints": len(value) - len(value.rstrip()),
    }


def diff(source: str, native: str) -> dict:
    a, b = shape(source), shape(native)
    return {
        "original": a,
        "compiled": b,
        "same_nonspace_characters": _nonspace(source) == _nonspace(native),
        "same_exact_verse_characters": source == native,
        "same_leading_symbol": a["starts_with_editorial_symbol_candidate"] ==
                               b["starts_with_editorial_symbol_candidate"],
        "same_leading_whitespace": source[:len(source)-len(source.lstrip())] ==
                                   native[:len(native)-len(native.lstrip())],
    }


def source_structure(source: bytes, refs: set[str]) -> dict:
    """Identify direct authored paragraph container ancestry at each host."""
    root = _source_tree(source)
    result = {}
    for node in root.iter(OSIS + "verse"):
        ref = node.get("sID") or node.get("osisID")
        if ref not in refs or node.get("eID"):
            continue
        if ref in result:
            raise ParagraphRenderingProbeError("Duplicated authorial verse milestone")
        parent_chain = [
            {"tag": "p" if x.tag == OSIS + "p" else "l" if x.tag == OSIS + "l" else "lg"}
            for x in node.iterancestors()
            if x.tag in {OSIS + "p", OSIS + "l", OSIS + "lg"}
        ]
        result[ref] = {
            "authorial_container_chain": [x["tag"] for x in reversed(parent_chain)],
            "start_element_is_milestone": bool(node.get("sID")),
            "start_element_has_direct_text_marker": bool((node.text or "").lstrip().startswith("*")),
            "start_element_tail_has_marker": bool((node.tail or "").lstrip().startswith("*")),
            "first_following_sibling_tag": (
                node.getnext().tag.rsplit("}", 1)[-1]
                if node.getnext() is not None and isinstance(node.getnext().tag, str)
                else None
            ),
            "preceding_sibling_tag": (
                node.getprevious().tag.rsplit("}", 1)[-1]
                if node.getprevious() is not None and isinstance(node.getprevious().tag, str)
                else None
            ),
        }
    if set(result) != refs:
        raise ParagraphRenderingProbeError("Source original passage markers missing")
    return result


def analyze_source(source: bytes, references: list[str]) -> tuple[dict, dict]:
    strings, notes, metadata = original_osis_verses_and_notes(source)
    wanted = set(references)
    if not wanted <= strings.keys():
        raise ParagraphRenderingProbeError("Requested source reference absent")
    root = _source_tree(source)
    first_para_refs = set()
    for paragraph in root.iter(OSIS + "p"):
        first = next((verse.get("sID") or verse.get("osisID")
                      for verse in paragraph.iter(OSIS + "verse")
                      if not verse.get("eID")), None)
        if first:
            first_para_refs.add(first)
    occurrences = Counter()
    marker_refs = []
    semantic_groups = Counter()
    suspicious_nonfirst = []
    for ref, value in strings.items():
        s = shape(value)
        marker = s["starts_with_editorial_symbol_candidate"]
        if not marker:
            continue
        occurrences[marker] += 1
        if len(marker_refs) < 24:
            marker_refs.append(ref)
        beginning = value.lstrip()
        if beginning.startswith("*Dieu") or beginning.startswith("*Seigneur"):
            semantic_groups["protected_divine_name_candidate"] += 1
        elif beginning.startswith("*["):
            semantic_groups["protected_textual_uncertainty_candidate"] += 1
        elif ref in first_para_refs:
            semantic_groups["subject_division_at_paragraph_start_candidate"] += 1
        else:
            semantic_groups["not_at_authored_paragraph_start_unresolved"] += 1
            if len(suspicious_nonfirst) < 24:
                suspicious_nonfirst.append(ref)
    summary = {
        "original_verse_count": len(strings),
        "original_note_count": metadata["publisher_numbered_note_count"],
        "whole_source_leading_marker_counts": dict(sorted(occurrences.items())),
        "semantic_candidate_categories_not_editorial_certification": dict(sorted(semantic_groups.items())),
        "bounded_leading_marker_references": marker_refs,
        "bounded_unresolved_marker_references": suspicious_nonfirst,
    }
    return {ref: strings[ref] for ref in references}, summary


def inspect(*, resource_id: str, module_id: str, module_path: Path,
            native_reader: Path, references: list[str]) -> dict:
    if not isinstance(references, list) or not 1 <= len(references) <= MAX_REFERENCES:
        raise ParagraphRenderingProbeError("Reference selection must be bounded")
    if len(set(references)) != len(references) or any(
            not isinstance(ref, str) or KEY.fullmatch(ref) is None for ref in references):
        raise ParagraphRenderingProbeError("Invalid or repeated reference")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", module_id):
        raise ParagraphRenderingProbeError("Invalid native module ID")
    if not module_path.is_dir() or module_path.is_symlink() or not native_reader.is_file():
        raise ParagraphRenderingProbeError("Missing real native module or reader")
    source = read_pinned_publisher_osis(resource_id)
    selected, source_summary = analyze_source(source, references)
    structure = source_structure(source, set(references))
    os.environ["SWORD_PATH"] = str(module_path.resolve())
    rows = {}
    for ref in references:
        process = subprocess.run(
            [str(native_reader.resolve()), module_id, ref],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=dict(os.environ), check=False, timeout=20,
        )
        if process.returncode != 0 or not 0 < len(process.stdout) <= MAX_NATIVE:
            raise ParagraphRenderingProbeError("Actual native raw read failed at " + ref)
        compiled, excluded = native_raw_main_text(process.stdout)
        row = diff(selected[ref], compiled)
        row["original_paragraph_markup"] = structure[ref]
        row["native_raw_byte_sha256"] = sha256(process.stdout).hexdigest()
        row["native_note_and_title_element_counts"] = excluded
        rows[ref] = row
    return {
        "schema_version": 1,
        "status": "read_only_original_vs_released_native_paragraph_lexical_diagnostic",
        "official_source_sha256": sha256(source).hexdigest(),
        "module_id": module_id,
        "original_source_marker_summary": source_summary,
        "verse_samples": rows,
        "source_and_sword_bytes_unchanged": True,
        "full_corpus_native_rendering_verified": False,
        "andbible_gui_rendering_verified": False,
        "formatting_repair_implemented": False,
        "publication_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--module-path", type=Path, required=True)
    parser.add_argument("--native-reader", type=Path, required=True)
    parser.add_argument("--ref", action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        parser.error("Report must be a new file in an existing directory")
    result = inspect(resource_id=args.resource_id, module_id=args.module_id,
                     module_path=args.module_path, native_reader=args.native_reader,
                     references=args.ref)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Checked pinned source and exact native SWORD paragraph samples.")
    print("Source leading marker counts:", json.dumps(result["original_source_marker_summary"]["whole_source_leading_marker_counts"], sort_keys=True))
    print("Candidate marker meanings:", json.dumps(result["original_source_marker_summary"]["semantic_candidate_categories_not_editorial_certification"], sort_keys=True))
    print("Unresolved marker references:", result["original_source_marker_summary"]["bounded_unresolved_marker_references"])
    for ref, row in result["verse_samples"].items():
        print(ref, "source", json.dumps(row["original"], sort_keys=True),
              "native", json.dumps(row["compiled"], sort_keys=True),
              "same_nonspace", row["same_nonspace_characters"],
              "source_markup", row["original_paragraph_markup"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
