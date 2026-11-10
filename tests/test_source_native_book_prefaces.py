"""Source/stock book preface evidence is privacy-safe and fail-closed."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_native_book_prefaces import (
    original_book_prefaces, NativeBookPrefaceEvidence, BookPrefaceError,
)

MAPPING = [("GEN","Gen"),("EXO","Exod")]


class SourceNativeBookPrefaceTests(unittest.TestCase):
    def test_empty_preface_marker_and_authored_introduction_are_distinct(self):
        source = (
            b'<usfx><book id="GEN"><p/>'
            b'<c id="1"/><v id="1"/>VERSE A</book>'
            b'<book id="EXO"><p>PRIVATE INTRODUCTION</p>'
            b'<c id="1"/><v id="1"/>VERSE B</book></usfx>'
        )
        pre, count = original_book_prefaces(source, MAPPING)
        self.assertEqual(count["source_pre_chapter_p"],2)
        self.assertEqual(count["source_pre_chapter_p_without_authored_words"],1)
        self.assertEqual(count["source_pre_chapter_p_with_authored_words"],1)
        self.assertEqual(pre["Gen"],[""])
        witness = NativeBookPrefaceEvidence()
        witness.observe("I","Gen.0.0",b'<div type="book" sID="a"/><title>BOOK</title>')
        witness.observe("I","Exod.0.0",b'<div type="x-p" sID="a"/>'
                        b'PRIVATE INTRODUCTION<div type="x-p" eID="a"/>')
        report=witness.finish(pre,count)
        self.assertEqual(report["preface_inventory_counts"]["mapped_books_inspected"],2)
        self.assertEqual(report["preface_inventory_counts"][
            "source_p_text_contiguous_in_native_intro_only"],1)
        self.assertEqual(report["preface_inventory_counts"][
            "native_book_intro_typed_x_p_elements"],2)
        self.assertTrue(report["no_scripture_or_raw_markup_in_receipt"])
        self.assertFalse(report["original_preface_p_to_typed_div_position_parity_verified"])
        self.assertFalse(report["editorial_and_publication_approved"])
        for word in ("PRIVATE","INTRODUCTION","VERSE","BOOK"):
            self.assertNotIn(word,str(report))

    def test_missing_native_book_intro_is_not_silently_approved(self):
        xml = b'<usfx><book id="GEN"><p>UNPUBLISHED CONTENT</p><c id="1"/><v id="1"/>VERSE</book></usfx>'
        pre, count = original_book_prefaces(xml,[("GEN","Gen")])
        report=NativeBookPrefaceEvidence().finish(pre,count)
        self.assertEqual(report["preface_inventory_counts"][
            "books_without_parseable_native_book_intro"],1)
        self.assertFalse(report["editorial_and_publication_approved"])
        self.assertNotIn("UNPUBLISHED",str(report))

    def test_source_prechapter_paragraph_with_verse_is_untrusted(self):
        xml=b'<usfx><book id="GEN"><p><c id="1"/><v id="1"/>TEXT</p></book></usfx>'
        with self.assertRaises(BookPrefaceError):
            original_book_prefaces(xml,[("GEN","Gen")])

    def test_source_duplicate_book_mapping_is_rejected(self):
        xml=b'<usfx><book id="GEN"><p/><c id="1"/><v id="1"/>ONE</book></usfx>'
        for mapping in ([],[("GEN","Gen"),("GEN","Gen")],[("GEN","Gen"),("EXO","Gen")]):
            with self.subTest(mapping=mapping),self.assertRaises(BookPrefaceError):
                original_book_prefaces(xml,mapping)

    def test_malformed_native_intro_is_counted_not_normalized(self):
        xml=b'<usfx><book id="GEN"><p>PRIVATE HEADING</p><c id="1"/><v id="1"/>TEXT</book></usfx>'
        pre,c=original_book_prefaces(xml,[("GEN","Gen")])
        witness=NativeBookPrefaceEvidence()
        witness.observe("I","Gen.0.0",b'<div type="x-p">')
        result=witness.finish(pre,c)
        self.assertEqual(result["preface_inventory_counts"][
            "books_without_parseable_native_book_intro"],1)
        self.assertNotIn("PRIVATE",str(result))
        self.assertFalse(result["editorial_and_publication_approved"])

    def test_native_chapter_intro_does_not_stand_in_for_missing_book_intro(self):
        xml=b'<usfx><book id="GEN"><p>AUTHORED PREFACE</p><c id="1"/><v id="1"/>TEXT</book></usfx>'
        pre,c=original_book_prefaces(xml,[("GEN","Gen")])
        witness=NativeBookPrefaceEvidence()
        witness.observe("I","Gen.1.0",b'<div type="x-p" sID="a"/>TEXT')
        result=witness.finish(pre,c)
        self.assertEqual(result["preface_inventory_counts"][
            "books_without_parseable_native_book_intro"],1)


if __name__=="__main__":
    unittest.main()
