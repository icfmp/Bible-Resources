"""Tests for bounded, key-scoped diatheke invocation and refusal of bad output."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from pilot_preflight import PilotError
from pilot_subprocess import query, present_key, MAX_OUTPUT


class BoundedReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fake = self.root/"diatheke"
        self.fake.chmod(0o700) if self.fake.exists() else None

    def executable(self, code: str):
        self.fake.write_text("#!/usr/bin/env python3\n"+code+"\n")
        self.fake.chmod(0o700)

    def test_key_must_be_last_and_output_format_precedes_key(self):
        self.executable(
            "import json,sys\n"
            "assert sys.argv[1:5] == ['-b','MHC','-f','internal']\n"
            "assert sys.argv[5:] == ['-k','Gen 1:1']\n"
            "print('<p>Correct entry</p>')"
        )
        code, body=query("MHC","Gen 1:1",fmt="internal",root=self.root,exe=str(self.fake))
        self.assertEqual(code,0)
        self.assertIn(b"Correct entry",body)
        self.assertTrue(present_key("Gen 1:1",body,code))

    def test_explicit_note_and_xref_options_precede_terminal_key(self):
        self.executable(
            "import sys\\n"
            "assert sys.argv[1:7]==['-b','MHC','-f','internal','-o','sfnhl']\\n"
            "assert sys.argv[7:]==['-k','Gen 1:1']\\n"
            "print('Synthetic note markup')"
        )
        code,body=query("MHC","Gen 1:1",fmt="internal",root=self.root,
                        exe=str(self.fake),options="sfnhl")
        self.assertEqual(code,0)
        self.assertIn(b"Synthetic",body)
        for invalid in ("not-valid","sffff","s!!","*"):
            with self.subTest(options=invalid):
                with self.assertRaisesRegex(PilotError,"Invalid explicit"):
                    query("MHC","Gen 1:1",fmt="internal",root=self.root,
                          exe=str(self.fake),options=invalid)

    def test_full_module_dump_is_blocked_at_small_cap(self):
        self.executable("import sys\nsys.stdout.write('X'*1000000)")
        with self.assertRaisesRegex(PilotError,"more than 4096 bytes"):
            query("MHC","Gen 1",fmt="internal",root=self.root,
                  exe=str(self.fake),limit=4096)
        self.assertEqual(list(self.root.glob("*.xml")),[])

    def test_missing_module_or_usage_is_not_a_valid_biblical_entry(self):
        self.assertFalse(present_key("Gen 1:1",b"Usage: diatheke [-b ...]",0))
        self.assertFalse(present_key("Gen 1:1",b"not found",0))
        self.assertFalse(present_key("Gen 1:1",b"",0))
        self.assertFalse(present_key("Gen 1:1",b"Text",1))

    def test_invalid_query_format_blocks_before_execution(self):
        with self.assertRaisesRegex(PilotError,"Unreviewed"):
            query("MHC","Gen 1",fmt="unsafe",root=self.root,exe=str(self.fake))


if __name__=="__main__":
    unittest.main()
