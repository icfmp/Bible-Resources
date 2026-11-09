"""Strict parsing and payload identity for independent native libSWORD indexes.

Synthetic fixtures never purport to be actual module readbacks. The CI workflow
separately runs the compiled C++ reader on the real published LSG payload.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sword_native_inventory import (
    NativeIndexError, _validate_payload, _write_evidence, parse_native_rows
)

VALID = (
    "M\tFixture\tKJV\t1.9.0\tRawText\n"
    "I\tAlpha.0.0\n"
    "R\tKJV\tAlpha\t1\t3\n"
    "K\tAlpha.1.1\n"
    "K\tAlpha.1.3\n"
    "I\tAlpha.1.0\n"
    "R\tKJV\tBeta\t1\t1\n"
    "K\tBeta.1.1\n"
    "S\t2\t3\t2\t0\n"
)


class NativeIndexParsingTests(unittest.TestCase):
    def test_valid_reader_registry_and_unoccupied_slots_are_distinct(self):
        keys, registry, receipt = parse_native_rows(VALID, "Fixture")
        self.assertEqual(keys, "Alpha.1.1\nAlpha.1.3\nBeta.1.1\n")
        self.assertEqual(registry, "KJV\tAlpha\t1\t3\nKJV\tBeta\t1\t1\n")
        self.assertEqual(receipt["native_registry_chapter_count"], 2)
        self.assertEqual(receipt["native_occupied_numbered_verse_count"], 3)
        self.assertEqual(receipt["native_occupied_verse_zero_intro_count"], 2)
        self.assertFalse(receipt["source_to_reader_index_parity_verified"])
        self.assertFalse(receipt["source_text_notes_markup_fidelity_verified"])
        self.assertFalse(receipt["published"])

    def test_actual_native_bare_book_and_chapter_intro_ids(self):
        native = VALID.replace("I\tAlpha.0.0", "I\tAlpha").replace(
            "I\tAlpha.1.0", "I\tAlpha.1")
        keys, registry, report = parse_native_rows(native, "Fixture")
        self.assertEqual(report["native_occupied_verse_zero_intro_count"], 2)
        self.assertEqual(report["native_occupied_intro_references"],
                         ["Alpha", "Alpha.1"])
        self.assertEqual(len(keys.splitlines()), 3)

    def test_occupied_anonymous_top_intro_is_preserved_as_unresolved(self):
        native = VALID.replace("I\tAlpha.0.0\n", "U\tTOP\t1\nI\tAlpha.0.0\n")
        native = native.replace("S\t2\t3\t2\t0", "S\t2\t3\t2\t1")
        keys, registry, report = parse_native_rows(native, "Fixture")
        self.assertEqual(report["native_nonaddressable_populated_top_count"], 1)
        self.assertFalse(report["native_anonymous_top_content_parity_verified"])
        self.assertEqual(len(keys.splitlines()), 3)

    def test_duplicate_anonymous_top_intro_fails(self):
        native = VALID.replace("I\tAlpha.0.0\n", "U\tTOP\t1\nU\tTOP\t1\nI\tAlpha.0.0\n")
        native = native.replace("S\t2\t3\t2\t0", "S\t2\t3\t2\t2")
        with self.assertRaisesRegex(NativeIndexError, "Duplicate"):
            parse_native_rows(native, "Fixture")

    def test_wrong_module_identity_blocked(self):
        with self.assertRaisesRegex(NativeIndexError, "header"):
            parse_native_rows(VALID, "Different")

    def test_unsupported_runtime_and_driver_blocked(self):
        for changed in (VALID.replace("1.9.0", "HEAD"),
                        VALID.replace("RawText", "RawLD"),
                        VALID.replace("\tKJV\t1.9.0", "\tFake.v11n\t1.9.0")):
            with self.subTest(changed=changed[:90]), self.assertRaises(NativeIndexError):
                parse_native_rows(changed, "Fixture")

    def test_corrupt_counter_or_missing_terminal_blocked(self):
        for changed in (VALID.replace("S\t2\t3\t2\t0", "S\t2\t4\t2\t0"),
                        VALID.replace("S\t2\t3\t2\t0\n", ""),
                        VALID.replace("S\t2\t3\t2\t0", "S\twrong\t3\t2\t0")):
            with self.subTest(changed=changed[-70:]), self.assertRaises(NativeIndexError):
                parse_native_rows(changed, "Fixture")

    def test_missing_or_reordered_registry_blocks(self):
        for changed in (VALID.replace("R\tKJV\tBeta\t1\t1\n", ""),
                        VALID.replace("R\tKJV\tBeta\t1\t1", "R\tNRSV\tBeta\t1\t1"),
                        VALID.replace("R\tKJV\tAlpha\t1\t3", "R\tKJV\tAlpha\t1\t1")):
            with self.subTest(changed=changed[:80]), self.assertRaises((NativeIndexError, ValueError)):
                parse_native_rows(changed, "Fixture")

    def test_reordered_or_duplicate_populated_keys_blocked(self):
        for changed in (VALID.replace("K\tAlpha.1.3\n", "K\tAlpha.1.1\n"),
                        VALID.replace("K\tAlpha.1.3\n", "K\tAlpha.1.0\n"),
                        VALID.replace("K\tAlpha.1.3\n", "K\tBeta.1.1\n")):
            with self.subTest(changed=changed[:95]), self.assertRaises(NativeIndexError):
                parse_native_rows(changed, "Fixture")

    def test_extra_and_duplicated_reader_intro_blocked(self):
        for changed in (VALID.replace("I\tAlpha.0.0\n", "I\tAlpha.0.1\n"),
                        VALID.replace("I\tAlpha.1.0\n", "I\tAlpha.0.0\n")):
            with self.subTest(changed=changed[:80]), self.assertRaises(NativeIndexError):
                parse_native_rows(changed, "Fixture")

    def test_unknown_bible_source_text_not_echoed_in_receipt(self):
        raw = VALID + "secret biblical content"
        with self.assertRaises(NativeIndexError):
            parse_native_rows(raw, "Fixture")


class NativeModuleIdentityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.module = self.home / "example"
        directory = self.module / "payload/mods.d"
        directory.mkdir(parents=True)
        self.config = directory / "fixture.conf"
        self.config.write_text(
            "[Fixture]\nDataPath=./modules/texts/rawtext/fixture/\n"
            "ModDrv=RawText\nVersification=KJV\n", encoding="utf-8")

    def test_unmodified_module_conf_identity(self):
        root, driver, system = _validate_payload(self.module, "Fixture")
        self.assertEqual(root, self.module / "payload")
        self.assertEqual(driver, "RawText")
        self.assertEqual(system, "KJV")

    def test_wrong_module_id_or_driver_blocks(self):
        with self.assertRaises(NativeIndexError):
            _validate_payload(self.module, "Different")
        self.config.write_text(self.config.read_text().replace(
            "ModDrv=RawText", "ModDrv=zCom"), encoding="utf-8")
        with self.assertRaises(NativeIndexError):
            _validate_payload(self.module, "Fixture")

    def test_extra_symlinked_module_conf_fails_closed(self):
        extra = self.module / "payload/mods.d/another.conf"
        extra.symlink_to(self.config)
        with self.assertRaises(NativeIndexError):
            _validate_payload(self.module, "Fixture")

    def test_evidence_refuses_to_mutate_module_directory(self):
        bad = self.module / "payload/native-index-report.json"
        with self.assertRaisesRegex(NativeIndexError, "source-module-overwriting"):
            _write_evidence([(bad, b"{}")], self.module)
        self.assertFalse(bad.exists())

    def test_repeated_versification_declaration_blocks(self):
        self.config.write_text(self.config.read_text() + "Versification=Segond\n",
                               encoding="utf-8")
        with self.assertRaisesRegex(NativeIndexError, "Repeated"):
            _validate_payload(self.module, "Fixture")

    def test_reader_proof_outputs_never_overwrite_existing(self):
        a = self.home / "keys.txt"
        b = self.home / "registry.tsv"
        c = self.home / "receipt.json"
        _write_evidence([(a, b"Alpha.1.1\n"), (b, b"KJV\tAlpha\t1\t1\n"),
                         (c, b"{}\n")], self.module)
        self.assertEqual(a.read_bytes(), b"Alpha.1.1\n")
        with self.assertRaisesRegex(NativeIndexError, "overwrite"):
            _write_evidence([(a, b"overwrite")], self.module)
        self.assertEqual(a.read_bytes(), b"Alpha.1.1\n")

    def test_bad_output_parent_never_creates_partial_files(self):
        a = self.home / "keys.txt"
        b = self.home / "missing/receipt.json"
        with self.assertRaisesRegex(NativeIndexError, "parent"):
            _write_evidence([(a, b"Alpha.1.1"), (b, b"{}")], self.module)
        self.assertFalse(a.exists())


if __name__ == "__main__":
    unittest.main()
