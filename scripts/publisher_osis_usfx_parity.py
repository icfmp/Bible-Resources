#!/usr/bin/env python3
"""Compare publisher-pinned OSIS and eBible-pinned USFX without content output.

The two files are independently authored/published representations of a
claimed edition. Never assume equal verse labels, note callers or metadata.
This observer is a prerequisite to choosing a rebuild source; it does not
alter, normalize, republish or certify an edition.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unicodedata

from lxml import etree

from bible_intake import ROOT, acquire, load_manifest
from lsg_source_compare import read_source_xml
from publisher_osis_observation import read_pinned_publisher_osis
from source_native_maintext_probe import authored_usfx_main_text
from source_native_notes_audit import collect_usfx_numbered_notes
from source_native_note_positions import original_usfx_note_anchors
from source_native_scope import read_crosswalk
from source_osis_inventory import source_inventory, _source_tree, OSIS
from stable_sword_refs import KEY

MAX_SAMPLE = 18
MAX_NOTE_TEXT = 2 * 1024 * 1024
EXCLUDED_MAIN = frozenset({"note", "title", "header"})

# Report hard source-identity failures before prolific stylistic note deltas.
# A global flat first-N sample can otherwise mask the *only* missing verse.
FINDING_PRIORITY = (
    "usfx_reference_absent_in_official_publisher",
    "publisher_reference_absent_in_ebible_usfx",
    "shared_scripture_nonspace_character_difference",
    "shared_note_count_difference",
    "source_note_anchor_position_difference",
    "lost_explicit_usfx_machine_target",
    "source_reference_target_difference",
    "source_note_caller_label_difference",
    "note_body_folded_difference",
)


def _bounded_priority_findings(findings: dict, limit: int = MAX_SAMPLE * 4):
    """Bounded metadata-only reviewer samples, prioritizing critical identity gaps."""
    order = {name: position for position, name in enumerate(FINDING_PRIORITY)}
    return [row for kind in sorted(findings,
                                   key=lambda name: (order.get(name, len(order)), name))
            for row in findings[kind]][:limit]


class PublisherSourceParityError(ValueError):
    """Untrusted, contradictory or unsafe original source evidence."""


def _nonspace(value: str) -> str:
    return "".join(c for c in value if not c.isspace())


def _fold(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC",value).split())


def _caller_class(value: str | None):
    if not value:
        return "missing"
    if len(value)==1 and "a" <= value <= "z":
        return "single_lowercase_ascii_letter"
    if len(value)==1 and "A" <= value <= "Z":
        return "single_uppercase_ascii_letter"
    if value.isascii() and value.isdecimal():
        return "ascii_decimal"
    if len(value)==1 and not value.isalnum():
        return "single_symbol"
    return "other_unreviewed_literal"


def original_osis_verses_and_notes(xml: bytes):
    """Independently reconstruct verse prose, note bodies and note anchors.

    Only explicit verse IDs are used. Verse milestones must pair exactly;
    neither malformed tags nor unknown source text is silently discarded.
    """
    # This already rejects wrong namespace, DTD and duplicate/out-of-order
    # verse milestones under the approved original-source OSIS grammar.
    source_keys, structural = source_inventory(xml)
    root = _source_tree(xml)
    books = root.findall(".//" + OSIS + "div[@type='book']")
    if not books or len(books)>250:
        raise PublisherSourceParityError("Unrecognized publisher OSIS book divisions")
    text = {}
    notes = {}
    extra = Counter()
    seen_books = set()
    for book in books:
        book_id = book.get("osisID")
        if (not isinstance(book_id,str) or not book_id
                or book_id in seen_books):
            raise PublisherSourceParityError("Duplicate or unreviewed OSIS book ID")
        seen_books.add(book_id)
        current = None
        codepoints = 0
        verse_container = []

        def append(fragment):
            nonlocal codepoints
            if current is not None and fragment:
                text[current].append(fragment)
                codepoints += sum(not character.isspace() for character in fragment)

        def visit(node, depth=0):
            nonlocal current, codepoints
            if depth > 256:
                raise PublisherSourceParityError("Excessive official OSIS nesting")
            if not isinstance(node.tag,str):
                return
            local=etree.QName(node).localname
            if local in EXCLUDED_MAIN:
                if any(x.tag == OSIS+"verse" for x in node.iterdescendants()):
                    raise PublisherSourceParityError(
                        "Publisher heading/note encloses verse numbering")
                if local == "note":
                    body="".join(node.itertext())
                    if len(body.encode("utf-8")) > MAX_NOTE_TEXT:
                        raise PublisherSourceParityError("Oversized official source note")
                    if current is None:
                        extra["notes_outside_numbered_verses"] += 1
                    else:
                        # Preserve original labels and linked explicit targets
                        # privately; only safe aggregates leave this module.
                        notes[current].append({
                            "body":body,
                            "caller":node.get("n"),
                            "type":node.get("type"),
                            "point":codepoints,
                            "targets":tuple(
                                x.get("osisRef") for x in node.iterdescendants()
                                if x.tag == OSIS+"reference" and x.get("osisRef")
                            ),
                        })
                return

            is_container=False
            if node.tag == OSIS+"verse":
                closing=node.get("eID")
                start=node.get("sID")
                reference=node.get("osisID")
                if closing:
                    if current != closing or start or reference:
                        raise PublisherSourceParityError(
                            "Mispaired publisher OSIS verse milestone")
                    current=None
                    return
                if not reference or KEY.fullmatch(reference) is None:
                    raise PublisherSourceParityError(
                        "Invalid publisher OSIS numbered verse identifier")
                if (start and start != reference) or current is not None:
                    raise PublisherSourceParityError(
                        "Overlapping publisher OSIS verse scope")
                if reference in text or not reference.startswith(book_id+"."):
                    raise PublisherSourceParityError(
                        "Publisher OSIS verse duplicates or leaves its book")
                text[reference]=[]
                notes[reference]=[]
                current=reference
                codepoints=0
                is_container=not bool(start)
                if is_container:
                    verse_container.append(reference)
            append(node.text)
            for child in node:
                visit(child, depth+1)
                append(child.tail)
            if is_container:
                if current != verse_container.pop():
                    raise PublisherSourceParityError(
                        "Publisher OSIS container verse cannot be closed")
                current=None

        visit(book)
        if current is not None or verse_container:
            raise PublisherSourceParityError("Unclosed publisher OSIS verse/book boundary")
    if set(text)!=set(source_keys.splitlines()):
        raise PublisherSourceParityError(
            "Independent source inventory and text reader disagree on verse scope")
    if len(seen_books)!=structural["source_book_count"]:
        raise PublisherSourceParityError(
            "Original OSIS book metadata disagrees with independent inspector")
    strings={ref:"".join(parts) for ref,parts in text.items()}
    if any(len(s.encode("utf-8"))>MAX_NOTE_TEXT for s in strings.values()):
        raise PublisherSourceParityError("Oversized publisher Bible verse")
    return strings,notes,{
        "publisher_book_count":len(seen_books),
        "publisher_numbered_verse_count":len(strings),
        "publisher_numbered_note_count":sum(map(len,notes.values())),
        "publisher_notes_outside_numbered_verses":
            extra["notes_outside_numbered_verses"],
        "source_osis_verse_key_sha256":structural["source_keys_sha256"],
        "source_osis_schema_version":1,
    }


def compare_original_sources(
    usfx_verses: dict, usfx_notes: dict, usfx_attrs: dict,
    usfx_positions: dict,
    publisher_verses: dict, publisher_notes: dict,
    official_meta: dict,
):
    """Metadata-only full union comparison with bounded canonical refs."""
    if (set(usfx_verses)!=set(usfx_positions)
            or set(publisher_verses)!=set(publisher_notes)
            or set(usfx_notes)!=set(usfx_attrs)
            or set(usfx_notes)-set(usfx_verses)):
        raise PublisherSourceParityError("Input source inventories are internally inconsistent")
    for source in (usfx_verses,publisher_verses):
        if not source or any(KEY.fullmatch(ref) is None for ref in source):
            raise PublisherSourceParityError("Unsafe source reference identifier")
    counts=Counter()
    findings={}
    digest=sha256()

    def note_sample(kind, ref, **extra):
        bucket=findings.setdefault(kind,[])
        if len(bucket)<MAX_SAMPLE:
            bucket.append({"reference":ref,"finding":kind,**extra})

    ekeys=set(usfx_verses)
    okeys=set(publisher_verses)
    missing_official=sorted(ekeys-okeys)
    missing_usfx=sorted(okeys-ekeys)
    counts["usfx_numbered_verse_count"]=len(ekeys)
    counts["publisher_numbered_verse_count"]=len(okeys)
    counts["usfx_only_reference_count"]=len(missing_official)
    counts["publisher_only_reference_count"]=len(missing_usfx)
    counts["shared_numbered_verse_count"]=len(ekeys&okeys)
    for ref in missing_official[:MAX_SAMPLE]:
        note_sample("usfx_reference_absent_in_official_publisher",ref)
    for ref in missing_usfx[:MAX_SAMPLE]:
        note_sample("publisher_reference_absent_in_ebible_usfx",ref)

    for ref in sorted(ekeys&okeys):
        e,o=usfx_verses[ref],publisher_verses[ref]
        if _nonspace(e)==_nonspace(o):
            counts["shared_verse_nonspace_characters_equal"]+=1
        else:
            counts["shared_verse_nonspace_characters_differ"]+=1
            note_sample("shared_scripture_nonspace_character_difference",ref,
                        usfx_nonspace_length=len(_nonspace(e)),
                        official_nonspace_length=len(_nonspace(o)))
        payload=json.dumps([ref,sha256(_nonspace(e).encode()).hexdigest(),
                            sha256(_nonspace(o).encode()).hexdigest()],
                            separators=(",",":"),ensure_ascii=True).encode()
        digest.update(len(payload).to_bytes(4,"big")+payload)
        src=usfx_notes.get(ref,())
        official=publisher_notes[ref]
        if len(src)!=len(official):
            counts["shared_verse_note_count_differs"]+=1
            note_sample("shared_note_count_difference",ref,
                        usfx_notes=len(src),official_notes=len(official))
            continue
        counts["shared_verse_note_count_matches"]+=1
        oldattrs=usfx_attrs.get(ref,())
        oldpoints=usfx_positions[ref]
        if len(oldattrs)!=len(src) or len(oldpoints)!=len(src):
            raise PublisherSourceParityError("USFX source notes/callers/points disagree")
        for idx,((oldtag,oldbody),oldatt,oldpoint,newnote) in enumerate(zip(
                src,oldattrs,oldpoints,official),start=1):
            counts["source_note_pairs_checked"]+=1
            if _fold(oldbody)==_fold(newnote["body"]):
                counts["note_body_words_punctuation_equal_after_space_folding"]+=1
            else:
                counts["note_body_folded_different"]+=1
                note_sample("note_body_folded_difference",ref,one_based_note=idx)
            if oldatt["caller"] == newnote["caller"]:
                counts["source_note_caller_labels_equal"]+=1
            else:
                counts["source_note_caller_labels_differ"]+=1
                note_sample("source_note_caller_label_difference",ref,
                            one_based_note=idx,
                            usfx_shape=_caller_class(oldatt["caller"]),
                            official_shape=_caller_class(newnote["caller"]))
            if _nonspace(e)==_nonspace(o):
                if oldpoint==newnote["point"]:
                    counts["note_anchor_punctuation_ordinal_equal"]+=1
                else:
                    counts["note_anchor_punctuation_ordinal_different"]+=1
                    note_sample("source_note_anchor_position_difference",ref,
                                one_based_note=idx,
                                usfx_nonspace_ordinal=oldpoint,
                                official_nonspace_ordinal=newnote["point"])
            else:
                counts["note_anchor_uncomparable_due_to_scripture_difference"]+=1
            original_targets=oldatt["explicit_targets"]
            publisher_targets=newnote["targets"]
            if original_targets and not publisher_targets:
                counts["usfx_explicit_target_absent_in_publisher"]+=1
                note_sample("lost_explicit_usfx_machine_target",ref,
                            one_based_note=idx)
            elif publisher_targets and not original_targets:
                counts["publisher_has_links_not_encoded_in_usfx"]+=1
                counts["publisher_total_explicit_links"]+=len(publisher_targets)
            elif original_targets!=publisher_targets:
                counts["both_explicit_target_sequences_differ"]+=1
                note_sample("source_reference_target_difference",ref,
                            one_based_note=idx)
            else:
                counts["explicit_target_sequences_equal"]+=1

    results={
        "schema_version":1,
        "status":("exact_index_main_text_note_caller_precheck"
                  if not missing_official and not missing_usfx
                  and not counts["shared_verse_nonspace_characters_differ"]
                  and not counts["shared_verse_note_count_differs"]
                  and not counts["source_note_caller_labels_differ"]
                  and not counts["note_body_folded_different"]
                  and not counts["note_anchor_punctuation_ordinal_different"]
                  and not counts["usfx_explicit_target_absent_in_publisher"]
                  and not counts["both_explicit_target_sequences_differ"]
                  else "material_publisher_osis_usfx_differences_require_review"),
        "original_source_comparison_counts":dict(sorted(counts.items())),
        "official_source_metadata":official_meta,
        "bounded_reference_and_note_ordinal_findings_only":
            _bounded_priority_findings(findings),
        "common_verse_nonspace_stream_comparison_sha256":digest.hexdigest(),
        "publisher_revision_same_as_usfx_verification":False,
        "publisher_original_layout_notes_targets_and_verse0_approved":False,
        "safe_for_automatic_source_switch_or_rebuild":False,
        "source_osis_and_usfx_bytes_never_uploaded":True,
        "publisher_original_note_caller_values_not_exposed":True,
        "not_publication_approval":True,
    }
    return results


def run(resource_id: str):
    cfg=load_manifest(resource_id)
    if cfg["source"]["format"]!="USFX":
        raise PublisherSourceParityError(
            "Secondary publisher OSIS comparison requires original USFX research source")
    with tempfile.TemporaryDirectory(prefix="bible-publisher-parity-") as scratch:
        temp=Path(scratch)
        receipts,archives=acquire(cfg,temp,source=True,sword=False)
        usfx,usfx_xml_receipt=read_source_xml(
            archives["source"],source_format="usfx")
        pairs=read_crosswalk(ROOT/cfg["crosswalk"])
        verses,_scope=authored_usfx_main_text(usfx,pairs)
        attrs={}
        notes,_metadata=collect_usfx_numbered_notes(
            usfx,pairs,attributes_out=attrs)
        anchors=original_usfx_note_anchors(usfx,pairs,verses,notes)
        official=read_pinned_publisher_osis(resource_id)
        official_verses,official_notes,official_meta=original_osis_verses_and_notes(
            official)
        report=compare_original_sources(
            verses,notes,attrs,anchors,
            official_verses,official_notes,official_meta)
        report["resource_id"]=resource_id
        report["official_publisher_osis_sha256"]=sha256(official).hexdigest()
        report["original_ebible_source_zip_sha256"]=receipts["source"]["sha256"]
        report["original_ebible_source_member_sha256"]=usfx_xml_receipt["sha256"]
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    if args.report.is_symlink() or args.report.exists() or not args.report.parent.is_dir():
        parser.error("Use a new report file in a real directory")
    report=run(args.resource_id)
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    counts=report["original_source_comparison_counts"]
    print("Original publisher OSIS vs eBible USFX:",report["status"])
    print("Numbered reference keys:",counts["publisher_numbered_verse_count"],
          "/",counts["usfx_numbered_verse_count"])
    print("Shared main-text nonspace differences:",
          counts.get("shared_verse_nonspace_characters_differ",0))
    print("Source authorial note caller label mismatches:",
          counts.get("source_note_caller_labels_differ",0))
    print("This is NOT source-edition identity, reconstruction or publication approval.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
