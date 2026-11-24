"""Regression tests for a source-pinned, strictly redundant paragraph edit."""
import sys
from pathlib import Path
from hashlib import sha256
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from remove_reviewed_empty_osis_paragraphs import clean, inspect_empty_paragraphs

SOURCE = (b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
          b'<osisText><div type="book" osisID="Gen"><title type="parallel">Parallel</title>'
          b'\n<p> \n</p>\n<p><verse osisID="Gen.1.1">Text.</verse></p>'
          b'</div></osisText></osis>')


class EmptyParagraphTests(unittest.TestCase):
    def test_detector_reports_bare_empty_nodes_independently_of_removal_context(self):
        data = SOURCE.replace(b'type="parallel"', b'type="section"')
        self.assertEqual(inspect_empty_paragraphs(data)["bare_empty_paragraph_count"], 1)
        data = data.replace(b'<p> \n</p>', b'<p><note>Note</note></p><p type="x-spacer"/>')
        self.assertEqual(inspect_empty_paragraphs(data)["bare_empty_paragraph_count"], 0)

    def test_exact_reversible_markup_only_edit(self):
        result, receipt = clean(SOURCE, sha256(SOURCE).hexdigest(), ["Gen.1.1"])
        self.assertEqual(result, SOURCE.replace(b'<p> \n</p>', b' \n'))
        self.assertTrue(receipt["exact_inverse_verified"])

    def test_reject_wrong_hash_or_reference(self):
        for digest, refs in [("0"*64, ["Gen.1.1"]), (sha256(SOURCE).hexdigest(), ["Gen.1.2"])]:
            with self.assertRaises(ValueError):
                clean(SOURCE, digest, refs)

    def test_reject_annotations_attributes_foreign_and_nonempty_elements(self):
        for markup in (b'<p><note>Note</note></p>', b'<p type="x-spacer"/>',
                       b'<p>Meaning</p>', b'<p><title>Heading</title></p>',
                       b'<p><verse osisID="Gen.1.2"/></p>', b'<p xmlns="urn:foreign"/>',
                       b'<p><!--meaningful comment--></p>'):
            data = SOURCE.replace(b'<p> \n</p>', markup)
            with self.subTest(markup=markup), self.assertRaises(ValueError):
                clean(data, sha256(data).hexdigest(), ["Gen.1.1"])

    def test_reject_ambiguous_context_and_comment_lexical_hit(self):
        for data in (SOURCE.replace(b'type="parallel"', b'type="section"'),
                     SOURCE.replace(b'<p> \n</p>', b'<!--<p/>--><p> \n</p>'),
                     SOURCE.replace(b'<p> \n</p>', b'<p> \n</p>visible')):
            with self.subTest(), self.assertRaises(ValueError):
                clean(data, sha256(data).hexdigest(), ["Gen.1.1"])
