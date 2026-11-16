"""Safeguards for the checked-in script lifecycle/usage inventory."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tool_registry import CORE, ROLES, generate, markdown


class ScriptInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = generate(ROOT)

    def test_all_tracked_tools_are_classified_without_any_delete_instruction(self):
        report = self.result
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"],
                         "SCRIPT_INVENTORY_STATIC_REVIEW_NOT_APPROVAL")
        rows = report["files"]
        paths = [r["path"] for r in rows]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertGreaterEqual(len(rows), 140)
        self.assertTrue(all(r["classification"] in ROLES for r in rows))
        self.assertTrue(all(len(r["sha256_at_inventory"]) == 64 for r in rows))
        self.assertTrue(all("delete" not in r["proposed_action"].lower()
                            for r in rows))

    def test_known_stable_packaging_and_commentary_inputs_have_core_contract(self):
        entries = {v["path"].rsplit("/",1)[1]: v
                   for v in self.result["files"]}
        for name in ("build.py", "validate.py", "publish_reviewed_release.py",
                     "release_preflight.py", "commentary_intake.py",
                     "commentary_native_inventory.py",
                     "reviewed_compiled_commentary_rebuild.py"):
            self.assertIn(name, entries)
            self.assertIn(name, CORE)
            self.assertEqual(entries[name]["classification"], "KEEP_GENERIC")
        self.assertTrue(any(ref.endswith("test_release_preflight.py")
                            for ref in entries["release_preflight.py"]["static_references"]))
        self.assertTrue(any("workflow" in ref
                            for ref in entries["validate.py"]["static_references"]))

    def test_registry_has_no_promoted_editorial_or_publication_claims(self):
        for entry in self.result["files"]:
            self.assertEqual(entry["release_approval"],
                             "never inferred from inventory")
            self.assertIn("separately", entry["source_sha_requirement"])
        self.assertIn("UNDECIDED", markdown(self.result))
        self.assertIn("historical", " ".join(self.result["limitations"]).lower())


if __name__ == "__main__":
    unittest.main()
