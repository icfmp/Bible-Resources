"""Keep MHCC-only reader CI from misreporting an unrelated MHC intake PR.

No external YAML parser needed: verify the narrow GitHub Actions path-filter
contract directly, including the continued generic-code and manual triggers.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MHCC_ONLY_WORKFLOWS = (
    "commentary-private-candidate-xiphos-gui.yml",
    "commentary-zcom-private-candidate.yml",
    "commentary-zcom-andbible-android.yml",
    "commentary-zcom-xiphos-private-smoke.yml",
)
ORIGINAL_MANIFEST = "config/commentary-intake/mhcc-crosswire.json"
UNRELATED_MANIFEST = "config/commentary-intake/mhc-crosswire.json"


def _pr_paths(workflow: str) -> tuple[str, ...]:
    path = ROOT / ".github" / "workflows" / workflow
    body = path.read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^  pull_request:\n    paths:\n(.*?)(?=^  workflow_dispatch:)",
        body,
    )
    if section is None:
        raise AssertionError(f"{workflow}: no reviewed pull-request paths")
    # Match all actual path entries, while permitting explanatory comments.
    candidates = [
        line.strip() for line in section.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    items = []
    for line in candidates:
        match = re.fullmatch(r"- '([^']+)'", line)
        if match is None:
            raise AssertionError(f"{workflow}: unreviewed path-filter syntax")
        items.append(match.group(1))
    if not items:
        raise AssertionError(f"{workflow}: missing CI path filters")
    return tuple(items)


class OriginalMhccWorkflowSourceScoping(unittest.TestCase):
    def test_manifest_only_mhc_change_does_not_trigger_original_mhcc_workflows(self):
        for workflow in MHCC_ONLY_WORKFLOWS:
            with self.subTest(workflow=workflow):
                paths = _pr_paths(workflow)
                self.assertIn(ORIGINAL_MANIFEST, paths)
                self.assertFalse(
                    any(fnmatchcase(UNRELATED_MANIFEST, pattern)
                        for pattern in paths),
                    "Unrelated MHC manifest must not invoke stock MHCC-only gates",
                )
                self.assertTrue(
                    any(fnmatchcase(ORIGINAL_MANIFEST, pattern)
                        for pattern in paths),
                    "MHCC manifest edits must still test original MHCC",
                )

    def test_code_change_and_manual_research_remain_supported(self):
        for workflow in MHCC_ONLY_WORKFLOWS:
            with self.subTest(workflow=workflow):
                paths = _pr_paths(workflow)
                self.assertTrue(
                    any(path.startswith("scripts/") for path in paths),
                    "Shared reader implementation changes must still be audited",
                )
                yaml = (ROOT / ".github" / "workflows" / workflow).read_text(
                    encoding="utf-8"
                )
                self.assertIn("  workflow_dispatch:\n", yaml)
                self.assertIn("default: mhcc-crosswire", yaml)

    def test_source_neutral_intake_and_anchor_workflows_select_manifest(self):
        # Unlike MHCC-specific workflows, these already select the modified
        # manifest(s) from the actual PR diff; do not narrow their path scope.
        for workflow in (
            "commentary-intake.yml",
            "commentary-anchor-parity.yml",
        ):
            with self.subTest(workflow=workflow):
                paths = _pr_paths(workflow)
                self.assertIn("config/commentary-intake/**", paths)
                yaml = (ROOT / ".github" / "workflows" / workflow).read_text(
                    encoding="utf-8"
                )
                self.assertIn("Select exactly the modified commentary manifests", yaml)
                self.assertIn("fromJSON(needs.select-source.outputs.resources)", yaml)


if __name__ == "__main__":
    unittest.main()
