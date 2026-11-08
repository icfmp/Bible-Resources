"""Offline, synthetic SWORD registry coverage tests with no Bible source data."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_v11n_coverage import parse_ceilings, compare_source_keys
from pilot_preflight import PilotError


def fixture():
    rows=[
        "NRSV\tMark\t1\t2",
        "NRSV\tJob\t1\t3",
        "Segond\tMark\t1\t2",
        "Segond\tJob\t1\t3",
        "Calvin\tMark\t1\t3",
        "Calvin\tJob\t1\t2",
        "KJV\tMark\t1\t3",
        "KJV\tJob\t1\t3",
    ]
    return parse_ceilings("\n".join(rows)+"\n")


class AllRegisteredV11nCoverageTests(unittest.TestCase):
    def test_source_only_and_empty_registry_slots_are_separate(self):
        keys=[("MRK",1,1),("MRK",1,2),("MRK",1,3),
              ("JOB",1,1),("JOB",1,2)]
        result=compare_source_keys(keys,{"MRK":"Mark","JOB":"Job"},fixture())
        by_name={row["system"]:row for row in result["candidate_registry_comparisons"]}
        self.assertEqual(result["source_reference_count"],5)
        self.assertEqual(result["registered_system_count"],4)
        self.assertEqual(by_name["Segond"]["source_references_outside_registry"],1)
        self.assertEqual(by_name["Segond"]["registry_slots_unoccupied_by_original_in_authored_chapters"],1)
        self.assertEqual(by_name["Calvin"]["source_references_outside_registry"],0)
        self.assertEqual(by_name["Calvin"]["registry_slots_unoccupied_by_original_in_authored_chapters"],0)
        self.assertEqual(result["exact_numeric_slot_candidate_names"],["Calvin"])
        self.assertFalse(result["approved_for_publication"])
        self.assertFalse(by_name["Calvin"]["original_verse_content_and_boundaries_verified"])

    def test_representable_numbers_do_not_prove_completeness_or_reference_order(self):
        keys=[("MRK",1,1),("MRK",1,3)]
        parsed=fixture()
        result=compare_source_keys(keys,{"MRK":"Mark"},parsed)
        by_name={row["system"]:row for row in result["candidate_registry_comparisons"]}
        self.assertTrue(by_name["Calvin"]["all_original_reference_numbers_have_slots"])
        self.assertEqual(by_name["Calvin"]["registry_slots_unoccupied_by_original_in_authored_chapters"],1)
        self.assertFalse(by_name["Calvin"]["exact_source_slot_set"])

    def test_unknown_books_chapters_are_never_guessed(self):
        keys=[("MRK",2,1)]
        report=compare_source_keys(keys,{"MRK":"Mark"},fixture())
        self.assertTrue(all(r["source_references_outside_registry"]==1
                            for r in report["candidate_registry_comparisons"]))
        self.assertTrue(all(r["source_chapters_not_in_registry"]==1
                            for r in report["candidate_registry_comparisons"]))

    def test_malformed_or_duplicate_register_rows_fail_closed(self):
        for invalid in (
            "",
            "Segond\tMark\t1\t2",
            "Segond\tMark\t1\t2\nNRSV\tJob\t1\t2\nSegond\tMark\t1\t3",
            "Segond\tMark\t1\t999\nNRSV\tJob\t1\t2",
            "Segond\tMark\t2\t3\nSegond\tMark\t3\t3\nNRSV\tJob\t1\t2",
            "Segond\tMark\t1\t2\nNRSV\tJob\tX\t2",
            "Segond\tMark\t1\t2\nNRSV\tJob\t1\t2\nNOT A REGISTRY\tJob\t1\t2",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(PilotError):
                    parse_ceilings(invalid)

    def test_source_mapping_must_be_complete_and_not_duplicated(self):
        rows=fixture()
        for keys,mapping in (
            ([("MRK",1,1),("JOB",1,1)],{"MRK":"Mark"}),
            ([("MRK",1,1),("JOB",1,1)],{"MRK":"Mark","JOB":"Mark"}),
            ([("MRK",1,1),("MRK",1,1)],{"MRK":"Mark"}),
            ([("MRK",0,1)],{"MRK":"Mark"}),
        ):
            with self.subTest(keys=keys,mapping=mapping):
                with self.assertRaises(PilotError):
                    compare_source_keys(keys,mapping,rows)

    def test_report_excludes_original_content(self):
        report=compare_source_keys([("MRK",1,1)],{"MRK":"Mark"},fixture())
        self.assertNotIn("TEST_BIBLE_CONTENT_SECRET",repr(report))
        self.assertIn("original_chapter_count",report)
        self.assertFalse(report["full_verse_mapping_verified"])


if __name__=="__main__":
    unittest.main()
