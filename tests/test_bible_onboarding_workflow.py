"""Guard the canonical Bible intake contract and its seven-stage checklist.

These tests verify navigable entrypoints and evidence-gate consistency, not
authorial fidelity or actual completion of an imported resource.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BibleOnboardingWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = (ROOT / "docs/workflows/BIBLE_7_STAGE_WORKFLOW.md").read_text(
            encoding="utf-8")
        cls.production = (ROOT / "docs/PRODUCTION_PIPELINE.md").read_text(
            encoding="utf-8")
        cls.issue = (ROOT / ".github/ISSUE_TEMPLATE/import.yml").read_text(
            encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.workflows_index = (ROOT / "docs/workflows/README.md").read_text(
            encoding="utf-8")

    def test_exactly_seven_documented_gates_and_issue_checkboxes(self):
        # Table rows in the maintained checklist, not the removed legacy
        # **1/7** markup. Both documents must enumerate 1-7 exactly once.
        guide_stages = [
            int(n) for n in re.findall(
                r"^\|\s*([1-7])\.\s+[^|]+\|",
                self.guide, flags=re.MULTILINE,
            )
        ]
        form_stages = [
            int(n) for n in re.findall(
                r"^\s+- \[ \] (\d)/7 ", self.issue, flags=re.MULTILINE,
            )
        ]
        self.assertEqual(guide_stages, list(range(1, 8)))
        self.assertEqual(form_stages, list(range(1, 8)))

    def test_issue_has_a_single_resumable_progress_record(self):
        for term in (
            "Progress: 0/7 DONE", "Status: IN_PROGRESS",
            "Last verified checkpoint:", "Next action:", "Blocker:",
            "id: checkpoints",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.issue)

    def test_evidence_gates_preserve_the_substantive_contract(self):
        guide = self.guide.lower()
        for term in (
            "do not mark done when", "blocked", "sha-256",
            "redistribution rights", "provenance manifest",
            "native versification", "missing verses", "notes",
            "cross references", "sword", "independent xiphos",
            "owner approval", "public url checked",
            "stage 4 is not stage 5", "never invent an absent verse",
        ):
            with self.subTest(checkpoint=term):
                self.assertIn(term, guide)
        canonical = self.production.lower()
        for term in (
            "single authoritative production process", "usfm/usfx",
            "original", "cleaned", "full native readback",
            "original-source", "required evidence",
        ):
            with self.subTest(canonical=term):
                self.assertIn(term, canonical)
        self.assertIn("(../PRODUCTION_PIPELINE.md)", self.guide)

    def test_public_entrypoints_and_import_template_point_to_current_workflow(self):
        self.assertIn("docs/PRODUCTION_PIPELINE.md", self.readme)
        self.assertIn("docs/workflows/README.md", self.readme)
        self.assertIn("(BIBLE_7_STAGE_WORKFLOW.md)", self.workflows_index)
        self.assertIn(
            "docs/workflows/BIBLE_7_STAGE_WORKFLOW.md", self.issue)
        self.assertIn(
            "(../../.github/ISSUE_TEMPLATE/import.yml)", self.guide)


if __name__ == "__main__":
    unittest.main()
