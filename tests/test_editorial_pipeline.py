"""Offline, non-publication fixtures: editorial audit and approved OSIS edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_osis import audit_osis
from normalize_osis import (
    apply_plan, checksum, element_address, element_hash, EditorialError
)
from test_guard_osis import NAMESPACE, TEST_ONLY_SCHEMA
from guard_osis import StructureFailure
from test_commentary_gate import CommentaryGateTests

NS = "{" + NAMESPACE + "}"


class EditorialPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "original.xml"
        self.output = self.root / "normalized.xml"
        self.plan_path = self.root / "plan.json"
        self.schema = self.root / "fixture.xsd"
        self.schema.write_bytes(TEST_ONLY_SCHEMA)
        policy = json.loads((ROOT / "config/osis-policy.json").read_text())
        policy["schema_status"] = "reviewed"  # synthetic unit-test schema only
        policy["schema_sha256"] = checksum(TEST_ONLY_SCHEMA)
        policy["schema_dependencies"] = []
        self.policy = self.root / "test-policy.json"
        self.policy.write_text(json.dumps(policy))
        self.commentary_policy = ROOT / "config/commentary-policy.json"

    def write(self, fragment: str, *, kind="bible"):
        if kind == "bible":
            xml = f'<osis xmlns="{NAMESPACE}"><osisText><div type="book" osisID="Gen"><chapter osisID="Gen.1">{fragment}</chapter></div></osisText></osis>'
        else:
            xml = f'<osis xmlns="{NAMESPACE}"><osisText><div type="book" osisID="Gen"><div type="section" annotateType="commentary" annotateRef="Gen.1.1">{fragment}</div></div></osisText></osis>'
        self.source.write_text(xml, encoding="utf-8")

    def plan(self, edit, *, kind="bible", edition="reader_optimized",
             derivatives=True, approved=True):
        source = self.source.read_bytes()
        value = {
            "schema_version": 1, "kind": kind,
            "source_sha256": checksum(source),
            "approved_for_structural_edits": approved,
            "edition": edition,
            "review": {"reviewed_by": "Test reviewer",
                       "evidence_url": "https://www.ebible.org/fraLSG/PSA023.htm",
                       "decision": "Restore paragraphs based on edition comparison."},
            "rights": {"redistribution_allowed": True,
                       "derivatives_allowed": derivatives,
                       "evidence_url": "https://www.ebible.org/details.php?id=fraLSG"},
            "edits": [edit],
        }
        self.plan_path.write_text(json.dumps(value), encoding="utf-8")
        return value

    def p(self, nth=0):
        doc = etree.parse(str(self.source))
        return doc.findall(".//" + NS + "p")[nth]

    def run_plan(self, *, kind="bible", diff=None):
        return apply_plan(self.source, self.plan_path, self.output,
                          schema_path=self.schema, kind=kind,
                          osis_policy=self.policy, commentary_policy=self.commentary_policy,
                          diff_path=diff)

    def test_bible_split_preserves_all_text_verse_ids_and_original(self):
        self.write('<verse osisID="Gen.1.1" sID="v1"/><p>First sentence. Second sentence.</p><verse eID="v1"/>')
        node = self.p()
        edit = {
            "operation": "split_paragraph",
            "node_path": element_address(node),
            "expected_element_sha256": element_hash(node),
            "right_starts_with": "Second sentence.",
            "reason": "Printed edition shows two adjacent paragraphs.",
            "source_reference": "Gen.1.1",
        }
        self.plan(edit)
        original = self.source.read_bytes()
        report = self.run_plan(diff=self.root/"private.diff")
        self.assertEqual(report["status"], "structural_edit_verified_not_published")
        self.assertTrue(report["full_text_exactly_preserved"])
        self.assertTrue(report["inline_semantic_tags_preserved"])
        self.assertEqual(report["source_sha256"], checksum(original))
        self.assertFalse(report["approved_for_publication"])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(len(etree.parse(str(self.output)).findall(".//"+NS+"p")), 2)
        self.assertEqual(etree.parse(str(self.output)).find(".//"+NS+"verse").get("osisID"), "Gen.1.1")
        self.assertIn("Second sentence", (self.root/"private.diff").read_text())

    def test_group_poetry_lines_preserves_original_text_and_stanza_tails(self):
        self.write('<p>Cantique de David.</p>\n<p>La première ligne.</p>\n<p>La seconde ligne.</p>\n')
        first, second = self.p(1), self.p(2)
        encoded = b"\0".join(etree.tostring(node, encoding="UTF-8", with_tail=False)
                             for node in (first, second))
        edit = {"operation":"group_poetry_lines",
                "node_paths":[element_address(first), element_address(second)],
                "expected_element_sha256": checksum(encoded),
                "reason":"Verse contains two poetic lines in reference edition.",
                "source_reference":"Ps.23.1"}
        self.plan(edit)
        result = self.run_plan()
        self.assertTrue(result["full_text_exactly_preserved"])
        doc = etree.parse(str(self.output))
        self.assertEqual([n.text for n in doc.findall(".//"+NS+"l")],
                         ["La première ligne.", "La seconde ligne."])
        self.assertEqual(len(doc.findall(".//"+NS+"lg")),1)
        self.assertEqual(len(doc.findall(".//"+NS+"p")),1)

    def test_commentary_split_preserves_annotation_and_embedded_quote(self):
        self.write('<p>Matthew Henry explains at length. The second point follows.</p><p><q>Bible quote</q> is explained here.</p>',
                   kind="commentary")
        p = self.p(0)
        edit = {"operation":"split_paragraph",
                "node_path": element_address(p),
                "expected_element_sha256": element_hash(p),
                "right_starts_with":"The second point",
                "reason":"Faithfully restore a verified paragraph division.",
                "source_reference":"Gen.1.1"}
        self.plan(edit,kind="commentary", edition="faithful", derivatives=False)
        result = self.run_plan(kind="commentary")
        self.assertTrue(result["full_text_exactly_preserved"])
        self.assertEqual(len(etree.parse(str(self.output)).findall(".//"+NS+"q")),1)

    def test_stale_source_hash_blocks_and_preserves_output(self):
        self.write('<p>Alpha. Beta.</p>')
        p = self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"Beta.",
                   "reason":"An edition proves distinct paragraphs.","source_reference":"Gen.1.1"})
        self.source.write_text(self.source.read_text().replace("Alpha.", "Different."))
        with self.assertRaisesRegex(EditorialError, "Stale source"):
            self.run_plan()
        self.assertFalse(self.output.exists())

    def test_no_editor_approval_blocks_without_modification(self):
        self.write('<p>Alpha. Beta.</p>')
        p=self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"Beta.",
                   "reason":"Verified paragraph division in printed edition.",
                   "source_reference":"Gen.1.1"},approved=False)
        with self.assertRaisesRegex(EditorialError,"approval"):
            self.run_plan()
        self.assertFalse(self.output.exists())

    def test_reader_optimized_derivative_rights_required(self):
        self.write('<p>Alpha. Beta.</p>')
        p=self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"Beta.",
                   "reason":"Verified paragraph division in printed edition.",
                   "source_reference":"Gen.1.1"},derivatives=False)
        with self.assertRaisesRegex(EditorialError,"derivative rights"):
            self.run_plan()

    def test_inline_marked_paragraph_cannot_be_split_casually(self):
        self.write('<p>First <hi type="italic">emphasis</hi> second part.</p>')
        p=self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"First",
                   "reason":"Some edition marked a paragraph boundary.",
                   "source_reference":"Gen.1.1"})
        with self.assertRaisesRegex(EditorialError,"plain unannotated"):
            self.run_plan()

    def test_repeated_marker_requires_explicit_unambiguous_boundary(self):
        self.write('<p>Alpha. Beta. Beta.</p>')
        p=self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"Beta.",
                   "reason":"Printed paragraph split at particular sentence.",
                   "source_reference":"Gen.1.1"})
        with self.assertRaisesRegex(EditorialError,"exactly once"):
            self.run_plan()

    def test_existing_output_is_never_overwritten(self):
        self.write('<p>Alpha. Beta.</p>')
        p=self.p()
        self.plan({"operation":"split_paragraph","node_path":element_address(p),
                   "expected_element_sha256":element_hash(p),
                   "right_starts_with":"Beta.",
                   "reason":"Printed paragraph split at particular sentence.",
                   "source_reference":"Gen.1.1"})
        self.output.write_bytes(b"existing")
        with self.assertRaisesRegex(EditorialError,"never source or existing"):
            self.run_plan()
        self.assertEqual(self.output.read_bytes(),b"existing")

    def test_audit_typography_reference_and_duplicate_keys_is_read_only(self):
        self.write('<verse osisID="Gen.1.1"/><verse osisID="Gen.1.1"/>'
                   + '<p>'+("ABC " * 30)+'</p>'
                   + '<hi type="bold">'+("emphasis " * 21)+'</hi>'
                   + '<p><reference>empty</reference></p>'
                   + '<p>'+("long prose "*200)+'</p>')
        original=self.source.read_bytes()
        result=audit_osis(self.source,kind="bible")
        codes={f["code"] for f in result["findings"]}
        self.assertTrue({"duplicate_verse_id","upper_case_paragraph",
                         "long_bold_range","invalid_cross_reference",
                         "excessive_styling"}.issubset(codes))
        self.assertEqual(result["source_sha256"],checksum(original))
        self.assertFalse(result["source_schema_validated"])
        self.assertEqual(original,self.source.read_bytes())

    def test_audit_commentary_does_not_delete_numbered_bible_quotes(self):
        lines=" ".join(f"{v} Some verse words follow." for v in range(1,8))
        self.write('<seg type="font-size: +1;">'+lines*3+'</seg>',
                   kind="commentary")
        original=self.source.read_bytes()
        report=audit_osis(self.source,kind="commentary")
        codes={entry["code"] for entry in report["findings"]}
        self.assertIn("introductory_scripture_candidate",codes)
        self.assertIn("unknown_style",codes)
        self.assertEqual(self.source.read_bytes(),original)


if __name__ == "__main__":
    unittest.main()
