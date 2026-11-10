"""Native original SWORD markup counters cannot leak biblical text."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from native_sword_markup_census import NativeMarkupCensus
from source_native_maintext_probe import native_raw_main_text


class NativeMarkupCensusTests(unittest.TestCase):
    def test_counts_actual_raw_verse_markup_including_notes_without_exposing_values(self):
        inspector = NativeMarkupCensus()
        raw = (
            b'<p>PRIVATE VERSE WORDS</p><milestone type="x-q1"/>'
            b'<lg><l>PRIVATE POEM WORDS</l></lg>'
            b'<note n="PRIVATE_CALLER">PRIVATE NOTE BODY</note>'
            b'<title>PRIVATE HEADING TEXT</title>'
            b'<reference osisRef="PRIVATE_TARGET">PRIVATE LINK TEXT</reference>'
        )
        main, excluded = native_raw_main_text(
            raw, markup_census=inspector, reference="Ps.23.1"
        )
        self.assertIn("PRIVATE VERSE", main)
        self.assertNotIn("PRIVATE NOTE", main)
        self.assertEqual(excluded["note"], 1)
        result = inspector.finish()
        self.assertEqual(result["native_numbered_verse_fragments_inspected"], 1)
        self.assertEqual(result["native_raw_element_counts"]["p"], 1)
        self.assertEqual(result["native_raw_element_counts"]["lg"], 1)
        self.assertEqual(result["native_raw_element_counts"]["l"], 1)
        self.assertEqual(result["native_raw_element_counts"]["note"], 1)
        self.assertEqual(result["native_structural_category_element_counts"]["poetry_like_milestone"], 1)
        self.assertEqual(result["native_structural_category_element_counts"]["explicit_poetry_or_linebreak_element"], 2)
        self.assertEqual(result["native_structural_category_element_counts"]["explicit_paragraph_element"], 1)
        self.assertEqual(result["native_numbered_verses_with_structural_category"]["note_element"], 1)
        self.assertEqual(result["first_reference_ids_without_scripture"]["note_element"], ["Ps.23.1"])
        self.assertFalse(result["raw_markup_content_or_attribute_values_exposed"])
        self.assertFalse(result["source_to_compiled_structure_fidelity_verified"])
        self.assertFalse(result["editorial_or_publication_approved"])
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("x-q1", str(result))

    def test_other_element_and_attribute_values_are_never_leaked(self):
        inspector = NativeMarkupCensus()
        raw = b'<privateSecret privateKey="PRIVATE_VALUE">PRIVATE_TEXT</privateSecret>'
        native_raw_main_text(raw, markup_census=inspector, reference="Gen.1.1")
        result = inspector.finish()
        self.assertEqual(result["native_raw_element_counts"]["other_unrecognized_xml_tag"], 1)
        self.assertEqual(result["native_raw_attribute_name_counts"]["other_unrecognized_attribute_name"], 1)
        self.assertNotIn("privateSecret", str(result))
        self.assertNotIn("PRIVATE", str(result))

    def test_bad_reader_ref_or_wrong_root_fails_closed(self):
        inspector = NativeMarkupCensus()
        with self.assertRaises(ValueError):
            native_raw_main_text(b'<p>text</p>', markup_census=inspector,
                                 reference="../Gen.1.1")
        with self.assertRaises(ValueError):
            inspector.observe("Gen.1.1", __import__("lxml").etree.fromstring(b"<other/>"))

    def test_four_refs_max_per_structure_category(self):
        inspector = NativeMarkupCensus()
        for verse in range(1,12):
            native_raw_main_text(
                b'<p>PRIVATE_WORD</p>', markup_census=inspector,
                reference=f"Gen.1.{verse}")
        result = inspector.finish()
        self.assertEqual(result["native_numbered_verse_fragments_inspected"], 11)
        self.assertEqual(len(result["first_reference_ids_without_scripture"]["explicit_paragraph_element"]), 4)
        self.assertEqual(result["native_structural_category_element_counts"]["explicit_paragraph_element"],11)


if __name__ == "__main__":
    unittest.main()
