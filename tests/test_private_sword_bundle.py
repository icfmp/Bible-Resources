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
    _validate_package_files, audit_private_sword_installation
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

    def test_reader_probes_must_be_explicit_and_edition_appropriate(self):
        for probes in ((), [""] , ["Alpha" * 50], ["x"] * 129):
            with self.subTest(probes=probes[:2]):
                with self.assertRaises(PilotError):
                    audit_private_sword_installation(self.root, self.id, samples=probes)

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

    def test_repeated_standard_global_option_filters_are_allowed(self):
        self.conf.write_text(
            "[PrivateExample]\n"
            "DataPath=./modules/texts/rawtext/privateexample/\n"
            "ModDrv=RawText\n"
            "GlobalOptionFilter=OSISLemma\n"
            "GlobalOptionFilter=OSISFootnotes\n"
            "GlobalOptionFilter=OSISHeadings\n",
            encoding="utf-8")
        result=_validate_package_files(self.root,self.id)
        self.assertEqual(len(result),3)

    def test_standard_zcom4_commentary_with_nonterminated_datapath(self):
        # This is the ordinary source-based osis2mod -s 4 output shape;
        # do not add a module-specific exception just to pass packaging.
        self.conf.write_text(
            "[PrivateExample]\\n"
            "DataPath=./modules/comments/zcom4/privateexample\\n"
            "ModDrv=zCom4\\n"
            "BlockType=CHAPTER\\n"
            "SourceType=OSIS\\n"
            "Lang=en\\n",
            encoding="utf-8")
        for existing in self.data.iterdir():
            existing.unlink()
        self.data.rmdir()
        self.data=self.root/"modules/comments/zcom4/privateexample"
        self.data.mkdir(parents=True)
        for name in ("ot.czs","ot.czv","ot.czz",
                     "nt.czs","nt.czv","nt.czz"):
            (self.data/name).write_bytes(b"synthetic-zcom4-"+name.encode())
        entries=_validate_package_files(self.root,self.id)
        self.assertEqual(len(entries),7)
        archive=Path(self.temp.name)/"zcom4.zip"
        proof=_zip_private_module(self.root,self.id,archive)
        self.assertEqual(proof["module_file_count"],7)
        with ZipFile(archive) as z:
            self.assertEqual(len(z.namelist()),7)
            self.assertIn("mods.d/privateexample.conf",z.namelist())

    def test_zcom4_data_path_still_rejects_module_traversal(self):
        for bad in ("./modules/comments/../outside",
                    "./modules/comments/zcom4/privateexample/../../etc",
                    "/modules/comments/zcom4/privateexample"):
            with self.subTest(path=bad):
                self.conf.write_text(
                    "[PrivateExample]\\nDataPath="+bad+
                    "\\nModDrv=zCom4\\n", encoding="utf-8")
                with self.assertRaises(PilotError):
                    _validate_package_files(self.root,self.id)

    def test_duplicate_critical_config_fields_are_rejected(self):
        self.conf.write_text(
            "[PrivateExample]\n"
            "DataPath=./modules/texts/rawtext/privateexample/\n"
            "DataPath=./modules/texts/rawtext/privateexample/\n"
            "ModDrv=RawText\n"
            "GlobalOptionFilter=OSISLemma\n"
            "GlobalOptionFilter=OSISFootnotes\n",
            encoding="utf-8")
        with self.assertRaises(PilotError):
            _validate_package_files(self.root,self.id)

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
