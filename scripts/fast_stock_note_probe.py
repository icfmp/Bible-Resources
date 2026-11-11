#!/usr/bin/env python3
"""Bounded, source-first note preflight before expensive SWORD layout audits.

This deliberately samples *original* note-bearing verse references via the
independent exact-key SWORD reader. A demonstrated source/native difference
blocks unchanged stock reuse; an inconclusive sample NEVER proves parity.
Original Scripture, note text, callers and raw XML remain in private memory.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unicodedata

from lsg_source_compare import read_source_xml
from real_second_bible_probe import _safe_single_module
from source_native_notes_audit import (
    collect_usfx_numbered_notes, parse_native_numbered_notes, NoteEvidenceError,
)
from source_native_scope import read_crosswalk
from stable_sword_refs import KEY

MAX_SAMPLES = 12
MAX_RAW = 2 * 1024 * 1024


def _fold(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def _receipt(status: str, reason: str, *, source_notes: int = 0,
             probed: int = 0, ref: str | None = None) -> dict:
    if status not in {"BLOCKED", "REVIEW_REQUIRED"}:
        raise ValueError("Unsupported fast stock decision")
    # Reference IDs are the sole source-derived string allowed in receipts.
    if ref is not None and not KEY.fullmatch(ref):
        raise ValueError("Untrusted stock source reference")
    return {
        "schema_version": 1,
        "status": status,
        "reason_code": reason,
        "sampled_exact_source_reference": ref,
        "original_numbered_note_inventory_count": source_notes,
        "independent_exact_native_verse_probes": probed,
        "fast_stock_reuse_disqualified": status == "BLOCKED",
        "whole_corpus_text_or_note_parity_verified": False,
        "stock_reuse_or_publication_approved": False,
        "source_words_notes_callers_and_targets_exposed": False,
    }


def _sample_references(source_attributes: dict, cap: int) -> list[str]:
    """Prioritize distinct books; no edition-specific verse keys or counts."""
    eligible = [
        ref for ref, attributes in source_attributes.items()
        if any(attr["caller"] not in (None, "", "+", "-")
               for attr in attributes)
    ]
    first_by_book = {}
    for ref in eligible:
        if KEY.fullmatch(ref) is None:
            raise NoteEvidenceError("Unrecognized source-mapped note verse key")
        first_by_book.setdefault(ref.split(".", 1)[0], ref)
    choices = list(first_by_book.values())[:cap]
    for ref in eligible:
        if len(choices) == cap:
            break
        if ref not in choices:
            choices.append(ref)
    return choices


def probe_stock_note_callers(source_zip: Path, stock_zip: Path,
                             crosswalk: Path, exact_entry_binary: Path,
                             expected_module_id: str,
                             *, max_samples: int = MAX_SAMPLES) -> dict:
    """Quickly disqualify known note-loss stock modules, not certify good ones.

    All ZIP bytes have ALREADY passed the enclosing stage's manifest SHA gate.
    Real module identity is still independently checked by the stock parser.
    """
    if (type(max_samples) is not int or not 1 <= max_samples <= MAX_SAMPLES
            or not exact_entry_binary.is_file()
            or exact_entry_binary.is_symlink()):
        return _receipt("REVIEW_REQUIRED", "exact_native_reader_prerequisite_missing")
    try:
        raw, _metadata = read_source_xml(source_zip, source_format="usfx")
        mapping = read_crosswalk(crosswalk)
        attrs = {}
        notes, scope = collect_usfx_numbered_notes(
            raw, mapping, attributes_out=attrs)
        total = scope["mapped_source_numbered_note_count"]
        # This narrow sample never approves notes outside numbered verses,
        # unindexed book introductions or unmapped source books.
        refs = _sample_references(attrs, max_samples)
    except (ValueError, OSError, UnicodeError, NoteEvidenceError):
        return _receipt("REVIEW_REQUIRED", "original_numbered_note_sampling_unverified")
    if not refs:
        return _receipt("REVIEW_REQUIRED", "no_literal_caller_note_sample",
                        source_notes=total)
    try:
        with tempfile.TemporaryDirectory(prefix="stock-note-preflight-") as root:
            isolated = Path(root) / "stock"
            conf = _safe_single_module(stock_zip, isolated)
            if conf["module_id"] != expected_module_id:
                return _receipt("REVIEW_REQUIRED", "module_identity_disagrees",
                                source_notes=total)
            env = dict(os.environ, SWORD_PATH=str((isolated / "payload").resolve(strict=True)))
            probed = 0
            for ref in refs:
                try:
                    result = subprocess.run(
                        [str(exact_entry_binary.resolve(strict=True)),
                         expected_module_id, ref],
                        env=env, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, timeout=12, check=False)
                except (OSError, subprocess.TimeoutExpired):
                    return _receipt("REVIEW_REQUIRED", "exact_native_sample_unavailable",
                                    source_notes=total, probed=probed)
                if result.returncode or len(result.stdout) > MAX_RAW:
                    return _receipt("REVIEW_REQUIRED", "native_sample_key_unaddressable",
                                    source_notes=total, probed=probed)
                try:
                    compiled_attributes = []
                    compiled_notes = parse_native_numbered_notes(
                        result.stdout, attributes_out=compiled_attributes)
                except (ValueError, UnicodeError, NoteEvidenceError):
                    return _receipt("REVIEW_REQUIRED", "native_note_markup_unparseable",
                                    source_notes=total, probed=probed)
                probed += 1
                source_notes = notes[ref]
                source_attrs = attrs[ref]
                # A different note count/body may arise from an edition
                # mismatch, different source keys, or an OSIS serialization.
                # Do not diagnose an original caller loss until the exact
                # note bodies can be independently matched. Deep audit must
                # resolve these cases, not auto-rebuild from a sample.
                if len(compiled_notes) != len(source_notes):
                    return _receipt("REVIEW_REQUIRED", "sample_note_count_requires_full_audit",
                                    source_notes=total, probed=probed, ref=ref)
                if any(_fold(old[1]) != _fold(new[1])
                       for old, new in zip(source_notes, compiled_notes)):
                    return _receipt("REVIEW_REQUIRED", "sample_note_body_requires_full_audit",
                                    source_notes=total, probed=probed, ref=ref)
                for authored, native in zip(source_attrs, compiled_attributes):
                    caller = authored["caller"]
                    if caller in (None, "", "+", "-"):
                        continue
                    if not native["n"]:
                        return _receipt("BLOCKED", "literal_note_caller_missing",
                                        source_notes=total, probed=probed, ref=ref)
                    if caller != native["n"]:
                        return _receipt("BLOCKED", "literal_note_caller_changed",
                                        source_notes=total, probed=probed, ref=ref)
                    source_tag = authored["source_tag"]
                    if source_tag in {"x", "ex", "f", "fe", "ef"}:
                        source_crossref = source_tag in {"x", "ex"}
                        if source_crossref != (native["osis_type"] == "crossReference"):
                            return _receipt("BLOCKED", "crossreference_note_kind_changed",
                                            source_notes=total, probed=probed, ref=ref)
            return _receipt("REVIEW_REQUIRED", "sample_only_no_proven_stock_loss",
                            source_notes=total, probed=probed)
    except (ValueError, OSError, UnicodeError):
        return _receipt("REVIEW_REQUIRED", "isolated_stock_module_unverified",
                        source_notes=total)
