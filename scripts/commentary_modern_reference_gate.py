#!/usr/bin/env python3
"""Compare original SWORD commentary links with draft markers without source export.

This reads exact original native XML *privately* through the project's existing
complete real-SWORD stream reader, fails closed on the pinned corpus SHA, and
reports only predeclared link identity hashes/booleans. It never infers links
from verse positions or changes an existing authorial source reference.
It is NOT a semantic or final OSIS source-link preservation approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

from sword_native_raw_corpus_inventory import parse_native_raw_corpus

_SHA = re.compile(r"^[a-f0-9]{64}$")
_REF = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]{0,2}\.[1-9][0-9]{0,2}$")


def canonical_only_for_comparison(target: str) -> str:
    """Validate the comparison spelling; do not rewrite source XML."""
    if not isinstance(target, str) or not target:
        raise ValueError("Original osisRef is missing or invalid")
    if target.startswith("Bible:"):
        target = target[6:]
    if not _REF.fullmatch(target):
        raise ValueError("Unrecognized original reference syntax; manual review needed")
    return target


def _source_reference_literals(raw: bytes) -> list[str]:
    """Return exact literal original link targets IN MEMORY ONLY."""
    try:
        node = ET.fromstring(b"<source>" + raw + b"</source>")
    except ET.ParseError as exc:
        raise ValueError("Original native XML is malformed; do not guess links") from exc
    references=[]
    for element in node.iter():
        if isinstance(element.tag,str) and element.tag.rsplit("}",1)[-1] == "reference":
            literal=element.attrib.get("osisRef")
            canonical_only_for_comparison(literal)
            references.append(literal)
    return references


def _original_reference_targets(raw: bytes) -> list[str]:
    return [canonical_only_for_comparison(value)
            for value in _source_reference_literals(raw)]


class SourceReferenceGate:
    def __init__(self, *, source_map: dict, expected_refs: dict, candidate: str):
        self.source_map = source_map
        self.chapter = source_map.get("scope")
        units = source_map.get("sections")
        if not isinstance(units,list) or not units:
            raise ValueError("Source-native unit map missing")
        self.units = {x["first_key"]: x for x in units}
        if len(self.units)!=len(units):
            raise ValueError("Duplicate original native unit key")
        if (not isinstance(expected_refs,dict)
                or set(expected_refs)!=set(self.units)):
            raise ValueError("Every source section must have an explicit reference expectation")
        self.expected=expected_refs
        self.candidate=candidate
        self.seen={}
        self._private_literal_links={}
        intro_rows=source_map.get("introductions",[])
        if not isinstance(intro_rows,list):
            raise ValueError("Original chapter/book introduction list invalid")
        self.intro_units={row["native_key"]:row for row in intro_rows}
        if len(self.intro_units)!=len(intro_rows):
            raise ValueError("Duplicate original introduction native key")
        self.intros_seen={}
        self.composite_expectations=source_map.get("intro_provenance_expectations")
        if self.composite_expectations is not None and not isinstance(self.composite_expectations,dict):
            raise ValueError("Unstructured original composite intro evidence")
        self.composite_verified=self.composite_expectations is None
        self._private_original_composite_tree=None
        for key,entries in expected_refs.items():
            if not isinstance(entries,list):
                raise ValueError("Expected source references must be a list")
            for entry in entries:
                if (not isinstance(entry,dict)
                        or not _REF.fullmatch(entry.get("canonical_target",""))
                        or not isinstance(entry.get("modern_text_marker"),str)
                        or not entry["modern_text_marker"]):
                    raise ValueError("Malformed verified original reference expectation")
                if entry["modern_text_marker"] not in candidate:
                    raise ValueError("Modern draft has not retained expected reference: "+key)

    def observe(self, kind: str, key: str, raw: bytes):
        if kind == "I" and key in self.intro_units:
            original=self.intro_units[key]
            digest=hashlib.sha256(raw).hexdigest()
            if digest != original.get("source_sha256") or key in self.intros_seen:
                raise ValueError("Native book/chapter intro differs from the pinned original")
            try:
                node=ET.fromstring(b"<source>" + raw + b"</source>")
            except ET.ParseError as exc:
                raise ValueError("Original introduction XML invalid") from exc
            visible=" ".join(node.itertext())
            self.intros_seen[key]={
                "source_raw_sha256":digest,
                "source_visible_word_count":len(re.findall(r"\b[\w’-]+\b",visible)),
                "has_visible_text":bool(visible.strip()),
                "source_introduction_still_not_semantically_approved":True
            }
            return
        if kind != "K" or key not in self.units:
            return
        if key in self.seen:
            raise ValueError("Source reader duplicated first native section key")
        unit=self.units[key]
        digest=hashlib.sha256(raw).hexdigest()
        if not _SHA.fullmatch(unit["source_sha256"]) or unit["source_sha256"]!=digest:
            raise ValueError("Source first native section changed from pinned SHA")
        literals=_source_reference_literals(raw)
        original=[canonical_only_for_comparison(value) for value in literals]
        expected=[i["canonical_target"] for i in self.expected[key]]
        if original != expected:
            raise ValueError("Original reference destinations diverge from predeclared native expectations")
        markup=unit.get("markup_census",{})
        source_count=markup.get("tag_counts",{}).get("reference",0)
        if len(original)!=source_count:
            raise ValueError("Exact source-native XML reference count differs from structural inventory")
        compound=self.composite_expectations
        if compound and key==compound.get("original_first_numbered_key"):
            try:
                source=ET.fromstring(b"<source>"+raw+b"</source>")
            except ET.ParseError as exc:
                raise ValueError("Invalid original composite first numbered XML") from exc
            visible=re.sub(r"\s+"," "," ".join(source.itertext())).strip()
            for field in ("expected_original_book_intro_start",
                          "expected_original_exposition_start"):
                phrase=compound.get(field)
                if not isinstance(phrase,str) or not phrase or phrase not in visible:
                    raise ValueError("First numbered original source does not contain declared book-intro/exposition boundary")
            counts={}
            for node in source.iter():
                if node is source or not isinstance(node.tag,str):
                    continue
                name=node.tag.rsplit("}",1)[-1]
                counts[name]=counts.get(name,0)+1
            for field,tag in (("expected_original_chapter_outline_row_count","row"),
                              ("expected_original_chapter_outline_table_count","table"),
                              ("expected_original_chapter_outline_title_count","title")):
                if type(compound.get(field)) is not int or counts.get(tag,0)!=compound[field]:
                    raise ValueError("Original composite source editorial outline structure has drifted")
            self.composite_verified=True
            self._private_original_composite_tree=source
        self._private_literal_links[key]=literals
        self.seen[key]={"reference_count":len(original),
                        "source_raw_sha256":digest,
                        "source_original_reference_identity_sha256":[
                            hashlib.sha256(r.encode("utf-8")).hexdigest()
                            for r in original],
                        "draft_marker_present":True}

    def original_composite_outline_tree_after_verified_source(self, raw_source_report: dict):
        """Use only for private source-identity-preserving introductory layout."""
        self.report(raw_source_report)
        if self._private_original_composite_tree is None:
            raise ValueError("Composite first native K source not independently attested")
        return self._private_original_composite_tree

    def exact_source_link_literals_after_verified_source(self, raw_source_report: dict):
        """Use only inside an isolated builder, never serialize the returned dict."""
        self.report(raw_source_report)
        return {key:list(values) for key,values in self._private_literal_links.items()}

    def report(self, raw_source_report: dict) -> dict:
        pin=self.source_map.get("verified_entire_native_corpus_sha256")
        if not isinstance(pin,str) or not _SHA.fullmatch(pin):
            raise ValueError("Invalid signed source-native corpus pin")
        if raw_source_report.get("all_native_raw_entries_ordered_sha256")!=pin:
            raise ValueError("Whole native source changed from approved corpus")
        if set(self.seen)!=set(self.units):
            raise ValueError("Some original first source units were not visited")
        if set(self.intros_seen)!=set(self.intro_units):
            raise ValueError("Some original book/chapter introduction keys not visited")
        if not self.composite_verified:
            raise ValueError("Book intro/outline origin in original first K was never attested")
        if self.composite_expectations and any(
                row["source_visible_word_count"]!=0
                for row in self.intros_seen.values()):
            raise ValueError("Source I placeholders unexpectedly acquired prose; manual reindex review needed")
        return {
            "status":"EXACT_ORIGINAL_REFERENCE_ATTRIBUTES_MATCH_EXPECTATIONS_NOT_LINK_SERIALIZATION_ACCEPTANCE",
            "chapter":self.chapter,
            "full_published_native_corpus_sha256":pin,
            "source_unique_units_checked":len(self.units),
            "original_reference_links_checked":sum(x["reference_count"] for x in self.seen.values()),
            "per_source_unit":self.seen,
            "original_intro_units_found":len(self.intros_seen),
            "original_book_intro_and_outline_owned_by_first_numbered_K_attested":bool(self.composite_expectations and self.composite_verified),
            "per_intro_unit":self.intros_seen,
            "original_prose_or_reference_labels_exported":False,
            "original_osisRef_literal_values_exported":False,
            "original_source_rewritten":False,
            "new_modern_osis_reference_targets_embedded":False,
            "independent_semantic_review_approved":False
        }



class WholeCanonOriginalLinkIdentityReceipt:
    """Attest every published original-K link and its order, without exporting prose.

    The pre-existing whole-canon source receipt supplies immutable group hashes,
    occupied verse keys and counts. This independent traversal validates them
    against the *same complete* SHA-pinned real SWORD raw stream. Link targets,
    linked display text and source XML are hashed in private memory only.
    This class does not match a translated word, inject a link, or build a module.
    """

    STATUS = "SOURCE_NATIVE_ALL_K_REFERENCE_IDENTITIES_NOT_MODERN_LINK_PARITY"

    def __init__(self, native: dict):
        if (native.get("status") != "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL"
                or native.get("source_prose_or_original_markup_exported") is not False
                or native.get("semantic_translation_independently_approved") is not False):
            raise ValueError("Whole-canon source receipt is not an admissible original")
        pin = native.get("original_compiled_corpus_sha256")
        if not isinstance(pin, str) or not _SHA.fullmatch(pin):
            raise ValueError("Missing pinned original full SWORD corpus SHA")
        chapters = native.get("chapters")
        if not isinstance(chapters, dict) or not chapters:
            raise ValueError("Original chapter inventory is empty")
        self.corpus_sha = pin
        self.units: dict[str, dict] = {}
        self.keys: dict[str, str] = {}
        self.seen_keys: set[str] = set()
        self.seen_first: set[str] = set()
        self.linked_units: dict[str, dict] = {}
        self.link_count = 0
        for chapter, contents in chapters.items():
            groups = contents.get("original_units")
            if not isinstance(groups, list):
                raise ValueError("Original source chapter groups missing: " + chapter)
            for group in groups:
                first = group.get("first_key")
                keys = group.get("keys")
                sha = group.get("source_unit_sha256")
                tags = group.get("markup", {}).get("tag_counts", {})
                count = tags.get("reference", 0)
                if (not isinstance(first, str) or not isinstance(keys, list)
                        or not keys or keys[0] != first or first in self.units
                        or not isinstance(sha, str) or not _SHA.fullmatch(sha)
                        or type(count) is not int or count < 0):
                    raise ValueError("Unreliable original source group record: " + chapter)
                if not isinstance(tags, dict) or group["markup"].get(
                        "strict_xml_fragment") is not True:
                    raise ValueError("Original K group has not passed strict XML parsing")
                self.units[first] = {"sha": sha, "ref_count": count,
                                     "last": keys[-1]}
                for key in keys:
                    if (not isinstance(key, str) or not key.startswith(chapter + ".")
                            or key in self.keys):
                        raise ValueError("Repeated or foreign original K address")
                    self.keys[key] = first
        if not self.units or not self.keys:
            raise ValueError("No authentic original numbered commentary entries")

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        if kind != "K":
            return
        owner = self.keys.get(key)
        if owner is None or key in self.seen_keys:
            raise ValueError("Unexpected or duplicate original numbered SWORD key: " + key)
        group = self.units[owner]
        if hashlib.sha256(raw).hexdigest() != group["sha"]:
            raise ValueError("Original K alias and source SHA differ: " + key)
        self.seen_keys.add(key)
        if key != owner:
            return
        if owner in self.seen_first:
            raise ValueError("Duplicate first original K group key")
        self.seen_first.add(owner)
        try:
            node = ET.fromstring(b"<original>" + raw + b"</original>")
        except ET.ParseError as exc:
            raise ValueError("Original link-bearing K XML is malformed: " + owner) from exc
        targets = []
        labels = []
        for element in node.iter():
            if not isinstance(element.tag, str) or element.tag.rsplit("}", 1)[-1] != "reference":
                continue
            literal = element.attrib.get("osisRef")
            if (not isinstance(literal, str) or not literal or len(literal) > 2048
                    or any(ord(char) < 32 for char in literal)):
                raise ValueError("Original reference has missing/unsafe literal target: " + owner)
            # Preserve exact literal attribute spelling and occurrence order.
            # Do not impose the restricted single-verse parser from the Gen.1 pilot.
            targets.append(hashlib.sha256(literal.encode("utf-8")).hexdigest())
            labels.append(hashlib.sha256(
                "".join(element.itertext()).encode("utf-8")).hexdigest())
        if len(targets) != group["ref_count"]:
            raise ValueError("Original XML reference count differs from authenticated census: "
                             + owner)
        self.link_count += len(targets)
        if targets:
            self.linked_units[owner] = {
                "first_key": owner,
                "last_key": group["last"],
                "source_raw_sha256": group["sha"],
                "reference_count": len(targets),
                "original_osisRef_sha256_in_document_order": targets,
                "original_visible_link_label_sha256_in_document_order": labels,
            }

    def report(self, reader_report: dict) -> dict:
        if reader_report.get("all_native_raw_entries_ordered_sha256") != self.corpus_sha:
            raise ValueError("Full original native SWORD SHA does not match pinned edition")
        if (self.seen_keys != set(self.keys)
                or self.seen_first != set(self.units)):
            raise ValueError("Original K keys or source body groups were not completely read")
        return {
            "status": self.STATUS,
            "whole_native_source_sha256": self.corpus_sha,
            "original_numbered_K_keys_verified": len(self.seen_keys),
            "original_unique_K_bodies_verified": len(self.seen_first),
            "original_reference_elements_verified": self.link_count,
            "original_link_bearing_K_bodies": len(self.linked_units),
            "source_link_groups": [
                self.linked_units[k] for k in sorted(self.linked_units)
            ],
            "original_link_destinations_only_sha256_not_exported": True,
            "original_visible_link_text_only_sha256_not_exported": True,
            "original_source_prose_or_XML_exported": False,
            "modern_manuscript_reference_presence_approved": False,
            "modern_osisRef_targets_or_order_verified": False,
            "translated_link_display_text_reviewed": False,
            "source_original_mutated": False,
            "modern_module_built_or_published": False,
        }


def run_whole_native_link_identity(*, reader: Path, root: Path,
                                    module_id: str, native_receipt: Path) -> dict:
    native = json.loads(native_receipt.read_text(encoding="utf-8"))
    gate = WholeCanonOriginalLinkIdentityReceipt(native)
    env = os.environ.copy()
    env["SWORD_PATH"] = str(root.resolve())
    proc = subprocess.Popen([str(reader.resolve()), module_id], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Original native raw stream is unavailable")
        complete, *_ = parse_native_raw_corpus(proc.stdout, on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=30) != 0:
            raise ValueError("Original native raw reader failed")
        return gate.report(complete)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


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



def _wrap_exact_authored_modern_text(section: ET.Element, *, anchor: str,
                                      display: str, occurrence: str,
                                      target: str) -> None:
    """Insert one reviewed Bible link without changing ANY modern visible prose.

    One full authored citation anchor must be present in exactly one XML text
    slot of one source-indexed section. No fuzzy search, source-word rewriting,
    markup flattening or implicit verse guessing is permitted.
    """
    if (not isinstance(anchor, str) or not anchor or len(anchor) > 512
            or not isinstance(display, str) or not display
            or display not in anchor or occurrence not in ("first", "last")
            or not _allowed_source_link_target(target)):
        raise ValueError("Invalid reviewed modern citation/text placement")
    positions = []
    for node in section.iter():
        # A source body can legitimately contain several distinct hyperlinks.
        # Existing reference *text* is protected against nested wrapping;
        # its trailing text is ordinary modern prose and can hold a next link.
        already_ref = node.tag.rsplit("}", 1)[-1] == "reference"
        for kind in ("text", "tail"):
            if already_ref and kind == "text":
                continue
            slot = getattr(node, kind)
            if isinstance(slot, str) and anchor in slot:
                for _ in range(slot.count(anchor)):
                    positions.append((node, kind, slot))
    if len(positions) != 1:
        raise ValueError("Reviewed modern citation anchor is missing or ambiguous")
    node, kind, original = positions[0]
    anchor_start = original.find(anchor)
    inner_at = (anchor.rfind(display) if occurrence == "last"
                else anchor.find(display))
    if inner_at < 0:
        raise ValueError("Reviewed linked text missing inside its full anchor")
    start = anchor_start + inner_at
    end = start + len(display)
    before, after = original[:start], original[end:]
    old_prose = "".join(section.itertext())
    ref = ET.Element("{http://www.bibletechnologies.net/2003/OSIS/namespace}reference",
                     {"osisRef": target})
    ref.text = display
    ref.tail = after
    if kind == "text":
        node.text = before
        node.insert(0, ref)
    else:
        parent = next((p for p in section.iter() if node in list(p)), None)
        if parent is None:
            raise ValueError("Reviewed citation tail has no XML parent")
        node.tail = before
        parent.insert(list(parent).index(node) + 1, ref)
    if "".join(section.itertext()) != old_prose:
        raise ValueError("Link insertion must not modify modern authorial visible text")


# This generic concordance is a *recognition* aid, not a replacement for
# authored Scripture references. Only exact, full "Book chapter:verse" forms
# inside one real modern commentary K body can be auto-attached to an
# authenticated original osisRef. Ranges and ellipses are NEVER guessed.
_ENGLISH_CANONICAL_NAMES = (
    "Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    "1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|"
    "Ezra|Nehemiah|Esther|Job|Psalm|Proverbs|Ecclesiastes|Song of Solomon|"
    "Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|"
    "Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|"
    "Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|"
    "Galatians|Ephesians|Philippians|Colossians|1 Thessalonians|"
    "2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|Hebrews|James|"
    "1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation"
).split("|")
from commentary_modern_draft_osis_preview import _CANON as _ORIGINAL_CANON
if len(_ENGLISH_CANONICAL_NAMES) != len(_ORIGINAL_CANON):
    raise RuntimeError("Canonical Bible book-name mapping cannot be trusted")
_ENGLISH_NAME_BY_OSIS = dict(zip(_ORIGINAL_CANON, _ENGLISH_CANONICAL_NAMES))
_ENGLISH_NAME_BY_OSIS["Ps"] = "Psalm"
# Exact, conventional, period-terminated English book abbreviations can be
# matched only inside the already authenticated source-owned K exposition.
# Do not accept unpunctuated lookalikes or infer any abbreviated verse numbers.
_AUTO_ALIASES = {
    "Gen": ("Genesis", "Gen."),
    "Exod": ("Exodus", "Exod.", "Ex."),
    "Lev": ("Leviticus", "Lev."),
    "Num": ("Numbers", "Num."),
    "Deut": ("Deuteronomy", "Deut."),
    "Josh": ("Joshua", "Josh."),
    "Judg": ("Judges", "Judg."),
    "1Sam": ("1 Samuel", "1 Sam."),
    "2Sam": ("2 Samuel", "2 Sam."),
    "1Kgs": ("1 Kings", "1 Kgs."),
    "2Kgs": ("2 Kings", "2 Kgs."),
    "1Chr": ("1 Chronicles", "1 Chr."),
    "2Chr": ("2 Chronicles", "2 Chr."),
    "Neh": ("Nehemiah", "Neh."),
    "Esth": ("Esther", "Esth."),
    "Ps": ("Psalm", "Psalms", "Ps."),
    "Prov": ("Proverbs", "Prov."),
    "Eccl": ("Ecclesiastes", "Eccl."),
    "Song": ("Song of Solomon", "Song of Songs"),
    "Isa": ("Isaiah", "Isa."),
    "Jer": ("Jeremiah", "Jer."),
    "Ezek": ("Ezekiel", "Ezek."),
    "Dan": ("Daniel", "Dan."),
    "Hos": ("Hosea", "Hos."),
    "Zech": ("Zechariah", "Zech."),
    "Matt": ("Matthew", "Matt."),
    "Mark": ("Mark", "Mk."),
    "Luke": ("Luke", "Lk."),
    "John": ("John", "Jn."),
    "Acts": ("Acts", "Acts."),
    "Rom": ("Romans", "Rom."),
    "1Cor": ("1 Corinthians", "1 Cor."),
    "2Cor": ("2 Corinthians", "2 Cor."),
    "Gal": ("Galatians", "Gal."),
    "Eph": ("Ephesians", "Eph."),
    "Phil": ("Philippians", "Phil."),
    "Col": ("Colossians", "Col."),
    "1Thess": ("1 Thessalonians", "1 Thess."),
    "2Thess": ("2 Thessalonians", "2 Thess."),
    "1Tim": ("1 Timothy", "1 Tim."),
    "2Tim": ("2 Timothy", "2 Tim."),
    "Heb": ("Hebrews", "Heb."),
    "Jas": ("James", "Jas."),
    "1Pet": ("1 Peter", "1 Pet."),
    "2Pet": ("2 Peter", "2 Pet."),
    "1John": ("1 John", "1 Jn."),
    "2John": ("2 John", "2 Jn."),
    "3John": ("3 John", "3 Jn."),
    "Rev": ("Revelation", "Rev."),
}


def _unambiguous_explicit_modern_verse(section: ET.Element, target: str):
    """Find one literal English full-name single-verse citation, otherwise None.

    No source XML or modern prose is changed by this recognition function.
    In particular it deliberately rejects 3:16–17, 3:16,17, ambiguous
    repetitions, existing links and citations that cross markup boundaries.
    """
    canonical = canonical_only_for_comparison(target)
    book, chapter, verse = canonical.rsplit(".", 2)
    names = _AUTO_ALIASES.get(book, (_ENGLISH_NAME_BY_OSIS.get(book),))
    if any(not x for x in names):
        return None
    candidates = []
    for name in names:
        regex = re.compile(r"(?<![A-Za-z0-9])" + re.escape(name) +
                           r"\s+" + re.escape(chapter) + ":" +
                           re.escape(verse) + r"(?![0-9])", re.I)
        for paragraph in section.iter():
            if paragraph.tag.rsplit("}",1)[-1] != "p":
                continue
            for node in paragraph.iter():
                if not isinstance(node.tag, str):
                    continue
                # Never overwrite existing reviewed links, but allow tails.
                for part in ("text", "tail"):
                    if part == "text" and node.tag.rsplit("}", 1)[-1] == "reference":
                        continue
                    value = getattr(node, part)
                    if not isinstance(value, str):
                        continue
                    for hit in regex.finditer(value):
                        suffix = value[hit.end():]
                        prefix = value[:hit.start()]
                        # "John 3:16" must not match inside "1 John 3:16".
                        if (book == "John" and
                                re.search(r"(?:^|[^A-Za-z0-9])[1-3]\s+$", prefix)):
                            continue
                        if re.match(r"\s*[-–—,]\s*\d", suffix):
                            continue
                        candidates.append(hit[0])
    return candidates[0] if len(candidates) == 1 else None



_SOURCE_FULL_RANGE = re.compile(
    r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)-"
    r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.(\d+)\.(\d+)$")


def _source_same_chapter_verse_range(literal: str):
    """Parse ONLY original full OSIS ranges with one book and chapter.

    Preserve the source literal in the final XML, including any work prefix.
    This is no general conversion of OSIS expression syntax or versification.
    """
    if not isinstance(literal, str):
        return None
    raw = literal[6:] if literal.startswith("Bible:") else literal
    hit = _SOURCE_FULL_RANGE.fullmatch(raw)
    if not hit:
        return None
    book, chapter, start, end_book, end_chapter, end = hit.groups()
    if (book != end_book or chapter != end_chapter
            or book not in _ENGLISH_NAME_BY_OSIS
            or not 1 <= int(start) < int(end) <= 200):
        return None
    if any(s.startswith("0") for s in (chapter, start, end)):
        return None
    return book, chapter, start, end



def _allowed_source_link_target(target: str) -> bool:
    try:
        canonical_only_for_comparison(target)
        return True
    except ValueError:
        return _source_same_chapter_verse_range(target) is not None


def _unambiguous_explicit_modern_range(section: ET.Element, literal: str):
    """Return one explicit same-book same-chapter modern 3:16–18, else None."""
    parsed = _source_same_chapter_verse_range(literal)
    if parsed is None:
        return None
    book, chapter, first, last = parsed
    names = _AUTO_ALIASES.get(book, (_ENGLISH_NAME_BY_OSIS.get(book),))
    matches=[]
    for name in names:
        if not name:
            continue
        rex=re.compile(r"(?<![A-Za-z0-9])" + re.escape(name) + r"\s+" +
                       re.escape(chapter) + ":" + re.escape(first) +
                       r"\s*[-–—]\s*" + re.escape(last) + r"(?![0-9])", re.I)
        for para in section.iter():
            if para.tag.rsplit("}",1)[-1] != "p":
                continue
            for node in para.iter():
                if not isinstance(node.tag,str):
                    continue
                for field in ("text","tail"):
                    if field=="text" and node.tag.rsplit("}",1)[-1]=="reference":
                        continue
                    slot=getattr(node,field)
                    if not isinstance(slot,str):
                        continue
                    for match in rex.finditer(slot):
                        prefix,suffix=slot[:match.start()],slot[match.end():]
                        if book=="John" and re.search(
                            r"(?:^|[^A-Za-z0-9])[1-3]\s+$",prefix):
                            continue
                        if re.match(r"\s*[-–—,]\s*\d",suffix):
                            continue
                        matches.append(match[0])
    return matches[0] if len(matches)==1 else None


def _source_range_section_ownership(*, literal: str, label: str,
                                    source_chapter: str, keys: list[str],
                                    section: ET.Element) -> dict[str, bool]:
    """Diagnostic only: does a genuine source self-range own a modern heading?

    Exact authored K key occupancy is decisive. A source cross-reference to
    another passage must never be silently relocated to an editorial heading.
    This classifier returns no text and does not add a hyperlink.
    """
    parsed = _source_same_chapter_verse_range(literal)
    if parsed is None:
        return {"same_chapter":False,"exact_K_scope":False,
                "matching_modern_heading":False,"source_label_is_verse_span":False}
    book, chapter, first, last = parsed
    same=source_chapter==book+"."+chapter
    from commentary_modern_draft_osis_preview import NS, _range
    target=literal[6:] if literal.startswith("Bible:") else literal
    exact=same and target==_range(keys)
    names=[v for v in section.findall(f"./{{{NS}}}title") if
           v.get("type")=="sub"]
    pattern=re.compile(r"\bverses?\s+"+re.escape(first)+
                       r"\s*[-–—]\s*"+re.escape(last)+r"\b", re.I)
    title=exact and len(names)==1 and bool(pattern.search(
        "".join(names[0].itertext())))
    source_label=re.fullmatch(
        r"(?:v(?:erses?)?\.?\s*)?"+re.escape(first)+r"\s*[-–—]\s*"+
        re.escape(last)+r"\.?", label.strip(), re.I)
    return {"same_chapter":same,"exact_K_scope":exact,
            "matching_modern_heading":bool(title),
            "source_label_is_verse_span":bool(source_label)}




def _find_exact_modern_original_outline_range_cell(
        modern_chapter: ET.Element, literal: str) -> ET.Element | None:
    """The ONE manuscript outline-table verse cell matching a source OSIS span.

    This does not infer new ranges, transpose chapter order or rewrite any
    authorial text; it returns None on missing, ambiguous or decorated cells.
    """
    parsed=_source_same_chapter_verse_range(literal)
    if parsed is None:
        return None
    book,chapter,start,end=parsed
    if modern_chapter.get("osisID")!=book+"."+chapter:
        return None
    from commentary_modern_draft_osis_preview import NS
    matches=[]
    for intro in modern_chapter.findall(f"./{{{NS}}}div[@type='introduction']"):
        titles=intro.findall(f"./{{{NS}}}title")
        if len(titles)!=1 or titles[0].text!="Original chapter outline":
            continue
        tables=intro.findall(f"./{{{NS}}}table")
        if len(tables)!=1:
            continue
        rows=tables[0].findall(f"./{{{NS}}}row")
        if len(rows)<2:
            continue
        header=rows[0].findall(f"./{{{NS}}}cell")
        if (len(header)!=2 or
                "".join(header[0].itertext()).strip()!="Original outline" or
                "".join(header[1].itertext()).strip()!="Verses"):
            continue
        for row in rows[1:]:
            cells=row.findall(f"./{{{NS}}}cell")
            if len(cells)!=2:
                continue
            text="".join(cells[1].itertext()).strip()
            if re.fullmatch(re.escape(start)+r"\s*[-–—]\s*"+re.escape(end),text):
                matches.append(cells[1])
    return matches[0] if len(matches)==1 else None

def _source_first_K_outline_row_evidence(*, literal: str, label: str,
                                         first_key: str, native_chapter: dict,
                                         modern_chapter: ET.Element) -> dict[str,bool]:
    """Classify authenticated original chapter-outline links without editing.

    Original cross-references must not be conflated with source-K outline
    navigation, which is often carried inside the first original K body but
    is represented by a separate original-outline table in modern manuscripts.
    """
    result={"source_first_K_owns_link":False,
            "unique_modern_outline_row_matches_source_target":False,
            "original_visible_label_explicitly_names_same_verse_span":False}
    parsed=_source_same_chapter_verse_range(literal)
    if parsed is None:
        return result
    book, chapter, first, last=parsed
    if modern_chapter.get("osisID")!=book+"."+chapter:
        return result
    units=native_chapter.get("original_units",[])
    if not units or units[0]["first_key"]!=first_key:
        return result
    result["source_first_K_owns_link"]=True
    result["unique_modern_outline_row_matches_source_target"]=(
        _find_exact_modern_original_outline_range_cell(
            modern_chapter,literal) is not None)
    # No arbitrary source prose: the original visible link's numeric chapter
    # and verse span must agree too (e.g., "Is. 1:1-9").
    result["original_visible_label_explicitly_names_same_verse_span"]=bool(
        re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z .]{0,28}\s+"+
                     re.escape(chapter)+":"+re.escape(first)+
                     r"\s*[-–—]\s*"+re.escape(last),label.strip()))
    return result



_AUTHENTIC_SINGLE_VERSE_LABEL = re.compile(
    r"^((?:[1-4]\s*)?[A-Za-z][A-Za-z. ]{0,27}?)\s+"
    r"([1-9][0-9]{0,2}):([1-9][0-9]{0,2})\.?$")


def _unique_authentic_original_visible_label(
        section: ET.Element, literal: str, label: str) -> str | None:
    """Match the *source-owned* printed single-verse citation, unchanged.

    A fallback for abbreviations already authored in both editions; it cannot
    invent a target, modern wording, link location, a Bible book identity or a
    range. The exact original osisRef and link-label hashes are authenticated
    separately by the full original native SWORD reader.
    """
    try:
        book, chapter, verse = canonical_only_for_comparison(literal).rsplit(".", 2)
    except ValueError:
        return None
    name = _ENGLISH_NAME_BY_OSIS.get(book)
    raw = label.strip()
    match = _AUTHENTIC_SINGLE_VERSE_LABEL.fullmatch(raw)
    if not name or match is None or match[2] != chapter or match[3] != verse:
        return None
    def norm(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.casefold())
    permitted = {norm(book), norm(re.sub(r"^([1-4])([A-Z])", r"\1 \2", book)),
                 norm(name)}
    if book=="Ps":
        permitted.update(("ps", "psalm", "psalms"))
    if book=="Song":
        permitted.update(("songofsolomon", "songofsongs"))
    if norm(match[1]) not in permitted:
        return None
    instances=[]
    from commentary_modern_draft_osis_preview import NS
    for p in section.iter():
        if p.tag!=f"{{{NS}}}p":
            continue
        for node in p.iter():
            for field in ("text","tail"):
                if field=="text" and node.tag==f"{{{NS}}}reference":
                    continue
                value=getattr(node,field)
                if not isinstance(value,str):
                    continue
                at=0
                while True:
                    i=value.find(raw,at)
                    if i<0:
                        break
                    j=i+len(raw)
                    if ((i==0 or not value[i-1].isalnum()) and
                            (j==len(value) or not value[j].isalnum())):
                        instances.append(raw)
                    at=i+1
    return instances[0] if len(instances)==1 else None


def _unrecognized_original_ref_class(literal: str) -> str:
    """Only classify syntax in metadata; never emit literal source osisRef."""
    raw = literal[6:] if literal.startswith("Bible:") else literal
    atom = r"[1-4]?[A-Za-z][A-Za-z0-9]*\.\d+\.\d+"
    if re.fullmatch(atom + "-" + atom, raw):
        return "full_verse_range"
    if re.fullmatch(atom + r"-\d+", raw):
        return "abbreviated_verse_range"
    if re.fullmatch(atom + r"\s+" + atom + r"(?:\s+" + atom + ")*", raw):
        return "space_joined_verses"
    if re.fullmatch(atom + r"[;,]\s*" + atom + r"(?:[;,]\s*" + atom + ")*", raw):
        return "punctuation_joined_verses"
    if re.match(atom + r"-", raw):
        return "other_range_syntax"
    if re.search(r"[\s;,]", raw):
        return "other_compound_syntax"
    return "other_original_syntax"


def _auto_single_verse_placements(*, private_original: dict, groups: dict,
                                  modern_chapters: dict, native: dict,
                                  blocked: set, corrections: dict,
                                  include_ranges: bool = False,
                                  include_outline_links: bool = False,
                                  include_authentic_labels: bool = False):
    """Return conservative placements plus classified counts, no private text."""
    from commentary_modern_draft_osis_preview import NS, _range
    found = []
    skipped = {"already_reviewed": 0, "proposed_original_correction": 0,
               "unsupported_original_reference_syntax": 0,
               "unrecognized_format_full_verse_range":0,
               "unrecognized_format_abbreviated_verse_range":0,
               "unrecognized_format_space_joined_verses":0,
               "unrecognized_format_punctuation_joined_verses":0,
               "unrecognized_format_other_range_syntax":0,
               "unrecognized_format_other_compound_syntax":0,
               "unrecognized_format_other_original_syntax":0,
               "repeated_original_target": 0, "unverified_or_single_digit_label": 0,
               "no_unique_full_modern_verse_citation": 0,
               "no_unique_full_modern_verse_range_citation":0,
               "matching_unique_authenticated_original_visible_label":0,
               "source_range_spans_chapters_or_has_unsafe_bounds":0,
               "unmatched_source_range_same_chapter":0,
               "unmatched_source_range_exact_original_K_scope":0,
               "unmatched_source_range_exact_K_scope_with_modern_heading":0,
               "unmatched_source_range_source_label_matches_scope":0,
               "unmatched_source_range_first_K_owns_chapter_outline_link":0,
               "unmatched_source_range_unique_modern_outline_row":0,
               "unmatched_source_range_outline_row_and_source_label_match":0}
    for first, links in private_original.items():
        chapter = first.rsplit(".", 1)[0]
        units = native["chapters"][chapter]["original_units"]
        ordinal = next(i for i, u in enumerate(units) if u["first_key"] == first)
        sections = modern_chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(units):
            raise ValueError("Source-group count changed during automatic citation lookup")
        section = sections[ordinal]
        if section.get("annotateRef") != _range(units[ordinal]["keys"]):
            raise ValueError("Auto lookup cannot use a non-original commentary scope")
        targets=[]
        for literal, _ in links:
            try:
                targets.append(canonical_only_for_comparison(literal))
            except ValueError:
                # Full original range syntax remains an immutable source
                # literal. Never infer abbreviated or cross-chapter spans.
                parsed=(_source_same_chapter_verse_range(literal)
                        if include_ranges else None)
                if parsed is not None:
                    targets.append("RANGE:"+
                        (literal[6:] if literal.startswith("Bible:") else literal))
                else:
                    targets.append(None)
        for pos, (literal, label) in enumerate(links, 1):
            key = (first, pos)
            if key in blocked:
                skipped["already_reviewed"] += 1
                continue
            if key in corrections:
                skipped["proposed_original_correction"] += 1
                continue
            canon = targets[pos-1]
            if canon is None:
                skipped["unsupported_original_reference_syntax"] += 1
                syntax = _unrecognized_original_ref_class(literal)
                skipped["unrecognized_format_"+syntax] += 1
                continue
            if targets.count(canon) != 1:
                skipped["repeated_original_target"] += 1
                continue
            if not label.strip() or re.fullmatch(r"[1-9]", label.strip()):
                skipped["unverified_or_single_digit_label"] += 1
                continue
            is_range=canon.startswith("RANGE:")
            if is_range:
                display=_unambiguous_explicit_modern_range(section,literal)
            else:
                display=_unambiguous_explicit_modern_verse(section,literal)
            if display is None and not is_range and include_authentic_labels:
                # Distinct source links sharing an identical printed marker
                # cannot be disambiguated by a unique modern text occurrence.
                original_label_occurrences=sum(
                    old_label.strip()==label.strip()
                    for _,old_label in links)
                authentic=(_unique_authentic_original_visible_label(
                    section,literal,label)
                    if original_label_occurrences==1 else None)
                if authentic is not None:
                    skipped["matching_unique_authenticated_original_visible_label"]+=1
                    found.append({
                        "modern_chapter": chapter,
                        "source_first_key": first,
                        "original_link_ordinal": pos,
                        "action": "AUTO_UNIQUE_AUTHENTIC_ORIGINAL_SINGLE_VERSE_LABEL",
                        "expected_modern_target": canon,
                        "modern_anchor": authentic,
                        "linked_display_text": authentic,
                        "display_occurrence": "last",
                    })
                    continue
            if display is None:
                if is_range:
                    ownership=_source_range_section_ownership(
                        literal=literal,label=label,source_chapter=chapter,
                        keys=units[ordinal]["keys"],section=section)
                    for field,category in (
                        ("same_chapter","unmatched_source_range_same_chapter"),
                        ("exact_K_scope","unmatched_source_range_exact_original_K_scope"),
                        ("matching_modern_heading",
                         "unmatched_source_range_exact_K_scope_with_modern_heading"),
                        ("source_label_is_verse_span",
                         "unmatched_source_range_source_label_matches_scope")):
                        if ownership[field]:
                            skipped[category]+=1
                    outline=_source_first_K_outline_row_evidence(
                        literal=literal,label=label,first_key=first,
                        native_chapter=native["chapters"][chapter],
                        modern_chapter=modern_chapters[chapter])
                    if outline["source_first_K_owns_link"]:
                        skipped["unmatched_source_range_first_K_owns_chapter_outline_link"]+=1
                    if outline["unique_modern_outline_row_matches_source_target"]:
                        skipped["unmatched_source_range_unique_modern_outline_row"]+=1
                    if (outline["unique_modern_outline_row_matches_source_target"]
                            and outline["original_visible_label_explicitly_names_same_verse_span"]):
                        skipped["unmatched_source_range_outline_row_and_source_label_match"]+=1
                        if include_outline_links and outline["source_first_K_owns_link"]:
                            cell=_find_exact_modern_original_outline_range_cell(
                                modern_chapters[chapter],literal)
                            if cell is None:
                                raise ValueError("Source-attested outline range cell vanished")
                            cell_text="".join(cell.itertext()).strip()
                            found.append({
                                "modern_chapter":chapter,
                                "source_first_key":first,
                                "original_link_ordinal":pos,
                                "action":"AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE",
                                "expected_modern_target":canon,
                                "modern_anchor":cell_text,
                                "linked_display_text":cell_text,
                                "display_occurrence":"last",
                            })
                            continue
                skipped["no_unique_full_modern_verse_range_citation" if is_range
                        else "no_unique_full_modern_verse_citation"] += 1
                continue
            found.append({
                "modern_chapter": chapter,
                "source_first_key": first,
                "original_link_ordinal": pos,
                "action": ("AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE"
                          if is_range else
                          "AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_VERSE"),
                "expected_modern_target": canon,
                "modern_anchor": display,
                "linked_display_text": display,
                "display_occurrence": "last",
            })
    return found, skipped



def _original_reference_table_ownership(fragment: ET.Element) -> list[bool]:
    """Source-native reference ancestry, in exact original document order.

    Tables and their nested XML containers are tracked without exporting
    original prose, headings, link labels or raw OSIS reference values.
    """
    result=[]
    def visit(node: ET.Element, in_table: bool) -> None:
        if not isinstance(node.tag,str):
            return
        tag=node.tag.rsplit("}",1)[-1]
        current=in_table or tag=="table"
        if tag=="reference":
            result.append(current)
        for child in node:
            visit(child,current)
    visit(fragment,False)
    return result



def _original_reference_title_ownership(fragment: ET.Element) -> list[bool]:
    """Track authentic title-contained hyperlinks, never source text."""
    flags=[]
    def walk(node: ET.Element, inside_title: bool) -> None:
        if not isinstance(node.tag,str):
            return
        tag=node.tag.rsplit("}",1)[-1]
        inside=inside_title or tag=="title"
        if tag=="reference":
            flags.append(inside)
        for child in node:
            walk(child,inside)
    walk(fragment,False)
    return flags



def _unplaced_original_link_review_ledger(*, original: dict, insertions: list,
                                           corrections: dict) -> dict:
    """Account for every original hyperlink without exporting source text.

    This review queue exposes only exact original K addresses, occurrence
    ordinals, SHA-256 identity hashes, OSIS-grammar class and disposition.
    Source-visible labels and original literal OSIS targets are not serialized.
    """
    placed={}
    for row in insertions:
        ordinal=row.get("original_link_ordinal")
        if ordinal is None:
            continue  # separately supported authored witness, not original markup
        key=(row["original_source_first_key"],ordinal)
        if key in placed:
            raise ValueError("Original source link was independently placed twice")
        placed[key]=row["placement_action"]
    seen=set()
    omitted=[]
    pending=[]
    for first,links in sorted(original.items()):
        for ordinal,(target,label) in enumerate(links,1):
            key=(first,ordinal)
            if key in seen:
                raise ValueError("Duplicate source link occurrence in original inventory")
            seen.add(key)
            if key in placed:
                continue
            correction=corrections.get(key)
            if correction is not None:
                if correction.get("disposition")!="OMIT_SPURIOUS_ENUMERATOR_LINK":
                    raise ValueError("Documented original link correction was never applied")
                status="EXPLICITLY_OMITTED_SPURIOUS_NATIVE_HYPERLINK"
            else:
                try:
                    canonical_only_for_comparison(target)
                    status="UNPLACED_SINGLE_VERSE_REFERENCE"
                except ValueError:
                    if _source_same_chapter_verse_range(target):
                        status="UNPLACED_SAME_CHAPTER_VERSE_RANGE"
                    else:
                        status="UNPLACED_OTHER_OR_COMPOSITE_OSIS_TARGET"
            item={
                "source_first_key":first,
                "source_reference_ordinal":ordinal,
                "original_osisRef_sha256":hashlib.sha256(
                    target.encode("utf-8")).hexdigest(),
                "original_visible_label_sha256":hashlib.sha256(
                    label.encode("utf-8")).hexdigest(),
                "disposition":status
            }
            (omitted if correction is not None else pending).append(item)
    if set(placed)-seen:
        raise ValueError("Linked source occurrence is not in original pinned SWORD")
    if sum(map(len,original.values()))!=len(seen):
        raise ValueError("Original linked element tally inconsistent")
    if len(placed)+len(omitted)+len(pending)!=len(seen):
        raise ValueError("Whole-source hyperlink audit disposition incomplete")
    status_counts={}
    for row in pending+omitted:
        state=row["disposition"]
        status_counts[state]=status_counts.get(state,0)+1
    return {
        "status":"SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
        "original_native_reference_elements":len(seen),
        "source_link_occurrences_verified_in_derived_osis":len(placed),
        "source_spurious_link_occurrences_explicitly_omitted":len(omitted),
        "source_original_links_still_requiring_placement_review":len(pending),
        "pending_and_omitted_by_disposition":status_counts,
        "source_reference_labels_or_literal_targets_exported":False,
        "publication_authorized":False,
        "pending":pending,
        "documented_omitted":omitted,
    }


def overlay_reviewed_private_links(*, base_osis: bytes, placements: dict,
                                    native: dict, identities: dict,
                                    dispositions: dict, repo_root: Path,
                                    reader: Path, module_directory: Path,
                                    module_id: str,
                                    auto_single_verse: bool = False,
                                    auto_ranges: bool = False,
                                    auto_outline_links: bool = False,
                                    auto_authentic_labels: bool = False) -> tuple[bytes, dict]:
    """Authenticate and place an explicitly bounded set of source-backed links.

    Real original SWORD attributes stay in private memory/isolated new OSIS,
    never in logs or metadata-only CI artifacts. This is one technical batch;
    it does not assert the 1,204 original source links have been transferred.
    """
    from commentary_modern_draft_osis_preview import NS, _range
    if auto_ranges and not auto_single_verse:
        raise ValueError("Range mapping requires source-matched single-verse mode")
    if auto_outline_links and not auto_ranges:
        raise ValueError("Outline mapping requires original source range validation")
    if auto_authentic_labels and not auto_single_verse:
        raise ValueError("Original-label matching needs authenticated singleton source mode")
    if (placements.get("status") !=
            "PRIVATE_REVIEWED_BOUNDED_LINK_PLACEMENT_NOT_FINAL_EDIT_OR_RELEASE"
            or placements.get("published_source_module") != "MHCC 0.1.1"
            or any(placements.get(k) is not False for k in
                ("source_original_changed", "modern_prose_modified",
                 "independent_semantic_and_link_review_approved",
                 "publication_authorized"))):
        raise ValueError("Link placement manifest may not declare approval")
    pin = placements.get("published_source_corpus_sha256")
    if (pin != native.get("original_compiled_corpus_sha256")
            or pin != identities.get("whole_native_source_sha256")
            or pin != "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"
            or native.get("source_prose_or_original_markup_exported") is not False
            or identities.get("status") != WholeCanonOriginalLinkIdentityReceipt.STATUS
            or identities.get("original_reference_elements_verified") != 1204):
        raise ValueError("Missing complete authenticated original native reference source")
    correction_receipt = validate_proposed_link_dispositions(
        manifest=dispositions, native=native, identities=identities,
        repository_root=repo_root)
    if (not correction_receipt["source_link_target_and_label_hashes_checked_in_original_order"]
            or correction_receipt["original_link_proposal_actions_reviewed"] != 17):
        raise ValueError("Existing proposed error corrections not source-attested")
    proposed = placements.get("placements")
    if not isinstance(proposed, list) or not 1 <= len(proposed) <= 40:
        raise ValueError("Private bounded link placement list missing")
    groups = {r["first_key"]: r for r in identities["source_link_groups"]}
    requested = set(groups) if auto_single_verse else set()
    seen = set()
    correction_by_key = {
        (case["source_first_key"], edit["source_link_ordinal"]):
        edit for case in dispositions["cases"]
        for edit in case["corrections"]
    }
    addition_by_key = {
        (case["source_first_key"], item["target"]): item
        for case in dispositions["cases"]
        for item in case.get("modern_witness_links", [])
    }
    counted = {"COPY_EXACT_AUTHENTIC_SOURCE": 0,
               "CORRECT_AUTHENTIC_WRONG_TARGET": 0,
               "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS": 0}
    for row in proposed:
        chapter = row.get("modern_chapter")
        first = row.get("source_first_key")
        action = row.get("action")
        dest = row.get("expected_modern_target")
        ordinal = row.get("original_link_ordinal")
        if (not isinstance(chapter, str) or not isinstance(first, str)
                or not first.startswith(chapter+".") or action not in counted
                or not isinstance(dest, str) or not _REF.fullmatch(dest)
                or not isinstance(row.get("modern_anchor"), str)
                or not isinstance(row.get("linked_display_text"), str)):
            raise ValueError("Malformed source-owned modern link placement")
        key = (first, ordinal, dest)
        if key in seen:
            raise ValueError("Duplicate modern link placement from original source")
        seen.add(key)
        units = native["chapters"].get(chapter, {}).get("original_units", [])
        source_unit = next((g for g in units if g["first_key"] == first), None)
        identity = groups.get(first)
        if (source_unit is None or identity is None
                or identity["source_raw_sha256"] != source_unit["source_unit_sha256"]):
            raise ValueError("Unattested original K group for modern link placement")
        if action == "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS":
            if "original_link_ordinal" in row:
                raise ValueError("Cannot invent an original linked-element ordinal")
            witness = addition_by_key.get((first, dest))
            if (witness is None or
                    witness.get("modern_text_marker") != row["modern_anchor"]):
                raise ValueError("Added link lacks actual independent source witness disposition")
        else:
            if type(ordinal) is not int or not 1 <= ordinal <= identity["reference_count"]:
                raise ValueError("Original link placement lacks exact source occurrence ordinal")
            correction = correction_by_key.get((first, ordinal))
            if action == "COPY_EXACT_AUTHENTIC_SOURCE" and correction is not None:
                raise ValueError("Never copy a known wrong/spurious original hyperlink")
            if action == "CORRECT_AUTHENTIC_WRONG_TARGET":
                if (correction is None or correction.get("disposition") !=
                        "RETARGET_VERIFIED_CONTINUATION_REFERENCE"
                        or correction.get("corrected_target") != dest):
                    raise ValueError("Proposed corrected target is not independently documented")
        requested.add(first)
        counted[action] += 1
    if not reader.is_file() or not module_directory.is_dir() or module_id != "MHCC":
        raise ValueError("Only isolated published MHCC original SWORD reader is supported")
    private_original = {}
    private_table_ownership = {}
    private_title_ownership = {}
    env = os.environ.copy()
    env["SWORD_PATH"] = str(module_directory.resolve())
    def observe(kind: str, key: str, raw: bytes):
        if kind != "K" or key not in requested:
            return
        if key in private_original:
            raise ValueError("Original first-K raw source repeated")
        chapter = key.rsplit(".", 1)[0]
        original_unit = next(r for r in native["chapters"][chapter]["original_units"]
                             if r["first_key"] == key)
        identity = groups[key]
        if hashlib.sha256(raw).hexdigest() != original_unit["source_unit_sha256"]:
            raise ValueError("Original K body failed source-pinned SHA verification")
        refs = []
        node = ET.fromstring(b"<original>" + raw + b"</original>")
        for element in node.iter():
            if isinstance(element.tag, str) and element.tag.rsplit("}",1)[-1] == "reference":
                literal = element.attrib.get("osisRef")
                if not isinstance(literal, str) or not literal:
                    raise ValueError("Invalid original source-native hyperlink target")
                label = "".join(element.itertext())
                refs.append((literal, label))
        table_context=_original_reference_table_ownership(node)
        title_context=_original_reference_title_ownership(node)
        if (len(refs) != identity["reference_count"]
                or len(table_context)!=len(refs) or len(title_context)!=len(refs)):
            raise ValueError("Original link/authorial title-table ancestry count mismatch")
        for n, (literal, label) in enumerate(refs):
            if (hashlib.sha256(literal.encode("utf-8")).hexdigest() !=
                    identity["original_osisRef_sha256_in_document_order"][n]
                    or hashlib.sha256(label.encode("utf-8")).hexdigest() !=
                    identity["original_visible_link_label_sha256_in_document_order"][n]):
                raise ValueError("Original link identity or order differs from authenticated ledger")
        private_original[key] = refs
        private_table_ownership[key] = table_context
        private_title_ownership[key] = title_context
    proc = subprocess.Popen([str(reader.resolve()), module_id], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("No private full-original source stream")
        source_report, *_ = parse_native_raw_corpus(proc.stdout, on_entry=observe)
        proc.stdout.close()
        if proc.wait(timeout=45) != 0:
            raise ValueError("Original native SWORD stream failed to complete")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    if (source_report["all_native_raw_entries_ordered_sha256"] != pin
            or set(private_original) != requested):
        raise ValueError("Unverified original whole corpus SHA or missing original source K")
    doc = ET.fromstring(base_osis)
    if any(x.tag == f"{{{NS}}}reference" for x in doc.iter()):
        raise ValueError("Source-link overlay accepts only the fully UNLINKED candidate")
    modern_chapters = {
        node.attrib["osisID"]: node for node in doc.iter()
        if node.tag == f"{{{NS}}}chapter"
    }
    if len(modern_chapters) != 1189:
        raise ValueError("Source-linked OSIS needs all 1189 modern chapters")
    original_visible = "".join(doc.itertext())
    inserted = []
    auto_counts = {"automatically_inserted":0,
                   "automatically_inserted_ranges":0,
                   "automatically_inserted_outline_links":0,
                   "automatically_inserted_source_labels":0}
    for row in proposed:
        chapter, first = row["modern_chapter"], row["source_first_key"]
        units = native["chapters"][chapter]["original_units"]
        nth = next(i for i, item in enumerate(units) if item["first_key"] == first)
        sections = modern_chapters[chapter].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")
        if len(sections) != len(units):
            raise ValueError("Modern OSIS original authorial section count drift")
        section = sections[nth]
        if section.attrib.get("annotateRef") != _range(units[nth]["keys"]):
            raise ValueError("Modern OSIS commentary verse scope differs from native source")
        ordinal = row.get("original_link_ordinal")
        action = row["action"]
        if action == "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS":
            actual_target = row["expected_modern_target"]
        else:
            original_literal = private_original[first][ordinal-1][0]
            original_canon = canonical_only_for_comparison(original_literal)
            if action == "COPY_EXACT_AUTHENTIC_SOURCE":
                if original_canon != row["expected_modern_target"]:
                    raise ValueError("Original link copy target differs from native literal")
                actual_target = original_literal
            else:
                correction = correction_by_key[(first, ordinal)]
                if original_canon != correction["original_target"]:
                    raise ValueError("Correction original link was not its attested literal")
                actual_target = row["expected_modern_target"]
        _wrap_exact_authored_modern_text(
            section, anchor=row["modern_anchor"],
            display=row["linked_display_text"],
            occurrence=row["display_occurrence"], target=actual_target)
        inserted.append({"chapter": chapter, "original_source_first_key": first,
                         "original_link_ordinal": ordinal,
                         "placement_action": action,
                         "derived_target_sha256": hashlib.sha256(
                            actual_target.encode("utf-8")).hexdigest()})
    if auto_single_verse:
        already={(row["source_first_key"],row["original_link_ordinal"])
                 for row in proposed if row.get("original_link_ordinal") is not None}
        automatic, skips = _auto_single_verse_placements(
            private_original=private_original, groups=groups,
            modern_chapters=modern_chapters, native=native,
            blocked=already, corrections=correction_by_key,
            include_ranges=auto_ranges,
            include_outline_links=auto_outline_links,
            include_authentic_labels=auto_authentic_labels)
        # The original raw source and its complete identity hashes are already
        # validated by observe(). Retain original literal osisRef unchanged.
        for row in automatic:
            first=row["source_first_key"]
            chapter=row["modern_chapter"]
            units=native["chapters"][chapter]["original_units"]
            nth=next(i for i,u in enumerate(units) if u["first_key"]==first)
            section=modern_chapters[chapter].findall(
                f"./{{{NS}}}div[@annotateType='commentary']")[nth]
            literal=private_original[first][row["original_link_ordinal"]-1][0]
            is_outline=(row["action"]==
                        "AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE")
            if row["action"]=="AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE" or is_outline:
                normalized="RANGE:"+(literal[6:] if literal.startswith("Bible:")
                                      else literal)
                if (_source_same_chapter_verse_range(literal) is None or
                        normalized!=row["expected_modern_target"]):
                    raise ValueError("Source range autolink failed exact original target")
            elif canonical_only_for_comparison(literal)!=row["expected_modern_target"]:
                raise ValueError("Autolink changed original authenticated destination")
            location=section
            if is_outline:
                source_label=private_original[first][row["original_link_ordinal"]-1][1]
                confirmed=_source_first_K_outline_row_evidence(
                    literal=literal,label=source_label,first_key=first,
                    native_chapter=native["chapters"][chapter],
                    modern_chapter=modern_chapters[chapter])
                if not (confirmed["source_first_K_owns_link"] and
                        confirmed["unique_modern_outline_row_matches_source_target"] and
                        confirmed["original_visible_label_explicitly_names_same_verse_span"]):
                    raise ValueError("Original chapter-outline link cannot be relocated safely")
                location=_find_exact_modern_original_outline_range_cell(
                    modern_chapters[chapter],literal)
                if location is None or "".join(location.itertext()).strip()!=row["modern_anchor"]:
                    raise ValueError("Original outline verse table cell changed after review")
            _wrap_exact_authored_modern_text(
                location, anchor=row["modern_anchor"],
                display=row["linked_display_text"],
                occurrence="last", target=literal)
            inserted.append({
                "chapter":chapter,
                "original_source_first_key":first,
                "original_link_ordinal":row["original_link_ordinal"],
                "placement_action":row["action"],
                "derived_target_sha256":hashlib.sha256(
                    literal.encode("utf-8")).hexdigest(),
            })
        auto_counts = {"automatically_inserted":len(automatic),
                       "automatically_inserted_source_labels":sum(
                           row["action"]=="AUTO_UNIQUE_AUTHENTIC_ORIGINAL_SINGLE_VERSE_LABEL"
                           for row in automatic),
                       "automatically_inserted_ranges":sum(
                           row["action"]=="AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE"
                           for row in automatic),
                       "automatically_inserted_outline_links":sum(
                           row["action"]=="AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE"
                           for row in automatic),
                       **skips}
        proposed = list(proposed)+automatic
    if "".join(doc.itertext()) != original_visible:
        raise ValueError("Modern commentary wording changed while adding source links")
    # Diagnose authorial source outline-table references separately. A text
    # range in the original chapter outline must NOT be treated as a
    # passage cited by Henry inside modern explanatory paragraphs.
    context_count={"all_original_references":0,
                   "source_links_in_original_tables":0,
                   "source_links_outside_original_tables":0,
                   "source_links_in_original_titles":0,
                   "source_links_outside_original_titles":0,
                   "source_full_verse_ranges_inside_original_titles":0,
                   "source_full_verse_ranges_outside_original_titles":0,
                   "unplaced_full_verse_ranges_inside_original_titles":0,
                   "unplaced_full_verse_ranges_outside_original_titles":0,
                   "source_full_verse_ranges_inside_original_tables":0,
                   "source_full_verse_ranges_outside_original_tables":0,
                   "unplaced_full_verse_ranges_inside_original_tables":0,
                   "unplaced_full_verse_ranges_outside_original_tables":0}
    placed={(row["original_source_first_key"],row.get("original_link_ordinal"))
            for row in inserted if row.get("original_link_ordinal") is not None}
    for first,links in private_original.items():
        flags=private_table_ownership[first]
        title_flags=private_title_ownership[first]
        for i,((literal,_),in_table,in_title) in enumerate(
                zip(links,flags,title_flags),1):
            context_count["all_original_references"]+=1
            context_count["source_links_in_original_tables" if in_table else
                          "source_links_outside_original_tables"]+=1
            context_count["source_links_in_original_titles" if in_title else
                          "source_links_outside_original_titles"]+=1
            if _unrecognized_original_ref_class(literal)=="full_verse_range":
                context_count["source_full_verse_ranges_inside_original_titles" if in_title
                              else "source_full_verse_ranges_outside_original_titles"]+=1
                if (first,i) not in placed:
                    context_count["unplaced_full_verse_ranges_inside_original_titles" if in_title
                                  else "unplaced_full_verse_ranges_outside_original_titles"]+=1
                context_count["source_full_verse_ranges_inside_original_tables" if in_table
                              else "source_full_verse_ranges_outside_original_tables"]+=1
                if (first,i) not in placed:
                    context_count["unplaced_full_verse_ranges_inside_original_tables" if in_table
                                  else "unplaced_full_verse_ranges_outside_original_tables"]+=1
    if auto_single_verse and context_count["all_original_references"]!=1204:
        raise ValueError("Source table ancestry audit did not cover all source K hyperlinks")
    embedded = [x for x in doc.iter() if x.tag == f"{{{NS}}}reference"]
    if len(embedded) != len(proposed):
        raise ValueError("Wrong source-anchored link count after modern OSIS insertion")
    # Capture exact derived order after all insertions. Modern English placement
    # may legitimately differ from source-XML order, and one K body may contain
    # multiple independent links (including the duplicated 1 Cor. 5:7 source).
    # No literal original source targets or linked words enter this receipt.
    modern_groups = []
    outline_action="AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE"
    K_placements=[row for row in proposed if row["action"]!=outline_action]
    I_placements=[row for row in proposed if row["action"]==outline_action]
    linked_keys={row["source_first_key"] for row in K_placements}
    for first in sorted(linked_keys):
        ch = first.rsplit(".",1)[0]
        units = native["chapters"][ch]["original_units"]
        nth = next(i for i,u in enumerate(units) if u["first_key"]==first)
        scope = modern_chapters[ch].findall(
            f"./{{{NS}}}div[@annotateType='commentary']")[nth]
        nodes = [v for v in scope.iter()
                 if v.tag == f"{{{NS}}}reference"]
        targets = [v.attrib.get("osisRef") for v in nodes]
        labels = ["".join(v.itertext()) for v in nodes]
        expected_count = sum(row["source_first_key"] == first for row in K_placements)
        if (len(targets)!=expected_count or
                any(not isinstance(t,str) or not t for t in targets)
                or any(not label for label in labels)):
            raise ValueError("Grouped modern source-linked occurrence count changed")
        modern_groups.append({
            "original_source_first_key":first,
            "source_linked_modern_osisRef_hashes_in_actual_document_order":[
                hashlib.sha256(t.encode("utf-8")).hexdigest() for t in targets],
            "source_linked_modern_label_hashes_in_actual_document_order":[
                hashlib.sha256(label.encode("utf-8")).hexdigest() for label in labels],
            "modern_link_occurrences":len(targets)
        })
    if sum(r["modern_link_occurrences"] for r in modern_groups) != len(K_placements):
        raise ValueError("Modern K-owned linked group count differs from source review")
    intro_groups=[]
    outline_chapters={row["modern_chapter"] for row in I_placements}
    for chapter in sorted(outline_chapters):
        root=modern_chapters[chapter]
        sources=[v for v in root.findall(f"./{{{NS}}}div[@type='introduction']")
                 if len(v.findall(f"./{{{NS}}}title"))==1 and
                 v.find(f"./{{{NS}}}title").text=="Original chapter outline"]
        if len(sources)!=1:
            raise ValueError("Source-owned original chapter outline introduction is ambiguous")
        nodes=[v for v in sources[0].iter() if v.tag==f"{{{NS}}}reference"]
        expected_count=sum(row["modern_chapter"]==chapter for row in I_placements)
        if (len(nodes)!=expected_count or
                any(not v.get("osisRef") or not "".join(v.itertext()) for v in nodes)):
            raise ValueError("Original chapter outline link count or placement changed")
        intro_groups.append({
            "modern_chapter":chapter,
            "modern_intro_osisRef_hashes_in_actual_document_order":[
                hashlib.sha256(v.get("osisRef").encode("utf-8")).hexdigest()
                for v in nodes],
            "modern_intro_label_hashes_in_actual_document_order":[
                hashlib.sha256("".join(v.itertext()).encode("utf-8")).hexdigest()
                for v in nodes],
            "modern_link_occurrences":len(nodes),
            "source_ownership":"ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RELOCATED_TO_MODERN_CHAPTER_I",
        })
    if (sum(r["modern_link_occurrences"] for r in modern_groups)+
            sum(r["modern_link_occurrences"] for r in intro_groups)!=len(proposed)):
        raise ValueError("Modern K and chapter-I source-link counts differ from original")
    output = ET.tostring(doc, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)
    return output, {
        "status":"PRIVATE_REVIEWED_LINKED_FULL_CANON_OSIS_CANDIDATE_NOT_RELEASED",
        "full_original_native_corpus_sha256":pin,
        "modern_chapters_preserved":1189,
        "source_pinned_original_K_bodies_revisited":len(requested),
        "source_K_groups_with_links_inserted":len(linked_keys),
        "modern_chapter_I_outline_groups_with_links":len(outline_chapters),
        "modern_original_outline_links_inserted":len(I_placements),
        "modern_inline_links_inserted":len(embedded),
        "automatic_source_matched_references":auto_counts,
        "source_original_hyperlink_table_ownership_census":context_count,
        "actual_original_links_copied_without_correction":counted[
            "COPY_EXACT_AUTHENTIC_SOURCE"],
        "documented_wrong_original_links_retargeted":counted[
            "CORRECT_AUTHENTIC_WRONG_TARGET"],
        "source_witness_authored_missing_original_link_added":counted[
            "ADD_AUTHORED_UNLINKED_SOURCE_WITNESS"],
        "source_prose_modified":False,
        "modern_visible_prose_modified":False,
        "original_source_link_identity_hashes_and_order_verified":True,
        "modern_linked_osis_sha256":hashlib.sha256(output).hexdigest(),
        "published_source_1204_links_fully_transferred":False,
        "remaining_source_links_require_individual_placement_review":True,
        "modern_SWORD_readback_verified":False,
        "independent_editorial_semantic_signoff":False,
        "publication_authorized":False,
        "linked_source_K_groups_with_exact_derived_target_order":modern_groups,
        "linked_modern_chapter_I_outline_groups_with_exact_derived_order":intro_groups,
        "insertions":inserted,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-reader",required=True,type=Path)
    p.add_argument("--module-directory",required=True,type=Path)
    p.add_argument("--module-id",required=True)
    p.add_argument("--source-map",type=Path)
    p.add_argument("--expected-references",type=Path)
    p.add_argument("--modern-candidate",type=Path)
    p.add_argument("--whole-native-receipt",type=Path)
    p.add_argument("--disposition-manifest",type=Path)
    p.add_argument("--original-link-identity-report",type=Path)
    p.add_argument("--native-receipt",type=Path)
    p.add_argument("--repository-root",type=Path)
    p.add_argument("--base-unlinked-osis",type=Path)
    p.add_argument("--reviewed-link-placement-manifest",type=Path)
    p.add_argument("--auto-source-matched-single-verses",action="store_true")
    p.add_argument("--auto-source-matched-same-chapter-ranges",action="store_true")
    p.add_argument("--auto-original-first-K-outline-links",action="store_true")
    p.add_argument("--auto-authenticated-original-printed-single-verses",action="store_true")
    p.add_argument("--linked-osis",type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    if not a.native_reader.is_file() or not a.module_directory.is_dir():
        p.error("Trusted real native reader and installed source module directory required")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}",a.module_id):
        p.error("Unexpected SWORD module ID")
    if a.reviewed_link_placement_manifest is not None:
        if (any(x is not None for x in (
                a.whole_native_receipt, a.source_map, a.expected_references,
                a.modern_candidate)) or any(x is None for x in (
                a.base_unlinked_osis, a.linked_osis, a.disposition_manifest,
                a.native_receipt, a.original_link_identity_report,
                a.repository_root))):
            p.error("Full-canon linked OSIS needs authentic source, identity, "
                    "documented corrections and private source reader")
        osis, result = overlay_reviewed_private_links(
            base_osis=a.base_unlinked_osis.read_bytes(),
            placements=json.loads(a.reviewed_link_placement_manifest.read_text(
                encoding="utf-8")),
            native=json.loads(a.native_receipt.read_text(encoding="utf-8")),
            identities=json.loads(a.original_link_identity_report.read_text(
                encoding="utf-8")),
            dispositions=json.loads(a.disposition_manifest.read_text(
                encoding="utf-8")),
            repo_root=a.repository_root, reader=a.native_reader,
            module_directory=a.module_directory, module_id=a.module_id,
            auto_single_verse=a.auto_source_matched_single_verses,
            auto_ranges=a.auto_source_matched_same_chapter_ranges,
            auto_outline_links=a.auto_original_first_K_outline_links,
            auto_authentic_labels=a.auto_authenticated_original_printed_single_verses)
        a.linked_osis.parent.mkdir(parents=True,exist_ok=True)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.linked_osis.write_bytes(osis)
        a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
        print("BOUNDED SOURCE-LINKED MODERN MHCC OSIS PASS: " +
              str(result["modern_inline_links_inserted"]) +
              " source-verified inline links (" +
              str(result["automatic_source_matched_references"]["automatically_inserted"]) +
              " exact matches, including " +
              str(result["modern_original_outline_links_inserted"]) +
              " original first-K chapter outline links) across all 1189 chapters; " +
              "unmatched original hyperlinks still need editorial placement; NO release")
        return 0
    if ((a.auto_source_matched_single_verses or
         a.auto_source_matched_same_chapter_ranges or
         a.auto_original_first_K_outline_links or
         a.auto_authenticated_original_printed_single_verses) and
            a.reviewed_link_placement_manifest is None):
        p.error("Automatic source-linked citation lookup needs reviewed base manifests")
    if any(x is not None for x in (
            a.base_unlinked_osis, a.linked_osis)):
        p.error("Full-canon OSIS arguments require reviewed placement manifest")
    if a.disposition_manifest is not None:
        if (any(x is not None for x in (a.whole_native_receipt,
                                        a.source_map,
                                        a.expected_references,
                                        a.modern_candidate))
                or any(x is None for x in (
                    a.original_link_identity_report, a.native_receipt,
                    a.repository_root))):
            p.error("Correction disposition mode requires separate original receipts and root")
        result = validate_proposed_link_dispositions(
            manifest=json.loads(a.disposition_manifest.read_text(encoding="utf-8")),
            native=json.loads(a.native_receipt.read_text(encoding="utf-8")),
            identities=json.loads(a.original_link_identity_report.read_text(encoding="utf-8")),
            repository_root=a.repository_root)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("MHCC MODERN PROPOSED SOURCE LINK CORRECTIONS VERIFIED: original=" +
              str(result["reviewed_original_hyperlink_elements_in_groups"]) +
              " omitted=" + str(result["source_links_proposed_to_omit"]) +
              " retarget=" + str(result["source_links_proposed_to_retarget"]) +
              " added=" + str(result["secondary_witness_links_proposed_to_add"]) +
              "; no derivative link compilation or editorial publication approval")
        return 0
    if a.whole_native_receipt is not None:
        if any(x is not None for x in
               (a.source_map, a.expected_references, a.modern_candidate)):
            p.error("Whole-canon original-only mode cannot claim modern marker parity")
        result = run_whole_native_link_identity(
            reader=a.native_reader, root=a.module_directory,
            module_id=a.module_id, native_receipt=a.whole_native_receipt)
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print("SOURCE-NATIVE COMPLETE ORIGINAL LINK IDENTITY PASS: groups=" +
              str(result["original_unique_K_bodies_verified"]) +
              ", native links=" + str(result["original_reference_elements_verified"]) +
              "; destination and label hashes only; zero modern link approval")
        return 0
    if any(x is None for x in
           (a.source_map, a.expected_references, a.modern_candidate)):
        p.error("Pilot mode requires --source-map, --expected-references and --modern-candidate")
    source=json.loads(a.source_map.read_text(encoding="utf-8"))
    expectation=json.loads(a.expected_references.read_text(encoding="utf-8"))
    gate=SourceReferenceGate(source_map=source,expected_refs=expectation,
                             candidate=a.modern_candidate.read_text(encoding="utf-8"))
    env=os.environ.copy()
    env["SWORD_PATH"]=str(a.module_directory.resolve())
    proc=subprocess.Popen([str(a.native_reader.resolve()),a.module_id],
                           env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        if proc.stdout is None:
            raise ValueError("Missing native source stream")
        summary,*_=parse_native_raw_corpus(proc.stdout,on_entry=gate.observe)
        proc.stdout.close()
        if proc.wait(timeout=25)!=0:
            raise ValueError("Native stock-SWORD reader did not complete successfully")
        report=gate.report(summary)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("SOURCE-NATIVE REFERENCE IDENTITY PASS: "+
              str(report["source_unique_units_checked"])+" source units; "+
              str(report["original_reference_links_checked"])+" links; "+
              "raw labels/targets kept private; no derivative approval")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


if __name__=="__main__":
    raise SystemExit(main())
