"""Offline real-reader runner behavior with disposable synthetic mock reader."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pilot_runtime import run_reader


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.archive = root / "lsg.zip"
        with zipfile.ZipFile(self.archive, "w") as z:
            z.writestr("mods.d/fralsg1910eb.conf",
                       "[fraLSG1910eb]\nModDrv=zText\nVersion=1\n")
            z.writestr("modules/texts/ztext/a/test.dat", b"synthetic bytes")
        self.config = json.loads((ROOT / "config/pilot-sources.json").read_text())
        self.fake = root / "diatheke"
        self.fake.write_text("#!/usr/bin/env python3\nprint('synthetic verse')\n")
        self.fake.chmod(0o700)

    def test_reader_stays_in_disposable_root_and_logs_checksums_not_text(self):
        original = self.archive.read_bytes()
        result = run_reader("lsg", self.archive, config=self.config, diatheke=str(self.fake))
        self.assertEqual(result["status"], "reader_probe_passed")
        self.assertEqual(len(result["checked_references"]),
                         len(self.config["pilots"]["lsg"]["sample_references"]))
        self.assertEqual(self.archive.read_bytes(), original)
        self.assertNotIn("synthetic verse", json.dumps(result))
        self.assertTrue(all(x["output_sha256"] for x in result["checked_references"]))

    def test_empty_reader_output_cannot_pass(self):
        self.fake.write_text("#!/usr/bin/env python3\npass\n")
        self.fake.chmod(0o700)
        result = run_reader("lsg", self.archive, config=self.config, diatheke=str(self.fake))
        self.assertEqual(result["status"], "reader_probe_incomplete")
        self.assertFalse(any(x["has_readable_content"] for x in result["checked_references"]))


if __name__ == "__main__":
    unittest.main()
