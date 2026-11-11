"""Test-only SWORD ZIP hardening: never reconstruct or modify source text."""
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from publisher_osis_preview_package import (
    package_preview,PreviewPackageError,COMPRESSED_FILES,sha_file,
)


def fake_payload(path, extra=False):
    base=path/"payload"
    conf=base/"mods.d/jnd2024research.conf"
    conf.parent.mkdir(parents=True)
    conf.write_text(
        "[JND2024Research]\n"
        "DataPath=./modules/texts/ztext/jnd2024research/\n"
        "ModDrv=zText\n"
        "Encoding=UTF-8\n"
        "Versification=Luther\n"
        "Version=0.0.0-research\n"
        "Description=Publisher research-only test\n",
        encoding="utf-8")
    data=base/"modules/texts/ztext/jnd2024research"
    data.mkdir(parents=True)
    for name in COMPRESSED_FILES:
        (data/name).write_bytes(b"PRIVATE-BYTES-"+name.encode())
    if extra:
        (data/"evil-private.xml").write_text("PRIVATE SCRIPTURE")
    return base


class PreviewPackageTests(unittest.TestCase):
    def test_zip_is_exact_deterministic_and_reinstallable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=fake_payload(root)
            preview=root/"preview.zip"
            proof=package_preview(source,preview,"JND2024Research","Luther")
            self.assertTrue(proof["all_module_files_byte_identical_to_audited_candidate"])
            self.assertFalse(proof["release_approved"])
            self.assertTrue(proof["preview_only"])
            self.assertFalse(proof["published"])
            self.assertEqual(proof["zip_sha256"],sha_file(preview))
            with ZipFile(preview) as zipped:
                self.assertEqual(len(zipped.namelist()),7)
                self.assertIsNone(zipped.testzip())
                for name in zipped.namelist():
                    self.assertEqual(zipped.read(name),(source/name).read_bytes())
            copy=root/"second.zip"
            package_preview(source,copy,"JND2024Research","Luther")
            self.assertEqual(preview.read_bytes(),copy.read_bytes())
            self.assertNotIn("PRIVATE",str(proof))

    def test_reject_unexpected_files_no_zip_leaked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=fake_payload(root,extra=True)
            preview=root/"preview.zip"
            with self.assertRaises(PreviewPackageError):
                package_preview(source,preview,"JND2024Research","Luther")
            self.assertFalse(preview.exists())

    def test_reject_incorrect_identity_unapproved_versification_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=fake_payload(root)
            preview=root/"preview.zip"
            for invalid in ("OtherModule","../escape",""):
                with self.assertRaises(PreviewPackageError):
                    package_preview(source,preview,invalid,"Luther")
            with self.assertRaises(PreviewPackageError):
                package_preview(source,preview,"JND2024Research","DarbyFr")
            package_preview(source,preview,"JND2024Research","Luther")
            with self.assertRaises(PreviewPackageError):
                package_preview(source,preview,"JND2024Research","Luther")

    def test_reject_symlinked_module_file_and_missing_ztext_segment(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=fake_payload(root)
            data=source/"modules/texts/ztext/jnd2024research"
            (data/"ot.bzz").unlink()
            with self.assertRaises(PreviewPackageError):
                package_preview(source,root/"preview.zip","JND2024Research","Luther")
            (data/"ot.bzz").symlink_to(data/"nt.bzz")
            with self.assertRaises(PreviewPackageError):
                package_preview(source,root/"preview.zip","JND2024Research","Luther")


if __name__=="__main__":
    unittest.main()
