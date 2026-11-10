"""Fail-closed release checks for source-pinned, separately reviewed profiles."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalogue_profiles import ProfileError, approved_profiles


class ApprovedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = json.loads(
            (ROOT / "modules/lsg-1910/metadata.json").read_text(encoding="utf-8"))

    def test_real_approved_lsg_has_both_complete_descriptions_and_citations(self):
        profiles = approved_profiles(ROOT, ROOT / "modules/lsg-1910", self.module)
        self.assertEqual(set(profiles), {"fr"})
        p = profiles["fr"]
        self.assertEqual(p["approved_at"], "2026-11-10")
        self.assertEqual(p["revision"], "2026-11-10.1")
        self.assertIn("1 Timothée 3.16", p["short_markdown"])
        self.assertIn("Actes 20.28", p["long_markdown"])
        self.assertIn("Jean 1.18", p["long_markdown"])
        self.assertIn("Marc 10.52", p["long_markdown"])
        self.assertIn("Job 34.37", p["long_markdown"])
        self.assertNotIn("certifié identique à un exemplaire", p["short_markdown"])
        self.assertNotIn("Ils ne suffisent toutefois pas", p["long_markdown"])
        self.assertTrue(all(url.startswith("https://")
                            for url in p["evidence_urls"].values()))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        doc = self.root / "docs/profiles/fr-segond-1910.md"
        doc.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "docs/profiles/fr-segond-1910.md", doc)
        self.document = doc
        folder = self.root / "modules/lsg-1910/profiles"
        folder.mkdir(parents=True)
        self.manifest = folder / "fr.json"
        shutil.copyfile(ROOT / "modules/lsg-1910/profiles/fr.json", self.manifest)
        self.moddir = folder.parent

    def _read(self, module=None):
        return approved_profiles(self.root, self.moddir, module or self.module)

    def _modify_receipt(self, change):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        change(data)
        self.manifest.write_text(json.dumps(data), encoding="utf-8")

    def test_stale_blob_digest_fails_closed(self):
        self.document.write_text(
            self.document.read_text(encoding="utf-8") + "\nUnapproved edit.\n",
            encoding="utf-8")
        with self.assertRaisesRegex(ProfileError, "changed since editorial approval"):
            self._read()

    def test_replacing_approved_text_with_draft_is_not_allowed(self):
        body = self.document.read_text(encoding="utf-8")
        body = body.replace("**EDITORIALLY APPROVED READER TEXT", "**DRAFT READER TEXT")
        self.document.write_text(body, encoding="utf-8")
        raw = self.document.read_bytes()
        sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        self._modify_receipt(lambda x: x.update(source_git_blob_sha1=sha))
        with self.assertRaisesRegex(ProfileError, "not editor-approved"):
            self._read()

    def test_missing_editorial_approval_fails(self):
        self._modify_receipt(lambda x: x.update(approved_by="PENDING"))
        with self.assertRaisesRegex(ProfileError, "human editorial approval"):
            self._read()

    def test_mismatched_sword_module_and_version_fails(self):
        self._modify_receipt(lambda x: x.update(module_version="0.1.1"))
        with self.assertRaisesRegex(ProfileError, "does not match released module"):
            self._read()

    def test_arbitrary_source_path_rejected(self):
        self._modify_receipt(lambda x: x.update(source_path="../../etc/passwd"))
        with self.assertRaisesRegex(ProfileError, "approved repository profile document"):
            self._read()

    def test_missing_or_reordered_markers_rejected(self):
        self._modify_receipt(lambda x: x["sections"].update(long="## Missing Header"))
        with self.assertRaisesRegex(ProfileError, "section markers"):
            self._read()

    def test_malformed_citation_rejected(self):
        self._modify_receipt(lambda x: x["evidence_urls"].update(
            one_timothy_3_16="http://insecure.invalid/"))
        with self.assertRaisesRegex(ProfileError, "source and citation URLs"):
            self._read()

    def test_unapproved_module_cannot_publish_profile(self):
        wrong = dict(self.module)
        wrong["quality"] = dict(wrong["quality"], status="draft")
        with self.assertRaisesRegex(ProfileError, "draft modules"):
            self._read(wrong)

    def test_unexpected_profile_file_rejected(self):
        (self.manifest.parent / "notes.txt").write_text("not approved", encoding="utf-8")
        with self.assertRaisesRegex(ProfileError, "unexpected profile file"):
            self._read()

    def test_duplicate_approval_receipt_fields_rejected(self):
        self._modify_receipt(lambda x: x.update(unapproved_extra="true"))
        with self.assertRaisesRegex(ProfileError, "unrecognized approval fields"):
            self._read()


if __name__ == "__main__":
    unittest.main()
