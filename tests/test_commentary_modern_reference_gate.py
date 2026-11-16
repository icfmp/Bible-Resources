"""Synthetic source-native biblical-link provenance and fail-closed tests."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_modern_reference_gate import SourceReferenceGate,canonical_only_for_comparison


ORIGINAL=(b'<div><reference osisRef="Bible:1John.5.20">1Jo 5:20</reference>'
          b' and <hi>original exposition</hi></div>')
SOURCE_HASH=hashlib.sha256(ORIGINAL).hexdigest()
FULL_HASH="a"*64


def source():
    return {
        "scope":"Gen.1",
        "verified_entire_native_corpus_sha256":FULL_HASH,
        "sections":[{
            "first_key":"Gen.1.3",
            "source_sha256":SOURCE_HASH,
            "markup_census":{"tag_counts":{"reference":1}}}
        ]
    }


def expected():
    return {"Gen.1.3":[{"canonical_target":"1John.5.20",
                          "modern_text_marker":"(1 John 5:20)"}]}


class OriginalReferenceGateTests(unittest.TestCase):
    def test_original_attributes_and_modern_markers_are_both_checked(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="The Son gives understanding (1 John 5:20).")
        g.observe("I","Gen.1",b"<div>an intro not a source section</div>")
        g.observe("K","Gen.1.3",ORIGINAL)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertEqual(proof["original_reference_links_checked"],1)
        self.assertEqual(proof["source_unique_units_checked"],1)
        self.assertFalse(proof["new_modern_osis_reference_targets_embedded"])
        self.assertFalse(proof["original_osisRef_literal_values_exported"])
        self.assertNotIn("1John.5.20",str(proof))

    def test_original_book_and_chapter_introductions_are_separately_attested(self):
        intro=b"<div><title>Chapter 1</title>Source introduction prose.</div>"
        metadata=source()
        metadata["introductions"]=[{
            "native_key":"Gen.1",
            "source_sha256":hashlib.sha256(intro).hexdigest()
        }]
        g=SourceReferenceGate(source_map=metadata,expected_refs=expected(),
                              candidate="(1 John 5:20)")
        g.observe("I","Gen.1",intro)
        g.observe("K","Gen.1.3",ORIGINAL)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertEqual(proof["original_intro_units_found"],1)
        self.assertEqual(proof["per_intro_unit"]["Gen.1"]["source_visible_word_count"],5)
        self.assertTrue(proof["per_intro_unit"]["Gen.1"]["has_visible_text"])
        self.assertNotIn("Source introduction prose",str(proof))

    def test_missing_original_introduction_blocks_complete_proof(self):
        intro=b"<div>Source introduction</div>"
        metadata=source()
        metadata["introductions"]=[{
            "native_key":"Gen.1",
            "source_sha256":hashlib.sha256(intro).hexdigest()
        }]
        g=SourceReferenceGate(source_map=metadata,expected_refs=expected(),
                              candidate="(1 John 5:20)")
        g.observe("K","Gen.1.3",ORIGINAL)
        with self.assertRaisesRegex(ValueError,"introduction"):
            g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})

    def test_no_silent_change_of_source_link_destination(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="(1 John 5:20)")
        with self.assertRaises(ValueError):
            g.observe("K","Gen.1.3",ORIGINAL.replace(b"5.20",b"5.21"))

    def test_changed_whole_source_blocked(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="(1 John 5:20)")
        g.observe("K","Gen.1.3",ORIGINAL)
        with self.assertRaisesRegex(ValueError,"Whole native source changed"):
            g.report({"all_native_raw_entries_ordered_sha256":"b"*64})

    def test_missing_modern_text_reference_blocked(self):
        with self.assertRaisesRegex(ValueError,"not retained"):
            SourceReferenceGate(source_map=source(),expected_refs=expected(),
                                candidate="The Son grants understanding.")

    def test_every_native_section_requires_explicit_expectation(self):
        with self.assertRaisesRegex(ValueError,"Every source section"):
            SourceReferenceGate(source_map=source(),expected_refs={},
                                candidate="(1 John 5:20)")

    def test_ambiguous_source_links_fail(self):
        for val in ("Bible:Gen.1", "x,y", "unknown", "", "Bible:Ps.0.0"):
            with self.subTest(value=val):
                with self.assertRaises(ValueError):
                    canonical_only_for_comparison(val)


if __name__=="__main__":
    unittest.main()
