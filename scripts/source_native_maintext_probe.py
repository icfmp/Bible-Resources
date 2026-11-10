#!/usr/bin/env python3
"""Private original-USFX vs actual stock-SWORD whole-corpus main-text diagnostic.

The publisher's original USFX and SWORD ZIPs are read independently.
Text/notes are processed ONLY inside Python memory; JSON contains hashes,
counts and key IDs, never Scripture. This is NOT a notes/layout, conversion,
source-edition identity, rights, or publication certificate.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
import unicodedata

from lxml import etree

from lsg_source_compare import read_source_xml, scan_usfx
from real_second_bible_probe import _safe_single_module
from native_absorbed_verse_groups import inspect_absorbed_source_verse_groups
from source_native_notes_audit import collect_usfx_numbered_notes, NoteAudit
from source_native_scope import read_crosswalk
from maintext_whitespace_patterns import MainTextWhitespacePatterns
from native_sword_markup_census import NativeMarkupCensus
from native_milestone_pair_audit import NativeMilestonePairAudit
from source_native_paragraph_counts import compare_authored_native_paragraphs, audit_usfx_book_prefaces
from native_book_intro_screen import private_original_preface_text, NativeBookIntroScreen
from source_native_layout_anchors import source_usfx_layout_start_anchors, compare_start_anchors
from source_native_ordered_body import original_body_opening_sequences, compare_ordered_body_openings, OrderedStructureError
from source_native_word_boundaries import (
    BoundaryAuditError, NativeBodyBoundaries, original_usfx_body_boundaries,
    compare_body_boundary_word_positions,
)
from source_native_record_scope_triage import (
    ScopeTriageError, compare_body_record_scopes,
)
from source_native_nonspace_boundaries import (
    NonspaceBoundaryError, compare_punctuation_sensitive_boundaries,
)
from stable_sword_refs import module_payload_digest
from sword_native_raw_corpus_inventory import (
    inspect_native_raw_corpus, write_new_metadata_report,
)

MAX_XML = 128 * 1024 * 1024
MAX_VERSE = 2 * 1024 * 1024
MAX_MISMATCHES = 25
# USFX p[@sfm="sp"] is a *speaker identification* (not a
# Scripture verse); see eBible's USFX schema and USFM/USX paragraph styles.
# Skip only an unambiguous heading node, never a whole paragraph carrying
# numbered Scripture verse markers. All excluded nodes remain in the source.
USFX_SPEAKER_P_STYLES = {"sp"}
USFX_NOTE = {"f", "fe", "x", "note", "ef", "ex"}
USFX_HEAD = {"s", "s1", "s2", "s3", "s4", "ms", "ms1", "ms2",
             "mt", "mt1", "mt2", "mr", "d", "cl", "r", "rem"}
# Generated verse/chapter labels and alternatives are not authored
# Scripture prose. A <ve> milestone also explicitly ends the verse.
USFX_LABELS = {"vp", "va", "cp", "ca"}
NATIVE_SKIP = {"note", "title"}
WORD = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)
USFM_ID = re.compile(r"^[1-4]?[A-Z][A-Z0-9]{1,4}$")


class MainTextParityError(ValueError):
    """Authored or native text could not be independently audited."""


def _tree(data: bytes, root_name: str):
    if not 0 < len(data) <= MAX_XML:
        raise MainTextParityError("Empty or oversized original XML")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        tree = etree.ElementTree(etree.fromstring(data, parser))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise MainTextParityError("Unparseable original source XML") from exc
    if (tree.docinfo.doctype or tree.docinfo.internalDTD
            or tree.docinfo.externalDTD or tree.getroot().tag != root_name):
        raise MainTextParityError("Unexpected source XML root or DTD")
    return tree.getroot()


def authored_usfx_main_text(xml: bytes, mapping: list[tuple[str, str]]):
    """Collect all mapped source verse characters, retaining punctuation/case.

    Heading and note bodies are separately counted but NOT mixed into main
    Scripture. The complete authored source may include unmapped books.
    """
    try:
        metadata, authored_keys = scan_usfx(xml)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise MainTextParityError("Malformed or unsupported original USFX XML") from exc
    if metadata["duplicate_verse_ids"] or metadata["nonstandard_verse_identifiers"]:
        raise MainTextParityError("Ambiguous authored USFX keys")
    root = _tree(xml, "usfx")
    pairs = dict(mapping)
    if not pairs or len(pairs) != len(mapping) or len(set(pairs.values())) != len(mapping):
        raise MainTextParityError("Ambiguous explicit book crosswalk")
    books = [x for x in root.iter() if isinstance(x.tag, str)
             and etree.QName(x).localname == "book"]
    if len(books) != len(metadata["original_books"]):
        raise MainTextParityError("Nested or ambiguous source book structure")
    observed: dict[str, list[str]] = {}
    skipped = Counter()
    visited = set()
    visited_order = []
    for book in books:
        src = book.get("id")
        if (not src or not USFM_ID.fullmatch(src) or src in visited):
            raise MainTextParityError("Unsafe or repeated authorial source book ID")
        visited.add(src)
        visited_order.append(src)
        if src not in pairs:
            continue
        dest = pairs[src]
        chapter = None
        active = None

        def append(fragment):
            if fragment and active is not None:
                observed[active].append(fragment)

        def visit(node, depth=0):
            nonlocal chapter, active
            if depth > 256:
                raise MainTextParityError("Source XML nesting exceeds safe bound")
            if not isinstance(node.tag, str):
                return
            kind = etree.QName(node).localname
            style = node.get("sfm", "")
            if ((kind == "p" and style in USFX_SPEAKER_P_STYLES)
                    or kind in USFX_NOTE or kind in USFX_HEAD
                    or kind in USFX_LABELS):
                if any(isinstance(child.tag, str)
                       and etree.QName(child).localname in {"c", "v"}
                       for child in node.iterdescendants()):
                    raise MainTextParityError(
                        "Editorial/source-note container encloses numbered text markers")
                skipped[f"{kind}:{style}" if kind == "p" else kind] += 1
                return
            if kind == "ve":
                skipped["ve"] += 1
                active = None
                return
            if kind == "book" and depth:
                raise MainTextParityError("Nested source books are unsupported")
            if kind == "c":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0:
                    raise MainTextParityError("Invalid authored chapter marker")
                chapter, active = int(value), None
            elif kind == "v":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) <= 0 or chapter is None:
                    raise MainTextParityError("Ambiguous authored verse, including ranges")
                active = f"{dest}.{chapter}.{int(value)}"
                if active in observed:
                    raise MainTextParityError("Repeated canonical authored verse")
                observed[active] = []
            # USFX v is a *starting milestone*, and its optional text is
            # the GENERATED/PRINTED verse marker, not a Scripture word.
            # USFX c is likewise a chapter marker, not main verse prose.
            if kind not in {"v", "c"}:
                append(node.text)
            for child in node:
                visit(child, depth + 1)
                append(child.tail)

        visit(book)
    if visited_order != metadata["original_books"]:
        raise MainTextParityError("Authored book order changed during scan")
    mapped_keys = {
        f"{pairs[code]}.{chapter}.{verse}" for code, chapter, verse in authored_keys
        if code in pairs
    }
    if set(observed) != mapped_keys:
        raise MainTextParityError("Authored source text and verse inventories disagree")
    strings = {ref: "".join(chunks) for ref, chunks in observed.items()}
    if any(len(value.encode("utf-8")) > MAX_VERSE for value in strings.values()):
        raise MainTextParityError("Implausibly long authored verse")
    return strings, {
        "source_original_book_count": len(visited),
        "mapped_numbered_source_keys": len(strings),
        "unmapped_authored_book_count": len(visited - set(pairs)),
        "unmapped_numbered_source_keys": sum(
            1 for code, _ch, _v in authored_keys if code not in pairs),
        "excluded_source_heading_or_note_element_counts": dict(sorted(skipped.items())),
        "source_explicit_usfm_to_native_book_crosswalk_only": True,
    }


def native_raw_main_text(raw: bytes, *, markup_census: NativeMarkupCensus | None = None,
                         reference: str | None = None) -> tuple[str, dict]:
    """Strictly parse a complete raw XML fragment; never 'repair' bad tags.

    Note text and headings are not Scripture. XML entity decoding is done
    by a strict parser; exact emitted bytes are tracked separately by the
    independent native raw corpus hash.
    """
    if len(raw) > MAX_VERSE:
        raise MainTextParityError("Oversized raw native verse")
    if b"<!DOCTYPE" in raw.upper() or b"<?xml" in raw.lower():
        raise MainTextParityError("Unexpected declarations inside native XML fragment")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(b"<private_root>" + raw + b"</private_root>", parser)
    except etree.XMLSyntaxError as exc:
        raise MainTextParityError("Stock SWORD raw entry is not a self-contained XML fragment") from exc
    if any(isinstance(x, etree._Entity) for x in root.iter()):
        raise MainTextParityError("Unresolved native XML entity")
    if markup_census is not None:
        if reference is None:
            raise MainTextParityError("Native markup census needs an actual reader reference")
        markup_census.observe(reference, root)
    chars = []
    excluded = Counter()

    def walk(node):
        if isinstance(node.tag, str):
            kind = etree.QName(node).localname
            if kind in NATIVE_SKIP:
                excluded[kind] += 1
                return
            if node.text:
                chars.append(node.text)
            for child in node:
                walk(child)
                if child.tail:
                    chars.append(child.tail)

    walk(root)
    return "".join(chars), dict(excluded)


def _tolerant_fragment_lexical_diagnostic(raw: bytes, authored: str) -> dict:
    """Secondary lexical *diagnostic* for non-self-contained native markup.

    HTMLParser can tokenize a malformed/unbalanced raw fragment; this is
    never treated as proof of XML structure, notes or main-text fidelity.
    Original authored and native words stay inside private memory.
    """
    from sword_missing_verse_witness import (
        MissingVerseWitnessError, _tokens, native_main_tokens,
    )
    try:
        native_words = native_main_tokens(raw)
    except (MissingVerseWitnessError, UnicodeError, ValueError):
        return {"status": "tolerant_token_reader_unavailable",
                "lexical_fidelity_verified": False}
    authored_words = _tokens(authored)
    return {
        "status": ("tolerant_word_sequence_matches_diagnostic_only"
                   if native_words == authored_words
                   else "tolerant_word_sequence_differs_diagnostic_only"),
        "authored_word_count": len(authored_words),
        "native_word_count": len(native_words),
        "lexical_fidelity_verified": False,
        "native_xml_structure_fidelity_verified": False,
    }


def _fold_whitespace(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def _classify(source: str, native: str) -> str:
    if source == native:
        return "exact_semantic_characters"
    if unicodedata.normalize("NFC", source) == unicodedata.normalize("NFC", native):
        return "unicode_normalization_only"
    if _fold_whitespace(source) == _fold_whitespace(native):
        return "whitespace_only"
    a, b = WORD.findall(source), WORD.findall(native)
    if a == b:
        return "word_sequence_same_punctuation_or_spacing_differs"
    if [t.casefold() for t in a] == [t.casefold() for t in b]:
        return "case_or_punctuation_differs_same_folded_words"
    return "word_sequence_differs"


# Preserve a few examples of EACH classification, prioritizing the
# material word/markup findings over ubiquitous whitespace differences.
# We cannot retain 25 first-verses-only whitespace rows and hide all real
# substantive mismatches.
SAMPLE_ORDER = (
    "word_sequence_differs",
    "native_raw_fragment_requires_review",
    "case_or_punctuation_differs_same_folded_words",
    "word_sequence_same_punctuation_or_spacing_differs",
    "whitespace_only",
    "unicode_normalization_only",
)


def _add_sample(buckets: dict[str, list[dict]], category: str, row: dict) -> None:
    rows = buckets.setdefault(category, [])
    if len(rows) < 4:
        rows.append(row)


def _prioritized_samples(buckets: dict[str, list[dict]], max_rows: int) -> list[dict]:
    if not 0 < max_rows <= MAX_MISMATCHES:
        raise MainTextParityError("Unsafe sample count")
    return [row for category in SAMPLE_ORDER
            for row in buckets.get(category, [])][:max_rows]


def compare_private_main_text(
    source: dict[str, str], mapped_source: dict, native_records: list[tuple[str, bytes]],
    *, max_examples: int = MAX_MISMATCHES,
) -> dict:
    """Utility for synthetic tests and final audited raw reader callback."""
    if not 0 < max_examples <= MAX_MISMATCHES:
        raise MainTextParityError("Unsafe mismatch sample bound")
    counts = Counter()
    samples = {}
    seen = set()
    native_keys = set()
    skipped_native = Counter()
    for reference, raw in native_records:
        if reference in seen:
            raise MainTextParityError("Duplicate actual native reference")
        seen.add(reference)
        native_keys.add(reference)
        if reference not in source:
            counts["native_verse_without_same_indexed_source_key"] += 1
            continue
        counts["matching_indexed_keys_checked"] += 1
        try:
            native, excluded = native_raw_main_text(raw)
        except MainTextParityError:
            counts["native_raw_not_parseable_as_self_contained_xml"] += 1
            _add_sample(samples, "native_raw_fragment_requires_review",
                        {"native_ref": reference,
                         "classification": "native_raw_fragment_requires_review"})
            continue
        skipped_native.update(excluded)
        src = source[reference]
        classification = _classify(src, native)
        counts[classification] += 1
        if classification != "exact_semantic_characters":
            _add_sample(samples, classification, {
                "native_ref": reference,
                "classification": classification,
                "source_character_count": len(src),
                "compiled_character_count": len(native),
                "source_word_count": len(WORD.findall(src)),
                "compiled_word_count": len(WORD.findall(native)),
                "source_utf8_sha256": sha256(src.encode("utf-8")).hexdigest(),
                "compiled_utf8_sha256": sha256(native.encode("utf-8")).hexdigest(),
            })
    missing = sorted(set(source) - native_keys)
    counts["source_verses_without_native_indexed_entry"] = len(missing)
    full_exact = bool(source and not missing
                      and counts["matching_indexed_keys_checked"] == len(source)
                      and counts["exact_semantic_characters"] == len(source)
                      and counts["native_verse_without_same_indexed_source_key"] == 0)
    return {
        "status": ("all_mapped_numbered_maintext_characters_match_index_only"
                   if full_exact else "blocked_full_mapped_numbered_maintext_parity"),
        "source_mapped_numbered_verse_count": len(source),
        "native_mapped_numbered_verse_count": len(native_keys),
        "classifications": dict(sorted(counts.items())),
        "first_differences_no_scripture": _prioritized_samples(samples, max_examples),
        "first_source_only_refs": missing[:max_examples],
        "native_excluded_note_or_title_elements": dict(sorted(skipped_native.items())),
        "excluded_authored_note_and_title_body_parity_verified": False,
        "exact_mapped_numbered_maintext_semantic_characters_verified": full_exact,
        "exact_original_source_bytes_equal_compiled_bytes_verified": False,
        "unmapped_source_books_verified": False,
        "intro_and_verse_zero_verified": False,
        "notes_strong_references_poetry_layout_verified": False,
        "publisher_exact_edition_revision_identity_verified": False,
        "approved_for_publication": False,
    }


def run_real_usfx_sword_text_probe(
    source_usfx_zip: Path, original_sword_zip: Path, crosswalk: Path,
    native_index_binary: Path, native_raw_binary: Path,
    native_entry_binary: Path | None = None
) -> dict:
    raw, publisher = read_source_xml(source_usfx_zip, source_format="usfx")
    mapping = read_crosswalk(crosswalk)
    source_text, scope = authored_usfx_main_text(raw, mapping)
    try:
        source_boundaries, source_boundary_counts = original_usfx_body_boundaries(
            raw, mapping, source_text)
        source_boundary_blocker = None
    except BoundaryAuditError:
        # A source that cannot be independently anchored is not equivalent
        # to an empty source with matching layout. Keep its other audits.
        source_boundaries, source_boundary_counts = None, None
        source_boundary_blocker = "authorial_source_boundary_scope_unverified"
    source_layout = source_usfx_layout_start_anchors(raw, mapping)
    try:
        source_body_openings, source_body_opening_counts = original_body_opening_sequences(raw, mapping)
        source_body_order_block = None
    except OrderedStructureError:
        # Some original research sources contain real numbering/book scope
        # discrepancies. Explicitly BLOCK this narrow source-native screen,
        # without aborting other full-source diagnostics or treating the
        # unverified sequence as an empty successful one. No raw XML/error
        # message may escape into a public GitHub artifact.
        source_body_openings, source_body_opening_counts = None, None
        source_body_order_block = {
            "schema_version":1,
            "status":"blocked_original_authorial_source_scope_or_structure",
            "reason_category":"original_source_cannot_be_unambiguously_mapped_for_order",
            "source_native_body_opening_order_verified":False,
            "source_native_exact_word_positions_or_boundary_spans_verified":False,
            "no_scripture_or_native_milestone_identifiers_in_report":True,
            "originals_rewritten_or_published":False,
        }
    private_prefaces, checked_prefaces = private_original_preface_text(raw, mapping)
    source_note_attributes = {}
    source_notes, source_note_scope = collect_usfx_numbered_notes(
        raw, mapping, attributes_out=source_note_attributes)
    if not set(source_notes).issubset(source_text):
        raise MainTextParityError("Source note inventory includes unknown numbered verses")
    note_audit = NoteAudit(source_notes, source_attributes=source_note_attributes)
    with tempfile.TemporaryDirectory(prefix="private-maintext-") as root:
        module = Path(root) / "original"
        conf = _safe_single_module(original_sword_zip, module)
        before = module_payload_digest(module)
        # Read actual stock-SWORD raw entries into this callback only.
        # No Scripture content is returned, printed or written to disk.
        native_keys = set()
        counts = Counter()
        samples = {}
        material = []
        privately_captured_mismatch_text = {}
        skipped_native = Counter()
        whitespace_patterns = MainTextWhitespacePatterns()
        native_markup = NativeMarkupCensus()
        native_pairs = NativeMilestonePairAudit()
        native_book_intro = NativeBookIntroScreen()
        native_boundaries = NativeBodyBoundaries() if source_boundaries is not None else None
        native_boundary_error = None

        def on_entry(kind, ref, bytes_):
            nonlocal native_boundary_error
            native_pairs.observe(kind, ref, bytes_)
            if native_boundaries is not None and native_boundary_error is None:
                try:
                    native_boundaries.observe(kind, ref, bytes_)
                except BoundaryAuditError:
                    # Never publish a third-party XML exception or silently
                    # infer successful structural correspondence.
                    native_boundary_error = "native_boundary_scope_unverified"
            native_book_intro.observe(kind, ref, bytes_)
            if kind == "I":
                native_markup.observe_intro(ref, bytes_)
                return
            if kind != "K":
                return
            if ref in native_keys:
                raise MainTextParityError("Duplicate native verse during compiled scan")
            native_keys.add(ref)
            note_audit.inspect(ref, bytes_)
            if ref not in source_text:
                counts["native_verse_without_same_indexed_source_key"] += 1
                return
            counts["matching_indexed_keys_checked"] += 1
            try:
                actual, excluded = native_raw_main_text(
                    bytes_, markup_census=native_markup, reference=ref)
            except MainTextParityError:
                counts["native_raw_not_parseable_as_self_contained_xml"] += 1
                diagnostic = _tolerant_fragment_lexical_diagnostic(
                    bytes_, source_text[ref])
                if len(material) < 60:
                    material.append({
                        "native_ref": ref,
                        "classification": "native_raw_fragment_requires_review",
                        "secondary_tolerant_lexical_diagnostic": diagnostic,
                    })
                _add_sample(samples, "native_raw_fragment_requires_review",
                            {"native_ref": ref,
                             "classification": "native_raw_fragment_requires_review"})
                return
            skipped_native.update(excluded)
            authored = source_text[ref]
            category = _classify(authored, actual)
            counts[category] += 1
            if category == "whitespace_only":
                whitespace_patterns.observe(ref, authored, actual)
            # Keep bounded unmatched *actual* Bible prose in private memory,
            # never in JSON or CI. A later scoped checker can test whether
            # missing numbered source verses were appended to this slot.
            if (category == "word_sequence_differs"
                    and len(privately_captured_mismatch_text) < 60):
                privately_captured_mismatch_text[ref] = actual
            if (category in {
                    "word_sequence_differs",
                    "case_or_punctuation_differs_same_folded_words",
                    "word_sequence_same_punctuation_or_spacing_differs",
                    } and len(material) < 60):
                material.append({
                    "native_ref": ref,
                    "classification": category,
                    "source_word_count": len(WORD.findall(authored)),
                    "native_word_count": len(WORD.findall(actual)),
                })
            if category != "exact_semantic_characters":
                _add_sample(samples, category, {
                    "native_ref": ref, "classification": category,
                    "source_character_count": len(authored),
                    "compiled_character_count": len(actual),
                    "source_word_count": len(WORD.findall(authored)),
                    "compiled_word_count": len(WORD.findall(actual)),
                    "source_utf8_sha256": sha256(authored.encode()).hexdigest(),
                    "compiled_utf8_sha256": sha256(actual.encode()).hexdigest(),
                })

        corpus = inspect_native_raw_corpus(
            module, conf["module_id"], native_raw_binary, native_index_binary,
            on_entry=on_entry, native_entry_binary=native_entry_binary)
        if before != module_payload_digest(module) or before != corpus["module_payload_sha256"]:
            raise MainTextParityError("Native module mutated during private content scan")
        # Read original source ZIP again to reject a source replacement mid-audit.
        if sha256(source_usfx_zip.read_bytes()).hexdigest() != publisher["archive_sha256"]:
            raise MainTextParityError("Original publisher archive changed during audit")
        missing = sorted(set(source_text) - native_keys)
        counts["source_verses_without_native_indexed_entry"] = len(missing)
        absorbed_group_witness = inspect_absorbed_source_verse_groups(
            source_text, native_keys, privately_captured_mismatch_text)
        exact = bool(source_text and len(native_keys) == len(source_text)
                     and not missing and counts["exact_semantic_characters"] == len(source_text)
                     and not counts["native_verse_without_same_indexed_source_key"])
        if source_boundary_blocker is not None:
            body_boundary = {
                "schema_version":1, "status":source_boundary_blocker,
                "all_mapped_book_p_q_start_end_word_ordinals_match":False,
                "no_source_text_note_content_or_native_ids_exposed":True,
            }
        elif native_boundary_error is not None:
            body_boundary = {
                "schema_version":1, "status":native_boundary_error,
                "all_mapped_book_p_q_start_end_word_ordinals_match":False,
                "no_source_text_note_content_or_native_ids_exposed":True,
            }
        else:
            try:
                native_boundary_data, native_boundary_counts = native_boundaries.finish()
                body_boundary = compare_body_boundary_word_positions(
                    source_boundaries, native_boundary_data,
                    source_boundary_counts, native_boundary_counts)
            except BoundaryAuditError:
                body_boundary = {
                    "schema_version":1,
                    "status":"source_native_boundary_comparison_unverified",
                    "all_mapped_book_p_q_start_end_word_ordinals_match":False,
                    "no_source_text_note_content_or_native_ids_exposed":True,
                }
        # A word-position-equal structure can be serialized in a prior
        # USFX verse but a following native SWORD verse/intro. Classify the
        # *original* authored verse-boundary geometry, rather than treating
        # all differing record names as 9,083 arbitrary editorial errors.
        # The private source/native scanners are the only inputs. Never
        # accept a record-shift interpretation if actual word positions
        # failed the independently run start+end comparison.
        if body_boundary.get("all_mapped_book_p_q_start_end_word_ordinals_match") is True:
            try:
                body_record_scope = compare_body_record_scopes(
                    source_boundaries, native_boundary_data, source_text)
            except ScopeTriageError:
                body_record_scope = {
                    "schema_version":1,
                    "status":"blocked_original_verse_boundaries_or_native_record_scope",
                    "source_to_native_record_scope_equivalence_verified":False,
                    "no_scripture_or_native_identifier_values_in_report":True,
                }
        else:
            body_record_scope = {
                "schema_version":1,
                "status":"blocked_prerequisite_source_native_p_q_word_boundaries",
                "source_to_native_record_scope_equivalence_verified":False,
                "no_scripture_or_native_identifier_values_in_report":True,
            }
        if body_boundary.get("all_mapped_book_p_q_start_end_word_ordinals_match") is True:
            try:
                body_nonspace = compare_punctuation_sensitive_boundaries(
                    source_boundaries, native_boundary_data)
            except NonspaceBoundaryError:
                body_nonspace = {
                    "schema_version":1,
                    "status":"blocked_original_native_punctuation_boundary_scope",
                    "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match":False,
                    "no_original_text_notes_native_markup_or_sids_in_receipt":True,
                }
        else:
            body_nonspace = {
                "schema_version":1,
                "status":"blocked_prerequisite_p_q_lexical_word_boundaries",
                "all_p_q_source_native_nonwhitespace_codepoint_boundaries_match":False,
                "no_original_text_notes_native_markup_or_sids_in_receipt":True,
            }
        comparison = {
            "status": ("all_mapped_numbered_maintext_characters_match_index_only"
                       if exact else "blocked_full_mapped_numbered_maintext_parity"),
            "source_mapped_numbered_verse_count": len(source_text),
            "native_numbered_verse_count": len(native_keys),
            "classifications": dict(sorted(counts.items())),
            "material_difference_metadata_no_scripture": material,
            "material_differences_metadata_truncated": (
                counts["word_sequence_differs"] +
                counts["case_or_punctuation_differs_same_folded_words"] +
                counts["word_sequence_same_punctuation_or_spacing_differs"] +
                counts["native_raw_not_parseable_as_self_contained_xml"]
            ) > len(material),
            "first_differences_no_scripture":
                _prioritized_samples(samples, MAX_MISMATCHES),
            "first_source_only_refs": missing[:MAX_MISMATCHES],
            "native_excluded_note_or_title_elements": dict(sorted(skipped_native.items())),
            "mapped_numbered_maintext_exact_semantic_characters_verified": exact,
            "maintext_whitespace_patterns": whitespace_patterns.finish(),
            "native_raw_structural_markup_inventory": native_markup.finish(),
            "native_crossentry_milestone_pair_audit": native_pairs.finish(),
            "source_native_body_boundary_word_position_screen": body_boundary,
            "source_native_body_record_scope_triage": body_record_scope,
            "source_native_nonwhitespace_codepoint_boundary_screen": body_nonspace,
            "source_native_ordered_body_kind_screen": (
                source_body_order_block if source_body_order_block is not None
                else compare_ordered_body_openings(
                    source_body_openings,
                    native_pairs.private_ordered_body_openings(),
                    source_body_opening_counts)),
            "source_prefatory_p_structure_classification": checked_prefaces,
            "source_native_book_intro_preface_screen":
                native_book_intro.finish(private_prefaces, checked_prefaces),
            "source_native_typed_paragraph_book_comparison":
                compare_authored_native_paragraphs(
                    raw, mapping, native_pairs.native_x_p_pairs_by_book()),
            "source_native_layout_start_anchor_screen":
                compare_start_anchors(source_layout, native_markup),
        }
        return {
            "schema_version": 1,
            "status": "real_usfx_to_stock_sword_maintext_diagnostic_not_publication",
            "publisher_original_usfx_zip_sha256": publisher["archive_sha256"],
            "publisher_original_usfx_xml_sha256": publisher["sha256"],
            "publisher_compiled_sword_zip_sha256": sha256(original_sword_zip.read_bytes()).hexdigest(),
            "book_crosswalk_sha256": sha256(crosswalk.read_bytes()).hexdigest(),
            "module_id": conf["module_id"],
            "module_native_driver": corpus["module_driver"],
            "module_versification": corpus["module_native_versification"],
            "stock_sword_version": corpus["native_engine_version"],
            "module_payload_sha256": before,
            "independent_whole_native_raw_manifest_sha256":
                corpus["all_native_raw_entries_ordered_sha256"],
            "native_inspector_sha256": corpus["independent_native_key_inspector_sha256"],
            "native_raw_inspector_sha256": corpus["native_raw_inspector_sha256"],
            "independent_native_whole_corpus_scan_completed":
                corpus["exact_all_occupied_native_keys_matched_independent_index"],
            "independent_native_exact_key_raw_spotcheck_verified":
                corpus["independent_native_exact_key_raw_spotcheck_verified"],
            "source_book_scope": scope,
            "original_source_note_scope": source_note_scope,
            "private_numbered_source_native_note_body_diagnostic": note_audit.finish(),
            "mapped_numbered_text_comparison": comparison,
            "source_only_verse_grouped_native_maintext_witness":
                absorbed_group_witness,
            "source_usfx_to_osis_conversion_verified": False,
            "exact_publisher_revision_identity_verified": False,
            "full_original_source_including_extra_books_and_intros_verified": False,
            "note_callers_bodies_anchors_references_strong_and_layout_verified": False,
            "actual_graphical_reader_rendering_verified": False,
            "publication_rights_and_human_editorial_approval": False,
            "published": False,
        }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-usfx-zip", type=Path, required=True)
    p.add_argument("--original-sword-zip", type=Path, required=True)
    p.add_argument("--crosswalk", type=Path, required=True)
    p.add_argument("--native-index-inspector", type=Path, required=True)
    p.add_argument("--native-raw-inspector", type=Path, required=True)
    p.add_argument("--native-entry-inspector", type=Path)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if (args.report.exists() or args.report.is_symlink()
            or not args.report.parent.is_dir()
            or args.report.parent.is_symlink()
            or args.report.resolve().is_relative_to(Path.cwd() / "modules")):
        p.error("Output report must be new, outside the resource module tree")
    try:
        report = run_real_usfx_sword_text_probe(
            args.source_usfx_zip, args.original_sword_zip, args.crosswalk,
            args.native_index_inspector, args.native_raw_inspector,
            native_entry_binary=args.native_entry_inspector)
        write_new_metadata_report(args.report, args.original_sword_zip, report)
    except (ValueError, OSError, UnicodeError) as exc:
        p.error(str(exc))
    rows = report["mapped_numbered_text_comparison"]
    print("Compared native-indexed source verse bodies:",
          rows["classifications"].get("matching_indexed_keys_checked", 0))
    print("Exact semantic characters:",
          rows["classifications"].get("exact_semantic_characters", 0))
    print("Overall authorial edition, annotations, structure, rights and release NOT approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
