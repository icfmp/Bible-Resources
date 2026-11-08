"""No Biblical contents in source-to-SWORD internal markup smoke tests."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_dynamic_sword_trial import summarize_internal_markup


class CompiledInternalMarkupAuditTests(unittest.TestCase):
    def test_tag_names_are_reported_without_original_payload(self):
        payload=(
            b'<w lemma="strong:H1">SECRET_SYNTHETIC_WORD</w>'
            b'<note type="crossReference"><reference>SECRET_SYNTHETIC_NOTE</reference>'
            b'</note><lg><l level="1">SECRET_SYNTHETIC_LINE</l></lg>'
            b'<hi type="italic">SECRET_SYNTHETIC_FORMAT</hi>')
        report=summarize_internal_markup(payload)
        self.assertEqual(report["tag_counts"]["w"],1)
        self.assertEqual(report["tag_counts"]["note"],1)
        self.assertEqual(report["tag_counts"]["reference"],1)
        self.assertEqual(report["tag_counts"]["l"],1)
        self.assertEqual(report["tag_counts"]["lg"],1)
        self.assertEqual(report["tag_counts"]["hi"],1)
        self.assertNotIn("SECRET_SYNTHETIC",repr(report))

    def test_partial_or_escaped_tags_are_not_treated_as_real_tags(self):
        report=summarize_internal_markup(
            b'&lt;note&gt;not a node &lt;/note&gt; <note>ACTUAL_MARKER</note>')
        self.assertEqual(report["tag_counts"]["note"],1)
        self.assertEqual(report["tag_counts"]["w"],0)


if __name__=="__main__":
    unittest.main()
