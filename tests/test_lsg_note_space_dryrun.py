"""Synthetic protections for reversible note-space restoration modeling."""
from pathlib import Path
import sys
import unittest
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_note_space_dryrun import simulate_source_note_spaces
from pilot_preflight import PilotError

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def fixture(*, source_space=" ", candidate_space="", changed_note=False):
    source=(
        '<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
        '<w s="H1">sera</w>'+source_space+
        '<x caller="a"><xo>1.1</xo><xt>Ps 1:1</xt></x>'
        '<w s="H2">vengé</w><ve id="1"/></p></book></usfx>'
    )
    reference="Ps 1:2" if changed_note else "Ps 1:1"
    generated=(
        f'<osis xmlns="{NS}"><osisText><div type="book" osisID="Gen">'
        '<chapter osisID="Gen.1"><p>'
        '<verse sID="Gen.1.1" osisID="Gen.1.1"/>'
        '<w lemma="strong:H1">sera</w>'+candidate_space+
        '<note type="crossReference" n="a">'
        '<reference type="annotateRef" subType="x-origin">1.1</reference>'
        '<reference>'+reference+'</reference></note>'
        '<w lemma="strong:H2">vengé</w>'
        '<verse eID="Gen.1.1"/></p></chapter></div></osisText></osis>'
    )
    return etree.fromstring(source.encode()),etree.fromstring(generated.encode())


class NoteSpaceDryrunTests(unittest.TestCase):
    def test_missing_authored_ascii_separator_is_restored_only_on_copy(self):
        source,target=fixture()
        original=etree.tostring(target)
        original_source=etree.tostring(source)
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],
                         {"source_space_modeled_in_memory":1,"source_separator_ascii_space":1})
        self.assertEqual(report["notes_with_missing_preceding_space_after_dryrun"],0)
        self.assertEqual(report["source_note_count"],1)
        self.assertTrue(report["original_candidate_unchanged"])
        self.assertNotEqual(report["candidate_before_sha256"],
                            report["candidate_draft_sha256"])
        self.assertEqual(etree.tostring(target),original)
        self.assertEqual(etree.tostring(source),original_source)
        self.assertIn(b'sera</w> <note',etree.tostring(cloned))
        self.assertNotIn(b'sera</w> <note',original)
        self.assertNotIn("vengé",repr(report))
        self.assertFalse(report["full_note_editorial_metadata_approved"])

    def test_matching_separator_is_unchanged(self):
        source,target=fixture(candidate_space=" ")
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],{"source_space_already_preserved":1})
        self.assertEqual(report["candidate_before_sha256"],
                         report["candidate_draft_sha256"])
        self.assertEqual(etree.tostring(cloned),etree.tostring(target))

    def test_absent_source_separator_is_not_invented(self):
        source,target=fixture(source_space="")
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],{"both_without_space":1})
        self.assertEqual(etree.tostring(cloned),etree.tostring(target))

    def test_candidate_extra_separator_is_not_silently_removed(self):
        source,target=fixture(source_space="",candidate_space=" ")
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],{"candidate_only_space_not_removed":1})
        self.assertEqual(etree.tostring(cloned),etree.tostring(target))

    def test_tab_is_normalized_in_clone_but_original_tabs_remain(self):
        source,target=fixture(source_space="\t")
        original_source=etree.tostring(source)
        original_target=etree.tostring(target)
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],
                         {"source_space_modeled_in_memory":1,"source_separator_tab":1})
        self.assertEqual(report["notes_with_missing_preceding_space_after_dryrun"],0)
        self.assertIn(b'sera</w> <note',etree.tostring(cloned))
        self.assertEqual(etree.tostring(source),original_source)
        self.assertEqual(etree.tostring(target),original_target)
        self.assertFalse(report["full_note_editorial_metadata_approved"])

    def test_newline_is_normalized_only_in_cloned_candidate(self):
        source,target=fixture(source_space="\n")
        original_source=etree.tostring(source)
        cloned,report=simulate_source_note_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["by_category"],
                         {"source_space_modeled_in_memory":1,"source_separator_newline":1})
        self.assertEqual(report["notes_with_missing_preceding_space_after_dryrun"],0)
        self.assertIn(b'sera</w> <note',etree.tostring(cloned))
        self.assertEqual(etree.tostring(source),original_source)
        self.assertFalse(report["full_note_editorial_metadata_approved"])

    def test_mismatched_reference_text_blocks_before_modeling(self):
        source,target=fixture(changed_note=True)
        with self.assertRaisesRegex(PilotError,"verified note identity"):
            simulate_source_note_spaces(source,target,{"GEN":"Gen"})


if __name__=="__main__":
    unittest.main()
