"""Source-neutral fail-closed tests for proposed commentary SWORD ID changes."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_sword_identity_migration import (
    proposed_sword_identity_migration,
)


class CommentarySwordMigrationTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.resource = "example-commentary"
        self.review_path = "config/commentary-intake/" + self.resource + "-reviewed-links.json"
        self.source_sha = "e" * 64
        self._write("modules/example-commentary/metadata.json", {
            "id": self.resource, "category": "commentary",
            "sword_id": "BRDEMO", "version": "0.1.0",
            "quality": {"status": "approved"},
            "origin": {"source_revision": "Archived source " + self.source_sha},
            "upstreams": [{"module_id": "DEMO", "last_integrated_version": "2.0"}],
        })
        self._write(self.review_path, {
            "resource_id": self.resource, "source_module_id": "DEMO",
            "source_archive_sha256": self.source_sha,
            "proposed_next_sword_id": "DEMO",
            "proposed_next_version": "0.1.1",
            "release_authorized": False, "package_staging_only": True,
        })
        self._write("catalog/v1/catalog.json", {
            "modules": [{
                "id": self.resource, "sword_id": "BRDEMO", "version": "0.1.0",
                "download": {
                    "url": "https://icfmp.github.io/Bible-Resources/sword/packages/BRDEMO.zip",
                    "sha256": "a" * 64, "size_bytes": 1234,
                },
            }],
        })
        self._write("config/release-plans/example-0.1.0.json", {
            "module_id": self.resource, "sword_id": "BRDEMO", "version": "0.1.0",
            "tag": "example-0.1.0", "zip_name": "BRDEMO-0.1.0.zip",
            "package_sha256": "a" * 64, "package_size_bytes": 1234,
        })

    def _write(self, name, payload):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(payload), encoding="utf-8")

    def _mutate(self, name, function):
        file = self.root / name
        payload = json.loads(file.read_text(encoding="utf-8"))
        function(payload)
        self._write(name, payload)

    def _plan(self):
        return proposed_sword_identity_migration(
            self.root, resource_id=self.resource, review_path=self.review_path
        )

    def test_private_proposal_preserves_old_asset_and_flags_provider_collision(self):
        plan = self._plan()
        self.assertEqual(plan["proposed_sword_id"], "DEMO")
        self.assertEqual(plan["proposed_new_versioned_asset"], "DEMO-0.1.1.zip")
        self.assertEqual(plan["old_versioned_asset_must_remain_immutable"], "BRDEMO-0.1.0.zip")
        self.assertEqual(plan["old_release_tag_must_remain_immutable"], "example-0.1.0")
        self.assertEqual(plan["proposed_single_catalogue_download"],
                         "https://icfmp.github.io/Bible-Resources/sword/packages/DEMO.zip")
        self.assertEqual(plan["proposed_conf_member"], "mods.d/demo.conf")
        self.assertTrue(plan["may_replace_upstream_module_in_installed_sword_library"])
        self.assertTrue(plan["previous_curated_sword_id_will_not_auto_uninstall"])
        self.assertFalse(plan["catalogue_changed"])
        self.assertFalse(plan["final_package_checksum_known"])
        self.assertFalse(plan["public_release_authorized"])

    def test_rejects_unrelated_id_or_unauthorized_source_edits(self):
        for field, value in [
            ("proposed_next_sword_id", "WRONG"),
            ("proposed_next_sword_id", "BRDEMO"),
            ("proposed_next_sword_id", "../DEMO"),
            ("proposed_next_version", "0.1.0"),
            ("release_authorized", True),
            ("package_staging_only", False),
            ("source_archive_sha256", "f" * 64),
        ]:
            with self.subTest(field=field):
                path = self.root / self.review_path
                original = path.read_bytes()
                try:
                    self._mutate(self.review_path, lambda p: p.update({field: value}))
                    with self.assertRaises(ValueError):
                        self._plan()
                finally:
                    path.write_bytes(original)

    def test_rejects_competing_curated_sword_id_or_old_digest_drift(self):
        name = "catalog/v1/catalog.json"
        file = self.root / name
        original = file.read_bytes()
        try:
            self._mutate(name, lambda p: p["modules"].append({
                "id": "other", "sword_id": "DEMO",
            }))
            with self.assertRaisesRegex(ValueError, "already belongs"):
                self._plan()
        finally:
            file.write_bytes(original)
        name = "config/release-plans/example-0.1.0.json"
        file = self.root / name
        original = file.read_bytes()
        try:
            self._mutate(name, lambda p: p.update(package_sha256="f" * 64))
            with self.assertRaisesRegex(ValueError, "source-identical"):
                self._plan()
        finally:
            file.write_bytes(original)

    def test_rejects_duplicate_active_plan_or_premature_catalogue_switch(self):
        plan_path = self.root / "config/release-plans/example-0.1.1.json"
        plan_path.write_text(json.dumps({
            "module_id": self.resource, "sword_id": "DEMO",
            "version": "0.1.1", "tag": "example-0.1.1",
        }), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "one active"):
            self._plan()
        plan_path.unlink()
        name = "catalog/v1/catalog.json"
        self._mutate(name, lambda p: p["modules"][0].update(sword_id="DEMO"))
        with self.assertRaisesRegex(ValueError, "source-identical"):
            self._plan()

    def test_real_repository_completed_identity_transition_matches_one_active_release(self):
        """The real repository must now prove its owner-approved current identity.

        Pre-release migration preflight remains tested using invented fixture
        data above; a completed release cannot also have an old active plan.
        """
        from catalogue_release_coverage import coverage
        metadata=json.loads(
            (ROOT/"modules/mhcc-crosswire/metadata.json").read_text(encoding="utf-8"))
        review=json.loads(
            (ROOT/"config/commentary-intake/mhcc-crosswire-reviewed-links.json").read_text(
                encoding="utf-8"))
        plan=json.loads(
            (ROOT/"config/release-plans/mhcc-0.1.1.json").read_text(encoding="utf-8"))
        catalogue=json.loads(
            (ROOT/"catalog/v1/catalog.json").read_text(encoding="utf-8"))
        row=[x for x in catalogue["modules"] if x["id"]=="mhcc-crosswire"]
        self.assertEqual(len(row),1)
        self.assertEqual(metadata["sword_id"],review["proposed_next_sword_id"])
        self.assertEqual(metadata["version"],review["proposed_next_version"])
        self.assertEqual(row[0]["sword_id"],metadata["sword_id"])
        self.assertEqual(row[0]["version"],metadata["version"])
        self.assertEqual(plan["sword_id"],metadata["sword_id"])
        self.assertEqual(plan["version"],metadata["version"])
        self.assertEqual(plan["zip_name"],
                         metadata["sword_id"]+"-"+metadata["version"]+".zip")
        self.assertEqual(plan["package_sha256"],row[0]["download"]["sha256"])
        self.assertEqual(plan["package_size_bytes"],row[0]["download"]["size_bytes"])
        self.assertFalse((ROOT/"config/release-plans/mhcc-0.1.0.json").exists())
        self.assertFalse((ROOT/"modules/mhcc-crosswire/profiles/en.json").exists())
        self.assertEqual(coverage(ROOT)["planned"][0][1]["module_id"],"mhcc-crosswire")


if __name__ == "__main__":
    unittest.main()
