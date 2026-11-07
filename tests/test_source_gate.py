"""Publisher-side regression tests for reviewed source provenance requirements."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate import source_gate_errors, normalization_report_errors


class PublicationGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "config").mkdir()
        self.module = self.root / "modules" / "example"
        self.module.mkdir(parents=True)
        self.policy = {
            "version": 1, "schema_status": "reviewed",
            "schema_sha256": "a" * 64,
            "namespace": "http://www.bibletechnologies.net/2003/OSIS/namespace",
            "supported_elements": ["osis"]
        }
        self.save_policy()
        self.save_proof()

    def save_policy(self):
        (self.root / "config/osis-policy.json").write_text(
            json.dumps(self.policy), encoding="utf-8"
        )

    def save_proof(self):
        digest = hashlib.sha256(
            json.dumps(self.policy, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.report = {
            "status": "validated", "no_transformation_performed": True,
            "schema_sha256": self.policy["schema_sha256"],
            "policy_sha256": digest, "source_sha256": "b" * 64,
        }
        (self.module / "SOURCE_VALIDATION.json").write_text(
            json.dumps(self.report), encoding="utf-8"
        )

    def normalizer_proof(self):
        return {
            "status":"structural_edit_verified_not_published",
            "kind":"bible","edition":"reader_optimized",
            "full_text_exactly_preserved":True,
            "inline_semantic_tags_preserved":True,
            "original_source_unchanged":True,
            "schema_sha256":self.policy["schema_sha256"],
            "source_sha256":"c"*64,
            "output_sha256":self.report["source_sha256"],
            "plan_sha256":"d"*64,
            "diff_sha256":"e"*64,
            "review_asserted_by_plan":"Human reviewer",
            "operations":[{"operation":"split_paragraph", "source_reference":"Gen.1.1"}],
        }

    def test_reader_optimized_publication_requires_editorial_proof(self):
        errors = normalization_report_errors(self.module, "reader_optimized", "bible", self.policy["schema_sha256"])
        self.assertTrue(any("NORMALIZATION_REPORT_MISSING" in e for e in errors))
        path=self.module/"NORMALIZATION_REPORT.json"
        path.write_text(json.dumps(self.normalizer_proof()),encoding="utf-8")
        self.assertEqual(normalization_report_errors(self.module,"reader_optimized","bible",
                                                    self.policy["schema_sha256"]), [])

    def test_reject_normalized_output_not_matching_source_validation(self):
        proof=self.normalizer_proof()
        proof["output_sha256"]="f"*64
        (self.module/"NORMALIZATION_REPORT.json").write_text(json.dumps(proof),encoding="utf-8")
        errors=normalization_report_errors(self.module,"reader_optimized","bible",self.policy["schema_sha256"])
        self.assertTrue(any("NORMALIZATION_OUTPUT_MISMATCH" in e for e in errors))

    def test_unchanged_faithful_source_does_not_require_edit_report(self):
        self.assertEqual(normalization_report_errors(self.module,"faithful","bible",
                                                    self.policy["schema_sha256"]), [])

    def test_valid_osis_provenance_gate(self):
        self.assertEqual(source_gate_errors(self.module, "OSIS", self.root), [])

    def test_unreviewed_schema_blocks_approved_module(self):
        self.policy["schema_status"] = "awaiting_pinned_official_copy"
        self.save_policy()
        issues = source_gate_errors(self.module, "OSIS", self.root)
        self.assertTrue(any("SCHEMA_NOT_REVIEWED" in item for item in issues))

    def test_unexpected_legacy_source_type_blocks(self):
        errors = source_gate_errors(self.module, "ThML", self.root)
        self.assertTrue(any("UNSUPPORTED_SOURCE_FORMAT" in item for item in errors))

    def test_stale_policy_or_schema_blocks(self):
        self.report["schema_sha256"] = "c" * 64
        (self.module / "SOURCE_VALIDATION.json").write_text(json.dumps(self.report), encoding="utf-8")
        errors = source_gate_errors(self.module, "OSIS", self.root)
        self.assertTrue(any("SOURCE_VALIDATION_STALE" in item for item in errors))

    def test_missing_report_blocks(self):
        (self.module / "SOURCE_VALIDATION.json").unlink()
        errors = source_gate_errors(self.module, "OSIS", self.root)
        self.assertTrue(any("SOURCE_VALIDATION_MISSING" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
