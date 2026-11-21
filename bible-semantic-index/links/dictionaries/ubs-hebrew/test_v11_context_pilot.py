#!/usr/bin/env python3
"""Bounded source-context sample stays private and never approves senses."""
from pathlib import Path
import runpy
import unittest

m=runpy.run_path(str(Path(__file__).with_name("build_v11_context_pilot.py")))

class SamplePolicy(unittest.TestCase):
    def test_stable_sha_sampling(self):
        self.assertEqual(m["_rank"]("o010010010012"),m["_rank"]("o010010010012"))
        self.assertNotEqual(m["_rank"]("o010010010012"),m["_rank"]("o010010010021"))
    def test_no_unattested_census(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m["sample"]({"status":"PUBLIC","candidate_word_count":53981},[],[],Path("/dev/null"))

if __name__=="__main__":
    unittest.main()
