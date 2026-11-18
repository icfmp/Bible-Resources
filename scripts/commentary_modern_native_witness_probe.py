#!/usr/bin/env python3
"""Source-neutral, read-only secondary-witness anchors in SHA-pinned native SWORD.

This verifies *presence of a few source words in an exact raw K body*. It is
NOT literal whole-body collation, translation assessment, link approval or a
builder. Never export original prose or raw XML to a log/artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata
from xml.etree import ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus


def word_tokens(value: str) -> list[str]:
    """Ignore punctuation, preserve the exact case-folded word sequence."""
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", value).casefold(),
                      re.UNICODE)


def anchor_found(haystack: list[str], phrase: str) -> bool:
    needle = word_tokens(phrase)
    if len(needle) < 4 or len(needle) > 18:
        raise ValueError("A source-witness probe must have 4–18 words")
    return any(haystack[i:i + len(needle)] == needle
               for i in range(len(haystack) - len(needle) + 1))


def visible_text_and_references(raw: bytes) -> tuple[str, list[str], dict]:
    """Bounded parse: return source text only IN MEMORY, never in report/log."""
    root = ET.fromstring(b"<original>" + raw + b"</original>")
    labels = [node.tag.rsplit("}", 1)[-1] for node in root.iter()]
    refs = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "reference":
            value = node.attrib.get("osisRef", "")
            if value:
                refs.append(value)
    return (" ".join(root.itertext()), refs, {
        "reference_tags": labels.count("reference"),
        "note_tags": labels.count("note"),
        "title_tags": labels.count("title"),
        "paragraph_tags": labels.count("p"),
    })


def inspect_source(*, reader: Path, root: Path, receipt: Path,
                   manifest: Path) -> dict:
    witness = json.loads(manifest.read_text(encoding="utf-8"))
    inventory = json.loads(receipt.read_text(encoding="utf-8"))
    if witness.get("status") != "SOURCE_TEXT_SECONDARY_WITNESS_ANCHOR_CANDIDATES_NOT_EDITORIAL_APPROVAL":
        raise ValueError("Unknown or unapproved witness manifest status")
    if witness.get("source_native_corpus_sha256") != inventory.get("original_compiled_corpus_sha256"):
        raise ValueError("Witness manifest does not match exact native source edition")
    if inventory.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL":
        raise ValueError("No authoritative complete raw-source receipt")
    if inventory.get("source_prose_or_original_markup_exported") is not False:
        raise ValueError("Original source must remain private")
    cases = witness.get("source_group_probes")
    if not isinstance(cases, list) or not cases:
        raise ValueError("No source witness probes supplied")
    keys_needed = set()
    hash_policy = witness.get("source_group_hash_policy", "manifest_exact")
    if hash_policy not in ("manifest_exact", "authenticated_native_receipt"):
        raise ValueError("Unknown source group hash policy")
    chapters_to_check = {case["chapter"] for case in cases}
    for case in cases:
        if len(case.get("anchors", [])) < 2 and not case.get("reference_targets_to_probe"):
            raise ValueError("Case must have multiple independent source anchors")
        chapter = case["chapter"]
        groups = inventory["chapters"][chapter]["original_units"]
        matched = [group for group in groups
                   if group["first_key"] == case["first"] and
                   group["keys"][-1] == case["last"]]
        if len(matched) != 1:
            raise ValueError("Exact native key boundary mismatch: " + chapter)
        if hash_policy == "manifest_exact" and matched[0]["source_unit_sha256"] != case["sha"]:
            raise ValueError("Source-group SHA is not the pinned modern edition: " + chapter)
        keys_needed.update((case["first"], case["last"]))
    original_raw: dict[str, bytes] = {}
    # Inspect other native K/I bodies in each affected chapter when a lexical
    # source witness is absent from its expected source body. Keep raw in
    # memory only, deduplicated by content hash.
    chapter_bodies: dict[str, dict[str, bytes]] = {ch: {} for ch in chapters_to_check}
    env = os.environ.copy()
    env["SWORD_PATH"] = str(root.resolve())
    module_id = witness.get("native_module_id", "")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id):
        raise ValueError("Invalid real SWORD module ID in witness manifest")
    proc = subprocess.Popen([str(reader.resolve()), module_id],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise RuntimeError("Unable to open native SWORD reader stdout")
        def collect(kind: str, key: str, raw: bytes) -> None:
            if kind == "K" and key in keys_needed:
                if key in original_raw:
                    raise ValueError("Duplicate exact original K key")
                original_raw[key] = raw
            chapter = (key.rsplit(".", 1)[0] if kind == "K" else
                       key[:-2] if kind == "I" and key.endswith(".0") else
                       key if kind == "I" else "")
            if chapter in chapter_bodies:
                chapter_bodies[chapter].setdefault(
                    hashlib.sha256(raw).hexdigest(), raw)
        report, _, _, _ = parse_native_raw_corpus(proc.stdout, on_entry=collect)
        proc.stdout.close()
        if proc.wait(timeout=30) != 0:
            raise ValueError("Native reader exited unsuccessfully")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    if report["all_native_raw_entries_ordered_sha256"] != witness["source_native_corpus_sha256"]:
        raise ValueError("Complete original source corpus SHA mismatch")
    if set(original_raw) != keys_needed:
        raise ValueError("Selected native keys missing from original release")
    results = []
    for case in cases:
        first = original_raw[case["first"]]
        last = original_raw[case["last"]]
        native_sha = hashlib.sha256(first).hexdigest()
        unit = next(group for group in inventory["chapters"][case["chapter"]]["original_units"]
                    if group["first_key"] == case["first"] and
                    group["keys"][-1] == case["last"])
        if first != last or native_sha != unit["source_unit_sha256"]:
            raise ValueError("Native linked unit differs from authenticated native receipt")
        if hash_policy == "manifest_exact" and native_sha != case["sha"]:
            raise ValueError("Modern edition source group did not match pinned manuscript SHA")
        try:
            text, refs, markup = visible_text_and_references(first)
            parseable = True
        except ET.ParseError:
            text, refs, markup = "", [], {}
            parseable = False
        words = word_tokens(text)
        checks = [{
            "id": a["id"],
            "found_in_exact_published_native_body": (
                anchor_found(words, a["words"]) if parseable else False)
        } for a in case["anchors"]]
        for anchor, result in zip(case["anchors"], checks):
            if not result["found_in_exact_published_native_body"]:
                # A missing phrase could be indexed under another entry in
                # the same chapter. Test that possibility without exporting
                # original authorial words or raw markup.
                matches = 0
                for other_hash, other_raw in chapter_bodies[case["chapter"]].items():
                    if other_hash == native_sha:
                        continue
                    try:
                        other_text, _, _ = visible_text_and_references(other_raw)
                    except ET.ParseError:
                        continue
                    if anchor_found(word_tokens(other_text), anchor["words"]):
                        matches += 1
                result["matching_other_native_K_I_bodies_in_same_chapter"] = matches
        targets = [{
            "expected_target": t,
            "exact_native_reference_attribute_present": t in refs,
        } for t in case.get("reference_targets_to_probe", [])]
        results.append({
            "chapter": case["chapter"],
            "original_first_key": case["first"],
            "original_last_key": case["last"],
            "source_unit_sha256_matches": True,
            "compiled_raw_sha_matches_modern_manifest": native_sha == case["sha"],
            "native_xml_fragment_parseable": parseable,
            "original_visible_words_count": len(words),
            "markup_counts": markup,
            "secondary_witness_anchor_checks": checks,
            "distinct_native_K_I_bodies_examined_in_chapter": len(chapter_bodies[case["chapter"]]),
            "requested_original_reference_checks": targets,
            "all_witness_anchors_found": all(c["found_in_exact_published_native_body"] for c in checks),
            "lexical_anchor_only_not_complete_semantic_review": True,
        })
    return {
        "status": "SHA_PINNED_NATIVE_SECONDARY_ANCHOR_PROBE_ONLY_NOT_EDITORIAL_APPROVAL",
        "original_module": witness["source_module"],
        "exact_original_raw_corpus_sha256_matched": True,
        "probed_source_groups": len(results),
        "probed_chapters": len(set(x["chapter"] for x in results)),
        "all_anchor_probes_found": all(x["all_witness_anchors_found"] for x in results),
        "human_original_meaning_and_references_approved": False,
        "original_source_text_or_xml_exported": False,
        "derived_module_compiled_or_published": False,
        "groups": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-reader", type=Path, required=True)
    parser.add_argument("--module-directory", type=Path, required=True)
    parser.add_argument("--native-receipt", type=Path, required=True)
    parser.add_argument("--witness-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.native_reader.is_file() or not args.module_directory.is_dir():
        parser.error("Native reader and installed original root are required")
    result = inspect_source(reader=args.native_reader, root=args.module_directory,
                            receipt=args.native_receipt, manifest=args.witness_manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("NATIVE_WITNESS_PROBE source authenticated, original groups=" +
          str(result["probed_source_groups"]) +
          ", chapters=" + str(result["probed_chapters"]) +
          ", all secondary anchors matched=" + str(result["all_anchor_probes_found"]))
    for group in result["groups"]:
        print("NATIVE_WITNESS_GROUP " + json.dumps({
            "chapter": group["chapter"],
            "first_key": group["original_first_key"],
            "last_key": group["original_last_key"],
            "anchors": group["secondary_witness_anchor_checks"],
            "reference_target_probes": group["requested_original_reference_checks"],
            "native_source_visible_words": group["original_visible_words_count"],
            "markup_counts": group["markup_counts"],
        }, sort_keys=True))
    print("IMPORTANT: no full original prose/meaning/reference parity and no release acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
