"""Private native-SWORD raw-entry witness tests: no published text fixtures."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sword_missing_verse_witness import (
    compare_unindexed_source_text, extract_usfx_main_verse_tokens,
    native_main_tokens, MissingVerseWitnessError
)

USFX = b'''<usfx><book id="ROM">
<c id="14"/><p>
<v id="23"/>Earlier original content.
<v id="24"/>The unusual original sequence starts here.
<f>Footnote must never count towards Bible text.</f>
<v id="25"/>More of the same original wording follows.
<v id="26"/>And this unique original ending concludes.
</p></book></usfx>'''
NATIVE = (b'<verse osisID="Rom.14.23"/>Earlier original content. '
          b'<milestone resp="v"/>The unusual original sequence starts here. '
          b'<note type="study">This note is not main text.</note>'
          b'<milestone resp="v"/>More of the same original wording follows. '
          b'<milestone resp="v"/>And this unique original ending concludes.')


class NativeRawWitnessTests(unittest.TestCase):
    def _check(self, usfx=USFX, native=NATIVE,
               missing=("Rom.14.24", "Rom.14.25", "Rom.14.26"),
               occupied="Rom.14.23\n"):
        calls = []
        def fetch(key):
            calls.append(key)
            return native
        receipt = compare_unindexed_source_text(
            usfx, ["ROM"], list(missing), [("ROM", "Rom")],
            occupied, fetch)
        return receipt, calls

    def test_same_native_entry_contains_all_three_original_word_runs(self):
        report, calls = self._check()
        self.assertEqual(calls, ["Rom.14.23"])
        self.assertEqual(report["source_scope_missing_native_verse_count"], 3)
        self.assertEqual(report["inspected_unique_native_raw_entries"], 1)
        self.assertTrue(all(
            row["source_word_run_found_contiguously_in_native_entry"]
            for row in report["source_missing_native_verses"]))
        self.assertTrue(report["grouped_preceding_native_entries"][0][
            "missing_source_word_runs_in_source_order"])
        self.assertFalse(report["authorial_complete_text_preservation_verified"])
        self.assertFalse(report["source_to_compiled_exact_punctuation_verified"])
        self.assertFalse(report["approved_for_publication"])
        self.assertFalse(report["published"])
        serialized = json.dumps(report)
        self.assertNotIn("unusual original sequence", serialized)
        self.assertNotIn("More of the same original", serialized)

    def test_source_text_absent_from_reader_not_dismissed_as_missing_key_only(self):
        report, _calls = self._check(native=b'<verse>Earlier original content.</verse>')
        self.assertEqual(report["inspected_unique_native_raw_entries"], 1)
        self.assertTrue(all(
            row["diagnostic"] == "source_word_run_not_found_in_preceding_native_entry"
            for row in report["source_missing_native_verses"]))
        self.assertFalse(report["grouped_preceding_native_entries"][0][
            "all_missing_source_word_runs_found"])

    def test_native_notes_do_not_falsely_supply_missing_scripture(self):
        text = (b'<verse>Earlier original content.</verse><note>'
                b'The unusual original sequence starts here.</note>')
        report, _ = self._check(native=text, missing=("Rom.14.24",))
        self.assertFalse(report["source_missing_native_verses"][0][
            "source_word_run_found_contiguously_in_native_entry"])

    def test_authorial_notes_are_not_treated_as_scripture(self):
        verses = extract_usfx_main_verse_tokens(USFX, "ROM", 14, {24, 25})
        self.assertEqual(verses[24],
                         ["the", "unusual", "original", "sequence", "starts", "here"])
        self.assertNotIn("footnote", verses[24])
        self.assertEqual(verses[25],
                         ["more", "of", "the", "same", "original", "wording", "follows"])

    def test_real_native_raw_xml_fragment_html_entities_and_notes(self):
        source = b'<hi>Word</hi> &amp; <w lemma="x">word</w><note>private</note>.'
        self.assertEqual(native_main_tokens(source), ["word", "word", "word"])
        self.assertNotIn("private", native_main_tokens(source))

    def test_short_authorial_text_is_inconclusive_not_proof(self):
        xml = (b'<usfx><book id="ROM"><c id="14"/>'
               b'<v id="24"/>Amen!</book></usfx>')
        report, calls = self._check(usfx=xml, missing=("Rom.14.24",))
        self.assertEqual(calls, [])
        self.assertEqual(report["source_missing_native_verses"][0]["diagnostic"],
                         "too_few_source_tokens_for_content_witness")
        self.assertFalse(report["authorial_complete_text_preservation_verified"])

    def test_no_previous_native_same_chapter_does_not_guess(self):
        report, calls = self._check(occupied="Rom.13.23\n", missing=("Rom.14.24",))
        self.assertEqual(calls, [])
        self.assertEqual(report["source_missing_native_verses"][0]["diagnostic"],
                         "no_preceding_occupied_native_entry_in_same_chapter")

    def test_missing_source_reference_is_not_allowed_to_be_occupied(self):
        with self.assertRaisesRegex(MissingVerseWitnessError, "Unreliable"):
            self._check(missing=("Rom.14.23",))
        with self.assertRaisesRegex(MissingVerseWitnessError, "Unreliable"):
            self._check(missing=("Rom.14.24", "Rom.14.24"))

    def test_mismatched_source_book_fails_closed(self):
        with self.assertRaisesRegex(MissingVerseWitnessError, "no authored book"):
            compare_unindexed_source_text(
                USFX, ["GEN"], ["Rom.14.24"], [("ROM", "Rom")],
                "Rom.14.23\n", lambda ref: NATIVE)

    def test_unknown_source_milestone_range_blocks_rather_than_guess(self):
        malformed = USFX.replace(b'<v id="24"/>', b'<v id="24-26"/>')
        with self.assertRaisesRegex(MissingVerseWitnessError, "Ambiguous"):
            extract_usfx_main_verse_tokens(malformed, "ROM", 14, {24})

    def test_malformed_xml_blocks(self):
        with self.assertRaises(Exception):
            extract_usfx_main_verse_tokens(USFX.replace(b"</usfx>", b"</other>"),
                                           "ROM", 14, {24})

    def test_source_dtd_blocks(self):
        with self.assertRaisesRegex(MissingVerseWitnessError, "DTD"):
            extract_usfx_main_verse_tokens(
                b'<!DOCTYPE usfx [<!ENTITY e "x">]>' + USFX, "ROM", 14, {24})

    def test_byte_payload_is_required_from_native_reader(self):
        with self.assertRaisesRegex(MissingVerseWitnessError, "non-bytes"):
            compare_unindexed_source_text(
                USFX, ["ROM"], ["Rom.14.24"], [("ROM", "Rom")],
                "Rom.14.23\n", lambda ref: "not actual raw bytes")

    def test_native_raw_missing_text_never_claims_verse_numbering_preserved(self):
        report, _ = self._check()
        self.assertTrue(report["actual_missing_refs_are_not_reintroduced"])
        self.assertTrue(all(row["original_verse_reference_still_unindexed"]
                            for row in report["source_missing_native_verses"]))


if __name__ == "__main__":
    unittest.main()
