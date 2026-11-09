"""Source-to-stock-SWORD layout start-position regression tests (no Bible text)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_stock_layout_positions import compare_compiled_layout_start_positions
from pilot_preflight import PilotError


class LayoutPositionTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.osis=Path(self.temp.name)/"synthetic.osis.xml"
        self.osis.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
 <osisText><div type="book" osisID="Gen"><chapter sID="Gen.1"/>
 <title>heading</title><p><verse sID="Gen.1.1"/>
 <w>a</w><lg><q><w>b</w></q></lg><verse eID="Gen.1.1"/>
 <w>between verses</w><verse sID="Gen.1.2"/><w>c</w>
 <verse eID="Gen.1.2"/></p></div></osisText></osis>''',
                             encoding="utf-8")
        self.plan=[
            ("Genesis 0:0","Gen","1"),
            ("Genesis 1:0","Gen","1"),
            ("Genesis 1:1","Gen","0"),
            ("Genesis 1:2","Gen","0"),
        ]
        self.rows=[
            "Gen\tGenesis 0:0\t0\ttitle:0",
            "Gen\tGenesis 1:0\t0\tp:0",
            "Gen\tGenesis 1:1\t2\tlg:1,q:1",
            "Gen\tGenesis 1:2\t2\t",
        ]

    def test_book_wide_positions_match_with_starts_in_intro_entries(self):
        report=compare_compiled_layout_start_positions(
            self.osis,self.plan,self.rows)
        self.assertEqual(report["status"],
                         "compiled_book_global_layout_start_positions_verified")
        self.assertEqual(report["books_matching_all_layout_start_word_offsets"],1)
        self.assertEqual(report["books_matching_full_cross_type_start_order"],1)
        self.assertEqual(report["source_layout_starts_by_kind"]["p"],1)
        self.assertEqual(report["source_layout_starts_by_kind"]["title"],1)
        self.assertFalse(report["end_boundaries_verified"])

    def test_interverse_word_relocation_preserves_book_position(self):
        rows=list(self.rows)
        rows[2]="Gen\tGenesis 1:1\t3\tlg:1,q:1"
        rows[3]="Gen\tGenesis 1:2\t1\t"
        result=compare_compiled_layout_start_positions(
            self.osis,self.plan,rows)
        self.assertEqual(result["status"],
                         "compiled_book_global_layout_start_positions_verified")

    def test_moved_quotation_is_detected_even_when_counts_match(self):
        changed=list(self.rows)
        changed[2]="Gen\tGenesis 1:1\t2\tlg:1,q:2"
        report=compare_compiled_layout_start_positions(
            self.osis,self.plan,changed)
        self.assertEqual(report["status"],
                         "compiled_layout_start_positions_need_review")
        self.assertEqual(report["source_layout_starts_by_kind"]["q"],1)
        self.assertEqual(report["compiled_layout_starts_by_kind"]["q"],1)
        self.assertEqual(report["first_layout_word_offset_differences"][0]
                         ["marker"],"q")

    def test_missing_marker_or_word_tag_blocks(self):
        for changed in (
            ["Gen\tGenesis 0:0\t0\t",*self.rows[1:]],
            [*self.rows[:3],"Gen\tGenesis 1:2\t1\t"],
        ):
            with self.subTest(changed=changed):
                report=compare_compiled_layout_start_positions(
                    self.osis,self.plan,changed)
                self.assertEqual(report["status"],
                                 "compiled_layout_start_positions_need_review")

    def test_malformed_or_out_of_bounds_marker_rejected(self):
        for bad in (
            "Gen\tGenesis 1:1\t2\tq:3",
            "Gen\tGenesis 1:1\t2\tbad:1",
            "Gen\tGenesis 1:1\t2\tq:-1",
            "Gen\tGenesis 1:1\t2\tq:NaN",
            "Gen\tGenesis 1:1\t2\tq:0,",
            "Gen\tGenesis 1:2\t2\tq:1",
        ):
            with self.subTest(bad=bad),self.assertRaises(PilotError):
                compare_compiled_layout_start_positions(
                    self.osis,self.plan,self.rows[:2]+[bad]+self.rows[3:])


if __name__=="__main__":
    unittest.main()
