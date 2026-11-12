"""Offline regression cases for generic commentary source and SWORD inventory."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from commentary_native_inventory import parse_index
from commentary_witness import witness_signals
from pilot_preflight import PilotError


class CommentaryStageEvidenceTests(unittest.TestCase):
    SAMPLE = (
        b"M\tTestCom\tKJV\t1.9.0\tzCom\n"
        b"I\tGen.0.0\n"
        b"K\tGen.1.1\n"
        b"K\tGen.1.2\n"
        b"K\tJohn.3.15\n"
        b"K\tJohn.3.17\n"
        b"S\t31000\t4\t1\t0\n"
    )

    def test_source_witness_fingerprints_all_bytes_without_text_leak(self):
        text = ("Book introduction, authorship and paragraphs.\r\n"
                + ("Some example commentary, no publication intended.\n" * 100)
                + "\nEnd.").encode()
        result = witness_signals(text)
        self.assertEqual(result["source_sha256"], sha256(text).hexdigest())
        self.assertEqual(result["newline_crlf"], 1)
        self.assertGreater(result["nonblank_lines"], 10)
        self.assertFalse(result["original_edition_identity_verified"])
        self.assertFalse(result["source_to_compiled_sword_parity_verified"])
        self.assertNotIn("authorship and paragraphs", json.dumps(result))

    def test_original_source_malformed_encoding_blocks_without_replacement(self):
        with self.assertRaisesRegex(PilotError, "UTF-8"):
            witness_signals(b"A" * 1000 + b"\xff")
        with self.assertRaisesRegex(PilotError, "NUL"):
            witness_signals(b"A" * 1000 + b"\x00")
        with self.assertRaisesRegex(PilotError, "empty"):
            witness_signals(b"short")

    def test_native_entry_key_inventory_is_not_claimed_as_authorial_parity(self):
        result = parse_index(self.SAMPLE, "TestCom")
        self.assertEqual(result["occupied_numbered_slots"], 4)
        self.assertEqual(result["occupied_intro_slots"], 1)
        self.assertEqual(result["books_with_occupied_slots"], 2)
        self.assertFalse(result["probe_john_3_16_native_occupied"])
        self.assertFalse(result["comments_as_passage_ranges_verified"])
        self.assertFalse(result["complete_commentary_entry_count_verified"])
        self.assertFalse(result["source_to_native_text_fidelity_verified"])
        self.assertNotIn("Some example commentary", json.dumps(result))

    def test_native_scan_requires_terminal_totals_and_unique_qualified_slots(self):
        cases = (
            self.SAMPLE.replace(b"S\t31000\t4\t1\t0\n", b""),
            self.SAMPLE.replace(b"S\t31000\t4\t1\t0", b"S\t31000\t5\t1\t0"),
            self.SAMPLE.replace(b"John.3.17", b"John.3.15"),
            self.SAMPLE.replace(b"John.3.17", b"John.3.0"),
            self.SAMPLE.replace(b"zCom", b"zText"),
            self.SAMPLE.replace(b"TestCom", b"OtherCom"),
        )
        for bad in cases:
            with self.subTest(case=bad[-60:]):
                with self.assertRaises(PilotError):
                    parse_index(bad, "TestCom")

    def test_opaque_native_top_records_are_counted_not_conflated(self):
        source = (
            b"M\tTestCom\tKJV\t1.9.0\tzCom\n"
            b"U\tTOP:1\nU\tTOP:2\n"
            b"K\tGen.1.1\n"
            b"S\t31000\t1\t0\t2\n"
        )
        result = parse_index(source, "TestCom")
        self.assertEqual(result["occupied_anonymous_top_slots"], 2)
        self.assertEqual(result["occupied_numbered_slots"], 1)
        with self.assertRaisesRegex(PilotError, "Duplicate"):
            parse_index(source.replace(b"TOP:2", b"TOP:1"), "TestCom")

    def test_native_inventory_deterministic_and_sensitive_to_order(self):
        a = parse_index(self.SAMPLE, "TestCom")
        b = parse_index(self.SAMPLE, "TestCom")
        c = parse_index(self.SAMPLE.replace(b"Gen.1.2", b"Gen.1.3"), "TestCom")
        self.assertEqual(a["ordered_occupied_key_sha256"], b["ordered_occupied_key_sha256"])
        self.assertNotEqual(a["ordered_occupied_key_sha256"], c["ordered_occupied_key_sha256"])


if __name__ == "__main__":
    unittest.main()
