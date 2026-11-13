"""No-network, synthetic safety tests for independent AndBible stable JSword."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_andbible_jsword import _junit_result, _live_samples, _original_native_link_witnesses
from pilot_preflight import PilotError


class CommentaryAndBibleJSwordTests(unittest.TestCase):
    def test_accepts_only_four_complete_java_engine_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "TEST.xml"
            p.write_text('<testsuite tests="4" errors="0" failures="0" skipped="0"/>',
                         encoding="utf-8")
            self.assertEqual(
                _junit_result(p, exit_code=0),
                {"tests": 4, "errors": 0, "failures": 0, "skipped": 0},
            )
            for content, code in [
                ('<testsuite tests="4" errors="0" failures="1" skipped="0"/>', 0),
                ('<testsuite tests="2" errors="0" failures="0" skipped="0"/>', 0),
                ('<testsuite tests="4" errors="0" failures="0" skipped="1"/>', 0),
                ('<testsuite tests="4" errors="0" failures="0" skipped="0"/>', 1),
                ('<testsuite tests="three" errors="0" failures="0"/>', 0),
                ('<testsuite tests="4" errors="0" failures="0"/>', 1),
                ('<anything tests="3" errors="0" failures="0"/>', 0),
            ]:
                p.write_text(content, encoding="utf-8")
                with self.assertRaises(PilotError):
                    _junit_result(p, exit_code=code)

    def test_missing_junit_or_oversized_xml_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "missing.xml"
            with self.assertRaises(PilotError):
                _junit_result(p, exit_code=0)
            p.write_text("x" * 501_000, encoding="utf-8")
            with self.assertRaises(PilotError):
                _junit_result(p, exit_code=0)

    @patch("commentary_andbible_jsword._exact_native_commentary_raw")
    @patch("commentary_andbible_jsword._original_stock_reference_bearing_samples")
    def test_authentic_source_ref_witnesses_keep_exact_duplicate_targets(
        self, inventory, reader,
    ):
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as tmp:
            full = Path(tmp) / "full"
            key = Path(tmp) / "key"
            full.write_text("compiled native scanner")
            key.write_text("compiled native single key")
            inventory.return_value = {
                "real_reference_bearing_original_native_samples": [
                    "Gen 1:3", "Exod 2:1",
                ]
            }
            reader.side_effect = [
                b'<reference osisRef="Ps.23.1">Original link</reference>'
                b'<reference osisRef="Ps.23.1">Repeated reference</reference>',
                b'<reference osisRef="Matt.5.3">Another link</reference>',
            ]
            witnesses, count = _original_native_link_witnesses(
                Path(tmp), "MHCC", full, key,
                expected_raw_sha256="a" * 64,
            )
        first = sha256(b"Ps.23.1").hexdigest()
        second = sha256(b"Matt.5.3").hexdigest()
        self.assertEqual(witnesses, [
            "Gen 1:3|" + first + "," + first,
            "Exod 2:1|" + second,
        ])
        self.assertEqual(count, 3)

    @patch("commentary_andbible_jsword.present_key", return_value=True)
    @patch("commentary_andbible_jsword.query")
    def test_sample_filter_excludes_only_very_short_reader_labels(self, query, _present):
        query.side_effect = [
            (0, b"Genuine source passage." * 30),
            (0, b"Not an occupied source key"),
            (0, b"Another real authorial commentary paragraph." * 4),
        ]
        refs, digests = _live_samples(
            {"module_id": "MHCC", "sample_references":
                ["Gen 1:1", "John 3:16", "Rev 22:21"]},
            Path("/nonexistent/only-mocked"), reader="diatheke",
        )
        self.assertEqual(refs, ["Gen 1:1", "Rev 22:21"])
        self.assertEqual(len(digests), 2)
        self.assertTrue(all(len(x) == 64 for x in digests))
        self.assertEqual(query.call_count, 3)

    @patch("commentary_andbible_jsword.present_key", return_value=True)
    @patch("commentary_andbible_jsword.query", return_value=(0, b"empty"))
    def test_refuses_samples_that_only_contain_key_labels(self, _query, _present):
        with self.assertRaisesRegex(PilotError, "Insufficient"):
            _live_samples(
                {"module_id": "MHCC", "sample_references": ["Gen 1:1", "John 3:16"]},
                Path("/nonexistent/only-mocked"), reader="diatheke",
            )

    @patch("commentary_andbible_jsword.query", return_value=(1, b"not available"))
    def test_a_failed_real_reader_probe_is_not_ignored(self, _query):
        with self.assertRaisesRegex(PilotError, "unreadable"):
            _live_samples(
                {"module_id": "MHCC", "sample_references": ["Gen 1:1", "Rev 22:21"]},
                Path("/nonexistent/only-mocked"), reader="diatheke",
            )


if __name__ == "__main__":
    unittest.main()
