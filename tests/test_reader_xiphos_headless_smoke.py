"""Synthetic Xiphos headless smoke ZIP safety; never launch GUI in unit tests."""
import sys
from pathlib import Path
from hashlib import sha256
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from reader_xiphos_headless_smoke import (
    extract_pinned_preview,XiphosSmokeError,
)


class XiphosSmokeUnitTests(unittest.TestCase):
    def make_zip(self,folder):
        root=Path(folder)
        path=root/"candidate.zip"
        module="GenericPreview"
        slug=module.lower()
        with ZipFile(path,"w") as z:
            z.writestr(f"mods.d/{slug}.conf",
                       f"[{module}]\nDataPath=./modules/texts/ztext/{slug}/\n"
                       "ModDrv=zText\nVersification=Luther\n"
                       "Version=0.0.0-research\n")
            for section in ("ot","nt"):
                for ext in ("bzs","bzv","bzz"):
                    z.writestr(f"modules/texts/ztext/{slug}/{section}.{ext}",
                               b"private-synthetic-bytes")
        return path,sha256(path.read_bytes()).hexdigest()

    def test_strict_exact_zip_allows_isolated_test_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            root=Path(folder)/"payload"
            root.mkdir()
            actual=extract_pinned_preview(source,root,"GenericPreview",
                                           digest,"Luther")
            self.assertEqual(actual,root)
            self.assertEqual(len([item for item in root.rglob("*") if item.is_file()]),7)
            self.assertNotIn("private-synthetic-bytes",str(actual))

    def test_hash_and_scheme_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            out=Path(folder)/"out"
            out.mkdir()
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview","0"*64,"Luther")
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview",digest,"KJV")

    def test_traversal_member_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            source,digest=self.make_zip(folder)
            with ZipFile(source,"a") as archive:
                archive.writestr("../PRIVATE-OUTSIDE",b"untrusted")
            digest=sha256(source.read_bytes()).hexdigest()
            out=Path(folder)/"out"
            out.mkdir()
            with self.assertRaises(XiphosSmokeError):
                extract_pinned_preview(source,out,"GenericPreview",digest,"Luther")
            self.assertFalse((Path(folder)/"PRIVATE-OUTSIDE").exists())


if __name__=="__main__":
    unittest.main()
