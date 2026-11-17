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


if __name__=="__main__":
    unittest.main()
