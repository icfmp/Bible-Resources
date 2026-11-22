"""Assert that active intake workflows are source-scoped after stock research retirement."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

RETIRED_STOCK_WORKFLOWS = (
    "commentary-zcom-private-candidate.yml",
    "commentary-evidence.yml",
    "commentary-xml-witness.yml",
    "commentary-anchor-parity.yml",
    "commentary-private-text-compare.yml",
    "commentary-xiphos-dual-reader.yml",
    "stage-stock-commentary.yml",
    "commentary-mhc-ccel-private-rebuild.yml",
    "commentary-mhc-private-jsword.yml",
    "commentary-mhc-private-xiphos.yml",
    "commentary-mhc-source-text.yml",
    "commentary-mhc-technical-rebuild.yml",
    "commentary-modern-source-receipt.yml",
)


def _pr_paths(workflow: str) -> tuple[str, ...]:
    path = ROOT / ".github" / "workflows" / workflow
    body = path.read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^  pull_request:\n    paths:\n(.*?)(?=^  workflow_dispatch:)",
        body,
    )
    if section is None:
        raise AssertionError(f"{workflow}: no reviewed pull-request paths")
    items = []
    for line in section.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.fullmatch(r"- '([^']+)'", stripped)
        if match is None:
            raise AssertionError(f"{workflow}: unreviewed path-filter syntax")
        items.append(match.group(1))
    if not items:
        raise AssertionError(f"{workflow}: missing CI path filters")
    return tuple(items)


class ActiveCommentaryCIContract(unittest.TestCase):
    def test_superseded_original_mhcc_stock_workflows_stay_retired(self):
        for workflow in RETIRED_STOCK_WORKFLOWS:
            with self.subTest(workflow=workflow):
                self.assertFalse(
                    (ROOT / ".github/workflows" / workflow).exists(),
                    "The OSIS-first process must not silently revive stock-only research",
                )

    def test_current_source_neutral_intake_selects_modified_manifest(self):
        workflow = "commentary-intake.yml"
        paths = _pr_paths(workflow)
        self.assertIn("config/commentary-intake/**", paths)
        yaml = (ROOT / ".github/workflows" / workflow).read_text(
            encoding="utf-8")
        self.assertIn("Select exactly the modified commentary manifests", yaml)
        self.assertIn("fromJSON(needs.select-source.outputs.resources)", yaml)
        self.assertIn("has_resources=", yaml)
        self.assertIn(
            "if: ${{ needs.select-source.outputs.has_resources == 'true' }}", yaml
        )
        self.assertNotIn('resources = ["mhcc-crosswire"]', yaml)
        self.assertIn("Library-only changes must not select", yaml)


if __name__ == "__main__":
    unittest.main()
