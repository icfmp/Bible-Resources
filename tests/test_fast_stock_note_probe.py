"""Fast original-note vs exact native SWORD sample, no genuine binaries needed."""
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from fast_stock_note_probe import probe_stock_note_callers, _sample_references


def usfx(caller="a"):
    return (f'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
            f'PRIVATE TEXT<f caller="{caller}"><ft>note body</ft></f>'
            f'</p></book></usfx>').encode()


class QuickNotesTests(unittest.TestCase):
    def setUp(self):
        self.root=TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        base=Path(self.root.name)
        self.binary=base/"exact-reader"
        self.binary.write_bytes(b"fixture")

    def run_probe(self, native=b'<note type="x-footnote">note body</note>',
                  caller="a", reader_code=0):
        def fake_install(_zip, path):
            (path/"payload").mkdir(parents=True)
            return {"module_id":"Fixture"}

        with (patch("fast_stock_note_probe.read_source_xml",
                    return_value=(usfx(caller),{})),
              patch("fast_stock_note_probe.read_crosswalk",
                    return_value=[("GEN","Gen")]),
              patch("fast_stock_note_probe._safe_single_module",
                    side_effect=fake_install),
              patch("fast_stock_note_probe.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["exact","Fixture","Gen.1.1"],reader_code,native)) as reader):
            result=probe_stock_note_callers(
                Path("/fake/source.zip"),Path("/fake/stock.zip"),
                Path("/fake/crosswalk.json"),self.binary,"Fixture")
        return result,reader

    def test_detects_missing_literal_caller_with_one_exact_native_lookup(self):
        result,reader=self.run_probe()
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["reason_code"],"literal_note_caller_missing")
        self.assertEqual(result["sampled_exact_source_reference"],"Gen.1.1")
        self.assertEqual(result["independent_exact_native_verse_probes"],1)
        reader.assert_called_once()
        self.assertNotIn("PRIVATE TEXT",str(result))
        self.assertNotIn("note body",str(result))

    def test_changed_literal_caller_is_blocker(self):
        result,_=self.run_probe(b'<note n="z">note body</note>')
        self.assertEqual(result["reason_code"],"literal_note_caller_changed")

    def test_same_label_and_note_only_requires_full_corpus(self):
        result,_=self.run_probe(b'<note n="a">note body</note>')
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"],"sample_only_no_proven_stock_loss")
        self.assertFalse(result["stock_reuse_or_publication_approved"])

    def test_missing_note_requires_full_audit_not_invented_loss(self):
        result,_=self.run_probe(b'<div/>')
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"],"sample_note_count_requires_full_audit")

    def test_note_body_encoding_difference_requires_full_audit(self):
        result,_=self.run_probe(b'<note n="a">different body</note>')
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"],"sample_note_body_requires_full_audit")

    def test_automatic_callers_are_not_mistaken_for_loss(self):
        result,reader=self.run_probe(caller="+")
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual(result["reason_code"],"no_literal_caller_note_sample")
        reader.assert_not_called()

    def test_nonindexable_raw_entry_and_malformed_xml_are_uncertainty(self):
        for native,code in ((b"private",6),(b"<!DOCTYPE bad>",0)):
            with self.subTest(code=code):
                result,_=self.run_probe(native,reader_code=code)
                self.assertEqual(result["status"],"REVIEW_REQUIRED")
                self.assertFalse(result["fast_stock_reuse_disqualified"])

    def test_sample_prioritizes_distinct_books(self):
        attrs={
            "Gen.1.1":[{"caller":"a"}],
            "Gen.1.2":[{"caller":"b"}],
            "Exod.1.1":[{"caller":"c"}],
        }
        self.assertEqual(_sample_references(attrs,2),["Gen.1.1","Exod.1.1"])
        self.assertEqual(_sample_references(attrs,3),
                         ["Gen.1.1","Exod.1.1","Gen.1.2"])

    def test_unsafe_or_unavailable_binary_cannot_mark_passed(self):
        result=probe_stock_note_callers(
            Path("source.zip"), Path("stock.zip"),
            Path("crosswalk"), Path("/nonexistent/exact-reader"), "Fixture")
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertFalse(result["fast_stock_reuse_disqualified"])

if __name__=="__main__":
    unittest.main()
