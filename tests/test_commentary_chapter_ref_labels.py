"""Synthetic original ThML scripRef label location tests: exact target never certified."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from commentary_chapter_ref_labels import link_label_location
from pilot_preflight import PilotError


class OriginalScriptureReferenceLabelTests(unittest.TestCase):
    def test_exact_original_label_inside_real_stock_reference_tag(self):
        result=link_label_location(
            [{"text":"Genesis 1:1", "attribute_name_types":["passage","osisRef"],
              "private_original_osisRef_target":"Gen.1.1"}],
            b'<p>Some words. <reference osisRef="Gen.1.1">Genesis 1:1</reference></p>'
        )
        self.assertEqual(result["original_scripRef_to_stock_text_location_classes"],
                         {"literal_label_inside_stock_reference_element":1})
        self.assertEqual(result["selected_stock_reference_elements_with_osisRef_attribute"],1)
        self.assertEqual(result["original_scripRef_attribute_name_occurrences"],
                         {"passage":1,"osisRef":1})
        self.assertEqual(result["original_scripRef_with_nonempty_osisRef_target_count"],1)
        self.assertEqual(result["original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"],1)
        self.assertTrue(result["source_and_selected_stock_reference_targets_exact_ordered_match"])
        self.assertNotIn("Genesis",json.dumps(result))
        self.assertTrue(result["matched_label_does_not_validate_reference_target_or_edition"])

    def test_original_label_can_be_plain_stock_text_without_reference_tag(self):
        result=link_label_location(
            [{"text":"Mark 3", "attribute_name_types":[]}],
            b"<p>A title mentions Mark 3 but without a real reference tag</p>"
        )
        self.assertEqual(result["original_scripRef_to_stock_text_location_classes"],
                         {"literal_label_in_stock_text_outside_confirmed_reference_element":1})

    def test_punctuation_drift_is_not_exact_text_or_target_parity(self):
        result=link_label_location(
            [{"text":"Gen. 1:1", "attribute_name_types":[]}],
            b'<p><reference osisRef="Gen.1.1">Gen 1,1</reference></p>'
        )
        self.assertEqual(result["original_scripRef_to_stock_text_location_classes"],
                         {"word_tokens_in_stock_reference_element_different_punctuation":1})

    def test_unlocated_empty_and_independent_targets_do_not_count_as_verified(self):
        result=link_label_location(
            [{"text":"Exodus special", "attribute_name_types":[]},
             {"text":"", "attribute_name_types":[]}],
            b'<reference osisRef="Exod.1.1">An unrelated reference.</reference>'
        )
        self.assertEqual(result["original_scripRef_to_stock_text_location_classes"],
                         {"empty_original_label_unreviewed":1,
                          "original_label_text_not_located_in_selected_stock_entry":1})

    def test_different_original_reference_target_is_not_guessed_from_label(self):
        out=link_label_location(
            [{"text":"Genesis 1:1", "attribute_name_types":["osisRef"],
              "private_original_osisRef_target":"Bible:Gen.1.1"}],
            b'<reference osisRef="Gen.1.1">Genesis 1:1</reference>'
        )
        self.assertEqual(
            out["original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"],0)
        self.assertFalse(out["source_and_selected_stock_reference_targets_exact_ordered_match"])
        self.assertNotIn("Bible:Gen.1.1",json.dumps(out))

    def test_same_reference_values_in_different_order_not_approved_as_ordered(self):
        out=link_label_location(
            [{"text":"first", "attribute_name_types":["osisRef"],
              "private_original_osisRef_target":"A"},
             {"text":"second", "attribute_name_types":["osisRef"],
              "private_original_osisRef_target":"B"}],
            b'<reference osisRef="B">second</reference><reference osisRef="A">first</reference>'
        )
        self.assertEqual(
            out["original_scripRef_osisRef_targets_exact_value_multiset_matches_in_stock"],2)
        self.assertFalse(out["source_and_selected_stock_reference_targets_exact_ordered_match"])

    def test_original_markup_recovery_or_unsafe_attribute_name_fails_closed(self):
        with self.assertRaises(PilotError):
            link_label_location([{"text":"Gen 1","attribute_name_types":[]}],
                                b"<reference>Unclosed</wrong>")
        with self.assertRaises(PilotError):
            link_label_location([{"text":"Gen 1","attribute_name_types":["bad <"]}],
                                b"<p>Gen 1</p>")


if __name__=="__main__":
    unittest.main()
