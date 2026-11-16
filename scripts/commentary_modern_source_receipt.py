#!/usr/bin/env python3
"""Read-only, source-neutral SWORD commentary chapter/intro receipt.

This is an audit INPUT for human/AI editorial modernization, not a translator,
SWORD builder, or semantic approval. No source prose, note text or XML is ever
written to stdout, a report, or a GitHub Actions artifact.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus

CHAPTER = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]{0,2}$")
OSIS_K = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]{0,2})\.([1-9][0-9]{0,2})$")
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")


def _xml_stats(raw: bytes) -> dict:
    """Count literal original structural markers, never normalize their data."""
    try:
        root = ET.fromstring(b"<original>" + raw + b"</original>")
    except ET.ParseError:
        return {"strict_xml_fragment": False}
    tags = defaultdict(int)
    for node in root.iter():
        if node is root:
            continue
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in ("div", "p", "title", "reference", "note", "hi",
                   "q", "quote", "table", "row", "cell", "l", "lb", "verse"):
            tags[tag] += 1
    return {"strict_xml_fragment": True, "tag_counts": dict(sorted(tags.items()))}


class Receipt:
    def __init__(self, chapters: list[str]):
        if not chapters or len(chapters) > 24 or len(set(chapters)) != len(chapters):
            raise ValueError("Supply 1–24 distinct canonical chapter OSIS keys")
        if any(CHAPTER.fullmatch(ch) is None for ch in chapters):
            raise ValueError("Invalid requested chapter OSIS reference")
        self.chapters = chapters
        self.by_chapter: dict[str, dict[str, dict]] = {ch: {} for ch in chapters}
        self.intros: dict[str, list[dict]] = {ch: [] for ch in chapters}
        self.books = {c.split(".", 1)[0] for c in chapters}

    def observe(self, kind: str, ref: str, raw: bytes) -> None:
        if kind == "U":
            return
        if kind not in ("K", "I"):
            raise ValueError("Invalid native frame type")
        checksum = hashlib.sha256(raw).hexdigest()
        if kind == "I":
            # Preserve a book-wide I as a separate source unit. Do not assume
            # chapter I entries belong to the previous/next numbered key.
            book = ref.split(".", 1)[0]
            targets = []
            for ch in self.chapters:
                if ch.split(".", 1)[0] != book:
                    continue
                if ref in (book, book + ".0.0") and ch.endswith(".1"):
                    targets.append(ch)
                elif ref in (ch, ch + ".0"):
                    targets.append(ch)
            for ch in targets:
                self.intros[ch].append({
                    "key": ref, "raw_sha256": checksum,
                    "raw_bytes": len(raw), "markup": _xml_stats(raw)
                })
            return
        match = OSIS_K.fullmatch(ref)
        if not match:
            raise ValueError("Native numbered commentary key is malformed")
        chapter = match.group(1) + "." + match.group(2)
        if chapter not in self.by_chapter:
            return
        sections = self.by_chapter[chapter]
        if checksum not in sections:
            sections[checksum] = {
                "source_unit_sha256": checksum,
                "first_key": ref, "keys": [],
                "raw_bytes": len(raw), "markup": _xml_stats(raw)
            }
        sections[checksum]["keys"].append(ref)

    def report(self, source_report: dict, expected_sha: str) -> dict:
        if not HEX_SHA.fullmatch(expected_sha):
            raise ValueError("Expected whole-source SHA-256 is invalid")
        actual = source_report["all_native_raw_entries_ordered_sha256"]
        if actual != expected_sha:
            raise ValueError("Complete native raw corpus hash does not match pinned edition")
        output = {}
        for chapter in self.chapters:
            blocks = list(self.by_chapter[chapter].values())
            if not blocks:
                raise ValueError("Requested chapter has no observed source commentary: " + chapter)
            keys = [key for b in blocks for key in b["keys"]]
            if len(set(keys)) != len(keys):
                raise ValueError("Repeated original native key in chapter " + chapter)
            output[chapter] = {
                "distinct_original_raw_units": len(blocks),
                "original_native_numbered_keys": len(keys),
                "original_units": blocks,
                "native_introductions_not_assumed_to_be_exposition": self.intros[chapter],
            }
        return {
            "status": "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
            "original_compiled_corpus_sha256": actual,
            "source_module_version_verified_by_caller": True,
            "complete_native_counts": {
                "K": source_report["actual_occupied_numbered_entry_count"],
                "I": source_report["actual_occupied_intro_entry_count"],
                "TOP": source_report["actual_occupied_anonymous_top_entry_count"]
            },
            "chapters": output,
            "source_prose_or_original_markup_exported": False,
            "semantic_translation_independently_approved": False,
            "structured_derivative_readback_tested": False,
        }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--native-reader", required=True, type=Path)
    p.add_argument("--module-directory", required=True, type=Path)
    p.add_argument("--module-id", required=True)
    p.add_argument("--expected-corpus-sha256", required=True)
    p.add_argument("--chapters", nargs="+", required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    if not a.native_reader.is_file() or not a.module_directory.is_dir():
        p.error("Native reader and installed module root are required")
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", a.module_id) is None:
        p.error("Invalid installed module identifier")
    receipt = Receipt(a.chapters)
    env = os.environ.copy()
    env["SWORD_PATH"] = str(a.module_directory.resolve())
    process = subprocess.Popen([str(a.native_reader.resolve()), a.module_id],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if process.stdout is None:
            raise RuntimeError("Native reader output pipe was not opened")
        raw_report, _, _, _ = parse_native_raw_corpus(process.stdout,
                                                      on_entry=receipt.observe)
        process.stdout.close()
        if process.wait(timeout=30) != 0:
            raise ValueError("Source-native reader failed")
        doc = receipt.report(raw_report, a.expected_corpus_sha256)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("Native commentary source receipt: PASS; chapters="
              + str(len(a.chapters))
              + "; source prose and markup not exported")
        return 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
