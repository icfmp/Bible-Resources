"""Synthetic explicit OSIS reference target parity tests; no Bible content."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lsg_stock_reference_parity import compare_compiled_explicit_reference_targets
from pilot_preflight import PilotError


class CompiledReferenceValueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.osis = Path(self.temporary.name) / "source.osis.xml"
        self.osis.write_text('''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
 <osisText>
 <div type="book" osisID="Gen"><chapter sID="Gen.1"/>
 <verse sID="Gen.1.1"/><reference osisRef="Gen.2.1">a</reference>
 <reference>b</reference><verse eID="Gen.1.1"/></div>
 <div type="book" osisID="Exod"><chapter sID="Exod.1"/>
 <verse sID="Exod.1.1"/><reference osisRef="Exod.3.2">c</reference>
 <verse eID="Exod.1.1"/></div>
 </osisText></osis>''', encoding="utf-8")
        self.rows = ["Gen\tGen.2.1", "Gen\t", "Exod\tExod.3.2"]

    def test_exact_explicit_values_and_empty_targets(self):
        report=compare_compiled_explicit_reference_targets(self.osis, self.rows)
        self.assertEqual(report["status"],
                         "compiled_ordered_explicit_osisref_values_verified")
        self.assertEqual(report["books_with_exact_ordered_osisref_values"],2)
        self.assertEqual(report["source_reference_tags"],3)
        self.assertEqual(report["compiled_reference_tags"],3)
        self.assertEqual(report["source_explicit_machine_target_values"],2)
        self.assertFalse(report["human_reference_target_accuracy_verified"])

    def test_changed_target_blocks_without_exporting_references(self):
        changed=list(self.rows)
        changed[0]="Gen\tGen.9.9"
        report=compare_compiled_explicit_reference_targets(self.osis,changed)
        self.assertEqual(report["status"],"blocked_compiled_explicit_osisref_mismatch")
        self.assertEqual(report["first_differing_books"][0]
                         ["first_different_reference_position"],1)
        self.assertNotIn("Gen.9.9",str(report))

    def test_loss_and_reordering_both_block(self):
        for changed in (
            ["Gen\tGen.2.1","Exod\tExod.3.2"],
            ["Gen\t","Gen\tGen.2.1","Exod\tExod.3.2"],
        ):
            with self.subTest(changed=changed):
                report=compare_compiled_explicit_reference_targets(self.osis,changed)
                self.assertEqual(report["status"],
                                 "blocked_compiled_explicit_osisref_mismatch")

    def test_xml_entity_is_decoded_once_not_twice(self):
        # The authoritative parsed XML value contains literal "&amp;".
        # The raw compiled attribute must preserve the same XML escaping
        # depth. An incorrectly unescaped raw value must be rejected.
        original=self.osis.read_text(encoding="utf-8")
        self.osis.write_text(
            original.replace('osisRef="Gen.2.1"',
                             'osisRef="Gen.2.1&amp;amp;"'),
            encoding="utf-8")
        expected=["Gen\tGen.2.1&amp;amp;","Gen\t","Exod\tExod.3.2"]
        result=compare_compiled_explicit_reference_targets(self.osis,expected)
        self.assertEqual(result["status"],
                         "compiled_ordered_explicit_osisref_values_verified")
        wrong=["Gen\tGen.2.1&amp;","Gen\t","Exod\tExod.3.2"]
        result=compare_compiled_explicit_reference_targets(self.osis,wrong)
        self.assertEqual(result["status"],
                         "blocked_compiled_explicit_osisref_mismatch")

    def test_bad_rows_fail_closed(self):
        for changed in (
            ["Lev\tGen.2.1"], ["Gen"], ["Gen\tGen.2.1\textra"],
        ):
            with self.subTest(changed=changed),self.assertRaises(PilotError):
                compare_compiled_explicit_reference_targets(self.osis,changed)


if __name__ == "__main__":
    unittest.main()
