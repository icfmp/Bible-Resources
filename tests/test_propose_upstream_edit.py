"""Offline, text-free upstream correction report test."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from normalize_osis import checksum, EditorialError
from propose_upstream_edit import proposal


class UpstreamProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.plan=self.root/"plan.json"
        self.report=self.root/"report.json"
        self.entry={"operation":"split_paragraph",
                    "reason":"Actual printed edition confirms the paragraph division.",
                    "source_reference":"Gen.1.1"}
        self.doc={"edition":"reader_optimized","kind":"bible",
                  "source_sha256":"a"*64,
                  "review":{"evidence_url":"https://ebible.org/fraLSG/GEN001.htm"},
                  "edits":[self.entry]}
        self.plan.write_text(json.dumps(self.doc))
        self.proof={"status":"structural_edit_verified_not_published",
                    "edition":"reader_optimized","kind":"bible",
                    "source_sha256":"a"*64,
                    "output_sha256":"b"*64,
                    "plan_sha256":checksum(self.plan.read_bytes()),
                    "diff_sha256":"c"*64,
                    "full_text_exactly_preserved":True,
                    "inline_semantic_tags_preserved":True,
                    "original_source_unchanged":True,
                    "operations":[{"operation":"split_paragraph",
                                   "source_reference":"Gen.1.1"}]}
        self.report.write_text(json.dumps(self.proof))

    def test_proposal_contains_citation_and_diff_hash_but_no_text(self):
        rendered=proposal(self.plan,self.report,provider="eBible",
                          module_id="fraLSG1910eb",source_revision="100.0")
        self.assertIn("Gen.1.1",rendered)
        self.assertIn("Original source SHA-256:",rendered)
        self.assertIn("No issue, pull request or release",rendered)
        self.assertNotIn("Full original verse text",rendered)

    def test_mismatching_report_is_blocked(self):
        self.proof["plan_sha256"]="0"*64
        self.report.write_text(json.dumps(self.proof))
        with self.assertRaises(EditorialError):
            proposal(self.plan,self.report,provider="eBible",
                     module_id="fraLSG1910eb",source_revision="100.0")


if __name__=="__main__":
    unittest.main()
