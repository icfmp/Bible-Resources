"""Offline safety and exact-index tests for stock commentary raw corpus scanner."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from commentary_native_raw_inventory import private_crosscheck
from pilot_preflight import PilotError
from sword_native_raw_corpus_inventory import parse_native_raw_corpus,RawCorpusError


class CommentaryRawInventoryTests(unittest.TestCase):
    def index(self):
        return (b"M\tTestCom\tKJV\t1.9.0\tzCom\n"
                b"I\tGen\n"
                b"K\tGen.1.1\n"
                b"K\tGen.1.3\n"
                b"U\tTOP:1\n"
                b"S\t30000\t2\t1\t1\n")

    def stream(self):
        entries=[
            ("I","Gen",b"<p>Unmodified book introduction</p>"),
            ("K","Gen.1.1",b"<p>The original commentary, not for reporting.</p>"),
            ("K","Gen.1.3",b"<p>Another original section with a comma, punctuation!</p>"),
            ("U","TOP:1",b"Opaque intro fragment"),
        ]
        data=b"".join((f"{k}\t{ref}\t{len(raw)}\n".encode("ascii")+raw)
                      for k,ref,raw in entries)
        return data+b"S\t4\t2\t1\t1\n",entries

    def test_every_raw_framed_record_has_full_slot_coverage(self):
        raw,entries=self.stream()
        seen=[]
        parsed,k,intros,top=parse_native_raw_corpus(
            BytesIO(raw),on_entry=lambda kind,ref,value: seen.append((kind,ref,value)))
        self.assertEqual(len(seen),4)
        self.assertEqual(k,["Gen.1.1","Gen.1.3"])
        self.assertEqual(intros,["Gen"])
        self.assertEqual(top,["TOP:1"])
        matched=private_crosscheck(self.index(),"TestCom",
            [(kind,ref) for kind,ref,_ in seen],parsed)
        self.assertTrue(matched["exact_all_occupied_stock_keys_read_and_crosschecked"])
        self.assertEqual(matched["all_stock_occupied_keys_count"],4)
        self.assertNotIn("The original commentary",json.dumps(matched))
        self.assertFalse(parsed["source_original_authorial_text_compared"])

    def test_different_key_order_or_reference_blocks(self):
        raw,entries=self.stream()
        parsed,*_=parse_native_raw_corpus(BytesIO(raw))
        with self.assertRaisesRegex(PilotError,"diverged"):
            private_crosscheck(self.index(),"TestCom",
                [("I","Gen"),("K","Gen.1.3"),("K","Gen.1.1"),("U","TOP:1")],parsed)
        with self.assertRaisesRegex(PilotError,"diverged"):
            private_crosscheck(self.index(),"TestCom",
                [("I","Gen"),("K","Gen.1.1"),("K","Gen.1.2"),("U","TOP:1")],parsed)

    def test_incomplete_content_stream_fails_closed(self):
        raw,_=self.stream()
        with self.assertRaises(RawCorpusError):
            parse_native_raw_corpus(BytesIO(raw[:-12]))
        with self.assertRaises(RawCorpusError):
            parse_native_raw_corpus(BytesIO(raw+b"garbage"))

    def test_index_count_mismatch_detected(self):
        raw,_=self.stream()
        parsed,*_=parse_native_raw_corpus(BytesIO(raw))
        with self.assertRaises(PilotError):
            private_crosscheck(self.index().replace(b"S\t30000\t2\t1\t1",
                                                   b"S\t30000\t3\t1\t1"),
                               "TestCom",
                               [("I","Gen"),("K","Gen.1.1"),("K","Gen.1.3"),("U","TOP:1")],
                               parsed)


if __name__=="__main__":
    unittest.main()
