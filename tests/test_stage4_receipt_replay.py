"""No-network replay of SHA/commit-bound stage-4 evidence from trusted artifact."""
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bible_intake import parse_audit_comment, parse_audit_command, IntakeError, load_manifest
from bible_stage_runner import main
from stage4_subcheck_receipts import create_subcheck_receipts

SHA = "c"*40
URL = "https://github.com/icfmp/Bible-Resources/actions/runs/333333333"


class ReplayTests(unittest.TestCase):
    def prior(self, folder):
        manifest=load_manifest("frajnd-2024")
        fidelity={
            "status":"BLOCKED",
            "evidence":{
                "original_archives":{
                    "source":{"sha256":manifest["source"]["sha256"]},
                    "sword":{"sha256":manifest["sword"]["sha256"]},
                },
                "fast_stock_note_preflight":{
                    "fast_stock_reuse_disqualified":True,
                    "independent_exact_native_verse_probes":1,
                    "sampled_exact_source_reference":"Gen.1.2",
                    "original_numbered_note_inventory_count":6340,
                },
                "whole_corpus_scan_performed":False,
            },
        }
        prior=create_subcheck_receipts(
            manifest,fidelity,commit_sha=SHA,run_url=URL)
        path=folder/"stage4-subchecks.json"
        path.write_text(json.dumps(prior),encoding="utf-8")
        return path

    def test_strict_issue_command_requires_reuse_run_only_for_subcheck(self):
        self.assertEqual(parse_audit_command(
            "/bible-audit frajnd-2024 4c 43254961838"),
            ("frajnd-2024","4c",43254961838))
        self.assertEqual(parse_audit_comment(
            "/bible-audit frajnd-2024 4c 43254961838"),
            ("frajnd-2024","4c"))
        self.assertEqual(parse_audit_comment(
            "/bible-audit frajnd-2024 4-5"),
            ("frajnd-2024","4-5"))
        for command in (
            "/bible-audit frajnd-2024 4c",
            "/bible-audit frajnd-2024 4c 0",
            "/bible-audit frajnd-2024 4c 001",
            "/bible-audit frajnd-2024 4 43254961838",
            "/bible-audit frajnd-2024 4a 333333333; cat secret",
            "/bible-audit frajnd-2024 4a 333333333\nSECRET",
            "/bible-audit frajnd-2024 4a 11111111111111111",
        ):
            with self.subTest(command=command),self.assertRaises(IntakeError):
                parse_audit_command(command)

    def test_prior_metadata_replay_never_downloads_or_scans_originals(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)
            prior=self.prior(path)
            folder=path/"report"
            folder.mkdir()
            with (
                patch.dict(os.environ,{"GITHUB_SHA":SHA,
                     "GITHUB_SERVER_URL":"https://github.com",
                     "GITHUB_REPOSITORY":"icfmp/Bible-Resources",
                     "GITHUB_RUN_ID":"444444444"},clear=False),
                patch("bible_stage_runner.acquire",
                      side_effect=AssertionError("Source download prohibited")),
                patch("bible_stage_runner.run_stage",
                      side_effect=AssertionError("Fresh native scan prohibited")),
                patch("bible_stage_runner.run_stage_four_and_five",
                      side_effect=AssertionError("Duplicate 4+5 scan prohibited")),
            ):
                ret=main(["--resource-id","frajnd-2024","--stage","4c",
                          "--prior-receipts",str(prior),
                          "--report-dir",str(folder)])
            self.assertEqual(ret,0)
            data=json.loads((folder/"stage-report.json").read_text())
            self.assertEqual(data["stage"],"4c")
            self.assertFalse(data["gate_completed"])
            self.assertEqual(data["schema_version"],3)
            self.assertEqual(data["status"],"BLOCKED")
            self.assertTrue(data["evidence"]["no_source_download_or_publication"])
            self.assertFalse(data["evidence"]["new_native_scan_completed"])
            self.assertEqual(data["evidence"]["previous_evidence_action_run"],URL)
            self.assertNotIn("scripture",json.dumps(data).lower())
            self.assertIn("replay", (folder/"stage-summary.md").read_text().lower())

    def test_changed_tool_commit_cannot_replay(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp); prior=self.prior(path)
            folder=path/"report";folder.mkdir()
            with (patch.dict(os.environ,{"GITHUB_SHA":"d"*40},clear=False),
                  patch("bible_stage_runner.acquire",
                        side_effect=AssertionError("Source download prohibited"))):
                ret=main(["--resource-id","frajnd-2024","--stage","4c",
                          "--prior-receipts",str(prior),
                          "--report-dir",str(folder)])
            self.assertEqual(ret,1)
            report=json.loads((folder/"stage-report.json").read_text())
            self.assertEqual(report["status"],"BLOCKED")
            self.assertNotIn("Gen.1.2",json.dumps(report))  # fail closed, not leak

    def test_incomplete_cli_replay_or_unsafe_existing_report_rejected(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)
            with self.assertRaises(SystemExit):
                main(["--resource-id","frajnd-2024","--stage","4a",
                      "--report-dir",str(path)])
            with self.assertRaises(SystemExit):
                main(["--resource-id","frajnd-2024","--stage","4-5",
                      "--prior-receipts",str(path/"missing"),
                      "--report-dir",str(path)])


if __name__=="__main__":
    unittest.main()
