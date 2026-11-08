"""Synthetic SWORD compiler / reader fixtures, no Scripture in test binaries."""
from pathlib import Path
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_sword_rebuild import (
    compile_candidate,SAMPLES,PROBE_V11N,ALTERNATE_PROBE_V11N,
    PUBLISHER_DECLARED_V11N, classify_chapter_slot_differences
)


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
          "import os,sys\n"
          "from pathlib import Path\n"
          "assert sys.argv[5]=='-k'\n"
          "conf=(Path(os.environ['SWORD_PATH'])/'mods.d/fralsg1910eb.conf').read_text()\n"
          "for feature in ('OSISLemma','OSISStrongs','OSISFootnotes',"
          "'OSISScripref','OSISHeadings'):\n"
          "    assert 'GlobalOptionFilter='+feature+'\\n' in conf\n"
          "print(sys.argv[-1]+': Synthetic words')\n")
        self.reader.chmod(0o700)

    def test_real_compilation_stage_does_not_touch_source_or_publish_files(self):
        original=self.source.read_bytes()
        r=compile_candidate(self.source,compiler=str(self.compiler),reader=str(self.reader))
        self.assertEqual(r["status"],"actual_text_module_compiled_and_samples_read_not_approved")
        self.assertEqual(len(r["reader_probes"]),len(SAMPLES))
        self.assertTrue(r["all_sample_keys_have_text"])
        self.assertEqual(r["versification"],"Segond")
        self.assertEqual(PROBE_V11N,"Segond")
        self.assertEqual(PUBLISHER_DECLARED_V11N,"NRSV")
        self.assertEqual(r["publisher_declared_versification"],"NRSV")
        self.assertFalse(r["publisher_v11n_matches_diagnostic_probe"])
        self.assertFalse(r["versification_approved"])
        self.assertTrue(r["source_file_unchanged"])
        self.assertFalse(r["approved_for_publication"])
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual(list(self.root.glob("**/*.conf")),[])

    def test_calvin_uses_an_independent_temporary_module_not_source_rewrites(self):
        # Exercise the same script with an alternative reviewed SWORD v11n.
        script=self.compiler.read_text()
        self.compiler.write_text(script.replace("['-v','Segond']",
                                                "['-v','Calvin']"))
        result=compile_candidate(self.source,compiler=str(self.compiler),
                                 reader=str(self.reader),versification="Calvin")
        self.assertTrue(result["real_module_rebuilt_in_temporary_directory"])
        self.assertEqual(result["versification"],"Calvin")
        self.assertEqual(ALTERNATE_PROBE_V11N,"Calvin")
        self.assertFalse(result["approved_for_publication"])
        self.assertFalse(result["versification_approved"])
        self.assertFalse(result["publisher_v11n_matches_diagnostic_probe"])
        self.assertEqual(self.source.read_bytes(),
                         b"<osis>SIMULATED PUBLIC TEST ONLY</osis>")

    def test_unreviewed_v11n_is_rejected_before_compilation(self):
        from pilot_preflight import PilotError
        with self.assertRaisesRegex(PilotError,"Unreviewed SWORD versification"):
            compile_candidate(self.source,compiler=str(self.compiler),
                              reader=str(self.reader),versification="unknown")

    def test_extra_blank_reader_registry_slot_is_not_mistaken_for_scripture(self):
        audit=classify_chapter_slot_differences(
            {35:"Source verse.",36:"Authorial final verse."},
            {35:"Source verse.",36:"Authorial final verse.",37:""}
        )
        self.assertEqual(audit["diagnostic_slot_classes"][0]["classification"],
                         "empty_readback_verse_slot")
        self.assertTrue(audit["complete_chapter_character_stream_equal_ignoring_whitespace"])
        self.assertFalse(audit["all_verse_reference_slots_verified"])
        self.assertFalse(audit["editorial_and_versification_approved"])
        self.assertNotIn("Authorial",repr(audit))

    def test_source_extra_verse_merged_into_previous_reader_slot_is_classified(self):
        audit=classify_chapter_slot_differences(
            {51:"First.",52:"Second.",53:"Last."},
            {51:"First.",52:"Second. Last."})
        self.assertEqual(audit["source_only_verses"],[53])
        self.assertEqual(audit["diagnostic_slot_classes"][0]["classification"],
                         "readback_preceding_slot_contains_both_verse_character_streams")
        self.assertTrue(audit["complete_chapter_character_stream_equal_ignoring_whitespace"])
        self.assertFalse(audit["editorial_and_versification_approved"])

    def test_true_missing_scripture_cannot_be_misclassified_as_index_only(self):
        audit=classify_chapter_slot_differences(
            {51:"First.",52:"Second.",53:"Last."},
            {51:"First.",52:"Second."})
        self.assertEqual(audit["diagnostic_slot_classes"][0]["classification"],
                         "unresolved_missing_verse_index")
        self.assertFalse(audit["complete_chapter_character_stream_equal_ignoring_whitespace"])
        audit=classify_chapter_slot_differences(
            {35:"A.",36:"B."},
            {35:"A.",36:"B.",37:"Unreviewed!"})
        self.assertEqual(audit["diagnostic_slot_classes"][0]["classification"],
                         "unexpected_populated_reader_slot")
        self.assertFalse(audit["complete_chapter_character_stream_equal_ignoring_whitespace"])

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
