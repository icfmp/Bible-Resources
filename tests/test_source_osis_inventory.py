"""Source-authored OSIS verse inventories: synthetic, edition-independent tests.

Never compare an invented reader list to claim a real stock SWORD scan. That
requires a separate, independently collected reader inventory (issue #28).
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_osis_inventory import (
    _read_source, _write_outputs, source_inventory, SourceInventoryError
)
from stable_sword_refs import inspect_references, parse_keys, parse_registry

NS = 'xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"'
INTRO = '<title>synthetic book introduction</title>'
FIRST = '<verse osisID="Alpha.1.1" sID="s1"/><w lemma="strong:X1">alpha</w><verse eID="s1"/>'
SECOND = '<verse osisID="Alpha.1.2"><note n="a">note</note><p>beta</p></verse>'
BETA = '<verse osisID="Beta.1.1"><l>gamma</l></verse>'


def document(first=FIRST, second=SECOND, beta=BETA):
    return (f'<osis {NS}><osisText osisIDWork="Synthetic">'
            f'<div type="book" osisID="Alpha">{INTRO}<chapter osisID="Alpha.1"/>'
            f'{first}{second}</div><div type="book" osisID="Beta">'
            f'<chapter osisID="Beta.1"/>{beta}</div>'
            '</osisText></osis>').encode("utf-8")


class SourceOsisInventoryTests(unittest.TestCase):
    def test_actual_source_order_and_multiple_verse_forms(self):
        raw = document()
        keys, report = source_inventory(raw)
        self.assertEqual(keys, "Alpha.1.1\nAlpha.1.2\nBeta.1.1\n")
        self.assertEqual(report["status"],
                         "source_osis_verse_keys_inventoried_not_release_approved")
        self.assertEqual(report["source_osis_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["source_keys_sha256"],
                         hashlib.sha256(keys.encode()).hexdigest())
        self.assertEqual(report["source_book_count"], 2)
        self.assertEqual(report["source_chapter_count"], 2)
        self.assertEqual(report["source_verse_count"], 3)
        self.assertEqual(report["books"][0]["whole_book_tag_counts"]["note"], 1)
        self.assertEqual(report["books"][0]["tags_before_first_numbered_verse"]["title"], 1)
        self.assertEqual(report["books"][1]["whole_book_tag_counts"]["l"], 1)
        self.assertFalse(report["actual_stock_sword_reader_keys_verified"])
        self.assertFalse(report["original_osis_schema_validated"])
        self.assertFalse(report["published"])
        self.assertNotIn("synthetic book introduction", json.dumps(report))

    def test_source_keys_fit_existing_sword_index_gate_format(self):
        keys, report = source_inventory(document())
        key_set = parse_keys(keys)
        registry = parse_registry(
            "Test\tAlpha\t1\t2\nTest\tBeta\t1\t1\n",
            "Test")
        # Deliberately supplied SYNTHETIC reader list. This is NOT a
        # claim of independent stock libsword readback.
        result = inspect_references(key_set, parse_keys(keys), registry)
        self.assertEqual(result["status"], "stable_reference_index_verified")
        self.assertEqual(report["source_verse_count"], len(key_set))

    def test_duplicate_verse_id_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "duplicated"):
            source_inventory(document(second='<verse osisID="Alpha.1.1"/>'))

    def test_out_of_order_verses_block(self):
        with self.assertRaisesRegex(SourceInventoryError, "out-of-order"):
            source_inventory(document(
                first='<verse osisID="Alpha.2.1"/>',
                second='<verse osisID="Alpha.1.2"/>'))

    def test_missing_verse_end_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "matching eID"):
            source_inventory(document(first='<verse osisID="Alpha.1.1" sID="s1"/>'))

    def test_wrong_verse_end_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "mismatched"):
            source_inventory(document(first=FIRST.replace('eID="s1"', 'eID="s2"')))

    def test_orphan_closing_milestone_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "orphan"):
            source_inventory(document(first='<verse eID="orphan"/>'))

    def test_source_book_mismatch_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "different OSIS book"):
            source_inventory(document(first='<verse osisID="Beta.1.1"/>'))

    def test_unsupported_alias_or_range_blocks_without_guessing(self):
        for first in ('<verse osisID="Alpha.1.1 Alpha.1.2"/>',
                      '<verse osisID="Alpha.1.1-2"/>',
                      '<verse n="1"/>',
                      '<verse osisID="Alpha.1.0"/>'):
            with self.subTest(first=first), self.assertRaises(SourceInventoryError):
                source_inventory(document(first=first))

    def test_internal_source_gap_reported_not_reconstructed(self):
        keys, report = source_inventory(document(second='<verse osisID="Alpha.1.3"/>'))
        self.assertEqual(keys, 'Alpha.1.1\nAlpha.1.3\nBeta.1.1\n')
        self.assertEqual(report["books"][0][
            "first_internal_numbering_gaps_not_missing_text_claims"], [
                {"chapter": 1, "after": 1, "before": 3}])

    def test_cross_book_duplicate_and_nested_book_block(self):
        for other in ('<div type="book" osisID="Alpha"><verse osisID="Alpha.1.3"/></div>',
                      '<div type="book" osisID="Beta"><verse osisID="Beta.1.2"/></div>'):
            # First fixture duplicates a name; second is a regular second
            # book and must only be rejected when nested.
            if 'osisID="Alpha"' in other:
                raw = (f'<osis {NS}><osisText><div type="book" osisID="Alpha">'
                       f'{FIRST}</div>{other}</osisText></osis>').encode()
            else:
                raw = (f'<osis {NS}><osisText><div type="book" osisID="Alpha">'
                       f'{FIRST}{other}</div></osisText></osis>').encode()
            with self.subTest(other=other), self.assertRaises(SourceInventoryError):
                source_inventory(raw)

    def test_verse_outside_authored_book_blocks(self):
        raw = (f'<osis {NS}><osisText><verse osisID="Alpha.1.1"/>'
               f'<div type="book" osisID="Beta">{BETA}</div>'
               '</osisText></osis>').encode()
        with self.assertRaisesRegex(SourceInventoryError, "outside"):
            source_inventory(raw)

    def test_foreign_or_non_osis_root_blocks(self):
        raw = b'<osis><osisText><div type="book" osisID="Alpha"/></osisText></osis>'
        with self.assertRaisesRegex(SourceInventoryError, "namespace"):
            source_inventory(raw)

    def test_dtd_rejected_not_processed(self):
        raw = ('<!DOCTYPE osis [<!ENTITY danger "hidden">]>'
               + document().decode()).encode()
        with self.assertRaisesRegex(SourceInventoryError, "DTD"):
            source_inventory(raw)

    def test_broken_xml_blocks(self):
        with self.assertRaisesRegex(SourceInventoryError, "well-formed"):
            source_inventory(document().replace(b"</osis>", b"</not-osis>"))

    def test_separate_sources_have_separate_hash_receipts(self):
        a = source_inventory(document())[1]
        b = source_inventory(document(second=SECOND.replace("beta", "delta")))[1]
        self.assertNotEqual(a["source_osis_sha256"], b["source_osis_sha256"])
        self.assertEqual(a["source_keys_sha256"], b["source_keys_sha256"])

    def test_safe_output_creation_and_overwrite_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.xml"
            source.write_bytes(document())
            keys, report = source_inventory(_read_source(source))
            out, receipt = root / "keys.txt", root / "receipt.json"
            _write_outputs(out, receipt, keys, report, source)
            self.assertEqual(out.read_text(), keys)
            self.assertEqual(json.loads(receipt.read_text()), report)
            with self.assertRaisesRegex(SourceInventoryError, "overwrite"):
                _write_outputs(out, receipt, keys, report, source)

    def test_no_partial_output_when_path_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.xml"
            source.write_bytes(document())
            keys, report = source_inventory(source.read_bytes())
            with self.assertRaisesRegex(SourceInventoryError, "parents"):
                _write_outputs(root / "keys.txt", root / "missing/receipt.json",
                               keys, report, source)
            self.assertFalse((root / "keys.txt").exists())

    def test_source_symlink_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, linked = root / "source.xml", root / "linked.xml"
            source.write_bytes(document())
            linked.symlink_to(source)
            with self.assertRaisesRegex(SourceInventoryError, "non-symlink"):
                _read_source(linked)


if __name__ == "__main__":
    unittest.main()
