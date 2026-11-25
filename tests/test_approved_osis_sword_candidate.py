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
    approved_source_for, project_reviewed_merge_slots,
)


class ReviewedMergeProjectionTests(unittest.TestCase):
    def test_exact_private_projection_preserves_notes_targets_and_anchors(self):
        verses = {"Gen.1.1": "First word.", "Gen.1.2": "Second!",
                  "Gen.2.1": "Next."}
        notes = {ref: [] for ref in verses}
        notes["Gen.1.2"] = [{"body": "A note", "caller": "a", "type": "study",
                             "targets": ("Gen.1.2",), "point": 3}]
        result, projected = project_reviewed_merge_slots(
            verses, notes, [("Gen.1.2", "Gen.1.1")])
        self.assertEqual(result, {"Gen.1.1": "First word. Second!", "Gen.2.1": "Next."})
        self.assertEqual(projected["Gen.1.1"][0]["point"], 13)
        self.assertEqual(projected["Gen.1.1"][0]["targets"], ("Gen.1.2",))
        self.assertEqual(notes["Gen.1.2"][0]["point"], 3)
        self.assertIn("Gen.1.2", verses)

    def test_reject_missing_nonadjacent_cross_chapter_nonfinal_and_duplicate_merges(self):
        verses = {"Gen.1.1": "a", "Gen.1.2": "b", "Gen.1.3": "c", "Gen.2.1": "d"}
        notes = {ref: [] for ref in verses}
        for merges in (
            [("Gen.1.2", "Gen.1.1")],
            [("Gen.1.3", "Gen.1.1")],
            [("Gen.2.1", "Gen.1.3")],
            [("Gen.1.4", "Gen.1.3")],
            [("Gen.1.3", "Gen.1.2"), ("Gen.1.3", "Gen.1.2")],
        ):
            with self.subTest(merges=merges):
                with self.assertRaises(ApprovedOSISNativeError):
                    project_reviewed_merge_slots(verses, notes, merges)

    def test_reject_invalid_note_anchor_and_missing_note_scope(self):
        verses = {"Gen.1.1": "a", "Gen.1.2": "b"}
        with self.assertRaises(ApprovedOSISNativeError):
            project_reviewed_merge_slots(verses, {}, [])
        notes = {"Gen.1.1": [], "Gen.1.2": [{"point": 2}]}
        with self.assertRaises(ApprovedOSISNativeError):
            project_reviewed_merge_slots(verses, notes, [("Gen.1.2", "Gen.1.1")])


class ApprovedSourceNativeAuditTests(unittest.TestCase):
    def test_unreviewed_or_missing_approved_modules_are_rejected(self):
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

    def test_missing_original_note_labels_block_numbered_fidelity(self):
        # Regression for #95: unchanged prose, note body, type and anchor
        # cannot compensate for lost authorial note-call labels.
        from unittest.mock import patch
        from approved_osis_sword_candidate import _candidate_result
        expected = {"Gen.1.1": [{"caller": "a", "type": "x-footnote",
                    "body": "PRIVATE NOTE", "targets": (), "point": 5}]}
        inventory = {"module_payload_sha256": "0" * 64,
                     "reader_version": "fixture", "module_driver": "zText"}
        source = {"Gen.1.1": "alpha beta"}
        boundary_proof = {"all_book_body_nonspace_and_boundary_events_equal": True}
        ordered_proof = {"same_order_and_kind_in_every_mapped_book": True}
        for marker, equal in ((b' n="a"', True), (b'', False),
                              (b' n="b"', False), (b' n=""', False)):
            with self.subTest(marker=marker):
                raw = (b'alpha<note type="x-footnote"' + marker +
                       b'>PRIVATE NOTE</note> beta')
                with patch("approved_osis_sword_candidate.collect_native_inventory",
                           return_value=("Gen.1.1\\n", {}, inventory)), \
                     patch("approved_osis_sword_candidate._read_native_frames",
                           return_value=iter([("K", "Gen.1.1", raw)])), \
                     patch("approved_osis_sword_candidate.compare_book_boundary_positions",
                           return_value=boundary_proof), \
                     patch("approved_osis_sword_candidate.compare_ordered_body_openings",
                           return_value=ordered_proof):
                    report = _candidate_result(Path("index"), Path("raw"),
                        Path("fixture"), "Fixture", "KJV", source, expected,
                        {}, {}, {}, {}, [])
                counts = report["source_to_compiled_counts"]
                self.assertEqual(counts["numbered_verse_nonspace_main_text_equal"], 1)
                self.assertEqual(counts["note_body_equal_after_whitespace_folding"], 1)
                self.assertEqual(counts["note_nonspace_anchor_equal"], 1)
                self.assertEqual(counts["note_original_caller_label_equal"] if equal
                                 else counts["note_original_caller_label_different"], 1)
                self.assertEqual(report["numbered_slot_text_and_note_parity_verified"], equal)
                self.assertNotIn("PRIVATE NOTE", str(report))

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
