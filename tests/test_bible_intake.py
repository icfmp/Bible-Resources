"""No-network tests for safe pinned Bible original archive observation."""
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
from bible_intake import IntakeError, ProviderRedirects, fetch_pinned, load_manifest, _safe_url, parse_observe_comment, observe_current_upstream


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
        self.source=_zip({"authorial.osis.xml":"<osis></osis>"})
        self.sword=_zip({
            "mods.d/TestMod.conf":
                "[TestMod]\nModDrv=RawText\nDescription=Fixture\nLang=en\n"
                "Version=0.1.0\nVersification=KJV\n"
                "DataPath=./modules/texts/rawtext/testmod/\n",
            "modules/texts/rawtext/testmod/ot":"data"
        })
        # Test-only edition: real manifest validation without active intake.
        self.resource_id = "synthetic-research"
        self.fixture_root = self.folder / "fixture-root"
        (self.fixture_root / "config/bible-intake").mkdir(parents=True)
        (self.fixture_root / "schemas").mkdir()
        shutil.copyfile(ROOT / "schemas/bible-intake.schema.json",
                        self.fixture_root / "schemas/bible-intake.schema.json")
        shutil.copyfile(ROOT / "config/standard_usfm_osis_66.json",
                        self.fixture_root / "config/standard_usfm_osis_66.json")
        fixture = {
            "schema_version": 1, "resource_id": self.resource_id,
            "category": "bible", "title": "Synthetic research Bible",
            "language": "en", "edition": "Test-only source and native sample",
            "provider": "ebible", "purpose": "research_only",
            "rights": {"status": "pending", "evidence_url": "https://ebible.org/"},
            "source": {"format": "OSIS", "member": "authorial.osis.xml",
                       "url": "https://ebible.org/Scriptures/synthetic-osis.zip",
                       "sha256": sha256(self.source).hexdigest()},
            "sword": {"url": "https://ebible.org/sword/zip/synthetic-sword.zip",
                      "sha256": sha256(self.sword).hexdigest(),
                      "module_id": "TestMod", "driver": "RawText",
                      "sample_references": ["Gen 1:1", "John 3:16"]},
        }
        (self.fixture_root / "config/bible-intake" /
         (self.resource_id + ".json")).write_text(json.dumps(fixture))
        self.cfg = load_manifest(self.resource_id, root=self.fixture_root)
        self.opener=_Opener({self.cfg["source"]["url"]:self.source,
                             self.cfg["sword"]["url"]:self.sword})

    def test_synthetic_manifest_is_research_not_publication(self):
        m=load_manifest(self.resource_id,root=self.fixture_root)
        self.assertEqual(m["purpose"],"research_only")
        self.assertEqual(m["rights"]["status"],"pending")
        self.assertEqual(m["source"]["format"],"OSIS")
        self.assertEqual(m["sword"]["driver"],"RawText")

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

    def test_observe_comment_parser_does_not_accept_script_or_multiple_lines(self):
        self.assertEqual(parse_observe_comment("/bible-observe frajnd-2024"), "frajnd-2024")
        for candidate in ("/bible-observe ../file", "/bible-observe frajnd-2024 3",
                          "/bible-observe frajnd-2024\\nother",
                          "/bible-observe frajnd-2024; echo unsafe"):
            with self.subTest(command=candidate), self.assertRaises(IntakeError):
                parse_observe_comment(candidate)

    def test_observe_upstream_hashes_without_authorizing_revision(self):
        with patch("bible_intake.load_manifest",return_value=self.cfg):
            report=observe_current_upstream(self.resource_id,opener=self.opener)
        self.assertFalse(report["published"])
        self.assertTrue(report["source_zip_not_retained"])
        self.assertTrue(report["archives"]["source"]["still_pinned"])
        self.assertTrue(report["archives"]["sword"]["still_pinned"])
        self.assertFalse(report["archives"]["source"]["rights_or_edition_equivalence_verified"])
        self.assertEqual(report["archives"]["sword"]["sword_conf"]["module_id"], "TestMod")
        self.assertEqual(report["archives"]["sword"]["sword_conf"]["driver"], "RawText")
        self.assertTrue(report["archives"]["sword"]["safe_original_zip_structure_verified"])
        self.assertEqual(report["archives"]["source"]["source_xml_members"], ["authorial.osis.xml"])
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



if __name__ == "__main__":
    unittest.main()
