#!/usr/bin/env python3
"""Check BSI workspace partition and future crosswalk contract without network."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkspaceTests(unittest.TestCase):
    def test_partition_and_immutable_source_lock(self):
        lock = json.loads((ROOT / "data" / "source.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["source_records_expected"], 6644)
        self.assertEqual(len(lock["source_snapshot_sha256"]), 64)
        self.assertEqual(len(lock["source_commit"]), 40)
        self.assertTrue((ROOT / "sources" / "checkout-acai.sh").is_file())
        self.assertIn("/checkouts/", (ROOT / "sources" / ".gitignore").read_text())
        for sub in ("work", "links/dictionaries", "links/encyclopedias"):
            self.assertTrue((ROOT / sub / "README.md").is_file(), sub)
        self.assertTrue((ROOT / "scripts" / "compile_index.py").is_file())
        self.assertTrue((ROOT / "data" / "editorial-decisions.json").is_file())

    def test_crosswalk_schema_is_narrow_and_review_based(self):
        schema = json.loads((ROOT / "links" / "schema.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(schema["additionalProperties"])
        link = schema["properties"]["links"]["items"]
        self.assertFalse(link["additionalProperties"])
        self.assertEqual(link["properties"]["review_status"]["const"], "reviewed")
        self.assertIn("evidence", link["required"])
        self.assertIn("entry_id", link["required"])
        self.assertNotIn("description", link["properties"])
        self.assertNotIn("article", link["properties"])

if __name__ == "__main__":
    unittest.main()
