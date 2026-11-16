"""Invented-only guards for private source-corrected SWORD candidate comparison."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_source_erratum_compiled_probe import (
    _original_citation_endpoints,
    _apply_private_reviewed_prose_changes,
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


    def test_private_prose_change_preserves_linked_source_identity_and_others(self):
        from hashlib import sha256
        source = b"<div/><hi>Verses 1-3</hi> Zebulun or Dn; other words."
        distinct = b"<div/><hi>Verses 4-5</hi> Completely independent text."
        originals = {"1Chr.7": [
            ("1Chr.7.1", source), ("1Chr.7.2", source), ("1Chr.7.3", source),
            ("1Chr.7.4", distinct),
        ]}
        plan = [{
            "original_native_entry": "1Chr.7.1",
            "original_raw_sha256": sha256(source).hexdigest(),
            "expected_original_linked_native_K_count": 3,
            "original_phrase": "Zebulun or Dn",
            "corrected_phrase": "Zebulun or Dan",
        }]
        changed, original_keys, receipts = _apply_private_reviewed_prose_changes(
            originals, originals, plan
        )
        self.assertEqual(sorted(original_keys),
                         ["1Chr.7.1", "1Chr.7.2", "1Chr.7.3"])
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["affected_original_K_count"], 3)
        self.assertEqual(changed["1Chr.7"][0][1],
                         source.replace(b"Zebulun or Dn", b"Zebulun or Dan"))
        self.assertEqual(changed["1Chr.7"][3][1], distinct)
        self.assertEqual(originals["1Chr.7"][0][1], source)
        self.assertTrue(receipts[0]["reverse_restores_exact_original_raw_bytes"])
        self.assertNotIn("Zebulun", str(receipts))

    def test_private_prose_change_fails_on_stale_source_or_repeated_plan(self):
        from hashlib import sha256
        source = b"<div/>Zebulun or Dn"
        original = {"1Chr.7": [("1Chr.7.1", source)]}
        good = {
            "original_native_entry": "1Chr.7.1",
            "original_raw_sha256": sha256(source).hexdigest(),
            "expected_original_linked_native_K_count": 1,
            "original_phrase": "Zebulun or Dn",
            "corrected_phrase": "Zebulun or Dan",
        }
        for override in (
            {"original_raw_sha256": "a"*64},
            {"expected_original_linked_native_K_count": 2},
            {"original_phrase": "Zebulun or Den"},
        ):
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    _apply_private_reviewed_prose_changes(
                        original, original, [{**good, **override}]
                    )
        with self.assertRaises(ValueError):
            _apply_private_reviewed_prose_changes(
                original, original, [good, good]
            )
        with self.assertRaises(ValueError):
            _apply_private_reviewed_prose_changes(
                original, original, [{**good, "original_raw_sha256": None}]
            )

    def test_private_prose_change_rejects_same_source_body_across_chapters(self):
        from hashlib import sha256
        body = b"<div/>Zebulun or Dn"
        originals = {"1Chr.7": [("1Chr.7.1", body)],
                     "1Chr.8": [("1Chr.8.1", body)]}
        with self.assertRaises(ValueError):
            _apply_private_reviewed_prose_changes(
                originals, originals, [{
                    "original_native_entry": "1Chr.7.1",
                    "original_raw_sha256": sha256(body).hexdigest(),
                    "expected_original_linked_native_K_count": 2,
                    "original_phrase": "Zebulun or Dn",
                    "corrected_phrase": "Zebulun or Dan",
                }]
            )


if __name__ == "__main__":
    unittest.main()
