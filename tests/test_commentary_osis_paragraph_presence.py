"""Source-neutral private whole/partial OSIS paragraph witness tests."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_osis_paragraph_presence import (
    original_ccel_paragraph_words,
    exact_original_paragraph_runs_in_osis,
    original_authoring_chapter_scope_metadata,
    PrivateOriginalChapterNativeAnchorCoverage,
    _private_whole_token_contiguous,
    _private_whole_token_subsequence,
    _private_native_word_relation,
    _private_exact_token_match_offsets,
)


def synthetic_case():
    words=[f"privateword{i:03d}" for i in range(36)]
    ref="Bible:Gen.1.1"
    # The first word and six lexical link-label words are genuine source text,
    # not extracted from inferred source-marker ranges.
    p="<p>"+ " ".join(words[:5]) + " <scripRef>" + " ".join(
        words[5:11]) + "</scripRef> " + " ".join(words[11:]) + "</p>"
    body="<div>"+p+"</div>"
    original=("<ThML>\n<scripCom osisRef='"+ref+"'/>"+body+"</ThML>").encode()
    from lxml import etree
    root=etree.fromstring(original)
    node=root.find("div")
    actual="".join(node.itertext())
    original_words=__import__("re").findall(r"\w+",actual)
    assert original_words==words
    case={
        "source_volume":1,
        "original_marker_line":2,
        "original_full_reference_sha256":sha256(ref.encode()).hexdigest(),
        "original_body_sha256":sha256(actual.encode()).hexdigest(),
        "original_paragraph_ordinal":1,
        "original_paragraph_visible_word_count":36,
        "original_paragraph_word_sha256":sha256(" ".join(words).encode()).hexdigest(),
    }
    return original,case,words


class OriginalAuthoringOsisParagraphPresenceTests(unittest.TestCase):
    def test_original_osis_chapter_milestones_define_private_prose_scope(self):
        from lxml import etree
        original=etree.fromstring(
            b'<div type="book" osisID="Gen">'
            b'outside'
            b'<chapter sID="Gen.1"/>'
            b'<div type="introduction"><p>Original introductory words.</p></div>'
            b'<verse sID="Gen.1.1"/><!-- not displayed --> Exposition text '
            b'<verse eID="Gen.1.1"/>'
            b'<chapter eID="Gen.1"/>'
            b'next chapter words'
            b'</div>')
        result=original_authoring_chapter_scope_metadata(original,"Gen.1")
        self.assertEqual(result["authentic_chapter_milestone_start_end_count"],[1,1])
        self.assertEqual(result["bounded_original_chapter_visible_words"],5)
        self.assertEqual(result["original_chapter_element_start_counts_by_tag"]["p"],1)
        self.assertEqual(result["original_chapter_element_start_counts_by_tag"]["verse"],2)
        self.assertNotIn("introductory",json.dumps(result))
        self.assertTrue(result["not_a_proof_of_original_paragraph_or_verse_ownership"])

    def test_missing_or_duplicate_original_chapter_marker_fails_closed(self):
        from lxml import etree
        for data in (
            b'<div type="book" osisID="Gen"><chapter sID="Gen.1"/>only</div>',
            b'<div type="book" osisID="Gen"><chapter sID="Gen.1"/>'
            b'<chapter sID="Gen.1"/><chapter eID="Gen.1"/></div>',
            b'<div type="book" osisID="Gen"><chapter eID="Gen.1"/></div>',
        ):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    original_authoring_chapter_scope_metadata(
                        etree.fromstring(data),"Gen.1")
        with self.assertRaises(ValueError):
            original_authoring_chapter_scope_metadata(
                etree.fromstring(b'<div type="book" osisID="Exod">x</div>'),
                "Gen.1")
    def test_whole_paragraph_source_presence_with_nested_reference_labels(self):
        ccel,case,words=synthetic_case()
        witness=original_ccel_paragraph_words(
            ccel,expected_xml_sha256=sha256(ccel).hexdigest(),case=case)
        self.assertEqual(witness,words)
        osis=("<osis><osisText><div>"+ " ".join(words)+ "</div></osisText></osis>").encode()
        out=exact_original_paragraph_runs_in_osis(
            osis,expected_osis_sha256=sha256(osis).hexdigest(),
            original_cases=[(case,witness)])
        row=out["original_ccel_paragraph_cases"][0]
        self.assertTrue(row["complete_original_paragraph_exact_word_tokens_anywhere_in_osis"])
        self.assertEqual(row[
            "longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis"],36)
        self.assertNotIn("privateword",json.dumps(out))
        self.assertTrue(out["no_authorial_bible_reference_ownership_proven"])

    def test_short_fragment_detected_but_never_counted_as_entire_paragraph(self):
        _,case,words=synthetic_case()
        only_eight=words[13:21]
        osis=("<osis><osisText><div>"+
              "unrelated "+" ".join(only_eight)+" unrelated" +
              "</div></osisText></osis>").encode()
        out=exact_original_paragraph_runs_in_osis(
            osis,expected_osis_sha256=sha256(osis).hexdigest(),
            original_cases=[(case,words)])
        row=out["original_ccel_paragraph_cases"][0]
        self.assertEqual(row[
            "longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis"],8)
        self.assertFalse(row["complete_original_paragraph_exact_word_tokens_anywhere_in_osis"])
        self.assertEqual(row["exact_8_word_anchor_occurrences_anywhere_in_osis"],1)
        self.assertNotIn("privateword013",json.dumps(out))

    def test_no_eight_consecutive_original_words_is_not_proof_of_absence(self):
        _,case,words=synthetic_case()
        source=(" ".join(words[:7]) + " unrelated " + " ".join(words[7:14]))
        osis=("<osis><osisText><div>"+source+"</div></osisText></osis>").encode()
        out=exact_original_paragraph_runs_in_osis(
            osis,expected_osis_sha256=sha256(osis).hexdigest(),
            original_cases=[(case,words)])
        row=out["original_ccel_paragraph_cases"][0]
        self.assertEqual(row["exact_8_word_anchor_occurrences_anywhere_in_osis"],0)
        self.assertEqual(row[
            "longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis"],0)
        self.assertFalse(row["complete_original_paragraph_exact_word_tokens_anywhere_in_osis"])

    def test_original_ccel_marker_body_and_paragraph_sha_are_all_required(self):
        original,case,words=synthetic_case()
        digest=sha256(original).hexdigest()
        for changed in (
            dict(case,original_full_reference_sha256="0"*64),
            dict(case,original_body_sha256="0"*64),
            dict(case,original_paragraph_word_sha256="0"*64),
            dict(case,original_marker_line=3),
            dict(case,original_paragraph_ordinal=2),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    original_ccel_paragraph_words(
                        original,expected_xml_sha256=digest,case=changed)
        with self.assertRaises(ValueError):
            original_ccel_paragraph_words(
                original,expected_xml_sha256="0"*64,case=case)

    def test_source_osis_sha_and_root_fail_closed(self):
        _,case,words=synthetic_case()
        x=b"<osis><osisText>different tokens</osisText></osis>"
        with self.assertRaises(ValueError):
            exact_original_paragraph_runs_in_osis(
                x,expected_osis_sha256="0"*64,original_cases=[(case,words)])
        invalid=b"<notosis>different tokens</notosis>"
        with self.assertRaises(ValueError):
            exact_original_paragraph_runs_in_osis(
                invalid,expected_osis_sha256=sha256(invalid).hexdigest(),
                original_cases=[(case,words)])


    def test_original_milestone_private_sink_matches_authenticated_scope_hash(self):
        from lxml import etree
        chapter_words = [f"privateword{i:02d}" for i in range(14)]
        xml = (
            '<div type="book" osisID="Gen">outside'
            '<chapter sID="Gen.1"/><p>' + " ".join(chapter_words) +
            '</p><chapter eID="Gen.1"/>next</div>'
        )
        root = etree.fromstring(xml.encode())
        sink = []
        metadata = original_authoring_chapter_scope_metadata(
            root, "Gen.1", _private_words_sink=sink)
        self.assertEqual(sink, chapter_words)
        self.assertEqual(metadata["bounded_original_chapter_visible_words"], 14)
        self.assertNotIn("privateword", json.dumps(metadata))
        with self.assertRaises(ValueError):
            original_authoring_chapter_scope_metadata(
                root, "Gen.1", _private_words_sink=sink)

    def test_private_source_native_anchor_census_deduplicates_repeated_k_raw(self):
        words = [f"privateword{i:02d}" for i in range(14)]
        census = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": words})
        first = ("<p>" + " ".join(words[:10]) + "</p>").encode()
        second = ("<div>" + " ".join(words[5:]) + "</div>").encode()
        census.observe("I", "Gen.0.0", b"introduction ignored")
        census.observe("K", "Exod.1.1", b"unrelated chapter ignored")
        census.observe("K", "Gen.1.1", first)
        census.observe("K", "Gen.1.2", first)
        census.observe("K", "Gen.1.3", second)
        result = census.report()
        row = result["original_chapter_cases"][0]
        self.assertEqual(row["actual_occupied_original_numbered_K_slots"], 3)
        self.assertEqual(row["distinct_original_native_raw_payloads"], 2)
        self.assertEqual(row["native_distinct_whole_body_ordered_word_relation_classes"],
                         {"native_contiguous_exact_tokens_in_chapter": 2})
        self.assertTrue(row["all_distinct_native_K_bodies_have_unique_exact_source_intervals"])
        self.assertEqual(row[
            "source_uncovered_word_tokens_after_unique_native_K_body_intervals"], 0)
        self.assertEqual(row["overlap_word_tokens_among_exact_native_K_body_intervals"], 5)
        self.assertEqual(row["source_uncovered_word_spans_metadata_only"], [])
        self.assertEqual(row["original_unique_eight_word_windows"], 7)
        self.assertEqual(
            row["exact_unique_source_eight_word_windows_in_original_native_K"], 5)
        self.assertFalse(
            row["one_original_native_raw_payload_matches_entire_original_chapter"])
        self.assertNotIn("privateword", json.dumps(result))
        self.assertNotIn("Gen.1", json.dumps(result))
        self.assertTrue(result["intro_and_top_payload_parity_not_compared"])

    def test_private_source_native_anchor_census_rejects_bad_xml_and_missing_chapter(self):
        words = [f"privateword{i:02d}" for i in range(10)]
        census = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": words})
        with self.assertRaises(ValueError):
            census.observe("K", "Gen.1.1", b"<p>unclosed")
        with self.assertRaises(ValueError):
            census.observe("K", "Gen.1.2", b"<fragment>bad &entity;</fragment>")
        empty = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": words})
        empty.observe("K", "Exod.1.1", b"no selected original K")
        with self.assertRaises(ValueError):
            empty.report()
        with self.assertRaises(ValueError):
            PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": ["short"]})



    def test_native_whole_body_token_relations_are_distinct_and_noneditorial(self):
        words = [f"token{i:02d}" for i in range(15)]
        self.assertEqual(
            _private_native_word_relation(words, words),
            "native_whole_chapter_exact_tokens")
        self.assertEqual(
            _private_native_word_relation(words, words[3:11]),
            "native_contiguous_exact_tokens_in_chapter")
        self.assertEqual(
            _private_native_word_relation(words, words[1:5] + words[7:13]),
            "native_ordered_exact_subsequence_only")
        self.assertEqual(
            _private_native_word_relation(words, [x.upper() for x in words[2:10]]),
            "native_contiguous_casefold_only")
        self.assertEqual(
            _private_native_word_relation(words,
                [x.upper() for x in words[1:4] + words[8:13]]),
            "native_ordered_casefold_subsequence_only")
        self.assertEqual(
            _private_native_word_relation(words,
                words[2:5] + ["unverified"] + words[5:11]),
            "native_full_ordered_token_relation_unresolved")
        self.assertEqual(
            _private_native_word_relation(words, []),
            "native_empty_visible_text")

    def test_token_contiguity_kmp_does_not_confuse_repeated_words(self):
        source = ["a", "b", "a", "b", "a", "c"]
        self.assertTrue(_private_whole_token_contiguous(
            source, ["a", "b", "a", "c"]))
        self.assertFalse(_private_whole_token_contiguous(
            source, ["a", "c", "a"]))
        self.assertTrue(_private_whole_token_subsequence(
            source, ["a", "c"]))
        self.assertFalse(_private_whole_token_subsequence(
            source, ["c", "a"]))
        self.assertFalse(_private_whole_token_contiguous(source, []))
        self.assertFalse(_private_whole_token_subsequence(source, []))

    def test_whole_body_relation_report_remains_closed_without_source_words(self):
        words = [f"privateword{i:02d}" for i in range(14)]
        census = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": words})
        census.observe("K", "Gen.1.1",
            ("<p>" + " ".join(words) + "</p>").encode())
        census.observe("K", "Gen.1.2",
            ("<p>" + " ".join(words[:8]).upper() + "</p>").encode())
        census.observe("K", "Gen.1.3",
            ("<p>" + " ".join(words[:6] + ["added"] + words[6:]) + "</p>").encode())
        report = census.report()
        classes = report["original_chapter_cases"][0][
            "native_distinct_whole_body_ordered_word_relation_classes"]
        self.assertEqual(classes, {
            "native_whole_chapter_exact_tokens": 1,
            "native_contiguous_casefold_only": 1,
            "native_full_ordered_token_relation_unresolved": 1,
        })
        self.assertEqual(sum(classes.values()), 3)
        self.assertFalse(report["original_chapter_cases"][0][
            "all_distinct_native_K_bodies_have_unique_exact_source_intervals"])
        self.assertIsNone(report["original_chapter_cases"][0][
            "source_uncovered_word_tokens_after_unique_native_K_body_intervals"])
        self.assertTrue(report["casefold_only_categories_do_not_authorize_case_changes"])
        self.assertTrue(report["exact_containment_does_not_prove_punctuation_or_markup"])
        self.assertNotIn("privateword", json.dumps(report))
        self.assertNotIn("Gen.1", json.dumps(report))


    def test_unique_native_full_body_placements_reveal_only_hashed_source_gaps(self):
        words = [f"gapword{i:02d}" for i in range(16)]
        probe = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": words})
        probe.observe("K", "Gen.1.1",
            ("<p>" + " ".join(words[1:6]) + "</p>").encode())
        probe.observe("K", "Gen.1.2",
            ("<div>" + " ".join(words[9:14]) + "</div>").encode())
        result = probe.report()
        row = result["original_chapter_cases"][0]
        self.assertEqual(row["native_distinct_whole_body_exact_source_location_classes"],
                         {"one_unique_exact_source_interval": 2})
        self.assertTrue(row["all_distinct_native_K_bodies_have_unique_exact_source_intervals"])
        self.assertEqual(row["overlap_word_tokens_among_exact_native_K_body_intervals"], 0)
        self.assertEqual(row[
            "source_uncovered_word_tokens_after_unique_native_K_body_intervals"], 6)
        spans = row["source_uncovered_word_spans_metadata_only"]
        self.assertEqual([entry["original_chapter_word_offset_not_verse_key"]
                          for entry in spans], [0, 6, 14])
        self.assertEqual([entry["source_uncovered_visible_word_tokens"]
                          for entry in spans], [1, 3, 2])
        self.assertEqual(spans[1]["original_ordered_source_word_sha256"],
                         sha256(" ".join(words[6:9]).encode()).hexdigest())
        self.assertNotIn("gapword", json.dumps(result))
        self.assertNotIn("Gen.1", json.dumps(result))
        self.assertTrue(result["source_uncovered_spans_not_automatically_missing_in_sword"])

    def test_repeated_native_body_source_positions_are_not_assigned(self):
        source = ["repeat"] * 14
        self.assertEqual(
            _private_exact_token_match_offsets(source, source[:8]),
            list(range(7)))
        with self.assertRaises(ValueError):
            _private_exact_token_match_offsets(source, source[:8],
                                              maximum_positions=2)
        probe = PrivateOriginalChapterNativeAnchorCoverage({"Gen.1": source})
        probe.observe("K", "Gen.1.1", ("<p>" + " ".join(source[:8]) + "</p>").encode())
        result = probe.report()["original_chapter_cases"][0]
        self.assertEqual(result["native_distinct_whole_body_exact_source_location_classes"],
                         {"multiple_exact_source_intervals_ambiguous": 1})
        self.assertFalse(result[
            "all_distinct_native_K_bodies_have_unique_exact_source_intervals"])
        self.assertIsNone(result[
            "source_uncovered_word_tokens_after_unique_native_K_body_intervals"])
        self.assertIsNone(result["source_uncovered_word_spans_metadata_only"])


if __name__=="__main__":
    unittest.main()
