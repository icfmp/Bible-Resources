"""Synthetic integrity gates for private, source-backed OSIS whitespace models."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_model_validation import inspect_space_only_clone, validate_modeled_clone
from pilot_preflight import PilotError
from guard_osis import StructureFailure

OSIS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def source_tree():
    return etree.fromstring((
        f'<osis xmlns="{OSIS}"><osisText><div type="book" osisID="Gen">'
        '<chapter osisID="Gen.1"><p><verse sID="Gen.1.1"/>'
        'Alpha<w lemma="strong:H1">Beta</w><note type="crossReference" n="a">'
        '<reference>Ps 1</reference></note><lg><l level="1">Poetry</l></lg>'
        '<verse eID="Gen.1.1"/></p></chapter></div></osisText></osis>'
    ).encode())


def deep_clone(original):
    return etree.fromstring(etree.tostring(original))


class ModeledCloneGateTests(unittest.TestCase):
    def test_only_attested_ascii_space_insertions_are_permitted(self):
        original=source_tree()
        copy=deep_clone(original)
        word=next(copy.iter(f"{{{OSIS}}}w"))
        word.tail=" " + (word.tail or "")
        word.text=" "+word.text
        report=inspect_space_only_clone(original,copy)
        self.assertEqual(report["total_inserted_ascii_spaces"],2)
        self.assertTrue(report["no_element_attribute_or_nonspace_text_mutation"])
        self.assertEqual(next(original.iter(f"{{{OSIS}}}w")).text,"Beta")

    def test_missing_original_space_must_be_rejected(self):
        original=source_tree()
        next(original.iter(f"{{{OSIS}}}w")).tail="  original"
        altered=deep_clone(original)
        next(altered.iter(f"{{{OSIS}}}w")).tail=" original"
        with self.assertRaisesRegex(PilotError,"non-space XML tail"):
            inspect_space_only_clone(original,altered)

    def test_canonical_word_or_note_text_changes_are_rejected(self):
        original=source_tree()
        for tag,content in [("w","Wrong"),("reference","Ps 2")]:
            altered=deep_clone(original)
            next(altered.iter(f"{{{OSIS}}}{tag}")).text=content
            with self.assertRaisesRegex(PilotError,"non-space XML text"):
                inspect_space_only_clone(original,altered)

    def test_changed_milestone_lemma_or_poetry_structure_rejected(self):
        original=source_tree()
        for tag,attribute,value in [
            ("verse","sID","Gen.1.2"),
            ("w","lemma","strong:H2"),
            ("l","level","2"),
        ]:
            changed=deep_clone(original)
            next(changed.iter(f"{{{OSIS}}}{tag}")).set(attribute,value)
            with self.assertRaisesRegex(PilotError,"structure or attributes"):
                inspect_space_only_clone(original,changed)
        removed=deep_clone(original)
        line=next(removed.iter(f"{{{OSIS}}}l"))
        line.getparent().remove(line)
        with self.assertRaisesRegex(PilotError,"element count"):
            inspect_space_only_clone(original,removed)

    def test_metadata_only_dryrun_does_not_approve_publication(self):
        original=source_tree()
        clone=deep_clone(original)
        next(clone.iter(f"{{{OSIS}}}w")).tail=" "
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"test-clone.osis.xml"
            path.write_bytes(etree.tostring(clone))
            no_schema=validate_modeled_clone(original,clone,path,None)
            self.assertFalse(no_schema["official_schema_and_policy_validated"])
            self.assertFalse(no_schema["approved_for_publication"])
            with patch("lsg_model_validation.inspect_osis",
                       return_value={"schema_sha256":"synthetic-digest"}) as validator:
                result=validate_modeled_clone(original,clone,path,Path(tmp)/"schema.xsd")
            validator.assert_called_once()
            self.assertEqual(result["status"],"modeled_clone_schema_and_policy_validated_only")
            self.assertEqual(result["schema_sha256"],"synthetic-digest")
            self.assertFalse(result["approved_for_publication"])
            self.assertEqual(original.find(f".//{{{OSIS}}}w").tail,None)

    def test_schema_failure_is_reported_not_waived(self):
        original=source_tree()
        clone=deep_clone(original)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"clone.xml"
            path.write_bytes(etree.tostring(clone))
            issue=StructureFailure(path,1,"OSIS_SCHEMA_INVALID","test-only")
            with patch("lsg_model_validation.inspect_osis",side_effect=issue):
                result=validate_modeled_clone(original,clone,path,Path(tmp)/"schema.xsd")
        self.assertEqual(result["status"],"modeled_clone_schema_or_policy_blocked")
        self.assertFalse(result["official_schema_and_policy_validated"])

    def test_on_disk_clone_must_match_audited_xml(self):
        original=source_tree()
        clone=deep_clone(original)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"clone.xml"
            path.write_bytes(etree.tostring(original).replace(b"Beta",b"Gamma"))
            with self.assertRaisesRegex(PilotError,"do not match audited clone"):
                validate_modeled_clone(original,clone,path,Path(tmp)/"schema.xsd")


if __name__=="__main__":
    unittest.main()
