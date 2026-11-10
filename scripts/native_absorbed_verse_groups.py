#!/usr/bin/env python3
"""Text-free generic witness for authored verses absorbed into native SWORD slots.

A native VerseKey may have no separate address for authored verses, while
their complete original main-verse text has been appended to the preceding
occupied entry. This is a read-only DIAGNOSTIC, never a license to merge
verses or infer faithful source versification. No Bible prose is returned.
"""
from __future__ import annotations

from hashlib import sha256
import re
import unicodedata

from stable_sword_refs import KEY

WORD = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*", re.UNICODE)
MAX_MISSING = 60
MAX_EVIDENCE = 60


class AbsorbedVerseEvidenceError(ValueError):
    """Ambiguous source/native reference or unsafe private content proof."""


def _ref_parts(ref: str) -> tuple[str, int, int]:
    match = KEY.fullmatch(ref)
    if not match:
        raise AbsorbedVerseEvidenceError("Malformed source/native verse identifier")
    return match.group(1), int(match.group(2)), int(match.group(3))


def _word_sequence(text: str) -> list[str]:
    return [unicodedata.normalize("NFC", x.casefold()) for x in WORD.findall(text)]


def _nfc_space(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def inspect_absorbed_source_verse_groups(
    authored: dict[str, str],
    native_occupied: set[str],
    privately_captured_native_maintext: dict[str, str],
) -> dict:
    """Compare complete grouped authorial verse prose with actual native entry.

    Source mapping and reader keys come from INDEPENDENT evidence. We only
    inspect same-chapter, immediately adjacent authored source verse refs:
    occupied N, then unindexed N+1, N+2, ... before the next occupied entry.
    A non-contiguous or missing capture explicitly blocks that group.
    """
    if not authored or not native_occupied:
        raise AbsorbedVerseEvidenceError("Empty independent source/reader index")
    if len(authored) != len(set(authored)):
        raise AbsorbedVerseEvidenceError("Duplicate source identifiers")
    for ref, value in authored.items():
        _ref_parts(ref)
        if not isinstance(value, str) or len(value.encode("utf-8")) > 2 * 1024 * 1024:
            raise AbsorbedVerseEvidenceError("Invalid authored source verse text")
    for ref in native_occupied | set(privately_captured_native_maintext):
        _ref_parts(ref)
    if not set(privately_captured_native_maintext).issubset(native_occupied):
        raise AbsorbedVerseEvidenceError("Captured native entry is not occupied")
    unexpected_native = native_occupied - set(authored)
    missing_refs = [ref for ref in authored if ref not in native_occupied]
    if len(missing_refs) > MAX_MISSING:
        return {
            "status": "blocked_too_many_source_only_refs_for_bounded_diagnostic",
            "source_only_reference_count": len(missing_refs),
            "source_only_references_still_unindexed": True,
            "whole_original_source_fidelity_verified": False,
            "publication_approved": False,
        }
    # There may be an unindexed intro/standalone authorial verse at the
    # beginning of a chapter. Never borrow the final verse of another chapter.
    groups = {}
    unresolved = []
    last_native: str | None = None
    last_authorial: str | None = None
    for ref in authored:
        book, chapter, verse = _ref_parts(ref)
        if ref in native_occupied:
            last_native = ref
        else:
            if last_native is None:
                unresolved.append({"authored_ref": ref,
                                   "reason": "no_preceding_occupied_native_key"})
            else:
                pb, pc, pv = _ref_parts(last_authorial) if last_authorial else ("", 0, 0)
                nb, nc, _ = _ref_parts(last_native)
                if (book != pb or chapter != pc or verse != pv + 1
                        or nb != book or nc != chapter):
                    unresolved.append({
                        "authored_ref": ref,
                        "reason": "noncontiguous_same_chapter_source_verse_sequence",
                    })
                else:
                    groups.setdefault(last_native, []).append(ref)
        last_authorial = ref

    rows = []
    for predecessor, missing in groups.items():
        preceding_book, preceding_chapter, preceding_verse = _ref_parts(predecessor)
        # The grouped original verse IDs must follow this exact native slot.
        # The set membership is not an independent test of textual position.
        if any(_ref_parts(ref) != (preceding_book, preceding_chapter,
                                 preceding_verse + i + 1)
               for i, ref in enumerate(missing)):
            unresolved.extend({
                "authored_ref": ref,
                "reason": "nonconsecutive_numbered_source_verse",
            } for ref in missing)
            continue
        row = {
            "occupied_native_ref": predecessor,
            "original_source_only_refs": missing,
            "source_only_ref_count": len(missing),
            "source_only_refs_remain_unindexed": True,
            "source_versification_preserved_in_native_reader": False,
            "complete_grouped_original_footnotes_and_anchors_verified": False,
            "complete_grouped_authorial_structure_verified": False,
        }
        compiled = privately_captured_native_maintext.get(predecessor)
        if compiled is None:
            row["status"] = "blocked_no_captured_same_native_entry_maintext"
        else:
            original = "".join(authored[ref] for ref in (predecessor, *missing))
            same_words = _word_sequence(original) == _word_sequence(compiled)
            exact = original == compiled
            nfc = unicodedata.normalize("NFC", original) == unicodedata.normalize(
                "NFC", compiled)
            whitespace = _nfc_space(original) == _nfc_space(compiled)
            row.update({
                "status": ("all_grouped_source_word_tokens_present_in_native_order"
                           if same_words
                           else "blocked_combined_source_word_sequence_differs"),
                "grouped_authored_main_word_count": len(_word_sequence(original)),
                "native_main_word_count": len(_word_sequence(compiled)),
                "complete_grouped_word_sequence_equal_diagnostic_only": same_words,
                "complete_grouped_semantic_characters_exact": exact,
                "complete_grouped_characters_NFC_equal": nfc,
                "complete_grouped_characters_equal_after_whitespace_folding": whitespace,
                "source_grouped_maintext_utf8_sha256":
                    sha256(original.encode("utf-8")).hexdigest(),
                "native_grouped_maintext_utf8_sha256":
                    sha256(compiled.encode("utf-8")).hexdigest(),
            })
        rows.append(row)
    witnessed = sum(len(row["original_source_only_refs"]) for row in rows
                    if row.get("complete_grouped_word_sequence_equal_diagnostic_only"))
    blocked_refs = sum(len(row["original_source_only_refs"]) for row in rows
                       if not row.get("complete_grouped_word_sequence_equal_diagnostic_only"))
    if witnessed + blocked_refs + len(unresolved) != len(missing_refs):
        raise AbsorbedVerseEvidenceError("A source-only reference was lost or double-counted")
    return {
        "schema_version": 1,
        "status": ("all_bounded_source_only_verse_groups_word_preservation_witnessed"
                   if missing_refs and witnessed == len(missing_refs)
                   and not unresolved and not unexpected_native
                   else "blocked_or_incomplete_absorbed_source_verse_group_evidence"),
        "source_only_reference_count": len(missing_refs),
        "source_only_refs_whose_full_grouped_word_sequence_is_present": witnessed,
        "source_only_refs_without_complete_grouped_word_witness":
            blocked_refs + len(unresolved),
        "native_occupied_refs_without_authored_counterpart_count": len(unexpected_native),
        "first_unexpected_native_refs": sorted(unexpected_native)[:MAX_EVIDENCE],
        "grouped_source_verses": rows[:MAX_EVIDENCE],
        "unresolved_source_verse_refs": unresolved[:MAX_EVIDENCE],
        "source_only_references_still_unindexed": bool(missing_refs),
        "publisher_original_usfx_to_osis_conversion_verified": False,
        "source_versification_preserved_in_native_reader": False,
        "whole_original_source_fidelity_verified": False,
        "notes_references_lexical_structure_verified": False,
        "same_editorial_revision_verified": False,
        "publication_approved": False,
    }
