#!/usr/bin/env python3
"""Original ThML marker boundaries versus *occupied* native SWORD K-key runs.

Source annotation boundaries and identical compiled raw-key runs are separate
witnesses. Numeric verse continuity, rightful verse-range placement, source
prose identity, paragraph structure and electronic edition identity remain
unproven. All original strings, original marker references and native keys
stay private. Only source lines, SHA-256 hashes, booleans and closed classes
may appear in the permanent audit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from commentary_xml_witness import _parse_reference, WORK_REF, OSIS_LOC
from pilot_preflight import PilotError

MAX_RAW_K_KEYS=50_000
MAX_REVIEW_UNITS=20
SHA_RE=re.compile(r"[0-9a-f]{64}\Z")


def local_tag(node) -> str:
    if node is None or not isinstance(node.tag,str):
        return "_none"
    tag=node.tag.rsplit("}",1)[-1]
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}",tag):
        raise PilotError("Unreviewed original ThML structural tag name")
    return tag


def original_marker_boundary(marker, div, reference: str, start: str) -> dict:
    """Source XML siblings only; does not infer missing verse or marker."""
    if (local_tag(marker)!="scripCom" or local_tag(div)!="div"
            or marker.getnext() is not div or marker.getparent() is not div.getparent()
            or marker.get("osisRef","") != reference):
        raise PilotError("Original ThML marker/reference/body witnesses do not agree")
    kind,book=_parse_reference(reference)
    if kind not in {"work_qualified_verse","work_qualified_same_book_verse_range"}:
        raise PilotError("Unreviewed original source verse/range marker kind")
    work=WORK_REF.fullmatch(reference)
    if not work or work.group(2).split("-",1)[0] != start:
        raise PilotError("Original marker start disagrees with its pinned source key")
    prev=marker.getprevious()
    prev_prev=prev.getprevious() if local_tag(prev)=="div" else None
    next_node=div.getnext()
    following_kind="not_followed_by_scripCom_sibling"
    following_same_book=False
    following_same_chapter=False
    if local_tag(next_node)=="scripCom":
        following_kind,following_book=_parse_reference(next_node.get("osisRef",""))
        if following_kind.startswith("unreviewed_"):
            raise PilotError("Original next source marker has unknown reference grammar")
        following_same_book=following_book==book
        next_ref=WORK_REF.fullmatch(next_node.get("osisRef",""))
        if next_ref and following_same_book:
            following_start=next_ref.group(2).split("-",1)[0]
            following_same_chapter=(
                following_start.rsplit(".",1)[0]==start.rsplit(".",1)[0]
                if following_kind!="work_qualified_chapter"
                else following_start==start.rsplit(".",1)[0]
            )
    range_end_is_same_chapter=False
    if kind=="work_qualified_same_book_verse_range":
        parts=work.group(2).split("-",1)
        if len(parts)!=2:
            raise PilotError("Source range marker lost reviewed endpoints")
        range_end_is_same_chapter=(
            parts[0].rsplit(".",1)[0]==parts[1].rsplit(".",1)[0]
        )
    parent=marker.getparent()
    return {
        "original_annotation_reference_kind":kind,
        "original_range_ends_in_same_chapter":range_end_is_same_chapter,
        "source_marker_parent_tag":local_tag(parent),
        "source_body_direct_child_tag_counts":dict(sorted(Counter(
            local_tag(child) for child in div if isinstance(child.tag,str)
        ).items())),
        "preceding_sibling_tag_before_source_marker":local_tag(prev),
        "preceding_sibling_was_div_preceded_by_scripCom":
            local_tag(prev)=="div" and local_tag(prev_prev)=="scripCom",
        "immediately_following_sibling_after_source_body_tag":local_tag(next_node),
        "immediately_following_original_marker_reference_kind":following_kind,
        "immediately_following_marker_same_book":following_same_book,
        "immediately_following_marker_same_chapter":following_same_chapter,
        "source_original_marker_and_body_unmodified":True,
    }


class NativeRawRunBoundaryInventory:
    """Record actual K keys, digest and chapter; assess source cases *after* audit."""

    def __init__(self):
        self.entries=defaultdict(list)
        self.total_k=0
        self.total_I=0

    def observe(self,kind: str,key: str,raw:bytes) -> None:
        if kind=="I":
            self.total_I+=1
            return
        if kind!="K":
            return
        if self.total_k >= MAX_RAW_K_KEYS:
            raise PilotError("Native SWORD K-key sequence exceeds structural review limit")
        if not isinstance(key,str) or not re.fullmatch(
            r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*",key
        ):
            raise PilotError("Original native numbered key grammar unreviewed")
        if not isinstance(raw,bytes):
            raise PilotError("Native compiled raw payload must be original bytes")
        book=key.split(".",1)[0]
        chapter=key.rsplit(".",1)[0]
        self.entries[book].append((key,chapter,sha256(raw).hexdigest()))
        self.total_k+=1

    def report(self,source:dict,case_receipts:list[dict]) -> dict:
        if (not isinstance(case_receipts,list) or
                not 1 <= len(case_receipts) <= MAX_REVIEW_UNITS or
                self.total_k+ self.total_I == 0):
            raise PilotError("Original native range-boundary case inventory unavailable")
        source_by_identity={}
        for start,units in source.items():
            for unit in units:
                ident=(unit["original_source_line"],unit["original_full_reference_sha256"],
                       unit["original_text_sha256"])
                if ident in source_by_identity:
                    raise PilotError("Repeated original line/hash source marker identity")
                source_by_identity[ident]=(start,unit)
        response=[]
        source_counts=Counter()
        run_counts=Counter()
        for case in case_receipts:
            ident=(case["original_source_line"],case["original_full_reference_sha256"],
                   case["original_body_sha256"])
            if not all(SHA_RE.fullmatch(s) for s in ident[1:]) or (
                type(ident[0]) is not int or ident[0]<1 or ident not in source_by_identity
            ):
                raise PilotError("Original source case lacks verified line and full hashes")
            start,original=source_by_identity[ident]
            pinned_raw=case["stock_raw_sha256"]
            if not isinstance(pinned_raw,str) or not SHA_RE.fullmatch(pinned_raw):
                raise PilotError("Original selected compiled stock raw SHA missing")
            book=start.split(".",1)[0]
            keys=self.entries.get(book,[])
            exact=[i for i,(key,chapter,digest) in enumerate(keys) if key==start]
            if len(exact)!=1:
                raise PilotError("Selected source start not present uniquely among original stock K keys")
            selected_index=exact[0]
            if keys[selected_index][2]!=pinned_raw:
                raise PilotError("Selected original stock raw does not match pinned SHA")
            left=selected_index
            right=selected_index
            while left>0 and keys[left-1][2]==pinned_raw:
                left-=1
            while right+1<len(keys) and keys[right+1][2]==pinned_raw:
                right+=1
            same_hash_indices=[i for i,(_k,_c,dig) in enumerate(keys) if dig==pinned_raw]
            if not same_hash_indices:
                raise PilotError("Original same-book compiled raw not found")
            separate_runs=1
            for i,j in zip(same_hash_indices,same_hash_indices[1:]):
                if j!=i+1:
                    separate_runs+=1
            run_size=right-left+1
            other_raw_slots=len(same_hash_indices)-run_size
            if run_size>len(same_hash_indices) or separate_runs<1:
                raise PilotError("Original native raw repeat contiguous boundary count impossible")
            source_structure=original.get("private_source_marker_boundary")
            if not isinstance(source_structure,dict):
                raise PilotError("Original source marker boundary not witnessed")
            same_chapter_count=sum(
                chapter==start.rsplit(".",1)[0]
                for (_key,chapter,_dig) in keys[left:right+1]
            )
            # Compare the *actual ThML-declared* source range endpoints
            # against the full native raw run, without inferring that
            # independently occupied SWORD keys establish source versification.
            explicit_end=original.get("private_original_declared_range_end_key")
            if (not isinstance(explicit_end,str) or
                    not OSIS_LOC.fullmatch(explicit_end) or
                    not OSIS_LOC.fullmatch(start)):
                raise PilotError("Unreviewed source original verse-range endpoint")
            start_c, source_first_verse=start.rsplit(".",1)
            end_c, source_last_verse=explicit_end.rsplit(".",1)
            if (start_c!=end_c or
                    not 0 < int(source_first_verse) <= int(source_last_verse) or
                    int(source_last_verse)-int(source_first_verse)+1 > 500):
                raise PilotError("Original source range endpoints exceed reviewed one-chapter scope")
            start_verse=int(source_first_verse)
            last_verse=int(source_last_verse)
            # Actual numbered K occupation, never a reconstructed verse grid.
            native_declared_span=[
                (key,chapter,digest)
                for key,chapter,digest in keys
                if chapter==start_c and start_verse<=int(key.rsplit(".",1)[-1])<=last_verse
            ]
            if not native_declared_span:
                raise PilotError("Original source selected start not found in genuine numbered span")
            native_span_keys={key for key,_chapter,_digest in native_declared_span}
            run_keys={key for key,_chapter,_digest in keys[left:right+1]}
            raw_in_span=sum(digest==pinned_raw for _key,_chapter,digest in native_declared_span)
            native_run_before_source_start=sum(
                chapter==start_c and int(key.rsplit(".",1)[-1])<start_verse
                for key,chapter,_digest in keys[left:right+1]
            )
            native_run_after_source_end=sum(
                chapter==start_c and int(key.rsplit(".",1)[-1])>last_verse
                for key,chapter,_digest in keys[left:right+1]
            )
            original_marker_starts_on_run=sum(
                len(source_units)
                for original_start,source_units in source.items()
                if original_start in run_keys
            )
            true_numeric_native_K_continuity=all(
                first_chapter==second_chapter and
                int(second_key.rsplit(".",1)[-1])==int(first_key.rsplit(".",1)[-1])+1
                for (first_key,first_chapter,_),(second_key,second_chapter,_)
                in zip(keys[left:right],keys[left+1:right+1])
            )
            native={
                "source_line":ident[0],
                "original_full_reference_sha256":ident[1],
                "original_body_sha256":ident[2],
                "selected_native_raw_sha256":pinned_raw,
                "original_source_marker_boundary":source_structure,
                "native_K_occurrences_with_same_raw_in_source_book":len(same_hash_indices),
                "native_K_consecutive_occupied_key_run_length":run_size,
                "native_K_run_consecutive_occupied_keys_before_selected":selected_index-left,
                "native_K_run_consecutive_occupied_keys_after_selected":right-selected_index,
                "native_K_run_key_count_in_same_selected_chapter":same_chapter_count,
                "native_K_run_has_keys_in_another_chapter_same_book":
                    same_chapter_count!=run_size,
                "native_K_run_other_identical_raw_keys_outside_selected_run":other_raw_slots,
                "native_K_separate_identical_raw_runs_in_same_book":separate_runs,
                "original_source_declared_end_key_sha256":
                    sha256(explicit_end.encode("utf-8")).hexdigest(),
                "original_explicit_verse_range_declared_numeric_verse_count":
                    last_verse-start_verse+1,
                "original_declared_range_native_occupied_K_key_count":len(native_declared_span),
                "original_declared_range_native_K_same_raw_as_selected_count":raw_in_span,
                "original_declared_range_native_K_other_raw_count":
                    len(native_declared_span)-raw_in_span,
                "original_declared_range_start_K_occupied":start in native_span_keys,
                "original_declared_range_end_K_occupied":explicit_end in native_span_keys,
                "original_declared_end_K_key_inside_selected_raw_run":
                    explicit_end in run_keys,
                "native_raw_run_first_K_key_equals_original_range_start":
                    keys[left][0]==start,
                "native_raw_run_last_K_key_equals_original_range_end":
                    keys[right][0]==explicit_end,
                "native_raw_run_occupied_K_keys_equal_occupied_K_keys_within_declared_original_range":
                    run_keys==native_span_keys,
                "native_raw_run_K_keys_before_original_range_start":
                    native_run_before_source_start,
                "native_raw_run_K_keys_after_original_range_end":
                    native_run_after_source_end,
                "actual_source_annotations_starting_at_K_keys_inside_same_native_raw_run":
                    original_marker_starts_on_run,
                "native_raw_run_K_key_numbers_are_truly_consecutive_within_one_chapter":
                    true_numeric_native_K_continuity,
                "native_run_first_key_sha256":sha256(keys[left][0].encode()).hexdigest(),
                "native_run_last_key_sha256":sha256(keys[right][0].encode()).hexdigest(),
                "native_key_immediately_before_raw_run_sha256":
                    sha256(keys[left-1][0].encode()).hexdigest() if left>0 else None,
                "native_raw_immediately_before_raw_run_sha256":
                    keys[left-1][2] if left>0 else None,
                "native_key_immediately_after_raw_run_sha256":
                    sha256(keys[right+1][0].encode()).hexdigest() if right+1<len(keys) else None,
                "native_raw_immediately_after_raw_run_sha256":
                    keys[right+1][2] if right+1<len(keys) else None,
                "native_K_consecutiveness_means_enumerated_occupied_keys_not_numeric_verse_continuity":True,
                "native_raw_repetition_does_not_authorize_original_authorial_range":True,
            }
            source_counts[source_structure["immediately_following_sibling_after_source_body_tag"]]+=1
            run_counts["single_occupied_K_raw_run" if run_size==1 else
                       "multiple_occupied_K_keys_share_adjacent_raw"]+=1
            if native["native_K_run_has_keys_in_another_chapter_same_book"]:
                run_counts["selected_raw_run_crosses_chapter_boundary"]+=1
            if other_raw_slots:
                run_counts["identical_raw_occurs_in_separate_K_runs"]+=1
            if native["native_raw_run_occupied_K_keys_equal_occupied_K_keys_within_declared_original_range"]:
                run_counts["occupied_native_raw_run_equals_occupied_original_range_span"]+=1
            else:
                run_counts["occupied_native_raw_run_differs_from_occupied_original_range_span"]+=1
            if native["native_raw_run_K_key_numbers_are_truly_consecutive_within_one_chapter"]:
                run_counts["native_occupied_K_run_is_also_numeric_verse_continuous"]+=1
            else:
                run_counts["native_occupied_K_run_has_numeric_verse_gap_or_chapter_change"]+=1
            response.append(native)
        if (len(response)!=len(case_receipts) or
                sum(source_counts.values())!=len(response) or
                run_counts["single_occupied_K_raw_run"]+
                run_counts["multiple_occupied_K_keys_share_adjacent_raw"]!=len(response) or
                run_counts["occupied_native_raw_run_equals_occupied_original_range_span"]+
                run_counts["occupied_native_raw_run_differs_from_occupied_original_range_span"]!=len(response) or
                run_counts["native_occupied_K_run_is_also_numeric_verse_continuous"]+
                run_counts["native_occupied_K_run_has_numeric_verse_gap_or_chapter_change"]!=len(response)):
            raise PilotError("Native and original source boundaries not fully reconciled")
        return {
            "source_marker_case_count":len(response),
            "actual_native_K_occupied_keys_in_full_corpus":self.total_k,
            "actual_native_I_intro_keys_in_full_corpus":self.total_I,
            "original_marker_following_source_sibling_tag_classes":dict(sorted(source_counts.items())),
            "selected_native_raw_run_structure_classes":dict(sorted(run_counts.items())),
            "original_source_marker_native_run_sha256_and_metadata_only_cases":
                sorted(response,key=lambda z:(z["source_line"],z["original_full_reference_sha256"])),
            "comparison_to_original_declared_range_uses_only_genuine_occupied_K_keys":True,
            "native_K_run_is_only_consecutive_occupied_keys_not_numeric_verses":True,
            "original_ThML_scripCom_marker_and_stock_SWORD_verse_key_are_not_equivalent_structural_authorities":True,
            "original_content_markup_and_edition_parity_verified":False,
        }


def compare_longer_original_source_to_occupied_native_runs(
        source: dict, native_inventory: NativeRawRunBoundaryInventory,
        selected_cases: list[tuple[str, dict]]) -> dict:
    """Reconcile EVERY source-longer-than-stock case to its original native K run.

    Reuse the independently tested native boundary inspector in bounded chunks;
    a linked SWORD K run and an authorial ThML scripCom range are *different*
    structural authorities. This is a location/structure observation only:
    never interpret source-added words as actually omitted original prose.
    Original words, reference strings, OSIS XML and native raw bytes never
    leave the private runner. Only line numbers, hashes and closed classes do.
    """
    if (not isinstance(source, dict) or not isinstance(native_inventory,
            NativeRawRunBoundaryInventory) or not isinstance(selected_cases, list)
            or len(selected_cases) > 500):
        raise PilotError("Unreviewed source-longer case inventory bound")
    counters = Counter()
    by_book = Counter()
    book_classes = defaultdict(Counter)
    sibling_tags = Counter()
    proof_rows = []
    seen = set()
    for start, case in selected_cases:
        if (not isinstance(start, str) or not OSIS_LOC.fullmatch(start)
                or not isinstance(case, dict)):
            raise PilotError("Source-longer case lacks canonical original identity")
        identity = (
            case.get("original_source_line"),
            case.get("original_full_reference_sha256"),
            case.get("original_body_sha256"),
        )
        if (type(identity[0]) is not int or identity[0] < 1
                or not all(isinstance(value, str) and SHA_RE.fullmatch(value)
                           for value in identity[1:])
                or identity in seen):
            raise PilotError("Duplicate or unattested source-longer section")
        seen.add(identity)
    for offset in range(0, len(selected_cases), MAX_REVIEW_UNITS):
        subset = selected_cases[offset:offset + MAX_REVIEW_UNITS]
        verified = native_inventory.report(source, [case for _, case in subset])
        rows = verified["original_source_marker_native_run_sha256_and_metadata_only_cases"]
        by_identity = {
            (row["source_line"], row["original_full_reference_sha256"],
             row["original_body_sha256"]): row
            for row in rows
        }
        if (len(rows) != len(subset) or len(by_identity) != len(rows)
                or verified["source_marker_case_count"] != len(subset)):
            raise PilotError("Native and original bounded batch did not reconcile")
        for start, case in subset:
            identity = (
                case["original_source_line"], case["original_full_reference_sha256"],
                case["original_body_sha256"],
            )
            row = by_identity.get(identity)
            if row is None or row["selected_native_raw_sha256"] != case.get(
                    "stock_raw_sha256"):
                raise PilotError("Source-longer original K raw did not match pinned slot")
            book = start.split(".", 1)[0]
            extends = (
                row["native_raw_run_K_keys_before_original_range_start"] > 0
                or row["native_raw_run_K_keys_after_original_range_end"] > 0
                or row["native_K_run_has_keys_in_another_chapter_same_book"]
            )
            if row[
                    "native_raw_run_occupied_K_keys_equal_occupied_K_keys_within_declared_original_range"]:
                klass = "same_occupied_K_extent_as_original_declared_source_range"
            elif extends:
                klass = "native_shared_raw_K_extent_exceeds_original_declared_range"
            elif row["original_declared_range_native_K_other_raw_count"] > 0:
                klass = "original_declared_range_contains_distinct_native_K_raw"
            else:
                klass = "native_and_source_extents_differ_without_known_direction"
            counters[klass] += 1
            by_book[book] += 1
            book_classes[book][klass] += 1
            boundary = row["original_source_marker_boundary"]
            if not isinstance(boundary, dict):
                raise PilotError("Original scripCom neighbor boundary missing")
            following = boundary.get("immediately_following_sibling_after_source_body_tag")
            if (not isinstance(following, str)
                    or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", following)):
                raise PilotError("Unreviewed actual authorial sibling tag")
            sibling_tags[following] += 1
            proof_rows.append({
                "source_book": book,
                "original_source_line": identity[0],
                "original_full_reference_sha256": identity[1],
                "original_body_sha256": identity[2],
                "selected_original_native_raw_sha256": case["stock_raw_sha256"],
                "original_start_key_sha256": sha256(start.encode("utf-8")).hexdigest(),
                "source_to_native_occupied_range_class": klass,
                "declared_source_range_native_occupied_K_count":
                    row["original_declared_range_native_occupied_K_key_count"],
                "original_range_native_K_with_different_raw_count":
                    row["original_declared_range_native_K_other_raw_count"],
                "same_raw_contiguous_occupied_native_K_run_size":
                    row["native_K_consecutive_occupied_key_run_length"],
                "other_source_annotations_starting_in_same_native_K_run":
                    row["actual_source_annotations_starting_at_K_keys_inside_same_native_raw_run"],
                "source_division_immediate_child_tag_counts":
                    boundary["source_body_direct_child_tag_counts"],
                "next_original_source_sibling_tag": following,
                "different_editions_not_equated": True,
                "original_or_native_text_unchanged": True,
            })
    expected = len(selected_cases)
    if (sum(counters.values()) != expected or
            sum(by_book.values()) != expected or
            sum(sibling_tags.values()) != expected or
            len(proof_rows) != expected or
            any(sum(v.values()) != by_book[book] for book, v in book_classes.items())):
        raise PilotError("Source-longer original/native run relationship audit incomplete")
    proof_rows.sort(key=lambda x: (
        x["source_book"], x["original_source_line"],
        x["original_full_reference_sha256"]))
    return {
        "status": "SOURCE_LONGER_SAME_START_NATIVE_K_SCOPE_RESEARCH_ONLY",
        "source_longer_same_start_cases": expected,
        "original_book_case_counts": dict(sorted(by_book.items())),
        "original_book_native_run_scope_classes": {
            k: dict(sorted(v.items())) for k, v in sorted(book_classes.items())
        },
        "native_run_vs_source_declared_scope_classes": dict(sorted(counters.items())),
        "original_source_body_next_sibling_tag_classes": dict(sorted(sibling_tags.items())),
        "all_original_source_longer_cases_have_exact_native_K_SHA_attestation": True,
        "all_original_source_longer_cases_reviewed_without_sampling": True,
        "original_source_native_K_run_bounded_sha_only_rows": proof_rows,
        "same_start_prose_difference_not_equivalent_to_missing_authored_text": True,
        "original_source_or_stock_binary_modified": False,
        "original_edition_or_section_layout_parity_proven": False,
        "published": False,
    }
