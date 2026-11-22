"""Regression tests for the shared isolated stock SWORD Bible installer."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research.bible.private_sword_install import _safe_single_module, PrivateSwordInstallError
from diff_sword_snapshots import SnapshotError


class PrivateSwordInstallTests(unittest.TestCase):
    def test_safe_zip_to_private_sword_root_without_changing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "module.zip"
            config = (b"[Example]\nVersion=1.0\nModDrv=zText\n"
                      b"Versification=KJV\n")
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", config)
                z.writestr("modules/texts/ztext/example/ot", b"PRIVATE-FIXTURE")
            before = archive.read_bytes()
            details = _safe_single_module(archive, root / "isolated-module")
            self.assertEqual(details["module_id"], "Example")
            self.assertEqual(details["original_version"], "1.0")
            self.assertEqual(details["original_driver"], "zText")
            self.assertEqual(details["original_versification"], "KJV")
            self.assertEqual(archive.read_bytes(), before)
            self.assertEqual((root / "isolated-module/payload/"
                              "modules/texts/ztext/example/ot").read_bytes(),
                             b"PRIVATE-FIXTURE")

    def test_non_bible_module_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "module.zip"
            config = b"[Example]\nVersion=1.0\nModDrv=zCom\n"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", config)
                z.writestr("modules/comments/zcom/example/ot", b"PRIVATE")
            with self.assertRaisesRegex(PrivateSwordInstallError, "supported Bible"):
                _safe_single_module(archive, root / "isolated")

    def test_unsafe_zip_path_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "malicious.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", b"[Example]\nVersion=1.0\nModDrv=zText\n")
                z.writestr("../leak", b"SECRET")
                z.writestr("modules/texts/ztext/example/ot", b"PRIVATE")
            with self.assertRaises(SnapshotError):
                _safe_single_module(archive, root / "isolated")
            self.assertFalse((root / "leak").exists())


if __name__ == "__main__":
    unittest.main()
