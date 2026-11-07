"""Synthetic 66-book fixture verifies complete text/word/note/poetry parity."""
from pathlib import Path
import tempfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_osis_parity import compare, _source_words, describe_symbol_edits

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


def fixture(*,change_word=False,missing_note=False):
    original=["<usfx>"]
    converted=[f'<osis xmlns="{NS}"><osisText>']
    for n in range(1,67):
        original.append(f'<book id="B{n:02}"><c id="1"/><p><v id="1"/>'
                        f'Alpha <w s="H123">Word{n}</w>'
                        f'<x><xo>1</xo><xt>Ps 1</xt></x> '
                        f'<q level="1">End.</q><ve id="1"/></p></book>')
        word=("Different" if n==30 and change_word else f"Word{n}")
        note="" if n==30 and missing_note else f'<note><reference osisRef="Ps.1.1">Ps 1</reference></note>'
        converted.append(f'<div type="book" osisID="Book{n}"><chapter osisID="Book{n}.1">'
                         f'<p><verse osisID="Book{n}.1.1" sID="Book{n}.1.1"/>'
                         f'Alpha <w lemma="strong:H123">{word}</w>{note} '
                         f'<lg><l level="1">End.</l></lg>'
                         f'<verse eID="Book{n}.1.1"/></p></chapter></div>')
    original.append("</usfx>")
    converted.append("</osisText></osis>")
    return "".join(original).encode(),"".join(converted).encode()


class FullSourceOsisParityTests(unittest.TestCase):
    def test_all_verses_words_note_placement_and_poetry_unchanged(self):
        raw,xml=fixture()
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"candidate.xml"
            source.write_bytes(xml)
            result=compare(source,raw)
            self.assertEqual(result["total_source_verse_keys"],66)
            self.assertEqual(result["exact_normalized_verse_text_matches"],66)
            self.assertEqual(result["exact_normalized_word_sequences"],66)
            self.assertEqual(result["matching_verse_note_counts"],66)
            self.assertEqual(result["matching_verse_poetry_line_counts"],66)
            poetry=result["source_to_candidate_poetry_structure_audit"]
            self.assertEqual(poetry["matching_per_verse_line_counts"],66)
            self.assertFalse(poetry["all_poetry_layout_verified"])
            owned=result["source_to_candidate_poetry_verse_owned_audit"]
            self.assertEqual(owned["matching_verse_line_counts_with_text_ownership"],66)
            self.assertEqual(owned["matching_verse_line_text_sequences_ignoring_whitespace"],66)
            self.assertEqual(result["source_word_markers"],66)
            self.assertEqual(result["converted_word_markers"],66)
            self.assertFalse(result["all_note_text_and_reference_targets_verified"])
            self.assertTrue(result["all_strong_attributes_verified"])
            self.assertEqual(result["source_to_candidate_strong_id_audit"]["matching_ordered_word_strong_ids"],66)

    def test_strong_id_change_detected_despite_identical_bible_words(self):
        raw,xml=fixture()
        xml=xml.replace(b"strong:H123",b"strong:H999",1)
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"candidate.xml"
            source.write_bytes(xml)
            result=compare(source,raw)
            self.assertEqual(result["exact_normalized_word_sequences"],66)
            self.assertFalse(result["all_strong_attributes_verified"])
            self.assertEqual(result["source_to_candidate_strong_id_audit"]["matching_ordered_word_strong_ids"],65)
            self.assertEqual(len(result["source_to_candidate_strong_id_audit"]["first_mismatching_strong_id_slots"]),1)

    def test_word_text_change_rejected_even_when_reference_keys_match(self):
        raw,xml=fixture(change_word=True)
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"candidate.xml"
            source.write_bytes(xml)
            result=compare(source,raw)
            self.assertEqual(result["exact_normalized_word_sequences"],65)
            self.assertEqual(result["exact_normalized_verse_text_matches"],65)
            self.assertTrue(result["first_differences"])
            self.assertEqual(result["first_differences"][0]["reference"],"B30.1.1")

    def test_xml_editorial_comments_are_not_added_to_verse_text(self):
        raw,xml=fixture()
        # u2o emits these marker comments at section/poetry boundaries.
        # Count canonical words only, while leaving the XML source intact.
        xml=xml.replace(b"Alpha <w",b"<!-- s1 --><!-- r -->Alpha <w")
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"candidate.xml"
            source.write_bytes(xml)
            result=compare(source,raw)
            self.assertEqual(result["exact_normalized_verse_text_matches"],66)
            self.assertEqual(result["verse_text_matches_ignoring_only_unicode_whitespace"],66)
            self.assertEqual(result["exact_normalized_word_sequences"],66)

    def test_non_whitespace_diagnostics_are_text_free_and_classified(self):
        changed=describe_symbol_edits("Au commencement, Dieu.", "Au commencement Dieu.")
        self.assertEqual(len(changed),1)
        self.assertEqual(changed[0]["operation"],"delete")
        self.assertEqual(changed[0]["source_alphanumeric"],0)
        self.assertEqual(changed[0]["source_codepoints"],1)
        self.assertNotIn("commencement",str(changed))
        self.assertEqual(describe_symbol_edits("Alpha  beta", "Alpha beta"),[])
        changed=describe_symbol_edits("Alpha beta", "Alpha betta")
        self.assertTrue(any(x["generated_alphanumeric"]>0 for x in changed))
        self.assertNotIn("betta",str(changed))
        self.assertNotIn("beta",str(changed))

    def test_note_and_section_heading_words_are_not_verse_words(self):
        # USFX plain-verse extraction already excludes editorial subtrees.
        # Do not invent word or poetry mismatches by counting them here.
        original=(b'<usfx><book id="GEN"><c id="1"/>'
                  b'<p><v id="1"/>Text <w s="H1">canonical</w>'
                  b'<x><w s="H2">annotation</w><q>quoted line</q></x>'
                  b'<s><w s="H3">section title</w></s>'
                  b'<p sfm="r"><w s="H4">reference heading</w></p>'
                  b'<q level="1">poetic line</q><ve id="1"/></p>'
                  b'</book></usfx>')
        words, notes, poetry = _source_words(original)
        self.assertEqual(words[("GEN",1,1)], ["canonical"])
        self.assertEqual(notes[("GEN",1,1)], 1)
        self.assertEqual(poetry[("GEN",1,1)], 1)

    def test_dropped_note_cannot_pass_counts(self):
        raw,xml=fixture(missing_note=True)
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"candidate.xml"
            source.write_bytes(xml)
            result=compare(source,raw)
            self.assertEqual(result["matching_verse_note_counts"],65)
            self.assertEqual(result["converted_note_markers"],65)


if __name__=="__main__":
    unittest.main()
