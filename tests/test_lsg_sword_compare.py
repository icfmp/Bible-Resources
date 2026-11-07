"""Offline parser fixtures for LSG USFX/diatheke sampled chapter fidelity."""
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_sword_compare import usfx_text_by_verse,parse_sword_chapter,plain
from pilot_preflight import PilotError


class LsgTextParityTests(unittest.TestCase):
    def test_usfx_verse_text_and_word_annotations_preserved_while_xrefs_excluded(self):
        xml=b"""<usfx><book id="PSA"><c id="23"/><p>
        <v id="1"/>Cantique de David. <w s="H123">L'Eternel</w> est mon berger:
        <x><xo>23:1</xo><xt>other reference</xt></x> je ne manquerai de rien.<ve id="1"/>
        <v id="2"/>Il me dirige pres des eaux paisibles.<ve id="2"/>
        </p></book></usfx>"""
        verse,features=usfx_text_by_verse(xml,filter_books={"PSA"})
        self.assertEqual(verse[("PSA",23,1)],
                         "Cantique de David. L'Eternel est mon berger: je ne manquerai de rien.")
        self.assertEqual(features[("PSA",23,1)]["w"],1)
        self.assertEqual(features[("PSA",23,1)]["x"],1)
        self.assertEqual(verse[("PSA",23,2)],"Il me dirige pres des eaux paisibles.")

    def test_diatheke_chapter_multiple_verses_are_parsed_without_folding_poetry(self):
        output=("Psalms 23:1: Cantique de David. \nL'Eternel est mon berger.\n"
                "Psalms 23:2: Il me fait reposer,\nIl me dirige.\n"
                "\n(fraLSG1910eb)\n").encode()
        pieces=parse_sword_chapter(output,23,"fraLSG1910eb")
        self.assertEqual(pieces[1],"Cantique de David. L'Eternel est mon berger.")
        self.assertEqual(pieces[2],"Il me fait reposer, Il me dirige.")

    def test_duplicate_sword_verse_cannot_pass(self):
        output=b"Genesis 1:1: Hello\nGenesis 1:1: repeated\n(fraLSG1910eb)\n"
        with self.assertRaisesRegex(PilotError,"Duplicate"):
            parse_sword_chapter(output,1,"fraLSG1910eb")

    def test_diatheke_non_verse_garbage_fails(self):
        with self.assertRaisesRegex(PilotError,"no per-verse"):
            parse_sword_chapter(b"Usage: diatheke",1,"fraLSG1910eb")


if __name__=="__main__":
    unittest.main()
