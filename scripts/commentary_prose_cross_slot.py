#!/usr/bin/env python3
"""Private read-only locating of large original commentary prose differences.

Only originally authenticated full-body SHA identities, lexical word counts
and SHA256 digests of genuine native keys/payloads leave the private runner.
Matching words in any other native key is NOT source-authorized passage
attribution, verse-range mapping, edition identity or editorial validation.

The probe is generic. It receives actual source units and a bounded list of
previously classified original prose anomalies; no MHCC-specific line, book,
word, passage or section is hard-coded.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

from commentary_nonlink_word_alignment import plain_word_alignment
from commentary_unresolved_lexical_triage import WORD, marked_word_token_indices
from pilot_preflight import PilotError

MAX_REVIEW_CASES = 12
MAX_NATIVE_STOCK_KEYS = 50_000
MAX_DISTINCT_RAW_PAYLOADS = 45_000
MAX_NATIVE_XML_BYTES = 2 * 1024 * 1024
MAX_STOCK_WORDS = 50_000
MAX_SOURCE_WORDS = 4_000
MIN_ANCHOR_RUN = 4
STRONG_ANCHOR_RUN = 6
MAX_TOP_RAW_PAYLOADS_PER_SCOPE = 4
VALID_SCOPES = (
    "other_numbered_key_same_chapter",
    "numbered_key_other_chapter_same_book",
    "same_chapter_intro",
    "other_chapter_intro_same_book",
    "book_intro",
)
SHA_RE = re.compile(r"[a-f0-9]{64}\Z")


def strict_native_stock_plain_words(raw: bytes) -> list[str]:
    """Exclude ONLY genuine compiled XML reference label words, not guessed ones."""
    if not isinstance(raw, bytes) or len(raw) > MAX_NATIVE_XML_BYTES or b"\x00" in raw:
        raise PilotError("Native commentary raw XML exceeds reviewed bounds")
    try:
        root = etree.fromstring(
            b"<stock>" + raw + b"</stock>",
            parser=etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_blank_text=False,
            ),
        )
    except (ValueError, etree.XMLSyntaxError):
        raise PilotError("Original compiled stock XML is not strictly parseable") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise PilotError("Unresolved native XML entity outside safe reading")
    value = "".join(root.itertext())
    words = WORD.findall(value)
    if len(words) > MAX_STOCK_WORDS:
        raise PilotError("Native stock entry has an unreviewed word count")
    linked = set(marked_word_token_indices(root, "reference", value))
    return [word for i, word in enumerate(words) if i not in linked]


def longest_contiguous_original_word_run(source_word_positions: dict[str, list[int]],
                                         compiled: list[str]) -> int:
    """Exact maximum contiguous source word-token run, with O(source words) memory."""
    previous = {}
    best = 0
    for word in compiled:
        current = {}
        for original_pos in source_word_positions.get(word, ()):
            length = previous.get(original_pos - 1, 0) + 1
            current[original_pos] = length
            if length > best:
                best = length
        previous = current
    return best


class OriginalProseAlternativeNativeSlotProbe:
    """One bounded second raw-corpus replay, with actual native K/I identities."""

    def __init__(self, source: dict[str, list[dict]], review_cases: list[dict]):
        if not 1 <= len(review_cases) <= MAX_REVIEW_CASES:
            raise PilotError("No bounded original source prose review cases")
        source_lookup = {}
        for start, units in source.items():
            for original in units:
                identity = (
                    original["original_source_line"],
                    original["original_full_reference_sha256"],
                    original["original_text_sha256"],
                )
                if identity in source_lookup:
                    raise PilotError("Original source line/hash identity is ambiguous")
                source_lookup[identity] = (start, original)
        self.units = []
        self.books = set()
        self.anchor_to_units_by_book = defaultdict(lambda: defaultdict(set))
        self.replay_native_keys = 0
        self.replay_relevant_native_keys = 0
        self.replay_strict_xml_failures = 0
        self.raw_seen = {}
        self.top_scopes = defaultdict(lambda: {scope: [] for scope in VALID_SCOPES})
        self.identical_selected_stock_raw_key_counts = Counter()
        self.candidate_with_original_six_word_anchor = Counter()
        self.candidate_with_original_four_or_five_word_anchor = Counter()
        for index, case in enumerate(review_cases):
            if not all(isinstance(case.get(k), str) and SHA_RE.fullmatch(case[k])
                       for k in (
                           "original_full_reference_sha256", "original_body_sha256",
                           "stock_raw_sha256",
                       )):
                raise PilotError("Missing full authentic source/stock SHA256 identity")
            line = case.get("original_source_line")
            if type(line) is not int or line <= 0:
                raise PilotError("Invalid source line identity")
            original_match = source_lookup.get((
                line,case["original_full_reference_sha256"],
                case["original_body_sha256"],
            ))
            if original_match is None:
                raise PilotError("Original prose review case is not from exact source")
            start, source_unit = original_match
            original_words = WORD.findall(source_unit["original_text"])
            linked_indices = source_unit["private_original_scripRef_word_indices"]
            if (len(original_words) < MIN_ANCHOR_RUN or
                    len(original_words) > MAX_SOURCE_WORDS or
                    not isinstance(linked_indices, list) or
                    any(type(pos) is not int or pos < 0 or pos >= len(original_words)
                        for pos in linked_indices) or
                    len(set(linked_indices)) != len(linked_indices)):
                raise PilotError("Unreviewed original citation label token positions")
            link_set = set(linked_indices)
            plain_words = [w for i,w in enumerate(original_words) if i not in link_set]
            alignment = case.get("exact_plain_word_alignment")
            if (not isinstance(alignment, dict)
                    or alignment.get("original_plain_word_tokens") != len(plain_words)
                    or alignment.get("original_plain_words_not_matched_in_exact_order") is None
                    or alignment["original_plain_words_not_matched_in_exact_order"] <= 10):
                raise PilotError("Cross-slot probe requires prior >10 source plain-word mismatch")
            if len(plain_words) < MIN_ANCHOR_RUN:
                raise PilotError("Original non-link prose too short for safe exact anchor scan")
            book,chapter = start.split(".",1)[0],start.rsplit(".",1)[0]
            positions = defaultdict(list)
            for pos,w in enumerate(plain_words):
                positions[w].append(pos)
            anchor_set = {
                tuple(plain_words[k:k+MIN_ANCHOR_RUN])
                for k in range(len(plain_words)-MIN_ANCHOR_RUN+1)
            }
            for anchor in anchor_set:
                self.anchor_to_units_by_book[book][anchor].add(index)
            strong_anchor_set = {
                tuple(plain_words[k:k+STRONG_ANCHOR_RUN])
                for k in range(len(plain_words)-STRONG_ANCHOR_RUN+1)
            }
            unit = {
                "line":line,
                "source_reference_sha256":case["original_full_reference_sha256"],
                "source_body_sha256":case["original_body_sha256"],
                "selected_stock_raw_sha256":case["stock_raw_sha256"],
                "original_selected_stock_lcs_word_count":
                    alignment["exact_unicode_longest_common_subsequence_word_count"],
                "start":start,"book":book,"chapter":chapter,
                "source_words":plain_words,"source_word_positions":positions,
                "source_word_count":len(plain_words),
                "unique_anchor_count":len(anchor_set),
                "unique_strong_anchor_count":len(strong_anchor_set),
            }
            if not isinstance(unit["original_selected_stock_lcs_word_count"],int):
                raise PilotError("Original selected-stock LCS witness is not complete")
            self.books.add(book)
            self.units.append(unit)
        if len({(u["line"],u["source_reference_sha256"]) for u in self.units}) != len(self.units):
            raise PilotError("Repeated source review annotation is not a unique original unit")

    @staticmethod
    def _scope(unit:dict, kind:str, key:str) -> str | None:
        if kind=="K":
            if key == unit["start"]:
                return None
            return ("other_numbered_key_same_chapter" if
                    key.rsplit(".",1)[0] == unit["chapter"] else
                    "numbered_key_other_chapter_same_book")
        if kind!="I":
            return None
        if key in (unit["chapter"],unit["chapter"]+".0"):
            return "same_chapter_intro"
        if key in (unit["book"],unit["book"]+".0",unit["book"]+".0.0"):
            return "book_intro"
        return "other_chapter_intro_same_book"

    def observe(self, kind:str, key:str, raw:bytes) -> None:
        self.replay_native_keys += 1
        if self.replay_native_keys > MAX_NATIVE_STOCK_KEYS:
            raise PilotError("Cross-slot native replay exceeds reviewed keys")
        if kind not in ("K","I"):
            return
        book = key.split(".",1)[0]
        if book not in self.books:
            return
        self.replay_relevant_native_keys += 1
        digest = sha256(raw).hexdigest()
        for case_index, unit in enumerate(self.units):
            if (unit["book"] == book and key != unit["start"] and
                    digest == unit["selected_stock_raw_sha256"]):
                self.identical_selected_stock_raw_key_counts[case_index] += 1
        cache_key = (book,digest)
        scores = self.raw_seen.get(cache_key)
        stock_words = None
        if scores is None:
            if len(self.raw_seen) >= MAX_DISTINCT_RAW_PAYLOADS:
                raise PilotError("Cross-slot unique original stock raw count exceeds bound")
            stock_words = strict_native_stock_plain_words(raw)
            indexed = self.anchor_to_units_by_book[book]
            matched_cases = set()
            for i in range(len(stock_words)-MIN_ANCHOR_RUN+1):
                matched_cases.update(indexed.get(
                    tuple(stock_words[i:i+MIN_ANCHOR_RUN]), ()
                ))
            scores = {}
            for case_index in matched_cases:
                unit=self.units[case_index]
                scores[case_index] = longest_contiguous_original_word_run(
                    unit["source_word_positions"],stock_words
                )
                if scores[case_index] < MIN_ANCHOR_RUN:
                    raise PilotError("Source substring anchor and run scanner disagree")
            self.raw_seen[cache_key] = (scores, len(stock_words))
            cached_len = len(stock_words)
        else:
            scores, cached_len = scores
        for case_index, best_run in scores.items():
            unit=self.units[case_index]
            scope=self._scope(unit,kind,key)
            if scope is None:
                continue
            # A different verse key with the exact same *raw content* is a
            # repeated native payload, not a new independent textual witness.
            if digest == unit["selected_stock_raw_sha256"]:
                continue
            if best_run >= STRONG_ANCHOR_RUN:
                self.candidate_with_original_six_word_anchor[case_index] += 1
            else:
                self.candidate_with_original_four_or_five_word_anchor[case_index] += 1
            pool=self.top_scopes[case_index][scope]
            if any(x["stock_raw_sha256"]==digest for x in pool):
                continue
            candidate_rank=(best_run, -abs(cached_len-unit["source_word_count"]))
            if len(pool) == MAX_TOP_RAW_PAYLOADS_PER_SCOPE:
                minimum=min(pool,key=lambda x:x["sort_rank"])
                if candidate_rank <= minimum["sort_rank"]:
                    continue
                pool.remove(minimum)
            if stock_words is None:
                stock_words = strict_native_stock_plain_words(raw)
            pool.append({
                "native_key_sha256":sha256(key.encode("utf-8")).hexdigest(),
                "stock_raw_sha256":digest,
                "same_native_chapter_as_original":scope=="other_numbered_key_same_chapter",
                "original_words_contiguous_best_run":best_run,
                "anchor_strength_class":(
                    "at_least_six_original_words_contiguous_in_stock"
                    if best_run >= STRONG_ANCHOR_RUN
                    else "only_four_or_five_original_words_contiguous_in_stock"
                ),
                "stock_plain_word_count":len(stock_words),
                "sort_rank":(best_run,-abs(len(stock_words)-unit["source_word_count"])),
                "private_stock_words":stock_words,
            })

    def report(self) -> dict:
        aggregate = Counter()
        cases = []
        for case_index,unit in enumerate(self.units):
            scope_receipts={}
            has_better = False
            has_full = False
            has_skipped = False
            for scope, pool in self.top_scopes[case_index].items():
                if not pool:
                    scope_receipts[scope] = {
                        "sampled_distinct_alternative_raw_payloads":0,
                        "scope_outcome":"no_nonidentical_stock_payload_with_four_contiguous_source_words",
                    }
                    continue
                best=None
                verified=0
                for candidate in pool:
                    alignment=plain_word_alignment(
                        unit["source_words"],candidate["private_stock_words"]
                    )
                    if alignment[
                        "exact_unicode_ordered_alignment_class"
                    ]=="alignment_skipped_exceeds_reviewed_word_or_cell_bound":
                        has_skipped=True
                        continue
                    verified+=1
                    current={
                        "best_compiled_native_key_sha256":candidate["native_key_sha256"],
                        "best_stock_raw_sha256":candidate["stock_raw_sha256"],
                        "shared_original_plain_words_in_order":alignment[
                            "exact_unicode_longest_common_subsequence_word_count"],
                        "original_plain_words_not_matched_in_order":alignment[
                            "original_plain_words_not_matched_in_exact_order"],
                        "stock_plain_words_not_matched_in_order":alignment[
                            "stock_plain_words_not_matched_in_exact_order"],
                        "longest_exact_contiguous_source_word_run":candidate[
                            "original_words_contiguous_best_run"],
                        "original_contiguous_anchor_strength_class":candidate[
                            "anchor_strength_class"],
                        "source_plain_word_count":unit["source_word_count"],
                        "compiled_plain_word_count":candidate["stock_plain_word_count"],
                        "stock_native_key_is_only_a_textual_location_witness":True,
                    }
                    if best is None or (
                        current["shared_original_plain_words_in_order"],
                        current["longest_exact_contiguous_source_word_run"],
                        current["best_stock_raw_sha256"],
                    ) > (
                        best["shared_original_plain_words_in_order"],
                        best["longest_exact_contiguous_source_word_run"],
                        best["best_stock_raw_sha256"],
                    ):
                        best=current
                if best is None:
                    scope_receipts[scope]={
                        "sampled_distinct_alternative_raw_payloads":len(pool),
                        "exact_order_alignment_candidates_not_skipped":0,
                        "scope_outcome":"all_reviewed_candidate_alignments_exceeded_budget",
                    }
                    continue
                original_baseline=unit["original_selected_stock_lcs_word_count"]
                matched=best["shared_original_plain_words_in_order"]
                if matched == unit["source_word_count"]:
                    outcome="all_original_plain_words_present_in_selected_other_stock_entry"
                    has_full=True
                    has_better=True
                elif matched > original_baseline:
                    outcome="other_stock_entry_improves_original_ordered_word_match"
                    has_better=True
                else:
                    outcome="best_sampled_other_stock_entry_not_better_than_original_selected"
                scope_receipts[scope]={
                    "sampled_distinct_alternative_raw_payloads":len(pool),
                    "exact_order_alignment_candidates_not_skipped":verified,
                    "scope_outcome":outcome,
                    "best_candidate":best,
                }
                aggregate[scope+"__"+outcome] += 1
            if has_full:
                overall="source_plain_words_fully_in_order_in_other_native_payload_not_section_proof"
            elif has_better:
                overall="other_native_stock_payload_improves_original_plain_word_order"
            elif has_skipped:
                overall="some_cross_slot_alignments_exceeded_budget_no_full_negative_claim"
            else:
                overall="no_better_ordered_source_plain_word_witness_in_sampled_native_slots"
            aggregate["overall__"+overall]+=1
            cases.append({
                "original_source_line":unit["line"],
                "original_full_reference_sha256":unit["source_reference_sha256"],
                "original_body_sha256":unit["source_body_sha256"],
                "selected_stock_raw_sha256":unit["selected_stock_raw_sha256"],
                "original_plain_word_count":unit["source_word_count"],
                "selected_stock_ordered_shared_plain_word_count":
                    unit["original_selected_stock_lcs_word_count"],
                "unique_original_four_word_anchors_examined":unit["unique_anchor_count"],
                "unique_original_six_word_anchors_examined":unit["unique_strong_anchor_count"],
                "same_raw_selected_payload_other_native_key_repetitions":self.identical_selected_stock_raw_key_counts[case_index],
                "native_slots_with_any_six_word_anchor_in_distinct_payload":
                    self.candidate_with_original_six_word_anchor[case_index],
                "native_slots_with_four_or_five_word_anchor_in_distinct_payload":
                    self.candidate_with_original_four_or_five_word_anchor[case_index],
                "overall_scope_conclusion":overall,
                "by_native_scope":scope_receipts,
                "original_source_ref_or_passage_not_derived_from_stock_key":True,
            })
        if sum(value for key,value in aggregate.items() if key.startswith("overall__")) != len(self.units):
            raise PilotError("Cross-slot source prose outcomes do not account for all source cases")
        if not self.replay_native_keys or not self.replay_relevant_native_keys:
            raise PilotError("Actual native raw replay did not inspect source-relevant books")
        return {
            "original_source_large_plain_word_cases":len(self.units),
            "minimum_fallback_word_anchor_length":MIN_ANCHOR_RUN,
            "strong_original_word_anchor_length":STRONG_ANCHOR_RUN,
            "sampled_top_distinct_raw_payloads_per_case_scope":MAX_TOP_RAW_PAYLOADS_PER_SCOPE,
            "all_native_raw_entries_replayed":self.replay_native_keys,
            "native_replay_entries_in_relevant_source_books":self.replay_relevant_native_keys,
            "distinct_original_native_stock_raw_payloads_scored":len(self.raw_seen),
            "cross_slot_scope_outcome_counts":dict(sorted(aggregate.items())),
            "all_original_large_plain_word_case_line_fullhash_scope_witnesses":
                sorted(cases,key=lambda x:(x["original_source_line"],x["original_full_reference_sha256"])),
            "weak_four_or_five_word_anchor_does_not_prove_same_original_authorial_section":True,
            "strong_six_word_anchor_was_separately_counted":True,
            "nonidentical_native_payload_match_is_not_an_original_source_range_or_edition_proof":True,
            "no_original_words_native_key_strings_scripture_targets_or_raw_XML_exposed":True,
            "source_annotation_and_original_stock_module_unchanged":True,
        }


class OriginalExtraGapNativeChapterProbe:
    """Private exact entire-extra-span search in authentic other chapter K/I slots.

    Only a bounded, source-neutral high-size subset is inspected. A hit is a
    textual location candidate, never approval to move original annotations.
    Neither original prose, native keys nor target strings enter the report.
    """

    MIN_FULL_SPAN_WORDS = 6
    MAX_OUTLIER_CASES = 4
    MAX_NATIVE_REPLAY_KEYS = 50_000

    def __init__(self, cases: list[tuple[str,dict,bytes,dict]]):
        from commentary_nonlink_words import _private_unique_original_gap_spans
        if not 1 <= len(cases) <= self.MAX_OUTLIER_CASES:
            raise PilotError("Source-extra native outlier research exceeds bounded cases")
        self.units = []
        self.replayed = 0
        for start,item,selected,metadata in cases:
            if (not isinstance(start,str) or start.count(".")!=2
                    or not isinstance(selected,bytes) or not isinstance(item,dict)
                    or not isinstance(metadata,dict)):
                raise PilotError("Original extra-span candidate lacks genuine source and native identities")
            original=item.get("original_text")
            line=item.get("original_source_line")
            if (not isinstance(original,str) or type(line) is not int or line<=0
                    or sha256(original.encode("utf-8")).hexdigest()!=item.get("original_text_sha256")
                    or not isinstance(item.get("original_full_reference_sha256"),str)
                    or not SHA_RE.fullmatch(item["original_full_reference_sha256"])):
                raise PilotError("Original extra-span candidate identity or text SHA is unverified")
            tokens=WORD.findall(original)
            linked=item.get("private_original_scripRef_word_indices")
            if (not isinstance(linked,list) or len(linked)!=len(set(linked))
                    or any(type(n) is not int or n<0 or n>=len(tokens) for n in linked)):
                raise PilotError("Original extra-span genuine link offsets unverified")
            linked_set=set(linked)
            source_plain=[w for i,w in enumerate(tokens) if i not in linked_set]
            stock_plain=strict_native_stock_plain_words(selected)
            spans=_private_unique_original_gap_spans(source_plain,stock_plain)
            layout=metadata.get("source_extra_unlinked_word_gap_layout")
            if (spans is None or not isinstance(layout,dict)
                    or layout.get("alignment_topology")!="unique_alignment_interior_extra_words_only"
                    or sum(map(len,spans))!=layout.get("source_extra_nonlink_word_count")
                    or len(spans)!=layout.get("fixed_extra_word_spans")
                    or sum(map(len,spans)) < 100):
                raise PilotError("Unapproved source-extra outlier selection or unique gap alignment")
            self.units.append({
                "original_source_line":line,
                "original_full_reference_sha256":item["original_full_reference_sha256"],
                "original_body_sha256":item["original_text_sha256"],
                "selected_native_sha256":sha256(selected).hexdigest(),
                "chapter":start.rsplit(".",1)[0],
                "original_source_extra_span_lengths":list(map(len,spans)),
                "private_original_extra_spans":[tuple(words) for words in spans],
                "private_original_unlinked_words":source_plain,
                "private_selected_stock_unlinked_words":stock_plain,
                "distinct_other_native_raw_sha":set(),
                "other_native_payload_counts":Counter(),
                "full_gap_hits":{ "K":set(), "I":set() },
                "identical_original_raw_repeat_keys":0,
            })
        if len({(u["original_source_line"],u["original_full_reference_sha256"])
                for u in self.units})!=len(self.units):
            raise PilotError("Duplicate original source extra-span outlier identity")

    def original_thml_extra_gap_structure(
            self, xml_bytes:bytes, *, expected_source_sha256:str) -> dict:
        """Read exact original adjacent ThML body paragraphs at outlier lines.

        The original XML source bytes, source ref and text hashes are
        authenticated again. Report only source line/SHA-bound paragraph and
        section-element ownership of word spans, never the underlying prose.
        A CCEL paragraph is *digital source structure*, not independent proof
        of the historic author's original editorial divisions.
        """
        from commentary_nonlink_words import _private_unique_original_gap_windows
        from commentary_unresolved_lexical_triage import marked_word_token_indices
        if (not isinstance(xml_bytes,bytes) or len(xml_bytes)>64*1024*1024
                or not SHA_RE.fullmatch(expected_source_sha256)
                or sha256(xml_bytes).hexdigest()!=expected_source_sha256):
            raise PilotError("Original CCEL ThML source bytes are not exactly authenticated")
        try:
            root=etree.fromstring(xml_bytes,parser=etree.XMLParser(
                resolve_entities=False,no_network=True,load_dtd=False,
                recover=False,huge_tree=False,remove_blank_text=False))
        except (ValueError,etree.XMLSyntaxError):
            raise PilotError("Original CCEL markup cannot be parsed without recovery") from None
        if any(isinstance(node,etree._Entity) for node in root.iter()):
            raise PilotError("Original CCEL has unreviewed external XML entities")
        matched={}
        sought={(u["original_source_line"],u["original_full_reference_sha256"])
                for u in self.units}
        for node in root.iter():
            if not isinstance(node.tag,str) or node.tag.rsplit("}",1)[-1]!="scripCom":
                continue
            ident=(node.sourceline,sha256(node.get("osisRef","").encode("utf-8")).hexdigest())
            if ident in sought:
                if ident in matched:
                    raise PilotError("Source line/reference hash points at multiple ThML markers")
                matched[ident]=node
        if set(matched)!=sought:
            raise PilotError("Original source-marker line/ref identity not found in exact XML")

        outputs=[]
        for unit in self.units:
            identity=(unit["original_source_line"],unit["original_full_reference_sha256"])
            marker=matched[identity]
            original_source_ref=marker.get("osisRef","")
            if (not re.fullmatch(
                    r"Bible:[A-Za-z0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+\.[0-9]+\.[0-9]+)?",
                    original_source_ref)
                    or len(original_source_ref)>128):
                raise PilotError("Original source scripCom citation cannot be safely recorded")
            body=marker.getnext()
            if (body is None or not isinstance(body.tag,str)
                    or body.tag.rsplit("}",1)[-1]!="div"
                    or (marker.tail and marker.tail.strip())):
                raise PilotError("Original source marker is not immediately followed by an authored div")
            original="".join(body.itertext())
            if sha256(original.encode("utf-8")).hexdigest()!=unit["original_body_sha256"]:
                raise PilotError("Original source marker's adjacent body text SHA differs")
            linked=set(marked_word_token_indices(body,"scripRef",original))
            words=WORD.findall(original)
            plain=[w for i,w in enumerate(words) if i not in linked]
            if plain!=unit["private_original_unlinked_words"]:
                raise PilotError("Original ThML link-word owners differ from earlier source census")
            windows=_private_unique_original_gap_windows(
                plain,unit["private_selected_stock_unlinked_words"])
            if windows is None or [b-a for a,b in windows]!=unit[
                    "original_source_extra_span_lengths"]:
                raise PilotError("Original source gap window/word identity changed")

            # Exact authored element text/tail order with character coordinates.
            fragments=[]
            paragraphs=[]
            char_pos=0
            paragraph_number=0
            def emit(value):
                nonlocal char_pos
                if value:
                    char_pos+=len(value)
            def walk(node):
                nonlocal paragraph_number
                start=char_pos
                tag=node.tag.rsplit("}",1)[-1] if isinstance(node.tag,str) else ""
                num=None
                if tag=="p":
                    paragraph_number+=1
                    num=paragraph_number
                emit(node.text)
                for child in node:
                    walk(child)
                    emit(child.tail)
                if num is not None:
                    paragraphs.append((start,char_pos,num))
            walk(body)
            if char_pos!=len(original):
                raise PilotError("Actual ThML text/tail paragraph offsets did not reconcile")
            # Every regex token must be placed entirely within ONE original p,
            # or conservatively classified as outside/ambiguous, not attributed.
            paragraph_owners=[]
            mixed_word_boundary_count=0
            for match in WORD.finditer(original):
                contained=[n for a,b,n in paragraphs
                           if a<=match.start() and match.end()<=b]
                overlapping=[n for a,b,n in paragraphs
                             if a<match.end() and match.start()<b]
                if len(contained)==1 and len(overlapping)==1:
                    paragraph_owners.append(contained[0])
                elif not overlapping:
                    paragraph_owners.append(None)
                else:
                    paragraph_owners.append(-1)
                    mixed_word_boundary_count+=1
            if len(paragraph_owners)!=len(words):
                raise PilotError("Source original paragraph words no longer equal original tokens")
            plain_owners=[owner for i,owner in enumerate(paragraph_owners)
                          if i not in linked]
            if len(plain_owners)!=len(plain):
                raise PilotError("Original source unlinked paragraph-owner word count changed")
            paragraph_positions={}
            for i,owner in enumerate(plain_owners):
                if owner is not None and owner!=-1:
                    paragraph_positions.setdefault(owner,set()).add(i)
            span_rows=[]
            for a,b in windows:
                positions=set(range(a,b))
                these=plain_owners[a:b]
                distinct={owner for owner in these if type(owner) is int and owner>0}
                outside=sum(owner is None for owner in these)
                mixed=sum(owner==-1 for owner in these)
                if mixed:
                    category="word_crosses_original_paragraph_markup_boundary"
                elif outside and distinct:
                    category="extra_span_mixes_original_paragraph_and_nonparagraph_words"
                elif outside:
                    category="extra_span_entirely_outside_original_p_elements"
                elif len(distinct)==1:
                    category="extra_span_inside_one_original_p"
                else:
                    category="extra_span_crosses_multiple_original_p_elements"
                whole=sum(paragraph_positions[n].issubset(positions) for n in distinct)
                partial=len(distinct)-whole
                uniquely_owned_original_p=(
                    next(iter(distinct))
                    if category=="extra_span_inside_one_original_p"
                    and whole==1 and partial==0 else None
                )
                span_rows.append({
                    "exact_original_unlinked_extra_word_count":b-a,
                    "original_paragraph_ownership_class":category,
                    "distinct_original_p_elements_touched":len(distinct),
                    "whole_original_p_elements_word_covered":whole,
                    "partially_covered_original_p_elements":partial,
                    "exact_whole_original_p_document_ordinal_when_unique":
                        uniquely_owned_original_p,
                    "original_unlinked_words_outside_p":outside,
                    "original_tokens_straddling_p_markup":mixed,
                })
            next_sibling=body.getnext()
            next_tag=(next_sibling.tag.rsplit("}",1)[-1]
                      if next_sibling is not None and isinstance(next_sibling.tag,str)
                      else "none")
            outputs.append({
                "original_source_line":unit["original_source_line"],
                "original_ccel_scripCom_osisRef_claim_only":original_source_ref,
                "original_full_reference_sha256":unit["original_full_reference_sha256"],
                "original_body_sha256":unit["original_body_sha256"],
                "selected_native_sha256":unit["selected_native_sha256"],
                "original_adjacent_div_p_element_total":len(paragraphs),
                "original_adjacent_div_unlinked_word_count":len(plain),
                "original_word_tokens_spanning_original_p_boundaries":mixed_word_boundary_count,
                "original_next_sibling_element_type_only":next_tag,
                "original_extra_word_spans_authentically_within_adjacent_source_div":
                    span_rows,
                "original_adjacent_div_structure_not_original_print_edition_identity":True,
            })
        return {
            "status":"PINNED_ORIGINAL_THML_SOURCE_EXTRA_PARAGRAPH_TOPOLOGY_ONLY",
            "source_xml_sha256":expected_source_sha256,
            "original_outlier_source_units_reconciled":len(outputs),
            "source_line_hash_and_original_adjacent_paragraph_structure_only":outputs,
            "original_reference_markers_and_section_divisions_not_modified":True,
            "only_original_ccel_source_scripCom_claimed_reference_recorded":True,
            "original_words_or_native_keys_exposed":False,
            "ccel_claimed_reference_is_not_native_mapping_or_authorial_edition_proof":True,
            "original_authorial_print_editional_structure_parity_established":False,
        }

    @staticmethod
    def _full_token_span_present(needle: tuple[str,...], haystack:list[str]) -> bool:
        if not needle or len(needle)>len(haystack):
            return False
        # Explicit token separators keep exact whole-word boundary semantics.
        sep=chr(0)
        return (sep+sep.join(needle)+sep) in (sep+sep.join(haystack)+sep)

    def observe(self, kind:str, key:str,raw:bytes) -> None:
        self.replayed+=1
        if self.replayed>self.MAX_NATIVE_REPLAY_KEYS:
            raise PilotError("Actual full native corpus replay exceeds outlier audit bound")
        if kind not in ("K","I"):
            return
        for unit in self.units:
            chapter=unit["chapter"]
            if (kind=="K" and key.rsplit(".",1)[0]!=chapter or
                    kind=="I" and key not in (chapter,chapter+".0")):
                continue
            raw_sha=sha256(raw).hexdigest()
            if raw_sha==unit["selected_native_sha256"]:
                unit["identical_original_raw_repeat_keys"]+=1
                continue
            if raw_sha in unit["distinct_other_native_raw_sha"]:
                continue
            unit["distinct_other_native_raw_sha"].add(raw_sha)
            unit["other_native_payload_counts"][kind]+=1
            words=strict_native_stock_plain_words(raw)
            for span_index,span in enumerate(unit["private_original_extra_spans"]):
                if len(span)>=self.MIN_FULL_SPAN_WORDS and self._full_token_span_present(
                        span,words):
                    unit["full_gap_hits"][kind].add(span_index)

    def report(self) -> dict:
        if self.replayed<=0:
            raise PilotError("Source-extra original native corpus was not actually replayed")
        findings=[]
        for unit in self.units:
            spans=unit["original_source_extra_span_lengths"]
            examined={i for i,n in enumerate(spans) if n>=self.MIN_FULL_SPAN_WORDS}
            found_k=unit["full_gap_hits"]["K"]
            found_i=unit["full_gap_hits"]["I"]
            if not found_k.issubset(examined) or not found_i.issubset(examined):
                raise PilotError("Unreviewed short gap matched in native chapter")
            findings.append({
                "original_source_line":unit["original_source_line"],
                "original_full_reference_sha256":unit["original_full_reference_sha256"],
                "original_body_sha256":unit["original_body_sha256"],
                "selected_native_sha256":unit["selected_native_sha256"],
                "original_unlinked_extra_word_span_lengths":spans,
                "extra_spans_tested_with_minimum_six_original_words":len(examined),
                "extra_spans_not_tested_under_six_original_words":len(spans)-len(examined),
                "extra_spans_exactly_witnessed_in_distinct_same_chapter_K_raw":
                    len(found_k),
                "extra_spans_exactly_witnessed_in_distinct_same_chapter_I_raw":
                    len(found_i),
                "distinct_extra_spans_witnessed_in_any_other_same_chapter_raw":
                    len(found_k|found_i),
                "same_chapter_other_distinct_native_raw_payloads_by_kind":
                    dict(sorted(unit["other_native_payload_counts"].items())),
                "identical_selected_native_raw_repeat_keys_not_independent":
                    unit["identical_original_raw_repeat_keys"],
                "same_chapter_no_hit_does_not_prove_absence_elsewhere_or_authorial_loss":True,
            })
        return {
            "status":"ORIGINAL_HIGH_EXTRA_SPAN_SAME_CHAPTER_OTHER_RAW_LOCATION_ONLY",
            "source_extra_outlier_cases_examined":len(findings),
            "minimum_contiguous_exact_original_nonlink_word_span_length":
                self.MIN_FULL_SPAN_WORDS,
            "complete_original_native_raw_entries_replayed":self.replayed,
            "original_source_line_hash_and_native_other_slot_counts_only":findings,
            "source_xml_or_original_crosswire_native_binary_modified":False,
            "no_original_words_or_native_key_strings_exposed":True,
            "same_chapter_location_not_authorial_section_or_full_edition_parity":True,
        }
