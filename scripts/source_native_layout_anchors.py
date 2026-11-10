#!/usr/bin/env python3
"""Generic source-USFX structural start-anchor screen versus stock SWORD.

This is an intentionally conservative *reference-level triage*, not a proof
of position-exact paragraphs, lines, note/word anchors, or cross-verse spans.
Only source and compiled reference IDs/counters appear in the report.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re

from lxml import etree

from source_usfx_structure import audit_source_usfx

MAX_MARKERS = 300_000
MAX_EXAMPLES = 18
NOTES_OR_HEADINGS = frozenset({
    "f", "fe", "x", "ef", "ex", "note", "s", "ms", "mt", "mr",
    "d", "cl", "rem", "r", "toc",
})
VERSE = re.compile(r"[1-9][0-9]{0,4}\Z")


class SourceLayoutError(ValueError):
    """Ambiguous or untrusted source event positions; fail closed."""


def _skip_nested_annotation(node, book):
    cur = node.getparent()
    while cur is not None and cur is not book:
        if isinstance(cur.tag, str) and etree.QName(cur).localname in NOTES_OR_HEADINGS:
            return True
        cur = cur.getparent()
    return False


def source_usfx_layout_start_anchors(xml: bytes, mapping: list[tuple[str,str]]) -> dict:
    """Map source paragraph/poetry starts to next numbered verse in private memory.

    A start before the next verse is not necessarily *within* that verse;
    no source markup is converted, moved or discarded here.
    """
    source = audit_source_usfx(xml)
    if source["source_structural_issues"]:
        raise SourceLayoutError("Unresolved source structure prevents layout anchoring")
    if (not mapping or len(set(mapping)) != len(mapping)
            or len({x[0] for x in mapping}) != len(mapping)
            or len({x[1] for x in mapping}) != len(mapping)):
        raise SourceLayoutError("Ambiguous or duplicate source/native crosswalk")
    crosswalk = dict(mapping)
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False,
                             no_network=True, recover=False, huge_tree=False)
    try:
        root = etree.fromstring(xml, parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise SourceLayoutError("Cannot parse original source for layout anchors") from exc
    totals = Counter()
    source_anchors = {"paragraph":set(), "poetry":set()}
    private_start_events = []  # ref-only, never returned directly in stage report
    samples = {}
    hashers = {kind:sha256() for kind in source_anchors}
    unanchored = Counter()
    encountered = 0
    seen = set()

    for book in root.iter("book"):
        code = book.get("id")
        if code in seen or not code:
            raise SourceLayoutError("Repeated/unknown source book in layout scan")
        seen.add(code)
        if code not in crosswalk:
            # The stage-4 source index comparator independently rejects
            # unmapped authored books rather than silently dropping content.
            totals["unmapped_source_books_seen"] += 1
            continue
        chapter = None
        last_ref = None
        pending = []
        for node in book.iter():
            if not isinstance(node.tag, str):
                continue
            tag = etree.QName(node).localname
            if tag == "c":
                raw = node.get("id", "")
                if not raw.isdigit() or int(raw) < 1:
                    raise SourceLayoutError("Invalid authorial chapter position")
                chapter = int(raw)
                last_ref = None
            elif tag == "v":
                raw = node.get("id", "")
                if chapter is None or not VERSE.fullmatch(raw):
                    raise SourceLayoutError("Unsupported original verse marker in layout scan")
                ref = f"{crosswalk[code]}.{chapter}.{int(raw)}"
                for kind, prior in pending:
                    totals[f"{kind}_start_events"] += 1
                    source_anchors[kind].add(ref)
                    private_start_events.append((kind, prior, ref))
                    payload = f"{kind}:{prior or 'before_verse'}:{ref}".encode("ascii")
                    hashers[kind].update(len(payload).to_bytes(4,"big")+payload)
                    if len(samples.setdefault(kind, [])) < MAX_EXAMPLES:
                        samples[kind].append({"prior_ref":prior,"next_ref":ref})
                pending.clear()
                last_ref = ref
            elif tag in {"p","q"} and not _skip_nested_annotation(node, book):
                encountered += 1
                if encountered > MAX_MARKERS:
                    raise SourceLayoutError("Too many source layout markers")
                pending.append(("paragraph" if tag=="p" else "poetry",last_ref))
        for kind, prior in pending:
            private_start_events.append((kind,prior,None))
            unanchored[f"{kind}_without_later_numbered_verse"] += 1
            totals[f"{kind}_start_events_after_last_verse"] += 1
            if len(samples.setdefault(kind+"_trailing", [])) < MAX_EXAMPLES:
                samples[kind+"_trailing"].append({"prior_ref":prior})

    return {
        "schema_version":1,
        "original_usfx_sha256":sha256(xml).hexdigest(),
        "source_start_event_counts":dict(sorted(totals.items())),
        "source_start_ref_sets_private":source_anchors,
        "source_start_events_private":private_start_events,
        "source_start_order_sha256":{
            k:v.hexdigest() for k,v in sorted(hashers.items())
        },
        "source_start_event_samples_refs_only":samples,
        "source_unanchored_end_events":dict(sorted(unanchored.items())),
        "source_start_anchors_are_next_verse_estimates":True,
        "source_markup_not_modified":True,
    }


def compare_start_anchors(source:dict, native_census) ->dict:
    """Compare broad next-verse coverage, not event position equivalence."""
    para = source["source_start_ref_sets_private"]["paragraph"]
    poetry = source["source_start_ref_sets_private"]["poetry"]
    div = native_census.verse_refs_for("div")
    line = native_census.verse_refs_for("line")
    missing_para = sorted(para-div)
    missing_poetry = sorted(poetry-line)
    adjacent = Counter()
    prior_examples = {"paragraph":[], "poetry":[]}
    neither_examples = {"paragraph":[], "poetry":[]}
    # A source start belongs to the interval between two numbered verses;
    # markers at either neighboring native slot may be related, but matching
    # a neighbor cannot alone prove event type, order or exact word position.
    for kind, preceding, following in source["source_start_events_private"]:
        native = div if kind == "paragraph" else line
        if following is not None and following in native:
            adjacent[f"{kind}_native_marker_at_next_numbered_ref"] += 1
        elif preceding is not None and preceding in native:
            adjacent[f"{kind}_native_marker_at_previous_numbered_ref_only"] += 1
            if len(prior_examples[kind]) < MAX_EXAMPLES:
                prior_examples[kind].append({
                    "previous_ref":preceding, "next_ref":following
                })
        else:
            adjacent[f"{kind}_no_native_marker_at_either_neighbor"] += 1
            if len(neither_examples[kind]) < MAX_EXAMPLES:
                neither_examples[kind].append({
                    "previous_ref":preceding, "next_ref":following
                })
    return {
        "interval_adjacency_coverage_not_equivalence":dict(sorted(adjacent.items())),
        "sample_previous_neighbor_only_refs":prior_examples,
        "sample_no_neighbor_marker_refs":neither_examples,
        "source_adjacent_marker_matches_are_not_position_or_type_proof":True,
        "schema_version":1,
        "source_start_event_counts":source["source_start_event_counts"],
        "source_start_order_sha256":source["source_start_order_sha256"],
        "source_start_event_samples_refs_only":source["source_start_event_samples_refs_only"],
        "source_unanchored_end_events":source["source_unanchored_end_events"],
        "source_paragraph_next_verse_ref_count":len(para),
        "source_poetry_next_verse_ref_count":len(poetry),
        "native_numbered_verses_with_div":len(div),
        "native_numbered_verses_with_line_markup":len(line),
        "source_paragraph_next_verse_refs_with_native_div":len(para&div),
        "source_poetry_next_verse_refs_with_native_line":len(poetry&line),
        "source_paragraph_next_verse_refs_without_native_div":len(missing_para),
        "source_poetry_next_verse_refs_without_native_line":len(missing_poetry),
        "sample_paragraph_next_ref_without_native_div":missing_para[:MAX_EXAMPLES],
        "sample_poetry_next_ref_without_native_line":missing_poetry[:MAX_EXAMPLES],
        "direct_event_or_exact_position_equivalence_verified":False,
        "native_div_type_mapping_or_cross_verse_scope_verified":False,
        "editorial_layout_or_publication_approved":False,
        "warning":"Next-numbered-verse co-occurrence is a coarse structural screen; it does not establish a faithful conversion or identical paragraph/line/verse-zero positions.",
    }
