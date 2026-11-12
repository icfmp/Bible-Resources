#!/usr/bin/env python3
"""Verify that omitted-verse editorial notes survive without dead navigation.

Generic, plan-driven, private source/native audit. Never create missing verses,
rewrite original text, or declare GUI behavior from XML alone.
"""
from __future__ import annotations

from collections import Counter
from lxml import etree

from repair_osis_note_links import _source_note_nodes
from source_osis_inventory import OSIS, _source_tree, source_inventory
from publisher_osis_sword_candidate import _native_notes

MAX_CASES = 100


class OmittedNoteAuditError(ValueError):
    """Unverified editorial note or potentially misleading native target."""


def _reference_children(note):
    return [n for n in note.iterdescendants()
            if isinstance(n.tag, str) and etree.QName(n).localname == "reference"]


def _one_host_note(notes, edit):
    found = notes.get(edit["note_host"], ())
    idx = edit["note_index"]
    if type(idx) is not int or idx < 1 or idx > len(found):
        raise OmittedNoteAuditError("Original note host or ordinal unverified")
    return found[idx - 1]


def _text(node):
    return "".join(node.itertext())


def source_cases(original: bytes, corrected: bytes, plan: dict):
    """Check corrected XML keeps authorial note words and drops only dead target."""
    actions = [x for x in plan["edits"]
               if x["action"] == "disable_absent_target"]
    if not 1 <= len(actions) <= MAX_CASES:
        raise OmittedNoteAuditError("No bounded original nonaddressable target plan")
    original_root = _source_tree(original)
    corrected_root = _source_tree(corrected)
    original_keys, _ = source_inventory(original)
    corrected_keys, _ = source_inventory(corrected)
    if original_keys != corrected_keys:
        raise OmittedNoteAuditError("Unexpected authored numbered key change")
    indexed = set(original_keys.splitlines())
    orig_notes = _source_note_nodes(original_root)
    fixed_notes = _source_note_nodes(corrected_root)
    results = {}
    for edit in actions:
        host, old_target = edit["note_host"], edit["old_target"]
        if not isinstance(old_target, str) or old_target in indexed or host not in indexed:
            raise OmittedNoteAuditError("Target is not a genuinely absent authorial verse")
        key = (host, edit["note_index"])
        if key in results or edit.get("new_target") is not None:
            raise OmittedNoteAuditError("Duplicated or unreviewed missing-target operation")
        old = _one_host_note(orig_notes, edit)
        fixed = _one_host_note(fixed_notes, edit)
        prior = _reference_children(old)
        after = _reference_children(fixed)
        if len(prior) != len(after) or len(prior) < 1:
            raise OmittedNoteAuditError("Original reference markup changed count")
        matches = [i for i,n in enumerate(prior)
                   if n.get("osisRef") == old_target]
        if len(matches) != 1:
            raise OmittedNoteAuditError("Missing or ambiguous original broken target")
        selected = after[matches[0]]
        if (selected.get("osisRef") is not None
                or any("href" in k.lower() or "target" in k.lower()
                       for k in selected.attrib)):
            raise OmittedNoteAuditError("Dead destination still active in source")
        if (not _text(selected).strip()
                or _text(selected) != _text(prior[matches[0]])
                or _text(old) != _text(fixed)
                or old.get("n") != fixed.get("n")
                or old.get("type") != fixed.get("type")):
            raise OmittedNoteAuditError("Authored explanatory text or note caller changed")
        if (len(_reference_children(old)) != len(_reference_children(fixed))
                or sum(1 for n in after if n.get("osisRef") == old_target)):
            raise OmittedNoteAuditError("Unreviewed link markup difference")
        results[key] = {
            "host": host,
            "note_index": edit["note_index"],
            "original_absent_verse_target": old_target,
            "source_note_all_characters_equal": True,
            "source_original_reference_display_text_equal": True,
            "source_broken_machine_target_removed": True,
            "displayed_reference_not_erased": True,
        }
    return results


def native_cases(source_results: dict, corrected: bytes, native_raw_by_host: dict):
    """Require native note bodies and inactive target metadata, no GUI claim."""
    notes = _source_note_nodes(_source_tree(corrected))
    if set(native_raw_by_host) != {key[0] for key in source_results}:
        raise OmittedNoteAuditError("Native frame host inventory is incomplete")
    output = []
    for (host, ordinal), source_status in source_results.items():
        raw = native_raw_by_host[host]
        native = _native_notes(raw)
        source_note = notes[host][ordinal-1]
        if len(native) != len(notes[host]) or ordinal > len(native):
            raise OmittedNoteAuditError("Compiled note ordinal not preserved")
        selected = native[ordinal-1]
        if (" ".join(selected["body"].split()) != " ".join(_text(source_note).split())
                or selected["caller"] != source_note.get("n")
                or selected["type"] != source_note.get("type")):
            raise OmittedNoteAuditError("Compiled authorial explanatory note changed")
        if source_status["original_absent_verse_target"] in selected["targets"]:
            raise OmittedNoteAuditError("Compiled note still exposes absent target")
        # Native SWORD may flatten an unlinked <reference> into plain text.
        # The complete note body equality proves its printed words survive.
        output.append({
            "host": host,
            "note_index": ordinal,
            "authored_note_caller_and_display_text_preserved": True,
            "missing_target_not_present_in_compiled_navigation_attributes": True,
            "missing_scripture_verse_was_not_fabricated": True,
            "GUI_dead_link_behavior_verified": False,
        })
    return {
        "status": "source_and_native_omitted_verse_note_metadata_verified",
        "missing_verse_note_count": len(output),
        "cases": output,
        "all_original_note_text_preserved": True,
        "no_omitted_verses_fabricated": True,
        "actual_reader_visual_state_verified": False,
        "editorially_approved": False,
        "published": False,
    }
