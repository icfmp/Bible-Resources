"""USFM candidate projection regressions using synthetic original witnesses."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from research.bible.usfm_source_projection import project
from research.bible.usfm_converter_patch import deterministic_patch, ConverterPatchError
from test_original_authorial_content_parity import USFX, OSIS, MAP, archive

class RegisteredUSFMConversionTests(unittest.TestCase):
    def test_unreviewed_converter_bytes_fail_closed(self):
        with self.assertRaises(ConverterPatchError):
            deterministic_patch(b"unreviewed Python code")

    def test_private_projection_is_deterministic_and_preserves_source(self):
        report={}
        with archive(r'\id GEN'+'\n'+r'\c 1 \v 1 \w alpha|strong="H1"\w* \x a \xo 1.1 \xt old\x* \w beta|strong="H2"\w*') as z:
            candidate=project(USFX,OSIS,MAP,z,report)
            self.assertEqual(project(USFX,OSIS,MAP,z,{}),candidate)
        self.assertTrue(report["paragraph_projection"]["numbered_parity"])
        self.assertTrue(report["paragraph_projection"]["inverse_exact"])
        self.assertTrue(report["paragraph_projection"]["nonparagraph_elements_unchanged"])

    def test_text_note_and_lexical_corruptions_fail(self):
        for corrupted in (
            OSIS.replace(b'alpha',b'altered'),
            OSIS.replace(b'strong:H1',b'strong:H3'),
            OSIS.replace(b'n="a"',b'n="b"'),
            OSIS.replace(b'>old<',b'>wrong<'),
            OSIS.replace(b'Gen.1.1',b'Gen.1.2'),
        ):
            self.assertNotEqual(corrupted,OSIS)
            with self.subTest(corruption=corrupted),self.assertRaises((ValueError,AssertionError)):
                project(USFX,corrupted,MAP,None,{})

    def test_repair_only_source_attested_table_controls_and_boundaries(self):
        source=USFX.replace(b'<c id="1"/>',
            b'<table><tr><tc>A</tc></tr></table><table><tr><tc>B</tc></tr></table><c id="1"/>')
        target=OSIS.replace(b'<chapter osisID="Gen.1" sID="Gen.1"/>',
            b'<table><row><cell>A</cell></row><row><cell>\\i B</cell></row></table><chapter osisID="Gen.1" sID="Gen.1"/>')
        report={}
        result=project(source,target,MAP,None,report)
        self.assertIn(b'</table><table>',result)
        self.assertNotIn(b'\\i',result)
        self.assertEqual(report["table_projection"]["edits"],{"restored_table_separators":1,"removed_literal_controls":1})
        with self.assertRaises(AssertionError):
            project(source,target.replace(b'\\i B',b'\\i Wrong'),MAP,None,{})
