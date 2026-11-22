"""Safeguards for the checked-in script lifecycle/usage inventory."""
import os
from pathlib import Path
import subprocess
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

    def test_proven_generic_tools_keep_shared_contracts(self):
        entries = {v["path"].rsplit("/", 1)[-1]: v
                   for v in self.result["files"]}
        for name in ("promote_sword_preview.py", "commentary_text_delta.py"):
            with self.subTest(shared=name):
                self.assertEqual(entries[name]["classification"], "KEEP_GENERIC")
                self.assertTrue(entries[name]["has_direct_tests_by_filename"])

    def test_lsg_source_probes_are_edition_owned_and_still_invoked(self):
        """LSG-specific diagnostics are not generic, yet retain their real callers."""
        entries = {entry["path"]: entry for entry in self.result["files"]}
        for name, workflow, test_name in (
            ("lsg_sword_compare.py", "lsg-fidelity.yml",
             "test_lsg_sword_compare.py"),
            ("probe_lsg_v11n.py", "lsg-v11n-probe.yml",
             "test_lsg_v11n_probe.py"),
        ):
            with self.subTest(name=name):
                local = "modules/lsg-1910/tools/" + name
                self.assertNotIn("scripts/historical/lsg/" + name, entries)
                self.assertIn(local, entries)
                self.assertEqual(entries[local]["classification"], "MODULE_LOCAL")
                # A filename heuristic can miss a real differently named test.
                # Verify the actual imported test rather than the hint.
                self.assertIn(".github/workflows/" + workflow,
                              entries[local]["static_references"])
                self.assertIn("tests/" + test_name,
                              entries[local]["static_references"])

    def test_lsg_module_tools_remain_real_command_line_entrypoints(self):
        """Direct workflow commands still start, without old-path wrappers."""
        for name in ("lsg_sword_compare.py", "probe_lsg_v11n.py"):
            with self.subTest(name=name):
                command = ROOT / "modules/lsg-1910/tools" / name
                result = subprocess.run(
                    [sys.executable, str(command), "--help"],
                    cwd=ROOT,
                    env=dict(os.environ, PYTHONPATH=str(ROOT / "scripts")),
                    capture_output=True, text=True, check=False, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_retired_darby_011_preflight_does_not_leave_live_entrypoints(self):
        """The historical 0.1.0 baseline is no longer in the approved 0.1.1 module."""
        entries = {entry["path"] for entry in self.result["files"]}
        self.assertNotIn("scripts/prepare_darby_011_private_release_candidate.py",
                         entries)
        self.assertNotIn("scripts/probe_darby_011_final_android.py", entries)
        self.assertFalse((ROOT / ".github/workflows/darby-0.1.1-preflight.yml").exists())

    def test_darby_source_native_replay_is_owned_by_the_approved_module(self):
        """A real 3-reader private QA caller is not shared production tooling."""
        entries = {item["path"]: item for item in self.result["files"]}
        local = ("modules/darby-jnd-2024/tools/"
                 "probe_private_repaired_darby_sword.py")
        self.assertIn(local, entries)
        self.assertNotIn("scripts/probe_private_repaired_darby_sword.py", entries)
        self.assertEqual(entries[local]["classification"], "MODULE_LOCAL")
        for workflow in ("darby-private-repaired-sword.yml",
                         "darby-andbible-jsword.yml",
                         "darby-andbible-android-private.yml"):
            with self.subTest(workflow=workflow):
                self.assertIn(".github/workflows/" + workflow,
                              entries[local]["static_references"])

    def test_darby_private_source_probe_still_starts_from_repository_root(self):
        command = (ROOT / "modules/darby-jnd-2024/tools/"
                   "probe_private_repaired_darby_sword.py")
        result = subprocess.run(
            [sys.executable, str(command), "--help"],
            cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "scripts")),
            capture_output=True, text=True, check=False, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)
        self.assertIn("--division-overlay", result.stdout)

    def test_completed_original_mhcc_stock_reader_harnesses_are_retired(self):
        """Keep source identity and generic readers, not old one-off GUI adapters."""
        paths = {row["path"] for row in self.result["files"]}
        for name in (
            "commentary_private_candidate_xiphos_gui.py",
            "commentary_stock_andbible_android.py",
            "commentary_android_text_witness.py",
            "commentary_android_webview_debug.py",
            "commentary_stock_xiphos_smoke.py",
            "commentary_andbible_jsword.py",
        ):
            with self.subTest(name=name):
                self.assertNotIn("scripts/" + name, paths)
                self.assertNotIn("modules/mhcc-crosswire/tools/" + name, paths)
        for workflow in (
            "commentary-private-candidate-xiphos-gui.yml",
            "commentary-zcom-andbible-android.yml",
            "commentary-zcom-xiphos-private-smoke.yml",
            "commentary-zcom-andbible-jsword.yml",
        ):
            with self.subTest(workflow=workflow):
                self.assertFalse((ROOT / ".github/workflows" / workflow).exists())
        self.assertFalse(
            (ROOT / "tests/java/org/icfmp/research/"
             "CommentaryAndBibleJSwordProbeTest.java").exists()
        )
        # Source identity and true shared readers remain active and tested.
        for name in ("commentary_xiphos_dual_reader.py",
                     "commentary_stock_candidate.py",
                     "probe_andbible_android_private_import.py",
                     "probe_andbible_jsword.py",
                     "reader_xiphos_headless_smoke.py"):
            self.assertIn("scripts/" + name, paths)

    def test_nested_package_imports_count_as_real_static_callers(self):
        entries = {item["path"]: item for item in self.result["files"]}
        module = ("scripts/research/commentary/"
                  "commentary_chapter_neighbors.py")
        self.assertIn(module, entries)
        self.assertIn("scripts/commentary_private_text_compare.py",
                      entries[module]["static_references"])
        self.assertIn("tests/test_commentary_chapter_neighbors.py",
                      entries[module]["static_references"])
        self.assertIn("scripts/research/commentary/"
                      "commentary_chapter_p_boundaries.py", entries)
        self.assertIn(
            "scripts/research/commentary/commentary_chapter_p_boundaries.py",
            entries["scripts/research/commentary/"
                    "commentary_chapter_paragraph_overlap.py"]["static_references"],
        )

    def test_source_neutral_section_probes_are_package_scoped(self):
        """Every moved non-CLI helper retains its real consumer and direct test."""
        entries = {item["path"]: item for item in self.result["files"]}
        for stem in (
            "commentary_editorial_topology",
            "commentary_intro_chapter_text_review",
            "commentary_paragraph_witness_probe",
            "commentary_osis_rebuild_preflight",
        ):
            with self.subTest(helper=stem):
                new_path = f"scripts/research/commentary/{stem}.py"
                self.assertIn(new_path, entries)
                self.assertNotIn(f"scripts/{stem}.py", entries)
                callers = entries[new_path]["static_references"]
                self.assertIn("scripts/commentary_section_scope_audit.py", callers)
                self.assertIn(f"tests/test_{stem}.py", callers)

    def test_extracted_section_evidence_has_real_import_callers(self):
        """Both extracted helpers retain their precise source-bound callers."""
        entries = {entry["path"]: entry for entry in self.result["files"]}
        lexical = "scripts/research/commentary/commentary_lexical_overlap.py"
        chapter = "scripts/research/commentary/commentary_chapter_body_evidence.py"
        self.assertIn(lexical, entries)
        self.assertIn(chapter, entries)
        self.assertIn("scripts/commentary_section_scope_audit.py",
                      entries[chapter]["static_references"])
        self.assertIn("tests/test_commentary_section_scope_audit.py",
                      entries[chapter]["static_references"])
        self.assertIn(chapter, entries[lexical]["static_references"])
        self.assertIn("tests/test_commentary_section_scope_audit.py",
                      entries[lexical]["static_references"])

    def test_original_link_identity_gate_is_a_scoped_import_only_helper(self):
        """Check all real module and regression-test consumers after extraction."""
        entries = {entry["path"]: entry for entry in self.result["files"]}
        name = "scripts/research/commentary/commentary_original_link_identity.py"
        self.assertIn(name, entries)
        for caller in (
            "scripts/commentary_modern_reference_gate.py",
            "scripts/commentary_modern_linked_candidate_preview.py",
            "tests/test_commentary_modern_reference_gate.py",
        ):
            with self.subTest(caller=caller):
                self.assertIn(caller, entries[name]["static_references"])
        self.assertNotIn("scripts/commentary_original_link_identity.py", entries)

    def test_link_disposition_review_keeps_real_cli_and_test_imports(self):
        """Original link proposal checking remains pinned and read-only."""
        entries = {entry["path"]: entry for entry in self.result["files"]}
        helper = ("scripts/research/commentary/"
                  "commentary_link_disposition_review.py")
        self.assertIn(helper, entries)
        for caller in ("scripts/commentary_modern_reference_gate.py",
                       "tests/test_commentary_modern_reference_gate.py"):
            self.assertIn(caller, entries[helper]["static_references"])
        self.assertNotIn("scripts/commentary_link_disposition_review.py", entries)

    def test_nonlink_analyses_share_one_reviewed_research_module(self):
        """Check all substantive imports after retiring two root module paths."""
        entries = {row["path"]: row for row in self.result["files"]}
        new = "scripts/research/commentary/commentary_nonlink_analysis.py"
        self.assertIn(new, entries)
        self.assertNotIn("scripts/commentary_nonlink_words.py", entries)
        self.assertNotIn("scripts/commentary_nonlink_word_alignment.py", entries)
        for caller in (
            "scripts/commentary_private_text_compare.py",
            "scripts/research/commentary/commentary_prose_cross_slot.py",
            "scripts/research/commentary/commentary_unresolved_lexical_triage.py",
            "scripts/commentary_section_scope_audit.py",
            "scripts/research/commentary/commentary_lexical_overlap.py",
            "tests/test_commentary_nonlink_words.py",
            "tests/test_commentary_nonlink_word_alignment.py",
            ".github/workflows/commentary-modern-source-receipt.yml",
        ):
            with self.subTest(caller=caller):
                self.assertIn(caller, entries[new]["static_references"])

    def test_source_neutral_lexical_and_cross_slot_helpers_are_packaged(self):
        """Non-CLI evidence algorithms must remain imported from one package."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "commentary_near_prose_unicode_review":
                ("scripts/commentary_private_text_compare.py",
                 "tests/test_commentary_near_prose_unicode_review.py"),
            "commentary_reference_cross_slot":
                ("scripts/commentary_private_text_compare.py",
                 "scripts/commentary_xiphos_dual_reader.py",
                 "tests/test_commentary_reference_cross_slot.py"),
            "commentary_source_identity_lexical_gate":
                ("scripts/commentary_private_text_compare.py",
                 "tests/test_commentary_source_identity_lexical_gate.py"),
            "commentary_prose_cross_slot":
                ("scripts/commentary_anchor_parity.py",
                 "scripts/commentary_shared_raw_source_units.py",
                 "tests/test_commentary_prose_cross_slot.py"),
            "commentary_unresolved_lexical_triage":
                ("scripts/commentary_section_scope_audit.py",
                 "scripts/research/commentary/commentary_chapter_body_evidence.py",
                 "tests/test_commentary_unresolved_lexical_triage.py"),
        }
        for name, consumers in helpers.items():
            with self.subTest(helper=name):
                old_path = "scripts/" + name + ".py"
                new_path = "scripts/research/commentary/" + name + ".py"
                self.assertNotIn(old_path, entries)
                self.assertFalse((ROOT / old_path).exists())
                self.assertIn(new_path, entries)
                self.assertTrue((ROOT / new_path).is_file())
                self.assertTrue(entries[new_path]["has_direct_tests_by_filename"])
                self.assertEqual(entries[new_path]["entrypoint_hint"],
                                 "library, native helper or workflow-invoked")
                for caller in consumers:
                    self.assertIn(caller, entries[new_path]["static_references"])

    def test_completed_hmcc_modern_staging_is_not_an_active_publisher(self):
        """Version-pinned first-release bootstraps belong to Git history only."""
        entries = {row["path"] for row in self.result["files"]}
        self.assertNotIn("scripts/stage_hmcc_modern_release.py", entries)
        self.assertFalse(
            (ROOT / ".github/workflows/stage-hmcc-modern-release.yml").exists()
        )
        # Retiring the pre-release job must not remove approved release inputs.
        self.assertTrue((ROOT / "modules/hmcc-modern/metadata.json").is_file())
        self.assertTrue(
            (ROOT / "config/release-plans/hmcc-modern-0.1.0.json").is_file()
        )

    def test_registry_has_no_promoted_editorial_or_publication_claims(self):
        for entry in self.result["files"]:
            self.assertEqual(entry["release_approval"],
                             "never inferred from inventory")
            self.assertIn("separately", entry["source_sha_requirement"])
        self.assertIn("UNDECIDED", markdown(self.result))
        self.assertIn("historical", " ".join(self.result["limitations"]).lower())


if __name__ == "__main__":
    unittest.main()
