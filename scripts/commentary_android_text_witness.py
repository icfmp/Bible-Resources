#!/usr/bin/env python3
"""PRIVATE exact-original MHCC prose vs actual Android WebView accessibility witness.

This is a *sample* reader-text check, not full editorial or visual sign-off.
Only text from the original SHA-pinned native zCom XML and real official
AndBible WebView descendants is compared. No text, UI XML, screenshots,
source excerpts, or private ZIP may leave the temporary CI workspace.
"""
from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus, RawCorpusError

from lxml import etree

from commentary_xiphos_dual_reader import _normalized_words
from pilot_preflight import PilotError
from probe_andbible_android_emulator import PACKAGE

REF = re.compile(r"[1-4]?[A-Za-z][A-Za-z ]{0,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}\Z")
WINDOW = 16
MAX_XML = 3_000_000


def read_only_actually_occupied_original_entries(
    source_root: Path, module_id: str, references: list[str],
    native_reader: Path,
) -> tuple[dict[str, bytes], int]:
    """Select only real occupied source keys; refuse all other native failures.

    The source module may index a commentary *range* at one physical verse
    key; querying other verse numbers must not invent or copy an entry.
    Our compiled native reader reserves exit code 9 for a nonmatching or
    unoccupied exact VerseKey. It verifies canonical key equality itself.
    """
    if (source_root.is_symlink() or not source_root.is_dir()
            or native_reader.is_symlink() or not native_reader.is_file()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id)
            or not isinstance(references, list)
            or not 2 <= len(references) <= 12
            or len(set(references)) != len(references)
            or any(not isinstance(ref, str) or not REF.fullmatch(ref)
                   for ref in references)):
        raise PilotError("Unsafe original occupied MHCC source inspection")
    present = {}
    not_verified_occupied = 0
    for reference in references:
        try:
            run = subprocess.run(
                [str(native_reader), module_id, reference],
                env=dict(os.environ, SWORD_PATH=str(source_root)),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PilotError("Original native SWORD sample inspection unavailable") from exc
        if run.returncode == 9:
            not_verified_occupied += 1
            continue
        if run.returncode != 0:
            raise PilotError(
                "Original native SWORD inspector failed for a reason other than an "
                "unoccupied key (status %d)" % run.returncode
            )
        if not 8 <= len(run.stdout) <= 256_000:
            raise PilotError("Unbounded original native occupied SWORD body")
        present[reference] = run.stdout
    if not present:
        raise PilotError("No actually occupied original source sample key proved")
    return present, not_verified_occupied


def _actual_original_authorial_words(native_xml: bytes) -> list[str]:
    """Extract real source body words via strict, non-network XML, never repair it."""
    if not isinstance(native_xml, bytes) or not 8 <= len(native_xml) <= 256_000:
        raise PilotError("Unbounded original Android source word witness")
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
        recover=False, huge_tree=False,
    )
    try:
        root = etree.fromstring(b"<source>" + native_xml + b"</source>", parser)
    except etree.XMLSyntaxError:
        return []
    words = _normalized_words(" ".join(root.itertext()).encode("utf-8"))
    if len(words) > 30000:
        raise PilotError("Unbounded original Android source word sequence")
    return words


def _actual_android_webview_word_sequences(ui_xml: bytes) -> tuple[list[list[str]], int]:
    """Read real WebView *descendant* text only; exclude toolbar/module names.

    UIAccessibility can expose a WebView with no authorial descendants. This
    yields INCONCLUSIVE, never proof of a damaged original commentary.
    """
    if not isinstance(ui_xml, bytes) or len(ui_xml) > MAX_XML:
        raise PilotError("Unbounded actual Android accessibility snapshot")
    try:
        root = ET.fromstring(ui_xml)
    except ET.ParseError:
        return [], 0
    sequences = []
    webviews = 0
    for node in root.iter("node"):
        if (node.attrib.get("package") != PACKAGE
                or not node.attrib.get("class", "").endswith("WebView")):
            continue
        webviews += 1
        if webviews > 12:
            raise PilotError("Unexpected number of Android WebViews")
        chunks = []
        for descendant in node.iter("node"):
            # The top-level WebView may contain a generic accessibility label,
            # but the actual content is in its descendants.
            if descendant is node:
                continue
            if descendant.attrib.get("package", PACKAGE) != PACKAGE:
                continue
            for key in ("text", "content-desc"):
                text = descendant.attrib.get(key, "")
                if text and len(text) <= 80_000:
                    chunks.append(text)
                    value = _normalized_words(text.encode("utf-8"))
                    if len(value) >= WINDOW:
                        sequences.append(value)
        # Allow a paragraph split across WebView descendants while requiring
        # that all matched prose stays in a *single real WebView*.
        if chunks:
            entire = _normalized_words(" ".join(chunks).encode("utf-8"))
            if len(entire) >= WINDOW:
                sequences.append(entire)
    if len(sequences) > 3000:
        raise PilotError("Unbounded Android descendant text nodes")
    return sequences, webviews


def full_native_original_prose_in_real_android_webview(
    source_root: Path, module_id: str, native_scanner: Path,
    expected_corpus_sha256: str, actual_ui_xml: bytes,
) -> dict:
    """One full, exact SHA-verified original scan; no passage-reference guess.

    Rather than infer that the Android reader currently displays one of five
    arbitrarily sampled references, compare real WebView descendant prose
    against every genuine *occupied* native numbered source key.
    """
    if (source_root.is_symlink() or not source_root.is_dir()
            or native_scanner.is_symlink() or not native_scanner.is_file()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_corpus_sha256)):
        raise PilotError("Unapproved full original stock SWORD scan context")
    sequences, webviews = _actual_android_webview_word_sequences(actual_ui_xml)
    visible = set()
    for words in sequences:
        for pos in range(len(words) - WINDOW + 1):
            phrase = tuple(words[pos:pos + WINDOW])
            if len(" ".join(phrase)) >= 85:
                visible.add(phrase)
    matching_entries = 0
    substantial_entries = 0
    def examine(kind: str, key: str, raw: bytes) -> None:
        nonlocal matching_entries, substantial_entries
        if kind != "K":
            return
        words = _actual_original_authorial_words(raw) if len(raw) >= 8 else []
        if len(words) < 32:
            return
        substantial_entries += 1
        for pos in range(12, min(len(words) - WINDOW + 1, 350)):
            phrase = tuple(words[pos:pos + WINDOW])
            if phrase in visible:
                matching_entries += 1
                break

    process = None
    try:
        process = subprocess.Popen(
            ["timeout", "300s", str(native_scanner), module_id],
            env=dict(os.environ, SWORD_PATH=str(source_root)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        if process.stdout is None:
            raise PilotError("Native original stream stdout unavailable")
        inventory, _, _, _ = parse_native_raw_corpus(
            process.stdout, on_entry=examine,
        )
        process.stdout.close()
        result_code = process.wait(timeout=20)
        if (result_code != 0 or inventory["all_native_raw_entries_ordered_sha256"]
                != expected_corpus_sha256):
            raise PilotError("Original full-native corpus digest or scanner changed")
    except (OSError, subprocess.TimeoutExpired, RawCorpusError) as exc:
        raise PilotError("Independent original full-native commentary scan unavailable") from exc
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
    scanned = inventory["all_actual_raw_entries_scanned"]
    if not 1 <= substantial_entries <= scanned or matching_entries > substantial_entries:
        raise PilotError("Unbounded original substantial commentary sample count")
    verified = matching_entries > 0 and webviews > 0
    return {
        "scope": "all_occupied_original_native_zCom_keys_vs_real_Android_WebView_prose",
        "original_full_native_corpus_sha256_attested": True,
        "actual_original_native_occupied_keys_scanned": scanned,
        "original_native_entries_with_substantial_exposition": substantial_entries,
        "real_AndBible_WebViews_observed": webviews,
        "real_AndBible_WebView_text_sequences_examined": len(sequences),
        "source_occupied_entries_with_16_consecutive_words_visible": matching_entries,
        "actual_original_authorial_prose_in_real_Android_WebView_verified": verified,
        "status": (
            "source_pinned_full_corpus_original_prose_visible_in_real_Android_WebView"
            if verified else "inconclusive_no_full_original_prose_witness_in_accessibility"
        ),
        "source_words_android_UI_XML_screenshots_or_ZIP_exported": False,
    }


def original_prose_in_real_android_webview(
    original_entries: Mapping[str, bytes], actual_ui_xml: bytes,
) -> dict:
    """Test 16 consecutive original words in a real native Android WebView.

    Never accept module titles, source ref labels, the Bible text, a screenshot
    change, or a selected-menu indicator as authorial prose. A visible match
    is only a bounded positive excerpt; absence is INCONCLUSIVE.
    """
    if (not isinstance(original_entries, Mapping)
            or not 1 <= len(original_entries) <= 12
            or any(not isinstance(k, str) or not REF.fullmatch(k)
                   for k in original_entries)):
        raise PilotError("Unreviewed original MHCC reference samples")
    sequences, webviews = _actual_android_webview_word_sequences(actual_ui_xml)
    visible = set()
    text_node_sequences = 0
    for words in sequences:
        text_node_sequences += 1
        for offset in range(len(words) - WINDOW + 1):
            visible.add(tuple(words[offset:offset + WINDOW]))
    inspected = 0
    matched = 0
    for native_xml in original_entries.values():
        words = _actual_original_authorial_words(native_xml)
        inspected += 1
        # The first 12 source words may be nonauthorial module/OSIS labels.
        # Require substantial original exposition well inside the body.
        if len(words) < 32:
            continue
        for offset in range(12, min(len(words) - WINDOW + 1, 350)):
            phrase = tuple(words[offset:offset + WINDOW])
            if len(" ".join(phrase)) < 85:
                continue
            if phrase in visible:
                matched += 1
                break
    verified = matched > 0 and webviews > 0
    return {
        "scope": "exact_original_native_zCom_prose_vs_actual_AndBible_WebView_accessibility",
        "original_native_occupied_sample_keys_inspected": inspected,
        "real_AndBible_WebViews_observed": webviews,
        "real_AndBible_WebView_text_sequences_examined": text_node_sequences,
        "original_prose_sample_entries_with_16_consecutive_words_visible": matched,
        "actual_original_prose_excerpt_in_Android_WebView_verified": verified,
        "status": (
            "source_pinned_original_exposition_visible_in_real_Android_WebView"
            if verified else "inconclusive_no_source_prose_witness_in_accessibility"
        ),
        "original_prose_UI_text_XML_screenshots_or_ZIP_exported": False,
    }
