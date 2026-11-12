"""Pure semantic structural corruption regressions; no Bible content or network."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from source_native_structure_topology import (
    compare_structural_event_topology,StructureTopologyError
)


def anchor(word, ref="Gen.1.1", scope="numbered"):
    return {
        "word_ordinal":word,
        "nonwhitespace_codepoint_ordinal":word*5,
        "inside_word":False,
        "reference":ref,
        "record_scope":scope,
    }


def event(kind,start,end,begin_ref="Gen.1.1",end_ref="Gen.1.1"):
    return {
        "kind":kind,
        "open":anchor(start,begin_ref),
        "close":anchor(end,end_ref),
    }


def input_books():
    return {"Gen":(
        ["SECRET SOURCE WORD " + str(i) for i in range(6)],
        [
            event("p",0,3,"Gen.1.1","Gen.1.2"),
            event("q",1,2,"Gen.1.1","Gen.1.1"),
            event("p",3,6,"Gen.1.2","Gen.1.3"),
        ],
    )}


class StructuralTopologyTest(unittest.TestCase):
    def pair(self, changed=None):
        source=input_books()
        native=copy.deepcopy(source) if changed is None else changed
        return compare_structural_event_topology(source,native)

    def test_exact_open_close_word_codepoint_order_without_layout_claims(self):
        receipt=self.pair()
        self.assertTrue(receipt["all_source_native_p_q_open_close_event_topology_match"])
        self.assertTrue(receipt["source_native_exact_record_scope_verified"])
        self.assertTrue(receipt["same_boundary_event_order_unambiguous"])
        self.assertFalse(receipt["source_original_style_and_linebreak_fidelity_verified"])
        self.assertFalse(receipt["editorial_or_publication_approved"])
        self.assertEqual(receipt["source_native_event_count_and_topology_categories"][
            "paired_open_close_word_and_codepoint_positions_equal"],3)
        self.assertNotIn("SECRET SOURCE WORD",json.dumps(receipt))
        self.assertEqual(receipt["source_event_fingerprint_sha256"],
                         receipt["compiled_event_fingerprint_sha256"])

    def test_moving_only_close_or_open_preserving_all_counts_blocks(self):
        for index,boundary,change in ((0,"close",2),(0,"open",1),
                                       (2,"close",5),(2,"open",4)):
            native=input_books()
            native["Gen"][1][index][boundary]=anchor(change)
            with self.subTest(index=index,boundary=boundary):
                receipt=self.pair(native)
                self.assertFalse(
                    receipt["all_source_native_p_q_open_close_event_topology_match"])
                self.assertEqual(receipt["status"],
                                 "source_native_structural_topology_differs")
                cats=receipt["source_native_event_count_and_topology_categories"]
                self.assertEqual(cats["source_p_opens"],cats["native_p_opens"])
                self.assertEqual(cats["source_q_opens"],cats["native_q_opens"])
                self.assertGreater(
                    cats["closing_word_or_codepoint_position_differences"]+
                    cats["opening_word_or_codepoint_position_differences"]+
                    cats["native_openings_out_of_source_order"],0)

    def test_event_swap_and_same_kind_swap_caught_even_with_equal_counts(self):
        for i,j in ((0,1),(0,2)):
            native=input_books()
            native["Gen"][1][i],native["Gen"][1][j]=(
                native["Gen"][1][j],native["Gen"][1][i])
            receipt=self.pair(native)
            self.assertFalse(receipt["all_source_native_p_q_open_close_event_topology_match"])
            self.assertEqual(receipt["status"],"source_native_structural_topology_differs")

    def test_duplicate_opening_deleted_close_or_reversed_range_block(self):
        for kind in ("duplicate","missing","reversed"):
            native=input_books()
            if kind=="duplicate":
                native["Gen"][1].append(copy.deepcopy(native["Gen"][1][0]))
            elif kind=="missing":
                native["Gen"][1][1]["close"]=None
            else:
                native["Gen"][1][1]["close"]=anchor(0)
            with self.subTest(kind=kind):
                receipt=self.pair(native)
                self.assertEqual(receipt["status"],"source_native_structural_topology_differs")

    def test_overlapping_crossing_events_block_even_on_same_source_and_native(self):
        original=input_books()
        original["Gen"][1][1]["close"]=anchor(4)
        result=compare_structural_event_topology(original,copy.deepcopy(original))
        self.assertEqual(result["status"],"source_native_structural_topology_differs")
        self.assertGreater(result["source_native_event_count_and_topology_categories"][
            "source_crossing_open_close_events"],0)

    def test_equal_coordinate_same_kind_opening_not_automatically_certified(self):
        source=input_books()
        source["Gen"][1][1]["open"]=copy.deepcopy(
            source["Gen"][1][0]["open"])
        result=compare_structural_event_topology(source,copy.deepcopy(source))
        self.assertEqual(result["status"],
                         "source_native_structural_topology_positions_equal_scope_review")
        self.assertFalse(result["same_boundary_event_order_unambiguous"])

    def test_cross_verse_and_intro_scope_classified_separately_from_positions(self):
        source=input_books()
        native=copy.deepcopy(source)
        native["Gen"][1][0]["close"]=anchor(3,"Gen.1.3")
        native["Gen"][1][2]["open"]=anchor(3,"Gen.0.0","native_intro")
        result=compare_structural_event_topology(source,native)
        self.assertTrue(result["all_source_native_p_q_open_close_event_topology_match"])
        self.assertFalse(result["source_native_exact_record_scope_verified"])
        self.assertEqual(result["status"],
                         "source_native_structural_topology_positions_equal_scope_review")
        self.assertEqual(result["source_native_event_count_and_topology_categories"][
            "record_or_verse_zero_scope_differences_for_review"],2)
        self.assertNotIn("SECRET SOURCE WORD",json.dumps(result))

    def test_independent_usfx_and_real_sword_fragment_parsers_cross_verse(self):
        from test_source_native_word_boundaries import original, compiled
        source,_source_counts=original()
        native,_native_counts=compiled()
        result=compare_structural_event_topology(source,native)
        self.assertTrue(
            result["all_source_native_p_q_open_close_event_topology_match"])
        # The real native x-p milestone opens in 'Gen.1' intro, while
        # original USFX opens at the same lexical place in a different
        # source-between-verses scope. Never infer literal record identity.
        self.assertFalse(result["source_native_exact_record_scope_verified"])
        self.assertEqual(
            result["status"],
            "source_native_structural_topology_positions_equal_scope_review")
        self.assertNotIn("PRIVATE TITLE",str(result))
        self.assertNotIn("alpha",str(result))
        early=(b'alpha <l sID="line"/>beta<l eID="line"/>'
               b'<div type="x-p" eID="p1"/> gamma '
               b'<div type="x-p" sID="p2"/>')
        shifted,_counts=compiled(first=early)
        negative=compare_structural_event_topology(source,shifted)
        self.assertEqual(negative["status"],
                         "source_native_structural_topology_differs")
        self.assertGreater(negative[
            "source_native_event_count_and_topology_categories"][
            "closing_word_or_codepoint_position_differences"],0)

    def test_unsafe_reference_scope_or_private_word_not_disclosed(self):
        source=input_books()
        source["Gen"][1][0]["close"]=anchor(3,"PRIVATE NOTE CONTENT")
        with self.assertRaises(StructureTopologyError):
            compare_structural_event_topology(source,input_books())
        source=input_books()
        source["Gen"][1][0]["open"]["record_scope"]="private-scripture"
        with self.assertRaises(StructureTopologyError):
            compare_structural_event_topology(source,input_books())


if __name__=="__main__":
    unittest.main()
