"""Synthetic stable-SWORD release gate checks; no Bible text or private source."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stable_sword_refs import (inspect_references, parse_keys, parse_registry,
                                module_payload_digest, proof_errors)


class StableSwordReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.module = Path(self.temp.name) / "module"
        data = self.module / "payload" / "mods.d"
        data.mkdir(parents=True)
        (data / "test.conf").write_text("[Test]\nVersification=Segond\n", encoding="utf-8")
        source = self.module / "SOURCE_VALIDATION.json"
        source.write_text(json.dumps({"source_sha256": "a" * 64}))
        self.reg = parse_registry("Segond\tMark\t1\t2\nSegond\tJob\t1\t3\n"
                                  "NRSV\tMark\t1\t3\n", "Segond")

    def write_proof(self, **updates):
        payload = module_payload_digest(self.module)
        record = inspect_references(parse_keys("Mark.1.1\nMark.1.2\n"),
                                    parse_keys("Mark.1.1\nMark.1.2\n"), self.reg)
        record.update({
            "versification": "Segond",
            "reader_engine": "libsword",
            "reader_version": "1.9.0",
            "engine_release": "stable",
            "registry_source": "installed_sword_versification_mgr",
            "source_osis_sha256": "a" * 64,
            "module_payload_sha256": payload,
            "reviewed_by": "Human reviewer",
        })
        record.update(updates)
        (self.module / "SWORD_COMPATIBILITY.json").write_text(json.dumps(record))
        return record

    def test_reject_real_outside_source_slot_in_synthetic_grid(self):
        source = parse_keys("Mark.1.1\nMark.1.2\nMark.1.3")
        reader = parse_keys("Mark.1.1\nMark.1.2")
        result = inspect_references(source, reader, self.reg)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["outside_registered_versification_count"], 1)
        self.assertEqual(result["source_references_unreachable_count"], 1)

    def test_unoccupied_registry_slot_is_not_scripture_to_invent(self):
        result = inspect_references(parse_keys("Job.1.1\nJob.1.2"),
                                    parse_keys("Job.1.1\nJob.1.2"), self.reg)
        self.assertEqual(result["status"], "stable_reference_index_verified")
        self.assertEqual(result["unoccupied_registered_slots_count"], 3)
        self.assertFalse(result["text_notes_markup_and_visuals_verified"])

    def test_compilation_does_not_hide_wrong_resolved_key(self):
        result = inspect_references(parse_keys("Mark.1.1\nMark.1.2"),
                                    parse_keys("Mark.1.1\nMark.1.3"), self.reg)
        self.assertEqual(result["source_references_unreachable_count"], 1)
        self.assertEqual(result["unexpected_populated_reader_references_count"], 1)

    def test_malformed_duplicates_and_unknown_registry_block(self):
        for raw in ("", "Mark.1.1\nMark.1.1", "Mark.0.1", "Mark.1.0",
                    "Mark.1.1 trailing"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_keys(raw)
        for raw in ("", "Custom\tMark\t1\t2", "Segond\tMark\t1\t2\nSegond\tMark\t1\t3"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_registry(raw, "Segond")

    def test_valid_metadata_is_not_full_editorial_fidelity(self):
        self.write_proof()
        self.assertEqual(proof_errors(self.module, "Segond", "a" * 64), [])

    def test_dev_runtime_and_unvalidated_index_block_release(self):
        for change in ({"engine_release": "development"},
                       {"reader_version": "HEAD"},
                       {"status": "blocked"},
                       {"source_references_unreachable_count": 1},
                       {"reviewed_by": "PENDING"},
                       {"versification": "Custom"}):
            with self.subTest(change=change):
                self.write_proof(**change)
                self.assertTrue(proof_errors(self.module, "Segond", "a" * 64))

    def test_source_and_payload_change_invalidate_proof(self):
        self.write_proof()
        self.assertTrue(proof_errors(self.module, "Segond", "b" * 64))
        (self.module / "payload/mods.d/test.conf").write_text("[Test]\nVersification=Different\n")
        self.assertTrue(any("SWORD_PAYLOAD_PROOF_STALE" in x
                            for x in proof_errors(self.module, "Segond", "a" * 64)))

    def test_missing_and_symlinked_proofs_fail(self):
        self.assertTrue(any("SWORD_COMPATIBILITY_MISSING" in x
                            for x in proof_errors(self.module, "Segond", "a" * 64)))
        self.write_proof()
        (self.module / "SWORD_COMPATIBILITY.json").unlink()
        (self.module / "SWORD_COMPATIBILITY.json").symlink_to("SOURCE_VALIDATION.json")
        self.assertTrue(proof_errors(self.module, "Segond", "a" * 64))


if __name__ == "__main__":
    unittest.main()
