"""Integration regression: no original Scripture files may be rewritten."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_ephemeral_osis_candidate import prepare_ephemeral_source_spaced_osis
from pilot_preflight import PilotError

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def synthetic_pair():
    usfx=(b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
          b'Hello <w s="H1">world</w>\n'
          b'<x caller="a"><xo>1.1</xo><xt>Ps 1</xt></x>'
          b'<ve id="1"/></p></book></usfx>')
    osis=(f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
          '<chapter osisID="Gen.1"><p><verse sID="Gen.1.1" osisID="Gen.1.1"/>'
          'Hello <w lemma="strong:H1">world</w>'
          '<note type="crossReference" n="a">'
          '<reference type="annotateRef" subType="x-origin">1.1</reference>'
          '<reference>Ps 1</reference></note><verse eID="Gen.1.1"/>'
          '</p></chapter></div></osisText></osis>').encode("utf-8")
    return usfx,osis


class EphemeralCandidateTests(unittest.TestCase):
    def test_source_bound_spaces_work_without_touching_original(self):
        usfx,osis=synthetic_pair()
        with tempfile.TemporaryDirectory() as folder:
            original=Path(folder)/"source.osis.xml"
            output=Path(folder)/"modeled.osis.xml"
            original.write_bytes(osis)
            with patch("lsg_ephemeral_osis_candidate.validate_modeled_clone",
                       return_value={
                           "official_schema_and_policy_validated":True,
                           "modeled_clone_validation":{
                               "no_element_attribute_or_nonspace_text_mutation":True,
                           },
                       }) as inspect:
                report=prepare_ephemeral_source_spaced_osis(
                    original,usfx,output,Path(folder)/"reviewed.xsd")
            self.assertTrue(inspect.called)
            self.assertEqual(original.read_bytes(),osis)
            self.assertNotEqual(output.read_bytes(),osis)
            self.assertIn(b'</w> <note',output.read_bytes())
            self.assertEqual(report["source_verse_keys"],1)
            self.assertEqual(report["matching_source_verse_texts"],1)
            self.assertEqual(report["note_spaces_inferred_from_publisher"],1)
            self.assertTrue(report["original_bytes_preserved"])
            self.assertFalse(report["published"])

    def test_reject_mutated_cross_reference_or_original_path(self):
        usfx,osis=synthetic_pair()
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"source.xml"
            target=Path(folder)/"normalized.xml"
            source.write_bytes(osis.replace(b'<reference>Ps 1</reference>',
                                            b'<reference>Ps 2</reference>'))
            with self.assertRaisesRegex(PilotError,"unverified notes"):
                prepare_ephemeral_source_spaced_osis(
                    source,usfx,target,Path(folder)/"schema.xsd")
            self.assertFalse(target.exists())
            with self.assertRaises(PilotError):
                prepare_ephemeral_source_spaced_osis(
                    source,usfx,source,Path(folder)/"schema.xsd")

    def test_reject_clones_without_official_schema_approval(self):
        usfx,osis=synthetic_pair()
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"source.xml"
            target=Path(folder)/"modeled.xml"
            source.write_bytes(osis)
            with patch("lsg_ephemeral_osis_candidate.validate_modeled_clone",
                       return_value={"official_schema_and_policy_validated":False}):
                with self.assertRaisesRegex(PilotError,"failed pinned OSIS"):
                    prepare_ephemeral_source_spaced_osis(
                        source,usfx,target,Path(folder)/"schema.xsd")
            self.assertEqual(source.read_bytes(),osis)


if __name__=="__main__":
    unittest.main()
