"""Synthetic source-native biblical-link provenance and fail-closed tests."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_modern_reference_gate import (SourceReferenceGate,
    WholeCanonOriginalLinkIdentityReceipt, canonical_only_for_comparison)


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

    def test_compound_original_first_K_owns_book_intro_and_outline_not_empty_I(self):
        raw=(b'<div><title>Chapter Outline</title>'
             b'Genesis was written under inspiration.'
             b'<table><row><cell>Creation</cell><cell>1-2</cell></row></table>'
             b'The first verse gives an account of Creation.'
             b'<reference osisRef="Bible:1John.5.20">1Jo</reference></div>')
        orig_intro=b"<div/>"
        meta=source()
        meta["sections"][0]["source_sha256"]=hashlib.sha256(raw).hexdigest()
        meta["sections"][0]["markup_census"]["tag_counts"]["reference"]=1
        meta["introductions"]=[{
            "native_key":"Gen",
            "source_sha256":hashlib.sha256(orig_intro).hexdigest()
        }]
        meta["intro_provenance_expectations"]={
            "original_first_numbered_key":"Gen.1.3",
            "expected_original_book_intro_start":"Genesis was written under inspiration",
            "expected_original_exposition_start":"The first verse gives an account",
            "expected_original_chapter_outline_table_count":1,
            "expected_original_chapter_outline_row_count":1,
            "expected_original_chapter_outline_title_count":1
        }
        g=SourceReferenceGate(source_map=meta,expected_refs=expected(),
                              candidate="This has (1 John 5:20).")
        g.observe("I","Gen",orig_intro)
        g.observe("K","Gen.1.3",raw)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertTrue(proof["original_book_intro_and_outline_owned_by_first_numbered_K_attested"])
        self.assertEqual(proof["per_intro_unit"]["Gen"]["source_visible_word_count"],0)
        self.assertFalse(proof["original_prose_or_reference_labels_exported"])

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


def whole_source_receipt(*, reference_count=1):
    return {
        "status": "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
        "original_compiled_corpus_sha256": FULL_HASH,
        "source_prose_or_original_markup_exported": False,
        "semantic_translation_independently_approved": False,
        "chapters": {
            "Gen.1": {
                "original_units": [{
                    "first_key": "Gen.1.3",
                    "keys": ["Gen.1.3", "Gen.1.4"],
                    "source_unit_sha256": SOURCE_HASH,
                    "markup": {
                        "strict_xml_fragment": True,
                        "tag_counts": {"reference": reference_count}
                    }
                }]
            }
        }
    }


class WholeNativeReferenceIdentityTests(unittest.TestCase):
    def test_exact_link_and_label_hashes_are_private_and_ordered(self):
        gate = WholeCanonOriginalLinkIdentityReceipt(whole_source_receipt())
        gate.observe("I", "Gen.1", b"<div>unrelated introduction</div>")
        gate.observe("K", "Gen.1.3", ORIGINAL)
        gate.observe("K", "Gen.1.4", ORIGINAL)
        report = gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        self.assertEqual(report["original_numbered_K_keys_verified"], 2)
        self.assertEqual(report["original_unique_K_bodies_verified"], 1)
        self.assertEqual(report["original_reference_elements_verified"], 1)
        self.assertEqual(report["original_link_bearing_K_bodies"], 1)
        group = report["source_link_groups"][0]
        self.assertEqual(group["source_raw_sha256"], SOURCE_HASH)
        self.assertEqual(group["original_osisRef_sha256_in_document_order"],
                         [hashlib.sha256(b"Bible:1John.5.20").hexdigest()])
        self.assertEqual(group["original_visible_link_label_sha256_in_document_order"],
                         [hashlib.sha256(b"1Jo 5:20").hexdigest()])
        self.assertNotIn("Bible:1John.5.20", str(report))
        self.assertNotIn("1Jo 5:20", str(report))
        self.assertFalse(report["modern_osisRef_targets_or_order_verified"])
        self.assertFalse(report["modern_module_built_or_published"])

    def test_complex_original_link_target_is_hashed_not_normalized(self):
        raw = (b'<div><reference osisRef="Bible:Gen.1.1-Gen.1.3">'
               b'original linked label</reference></div>')
        receipt = whole_source_receipt()
        receipt["chapters"]["Gen.1"]["original_units"][0][
            "source_unit_sha256"] = hashlib.sha256(raw).hexdigest()
        gate = WholeCanonOriginalLinkIdentityReceipt(receipt)
        gate.observe("K", "Gen.1.3", raw)
        gate.observe("K", "Gen.1.4", raw)
        report = gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        self.assertEqual(report["source_link_groups"][0][
            "original_osisRef_sha256_in_document_order"], [
                hashlib.sha256(b"Bible:Gen.1.1-Gen.1.3").hexdigest()])
        self.assertFalse(report["original_source_prose_or_XML_exported"])

    def test_missing_or_corrupt_original_aliases_fail_closed(self):
        gate = WholeCanonOriginalLinkIdentityReceipt(whole_source_receipt())
        gate.observe("K", "Gen.1.3", ORIGINAL)
        with self.assertRaisesRegex(ValueError, "not completely read"):
            gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        with self.assertRaisesRegex(ValueError, "source SHA differ"):
            gate.observe("K", "Gen.1.4", ORIGINAL.replace(b"5.20", b"5.21"))
        gate.observe("K", "Gen.1.4", ORIGINAL)
        with self.assertRaisesRegex(ValueError, "SHA does not match"):
            gate.report({"all_native_raw_entries_ordered_sha256": "b" * 64})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            gate.observe("K", "Gen.1.4", ORIGINAL)

    def test_source_reference_count_drift_and_missing_osisref_are_rejected(self):
        wrong_census = WholeCanonOriginalLinkIdentityReceipt(
            whole_source_receipt(reference_count=2))
        with self.assertRaisesRegex(ValueError, "reference count"):
            wrong_census.observe("K", "Gen.1.3", ORIGINAL)

        raw = b"<div><reference>original label without destination</reference></div>"
        source = whole_source_receipt()
        source["chapters"]["Gen.1"]["original_units"][0][
            "source_unit_sha256"] = hashlib.sha256(raw).hexdigest()
        gate = WholeCanonOriginalLinkIdentityReceipt(source)
        with self.assertRaisesRegex(ValueError, "missing/unsafe"):
            gate.observe("K", "Gen.1.3", raw)

    def test_duplicate_key_in_source_receipt_is_rejected(self):
        receipt = whole_source_receipt()
        receipt["chapters"]["Gen.1"]["original_units"][0]["keys"].append("Gen.1.4")
        with self.assertRaisesRegex(ValueError, "Repeated"):
            WholeCanonOriginalLinkIdentityReceipt(receipt)


if __name__=="__main__":
    unittest.main()
