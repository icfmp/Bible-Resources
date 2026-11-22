"""Synthetic safety tests for native SWORD audits from approved cleaned OSIS."""
import os
from pathlib import Path
import json
from hashlib import sha256
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from research.bible.native_milestone_pair_audit import NativeMilestonePairAudit
from approved_osis_sword_candidate import (
    ApprovedOSISNativeError, _create_candidate_layout, _native_notes,
    _read_native_frames, _compile_osis, safe_failure_code,
    compiler_output_metrics,
    select_candidate_versifications, approved_source_for,
)


class ApprovedSourceNativeAuditTests(unittest.TestCase):
    def test_only_approved_versification_can_be_requested(self):
        cfg, _ = approved_source_for("darby-jnd-2024")
        self.assertEqual(select_candidate_versifications(cfg, None), ["Luther"])
        self.assertEqual(select_candidate_versifications(cfg, "Luther"), ["Luther"])
        for invalid in ("DarbyFr", "KJV", "../evil", "", "Luther/evil"):
            with self.assertRaises(ApprovedOSISNativeError):
                select_candidate_versifications(cfg, invalid)
        for value in ("../evil", "", "frajnd-2024", "SECRET/private"):
            with self.assertRaises(ApprovedOSISNativeError):
                approved_source_for(value)

    def test_approved_cleaned_osis_uses_exact_published_source_pins(self):
        for name, scheme in (("darby-jnd-2024", "Luther"),
                             ("lsg-1910", "Segond")):
            with self.subTest(resource=name):
                cfg, raw = approved_source_for(name)
                self.assertEqual(cfg["candidate_versifications"], [scheme])
                self.assertEqual(cfg["language"], "fr")
                self.assertGreater(len(raw), 1_000_000)
                meta = json.loads((Path(__file__).resolve().parents[1] /
                                   "modules" / name /
                                   "SOURCE_VALIDATION.json").read_text())
                self.assertEqual(sha256(raw).hexdigest(), meta["source_sha256"])

    def test_approved_source_rejects_tampering_before_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "modules" / "fixture"
            module.mkdir(parents=True)
            cleaned = root / "sources/cleaned/bibles/en/fixture"
            cleaned.mkdir(parents=True)
            xml = cleaned / "fixture.osis.xml"
            xml.write_bytes(b"<osis>approved bytes</osis>")
            digest = sha256(xml.read_bytes()).hexdigest()
            meta = {"id":"fixture", "category":"bible", "language":"en",
                    "sword_id":"TestFixture", "versification":"KJV",
                    "quality":{"status":"approved"}}
            receipt = {"status":"validated", "source_kind":"bible",
                       "source_sha256":digest}
            manifest = {"resource_id":"fixture", "type":"bible",
                        "language":"en", "source_format":"OSIS",
                        "cleaned_source_sha256":digest}
            (module / "metadata.json").write_text(json.dumps(meta))
            (module / "SOURCE_VALIDATION.json").write_text(json.dumps(receipt))
            (cleaned / "CLEANUP_MANIFEST.json").write_text(json.dumps(manifest))
            cfg, raw = approved_source_for("fixture", root=root)
            self.assertEqual(raw, xml.read_bytes())
            self.assertEqual(cfg["language"], "en")
            self.assertEqual(cfg["candidate_versifications"], ["KJV"])
            xml.write_bytes(raw + b"changed")
            with self.assertRaises(ApprovedOSISNativeError):
                approved_source_for("fixture", root=root)
            xml.write_bytes(raw)
            manifest["cleaned_source_sha256"] = "0" * 64
            (cleaned / "CLEANUP_MANIFEST.json").write_text(json.dumps(manifest))
            with self.assertRaises(ApprovedOSISNativeError):
                approved_source_for("fixture", root=root)
            manifest["cleaned_source_sha256"] = digest
            (cleaned / "CLEANUP_MANIFEST.json").write_text(json.dumps(manifest))
            meta["quality"]["status"] = "pending"
            (module / "metadata.json").write_text(json.dumps(meta))
            with self.assertRaises(ApprovedOSISNativeError):
                approved_source_for("fixture", root=root)

    def test_layout_is_separate_nonpublishing_standard_sword(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            payload,out=_create_candidate_layout(
                root/"build","TestAuditResearch","Luther")
            conf=(payload/"mods.d/testauditresearch.conf").read_text()
            self.assertIn("ModDrv=zText",conf)
            self.assertIn("BlockType=BOOK",conf)
            self.assertIn("CompressType=ZIP",conf)
            self.assertIn("Versification=Luther",conf)
            self.assertIn("SourceType=OSIS",conf)
            self.assertTrue(out.is_dir())
            with self.assertRaises(ApprovedOSISNativeError):
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
            with self.assertRaises(ApprovedOSISNativeError):
                list(_read_native_frames(stub,"Fake",root))

    def test_safe_failure_codes_do_not_expose_private_exception_content(self):
        self.assertEqual(safe_failure_code(ApprovedOSISNativeError(
            "OSIS tool returned nonzero exit status 1")), "compiler_nonzero_exit")
        self.assertEqual(safe_failure_code(ApprovedOSISNativeError(
            "Stock SWORD module contains no populated Bible verses")),
            "native_zero_populated_verses")
        self.assertEqual(safe_failure_code(ApprovedOSISNativeError(
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

    def test_compiled_paragraph_milestones_spanning_verses_are_paired(self):
        # The real candidate's independent raw-reader scan must cover every
        # numbered, intro and TOP frame; a matching tag *count* is not enough.
        audit=NativeMilestonePairAudit()
        audit.observe("K","Gen.1.1",
                      b'<div type="x-p" sID="PRIVATE-A"/>first')
        audit.observe("K","Gen.1.2",
                      b'second<div eID="PRIVATE-A"/>')
        result=audit.finish()
        self.assertEqual(result["paired_div_types_allowlisted"]["x-p"],1)
        self.assertEqual(result["native_numbered_intro_scan_counts"][
            "paired_matching_sID_eID"],1)
        self.assertNotIn("PRIVATE-A",str(result))

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
