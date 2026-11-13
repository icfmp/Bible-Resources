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
MIN_ANCHOR_RUN = 6
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
            self.candidate_with_original_six_word_anchor[case_index] += 1
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
                        "scope_outcome":"no_nonidentical_stock_payload_with_six_contiguous_source_words",
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
                "unique_original_six_word_anchors_examined":unit["unique_anchor_count"],
                "same_raw_selected_payload_other_native_key_repetitions":self.identical_selected_stock_raw_key_counts[case_index],
                "native_slots_with_any_six_word_anchor_in_distinct_payload":
                    self.candidate_with_original_six_word_anchor[case_index],
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
            "original_six_word_anchor_length":MIN_ANCHOR_RUN,
            "sampled_top_distinct_raw_payloads_per_case_scope":MAX_TOP_RAW_PAYLOADS_PER_SCOPE,
            "all_native_raw_entries_replayed":self.replay_native_keys,
            "native_replay_entries_in_relevant_source_books":self.replay_relevant_native_keys,
            "distinct_original_native_stock_raw_payloads_scored":len(self.raw_seen),
            "cross_slot_scope_outcome_counts":dict(sorted(aggregate.items())),
            "all_original_large_plain_word_case_line_fullhash_scope_witnesses":
                sorted(cases,key=lambda x:(x["original_source_line"],x["original_full_reference_sha256"])),
            "nonidentical_native_payload_match_is_not_an_original_source_range_or_edition_proof":True,
            "no_original_words_native_key_strings_scripture_targets_or_raw_XML_exposed":True,
            "source_annotation_and_original_stock_module_unchanged":True,
        }
