"""Approved Bibles must declare a recognized, evidence-bound index strategy."""
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class IndexAuditRequirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = Draft202012Validator(
            json.loads((ROOT / "schemas/module.schema.json").read_text()))
        cls.metadata = json.loads(
            (ROOT / "modules/lsg-1910/metadata.json").read_text())

    def errors(self, metadata):
        return list(self.validator.iter_errors(metadata))

    def test_every_approved_bible_has_valid_index_proof_declaration(self):
        """New releases cannot escape index validation by not being LSG."""
        approved = []
        for path in sorted((ROOT / "modules").glob("*/metadata.json")):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if (metadata.get("category") == "bible" and
                    metadata.get("quality", {}).get("status") == "approved"):
                approved.append(path)
                with self.subTest(module=path.parent.name):
                    self.assertEqual(self.errors(metadata), [])
                    self.assertIn("index_audit", metadata)
                    self.assertIn("mode", metadata["index_audit"])
        self.assertGreater(len(approved), 0)

    def test_approved_bible_without_index_proof_rejected(self):
        metadata = dict(self.metadata)
        metadata.pop("index_audit")
        self.assertTrue(self.errors(metadata))

    def test_legacy_proof_cannot_omit_manifest(self):
        metadata = dict(self.metadata, index_audit={"mode": "published_source_audit"})
        self.assertTrue(self.errors(metadata))

    def test_native_proof_cannot_fall_back_to_old_manifest(self):
        metadata = dict(self.metadata, index_audit={
            "mode": "stock_reader_keys",
            "manifest": "config/old.json",
        })
        self.assertTrue(self.errors(metadata))

    def test_unknown_proof_mode_rejected(self):
        metadata = dict(self.metadata, index_audit={"mode": "trust_me"})
        self.assertTrue(self.errors(metadata))


if __name__ == "__main__":
    unittest.main()
