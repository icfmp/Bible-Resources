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
from bible_intake import IntakeError, ProviderRedirects, acquire, fetch_pinned, load_manifest, _safe_url, parse_audit_comment, observe_current_upstream
from bible_stage_runner import run_stage, _write_report, STAGES


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
        for command in ("/bible-audit ../outside 4",
                        "/bible-audit safe 8",
                        "/bible-audit safe 4; rm -rf /",
                        "/bible-audit safe 4\\nother",
                        "/bible-audit safe 04"):
            with self.subTest(command=command),self.assertRaises(IntakeError):
                parse_audit_comment(command)

    def test_observe_upstream_hashes_without_authorizing_revision(self):
        with patch("bible_intake.load_manifest",return_value=self.cfg):
            report=observe_current_upstream("webp-research",opener=self.opener)
        self.assertFalse(report["published"])
        self.assertTrue(report["source_zip_not_retained"])
        self.assertTrue(report["archives"]["source"]["still_pinned"])
        self.assertTrue(report["archives"]["sword"]["still_pinned"])
        self.assertFalse(report["archives"]["source"]["rights_or_edition_equivalence_verified"])
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

    def test_stage_two_proves_both_original_archives_and_sword_driver(self):
        result=run_stage(self.cfg,2,self.folder,opener=self.opener)
        self.assertEqual(result["status"],"DONE")
        self.assertEqual(result["evidence"]["original_archives"]["sword"]["sword"]["driver"],"RawText")
        self.assertFalse(result["missing"])

    def test_stage_two_rejects_incorrect_original_binary_driver(self):
        self.cfg["sword"]["driver"]="zText"
        with self.assertRaisesRegex(IntakeError,"driver differs"):
            run_stage(self.cfg,2,self.folder,opener=self.opener)

    def test_stage_four_without_stock_native_inspector_is_blocked(self):
        with patch("bible_stage_runner.acquire",return_value=({"source":{},"sword":{}},{})):
            result=run_stage(self.cfg,4,self.folder)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertIn("binary missing",result["missing"][0])

    def test_stage_seven_never_publishes_or_auto_approves(self):
        result=run_stage(self.cfg,7,self.folder)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertTrue(any("Owner" in x for x in result["missing"]))

    def test_reports_are_metadata_only_and_not_overwritten(self):
        report={
          "resource_id":"fixture","stage":2,"stage_name":STAGES[2],
          "status":"DONE","git_sha":"abc123","run_url":None,
          "verified":["pinned SHA passed"],"missing":[],
          "evidence":{"original_archives":{"source":{"sha256":"a"*64}}},
          "reusable_for_pub_approval":False,
        }
        _write_report(self.folder,report)
        self.assertIn("pinned SHA passed",(self.folder/"stage-summary.md").read_text())
        self.assertFalse(json.loads((self.folder/"stage-report.json").read_text())["reusable_for_pub_approval"])
        with self.assertRaisesRegex(IntakeError,"replace"):
            _write_report(self.folder,report)

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
