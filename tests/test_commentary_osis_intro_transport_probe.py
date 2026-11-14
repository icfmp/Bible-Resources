"""Completely synthetic introduction-transport wrapper checks."""
import sys
from pathlib import Path
import unittest
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_osis_intro_transport_probe import make_unmodified_intro_osis


class IntroTransportTests(unittest.TestCase):
    def test_original_intro_bytes_stay_verbatim_in_each_candidate(self):
        raw=b'<chapter osisID="Gen.1"/><div type="section"/>Invented original prose'
        for mode in ("book_direct", "chapter_wrapper"):
            xml=make_unmodified_intro_osis("Gen.1",raw,mode=mode,work_id="IntroTest")
            self.assertIn(raw,xml)
            root=etree.fromstring(xml)
            self.assertEqual(root.tag.rsplit("}",1)[-1],"osis")
            self.assertIn(b'osisID="Gen"',xml)
            if mode=="chapter_wrapper":
                self.assertIn(b'<div type="chapter" osisID="Gen.1">',xml)

    def test_empty_or_invalid_intro_is_rejected(self):
        for raw in (b'<chapter', b'invalid\x00binary'):
            with self.assertRaises(ValueError):
                make_unmodified_intro_osis("Gen.1",raw,mode="book_direct",work_id="IntroTest")

    def test_never_crosses_chapter_or_introduces_custom_module_identifiers(self):
        with self.assertRaises(ValueError):
            make_unmodified_intro_osis("Gen.0",b"<div/>",mode="book_direct",work_id="IntroTest")
        with self.assertRaises(ValueError):
            make_unmodified_intro_osis("Gen.1",b"<div/>",mode="invalid",work_id="IntroTest")
        with self.assertRaises(ValueError):
            make_unmodified_intro_osis("Gen.1",b"<div/>",mode="book_direct",
                                       work_id='Invalid"Module')


if __name__=="__main__":
    unittest.main()
