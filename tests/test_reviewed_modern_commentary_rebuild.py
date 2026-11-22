"""Fail-closed regression tests for the distinct modern commentary source gate."""
from pathlib import Path
import json
import hashlib
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

    def test_existing_editorial_witnesses_have_byte_exact_pins(self):
        """Explicitly detect any byte difference in the two owner-reviewed files."""
        from reviewed_modern_commentary_rebuild import REVIEWED_MODERN_WITNESSES
        pin = REVIEWED_MODERN_WITNESSES["hmcc-modern"]
        actual = {
            "plan_sha256": hashlib.sha256(
                (ROOT / "config/commentary-rebuilds/hmcc-modern.json").read_bytes()
            ).hexdigest(),
            "decisions_sha256": hashlib.sha256(
                (ROOT / pin["decisions_path"]).read_bytes()
            ).hexdigest(),
        }
        self.assertEqual(
            (pin["plan_sha256"], pin["decisions_sha256"]),
            (actual["plan_sha256"], actual["decisions_sha256"]),
        )

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

    def test_revised_owner_decisions_fail_even_when_counts_stay_unchanged(self):
        """Changed destinations cannot be approved by editing a JSON value."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original_plan = ROOT / "config/commentary-rebuilds/hmcc-modern.json"
            plan = root / "config/commentary-rebuilds/hmcc-modern.json"
            plan.parent.mkdir(parents=True)
            shutil.copy2(original_plan, plan)
            original = (ROOT / "work/hmcc-modern/production/"
                        "OWNER_EDITORIAL_DECISIONS_2026-11-19.json")
            decisions = (root / "work/hmcc-modern/production/"
                         "OWNER_EDITORIAL_DECISIONS_2026-11-19.json")
            decisions.parent.mkdir(parents=True)
            shutil.copy2(original, decisions)
            self.assertEqual(
                reviewed_modern_commentary_errors(
                    self.module, root, self.metadata, self.conf), []
            )
            altered = json.loads(decisions.read_text(encoding="utf-8"))
            self.assertTrue(altered["link_cases"])
            altered["link_cases"][0]["approved_derived_destinations"][0] = "Gen.1.1"
            decisions.write_text(json.dumps(altered), encoding="utf-8")
            result = reviewed_modern_commentary_errors(
                self.module, root, self.metadata, self.conf)
            self.assertTrue(result)
            self.assertIn("Pinned editorial evidence SHA256 differs", result[0])

    def test_review_plan_is_independently_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "config/commentary-rebuilds/hmcc-modern.json"
            plan.parent.mkdir(parents=True)
            original = ROOT / "config/commentary-rebuilds/hmcc-modern.json"
            shutil.copy2(original, plan)
            altered = json.loads(plan.read_text(encoding="utf-8"))
            altered["authorization"]["decision"] += " Unreviewed new approval."
            plan.write_text(json.dumps(altered), encoding="utf-8")
            result = reviewed_modern_commentary_errors(
                self.module, root, self.metadata, self.conf)
            self.assertTrue(result)
            self.assertIn("Pinned editorial evidence SHA256 differs", result[0])

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
