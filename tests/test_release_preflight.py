"""End-to-end tests of one production release preflight across three editions."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_preflight import PreflightError, inspect_approved_releases


class CrossEditionReleasePreflightTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ids = ("lsg-1910", "darby-jnd-2024", "mhcc-crosswire")
        cls.report = inspect_approved_releases(ROOT, cls.ids)

    def test_actual_rawtext_ztext_zcom_published_modules_share_the_same_interface(self):
        report = self.report
        self.assertEqual(report["status"],
                         "OFFLINE_APPROVED_RELEASE_PREFLIGHT_NOT_PUBLICATION")
        by_id = {r["resource_id"]: r for r in report["modules"]}
        self.assertEqual(set(by_id), set(self.ids))
        self.assertEqual(by_id["lsg-1910"]["driver"], "RawText")
        self.assertEqual(by_id["darby-jnd-2024"]["driver"], "zText")
        self.assertEqual(by_id["mhcc-crosswire"]["driver"], "zCom")
        for record in by_id.values():
            self.assertRegex(record["package_sha256"], r"^[a-f0-9]{64}$")
            self.assertGreater(record["package_size_bytes"], 0)
            self.assertTrue(record["native_payload_member_identity_verified"])
            self.assertTrue(record["release_authorization_verified_in_current_plan"])
            self.assertFalse(record["public_download_checked"])
        self.assertFalse(report["source_text_exported"])
        self.assertFalse(report["module_content_mutated"])
        self.assertFalse(report["public_release_created"])
        self.assertFalse(report["catalogue_changed"])

    def test_real_preflight_matches_approved_three_distinct_release_plans(self):
        by_id = {r["resource_id"]: r for r in self.report["modules"]}
        for record in by_id.values():
            path = ROOT / "config/release-plans" / (
                record["release_tag"] + ".json")
            plan = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(resource=record["resource_id"]):
                self.assertEqual(record["package_sha256"],
                                 plan["package_sha256"])
                self.assertEqual(record["package_size_bytes"],
                                 plan["package_size_bytes"])
                self.assertEqual(record["sword_id"], plan["sword_id"])
                self.assertEqual(record["version"], plan["version"])

    def test_unknown_or_repeated_or_malicious_resource_ids_fail_closed(self):
        for values in ((), ("does-not-exist",),
                       ("lsg-1910", "lsg-1910"), ("../lsg-1910",),
                       ("mhcc-crosswire/../../etc",)):
            with self.subTest(values=values):
                with self.assertRaises(PreflightError):
                    inspect_approved_releases(ROOT, values)


if __name__ == "__main__":
    unittest.main()
