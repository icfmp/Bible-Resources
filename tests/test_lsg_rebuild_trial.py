"""Offline, source-free validation of candidate LSG OSIS structure analysis."""
from pathlib import Path
import tempfile
import zipfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_rebuild_trial import _osis_summary,_safe_files,_marker_evidence
from pilot_preflight import PilotError

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def sample_sources(drop_osis_verse=False):
    books=list(range(1,67))
    usfx=["<usfx>"]
    osis=[f'<osis xmlns="{NS}"><osisText>']
    for i in books:
        usfx.append(f'<book id="BK{i:02}"><c id="1"/><v id="1"/>Example<ve id="1"/></book>')
        osis.append(f'<div type="book" osisID="Book{i}"><chapter osisID="Book{i}.1">')
        if not drop_osis_verse or i!=32:
            osis.append(f'<verse osisID="Book{i}.1.1"/>Example')
        osis.append("</chapter></div>")
    return ("".join(usfx)+"</usfx>").encode(),("".join(osis)+"</osisText></osis>").encode()


class LSGRebuildTrialTests(unittest.TestCase):
    def test_editorial_marker_gate_uses_content_ownership_not_opening_position(self):
        report={
            "total_source_verse_keys":66,
            "exact_normalized_word_sequences":66,
            "matching_verse_note_counts":66,
            "matching_verse_poetry_line_counts":65,
            "unconverted_usfm_markup_diagnostic":{"no_unconverted_usfm_markup":True},
            "source_to_candidate_poetry_verse_owned_audit":{
                "all_poetry_segments_and_levels_verified":True,
                "all_selah_text_and_verse_positions_verified":True,
            },
        }
        evidence=_marker_evidence(report)
        self.assertFalse(evidence["legacy_poetry_opening_position_counts_equal"])
        self.assertTrue(evidence["source_marker_counts_parity"])
        self.assertFalse(evidence["full_poetry_editorial_layout_approved"])
        report["source_to_candidate_poetry_verse_owned_audit"][
            "all_selah_text_and_verse_positions_verified"]=False
        self.assertFalse(_marker_evidence(report)["source_marker_counts_parity"])

    def test_source_key_parity_requires_all_books_and_all_verses(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"candidate.xml"
            source,candidate=sample_sources()
            path.write_bytes(candidate)
            result=_osis_summary(path,source,[])
            self.assertEqual(result["publisher_source_verse_keys"],66)
            self.assertEqual(result["converted_verse_openings"],66)
            self.assertEqual(result["verse_keys_missing_from_converted"],0)
            self.assertEqual(result["verse_keys_unexpected_in_converted"],0)
            self.assertFalse(result["generated_xml_is_original_source"])
            self.assertFalse(result["notes_verified"])

    def test_single_dropped_verse_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"candidate.xml"
            source,candidate=sample_sources(drop_osis_verse=True)
            path.write_bytes(candidate)
            result=_osis_summary(path,source,[])
            self.assertEqual(result["verse_keys_missing_from_converted"],1)
            self.assertIn("Book32.1.1",result["missing_first_30"])

    def test_source_zip_unpacked_only_after_security_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            archive=root/"bad.zip"
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("../bad.usfm","not Scripture")
            with self.assertRaisesRegex(PilotError,"unsafe"):
                _safe_files(archive,root/"output")
            self.assertFalse((root/"bad.usfm").exists())


if __name__=="__main__":
    unittest.main()
