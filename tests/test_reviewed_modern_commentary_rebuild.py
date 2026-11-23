"""Fail-closed regression tests for the distinct modern commentary source gate."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reviewed_modern_commentary_rebuild import reviewed_modern_commentary_errors
from validate import parse_conf


class ModernCommentaryReleaseContract(unittest.TestCase):
    def setUp(self):
        self.module = ROOT / "modules/hmcc-modern"
        self.metadata = json.loads((self.module / "metadata.json").read_text())
        self.conf = parse_conf(
            self.module / "payload/mods.d/hmccmodern.conf")[1]

    def test_owner_decision_evidence_is_edition_owned_and_complete(self):
        """Keep the four release evidence records with their canonical edition."""
        evidence = ROOT / "sources/cleaned/commentaries/en/hmcc-modern/editorial/evidence"
        required = (
            "OWNER_EDITORIAL_DECISIONS_2026-11-19.json",
            "ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json",
            "FOUR_NATIVE_LINK_ERRATA_REVIEW_2026-11-18.json",
            "PRIMARY_SOURCE_STRICT_TWO_SECTION_QUARANTINE_2026-11-19.json",
        )
        for name in required:
            with self.subTest(name=name):
                path = evidence / name
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)
        plan = json.loads(
            (ROOT / "config/commentary-rebuilds/hmcc-modern.json").read_text(
                encoding="utf-8"))
        self.assertEqual(
            plan["source_decisions"],
            "sources/cleaned/commentaries/en/hmcc-modern/editorial/evidence/"
            "OWNER_EDITORIAL_DECISIONS_2026-11-19.json")
        self.assertFalse((ROOT / "work").exists())

    def test_real_authenticated_binary_and_provenance_pass(self):
        self.assertEqual(
            reviewed_modern_commentary_errors(
                self.module, ROOT, self.metadata, self.conf), [])

    def test_a_modified_compressed_member_fails_even_if_other_metadata_is_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "hmcc-modern"
            shutil.copytree(self.module, target)
            member = target / "payload/modules/comments/zcom/hmccmodern/ot.czz"
            member.write_bytes(member.read_bytes() + b"\x00")
            failures = reviewed_modern_commentary_errors(
                target, ROOT, self.metadata, self.conf)
            self.assertTrue(failures)
            self.assertIn("SHA256 differs", failures[0])

    def test_extra_payload_member_fails_even_when_hashes_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "hmcc-modern"
            shutil.copytree(self.module, target)
            extra = target / "payload/modules/comments/zcom/hmccmodern/nt.unknown"
            extra.write_bytes(b"unreviewed bytes")
            failures = reviewed_modern_commentary_errors(
                target, ROOT, self.metadata, self.conf)
            self.assertTrue(failures)
            self.assertIn("inventory", failures[0].lower())

    def test_unapproved_module_path_and_driver_cannot_pass(self):
        revised = json.loads(json.dumps(self.metadata))
        revised["sword_id"] = "../escape"
        failures = reviewed_modern_commentary_errors(
            self.module, ROOT, revised, self.conf)
        self.assertTrue(failures)
        modified = dict(self.conf, BlockType="BOOK")
        failures = reviewed_modern_commentary_errors(
            self.module, ROOT, self.metadata, modified)
        self.assertTrue(failures)
        self.assertIn("metadata", failures[0].lower())

    def test_false_owner_authorization_fails(self):
        revised = json.loads(json.dumps(self.metadata))
        revised["rights"]["redistribution_allowed"] = False
        failures = reviewed_modern_commentary_errors(
            self.module, ROOT, revised, self.conf)
        self.assertTrue(failures)
        self.assertIn("rights", failures[0].lower())

    def test_a_different_sword_configuration_fails(self):
        modified = dict(self.conf)
        modified["Version"] = "0.2.0"
        failures = reviewed_modern_commentary_errors(
            self.module, ROOT, self.metadata, modified)
        self.assertTrue(failures)
        self.assertIn("metadata", failures[0].lower())


if __name__ == "__main__":
    unittest.main()
