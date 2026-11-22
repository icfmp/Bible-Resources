"""Guard source-scoped commentary intake and native audit workflows."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

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
    def test_active_intake_and_raw_workflows_only_select_changed_registered_sources(self):
        """PRs unrelated to reviewed source manifests must not probe stock ZIPs."""
        for workflow, job in (
            ("commentary-intake.yml", "intake"),
            ("commentary-native-raw-corpus.yml", "full_stock_commentary_raw"),
        ):
            with self.subTest(workflow=workflow):
                paths = _pr_paths(workflow)
                self.assertIn("config/commentary-intake/**", paths)
                yaml = (ROOT / ".github/workflows" / workflow).read_text(
                    encoding="utf-8")
                self.assertIn("Select exactly the modified commentary manifests", yaml)
                self.assertIn(
                    "resources = sorted(set(registered[path] for path in changed if path in registered))",
                    yaml,
                )
                self.assertIn("if path in registered", yaml)
                self.assertIn('if data.get("category") == "commentary"', yaml)
                self.assertIn("has_resources=", yaml)
                self.assertIn("fromJSON(needs.select-source.outputs.resources)", yaml)
                self.assertIn(
                    f"{job}:\\n    needs: select-source\\n"
                    "    if: ${{ needs.select-source.outputs.has_resources == 'true' }}".replace(
                        "\\${", "${"),
                    yaml,
                )
                self.assertNotIn('resources = ["mhcc-crosswire"]', yaml)



if __name__ == "__main__":
    unittest.main()
