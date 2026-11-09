"""Machine-readable Bible Resources catalogue update contract.

Tests the REAL approved resource payload and the generated public JSON, not
a mocked catalogue. The package checksum must describe download bytes, and
the SWORD .conf Version must agree with the curated release version.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate as validator
from build import build
from check_updates import parse_conf

BASE = "https://icfmp.github.io/Bible-Resources/"


class CatalogueUpdateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name) / "dist"
        cls.generated_entries = build(ROOT, cls.output, BASE)
        cls.catalogue = json.loads(
            (cls.output / "catalog/v1/catalog.json").read_text(encoding="utf-8"))
        cls.published_snapshot = json.loads(
            (ROOT / "catalog/v1/catalog.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_snapshot_and_generated_feed_are_identical(self):
        self.assertEqual(self.published_snapshot, self.catalogue)
        self.assertEqual(self.catalogue["schema_version"], 1)
        self.assertEqual(self.catalogue["repository_url"], BASE)
        self.assertEqual(self.catalogue["modules"], self.generated_entries)

    def test_every_approved_module_exposes_update_identity_and_exact_download(self):
        approved = {
            m["id"]: (directory, m)
            for directory, m in validator.validate(ROOT)[0]
            if m["quality"]["status"] == "approved"
        }
        self.assertTrue(approved, "Real release contract requires at least one approved resource")
        entries = self.catalogue["modules"]
        self.assertEqual(len(entries), len(approved))
        seen = set()
        for entry in entries:
            with self.subTest(module=entry["id"]):
                module_id = entry["id"]
                self.assertNotIn(module_id, seen)
                seen.add(module_id)
                directory, metadata = approved[module_id]
                self.assertEqual(entry["canonical_edition_id"],
                                 metadata["canonical_edition_id"])
                self.assertEqual(entry["sword_id"], metadata["sword_id"])
                self.assertEqual(entry["version"], metadata["version"])
                self.assertEqual(entry["edition"], metadata["quality"]["edition"])
                self.assertEqual(entry["versification"], metadata.get("versification"))
                self.assertTrue(metadata["rights"]["redistribution_allowed"])
                self.assertEqual(metadata["quality"]["status"], "approved")

                uri = urlparse(entry["download"]["url"])
                self.assertEqual(uri.scheme, "https")
                self.assertEqual(uri.netloc, "icfmp.github.io")
                self.assertFalse(uri.query or uri.fragment or uri.params)
                prefix = "/Bible-Resources/"
                self.assertTrue(uri.path.startswith(prefix))
                rel = unquote(uri.path[len(prefix):])
                self.assertEqual(rel, f"sword/packages/{entry['sword_id']}.zip")
                pkg = self.output / rel
                self.assertTrue(pkg.is_file())
                self.assertEqual(pkg.stat().st_size, entry["download"]["size_bytes"])
                self.assertEqual(hashlib.sha256(pkg.read_bytes()).hexdigest(),
                                 entry["download"]["sha256"])

                with zipfile.ZipFile(pkg) as archive:
                    names = archive.namelist()
                    self.assertEqual(len(names), len(set(names)))
                    conf_name = f"mods.d/{entry['sword_id'].lower()}.conf"
                    self.assertIn(conf_name, names)
                    fields = parse_conf(archive.read(conf_name))
                    self.assertEqual(fields["module_id"], entry["sword_id"])
                    self.assertEqual(fields["version"], entry["version"])
                    if entry["versification"] is not None:
                        self.assertEqual(fields["versification"], entry["versification"])

    def test_version_mismatch_fails_publication_before_any_update_signal(self):
        original_parse = validator.parse_conf

        def changed_version(path):
            section, fields = original_parse(path)
            fields = dict(fields)
            fields["Version"] = "999.0.0"
            return section, fields

        with patch.object(validator, "parse_conf", side_effect=changed_version):
            _modules, errors = validator.validate(ROOT)
        self.assertTrue(any(
            "does not match curated metadata version" in error for error in errors
        ), "Curated version and installed SWORD Version must never diverge")

    def test_catalogue_is_only_approved_resources_not_upstream_monitor(self):
        self.assertTrue(all(entry["id"] and entry["version"]
                            for entry in self.catalogue["modules"]))
        self.assertNotIn("upstreams", self.catalogue)
        self.assertNotIn("installed_versions", self.catalogue)
        self.assertNotIn("auto_update", self.catalogue)


if __name__ == "__main__":
    unittest.main()
