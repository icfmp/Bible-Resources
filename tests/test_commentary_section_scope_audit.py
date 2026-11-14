"""Synthetic regressions for source-neutral commentary section-scope triage."""
import sys
import json
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lxml import etree
from commentary_section_scope_audit import (
    heading_extent, classify, compare_independent_thml_witness,
    describe_unrecognized_heading, audit_unrecognized_slots,
    independent_chapter_scope_evidence, independent_div2_chapter_body_evidence,
    independent_lexical_overlap,
)


class HeadingTests(unittest.TestCase):
    def test_comma_section_with_space_outside_heading(self):
        self.assertEqual(
            heading_extent(b"<title>Verse 7</title> ,8 Observe carefully."),
            ((7, 8), "comma")
        )

    def test_dash_and_plural_heading(self):
        self.assertEqual(
            heading_extent(b"<title>Verses 2-6</title><p>Some prose.</p>"),
            ((2, 3, 4, 5, 6), "dash")
        )

    def test_multiple_explicit_comma_verses(self):
        self.assertEqual(heading_extent(b"Verses 1,2,3 Comment"),
                         ((1, 2, 3), "comma"))

    def test_single_verse_and_no_heading(self):
        self.assertEqual(heading_extent(b"<title>Verse 4</title>"),
                         ((4,), "single"))
        self.assertIsNone(heading_extent(b"<p>A sermon concerning the book.</p>"))

    def test_reversed_and_ambiguous_range_not_guessed(self):
        self.assertIsNone(heading_extent(b"Verses 7-2 Text"))
        self.assertIsNone(heading_extent(b"Verses 8,4-7 Text"))
        self.assertIsNone(heading_extent(b"Verses 2-5,4-7 Text"))

    def test_discontinuous_nonoverlapping_ranges_are_not_lost(self):
        self.assertEqual(
            heading_extent(b"<title>Verses 24-30, 36-43</title><p>Discussion</p>"),
            (tuple(range(24, 31)) + tuple(range(36, 44)), "discontinuous")
        )
        self.assertEqual(
            heading_extent(b"<title>Verses 2,4-7</title>"),
            ((2,4,5,6,7), "discontinuous")
        )

    def test_xml_malformed_or_entities_rejected(self):
        self.assertIsNone(heading_extent(b"<p>Verse 2 <b>unclosed</p>"))
        self.assertIsNone(heading_extent(b"<p>&madeup; Verse 1</p>"))


class ClassificationTests(unittest.TestCase):
    def test_same_native_raw_for_whole_declared_section(self):
        records = {
            "Song.1.7": {"sha256": "a", "heading": ((7, 8), "comma")},
            "Song.1.8": {"sha256": "a", "heading": ((7, 8), "comma")},
        }
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["start_anchored_sections"], 1)
        self.assertEqual(outcome["counts"]["all_declared_slots_same_raw_payload"], 1)
        self.assertEqual(outcome["anomalies"], [])
        self.assertEqual(outcome["probes"]["Song.1.7"]["same_payload_slots"], ["Song.1.8"])

    def test_missing_verse_for_comma_span_stays_suspected(self):
        records = {"Jer.4.1": {"sha256": "a", "heading": ((1, 2), "comma")}}
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["missing_slots_within_declared_section"], 1)
        self.assertEqual(outcome["anomalies"][0]["missing_slots"], ["Jer.4.2"])
        self.assertEqual(outcome["anomalies"][0]["classification"],
                         "SUSPECTED_NOT_EDITORIALLY_CONFIRMED")

    def test_distinct_payload_in_declared_range(self):
        records = {
            "Jer.4.3": {"sha256": "a", "heading": ((3, 4), "comma")},
            "Jer.4.4": {"sha256": "b", "heading": ((3, 4), "comma")},
        }
        outcome = classify(records)
        self.assertEqual(outcome["counts"]["distinct_payload_within_declared_section"], 1)

    def test_discontinuous_commentary_reports_missing_second_block(self):
        entries = {
            f"Matt.13.{verse}": {
                "sha256": "a", "heading": (
                    tuple(range(24, 31)) + tuple(range(36, 44)),
                    "discontinuous"
                )
            }
            for verse in range(24, 31)
        }
        report = classify(entries)
        self.assertEqual(report["counts"]["start_sections_discontinuous"], 1)
        self.assertEqual(
            report["anomalies"][0]["missing_slots"],
            [f"Matt.13.{verse}" for verse in range(36,44)]
        )

    def test_missing_members_of_dash_section(self):
        outcome = classify({
            "Song.1.2": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
            "Song.1.3": {"sha256": "a", "heading": ((2, 3, 4), "dash")},
        })
        self.assertEqual(outcome["anomalies"][0]["missing_slots"], ["Song.1.4"])



class UnknownHeadingTests(unittest.TestCase):
    def test_no_verse_title_is_not_mistaken_for_lost_content(self):
        p = describe_unrecognized_heading(b"<title>Introduction</title><p>Context</p>")
        self.assertEqual(p["reason"], "NON_NUMERIC_XML_TITLE")
        self.assertTrue(p["visible_nonempty"])

    def test_empty_and_invalid_xml_have_different_classes(self):
        self.assertEqual(describe_unrecognized_heading(b" ")["reason"], "EMPTY_RAW_PAYLOAD")
        self.assertEqual(describe_unrecognized_heading(b"<p>broken</b>")["reason"],
                         "INVALID_XML_FRAGMENT")

    def test_no_title_and_nonempty_prose(self):
        p = describe_unrecognized_heading(b"<p>Context without numbered title</p>")
        self.assertEqual(p["reason"], "UNLABELLED_VISIBLE_PROSE")

    def test_unparsed_heading_not_automatically_corrected(self):
        p = describe_unrecognized_heading(b"<title>Verses two to five</title>")
        self.assertEqual(p["reason"], "UNPARSED_VERSE_LABEL")

    def test_raw_payload_groups_are_tracked_without_prose(self):
        unknown = describe_unrecognized_heading(b"<title>Introduction</title>")
        rows = {
            "Gen.1.1": {"sha256": "a", "heading": None, "unrecognized_profile": unknown},
            "Gen.1.2": {"sha256": "a", "heading": None, "unrecognized_profile": unknown},
            "Gen.1.3": {"sha256": "b", "heading": ((3, 4), "dash"),
                        "unrecognized_profile": None},
        }
        result = audit_unrecognized_slots(rows)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["reason_counts"]["NON_NUMERIC_XML_TITLE"], 2)
        self.assertEqual(result["distinct_native_raw_payload_hashes"], 1)
        self.assertEqual(result["first_verse_entries"], 1)
        self.assertEqual(result["single_occupied_slot_chapters_among_unknown"], 0)
        self.assertEqual(result["case_rows"][0]["number_of_occupied_native_slots_in_chapter"], 3)
        self.assertEqual(result["case_rows"][0]["highest_occupied_native_verse_in_chapter"], 3)
        self.assertFalse(result["unrecognized_means_missing_text_proven"])
        self.assertTrue(result["all_output_is_original_text_free_metadata"])



class SafeLexicalEvidenceTests(unittest.TestCase):
    def test_identical_original_word_sequence_is_high_overlap_without_rewrite(self):
        r = independent_lexical_overlap(
            "Wisdom directs those who listen carefully.",
            b"<p>Wisdom directs those who listen carefully.</p>",
        )
        self.assertEqual(r["overlap_class"], "HIGH_95_PLUS")
        self.assertTrue(r["exact_ordered_word_equality"])
        self.assertEqual(
            r["ordered_word_alignment"]["exact_unicode_ordered_alignment_class"],
            "plain_words_exactly_identical_in_original_order"
        )
        self.assertFalse(r["historical_or_editorial_equivalence_proven"])
        self.assertNotIn("Wisdom", str(r))

    def test_original_source_suffix_has_a_distinct_stock_title_prefix(self):
        result = independent_lexical_overlap(
            "The whole chapter commentary.",
            b"<title>Chapter 1</title><p>The whole chapter commentary.</p>",
        )
        self.assertEqual(result["ordered_word_alignment"][
            "exact_unicode_ordered_alignment_class"
        ], "all_source_plain_words_in_stock_order_with_extra_stock_words")
        prefix = result["stock_extra_prefix_xml_topology"]
        self.assertTrue(prefix["full_original_source_word_sequence_inside_stock"])
        self.assertEqual(prefix["unapproved_stock_extra_word_prefix_count"], 2)
        self.assertEqual(prefix["top_level_element_types_wholly_before_original_source_words"], {"title": 1})
        self.assertFalse(prefix["additional_stock_words_approved_as_heading"])
        self.assertFalse(result["historical_or_editorial_equivalence_proven"])

    def test_unrelated_original_words_fail_the_overlapping_diagnostic(self):
        r = independent_lexical_overlap(
            "Alpha beta gamma delta epsilon zeta",
            b"<p>One two three four five six seven</p>",
        )
        self.assertEqual(r["overlap_class"], "LOW_OVERLAP")

    def test_multiset_cannot_hide_word_order_changes(self):
        r = independent_lexical_overlap(
            "faith hope charity truth",
            b"<p>truth charity hope faith</p>",
        )
        self.assertEqual(r["overlap_class"], "HIGH_95_PLUS")
        self.assertNotEqual(
            r["ordered_word_alignment"]["exact_unicode_ordered_alignment_class"],
            "plain_words_exactly_identical_in_original_order"
        )

    def test_xml_failure_does_not_claim_a_match(self):
        r = independent_lexical_overlap(
            "Some original prose", b"<p>Unclosed original text"
        )
        self.assertEqual(r["status"], "UNPARSEABLE_ORIGINAL_RAW")
        self.assertFalse(r["source_text_equal"])

class ChapterScopeEvidenceTests(unittest.TestCase):
    def test_chapter_only_div2_is_candidate_not_editorial_approval(self):
        source = etree.fromstring(
            b'<root><div2>'
            b'<scripCom osisRef="Bible:Gen.36"/>'
            b'<h2>Chapter summary</h2><p>Whole chapter notes</p>'
            b'</div2></root>'
        )
        candidates = [{
            "native_key": "Gen.36.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1
        }]
        result = independent_chapter_scope_evidence(source, candidates)
        self.assertEqual(result["source_scope_candidate_classes"],
                         {"INDEPENDENT_UNDIVIDED_CHAPTER_SCOPE_CANDIDATE": 1})
        self.assertFalse(result["per_verse_navigation_approved"])

    def test_chapter_intro_does_not_override_independent_verse_sections(self):
        source = etree.fromstring(
            b'<root><div2>'
            b'<scripCom osisRef="Bible:Gen.36"/>'
            b'<h2>Chapter summary</h2>'
            b'<scripCom osisRef="Bible:Gen.36.1-Gen.36.5"/>'
            b'<div><p>A specific original section</p></div>'
            b'</div2></root>'
        )
        candidate = [{
            "native_key": "Gen.36.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1
        }]
        result = independent_chapter_scope_evidence(source, candidate)
        self.assertEqual(result["source_scope_candidate_classes"],
            {"CHAPTER_ANNOTATION_WITH_SECTIONS_OR_UNREVIEWED_SHAPE": 1})

    def test_missing_source_chapter_annotation_fails_to_classify_scope(self):
        source = etree.fromstring(
            b'<root><div2><p>Some original prose</p></div2></root>'
        )
        candidate = [{
            "native_key": "Gen.36.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1
        }]
        result = independent_chapter_scope_evidence(source, candidate)
        self.assertEqual(result["source_scope_candidate_classes"],
                         {"NO_MATCHING_CHAPTER_ANNOTATION_IN_OTHER_EDITION": 1})
        self.assertFalse(result["per_verse_navigation_approved"])



class SourceDivisionChapterTests(unittest.TestCase):
    def test_undivided_source_chapter_with_title_and_order_witness(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis"><div2><h2>Chapter 1</h2>'
            b'<p>Independent chapter exposition</p></div2></div1>'
            b'<div1 title="Exodus"><div2><h2>Chapter 1</h2>'
            b'<p>Another exposition</p></div2></div1></root>'
        )
        registry = {"chapter_maximums": {"Gen.1":31, "Exod.1":22}}
        cases = [{
            "native_key": "Gen.1.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1,
            "raw_payload_sha256": "a" * 64,
        }]
        result = independent_div2_chapter_body_evidence(
            document, registry, cases
        )
        self.assertEqual(result["candidate_classes"], {
            "SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE": 1
        })
        self.assertFalse(result["derived_authorial_section_scope_proven"])
        self.assertEqual(result["case_rows"][0]["source_h2_numeric_chapters"], [1])

    def test_same_book_chapter_intro_with_numbered_comments_is_not_whole_chapter(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis"><div2><h2>Chapter 1</h2>'
            b'<scripCom osisRef="Bible:Gen.1.1-Gen.1.5"/>'
            b'<div><p>First commentary section</p></div></div2></div1></root>'
        )
        registry = {"chapter_maximums": {"Gen.1":31}}
        cases = [{
            "native_key": "Gen.1.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1,
            "raw_payload_sha256": "a" * 64,
        }]
        result = independent_div2_chapter_body_evidence(
            document, registry, cases
        )
        self.assertEqual(result["candidate_classes"], {
            "SOURCE_DIV2_HAS_INDEPENDENT_VERSE_SECTIONS": 1
        })
        self.assertEqual(result["case_rows"][0]["source_annotated_chapters"], ["Gen.1"])

    def test_conflicting_source_book_title_never_approves_a_reindex(self):
        document = etree.fromstring(
            b'<root><div1 title="Exodus"><div2><p>Text</p></div2></div1></root>'
        )
        registry = {"chapter_maximums": {"Gen.1":31}}
        cases = [{
            "native_key": "Gen.1.1", "first_verse_in_chapter": True,
            "number_of_occupied_native_slots_in_chapter": 1,
            "raw_payload_sha256": "a" * 64,
        }]
        result = independent_div2_chapter_body_evidence(document, registry, cases)
        self.assertEqual(result["candidate_classes"], {
            "SOURCE_BOOK_OR_CHAPTER_ALIGNMENT_NEEDS_REVIEW": 1
        })

    def test_unmarked_noncanonical_source_appendix_is_not_assigned_a_bible_book(self):
        document = etree.fromstring(
            b'<root>'
            b'<div1 title="Genesis"><div2><p>Genesis one</p></div2></div1>'
            b'<div1 title="Exodus"><div2><p>Exodus one</p></div2></div1>'
            b'<div1 title="Original index"><div2><p>Alphabetical appendix</p></div2>'
            b'<div2><p>Another index page</p></div2></div1>'
            b'</root>'
        )
        registry = {"chapter_maximums": {"Gen.1":31, "Exod.1":22}}
        cases = [
            {"native_key": "Gen.1.1", "first_verse_in_chapter": True,
             "number_of_occupied_native_slots_in_chapter": 1,
             "raw_payload_sha256": "a" * 64},
        ]
        report = independent_div2_chapter_body_evidence(document, registry, cases)
        self.assertEqual(report["unattributed_noncanonical_div1_with_div2_excluded"], 1)
        self.assertEqual(report["source_book_divisions"], 2)
        self.assertEqual(report["candidate_classes"],
                         {"SOURCE_DIV2_UNDIVIDED_CHAPTER_BODY_CANDIDATE": 1})

    def test_source_skipped_first_chapter_uses_its_own_explicit_heading(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis">'
            b'<div2><scripCom osisRef="Bible:Gen.2"/>'
            b'<h2>Chapter 2</h2><p>Undivided notes for chapter 2</p></div2>'
            b'</div1></root>'
        )
        native = {"chapter_maximums": {"Gen.1":31, "Gen.2":25}}
        cases = [
            {"native_key": f"Gen.{chapter}.1", "first_verse_in_chapter": True,
             "number_of_occupied_native_slots_in_chapter": 1,
             "raw_payload_sha256": "a" * 64}
            for chapter in (1, 2)
        ]
        result = independent_div2_chapter_body_evidence(document, native, cases)
        by_key = {r["native_start"]: r for r in result["case_rows"]}
        self.assertEqual(by_key["Gen.1.1"]["source_div2_structure_class"],
                         "NO_SAFE_SOURCE_DIV2_FOR_NATIVE_CHAPTER")
        self.assertEqual(by_key["Gen.2.1"]["source_div2_structure_class"],
                         "SOURCE_DIV2_UNDIVIDED_EXPLICIT_HEADING_CANDIDATE")
        self.assertEqual(by_key["Gen.2.1"]["source_div2_original_ordinal"], 1)

    def test_original_chapter_one_before_first_div2_is_documented_not_guessed(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis">'
            b'<h1>Genesis</h1><scripCom osisRef="Bible:Gen.1"/>'
            b'<h2>Chapter 1</h2><p>Unwrapped first chapter notes</p>'
            b'<div2><h2>Chapter 2</h2><p>Second chapter notes</p></div2>'
            b'</div1></root>'
        )
        native = {"chapter_maximums": {"Gen.1":31, "Gen.2":25}}
        result = independent_div2_chapter_body_evidence(document, native, [])
        book = result["book_alignment_evidence_rows"][0]
        self.assertEqual(book["source_prefix_chapter_scripCom_refs"], ["Gen.1"])
        self.assertEqual(book["source_prefix_numeric_h2_chapters"], [1])
        self.assertEqual(book["source_prefix_nonempty_paragraphs"], 1)
        self.assertEqual(book["native_registry_chapter_count"], 2)
        self.assertEqual(book["source_direct_div2_count"], 1)
        stock = {"Gen.1.1": b"<p>Unwrapped first chapter notes</p>"}
        compared = independent_div2_chapter_body_evidence(
            document, native, [
                {"native_key": "Gen.1.1", "first_verse_in_chapter": True,
                 "number_of_occupied_native_slots_in_chapter": 1,
                 "raw_payload_sha256": "a" * 64}
            ], stock,
        )
        metrics = compared["case_rows"][0]["independent_lexical_comparison"]
        self.assertEqual(metrics["overlap_class"], "HIGH_95_PLUS")
        self.assertNotIn("Unwrapped", json.dumps(compared))

    def test_chapter_heading_conflicting_with_source_scripcom_is_not_reassigned(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis">'
            b'<div2><scripCom osisRef="Bible:Gen.1"/>'
            b'<h2>Chapter 2</h2><p>Contradictory source metadata</p></div2>'
            b'</div1></root>'
        )
        native = {"chapter_maximums": {"Gen.1":31, "Gen.2":25}}
        cases = [{"native_key": "Gen.2.1", "first_verse_in_chapter": True,
                  "number_of_occupied_native_slots_in_chapter": 1,
                  "raw_payload_sha256": "a" * 64}]
        result = independent_div2_chapter_body_evidence(document, native, cases)
        self.assertEqual(result["candidate_classes"],
                         {"NO_SAFE_SOURCE_DIV2_FOR_NATIVE_CHAPTER": 1})

    def test_partial_source_book_coverage_is_not_accepted(self):
        document = etree.fromstring(
            b'<root><div1 title="Genesis"><div2><p>Text</p></div2></div1></root>'
        )
        registry = {"chapter_maximums": {"Gen.1":31, "Exod.1":22}}
        result = independent_div2_chapter_body_evidence(document, registry, [])
        self.assertEqual(result["status"], "SOURCE_BOOK_LAYOUT_NOT_EXACT_NATIVE_BOOK_COUNT")


class IndependentWitnessTests(unittest.TestCase):
    def test_unlabelled_stock_entry_can_have_explicit_independent_section(self):
        xml = (
            b"<root>"
            b'<scripCom osisRef="Bible:Gen.36.1-Gen.36.43"/>'
            b'<scripRef osisRef="Bible:Gen.36.1-Gen.36.43"/>'
            b"</root>"
        )
        digest = sha256(xml).hexdigest()
        manifest = {"commentary_source": {
            "xml_witness_url": "https://www.ccel.org/fake.xml",
            "xml_witness_sha256": digest,
        }}
        unknown = [{
            "native_key": "Gen.36.1",
            "raw_payload_sha256": "fake-unique-payload",
            "number_of_occupied_native_slots_in_chapter": 1,
        }]
        def fixture(url, dest, provider):
            dest.write_bytes(xml)
            return {"sha256": digest, "bytes": len(xml)}
        with TemporaryDirectory() as td, patch(
            "commentary_section_scope_audit.fetch", fixture
        ):
            got = compare_independent_thml_witness(
                manifest, [], [], Path(td), unknown
            )
        self.assertEqual(
            got["unrecognized_source_annotation_classes"],
            {"SOURCE_EXPLICIT_MULTI_VERSE_SECTION": 1}
        )
        self.assertEqual(
            got["unrecognized_distinct_payload_source_rows"][0]["source_section_endpoints"],
            ["Gen.36.43"]
        )
        self.assertFalse(got["editorial_correctness_proven"])

    def test_citation_range_is_not_commentary_section_anchor(self):
        xml = (
            b"<root>"
            b'<scripRef osisRef="Bible:Song.1.7-Song.1.8"/>'
            b'<scripCom osisRef="Bible:Song.1.9-Song.1.17"/>'
            b"</root>"
        )
        digest = sha256(xml).hexdigest()
        manifest = {"commentary_source": {
            "xml_witness_url": "https://www.ccel.org/fake.xml",
            "xml_witness_sha256": digest
        }}
        sections = [
            {"start": "Song.1.7", "declared_end": 8, "heading_kind": "comma"},
            {"start": "Song.1.9", "declared_end": 17, "heading_kind": "dash"}
        ]
        anomalies = [{"start": "Song.1.7", "declared_end": 8}]

        def private_fixture_fetch(url, dest, provider):
            self.assertEqual(provider, "ccel")
            dest.write_bytes(xml)
            return {"sha256": digest, "bytes": len(xml)}

        with TemporaryDirectory() as td:
            with patch("commentary_section_scope_audit.fetch", private_fixture_fetch):
                outcome = compare_independent_thml_witness(
                    manifest, sections, anomalies, Path(td)
                )
        self.assertEqual(
            outcome["source_range_agreement_counts"], {
                "NO_MATCHING_INDEPENDENT_START": 1,
                "SAME_DECLARED_RANGE_IN_INDEPENDENT_EDITION": 1
            }
        )
        self.assertEqual(
            outcome["independent_scripref_range_agreement_counts"], {
                "EXACT_INDEPENDENT_SCRIPREF_RANGE": 1,
                "NO_EXACT_INDEPENDENT_SCRIPREF_RANGE": 1
            }
        )
        case = outcome["anomaly_source_range_corroboration"][0]
        self.assertEqual(case["relation"], "NO_MATCHING_INDEPENDENT_START")
        self.assertTrue(case["same_end_in_independent_scripref"])
        self.assertFalse(outcome["ccel_edition_equivalence_to_stock_proven"])


if __name__ == "__main__":
    unittest.main()
