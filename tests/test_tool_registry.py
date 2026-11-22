"""Safeguards for the checked-in script lifecycle/usage inventory."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tool_registry import (CORE, ROLES, REVIEWED_ACTIVE, REVIEWED_EDITION_COUPLED,
                           generate, markdown)


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
        self.assertTrue(rows, 'An empty tool inventory cannot describe production')
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


    def test_remaining_scripts_have_explicit_reviewed_lifecycle(self):
        """All currently retained tools need an actual reviewer decision."""
        rows = self.result["files"]
        names = {r["path"].rsplit("/", 1)[-1] for r in rows}
        self.assertEqual(
            names,
            (CORE | REVIEWED_ACTIVE | REVIEWED_EDITION_COUPLED) & names,
        )
        self.assertEqual(
            len([r for r in rows if r["classification"] == "UNDECIDED"]), 0
        )
        reviewed = {r["path"].rsplit("/", 1)[-1]: r for r in rows
                    if r["path"].rsplit("/", 1)[-1] in REVIEWED_ACTIVE}
        self.assertEqual(set(reviewed), REVIEWED_ACTIVE)
        for name, row in reviewed.items():
            self.assertEqual(row["classification"], "KEEP_GENERIC")
            self.assertEqual(row["confidence"], "medium")
            if name != "__init__.py":
                self.assertTrue(row["static_references"], name)
        coupled = {r["path"].rsplit("/", 1)[-1]: r for r in rows
                   if r["path"].rsplit("/", 1)[-1] in REVIEWED_EDITION_COUPLED}
        self.assertEqual(set(coupled), REVIEWED_EDITION_COUPLED)
        self.assertTrue(all(r["classification"] == "GENERALIZE"
                            for r in coupled.values()))
        # These gates currently secure different *approved* publications.
        for module_id, expected_mode in (
            ("mhc-crosswire", "reviewed_osis_commentary_rebuild"),
            ("hmcc-modern", "reviewed_modern_commentary_rebuild"),
            ("mhcc-crosswire", "reviewed_compiled_commentary_rebuild"),
        ):
            import json
            metadata = json.loads(
                (ROOT / "modules" / module_id / "metadata.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["quality"]["status"], "approved")
            self.assertEqual(metadata["index_audit"]["mode"], expected_mode)
            self.assertIn("scripts/" + expected_mode + ".py",
                          {r["path"] for r in rows})





    def test_osis_source_native_helpers_are_package_owned(self):
        """Generic OSIS reference and markup screens are import-only and tested."""
        entries = {row["path"]: row for row in self.result["files"]}
        for stem, caller in (
            ("source_native_osis_target_addressability",
             "scripts/approved_osis_sword_candidate.py"),
            ("source_native_osis_structure_screen",
             "scripts/approved_osis_sword_candidate.py"),
        ):
            with self.subTest(helper=stem):
                relocated = "scripts/research/bible/" + stem + ".py"
                self.assertIn(relocated, entries)
                self.assertNotIn("scripts/" + stem + ".py", entries)
                self.assertIn(caller, entries[relocated]["static_references"])
                self.assertIn("tests/test_" + stem + ".py",
                              entries[relocated]["static_references"])

    def test_osis_boundary_evidence_is_a_shared_import_only_library(self):
        entries = {row["path"]: row for row in self.result["files"]}
        stem = "source_native_osis_boundary_positions"
        expected = "scripts/research/bible/" + stem + ".py"
        self.assertIn(expected, entries)
        self.assertNotIn("scripts/" + stem + ".py", entries)
        self.assertIn("scripts/approved_osis_sword_candidate.py",
                      entries[expected]["static_references"])
        self.assertIn("tests/test_" + stem + ".py",
                      entries[expected]["static_references"])

    def test_native_raw_reader_is_shared_not_hidden_in_usfx_cli(self):
        """OSIS code must not import original-USFX-only command for native text."""
        entries = {row["path"]: row for row in self.result["files"]}
        shared = "scripts/research/bible/native_raw_main_text.py"
        self.assertIn(shared, entries)
        refs = entries[shared]["static_references"]
        for p in (
            "scripts/approved_osis_sword_candidate.py",
            "tests/test_native_raw_main_text.py",
        ):
            with self.subTest(caller=p):
                self.assertIn(p, refs)



    def test_current_osis_source_native_helpers_are_package_owned(self):
        """Only maintained OSIS/native helpers should have live consumers."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "native_milestone_pair_audit": (
                "scripts/approved_osis_sword_candidate.py",
                "tests/test_native_milestone_pair_audit.py"),
            "native_sword_markup_census": (
                "scripts/research/bible/native_raw_main_text.py",
                "tests/test_native_sword_markup_census.py"),
            "source_native_ordered_body": (
                "scripts/approved_osis_sword_candidate.py",
                "tests/test_source_native_ordered_body.py"),
            "source_native_note_positions": (
                "scripts/approved_osis_sword_candidate.py",
                "tests/test_source_native_note_positions.py"),
            "source_osis_verse_notes": (
                "scripts/approved_osis_sword_candidate.py",
                "tests/test_source_osis_verse_notes.py"),
        }
        for stem, callers in helpers.items():
            with self.subTest(helper=stem):
                path = "scripts/research/bible/" + stem + ".py"
                self.assertIn(path, entries)
                self.assertTrue(entries[path]["has_direct_tests_by_filename"])
                for caller in callers:
                    self.assertIn(caller, entries[path]["static_references"])




    def test_approved_osis_native_gate_uses_curated_sources(self):
        """An approved cleaned master, not an intake ZIP, enters native QA."""
        current = {row["path"] for row in self.result["files"]}
        self.assertIn("scripts/approved_osis_sword_candidate.py", current)
        self.assertTrue(
            (ROOT / ".github/workflows/approved-osis-native-audit.yml").is_file()
        )
        source = (ROOT / "scripts/approved_osis_sword_candidate.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("approved_source_for(resource_id)", source)

    def test_active_workflows_only_reference_existing_shared_scripts(self):
        """Check current workflows rather than naming retired pilot commands."""
        import re

        active = {row["path"] for row in self.result["files"]}
        pattern = re.compile(r"(?<![A-Za-z0-9_/])scripts/[A-Za-z0-9_./-]+\.(?:py|sh)\b")
        checked = 0
        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            content = workflow.read_text(encoding="utf-8")
            for script in pattern.findall(content):
                checked += 1
                with self.subTest(workflow=workflow.name, script=script):
                    self.assertIn(script, active)
        self.assertGreater(checked, 0, "Workflow references were not inspected")

    def test_registry_has_no_promoted_editorial_or_publication_claims(self):
        for entry in self.result["files"]:
            self.assertEqual(entry["release_approval"],
                             "never inferred from inventory")
            self.assertIn("separately", entry["source_sha_requirement"])
        self.assertIn("UNDECIDED", markdown(self.result))
        self.assertIn("historical", " ".join(self.result["limitations"]).lower())


if __name__ == "__main__":
    unittest.main()
