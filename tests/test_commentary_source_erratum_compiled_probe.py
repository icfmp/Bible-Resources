"""Invented-only guards for private source-corrected SWORD candidate comparison."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_source_erratum_compiled_probe import (
    _original_citation_endpoints,
)


class SourceErratumCorrectedNativeLinkTests(unittest.TestCase):
    def test_one_exact_corrected_native_link_only(self):
        original = (
            b"<div>Invented exposition "
            b'<reference osisRef="Bible:Gen.1.3-Gen.1.1">'
            b"Gen 1:3-1</reference></div>"
        )
        revised = original.replace(
            b"Gen.1.3-Gen.1.1", b"Gen.1.3-Gen.1.5"
        ).replace(b"Gen 1:3-1", b"Gen 1:3-5")
        self.assertEqual(
            _original_citation_endpoints(original, first="Gen.1.3",
                                         expected_end="Gen.1.5"), 0
        )
        self.assertEqual(
            _original_citation_endpoints(revised, first="Gen.1.3",
                                         expected_end="Gen.1.5"), 1
        )
        self.assertEqual(
            _original_citation_endpoints(revised, first="Gen.1.3",
                                         expected_end="Gen.1.4"), 0
        )
        self.assertEqual(
            _original_citation_endpoints(revised + revised,
                                         first="Gen.1.3",
                                         expected_end="Gen.1.5"), 2
        )

    def test_similar_prefix_and_same_end_on_different_start_are_not_matches(self):
        first = "Gen.1.3"
        end = "Gen.1.5"
        misleading = (
            b'<reference osisRef="Bible:Gen.1.30-Gen.1.5">wrong first</reference>'
            b'<reference osisRef="Bible:Gen.1.4-Gen.1.5">same end</reference>'
            b'<reference osisRef="Gen.1.3-Gen.2.5">same numeral</reference>'
            b'<reference osisRef="Bible:Gen.1.3,Gen.1.5">complex target</reference>'
        )
        self.assertEqual(
            _original_citation_endpoints(misleading, first=first,
                                         expected_end=end), 0)
        self.assertEqual(
            _original_citation_endpoints(
                misleading + b'<reference osisRef="Bible:Gen.1.3-5">valid</reference>',
                first=first, expected_end=end), 1)
        with self.assertRaises(ValueError):
            _original_citation_endpoints(
                misleading, first="Gen.1", expected_end=end)

    def test_bad_xml_and_nonmatching_target_cannot_be_accepted(self):
        with self.assertRaises(ValueError):
            _original_citation_endpoints(
                b"<reference>", first="Gen.1.3", expected_end="Gen.1.5"
            )
        with self.assertRaises(ValueError):
            _original_citation_endpoints(
                b'<!DOCTYPE x [<!ENTITY t SYSTEM "file:///etc/passwd">]>'
                b"<reference>&t;</reference>",
                first="Gen.1.3", expected_end="Gen.1.5"
            )


if __name__ == "__main__":
    unittest.main()
