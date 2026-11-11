"""Synthetic source-vs-native body boundary (not typography) audit regression."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_osis_boundary_positions import (
    authorial_book_streams, NativeBookStreams,
    compare_book_boundary_positions, BoundaryScreenError,
)

OSIS=(b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
      b'<div type="book" osisID="Gen"><chapter osisID="Gen.1">'
      b'<title>PRIVATE TITLE</title>'
      b'<p><verse osisID="Gen.1.1"/>alpha<note>PRIVATE NOTE</note> beta</p>'
      b'<lg><l>poetry</l></lg></chapter></div></osis>')


def native(first=b'<div type="x-p" sID="p"/>',
           second=(b'alpha<note>PRIVATE NOTE</note> beta'
                   b'<div type="x-p" eID="p"/>'
                   b'<lg sID="g"/><l sID="l"/>poetry'
                   b'<l eID="l"/><lg eID="g"/>')):
    compiled=NativeBookStreams()
    compiled.observe("I","Gen",b'<title>PRIVATE TITLE</title>'+first)
    compiled.observe("K","Gen.1.1",second)
    return compiled


class OriginalNativeBoundaryPositionTests(unittest.TestCase):
    def test_source_and_native_boundary_positions_and_text_agree(self):
        proof=compare_book_boundary_positions(authorial_book_streams(OSIS),native())
        self.assertTrue(proof["all_book_body_nonspace_and_boundary_events_equal"])
        self.assertEqual(proof["counts"]["books_compared"],1)
        self.assertEqual(proof["counts"]["source_p_open_events"],1)
        self.assertEqual(proof["counts"]["source_l_open_events"],1)
        self.assertEqual(proof["counts"]["source_lg_open_events"],1)
        self.assertEqual(proof["counts"]["boundary_event_positions_equal"],6)
        self.assertFalse(proof["literal_whitespace_or_exact_typography_verified"])
        self.assertNotIn("PRIVATE",str(proof))

    def test_moved_line_start_does_not_pass_even_when_words_equal(self):
        changed=native(second=(b'alpha<note>PRIVATE NOTE</note>'
                               b'<lg sID="g"/><l sID="l"/> beta'
                               b'<div type="x-p" eID="p"/>poetry'
                               b'<l eID="l"/><lg eID="g"/>'))
        proof=compare_book_boundary_positions(authorial_book_streams(OSIS),changed)
        self.assertFalse(proof["all_book_body_nonspace_and_boundary_events_equal"])
        self.assertGreater(proof["counts"]["boundary_event_groups_unverified_or_different"],0)
        self.assertNotIn("PRIVATE",str(proof))

    def test_actual_changed_words_or_missing_prose_blocks_position_claim(self):
        broken=native(second=b'wrong text<div type="x-p" eID="p"/>')
        result=compare_book_boundary_positions(authorial_book_streams(OSIS),broken)
        self.assertFalse(result["all_book_body_nonspace_and_boundary_events_equal"])
        self.assertEqual(result["counts"]["books_with_unmatched_full_body_stream"],1)

    def test_malformed_or_nested_source_rejected(self):
        with self.assertRaises(BoundaryScreenError):
            authorial_book_streams(
                b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
                b'<div type="book" osisID="Gen"><div type="book" osisID="Exod"/>'
                b'</div></osis>')

    def test_compiled_extra_top_prose_not_silently_accepted(self):
        compiled=native()
        compiled.observe("U","TOP:1",b"PRIVATE EXTRA TEXT")
        proof=compare_book_boundary_positions(authorial_book_streams(OSIS),compiled)
        self.assertFalse(proof["all_book_body_nonspace_and_boundary_events_equal"])
        self.assertGreater(proof["native_anonymous_top_nonspace_body_characters"],0)
        self.assertNotIn("PRIVATE",str(proof))

    def test_native_unbalanced_xml_fails_closed(self):
        with self.assertRaises(ValueError):
            native(second=b'<l sID="x">BROKEN')


if __name__=="__main__":
    unittest.main()
