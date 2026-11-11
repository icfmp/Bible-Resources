"""Synthetic safety tests for disposable official OSIS SWORD research builds."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from publisher_osis_sword_candidate import (
    PublisherSWORDResearchError, _create_candidate_layout, _native_notes,
    _read_native_frames, _compile_osis, config_for, safe_failure_code,
    compiler_output_metrics,
    select_candidate_versifications,
)


class PublisherSwordProbeTests(unittest.TestCase):
    def test_reviewed_candidate_does_not_assume_one_versification(self):
        cfg=config_for("frajnd-2024")
        self.assertEqual(cfg["purpose"],"research_only")
        self.assertEqual(cfg["candidate_module_id"],"JND2024Research")
        self.assertEqual(cfg["candidate_versifications"],["DarbyFr","Luther"])
        for value in ("../evil","", "SECRET/private"):
            with self.assertRaises(PublisherSWORDResearchError):
                config_for(value)

    def test_explicit_one_scheme_limits_work_without_source_download(self):
        cfg=config_for("frajnd-2024")
        self.assertEqual(select_candidate_versifications(cfg,"Luther"),["Luther"])
        self.assertEqual(select_candidate_versifications(cfg,"DarbyFr"),["DarbyFr"])
        self.assertEqual(select_candidate_versifications(cfg,None),["DarbyFr","Luther"])
        for invalid in ("KJV","../evil","","DarbyFr/evil"):
            with self.assertRaises(PublisherSWORDResearchError):
                select_candidate_versifications(cfg,invalid)

    def test_layout_is_separate_nonpublishing_standard_sword(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            payload,out=_create_candidate_layout(
                root/"build","JND2024Research","Luther")
            conf=(payload/"mods.d/jnd2024research.conf").read_text()
            self.assertIn("ModDrv=zText",conf)
            self.assertIn("Versification=Luther",conf)
            self.assertIn("SourceType=OSIS",conf)
            self.assertTrue(out.is_dir())
            with self.assertRaises(PublisherSWORDResearchError):
                _create_candidate_layout(root/"bad","../Private","Luther")

    def test_raw_footnote_n_preserved_as_source_value_in_private_memory(self):
        entries=_native_notes(
            b'alpha<note n="a" type="x-footnote">PRIVATE NOTE '
            b'<reference osisRef="Gen.1.2">other</reference></note> beta')
        self.assertEqual(entries,[{
            "caller":"a","type":"x-footnote","body":"PRIVATE NOTE other",
            "targets":("Gen.1.2",),
        }])

    def test_complete_private_raw_stream_frames_and_no_logging(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            script=base/"raw-research-stub"
            raw=b'<note n="a">PRIVATE SECRET</note> ABC'
            script.write_text(
                '#!/usr/bin/env python3\n'
                'import sys\n'
                'out=sys.stdout.buffer\n'
                f'r={raw!r}\n'
                'out.write(b"K\\tGen.1.1\\t"+str(len(r)).encode()+b"\\n")\n'
                'out.write(r)\n'
                'out.write(b"S\\t1\\t1\\t0\\t0\\n")\n')
            script.chmod(0o755)
            rows=list(_read_native_frames(script,"Fake",base))
            self.assertEqual(rows,[("K","Gen.1.1",raw)])
            self.assertNotIn(b"PRIVATE SECRET",str(len(rows)).encode())

    def test_truncated_or_untrusted_raw_reader_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            stub=root/"bad-reader"
            stub.write_text(
                '#!/usr/bin/env python3\n'
                'import sys\n'
                'sys.stdout.buffer.write(b"K\\tGen.1.1\\t8\\nshort")\n')
            stub.chmod(0o755)
            with self.assertRaises(PublisherSWORDResearchError):
                list(_read_native_frames(stub,"Fake",root))

    def test_safe_failure_codes_do_not_expose_private_exception_content(self):
        self.assertEqual(safe_failure_code(PublisherSWORDResearchError(
            "OSIS tool returned nonzero exit status 1")), "compiler_nonzero_exit")
        self.assertEqual(safe_failure_code(PublisherSWORDResearchError(
            "Stock SWORD module contains no populated Bible verses")),
            "native_zero_populated_verses")
        self.assertEqual(safe_failure_code(PublisherSWORDResearchError(
            "Official OSIS compiler exceeded bounded timeout")),
            "compiler_bounded_timeout")
        self.assertEqual(safe_failure_code(ValueError(
            "Stock-SWORD native inspector blocked (exit 7); PRIVATE VERSE")),
            "native_inspector_exit_7")
        self.assertEqual(safe_failure_code(ValueError(
            "PRIVATE PUBLISHER VERSE <unknown>")),
            "unclassified_private_failure")

    def test_private_compiler_output_receipt_never_includes_filenames(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            (path/"PRIVATE_SCRIPTURE.zdt").write_bytes(b"some_private_content")
            report=compiler_output_metrics(path)
            self.assertEqual(report["files"],1)
            self.assertEqual(report["nonempty_files"],1)
            self.assertEqual(report["total_bytes"],len(b"some_private_content"))
            self.assertNotIn("PRIVATE",str(report))

    def test_compiler_log_never_copies_scripture(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            tool=root/"compiler"
            tool.write_text(
                '#!/usr/bin/env python3\n'
                'print("WARNING(PARSE)[11,22]: PRIVATE SCRIPTURE")\n')
            tool.chmod(0o755)
            original=root/"authored.xml"
            original.write_text("<osis/>")
            out=root/"empty-output"
            out.mkdir()
            report=_compile_osis(tool,original,out,"Luther",root/"private.log")
            self.assertEqual(report["returncode"],0)
            self.assertEqual(report["diagnostic_categories"]["WARNING"],1)
            self.assertEqual(report["first_diagnostic_locations_no_source_text"][0][
                "source_line"],11)
            self.assertNotIn("PRIVATE",str(report))


if __name__=="__main__":
    unittest.main()
