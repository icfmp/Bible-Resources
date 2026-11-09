"""Private stock-SWORD ZIP packaging checks with synthetic module files."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from private_sword_bundle import (
    _zip_private_module, _extract_into_isolated_sword_home,
    _validate_package_files
)
from pilot_preflight import PilotError


class PrivateSwordBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"source"
        self.id="PrivateExample"
        self.conf=self.root/"mods.d"/"privateexample.conf"
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text(
            "[PrivateExample]\n"
            "DataPath=./modules/texts/rawtext/privateexample/\n"
            "ModDrv=RawText\n"
            "Lang=fr\n",encoding="utf-8")
        self.data=self.root/"modules/texts/rawtext/privateexample"
        self.data.mkdir(parents=True)
        (self.data/"ot").write_bytes(b"\x01\x02")
        (self.data/"nt").write_bytes(b"\x03\x04")

    def test_bundle_is_reproducible_standard_layout_and_exact_bytes(self):
        first=Path(self.temp.name)/"first.zip"
        second=Path(self.temp.name)/"second.zip"
        a=_zip_private_module(self.root,self.id,first)
        b=_zip_private_module(self.root,self.id,second)
        self.assertEqual(a["zip_sha256"],b["zip_sha256"])
        self.assertEqual(a["module_file_count"],3)
        target=Path(self.temp.name)/"isolated"
        _extract_into_isolated_sword_home(first,target,a["source_file_sha256"])
        self.assertEqual(
            set(a["source_file_sha256"]),
            set(n for n,_ in _validate_package_files(target,self.id)))
        with ZipFile(first) as z:
            self.assertEqual(z.namelist(),sorted(z.namelist()))
            self.assertTrue(all(name.startswith(("mods.d/","modules/"))
                                for name in z.namelist()))

    def test_unsafe_absolute_or_parent_data_path_rejected(self):
        for path in ("../../etc/","./modules/../outside/",
                     "/tmp/modules/"):
            with self.subTest(path=path):
                self.conf.write_text(
                    "[PrivateExample]\nDataPath="+path+
                    "\nModDrv=RawText\n",encoding="utf-8")
                with self.assertRaises(PilotError):
                    _validate_package_files(self.root,self.id)

    def test_wrong_module_id_and_missing_payload_block(self):
        with self.assertRaises(PilotError):
            _validate_package_files(self.root,"Wrong")
        for entry in self.data.iterdir():
            entry.unlink()
        with self.assertRaises(PilotError):
            _validate_package_files(self.root,self.id)

    def test_file_symlink_rejected(self):
        target=self.data/"nt"
        target.unlink()
        target.symlink_to(self.data/"ot")
        with self.assertRaises(PilotError):
            _validate_package_files(self.root,self.id)

    def test_modification_to_installed_binary_is_detected(self):
        archive=Path(self.temp.name)/"candidate.zip"
        manifest=_zip_private_module(self.root,self.id,archive)
        bad=dict(manifest["source_file_sha256"])
        k=next(name for name in bad if name.startswith("modules/"))
        bad[k]="0"*64
        with self.assertRaises(PilotError):
            _extract_into_isolated_sword_home(
                archive,Path(self.temp.name)/"bad-install",bad)


if __name__=="__main__":
    unittest.main()
