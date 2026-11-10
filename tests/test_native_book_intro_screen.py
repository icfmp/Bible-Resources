"""Privacy-safe original prechapter paragraph vs SWORD book intro fixtures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from native_book_intro_screen import (
    private_original_preface_text, NativeBookIntroScreen, BookIntroScreenError
)

MAPPING = [("GEN","Gen"),("EXO","Exod")]


class OriginalNativeBookIntroTests(unittest.TestCase):
    def source(self):
        return (b'<usfx><book id="GEN"><p sfm="p">PRIVATE BOOK INTRO A</p>'
                b'<c id="1"/><v id="1"/>VERSE 1</book>'
                b'<book id="EXO"><p sfm="p">PRIVATE BOOK INTRO B</p>'
                b'<c id="1"/><v id="1"/>VERSE 2</book></usfx>')

    def test_source_classification_reused_and_exact_book_intro_match_is_only_diagnostic(self):
        pre, classified = private_original_preface_text(self.source(),MAPPING)
        self.assertEqual(classified["prefatory_source_p_class_counts"][
            "prefatory_p_with_non_annotation_text"],2)
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen",b'<div type="book" sID="id"/>'
                        b'<title>PRIVATE BOOK INTRO A</title>')
        witness.observe("I","Gen.1",b'<div type="x-milestone"/>')
        witness.observe("I","Exod.1",b'<title>PRIVATE BOOK INTRO B</title>')
        result=witness.finish(pre,classified)
        counts=result["source_prefatory_paragraph_vs_native_intro_counts"]
        self.assertEqual(counts["source_preface_paragraph_checked"],2)
        self.assertEqual(counts["preface_text_detected_in_book_or_first_chapter_intro"],2)
        self.assertEqual(counts["text_detected_at_book_scope"],1)
        self.assertEqual(counts["text_detected_at_first_chapter_scope_only"],1)
        self.assertEqual(counts["native_book_div_type_book"],1)
        self.assertFalse(result["source_native_prefatory_paragraph_position_parity_verified"])
        self.assertFalse(result["editorial_or_publication_approved"])
        for word in ("PRIVATE","BOOK INTRO","VERSE"):
            self.assertNotIn(word,str(result))

    def test_missing_book_intro_reported_not_approved(self):
        pre,classified=private_original_preface_text(self.source(),MAPPING)
        result=NativeBookIntroScreen().finish(pre,classified)
        count=result["source_prefatory_paragraph_vs_native_intro_counts"]
        self.assertEqual(count["preface_text_not_contiguous_in_checked_native_intros"],2)
        self.assertEqual(len(result["first_unmatched_preface_book_codes_only"]),2)
        self.assertTrue(result["source_preface_text_not_in_artifact"])

    def test_note_body_is_not_mistaken_for_authored_preface_content(self):
        raw=(b'<usfx><book id="GEN"><p><f>PRIVATE NOTE BODY</f>'
             b'PRIVATE PREFACE</p><c id="1"/><v id="1"/>V</book></usfx>')
        pre,classify=private_original_preface_text(raw,[("GEN","Gen")])
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen.0.0",b'<title>PRIVATE NOTE BODY</title>')
        unmatched=witness.finish(pre,classify)
        self.assertEqual(unmatched["source_prefatory_paragraph_vs_native_intro_counts"][
            "preface_text_not_contiguous_in_checked_native_intros"],1)
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen.0.0",b'<title>PRIVATE PREFACE</title>')
        matched=witness.finish(pre,classify)
        self.assertEqual(matched["source_prefatory_paragraph_vs_native_intro_counts"][
            "preface_text_detected_in_book_or_first_chapter_intro"],1)

    def test_source_prefatory_paragraph_with_numbered_marker_rejected(self):
        raw=(b'<usfx><book id="GEN"><p><c id="1"/><v id="1"/>TEXT'
             b'</p></book></usfx>')
        with self.assertRaises(BookIntroScreenError):
            private_original_preface_text(raw,[("GEN","Gen")])

    def test_native_malformed_intro_remains_unverified_not_repaired(self):
        pre,classified=private_original_preface_text(self.source(),MAPPING)
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen",b'<title>PRIVATE BOOK INTRO A')
        report=witness.finish(pre,classified)
        count=report["source_prefatory_paragraph_vs_native_intro_counts"]
        self.assertEqual(count["unparseable_book_intro_entries"],1)
        self.assertEqual(count["preface_text_not_contiguous_in_checked_native_intros"],2)
        self.assertNotIn("PRIVATE",str(report))

    def test_duplicate_native_book_intro_slot_rejected(self):
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen",b'<title>One</title>')
        with self.assertRaises(BookIntroScreenError):
            witness.observe("I","Gen.0.0",b'<title>Two</title>')

    def test_unrelated_intro_not_substitute_for_native_book_or_first_chapter(self):
        pre,classified=private_original_preface_text(self.source(),MAPPING)
        witness=NativeBookIntroScreen()
        witness.observe("I","Gen.2",b'<title>PRIVATE BOOK INTRO A</title>')
        report=witness.finish(pre,classified)
        self.assertEqual(report["source_prefatory_paragraph_vs_native_intro_counts"][
            "preface_text_not_contiguous_in_checked_native_intros"],2)

    def test_empty_original_preface_does_not_claim_native_text_match(self):
        xml=b'<usfx><book id="GEN"><p/><c id="1"/><v id="1"/>A</book></usfx>'
        pre,c=private_original_preface_text(xml,[("GEN","Gen")])
        report=NativeBookIntroScreen().finish(pre,c)
        self.assertEqual(report["source_prefatory_paragraph_vs_native_intro_counts"][
            "source_preface_paragraph_without_non_note_text"],1)
        self.assertNotIn("preface_text_detected_in_book_or_first_chapter_intro",
                         report["source_prefatory_paragraph_vs_native_intro_counts"])


if __name__ == "__main__":
    unittest.main()
