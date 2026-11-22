#!/usr/bin/env python3
"""Private authorial-USFX vs stock-SWORD raw note BODY diagnostics (#28).

Only explicitly mapped numbered-verse note bodies are compared. No note
text or original XML enters reports/logs. This is not proof of note callers,
anchors, types, reference targets, or original publication rights.
"""
from __future__ import annotations

from collections import Counter
from lxml import etree
import unicodedata

# No dependency on the parent full-corpus CLI: the latter imports this
# module, and import cycles would make both entrypoints unusable.
MAX_VERSE = 2 * 1024 * 1024
USFX_HEAD = frozenset({"s", "s1", "s2", "s3", "s4", "ms", "ms1",
                       "ms2", "mt", "mt1", "mt2", "mr", "d", "cl", "r", "rem"})
USFX_LABELS = frozenset({"vp", "va", "cp", "ca"})
USFX_SPEAKER_P_STYLES = frozenset({"sp"})

SOURCE_NOTES = frozenset({"f", "fe", "x", "ef", "ex", "note"})
MAX_NOTES = 150_000
MAX_FINDINGS = 30
MAX_NOTE_DEPTH = 256


class NoteEvidenceError(ValueError):
    """Ambiguous source/native note ownership or untrusted raw fragment."""


def _text(node):
    return "".join(node.itertext())


def _fold(value):
    return " ".join(unicodedata.normalize("NFC", value).split())


def _caller_shape(value):
    """Allowlisted categorical original caller shape; never reveal labels."""
    if value in (None, "", "+", "-"):
        return "automatic_or_unspecified"
    if len(value) == 1 and "a" <= value <= "z":
        return "single_lowercase_ascii_letter"
    if len(value) == 1 and "A" <= value <= "Z":
        return "single_uppercase_ascii_letter"
    if value.isascii() and value.isdecimal():
        return "ascii_decimal"
    if len(value) == 1 and not value.isalnum():
        return "single_symbol"
    return "other_unreviewed_literal"



def collect_usfx_numbered_notes(
    xml: bytes, mapping: list[tuple[str, str]],
    *, attributes_out: dict | None = None,
) -> tuple[dict, dict]:
    """Inventory notes by source verse without merging or inventing verse IDs.

    Count notes outside numbered verses separately. No content escapes.
    """
    if not 0 < len(xml) <= 128 * 1024 * 1024:
        raise NoteEvidenceError("Empty or oversized original source")
    try:
        parsed = etree.ElementTree(etree.fromstring(
            xml, etree.XMLParser(resolve_entities=False, load_dtd=False,
                                 no_network=True, recover=False, huge_tree=False)))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise NoteEvidenceError("Invalid original USFX") from exc
    if (parsed.docinfo.doctype or parsed.docinfo.internalDTD or
            parsed.docinfo.externalDTD or parsed.getroot().tag != "usfx"):
        raise NoteEvidenceError("Unexpected source root or DTD")
    root = parsed.getroot()
    pairs = dict(mapping)
    if not pairs or len(pairs) != len(mapping) or len(set(pairs.values())) != len(mapping):
        raise NoteEvidenceError("Ambiguous source book crosswalk")
    notes = {}
    extra = Counter()
    total = 0
    seen_books = set()
    for book in root.iter("book"):
        code = book.get("id")
        if not code or code in seen_books:
            raise NoteEvidenceError("Missing or repeated source book")
        seen_books.add(code)
        if code not in pairs:
            extra["unmapped_source_book_count"] += 1
            continue
        chapter = None
        active = None

        def walk(node, depth=0):
            nonlocal chapter, active, total
            if depth > MAX_NOTE_DEPTH:
                raise NoteEvidenceError("Excessive source XML nesting")
            if not isinstance(node.tag, str):
                return
            tag = etree.QName(node).localname
            style = node.get("sfm", "")
            if tag in SOURCE_NOTES:
                if any(isinstance(x.tag, str) and etree.QName(x).localname in {"v", "c"}
                       for x in node.iterdescendants()):
                    raise NoteEvidenceError("Note encloses verse or chapter milestone")
                total += 1
                if total > MAX_NOTES:
                    raise NoteEvidenceError("Too many authored notes")
                body = _text(node)
                if len(body.encode("utf-8")) > MAX_VERSE:
                    raise NoteEvidenceError("Oversized authorial note")
                if active is None:
                    extra["notes_outside_numbered_verses"] += 1
                else:
                    notes.setdefault(active, []).append((tag, body))
                    if attributes_out is not None:
                        attributes_out.setdefault(active, []).append({
                            "source_tag": tag,
                            "caller": node.get("caller"),
                            "explicit_targets": tuple(
                                child.get("tgt") for child in node.iterdescendants()
                                if isinstance(child.tag, str)
                                and etree.QName(child).localname == "ref"
                                and child.get("tgt")
                            ),
                        })
                return
            if (tag in USFX_HEAD or tag in USFX_LABELS or
                    (tag == "p" and style in USFX_SPEAKER_P_STYLES)):
                if any(isinstance(x.tag, str) and etree.QName(x).localname in {"v", "c"}
                       for x in node.iterdescendants()):
                    raise NoteEvidenceError("Editorial container encloses verse milestone")
                # Notes in editorial headings are not numbered Scripture notes.
                extra["excluded_editorial_containers"] += 1
                return
            if tag == "c":
                value = node.get("id", "")
                if not value.isdecimal() or int(value) < 1:
                    raise NoteEvidenceError("Ambiguous source chapter")
                chapter, active = int(value), None
            elif tag == "v":
                value = node.get("id", "")
                if chapter is None or not value.isdecimal() or int(value) < 1:
                    raise NoteEvidenceError("Ambiguous source verse")
                active = f"{pairs[code]}.{chapter}.{int(value)}"
                if active in notes:
                    # A repeated verse with a note cannot be assigned safely.
                    raise NoteEvidenceError("Repeated source note-bearing verse")
            elif tag == "ve":
                active = None
            for child in node:
                walk(child, depth + 1)
        walk(book)
    return notes, {
        "mapped_source_numbered_note_count": sum(map(len, notes.values())),
        "mapped_source_note_bearing_verse_count": len(notes),
        "unmapped_source_book_count": extra["unmapped_source_book_count"],
        "notes_outside_numbered_verses": extra["notes_outside_numbered_verses"],
        "excluded_editorial_containers": extra["excluded_editorial_containers"],
        "source_note_caller_type_anchor_reference_target_verified": False,
    }


def parse_native_numbered_notes(
    raw: bytes, *, attributes_out: list | None = None,
) -> list[tuple[str, str]]:
    """Strict raw XML; reject non-self-contained fragments, never repair them."""
    if len(raw) > MAX_VERSE or b"<!DOCTYPE" in raw.upper() or b"<?xml" in raw.lower():
        raise NoteEvidenceError("Untrusted or oversized native raw fragment")
    try:
        root = etree.fromstring(
            b"<private_notes>" + raw + b"</private_notes>",
            etree.XMLParser(resolve_entities=False, load_dtd=False,
                            no_network=True, recover=False, huge_tree=False))
    except etree.XMLSyntaxError as exc:
        raise NoteEvidenceError("Native note-bearing fragment is not valid standalone XML") from exc
    if any(isinstance(x, etree._Entity) for x in root.iter()):
        raise NoteEvidenceError("Unresolved XML entity in native notes")
    out = []
    for node in root.iter():
        if isinstance(node.tag, str) and etree.QName(node).localname == "note":
            body = _text(node)
            if len(body.encode("utf-8")) > MAX_VERSE:
                raise NoteEvidenceError("Oversized native note")
            out.append(("note", body))
            if attributes_out is not None:
                attributes_out.append({
                    "osis_type": node.get("type"),
                    "n": node.get("n"),
                    "explicit_targets": tuple(
                        child.get("osisRef") for child in node.iterdescendants()
                        if isinstance(child.tag, str)
                        and etree.QName(child).localname == "reference"
                        and child.get("osisRef")
                        and child.get("type") != "annotateRef"
                    ),
                })
            if len(out) > MAX_NOTES:
                raise NoteEvidenceError("Too many native notes")
    return out


class NoteAudit:
    """Bounded private comparison; no original note content in result."""

    def __init__(
        self, source_notes: dict[str, list[tuple[str, str]]],
        *, source_attributes: dict | None = None,
    ):
        self.source_notes = source_notes
        self.source_attributes = source_attributes
        if source_attributes is not None:
            if set(source_attributes) != set(source_notes):
                raise NoteEvidenceError("Source note/annotation owner inventories disagree")
            if any(len(source_attributes[k]) != len(v)
                   for k, v in source_notes.items()):
                raise NoteEvidenceError("Source note/annotation counts disagree")
        self.annotation_counts = Counter()
        self.annotation_findings = {}
        self.counts = Counter()
        self.findings = {}
        self.native_seen = set()
        self.native_note_count = 0

    def inspect(self, ref: str, raw: bytes):
        if ref in self.native_seen:
            raise NoteEvidenceError("Duplicate native numbered verse")
        self.native_seen.add(ref)
        src = self.source_notes.get(ref, [])
        native_attributes = [] if self.source_attributes is not None else None
        try:
            native = parse_native_numbered_notes(raw, attributes_out=native_attributes)
        except NoteEvidenceError:
            self.counts["native_fragment_unparseable_notes_unverified"] += 1
            self._finding("native_fragment_unparseable_notes_unverified", {
                "ref": ref, "kind": "native_fragment_unparseable_notes_unverified",
                "source_note_count": len(src),
            })
            return
        self.native_note_count += len(native)
        if self.source_attributes is not None:
            self._inspect_annotation_attributes(
                ref, self.source_attributes.get(ref, ()), native_attributes)
        if self.native_note_count > MAX_NOTES:
            raise NoteEvidenceError("Native note total exceeds safe bound")
        if not src and not native:
            self.counts["both_without_numbered_notes"] += 1
            return
        self.counts["numbered_verses_with_notes_in_either_side"] += 1
        if len(src) != len(native):
            kind = "note_count_differs"
        elif all(s[1] == n[1] for s, n in zip(src, native)):
            kind = "ordered_note_body_characters_equal"
        elif all(_fold(s[1]) == _fold(n[1]) for s, n in zip(src, native)):
            kind = "ordered_note_bodies_equal_after_whitespace_folding"
        else:
            kind = "ordered_note_bodies_differ"
        self.counts[kind] += 1
        if kind != "ordered_note_body_characters_equal":
            self._finding(kind, {
                "ref": ref, "kind": kind,
                "source_note_count": len(src), "native_note_count": len(native),
            })

    def _annotation_finding(self, category, ref, source_count, native_count):
        bucket = self.annotation_findings.setdefault(category, [])
        if len(bucket) < 4:
            bucket.append({
                "ref": ref, "kind": category,
                "source_note_count": source_count,
                "native_note_count": native_count,
            })

    def _inspect_annotation_attributes(self, ref, source, native):
        if len(source) != len(native):
            self.annotation_counts["note_count_alignment_unavailable"] += 1
            self._annotation_finding(
                "note_count_alignment_unavailable", ref, len(source), len(native))
            return
        for authored, compiled in zip(source, native):
            original_kind = authored["source_tag"]
            # USFX x/ex are dedicated cross-reference notes. The other
            # source styles are NOT assumed equivalent to arbitrary OSIS
            # note categories, but crossReference vs non-crossReference
            # can be independently observed in both representations.
            if original_kind in {"x", "ex"}:
                source_is_crossref = True
            elif original_kind in {"f", "fe", "ef"}:
                source_is_crossref = False
            else:
                source_is_crossref = None
            native_is_crossref = compiled["osis_type"] == "crossReference"
            if source_is_crossref is None:
                self.annotation_counts["source_note_type_unknown"] += 1
            elif source_is_crossref == native_is_crossref:
                self.annotation_counts["cross_reference_class_agrees"] += 1
            else:
                self.annotation_counts["cross_reference_class_differs"] += 1
                self._annotation_finding(
                    "cross_reference_class_differs", ref, len(source), len(native))
            caller, printed = authored["caller"], compiled["n"]
            self.annotation_counts[
                "source_caller_shape_" + _caller_shape(caller)] += 1
            self.annotation_counts[
                "native_note_n_present" if printed else "native_note_n_absent"] += 1
            # "+" and "-" select automatic/no marker in USFM; never
            # compare them literally with SWORD's generated note label.
            if caller in {None, "", "+", "-"}:
                self.annotation_counts["source_caller_automatic_absent_or_unverifiable"] += 1
            elif not printed:
                self.annotation_counts["literal_source_caller_no_native_n"] += 1
                self._annotation_finding(
                    "literal_source_caller_no_native_n", ref, len(source), len(native))
            elif caller == printed:
                self.annotation_counts["literal_caller_string_equal"] += 1
            else:
                self.annotation_counts["literal_caller_string_differs"] += 1
                self._annotation_finding(
                    "literal_caller_string_differs", ref, len(source), len(native))
            source_targets = authored["explicit_targets"]
            native_targets = compiled["explicit_targets"]
            if not source_targets and not native_targets:
                self.annotation_counts["neither_side_has_explicit_machine_target"] += 1
            elif source_targets == native_targets:
                # Same raw strings do not prove resolved canonical verse
                # targets, conversion mapping or SWORD link navigation.
                self.annotation_counts["explicit_target_raw_strings_equal"] += 1
            elif source_targets and not native_targets:
                self.annotation_counts["authored_explicit_target_absent_in_native"] += 1
                self._annotation_finding(
                    "authored_explicit_target_absent_in_native", ref,
                    len(source), len(native))
            elif native_targets and not source_targets:
                self.annotation_counts["native_target_without_authorial_machine_target"] += 1
            else:
                self.annotation_counts["explicit_target_raw_strings_differ"] += 1
                self._annotation_finding(
                    "explicit_target_raw_strings_differ", ref,
                    len(source), len(native))

    def _finding(self, category, row):
        bucket = self.findings.setdefault(category, [])
        if len(bucket) < 6:
            bucket.append(row)

    def finish(self):
        source_only = sorted(set(self.source_notes) - self.native_seen)
        priority = ("note_count_differs", "ordered_note_bodies_differ",
                    "native_fragment_unparseable_notes_unverified",
                    "ordered_note_bodies_equal_after_whitespace_folding")
        findings = [row for kind in priority for row in self.findings.get(kind, [])]
        findings = findings[:MAX_FINDINGS]
        self.counts["source_note_bearing_verses_without_native_slot"] = len(source_only)
        return {
            "status": "numbered_source_to_native_note_body_diagnostic_not_editorial_approval",
            "source_numbered_note_count": sum(map(len, self.source_notes.values())),
            "native_parseable_numbered_note_count": self.native_note_count,
            "classifications": dict(sorted(self.counts.items())),
            "first_findings_without_note_text": findings,
            "source_note_bearing_refs_without_native_slots": source_only[:MAX_FINDINGS],
            "source_note_body_exact_full_parity_verified": False,
            "source_note_callers_anchors_types_and_crossreference_targets_verified": False,
            "source_note_position_within_verse_verified": False,
            "note_annotation_structure_diagnostic": {
                "classifications": dict(sorted(self.annotation_counts.items())),
                "first_material_findings_no_note_text": [
                    item
                    for category in (
                        "cross_reference_class_differs",
                        "literal_caller_string_differs",
                        "literal_source_caller_no_native_n",
                        "authored_explicit_target_absent_in_native",
                        "explicit_target_raw_strings_differ",
                        "note_count_alignment_unavailable",
                    )
                    for item in self.annotation_findings.get(category, [])
                ][:MAX_FINDINGS],
                "source_note_type_equivalence_verified": False,
                "source_callers_and_note_anchor_positions_verified": False,
                "source_to_compiled_reference_targets_resolved_verified": False,
                "note_reordering_or_absorbed_verse_notes_verified": False,
            },
            "unmapped_books_and_intros_verified": False,
            "published_or_editorially_approved": False,
        }
