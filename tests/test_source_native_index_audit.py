"""Independent OSIS -> SWORD combined index command; synthetic tests only.

The native producer is mocked here. Its real stock-libsword path is already
exercised independently on released LSG RawText and original WEBP zText in CI.
"""
from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_native_index_audit import (
    audit_source_native_index, SourceNativeIndexError, main,
)
from stable_sword_refs import module_payload_digest

NS = 'xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"'


def osis(second="Beta.1.1", wording="beta"):
    return (f'<osis {NS}><osisText><div type="book" osisID="Alpha">'
            '<chapter osisID="Alpha.1"/><verse osisID="Alpha.1.1">alpha</verse>'
            '</div><div type="book" osisID="Beta"><chapter osisID="Beta.1"/>'
            f'<verse osisID="{second}">{wording}</verse>'
            '</div></osisText></osis>').encode("utf-8")


class IndexCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "original.osis.xml"
        self.source.write_bytes(osis())
        self.module = self.root / "module"
        (self.module / "payload").mkdir(parents=True)
        (self.module / "payload" / "native.bin").write_bytes(b"synthetic module bytes")
        self.inspector = self.root / "stock-index"
        self.inspector.write_bytes(b"synthetic inspector; never executed")
        self.keys = "Alpha.1.1\nBeta.1.1\n"
        self.registry = "Synthetic\tAlpha\t1\t1\nSynthetic\tBeta\t1\t1\n"

    def reader(self, keys=None, registry=None, system="Synthetic"):
        keys = self.keys if keys is None else keys
        registry = self.registry if registry is None else registry
        return keys, registry, {
            "module_payload_sha256": module_payload_digest(self.module),
            "native_reader_keys_sha256": sha256(keys.encode()).hexdigest(),
            "native_registry_sha256": sha256(registry.encode()).hexdigest(),
            "native_occupied_numbered_verse_count": len(keys.splitlines()),
            "reader_version": "1.9.0",
            "module_driver": "zText",
            "native_versification": system,
            "native_inspector_sha256": sha256(self.inspector.read_bytes()).hexdigest(),
            "native_occupied_intro_references": [],
            "native_nonaddressable_populated_top_count": 0,
        }

    def run_audit(self, reader=None):
        with patch("source_native_index_audit.collect_native_inventory",
                   return_value=reader or self.reader()):
            return audit_source_native_index(
                self.source, self.module, "Synthetic", self.inspector)

    def test_two_independent_inventories_match_index_only(self):
        r = self.run_audit()
        self.assertEqual(r["status"], "source_osis_native_verse_keys_exact_index_only")
        self.assertTrue(r["comparison"]["exact_reference_key_parity"])
        self.assertEqual(r["module_payload_sha256"], module_payload_digest(self.module))
        self.assertFalse(r["source_to_compiled_text_punctuation_notes_strong_layout_verified"])
        self.assertFalse(r["same_edition_revision_verified"])
        self.assertFalse(r["published"])
        self.assertNotIn("alpha", json.dumps(r))
        self.assertNotIn("beta", json.dumps(r))

    def test_different_source_words_do_not_pass_text_fidelity(self):
        before = self.run_audit()
        self.source.write_bytes(osis(wording="changed WORD and punctuation!"))
        after = self.run_audit()
        self.assertTrue(after["comparison"]["exact_reference_key_parity"])
        self.assertNotEqual(before["source_osis_sha256"], after["source_osis_sha256"])
        self.assertFalse(after["source_to_compiled_text_punctuation_notes_strong_layout_verified"])

    def test_missing_compiled_verse_blocks_even_if_registry_has_it(self):
        r = self.run_audit(self.reader(keys="Alpha.1.1\n"))
        self.assertEqual(r["status"], "blocked_source_osis_native_verse_key_difference")
        self.assertEqual(r["comparison"]["source_references_unreachable_count"], 1)

    def test_incorrect_declared_native_versification_blocks(self):
        r = self.run_audit(self.reader(
            registry="Synthetic\tAlpha\t1\t1\nSynthetic\tBeta\t1\t0\n"))
        self.assertEqual(r["status"], "blocked_source_osis_native_verse_key_difference")

    def test_report_integrity_blocks_wrong_receipts(self):
        rows = [
            ("native_reader_keys_sha256", "0" * 64),
            ("native_registry_sha256", "0" * 64),
            ("module_payload_sha256", "0" * 64),
            ("native_occupied_numbered_verse_count", 999),
            ("reader_version", ""),
            ("native_versification", None),
        ]
        for field, bad in rows:
            with self.subTest(field=field):
                result = self.reader()
                result[2][field] = bad
                with self.assertRaises(SourceNativeIndexError):
                    self.run_audit(result)

    def test_original_source_symlink_rejected(self):
        self.source.unlink()
        self.source.symlink_to(self.inspector)
        with self.assertRaises(ValueError):
            self.run_audit()

    def test_changed_source_during_native_scan_rejected(self):
        def tamper(*_args):
            self.source.write_bytes(osis(wording="tampered"))
            return self.reader()
        with patch("source_native_index_audit.collect_native_inventory",
                   side_effect=tamper), self.assertRaisesRegex(
                       SourceNativeIndexError, "changed during"):
            audit_source_native_index(self.source, self.module, "Synthetic",
                                      self.inspector)

    def test_cli_writes_once_and_cannot_write_inside_module(self):
        output = self.root / "receipt.json"
        import source_native_index_audit as command
        argv = ["audit", "--source-osis", str(self.source),
                "--module-directory", str(self.module),
                "--module-id", "Synthetic",
                "--native-index-binary", str(self.inspector),
                "--report", str(output)]
        with patch.object(sys, "argv", argv), patch.object(
                command, "collect_native_inventory", return_value=self.reader()):
            self.assertEqual(main(), 0)
            self.assertFalse(json.loads(output.read_text())["published"])
            with self.assertRaises(SystemExit):
                main()
        with patch.object(sys, "argv", argv[:-1] + [
                str(self.module / "payload" / "receipt.json")]), patch.object(
                command, "collect_native_inventory", return_value=self.reader()):
            with self.assertRaises(SystemExit):
                main()


if __name__ == "__main__":
    unittest.main()
