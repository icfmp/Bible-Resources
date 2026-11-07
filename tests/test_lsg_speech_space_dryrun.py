"""Protect source-authorized whitespace modeling after speech closings."""
import sys
import unittest
from pathlib import Path
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_speech_space_dryrun import simulate_source_speech_spaces

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def sample(*, source_space=" ", candidate_space="", change_word=False,
           speech_indent=0):
    source=(
        '<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
        '<wj><w s="H123">Lève-toi,</w></wj>'
        +source_space+
        '<w s="H321">dit</w><ve id="1"/></p></book></usfx>')
    prefix="<w lemma=\"strong:H44\">Added</w>" if speech_indent else ""
    say="Different" if change_word else "Lève-toi,"
    osis=(
        f'<osis xmlns="{NS}"><osisText>'
        '<div type="book" osisID="Gen"><chapter osisID="Gen.1">'
        '<p><verse sID="Gen.1.1" osisID="Gen.1.1"/>'
        +prefix+
        '<q who="Jesus" marker=""><w lemma="strong:H123">'+say+'</w></q>'
        +candidate_space+
        '<w lemma="strong:H321">dit</w><verse eID="Gen.1.1"/>'
        '</p></chapter></div></osisText></osis>')
    return etree.fromstring(source.encode()),etree.fromstring(osis.encode())


class JesusSpeechSpaceTests(unittest.TestCase):
    def test_missing_space_is_only_added_to_an_isolated_copy(self):
        source,target=sample()
        original_source=etree.tostring(source)
        original_target=etree.tostring(target)
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["source_speech_segments"],1)
        self.assertEqual(report["candidate_speech_segments"],1)
        self.assertEqual(report["categories"][
            "source_attested_speech_separator_modeled"],1)
        self.assertIn(b'</q> <w',etree.tostring(clone))
        self.assertEqual(etree.tostring(source),original_source)
        self.assertEqual(etree.tostring(target),original_target)
        self.assertFalse(report["approved_for_publication"])
        self.assertNotIn("Lève-toi",repr(report))

    def test_matching_space_is_not_changed(self):
        source,target=sample(candidate_space=" ")
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["categories"]["speech_separator_already_present"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))

    def test_no_authored_space_is_not_invented(self):
        source,target=sample(source_space="")
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["categories"]["speech_separator_absent_in_both"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))

    def test_candidate_extra_space_is_not_removed_silently(self):
        source,target=sample(source_space="",candidate_space=" ")
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["categories"][
            "candidate_only_speech_separator_not_removed"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))

    def test_changed_quote_contents_block_simulation(self):
        source,target=sample(change_word=True)
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["categories"]["unverified_speech_segment_identity"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))

    def test_different_word_anchor_blocks_simulation(self):
        source,target=sample(speech_indent=1)
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["categories"]["unverified_speech_segment_identity"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))

    def test_missing_original_speech_span_blocks_model(self):
        source,target=sample()
        wj=next(source.iter("wj"))
        wj.tag="not-wj"
        clone,report=simulate_source_speech_spaces(source,target,{"GEN":"Gen"})
        self.assertEqual(report["candidate_only_speech_verse_count"],1)
        self.assertEqual(etree.tostring(clone),etree.tostring(target))


if __name__=="__main__":
    unittest.main()
