"""Read-only gate for documented MHCC Modern original-link correction proposals.

This reviewer checks attested original native link digests, explicit owner
proposal dispositions, and source-pinned modern section text. It never
modifies source XML, corrected manuscripts or compiled SWORD modules.
Its current MHCC Modern source identity is deliberately preserved as-is:
this extraction does not generalize editorial policies or authorize release.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from research.commentary.commentary_original_link_identity import (
    _SHA, _REF, WholeCanonOriginalLinkIdentityReceipt,
)


def validate_proposed_link_dispositions(*, manifest: dict, native: dict,
                                        identities: dict, repository_root: Path) -> dict:
    """Audit a bounded correction plan against authenticated native link hashes.

    The identity ledger comes from the *real* complete native SWORD reader.
    Authorial prose, displayed source labels, and raw original XML stay absent.
    Witness/editorial assertions are NOT transformed into release approval.
    """
    from commentary_modern_draft_guard import _claimed_verse_keys_in_heading

    status = "SECONDARY_WITNESS_LINK_CORRECTION_PROPOSALS_NOT_EDITORIAL_RELEASE_APPROVAL"
    if (manifest.get("status") != status
            or native.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL"
            or identities.get("status") != WholeCanonOriginalLinkIdentityReceipt.STATUS):
        raise ValueError("Unapproved or incompatible original link provenance")
    pin = manifest.get("source_native_corpus_sha256")
    if (not isinstance(pin, str) or not _SHA.fullmatch(pin)
            or pin != native.get("original_compiled_corpus_sha256")
            or pin != identities.get("whole_native_source_sha256")
            or manifest.get("source_module") != "MHCC 0.1.1"):
        raise ValueError("Original full native source identity is not the attested edition")
    for flag in ("explicit_owner_publication_authorization",
                 "independent_original_semantic_signoff",
                 "modern_sword_compiled_or_published"):
        if manifest.get(flag) is not False:
            raise ValueError("Unapproved modern derivative cannot claim release signoff")
    if (native.get("source_prose_or_original_markup_exported") is not False
            or identities.get("original_link_destinations_only_sha256_not_exported") is not True
            or identities.get("original_visible_link_text_only_sha256_not_exported") is not True
            or identities.get("original_source_prose_or_XML_exported") is not False
            or identities.get("original_numbered_K_keys_verified") != 28742
            or identities.get("original_unique_K_bodies_verified") != 4047
            or identities.get("original_reference_elements_verified") != 1204):
        raise ValueError("Missing or incomplete real source-native original link receipt")
    rows = identities.get("source_link_groups")
    if not isinstance(rows, list) or len(rows) != identities.get("original_link_bearing_K_bodies"):
        raise ValueError("Incomplete original reference-group identity inventory")
    index = {row["first_key"]: row for row in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate original linked K body")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 50:
        raise ValueError("Missing or unbounded source-correction cases")
    checked = []
    visited_keys = set()
    corrections = 0
    omitted = retargeted = added = 0
    for case in cases:
        chapter = case.get("chapter")
        first = case.get("source_first_key")
        if (not isinstance(chapter, str) or not isinstance(first, str)
                or not first.startswith(chapter + ".")
                or first in visited_keys):
            raise ValueError("Duplicate or wrong original source correction scope")
        visited_keys.add(first)
        original_chapter = native["chapters"].get(chapter, {})
        originals = original_chapter.get("original_units", [])
        group = next((r for r in originals if r["first_key"] == first), None)
        attested = index.get(first)
        if (group is None or attested is None
                or group["source_unit_sha256"] != case.get("source_unit_sha256")
                or attested["source_raw_sha256"] != case.get("source_unit_sha256")):
            raise ValueError("Source correction is not anchored in the authentic raw body")
        links = attested["original_osisRef_sha256_in_document_order"]
        labels = attested["original_visible_link_label_sha256_in_document_order"]
        if (not isinstance(links, list) or not isinstance(labels, list)
                or len(links) != len(labels)
                or len(links) != attested["reference_count"]):
            raise ValueError("Source link ordinal evidence incomplete")
        path = case.get("modern_path")
        if (not isinstance(path, str)
                or not re.fullmatch(r"work/mhcc-modern/production/accepted/[a-z0-9-]+\.md", path)):
            raise ValueError("Modern manuscript is outside the approved draft root")
        modern = (repository_root / path).read_text(encoding="utf-8")
        if not modern.startswith("---\n") or "\n---\n" not in modern:
            raise ValueError("Modern manuscript has invalid source front matter")
        header, body = modern[4:].split("\n---\n", 1)
        if (f'chapter_osis: "{chapter}"' not in header.splitlines()
                or f'source_native_corpus_sha256: "{pin}"' not in header.splitlines()
                or 'publication_status: "NOT RELEASED' not in header):
            raise ValueError("Modern manuscript source pin, chapter or status changed")
        body = body.split("\n---\n", 1)[0]
        sections = list(re.finditer(r"(?m)^## (.+)\s*$", body))
        title = case.get("modern_section_heading")
        found = [i for i, h in enumerate(sections) if h.group(1).strip() == title]
        if len(found) != 1:
            raise ValueError("Modern authored section heading not uniquely identified")
        offset = found[0]
        section_text = body[sections[offset].end():
                            sections[offset + 1].start()
                            if offset + 1 < len(sections) else len(body)]
        source_verses = [int(k.rsplit(".", 1)[1]) for k in group["keys"]]
        if _claimed_verse_keys_in_heading(title) != source_verses:
            raise ValueError("Modern authored range differs from original source K keys")
        witness = case.get("witness_url")
        if (not isinstance(witness, str) or not witness.startswith("https://")
                or len(witness) > 512):
            raise ValueError("No documented independent published witness")
        edits = case.get("corrections")
        if not isinstance(edits, list) or not edits:
            raise ValueError("Each case needs explicit original-reference dispositions")
        seen_ordinals = set()
        for edit in edits:
            ordinal = edit.get("source_link_ordinal")
            source_target = edit.get("original_target")
            source_label = edit.get("original_label")
            action = edit.get("disposition")
            context = edit.get("modern_context_anchor")
            if (type(ordinal) is not int or ordinal < 1 or ordinal > len(links)
                    or ordinal in seen_ordinals
                    or not isinstance(source_target, str)
                    or not isinstance(source_label, str)
                    or not isinstance(context, str) or not context
                    or context not in section_text):
                raise ValueError("Unverified or duplicated original reference disposition")
            seen_ordinals.add(ordinal)
            if (hashlib.sha256(source_target.encode("utf-8")).hexdigest()
                    != links[ordinal - 1]
                    or hashlib.sha256(source_label.encode("utf-8")).hexdigest()
                    != labels[ordinal - 1]):
                raise ValueError("Original link target/label fingerprint mismatch")
            if action == "OMIT_SPURIOUS_ENUMERATOR_LINK":
                if not re.fullmatch(r"[1-9]", source_label):
                    raise ValueError("Spurious enumerator is not a single digit")
                if "corrected_target" in edit:
                    raise ValueError("Spurious link cannot silently acquire a target")
                omitted += 1
            elif action == "RETARGET_VERIFIED_CONTINUATION_REFERENCE":
                corrected = edit.get("corrected_target")
                if (not isinstance(corrected, str) or not _REF.fullmatch(corrected)
                        or corrected == source_target):
                    raise ValueError("Invalid witnessed target correction")
                if not re.fullmatch(r"\d{1,3}", source_label):
                    raise ValueError("Continuation source label is not a verse number")
                retargeted += 1
            else:
                raise ValueError("Unapproved source link editorial operation")
            corrections += 1
        additions = case.get("modern_witness_links", [])
        if not isinstance(additions, list):
            raise ValueError("Malformed missing original hyperlink review")
        observed_additions = set()
        for proposed in additions:
            target = proposed.get("target")
            marker = proposed.get("modern_text_marker")
            if (proposed.get("disposition") !=
                    "ADD_SECONDARY_WITNESS_AUTHORED_REFERENCE_NOT_IN_NATIVE_LINKS"
                    or not isinstance(target, str) or not _REF.fullmatch(target)
                    or target in observed_additions
                    or hashlib.sha256(target.encode("utf-8")).hexdigest() in links
                    or not isinstance(marker, str) or not marker
                    or marker not in section_text):
                raise ValueError("Proposed witness link is not tied to original and modern scope")
            observed_additions.add(target)
            added += 1
        checked.append({
            "chapter": chapter, "source_first_key": first,
            "authenticated_original_link_elements": len(links),
            "proposed_omissions": sum(e["disposition"] ==
                  "OMIT_SPURIOUS_ENUMERATOR_LINK" for e in edits),
            "proposed_retargets": sum(e["disposition"] ==
                  "RETARGET_VERIFIED_CONTINUATION_REFERENCE" for e in edits),
            "proposed_witness_additions": len(additions),
            "original_source_raw_sha256_confirmed": True,
            "modern_section_scope_and_marker_presence_confirmed": True,
        })
    if not omitted and not retargeted and not added:
        raise ValueError("Empty correction proposal")
    return {
        "status": "PINNED_SOURCE_AND_MODERN_CORRECTION_CANDIDATES_CHECKED_NOT_RELEASED",
        "whole_original_native_corpus_sha256": pin,
        "reviewed_source_link_groups": len(checked),
        "reviewed_original_hyperlink_elements_in_groups": sum(
            row["authenticated_original_link_elements"] for row in checked),
        "source_links_proposed_to_omit": omitted,
        "source_links_proposed_to_retarget": retargeted,
        "secondary_witness_links_proposed_to_add": added,
        "original_link_proposal_actions_reviewed": corrections,
        "source_link_target_and_label_hashes_checked_in_original_order": True,
        "modern_section_scope_and_marker_presence_checked": True,
        "real_native_source_changes": False,
        "derived_SWORD_link_placements_or_native_readbacks_tested": False,
        "editorial_translation_approved": False,
        "release_authorized": False,
        "cases": checked,
    }
