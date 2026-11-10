"""Generic stage-4 classification must fail closed on missing/reordered text."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from maintext_fidelity_classification import classify_compiled_numbered_maintext


class MainTextScopeClassifierTests(unittest.TestCase):
    def setUp(self):
        self.main={
            "source_mapped_numbered_verse_count":3,
            "native_numbered_verse_count":3,
            "classifications":{
                "matching_indexed_keys_checked":3,
                "source_verses_without_native_indexed_entry":0,
                "whitespace_only":3,
            },
            "first_source_only_refs":[],
            "material_differences_metadata_truncated":False,
        }
        self.scope={"mapped_numbered_source_keys":3,"unmapped_authored_book_count":0,
                    "unmapped_numbered_source_keys":0}
        self.absorbed={"source_only_reference_count":0,
                       "native_occupied_refs_without_authored_counterpart_count":0}

    def run_classification(self,*,m=None,scope=None,absorbed=None,scan=True,spot=True):
        return classify_compiled_numbered_maintext(
            m if m is not None else self.main,
            scope if scope is not None else self.scope,
            absorbed if absorbed is not None else self.absorbed,
            full_native_scan_verified=scan,exact_entry_spotcheck_verified=spot,
        )

    def test_only_whitespace_differs_still_requires_layout_review(self):
        r=self.run_classification()
        self.assertEqual(r["status"],"all_mapped_numbered_text_equal_after_whitespace_folding_only")
        self.assertTrue(r["all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding"])
        self.assertFalse(r["numbered_maintext_exact_characters_verified"])
        self.assertEqual(r["source_verses_with_whitespace_only_changes"],3)
        self.assertFalse(r["original_whitespace_layout_headings_and_poetry_verified"])
        self.assertFalse(r["publication_approved"])

    def test_exact_characters_can_be_true_but_editorial_fidelity_is_not(self):
        m=copy.deepcopy(self.main)
        m["classifications"].pop("whitespace_only")
        m["classifications"]["exact_semantic_characters"]=3
        r=self.run_classification(m=m)
        self.assertTrue(r["numbered_maintext_exact_characters_verified"])
        self.assertFalse(r["book_intro_verse_zero_and_original_book_order_verified"])

    def test_actual_text_punctuation_difference_never_passes(self):
        for name in ("word_sequence_differs",
                     "case_or_punctuation_differs_same_folded_words",
                     "word_sequence_same_punctuation_or_spacing_differs",
                     "native_raw_not_parseable_as_self_contained_xml"):
            m=copy.deepcopy(self.main)
            m["classifications"]["whitespace_only"]=2
            m["classifications"][name]=1
            with self.subTest(name=name):
                r=self.run_classification(m=m)
                self.assertEqual(r["status"],"blocked_non_whitespace_or_index_discrepancy")
                self.assertFalse(r["all_mapped_numbered_words_case_punctuation_preserved_after_whitespace_folding"])

    def test_no_missing_or_extra_source_native_keys_may_be_ignored(self):
        for modification in (
            ("m","native_numbered_verse_count",4),
            ("m","first_source_only_refs",["Gen.1.2"]),
            ("sc","unmapped_authored_book_count",1),
            ("sc","mapped_numbered_source_keys",2),
            ("a","source_only_reference_count",1),
            ("a","native_occupied_refs_without_authored_counterpart_count",1),
        ):
            m=copy.deepcopy(self.main);sc=copy.deepcopy(self.scope);a=copy.deepcopy(self.absorbed)
            target,key,value=modification
            {"m":m,"sc":sc,"a":a}[target][key]=value
            with self.subTest(modification=modification):
                self.assertEqual(self.run_classification(m=m,scope=sc,absorbed=a)["status"],
                                 "blocked_non_whitespace_or_index_discrepancy")

    def test_missing_independent_native_proof_never_passes(self):
        self.assertEqual(self.run_classification(scan=False)["status"],
                         "blocked_non_whitespace_or_index_discrepancy")
        self.assertEqual(self.run_classification(spot=False)["status"],
                         "blocked_non_whitespace_or_index_discrepancy")
        m=copy.deepcopy(self.main)
        m["material_differences_metadata_truncated"]=True
        self.assertEqual(self.run_classification(m=m)["status"],
                         "blocked_non_whitespace_or_index_discrepancy")


if __name__=="__main__":
    unittest.main()
