"""Source-bound chapter/body coverage research, not commentary rewriting.

Independently corroborate source chapter units and existing native keys; do
not infer missing authorial verse-level scope or export original prose.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from commentary_source_english_osis_alias import (
    read_existing_66_book_english_aliases, _canon_name,
)
from commentary_unresolved_lexical_triage import marked_word_token_indices
from commentary_xml_witness import _parse_reference, WORK_REF
from pilot_preflight import PilotError

from research.commentary.commentary_chapter_ref_labels import link_label_location
from research.commentary.commentary_lexical_overlap import independent_lexical_overlap


def independent_div2_chapter_body_evidence(document, native_registry: dict,
                                          unrecognized_cases: list[dict],
                                          stock_unknown_raw: dict[str, bytes] | None = None,
                                          original_visible_chapter_intro_raw: dict[str, bytes] | None = None) -> dict:
    """Collate chapter wrappers in canonical order, verifying book identities.

    Source order alone is never authority: each div1 must be the expected book
    with independently checked chapter count, a non-conflicting source book
    title and/or explicit source section annotations. Unmarked div2 paragraphs
    are evidence for a *chapter-unit candidate*, not automatically approval
    to assign its whole body to each verse in the stock digital edition.
    """
    chapter_maximums = native_registry["chapter_maximums"]
    native_by_book = defaultdict(list)
    for chapter_key in chapter_maximums:
        book, chapter_str = chapter_key.rsplit(".", 1)
        native_by_book[book].append(int(chapter_str))
    if any(chapters != list(range(1, len(chapters) + 1))
           for chapters in native_by_book.values()):
        raise PilotError("Actual native registry has discontinuous chapter enumeration")
    canonical_books = list(native_by_book)
    aliases, alias_registry_meta = read_existing_66_book_english_aliases()
    if not set(canonical_books).issubset(aliases):
        return {
            "status": "SOURCE_BOOK_ALIASES_NOT_REVIEWED_FOR_NATIVE_MODULE",
            "case_rows": [], "scope_authorized": False
        }
    chapters_div1 = []
    excluded_unattributed_div1 = 0
    for node in document.iter():
        if not isinstance(node.tag, str) or node.tag.rsplit("}", 1)[-1] != "div1":
            continue
        chapters = [x for x in node if
                    isinstance(x.tag, str) and x.tag.rsplit("}", 1)[-1] == "div2"]
        if not chapters:
            continue
        title = _canon_name(node.get("title", ""))
        title_names = [
            code for code, alias in aliases.items()
            if re.search(r"(?<!\w)" + re.escape(_canon_name(alias)) + r"(?!\w)", title)
        ]
        has_scripcom = any(
            isinstance(child.tag, str)
            and child.tag.rsplit("}", 1)[-1] == "scripCom"
            for child in node.iter()
        )
        if not title_names and not has_scripcom:
            excluded_unattributed_div1 += 1
            continue
        chapters_div1.append((node, chapters))
    if len(chapters_div1) != len(canonical_books):
        return {
            "status": "SOURCE_BOOK_LAYOUT_NOT_EXACT_NATIVE_BOOK_COUNT",
            "native_book_count": len(canonical_books),
            "source_book_divisions": len(chapters_div1),
            "case_rows": [], "scope_authorized": False
        }
    source_chapters = {}
    private_book_prefix_text = {}
    private_book_prefix_neighbors = {}
    private_book_prefix_ref_links = {}
    private_book_prefix_structure = {}
    explicit_source_chapters = {}
    ambiguous_source_heading_chapters = set()
    book_classes = Counter()
    book_evidence_rows = []
    for (div1, chapters), code in zip(chapters_div1, canonical_books):
        title = _canon_name(div1.get("title", ""))
        candidates = set()
        for book, alias in aliases.items():
            needle = _canon_name(alias)
            if re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", title):
                candidates.add(book)
        annotated_books = set()
        for marker in div1.iter():
            if not isinstance(marker.tag, str) or marker.tag.rsplit("}", 1)[-1] != "scripCom":
                continue
            kind, book = _parse_reference(marker.get("osisRef", ""))
            if book and kind in (
                "work_qualified_chapter", "work_qualified_verse",
                "work_qualified_same_book_verse_range"
            ):
                annotated_books.add(book)
        if len(candidates) > 1 or (candidates and code not in candidates):
            identity = "SOURCE_BOOK_TITLE_CONFLICT_OR_AMBIGUOUS"
        elif annotated_books and annotated_books != {code}:
            identity = "SOURCE_BOOK_ANNOTATION_CONFLICT"
        elif code in candidates and code in annotated_books:
            identity = "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH"
        elif code in candidates:
            identity = "SOURCE_BOOK_TITLE_MATCH"
        elif annotated_books == {code}:
            identity = "SOURCE_BOOK_MARKERS_MATCH"
        else:
            identity = "SOURCE_BOOK_IDENTITY_ORDINAL_ONLY_UNREVIEWED"
        if len(chapters) != len(native_by_book[code]):
            identity = "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
        book_classes[identity] += 1
        source_prefix_nodes = []
        for direct_child in div1:
            if isinstance(direct_child.tag, str) and direct_child.tag.rsplit("}", 1)[-1] == "div2":
                break
            source_prefix_nodes.append(direct_child)
        prefix_tag_counts = Counter(
            node.tag.rsplit("}", 1)[-1]
            for node in source_prefix_nodes if isinstance(node.tag, str)
        )
        prefix_chapter_markers = []
        prefix_heading_numbers = set()
        prefix_nonempty_paragraphs = 0
        for prefix_node in source_prefix_nodes:
            for element in prefix_node.iter():
                if not isinstance(element.tag, str):
                    continue
                kind = element.tag.rsplit("}", 1)[-1]
                if kind == "scripCom":
                    ref = element.get("osisRef", "")
                    typ, _ = _parse_reference(ref)
                    matched = WORK_REF.fullmatch(ref)
                    if typ == "work_qualified_chapter" and matched:
                        prefix_chapter_markers.append(matched.group(2))
                if kind in ("h2", "title"):
                    heading = "".join(element.itertext())
                    for number in re.findall(r"\bchapter\s+([1-9]\d*)\b", heading, re.I):
                        prefix_heading_numbers.add(int(number))
                if kind == "p":
                    prefix_nonempty_paragraphs += bool("".join(element.itertext()).strip())
        private_book_prefix_text[code] = " ".join(
            "".join(node.itertext())
            for element in source_prefix_nodes
            for node in element.iter()
            if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "p"
        )
        private_book_prefix_ref_links[code] = [
            {
                "text": "".join(node.itertext()),
                "attribute_name_types": list(node.attrib),
                "private_original_osisRef_target": node.get("osisRef", ""),
            }
            for element in source_prefix_nodes for node in element.iter()
            if isinstance(node.tag, str)
            and node.tag.rsplit("}", 1)[-1] == "scripRef"
        ]
        private_book_prefix_neighbors[code] = [
            ("source_div1_title_attribute", div1.get("title", "")),
            *(
                ("source_immediate_previous_heading_element",
                 "".join(element.itertext()))
                for element in source_prefix_nodes
                if isinstance(element.tag, str)
                and element.tag.rsplit("}", 1)[-1] in {"h1", "h2", "title"}
            ),
        ][:8]
        # Extra caution: several CCEL ThML editions put the first
        # chapter prose directly under the BOOK div1, before the first div2.
        # Only a complete one-chapter deficit + explicit nonconflicting
        # chapter numbering from chapter 2 onward can support that scope.
        # This remains an *independent digital witness*, not a publication
        # or text normalization permit.
        first_expected_chapter = 2
        numbered_source_div2_evidence = 0
        source_div2_heading_conflicts = 0
        source_first_div2_declares_chapter_two = False
        for offset, child in enumerate(chapters, start=first_expected_chapter):
            declared_numbers = set()
            for heading in child:
                if (isinstance(heading.tag, str)
                        and heading.tag.rsplit("}", 1)[-1] in ("h2", "title")):
                    declared_numbers.update(int(n) for n in re.findall(
                        r"\bchapter\s+([1-9]\d*)\b",
                        "".join(heading.itertext()), re.I
                    ))
            if declared_numbers:
                numbered_source_div2_evidence += 1
                if declared_numbers != {offset}:
                    source_div2_heading_conflicts += 1
            if offset == first_expected_chapter:
                source_first_div2_declares_chapter_two = (
                    declared_numbers == {first_expected_chapter}
                )
        first_prefix_compatible = (
            len(chapters) == len(native_by_book[code]) - 1
            and candidates == {code} and annotated_books == {code}
            and len(native_by_book[code]) >= 3
            and prefix_nonempty_paragraphs >= 1
            and source_first_div2_declares_chapter_two
            and numbered_source_div2_evidence >= 2
            and source_div2_heading_conflicts == 0
            and set(prefix_chapter_markers) <= {f"{code}.1"}
            and set(prefix_heading_numbers) <= {1}
        )
        private_book_prefix_structure[code] = {
            "missing_exactly_one_div2_with_book_prefix_prose":
                len(chapters) == len(native_by_book[code]) - 1
                and prefix_nonempty_paragraphs > 0,
            "first_div2_explicitly_declares_second_chapter":
                source_first_div2_declares_chapter_two,
            "nonconflicting_later_numeric_chapter_headings":
                numbered_source_div2_evidence,
            "conflicting_later_numeric_chapter_headings":
                source_div2_heading_conflicts,
            "all_source_book_identity_and_chapter_order_guards_pass":
                first_prefix_compatible,
            "original_book_prefix_text_not_reassigned": True,
        }
        book_evidence_rows.append({
            "native_book": code,
            "title_alias_candidate_books": sorted(candidates),
            "explicit_source_annotation_books": sorted(annotated_books),
            "source_direct_div2_count": len(chapters),
            "native_registry_chapter_count": len(native_by_book[code]),
            "identity_class": identity,
            "source_direct_nodes_before_first_div2": dict(sorted(prefix_tag_counts.items())),
            "source_prefix_chapter_scripCom_refs": sorted(set(prefix_chapter_markers)),
            "source_prefix_numeric_h2_chapters": sorted(prefix_heading_numbers),
            "source_prefix_nonempty_paragraphs": prefix_nonempty_paragraphs,
        })
        for chapter_number, div2 in enumerate(chapters, start=1):
            chapter = f"{code}.{chapter_number}"
            markers = [
                marker for marker in div2.iter()
                if isinstance(marker.tag, str)
                and marker.tag.rsplit("}", 1)[-1] == "scripCom"
            ]
            numbered = [
                marker for marker in markers
                if _parse_reference(marker.get("osisRef", ""))[0] in (
                    "work_qualified_verse", "work_qualified_same_book_verse_range"
                )
            ]
            chapter_markers = [
                marker for marker in markers
                if _parse_reference(marker.get("osisRef", ""))[0]
                == "work_qualified_chapter"
            ]
            marker_chapter_references = set()
            for marker in markers:
                kind, _ = _parse_reference(marker.get("osisRef", ""))
                if kind not in (
                    "work_qualified_chapter", "work_qualified_verse",
                    "work_qualified_same_book_verse_range"
                ):
                    continue
                match = WORK_REF.fullmatch(marker.get("osisRef", ""))
                if match:
                    for part in match.group(2).split("-"):
                        parts = part.split(".")
                        if len(parts) >= 2 and parts[1].isdigit():
                            marker_chapter_references.add(parts[0] + "." + parts[1])
            # Title text is inspected privately for *numerical* chapter
            # indicators only; it is not emitted in the report.
            heading_chapter_numbers = set()
            for head in div2:
                if not isinstance(head.tag, str) or head.tag.rsplit("}", 1)[-1] not in ("h2", "title"):
                    continue
                text = "".join(head.itertext())
                for number in re.findall(r"\bchapter\s+([1-9]\d*)\b", text, re.I):
                    heading_chapter_numbers.add(int(number))
            nonempty_paragraphs = sum(
                bool("".join(node.itertext()).strip())
                for node in div2.iter()
                if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "p"
            )
            source_chapters[chapter] = {
                "book_identity_class": identity,
                "source_marker_count": len(markers),
                "source_numbered_section_marker_count": len(numbered),
                "source_chapter_marker_count": len(chapter_markers),
                "source_nonempty_paragraph_count": nonempty_paragraphs,
                "source_annotated_chapter_references": sorted(marker_chapter_references),
                "source_h2_explicit_numeric_chapters": sorted(heading_chapter_numbers),
                "source_div2_text_sha256": sha256(
                    "".join(div2.itertext()).encode("utf-8")
                ).hexdigest(),
                "source_div2_original_text_retained": True,
                "source_div2_ordinal": chapter_number,
                "_private_source_visible_text": "".join(div2.itertext()),
                "_private_source_xml_div2_element": div2,
                "_private_original_scripref_links": [
                    {
                        "text": "".join(node.itertext()),
                        "attribute_name_types": list(node.attrib),
                        "private_original_osisRef_target": node.get("osisRef", ""),
                    }
                    for node in div2.iter()
                    if isinstance(node.tag, str)
                    and node.tag.rsplit("}", 1)[-1] == "scripRef"
                ],
                "_private_source_neighbor_candidates": [
                    ("source_div2_title_attribute", div2.get("title", "")),
                    ("source_div1_title_attribute", div1.get("title", "")),
                    *(
                        ("source_immediate_previous_heading_element",
                         "".join(head.itertext()))
                        for head in div2
                        if isinstance(head.tag, str)
                        and head.tag.rsplit("}", 1)[-1] in {"h2", "h1", "title"}
                    ),
                ][:8],
            }
            if (identity == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
                    and candidates == {code} and annotated_books == {code}
                    and len(heading_chapter_numbers) == 1):
                declared = next(iter(heading_chapter_numbers))
                target = f"{code}.{declared}"
                if (target in chapter_maximums
                        and marker_chapter_references <= {target}):
                    if target in explicit_source_chapters:
                        ambiguous_source_heading_chapters.add(target)
                    else:
                        explicit_source_chapters[target] = source_chapters[chapter]
    cases = []
    classes = Counter()
    candidates = [
        row for row in unrecognized_cases
        if row.get("first_verse_in_chapter", False)
        and row.get("number_of_occupied_native_slots_in_chapter") == 1
    ]
    for row in candidates:
        chapter = row["native_key"].rsplit(".", 1)[0]
        source = source_chapters.get(chapter)
        alignment_method = "SOURCE_NATIVE_DIV2_ORDINAL_AND_BOOK"
        if chapter in explicit_source_chapters or chapter in ambiguous_source_heading_chapters:
            source = (
                explicit_source_chapters.get(chapter)
                if chapter not in ambiguous_source_heading_chapters else None
            )
            alignment_method = "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        elif (source is not None and
              source["book_identity_class"] == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"):
            # The unverified div2 ordinal must never stand in for a chapter
            # omitted from this digital witness's division sequence.
            source = None
            alignment_method = "NO_SAFE_EXPLICIT_SOURCE_CHAPTER_MAPPING"
        if source is None:
            classification = "NO_SAFE_SOURCE_DIV2_FOR_NATIVE_CHAPTER"
        elif source["book_identity_class"] not in {
            "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH",
            "SOURCE_BOOK_TITLE_MATCH",
            "SOURCE_BOOK_MARKERS_MATCH",
            "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
        }:
            classification = "SOURCE_BOOK_OR_CHAPTER_ALIGNMENT_NEEDS_REVIEW"
        elif source["book_identity_class"] == "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY" and (
            alignment_method != "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        ):
            classification = "SOURCE_CHAPTER_COUNT_UNREVIEWED"
        elif source["source_h2_explicit_numeric_chapters"] and (
            int(chapter.rsplit(".", 1)[1])
            not in source["source_h2_explicit_numeric_chapters"]
        ):
            classification = "SOURCE_HEADING_CHAPTER_CONFLICT"
        elif source["source_numbered_section_marker_count"] > 0:
            classification = "SOURCE_DIV2_HAS_INDEPENDENT_VERSE_SECTIONS"
        elif source["source_nonempty_paragraph_count"] == 0:
            classification = "SOURCE_DIV2_NO_NONEMPTY_COMMENTARY_PARAGRAPHS"
        elif alignment_method == "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING":
            classification = "SOURCE_DIV2_UNDIVIDED_EXPLICIT_HEADING_CANDIDATE"
        else:
            classification = "SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE"
        lexical = None
        reference_targets = None
        if stock_unknown_raw and row["native_key"] in stock_unknown_raw:
            # For a source div2, compare that chapter's actual private source
            # unit; for a missing first div2, compare the prefix *as a probe*
            # and never silently call it the authored first chapter.
            source_text = (
                source["_private_source_visible_text"] if source is not None
                else private_book_prefix_text.get(chapter.split(".", 1)[0])
                if chapter.endswith(".1") else None
            )
            if source_text is not None:
                neighboring = (
                    source["_private_source_neighbor_candidates"] if source is not None
                    else private_book_prefix_neighbors.get(chapter.split(".", 1)[0], [])
                )
                # Keep all private source strings bounded before passing them to
                # a metadata-only XML source-context comparison.
                neighboring = [
                    (name, value) for name, value in neighboring
                    if isinstance(value, str) and len(value) <= 2048
                ]
                lexical = independent_lexical_overlap(
                    source_text, stock_unknown_raw[row["native_key"]],
                    source_neighbor_candidates=neighboring
                )
                source_links = (
                    source["_private_original_scripref_links"] if source is not None
                    else private_book_prefix_ref_links.get(chapter.split(".", 1)[0], [])
                )
                # The existing strict original-reference/stock-reference
                # comparator verifies literal source target pairing without
                # treating label resemblance as destination identity.
                reference_targets = link_label_location(
                    source_links, stock_unknown_raw[row["native_key"]]
                )
                one_word = lexical.get("isolated_one_word_xml_location")
                if one_word is not None:
                    if source is None:
                        source_position = "NO_SAFE_INDEPENDENT_SOURCE_UNIT"
                    else:
                        source_link_word_positions = set(marked_word_token_indices(
                            source["_private_source_xml_div2_element"], "scripRef",
                            source_text
                        ))
                        source_position = (
                            "SOURCE_SCRIPREF_LINK_LABEL"
                            if one_word["original_word_index_from_zero"]
                            in source_link_word_positions
                            else "SOURCE_COMMENTARY_TEXT_OUTSIDE_SCRIPREF"
                        )
                    one_word["original_source_word_markup_location"] = source_position
                    one_word["source_link_annotation_is_not_authorial_prose_parity"] = True
        prefix_proof = None
        if source is None and chapter.endswith(".1"):
            candidate_proof = private_book_prefix_structure.get(
                chapter.rsplit(".", 1)[0], {}
            )
            source_alignment = (
                lexical.get("ordered_word_alignment",{})
                if isinstance(lexical, dict) else {}
            )
            full_original_prose_retained = (
                source_alignment.get(
                    "original_plain_words_not_matched_in_exact_order"
                ) == 0
                and source_alignment.get(
                    "exact_unicode_longest_common_subsequence_word_count"
                ) == source_alignment.get("original_plain_word_tokens")
                and isinstance(lexical,dict)
                and lexical.get("overlap_class") == "HIGH_95_PLUS"
            )
            prefix_proof = {
                **candidate_proof,
                "source_book_prefix_prose_is_complete_in_original_K":
                    full_original_prose_retained,
                "source_book_prefix_first_chapter_attribution_approved":False,
            }
            if (candidate_proof.get(
                    "all_source_book_identity_and_chapter_order_guards_pass")
                    and full_original_prose_retained):
                classification = (
                    "SOURCE_BOOK_PREFIX_FIRST_CHAPTER_UNDIVIDED_CANDIDATE"
                )
        classes[classification] += 1
        cases.append({
            "independent_lexical_comparison": lexical,
            "independent_reference_target_comparison": reference_targets,
            "native_start": row["native_key"],
            "source_div2_structure_class": classification,
            "source_book_prefix_first_chapter_structural_witness": prefix_proof,
            "source_chapter_alignment_method": alignment_method,
            "source_div2_original_ordinal": source["source_div2_ordinal"] if source else None,
            "source_chapter_marker_count": source["source_chapter_marker_count"] if source else 0,
            "source_numbered_marker_count": source["source_numbered_section_marker_count"] if source else 0,
            "source_nonempty_paragraph_count": source["source_nonempty_paragraph_count"] if source else 0,
            "source_div2_text_sha256": source["source_div2_text_sha256"] if source else None,
            "source_annotated_chapters": source["source_annotated_chapter_references"] if source else [],
            "source_h2_numeric_chapters": source["source_h2_explicit_numeric_chapters"] if source else [],
            "stock_raw_sha256": row["raw_payload_sha256"],
            "source_text_to_stock_text_identity_proven": False,
            "approved_for_native_index_expansion": False,
        })
    # Compare inline scripture-link *targets* separately from displayed
    # words: an exact spelling match must never substitute for real OSIS
    # destination preservation. These are different pinned digital editions.
    reference_classes = Counter()
    reference_totals = Counter()
    reference_exception_rows = []
    missing_stock_link_label_locations = Counter()
    unmatched_source_target_label_locations = Counter()
    unpaired_literal_unique_anchor_candidates = 0
    for row in cases:
        refs = row.get("independent_reference_target_comparison")
        if refs is None:
            reference_classes["NOT_COMPARABLE"] += 1
            continue
        orig = refs["original_scripRef_with_nonempty_osisRef_target_count"]
        stock = refs["selected_stock_reference_elements_with_osisRef_attribute"]
        paired = (
            refs["original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"]
            + refs["original_scripRef_osisRef_work_qualifier_only_matches_in_stock"]
        )
        if paired > min(orig, stock):
            raise PilotError("Original/stock reference target pairing exceeds actual markup")
        unpaired_source = orig - paired
        unpaired_stock = stock - paired
        if refs["unpaired_original_source_target_occurrences"] != unpaired_source:
            raise PilotError("Independent original source target remainder misclassified")
        unmatched_source_target_label_locations.update(
            refs["unpaired_original_source_target_label_location_classes"]
        )
        unpaired_literal_unique_anchor_candidates += refs[
            "unpaired_unique_literal_unlinked_citation_label_candidate_count"
        ]
        reference_totals["original_source_nonempty_target_occurrences"] += orig
        reference_totals["stock_nonempty_target_occurrences"] += stock
        reference_totals["paired_target_occurrences_exact_or_literal_work_prefix"] += paired
        reference_totals["source_target_occurrences_not_paired_in_selected_stock"] += unpaired_source
        reference_totals["stock_target_occurrences_not_paired_in_selected_source"] += unpaired_stock
        if orig == stock == 0:
            classification = "BOTH_HAVE_NO_LINK_MARKUP"
        elif orig and not stock:
            classification = "SOURCE_LINK_MARKUP_NOT_PRESENT_IN_SELECTED_STOCK"
        elif not orig and stock:
            classification = "STOCK_ONLY_LINK_MARKUP"
        elif orig == stock == paired:
            classification = "ALL_LINK_TARGETS_MATCH_EXACT_OR_LITERAL_WORK_PREFIX"
        elif unpaired_source and not unpaired_stock:
            classification = "SOURCE_HAS_EXTRA_UNPAIRED_LINK_TARGETS"
        elif unpaired_stock and not unpaired_source:
            classification = "STOCK_HAS_EXTRA_UNPAIRED_LINK_TARGETS"
        else:
            classification = "BOTH_EDITIONS_HAVE_UNPAIRED_LINK_TARGETS"
        reference_classes[classification] += 1
        if classification == "SOURCE_LINK_MARKUP_NOT_PRESENT_IN_SELECTED_STOCK":
            # Every source citation in this precise class is target-unpaired:
            # its displayed label may remain visible as ordinary stock prose,
            # or be absent from the selected stock text. Never infer the
            # underlying destination from label resemblance alone.
            missing_stock_link_label_locations.update(
                refs["original_scripRef_to_stock_text_location_classes"]
            )
        if unpaired_source or unpaired_stock:
            reference_exception_rows.append({
                "native_start": row["native_start"],
                "source_target_occurrences_not_paired": unpaired_source,
                "stock_target_occurrences_not_paired": unpaired_stock,
                "selected_stock_reference_element_count":
                    refs["selected_stock_reference_element_count"],
                "classification": classification,
                "source_link_label_location_classes":
                    refs["original_scripRef_to_stock_text_location_classes"],
                "unpaired_source_link_label_location_classes":
                    refs["unpaired_original_source_target_label_location_classes"],
                "unique_literal_unlinked_original_source_label_candidates":
                    refs["unpaired_unique_literal_unlinked_citation_label_candidate_count"],
                "source_to_stock_reference_markup_parity_proven": False,
            })
    single_word_source_markup = Counter(
        row["independent_lexical_comparison"]["isolated_one_word_xml_location"].get(
            "original_source_word_markup_location", "NOT_LOCATED"
        )
        for row in cases
        if row["independent_lexical_comparison"] is not None
        and row["independent_lexical_comparison"].get("isolated_one_word_xml_location")
    )
    word_classes = Counter(
        row["independent_lexical_comparison"].get("overlap_class", "UNREVIEWED")
        for row in cases if row["independent_lexical_comparison"] is not None
    )
    ordered_word_classes = Counter(
        row["independent_lexical_comparison"]["ordered_word_alignment"][
            "exact_unicode_ordered_alignment_class"
        ]
        for row in cases if row["independent_lexical_comparison"] is not None
        and "ordered_word_alignment" in row["independent_lexical_comparison"]
    )
    # Reuse the *same* already verified book-title/chapter-ordinal
    # source mapping for original native I text, rather than guessing a
    # section scope from another edition's stray verse citation.
    introduction_witnesses = []
    for intro_chapter, raw in sorted((original_visible_chapter_intro_raw or {}).items()):
        source = source_chapters.get(intro_chapter)
        alignment = "SOURCE_NATIVE_DIV2_ORDINAL_AND_BOOK"
        if (intro_chapter in explicit_source_chapters
                or intro_chapter in ambiguous_source_heading_chapters):
            source = (
                explicit_source_chapters.get(intro_chapter)
                if intro_chapter not in ambiguous_source_heading_chapters else None
            )
            alignment = "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"
        if (source is not None
                and source["book_identity_class"] ==
                   "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY"
                and alignment != "EXPLICIT_NUMERIC_SOURCE_CHAPTER_HEADING"):
            source = None
        if source is None:
            classification = "NO_SAFE_WITNESS_DIV2_CHAPTER_MAPPING"
        elif source["book_identity_class"] not in {
                "SOURCE_BOOK_TITLE_AND_MARKERS_MATCH",
                "SOURCE_BOOK_TITLE_MATCH",
                "SOURCE_BOOK_MARKERS_MATCH",
                "SOURCE_CHAPTER_COUNT_DIFFERS_FROM_NATIVE_REGISTRY",
        }:
            classification = "SOURCE_BOOK_IDENTITY_UNVERIFIED"
        elif (source["source_h2_explicit_numeric_chapters"]
              and int(intro_chapter.rsplit(".", 1)[1])
              not in source["source_h2_explicit_numeric_chapters"]):
            classification = "SOURCE_CHAPTER_HEADING_DISAGREES_WITH_NATIVE_KEY"
        else:
            classification = "INDEPENDENT_DIGITAL_EDITION_CHAPTER_LOCATION_CORROBORATED"
        lex = (
            independent_lexical_overlap(source["_private_source_visible_text"], raw)
            if classification ==
               "INDEPENDENT_DIGITAL_EDITION_CHAPTER_LOCATION_CORROBORATED"
            else None
        )
        introduction_witnesses.append({
            "original_native_intro_chapter": intro_chapter,
            "classification": classification,
            "source_book_alignment_class": (
                source["book_identity_class"] if source is not None else None
            ),
            "source_chapter_alignment_method": alignment,
            "source_numbered_comment_section_markers": (
                source["source_numbered_section_marker_count"]
                if source is not None else None
            ),
            "source_chapter_comment_section_markers": (
                source["source_chapter_marker_count"]
                if source is not None else None
            ),
            "original_intro_vs_witness_word_overlap": lex,
            "is_not_source_edition_or_authorial_chapter_approval": True,
        })
    return {
        "status": "SOURCE_DIV2_STRUCTURE_COLLATED_NO_REINDEX_AUTHORIZATION",
        "independent_source_div2_text_bearing_native_intro_reviews":
            introduction_witnesses,
        "independent_stock_vs_source_reference_target_classes":
            dict(sorted(reference_classes.items())),
        "independent_stock_vs_source_reference_target_totals":
            dict(sorted(reference_totals.items())),
        "independent_stock_vs_source_reference_target_exception_rows":
            reference_exception_rows,
        "source_reference_labels_when_stock_has_no_link_markup":
            dict(sorted(missing_stock_link_label_locations.items())),
        "unpaired_original_source_reference_target_label_location_classes":
            dict(sorted(unmatched_source_target_label_locations.items())),
        "unpaired_unique_literal_reference_label_candidate_count":
            unpaired_literal_unique_anchor_candidates,
        "all_cross_edition_unpaired_source_targets_require_review":True,
        "source_reference_label_location_is_not_a_target_or_text_parity_check": True,
        "isolated_one_word_original_source_markup_location_classes":
            dict(sorted(single_word_source_markup.items())),
        "source_reference_target_completeness_not_proven": True,
        "independent_stock_vs_source_lexical_diagnostic_classes":
            dict(sorted(word_classes.items())),
        "independent_stock_vs_source_ordered_word_diagnostic_classes":
            dict(sorted(ordered_word_classes.items())),
        "source_book_divisions": len(chapters_div1),
        "unattributed_noncanonical_div1_with_div2_excluded": excluded_unattributed_div1,
        "native_book_count": len(canonical_books),
        "book_alignment_evidence_classes": dict(sorted(book_classes.items())),
        "book_alignment_evidence_rows": book_evidence_rows,
        "ambiguous_original_numeric_chapter_headings": sorted(ambiguous_source_heading_chapters),
        "reviewed_registry_evidence": alias_registry_meta,
        "candidate_classes": dict(sorted(classes.items())),
        "case_rows": cases,
        "derived_authorial_section_scope_proven": False,
        "original_xml_or_stock_modified": False
    }
