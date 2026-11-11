"""No-network tests for reproducible and fail-closed staged Bible research."""
import io
import json
from hashlib import sha256
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bible_intake import IntakeError, ProviderRedirects, acquire, fetch_pinned, load_manifest, _safe_url, parse_audit_comment, parse_observe_comment, observe_current_upstream
from bible_stage_runner import run_stage, run_stage_four_and_five, _write_report, STAGES, main


class _Response(io.BytesIO):
    def __init__(self, url, data):
        super().__init__(data)
        self.url=url

    def geturl(self):
        return self.url


class _Opener:
    def __init__(self, entries):
        self.entries=entries

    def open(self, request, timeout=75):
        if request.full_url not in self.entries:
            raise OSError("Unexpected unapproved download")
        return _Response(request.full_url, self.entries[request.full_url])


def _zip(files):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for name,value in files.items():
            archive.writestr(name,value)
    return buffer.getvalue()


class BibleIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.source=_zip({"authorial_usfx.xml":"<usfx></usfx>"})
        self.sword=_zip({
            "mods.d/TestMod.conf":
                "[TestMod]\nModDrv=RawText\nDescription=Fixture\nLang=en\n"
                "Version=0.1.0\nVersification=KJV\n"
                "DataPath=./modules/texts/rawtext/testmod/\n",
            "modules/texts/rawtext/testmod/ot":"data"
        })
        self.cfg=load_manifest("webp-research")
        self.cfg["source"]["sha256"]=sha256(self.source).hexdigest()
        self.cfg["sword"]["sha256"]=sha256(self.sword).hexdigest()
        self.cfg["sword"]["module_id"]="TestMod"
        self.cfg["sword"]["driver"]="RawText"
        self.opener=_Opener({self.cfg["source"]["url"]:self.source,
                             self.cfg["sword"]["url"]:self.sword})

    def test_exact_manifest_is_research_not_publication(self):
        m=load_manifest("webp-research")
        self.assertEqual(m["purpose"],"research_only")
        self.assertEqual(m["rights"]["status"],"pending")
        self.assertEqual(m["source"]["format"],"USFX")
        self.assertEqual(m["sword"]["driver"],"zText")

    def test_reject_unknown_or_traversal_resource_id(self):
        for identifier in ("../etc/passwd","no.json","", "X", "a/"+"x"*100):
            with self.subTest(identifier=identifier),self.assertRaises(IntakeError):
                load_manifest(identifier)

    def test_reject_untrusted_host_http_credentials_queries_and_fragments(self):
        cases=("https://evil.example/file.zip","http://ebible.org/a.zip",
               "https://user:pass@ebible.org/x.zip",
               "https://ebible.org:444/x.zip","https://ebible.org/a.zip?token=private",
               "https://ebible.org/a.zip#part",
               "https://ebible.org.evil.example/a.zip")
        for url in cases:
            with self.subTest(url=url),self.assertRaises(IntakeError):
                _safe_url(url,"ebible")

    def test_redirect_out_of_provider_allowlist_is_blocked(self):
        redirect=ProviderRedirects("ebible")
        with self.assertRaises(IntakeError):
            redirect.redirect_request(None,None,302,"Move",{},"https://evil.example/a.zip")

    def test_authenticated_comment_command_parser_is_strict(self):
        self.assertEqual(parse_audit_comment("/bible-audit next-bible-1910 4"),
                         ("next-bible-1910",4))
        self.assertEqual(parse_audit_comment("/bible-audit next-bible-1910 4-5"),
                         ("next-bible-1910","4-5"))
        for command in ("/bible-audit ../outside 4",
                        "/bible-audit safe 8",
                        "/bible-audit safe 4; rm -rf /",
                        "/bible-audit safe 4\\nother",
                        "/bible-audit safe 04"):
            with self.subTest(command=command),self.assertRaises(IntakeError):
                parse_audit_comment(command)

    def test_observe_comment_parser_does_not_accept_script_or_multiple_lines(self):
        self.assertEqual(parse_observe_comment("/bible-observe frajnd-2024"), "frajnd-2024")
        for candidate in ("/bible-observe ../file", "/bible-observe frajnd-2024 3",
                          "/bible-observe frajnd-2024\\nother",
                          "/bible-observe frajnd-2024; echo unsafe"):
            with self.subTest(command=candidate), self.assertRaises(IntakeError):
                parse_observe_comment(candidate)

    def test_observe_upstream_hashes_without_authorizing_revision(self):
        with patch("bible_intake.load_manifest",return_value=self.cfg):
            report=observe_current_upstream("webp-research",opener=self.opener)
        self.assertFalse(report["published"])
        self.assertTrue(report["source_zip_not_retained"])
        self.assertTrue(report["archives"]["source"]["still_pinned"])
        self.assertTrue(report["archives"]["sword"]["still_pinned"])
        self.assertFalse(report["archives"]["source"]["rights_or_edition_equivalence_verified"])
        self.assertEqual(report["archives"]["sword"]["sword_conf"]["module_id"], "TestMod")
        self.assertEqual(report["archives"]["sword"]["sword_conf"]["driver"], "RawText")
        self.assertTrue(report["archives"]["sword"]["safe_original_zip_structure_verified"])
        self.assertEqual(report["archives"]["source"]["source_xml_members"], ["authorial_usfx.xml"])
        self.assertFalse(report["safe_to_acquire_without_approved_pins"])
        self.assertFalse(report["exact_edition_content_equivalence_verified"])
        self.assertFalse((self.folder/"source.zip").exists())

    def test_streaming_download_and_hash_pinning(self):
        dest=self.folder/"source.zip"
        receipt=fetch_pinned(self.cfg["source"]["url"],
                             self.cfg["source"]["sha256"],"ebible",dest,opener=self.opener)
        self.assertEqual(receipt["sha256"],sha256(self.source).hexdigest())
        self.assertEqual(dest.read_bytes(),self.source)

    def test_mismatched_sha_does_not_leave_corrupt_file(self):
        dest=self.folder/"original.zip"
        with self.assertRaisesRegex(IntakeError,"SHA-256 drift"):
            fetch_pinned(self.cfg["source"]["url"],"0"*64,"ebible",dest,opener=self.opener)
        self.assertFalse(dest.exists())
        self.assertFalse(list(self.folder.glob(".intake-*")))

    def test_overwrite_is_refused(self):
        dest=self.folder/"original.zip"
        dest.write_bytes(b"previous approved file")
        with self.assertRaisesRegex(IntakeError,"overwrite"):
            fetch_pinned(self.cfg["source"]["url"],
                          self.cfg["source"]["sha256"],"ebible",dest,opener=self.opener)
        self.assertEqual(dest.read_bytes(),b"previous approved file")

    def test_stage_one_requires_human_review(self):
        result=run_stage(self.cfg,1,self.folder)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertTrue(any("Rights" in x for x in result["missing"]))

    def test_provisional_stage_one_never_fetches_without_sha_pins(self):
        # A fixture deliberately left unpinned in memory, independent of a
        # real import's progress from observation to approved fingerprints.
        manifest = load_manifest("frajnd-2024")
        manifest["source"]["sha256"] = None
        manifest["sword"]["sha256"] = None
        manifest["sword"]["module_id"] = None
        manifest["sword"]["driver"] = None
        with patch("bible_stage_runner.acquire", side_effect=AssertionError("Network must not be attempted")) as fetch:
            stage_one = run_stage(manifest, 1, self.folder)
            stage_two = run_stage(manifest, 2, self.folder)
            stage_three = run_stage(manifest, 3, self.folder)
        fetch.assert_not_called()
        self.assertEqual(stage_one["status"], "REVIEW_REQUIRED")
        self.assertTrue(any("SHA-256 not yet" in field for field in stage_one["missing"]))
        self.assertEqual(stage_two["status"], "BLOCKED")
        self.assertEqual(stage_three["status"], "BLOCKED")
        with self.assertRaisesRegex(IntakeError, "Invalid expected SHA-256"):
            fetch_pinned(manifest["source"]["url"], None, "ebible",
                         self.folder/"forbidden.zip", opener=_Opener({}))
        self.assertFalse((self.folder/"forbidden.zip").exists())

    def test_stage_two_proves_both_original_archives_and_sword_driver(self):
        result=run_stage(self.cfg,2,self.folder,opener=self.opener)
        self.assertEqual(result["status"],"DONE")
        self.assertEqual(result["evidence"]["original_archives"]["sword"]["sword"]["driver"],"RawText")
        self.assertFalse(result["missing"])

    def test_stage_two_rejects_incorrect_original_binary_driver(self):
        self.cfg["sword"]["driver"]="zText"
        with self.assertRaisesRegex(IntakeError,"driver differs"):
            run_stage(self.cfg,2,self.folder,opener=self.opener)

    def test_stage_three_source_requires_reviewed_usfx_schema_and_no_text_output(self):
        # Original-SWORD reuse does not require a fabricated USFX→OSIS conversion.
        raw=(b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>'
             b'PRIVATE AUTHORIAL WORDS<f caller="+"><ft>PRIVATE NOTE</ft></f>'
             b'</p></book></usfx>')
        archived=self.folder/"original.zip"
        archived.write_bytes(_zip({"fixture_usfx.xml":raw}))
        schema=self.folder/"usfx.xsd"
        schema.write_bytes(b"schema-byte-placeholder")
        with patch("bible_stage_runner.acquire",
                   return_value=({"source":{"sha256":"a"*64}},{"source":archived})):
            missing=run_stage(self.cfg,3,self.folder)
            self.assertEqual(missing["status"],"BLOCKED")
            self.assertTrue(any("USFX XSD" in s for s in missing["missing"]))
            with patch("usfx_schema_gate.validate_source_with_pinned_schema",
                       return_value={"official_usfx_schema_validated":True,
                                     "status":"official_usfx_xsd_validated"}):
                reviewed=run_stage(self.cfg,3,self.folder,usfx_schema=schema)
        self.assertEqual(reviewed["status"],"PARTIAL")
        self.assertEqual(reviewed["evidence"]["source_inventory"]["source_note_types"],{"f":1})
        self.assertFalse(reviewed["evidence"]["conversion_performed"])
        self.assertFalse(reviewed["evidence"]["conversion_applicability_reviewed"])
        self.assertNotIn("PRIVATE",str(reviewed))
        self.assertIn("Exact official pinned USFX XSD validated the complete original source",
                      reviewed["verified"])

    def test_stage_four_without_stock_native_inspector_is_blocked(self):
        with patch("bible_stage_runner.acquire",return_value=({"source":{},"sword":{}},{})):
            result=run_stage(self.cfg,4,self.folder)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertIn("binary missing",result["missing"][0])

    def _fake_stage_four_receipt(self, *, loss=False):
        return {
            "status": "BLOCKED" if loss else "PARTIAL",
            "verified": ["Synthetic stage-4 private source/native proof"],
            "missing": ["Review stock loss" if loss else "Review whitespace"],
            "evidence": {
                "original_archives": {
                    "source": {"sha256": "a"*64},
                    "sword": {"sha256": "b"*64},
                },
                "notes": {"status": "numbered-source-note-diagnostic"},
                "note_anchor_positions": {
                    "all_numbered_note_nonspace_anchor_positions_match": True,
                },
                "source_scope": {},
                "stock_reuse_preflight": {
                    "proven_material_stock_loss": loss,
                    "material_loss_categories":
                        {"literal_source_caller_no_native_n": 2} if loss else {},
                },
            },
        }

    def test_fast_note_loss_rejects_stock_before_full_corpus_scan(self):
        from bible_stage_runner import _run_fidelity
        self.cfg["source"]["format"] = "USFX"
        native = self.folder/"native-binary"
        native.write_bytes(b"fixture")
        with (patch("fast_stock_note_probe.probe_stock_note_callers",
                    return_value={
                        "status":"BLOCKED",
                        "reason_code":"literal_note_caller_missing",
                        "fast_stock_reuse_disqualified":True,
                    }) as pre,
              patch("source_native_maintext_probe.run_real_usfx_sword_text_probe",
                    side_effect=AssertionError("Full corpus must be skipped")) as full):
            result = _run_fidelity(
                self.cfg,{"source":self.folder/"source.zip",
                          "sword":self.folder/"stock.zip"},
                self.folder,index_binary=native,raw_binary=native,
                entry_binary=native,schema=None)
        pre.assert_called_once()
        full.assert_not_called()
        self.assertEqual(result["status"],"BLOCKED")
        self.assertFalse(result["evidence"]["whole_corpus_scan_performed"])
        self.assertEqual(result["evidence"]["fast_stock_note_preflight"][
            "reason_code"],"literal_note_caller_missing")

    def test_stage_five_keeps_fast_stock_loss_without_claiming_full_notes(self):
        from bible_stage_runner import _stage5_from_fidelity
        fast={
            "status":"BLOCKED",
            "reason_code":"literal_note_caller_missing",
            "fast_stock_reuse_disqualified":True,
        }
        stage4={
            "status":"BLOCKED","evidence":{"fast_stock_note_preflight":fast}}
        result=_stage5_from_fidelity(stage4, {})
        self.assertEqual(result["status"],"BLOCKED")
        self.assertFalse(result["evidence"]["whole_corpus_scan_performed"])
        self.assertTrue(result["evidence"]["fast_stock_note_preflight"][
            "fast_stock_reuse_disqualified"])

    def test_stage_four_five_bundle_invokes_one_fidelity_stage(self):
        original = self._fake_stage_four_receipt()
        with patch("bible_stage_runner.run_stage", return_value=original) as checked:
            four, five = run_stage_four_and_five(self.cfg, self.folder)
        checked.assert_called_once()
        self.assertEqual(checked.call_args.args[1], 4)
        self.assertIs(four, original)
        self.assertEqual(five["status"], "PARTIAL")
        self.assertEqual(five["evidence"]["original_archives"],
                         four["evidence"]["original_archives"])

    def test_stage_four_five_bundle_retains_annotation_loss_blocker(self):
        original = self._fake_stage_four_receipt(loss=True)
        with patch("bible_stage_runner.run_stage", return_value=original):
            four, five = run_stage_four_and_five(self.cfg, self.folder)
        self.assertEqual(four["status"], "BLOCKED")
        self.assertEqual(five["status"], "BLOCKED")
        self.assertTrue(five["evidence"]["stock_reuse_preflight"][
            "proven_material_stock_loss"])

    def test_stage_four_five_bundle_does_not_infer_missing_notes(self):
        original = self._fake_stage_four_receipt()
        del original["evidence"]["notes"]
        with patch("bible_stage_runner.run_stage", return_value=original):
            four, five = run_stage_four_and_five(self.cfg, self.folder)
        self.assertEqual(four["status"], "PARTIAL")
        self.assertEqual(five["status"], "BLOCKED")

    def test_combined_cli_writes_two_separate_machine_receipts(self):
        original = self._fake_stage_four_receipt(loss=True)
        five = {
            "status": "BLOCKED", "verified": [],
            "missing": ["Review omitted note callers"],
            "evidence": {"stock_reuse_preflight":
                         original["evidence"]["stock_reuse_preflight"]},
        }
        with patch("bible_stage_runner.run_stage_four_and_five",
                   return_value=(original,five)) as combined:
            exit_code=main(["--resource-id","webp-research","--stage","4-5",
                            "--report-dir",str(self.folder)])
        self.assertEqual(exit_code,0)  # Audit BLOCKED is a valid diagnostic
        combined.assert_called_once()
        report=json.loads((self.folder/"stage-report.json").read_text())
        self.assertEqual(report["stage"],"4-5")
        self.assertEqual(report["schema_version"],2)
        self.assertEqual(report["status"],"BLOCKED")
        self.assertFalse(report["gate_completed"])
        self.assertFalse(report["reusable_for_pub_approval"])
        self.assertEqual(report["evidence"]["shared_fidelity_invocations"],1)
        self.assertFalse(report["evidence"]["full_native_corpus_scan_completed"])
        self.assertEqual(set(report["evidence"]["stage_machine_receipts"]),{"4","5"})
        self.assertIn("stage 4-5/7",(self.folder/"stage-summary.md").read_text())

    def test_bundle_command_rejects_unreviewed_ranges_and_shell_content(self):
        for value in ("/bible-audit safe 3-4", "/bible-audit safe 4-5; rm -rf /",
                      "/bible-audit safe 4-5\\nPRIVATE"):
            with self.subTest(value=value), self.assertRaises(IntakeError):
                parse_audit_comment(value)

    def test_stage_seven_never_publishes_or_auto_approves(self):
        result=run_stage(self.cfg,7,self.folder)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertTrue(any("Owner" in x for x in result["missing"]))

    def test_reports_are_metadata_only_and_not_overwritten(self):
        report={
          "resource_id":"fixture","stage":2,"stage_name":STAGES[2],
          "status":"DONE","git_sha":"abc123","run_url":None,
          "next_action":"Proceed to stage 3/7",
          "verified":["pinned SHA passed"],"missing":[],
          "evidence":{"original_archives":{"source":{"sha256":"a"*64}}},
          "reusable_for_pub_approval":False,
        }
        _write_report(self.folder,report)
        self.assertIn("pinned SHA passed",(self.folder/"stage-summary.md").read_text())
        self.assertFalse(json.loads((self.folder/"stage-report.json").read_text())["reusable_for_pub_approval"])
        with self.assertRaisesRegex(IntakeError,"replace"):
            _write_report(self.folder,report)

    def test_stage_four_issue_summary_exposes_only_safe_bounded_newline_coordinates(self):
        samples=[
            {"reference":"Gen.1.1","source_xml_fragment_origin":
             "text_within_paragraph_element",
             "original_verse_nonspace_codepoint_gap":11,
             "nearest_explicit_authorial_p_q_boundary_distance_codepoints":4,
             "editorial_linebreak_intent_unverified":True},
            {"reference":"PRIVATE SECRET","source_xml_fragment_origin":
             "text_within_paragraph_element",
             "original_verse_nonspace_codepoint_gap":11,
             "nearest_explicit_authorial_p_q_boundary_distance_codepoints":4,
             "editorial_linebreak_intent_unverified":True},
            {"reference":"Gen.1.2","source_xml_fragment_origin":
             "PRIVATE NOTE CONTENT",
             "original_verse_nonspace_codepoint_gap":11,
             "nearest_explicit_authorial_p_q_boundary_distance_codepoints":4,
             "editorial_linebreak_intent_unverified":True}
        ]
        report={
          "resource_id":"fixture","stage":4,"stage_name":STAGES[4],
          "status":"PARTIAL","git_sha":"abc123","run_url":None,
          "next_action":"Review semantics", "verified":[], "missing":["Review required"],
          "evidence":{"maintext":{"source_native_structural_whitespace_gap_triage":{
              "first_unmarked_internal_newline_xml_origin_references_only":samples
          }}},
        }
        _write_report(self.folder,report)
        summary=(self.folder/"stage-summary.md").read_text()
        self.assertIn("Gen.1.1", summary)
        self.assertIn("source gap 11", summary)
        self.assertIn("boundary 4 codepoints away", summary)
        self.assertIn("do NOT prove layout equivalence", summary)
        self.assertNotIn("PRIVATE SECRET", summary)
        self.assertNotIn("PRIVATE NOTE CONTENT", summary)

    def test_manifest_unknown_fields_and_reviewed_path_escape_rejected(self):
        newroot=self.folder/"repo"
        (newroot/"config/bible-intake").mkdir(parents=True)
        (newroot/"schemas").mkdir()
        (newroot/"config").mkdir(exist_ok=True)
        shutil.copyfile(ROOT/"schemas/bible-intake.schema.json",
                        newroot/"schemas/bible-intake.schema.json")
        manifest=load_manifest("webp-research")
        manifest["unexpected_authorization"]="published"
        (newroot/"config/bible-intake/webp-research.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(IntakeError,"Invalid reviewed manifest"):
            load_manifest("webp-research",root=newroot)


if __name__=="__main__":
    unittest.main()
