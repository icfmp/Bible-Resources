"""Synthetic SWORD compiler / reader fixtures, no Scripture in test binaries."""
from pathlib import Path
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_sword_rebuild import compile_candidate,SAMPLES


class LSGSegondRebuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/"source.osis.xml"
        self.source.write_bytes(b"<osis>SIMULATED PUBLIC TEST ONLY</osis>")
        self.compiler=self.root/"osis2mod"
        self.reader=self.root/"diatheke"
        self.compiler.write_text(
          "#!/usr/bin/env python3\n"
          "from pathlib import Path\n"
          "import sys\n"
          "assert sys.argv[-2:]==['-v','Segond']\n"
          "Path(sys.argv[1],'ot').write_bytes(b'NON_BIBLICAL_TEST_DATA')\n")
        self.compiler.chmod(0o700)
        self.reader.write_text(
          "#!/usr/bin/env python3\n"
          "import sys\n"
          "assert sys.argv[5]=='-k'\n"
          "print(sys.argv[-1]+': Synthetic words')\n")
        self.reader.chmod(0o700)

    def test_real_compilation_stage_does_not_touch_source_or_publish_files(self):
        original=self.source.read_bytes()
        r=compile_candidate(self.source,compiler=str(self.compiler),reader=str(self.reader))
        self.assertEqual(r["status"],"actual_text_module_compiled_and_samples_read_not_approved")
        self.assertEqual(len(r["reader_probes"]),len(SAMPLES))
        self.assertTrue(r["all_sample_keys_have_text"])
        self.assertTrue(r["source_file_unchanged"])
        self.assertFalse(r["approved_for_publication"])
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual(list(self.root.glob("**/*.conf")),[])

    def test_missing_compiled_data_is_not_mistaken_for_a_module(self):
        self.compiler.write_text("#!/usr/bin/env python3\npass\n")
        self.compiler.chmod(0o700)
        result=compile_candidate(self.source,compiler=str(self.compiler),reader=str(self.reader))
        self.assertFalse(result["real_module_rebuilt_in_temporary_directory"])
        self.assertEqual(result["status"],"blocked_compiler_or_unbounded_diagnostics")

    def test_reader_with_only_header_is_not_a_valid_text_round_trip(self):
        self.reader.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\nprint(sys.argv[-1]+':')\n"
        )
        self.reader.chmod(0o700)
        r=compile_candidate(self.source,compiler=str(self.compiler),reader=str(self.reader))
        self.assertFalse(r["all_sample_keys_have_text"])
        self.assertEqual(r["status"],"compiled_but_sample_or_v11n_errors_block")


if __name__=="__main__":
    unittest.main()
