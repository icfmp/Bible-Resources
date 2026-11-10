"""Guard the seven-stage process and issue tracker from accidental drift.

These tests certify only workflow documentation/template consistency, not
Scripture fidelity or completion of an actual resource stage.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BibleOnboardingWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = (ROOT / "docs/BIBLE_7_STAGE_WORKFLOW.md").read_text(encoding="utf-8")
        cls.issue = (ROOT / ".github/ISSUE_TEMPLATE/import.yml").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_exactly_seven_documented_gates_and_issue_checkboxes(self):
        guide_stages = [
            int(x) for x in re.findall(
                r"^\| \*\*(\d)/7\*\* \|", self.guide, flags=re.MULTILINE
            )
        ]
        form_stages = [
            int(x) for x in re.findall(
                r"^\s+- \[ \] (\d)/7 ", self.issue, flags=re.MULTILINE
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

    def test_hard_fail_gates_and_checkpoint_evidence_are_documented(self):
        for term in (
            "BLOCKED", "SHA-256", "USFM/USFX", "SWORD",
            "notes", "cross-reference", "verse-zero", "approval",
            "PR/commit", "actual", "7/7", "do not",
        ):
            with self.subTest(term=term):
                self.assertIn(term.lower(), self.guide.lower())

    def test_public_readme_points_to_the_same_single_workflow(self):
        self.assertIn("docs/BIBLE_7_STAGE_WORKFLOW.md", self.readme)
        self.assertIn(".github/ISSUE_TEMPLATE/import.yml", self.readme)


if __name__ == "__main__":
    unittest.main()
