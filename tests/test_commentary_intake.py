"""Offline tests for source-neutral commentary intake; no network or text release."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_intake import load_manifest, inspect_resource
from pilot_preflight import PilotError


class CommentaryIntakeTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.manifests = self.root / "config"
        self.manifests.mkdir()
        self.manifest = {
            "schema_version": 1, "resource_id": "example-commentary",
            "category": "commentary", "module_id": "ExampleCom",
            "title": "Example commentary", "language": "en", "version": "2.0",
            "provider": "crosswire",
            "source_page_url": "https://crosswire.org/sword/modules/ModInfo.jsp?modName=ExampleCom",
            "sword_zip_url": "https://crosswire.org/ftpmirror/pub/sword/packages/rawzip/ExampleCom.zip",
            "authorial_witness_url": "https://www.ccel.org/example",
            "archive_sha256": None, "sample_references": ["Gen 1:1", "Ps 23:1"],
            "rights": {"status": "research_only", "owner_approved": False,
                       "evidence_url": "https://crosswire.org/example"}
        }
        self.write_manifest(self.manifest)

    def write_manifest(self, value):
        (self.manifests / "example-commentary.json").write_text(
            json.dumps(value), encoding="utf-8")

    def test_stage_one_is_metadata_only_and_never_mistaken_for_approval(self):
        with patch("commentary_intake.fetch", side_effect=AssertionError("unexpected download")):
            r = inspect_resource("example-commentary", "1", directory=self.manifests)
        self.assertEqual(r["status"], "metadata_review_required")
        self.assertFalse(r["download_performed"])
        self.assertFalse(r["copyright_and_redistribution_approved"])
        self.assertFalse(r["full_original_to_module_parity"])
        self.assertFalse(r["published"])

    def test_stage_two_requires_a_pin_before_network(self):
        with patch("commentary_intake.fetch", side_effect=AssertionError("unexpected download")):
            with self.assertRaisesRegex(PilotError, "pinned"):
                inspect_resource("example-commentary", "2", directory=self.manifests)

    def test_rejects_unreviewed_license_url_and_path_traversal(self):
        for update in (
            {"rights": {"status": "verified", "owner_approved": True,
                        "evidence_url": "https://crosswire.org/example"}},
            {"sword_zip_url": "https://crosswire.org.attacker.invalid/ExampleCom.zip"},
            {"sword_zip_url": "http://crosswire.org/ExampleCom.zip"},
            {"sword_zip_url": "https://crosswire.org/download/DifferentCom.zip"},
            {"archive_sha256": "111"},
        ):
            value = copy.deepcopy(self.manifest)
            value.update(update)
            self.write_manifest(value)
            with self.assertRaises(PilotError):
                load_manifest("example-commentary", self.manifests)
        with self.assertRaises(PilotError):
            load_manifest("../example-commentary", self.manifests)

    def test_observation_reports_binary_hash_and_never_emits_commentary_text(self):
        source = self.root / "source.zip"
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("mods.d/examplecom.conf",
                       "[ExampleCom]\nModDrv=zCom\nLang=en\nVersion=2.0\n"
                       "DistributionLicense=Public Domain\nVersification=KJV\n"
                       "SourceType=ThML\nDescription=Example commentary\n")
            z.writestr("modules/comments/zcom/example/ot.bzz",
                       b"SECRET ORIGINAL COMMENTARY NEVER PUBLISH")
        reader = self.root / "fake-diatheke"
        reader.write_text("#!/usr/bin/env python3\nprint('<p>SECRET READER TEXT</p>')\n")
        reader.chmod(0o700)

        def local_fetch(url, destination, provider):
            self.assertEqual(provider, "crosswire")
            shutil.copyfile(source, destination)
            return {"url": url, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "bytes": source.stat().st_size}

        with patch("commentary_intake.fetch", side_effect=local_fetch):
            result = inspect_resource("example-commentary", "observe",
                                      directory=self.manifests, reader=str(reader))
        report = json.dumps(result)
        self.assertEqual(result["status"], "observed_not_approved")
        self.assertEqual(result["sword_conf"]["distribution_license"], "Public Domain")
        self.assertTrue(result["reader_samples_all_present"])
        self.assertFalse(result["archive_pin_matches"])
        self.assertNotIn("SECRET ORIGINAL COMMENTARY", report)
        self.assertNotIn("SECRET READER TEXT", report)
        self.assertFalse(result["full_original_to_module_parity"])

    def test_changed_archive_blocks_stage_two_without_repinning(self):
        value = copy.deepcopy(self.manifest)
        value["archive_sha256"] = "a" * 64
        self.write_manifest(value)
        with patch("commentary_intake.fetch",
                   return_value={"sha256": "b" * 64, "bytes": 12, "url": value["sword_zip_url"]}):
            with self.assertRaisesRegex(PilotError, "changed"):
                inspect_resource("example-commentary", "2", directory=self.manifests)


if __name__ == "__main__":
    unittest.main()
