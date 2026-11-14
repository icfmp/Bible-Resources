"""Invented-only mixed original I and K OSIS transport regression."""
import sys
from pathlib import Path
import unittest
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_osis_mixed_transport_probe import build_mixed_original_transport


class MixedOriginalTransportTests(unittest.TestCase):
    def test_original_book_intro_chapter_intro_and_verses_all_inside_xml_unchanged(self):
        book=b'<div type="book"/>'
        intro=b'<chapter osisID="Gen.36"/><div type="section"/>'
        verse=b'<title>Invented chapter prose</title><div>Text for chapter.</div>'
        xml,meta=build_mixed_original_transport(
            "Gen.36",book,intro,
            [("Gen.36.1",verse),("Gen.36.2",verse)],
            work_id="MixedTest"
        )
        self.assertIn(book,xml)
        self.assertIn(intro,xml)
        self.assertIn(verse,xml)
        self.assertEqual(meta["numbered_source_keys"],2)
        self.assertEqual(meta["numbered_source_groups"],1)
        self.assertFalse(meta["source_intro_raw_modified"])
        self.assertFalse(meta["source_k_raw_modified"])
        self.assertFalse(meta["source_published"])
        document=etree.fromstring(xml)
        self.assertEqual(len(document.xpath(
            "//*[local-name()='div' and @annotateRef='Gen.36.1-Gen.36.2']"
        )),1)

    def test_chapter_range_mismatch_and_binary_material_are_blocked(self):
        for rows in (
            [("Gen.35.1",b"<p>Other chapter</p>")],
            [("Gen.36.2",b"<p>later</p>"),
             ("Gen.36.1",b"<p>earlier</p>")],
            [("Gen.36.1",b"<p>binary\\x00</p>")]
        ):
            with self.assertRaises(ValueError):
                build_mixed_original_transport(
                    "Gen.36",b"<div/>",b"<chapter/>",rows,
                    work_id="MixedTest"
                )


if __name__=="__main__":
    unittest.main()
