"""Fail-closed CrossWire OSIS commentary tests; no real copyrighted text."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from guard_osis import StructureFailure
from guard_commentary import inspect_commentary, main as commentary_main
from validate import source_gate_errors
from test_guard_osis import NAMESPACE, TEST_ONLY_SCHEMA


class CommentaryGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "commentary.osis.xml"
        self.schema = self.root / "synthetic-ONLY-for-unit-tests.xsd"
        self.schema.write_bytes(TEST_ONLY_SCHEMA)
        self.osis_policy = self.root / "osis-policy.json"
        osis = json.loads((ROOT / "config/osis-policy.json").read_text(encoding="utf-8"))
        osis["schema_status"] = "reviewed"  # Only a synthetic unit-test schema
        osis["schema_sha256"] = hashlib.sha256(TEST_ONLY_SCHEMA).hexdigest()
        osis["schema_dependencies"] = []  # Synthetic fixture has no imports
        self.osis_policy.write_text(json.dumps(osis), encoding="utf-8")
        self.commentary_policy = self.root / "commentary-policy.json"
        self.commentary_policy.write_bytes((ROOT / "config/commentary-policy.json").read_bytes())

    def write(self, lines):
        self.source.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def base(self, annotated_div):
        self.write([
            f'<osis xmlns="{NAMESPACE}">',
            ' <osisText osisIDWork="TestCom" osisRefWork="Commentary">',
            '  <div type="bookGroup">',
            '   <div type="book" osisID="Gen">',
            *annotated_div,
            '   </div>',
            '  </div>',
            ' </osisText>',
            '</osis>',
        ])

    def validate(self):
        return inspect_commentary(self.source, self.schema, self.osis_policy,
                                  self.commentary_policy)

    def assert_failure(self, code, line):
        with self.assertRaises(StructureFailure) as exc:
            self.validate()
        self.assertEqual(exc.exception.code, code)
        self.assertEqual(exc.exception.line, line)
        self.assertIn(str(self.source), str(exc.exception))

    def test_annotated_commentary_preserves_embedded_scripture_and_emphasis(self):
        self.base([
            '    <div type="section" annotateType="commentary" annotateRef="Gen.1.1">',
            '      <title>A deliberately bold heading</title>',
            '      <p>Here is a <q>long scriptural quotation</q> whose author later discusses its <hi type="bold">meaning</hi>.</p>',
            '      <p>See also <reference osisRef="Gen.1.2">Genesis 1:2</reference>.</p>',
            '    </div>',
        ])
        original = self.source.read_bytes()
        result = self.validate()
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["source_kind"], "commentary")
        self.assertEqual(result["annotation_count"], 1)
        self.assertTrue(result["no_transformation_performed"])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(result["source_sha256"], hashlib.sha256(original).hexdigest())

    def test_cross_chapter_range(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1-Gen.2.3"><p>On two chapters</p></div>'])
        self.assertEqual(self.validate()["annotation_count"], 1)

    def test_discontinuous_reference_list(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1 Gen.1.5"><p>Two passages</p></div>'])
        self.assertEqual(self.validate()["annotation_counts"]["reference_groups"], 2)

    def test_book_and_chapter_introductions_need_no_guessed_verse(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1"><p>Chapter overview</p></div>'])
        self.assertEqual(self.validate()["annotation_count"], 1)

    def test_unbound_structure_is_not_reassigned(self):
        self.base(['    <div type="section"><p>Missing annotation</p></div>'])
        self.assert_failure("COMMENTARY_NO_ENTRIES", 1)

    def test_missing_target_is_blocked_at_annotation(self):
        self.base(['    <div type="section" annotateType="commentary"><p>Some commentary</p></div>'])
        self.assert_failure("COMMENTARY_REFERENCE_MISSING", 5)

    def test_annotate_ref_without_type_is_not_inferred(self):
        self.base(['    <div type="section" annotateRef="Gen.1.1"><p>Some commentary</p></div>'])
        self.assert_failure("COMMENTARY_ANNOTATION_TYPE", 5)

    def test_unexpected_annotation_type_is_not_guessed(self):
        self.base(['    <div type="section" annotateType="other" annotateRef="Gen.1.1"><p>Some commentary</p></div>'])
        self.assert_failure("COMMENTARY_ANNOTATION_TYPE", 5)

    def test_work_prefix_is_rejected(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Bible:Gen.1.1"><p>Text</p></div>'])
        self.assert_failure("COMMENTARY_WORK_PREFIX", 5)

    def test_reversed_range_is_rejected(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.2.3-Gen.1.1"><p>Text</p></div>'])
        self.assert_failure("COMMENTARY_REVERSED_RANGE", 5)

    def test_cross_book_range_does_not_guess_canon_order(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1-Exod.1.1"><p>Text</p></div>'])
        self.assert_failure("COMMENTARY_CROSS_BOOK_RANGE_UNREVIEWED", 5)

    def test_reference_with_unreviewed_syntax_stops(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1@special"><p>Text</p></div>'])
        self.assert_failure("COMMENTARY_REFERENCE_UNREVIEWED", 5)

    def test_unsupported_nested_markup_stops_in_shared_guard(self):
        self.base([
            '    <div type="section" annotateType="commentary" annotateRef="Gen.1.1">',
            '      <custom>Unknown format</custom>',
            '    </div>',
        ])
        self.assert_failure("UNREVIEWED_ELEMENT", 6)

    def test_blocked_report_replaces_stale_success(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.4.1-Gen.3.1"><p>Text</p></div>'])
        report = self.root / "SOURCE_VALIDATION.json"
        report.write_text('{"status":"validated"}', encoding="utf-8")
        code = commentary_main([str(self.source), "--schema", str(self.schema),
                                "--osis-policy", str(self.osis_policy),
                                "--commentary-policy", str(self.commentary_policy),
                                "--report", str(report)])
        self.assertEqual(code, 1)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "blocked")
        self.assertEqual(data["diagnostic"]["line"], 5)

    def test_publish_rejects_generic_osis_report_for_commentary(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1"><p>Text</p></div>'])
        verified = self.validate()
        policy_root = self.root / "config"
        policy_root.mkdir()
        (policy_root / "osis-policy.json").write_bytes(self.osis_policy.read_bytes())
        (policy_root / "commentary-policy.json").write_bytes(self.commentary_policy.read_bytes())
        module = self.root / "modules" / "example"
        module.mkdir(parents=True)
        (module / "SOURCE_VALIDATION.json").write_text(json.dumps({
            **verified, "source_kind": "bible"
        }), encoding="utf-8")
        issues = source_gate_errors(module, "OSIS", self.root, "commentary")
        self.assertTrue(any("COMMENTARY_PROOF_MISSING" in issue for issue in issues))

    def test_publish_requires_fresh_commentary_policy(self):
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1"><p>Text</p></div>'])
        verified = self.validate()
        policy_root = self.root / "config"
        policy_root.mkdir()
        (policy_root / "osis-policy.json").write_bytes(self.osis_policy.read_bytes())
        (policy_root / "commentary-policy.json").write_bytes(self.commentary_policy.read_bytes())
        module = self.root / "modules" / "example"
        module.mkdir(parents=True)
        (module / "SOURCE_VALIDATION.json").write_text(json.dumps(verified), encoding="utf-8")
        self.assertEqual(source_gate_errors(module, "OSIS", self.root, "commentary"), [])
        verified["commentary_policy_sha256"] = "0" * 64
        (module / "SOURCE_VALIDATION.json").write_text(json.dumps(verified), encoding="utf-8")
        issues = source_gate_errors(module, "OSIS", self.root, "commentary")
        self.assertTrue(any("COMMENTARY_PROOF_STALE" in issue for issue in issues))

    def test_unpinned_official_schema_remains_blocked(self):
        policy = json.loads(self.osis_policy.read_text(encoding="utf-8"))
        policy["schema_sha256"] = None
        self.osis_policy.write_text(json.dumps(policy), encoding="utf-8")
        self.base(['    <div type="section" annotateType="commentary" annotateRef="Gen.1.1"><p>Text</p></div>'])
        with self.assertRaises(StructureFailure) as exc:
            self.validate()
        self.assertEqual(exc.exception.code, "UNPINNED_SCHEMA")


if __name__ == "__main__":
    unittest.main()
