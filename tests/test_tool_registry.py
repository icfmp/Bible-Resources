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


    def test_retired_legacy_usfx_probes_do_not_remain_in_shared_scripts(self):
        """One-off USFX/stock parity research is not the current OSIS process."""
        entries = {row["path"] for row in self.result["files"]}
        for name in (
            "publisher_osis_usfx_parity.py",
            "source_native_maintext_probe.py",
            "source_native_record_scope_triage.py",
            "source_native_structural_whitespace.py",
            "source_usfx_newline_provenance.py",
            "native_book_intro_screen.py",
            "sword_missing_verse_witness.py",
        ):
            self.assertNotIn("scripts/" + name, entries)
        for name in (
            "maintext_whitespace_patterns.py",
            "native_absorbed_verse_groups.py",
            "note_whitespace_diagnostics.py",
            "source_native_layout_anchors.py",
            "source_native_nonspace_boundaries.py",
            "source_native_structure_topology.py",
            "source_native_word_boundaries.py",
            "source_native_scope.py",
            "source_native_notes_audit.py",
        ):
            self.assertNotIn("scripts/research/bible/" + name, entries)


    def test_osis_source_native_helpers_are_package_owned(self):
        """Generic OSIS reference and markup screens are import-only and tested."""
        entries = {row["path"]: row for row in self.result["files"]}
        for stem, caller in (
            ("source_native_osis_target_addressability",
             "scripts/repair_osis_note_links.py"),
            ("source_native_osis_structure_screen",
             "scripts/publisher_osis_sword_candidate.py"),
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
        self.assertIn("scripts/publisher_osis_sword_candidate.py",
                      entries[expected]["static_references"])
        self.assertIn("modules/darby-jnd-2024/tools/probe_private_repaired_darby_sword.py",
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
            "scripts/publisher_osis_sword_candidate.py",
            "scripts/inspect_paragraph_rendering.py",
            "modules/darby-jnd-2024/tools/probe_private_repaired_darby_sword.py",
            "tests/test_native_raw_main_text.py",
        ):
            with self.subTest(caller=p):
                self.assertIn(p, refs)


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

    def test_old_section_scope_experiment_is_not_retained(self):
        """Completed stock commentary section research stays in Git history."""
        active = {row["path"] for row in self.result["files"]}
        retired = (
            "commentary_section_scope_audit",
            "commentary_chapter_body_evidence",
            "commentary_editorial_topology",
            "commentary_intro_chapter_text_review",
            "commentary_layout_census",
            "commentary_lexical_overlap",
            "commentary_literal_erratum_preflight",
            "commentary_osis_intro_transport_probe",
            "commentary_osis_rebuild_preflight",
            "commentary_paragraph_witness_probe",
            "commentary_public_metadata_preflight",
            "commentary_rebuild_attestation_draft",
            "commentary_source_erratum_compiled_probe",
        )
        for stem in retired:
            self.assertNotIn("scripts/" + stem + ".py", active)
            self.assertNotIn("scripts/research/commentary/" + stem + ".py",
                             active)


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
            "tests/test_commentary_nonlink_words.py",
            "tests/test_commentary_nonlink_word_alignment.py",
            ".github/workflows/commentary-modern-source-receipt.yml",
        ):
            with self.subTest(caller=caller):
                self.assertIn(caller, entries[new]["static_references"])

    def test_current_osis_source_native_helpers_are_package_owned(self):
        """Only maintained OSIS/native helpers should have live consumers."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "native_milestone_pair_audit": (
                "modules/darby-jnd-2024/tools/probe_private_repaired_darby_sword.py",
                "tests/test_native_milestone_pair_audit.py"),
            "native_sword_markup_census": (
                "scripts/research/bible/native_raw_main_text.py",
                "tests/test_native_sword_markup_census.py"),
            "source_native_ordered_body": (
                "scripts/publisher_osis_sword_candidate.py",
                "tests/test_source_native_ordered_body.py"),
            "source_native_note_positions": (
                "scripts/publisher_osis_sword_candidate.py",
                "tests/test_source_native_note_positions.py"),
            "source_osis_verse_notes": (
                "scripts/publisher_osis_sword_candidate.py",
                "tests/test_source_osis_verse_notes.py"),
        }
        for stem, callers in helpers.items():
            with self.subTest(helper=stem):
                path = "scripts/research/bible/" + stem + ".py"
                self.assertIn(path, entries)
                self.assertTrue(entries[path]["has_direct_tests_by_filename"])
                for caller in callers:
                    self.assertIn(caller, entries[path]["static_references"])


    def test_private_transport_and_reader_probes_are_packaged(self):
        """Do not present imported diagnostic functions as separate CLIs."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "commentary_bookcode_repair_receipt_guard": (
                ".github/workflows/commentary-private-text-compare.yml",
                "tests/test_commentary_bookcode_repair_receipt_guard.py"),
            "commentary_osis_paragraph_presence": (
                ".github/workflows/commentary-mhc-source-text.yml",
                "tests/test_commentary_osis_paragraph_presence.py"),
            "commentary_osis_transport_probe": (
                "scripts/commentary_osis_mixed_transport_probe.py",
                "tests/test_commentary_osis_transport_probe.py"),
            "commentary_xiphos_heading_probe": (
                ".github/workflows/commentary-mhc-technical-rebuild.yml",
                ".github/workflows/commentary-modern-source-receipt.yml",
                "tests/test_commentary_xiphos_heading_probe.py"),
        }
        for name, callers in helpers.items():
            with self.subTest(name=name):
                root_file = f"scripts/{name}.py"
                packaged = f"scripts/research/commentary/{name}.py"
                self.assertNotIn(root_file, entries)
                self.assertFalse((ROOT / root_file).exists())
                self.assertIn(packaged, entries)
                self.assertTrue((ROOT / packaged).is_file())
                self.assertTrue(entries[packaged]["has_direct_tests_by_filename"])
                for caller in callers:
                    self.assertIn(caller, entries[packaged]["static_references"])

    def test_source_authenticity_and_editorial_preflights_are_libraries(self):
        """Six conservative original/source checks are import-only and tested."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "commentary_reference_registry_triage": (
                "scripts/commentary_anchor_parity.py",
                "tests/test_commentary_reference_registry_triage.py"),
            "commentary_original_bookcode_repair": (
                "scripts/commentary_private_text_compare.py",
                "tests/test_commentary_original_bookcode_repair.py"),
            "commentary_source_english_osis_alias": (
                "scripts/research/commentary/commentary_source_identity_lexical_gate.py",
                "tests/test_commentary_source_english_osis_alias.py"),
        }
        for name, callers in helpers.items():
            with self.subTest(name=name):
                old = f"scripts/{name}.py"
                packaged = f"scripts/research/commentary/{name}.py"
                self.assertNotIn(old, entries)
                self.assertFalse((ROOT / old).exists())
                self.assertIn(packaged, entries)
                self.assertTrue((ROOT / packaged).is_file())
                self.assertTrue(entries[packaged]["has_direct_tests_by_filename"])
                for caller in callers:
                    self.assertIn(caller, entries[packaged]["static_references"])

    def test_commentary_census_and_topology_helpers_are_packaged(self):
        """Six independently useful non-CLI helpers retain real consumers."""
        entries = {row["path"]: row for row in self.result["files"]}
        helpers = {
            "commentary_original_div1_book_consistency": (
                "scripts/commentary_private_text_compare.py",
                "tests/test_commentary_original_div1_book_consistency.py"),
            "commentary_stock_prefix_topology": (
                "scripts/commentary_private_text_compare.py",
                "tests/test_commentary_stock_prefix_topology.py"),
            "commentary_shared_raw_source_units": (
                "scripts/commentary_private_text_compare.py",
                "tests/test_commentary_shared_raw_source_units.py"),
            "commentary_source_native_boundaries": (
                "scripts/commentary_private_text_compare.py",
                ".github/workflows/commentary-mhc-source-text.yml",
                "tests/test_commentary_source_native_boundaries.py"),
            "commentary_navigation_link_plan": (
                "scripts/commentary_anchor_parity.py",
                "tests/test_commentary_navigation_link_plan.py"),
        }
        for name, callers in helpers.items():
            with self.subTest(name=name):
                root_path = f"scripts/{name}.py"
                packaged_path = f"scripts/research/commentary/{name}.py"
                self.assertNotIn(root_path, entries)
                self.assertFalse((ROOT / root_path).exists())
                self.assertIn(packaged_path, entries)
                self.assertTrue((ROOT / packaged_path).is_file())
                self.assertTrue(entries[packaged_path]["has_direct_tests_by_filename"])
                for caller in callers:
                    self.assertIn(caller, entries[packaged_path]["static_references"])

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
                 "scripts/research/commentary/commentary_shared_raw_source_units.py",
                 "tests/test_commentary_prose_cross_slot.py"),
            "commentary_unresolved_lexical_triage":
                ("scripts/commentary_private_text_compare.py",
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
