"""Minimum publication safety and reproducibility tests."""
import json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate import validate
from build import build
from audit_text import audit

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"modules").mkdir()
        (self.root/"schemas").mkdir()
        shutil.copyfile(ROOT/"schemas/module.schema.json",self.root/"schemas/module.schema.json")
        self.m=json.loads((ROOT/"examples/metadata.template.json").read_text())
    def create(self):
        d=self.root/"modules"/self.m["id"];d.mkdir()
        (d/"metadata.json").write_text(json.dumps(self.m),encoding="utf-8")
        return d
    def test_empty_repo(self):
        modules,errors=validate(self.root)
        self.assertEqual((modules,errors),([],[]))
        self.assertEqual(build(self.root,self.root/"dist","https://example.org/"),[])
    def test_draft_not_published(self):
        self.create()
        self.assertEqual(validate(self.root)[1],[])
        self.assertEqual(build(self.root,self.root/"dist","https://example.org/"),[])
    def test_unlicensed_approval_fails(self):
        self.m["quality"]["status"]="approved"
        self.create()
        self.assertTrue(validate(self.root)[1])
    def test_reject_wrong_language(self):
        self.m["language"]="Not a language"
        self.create()
        self.assertTrue(validate(self.root)[1])
    def test_scripture_audit_is_read_only(self):
        text="\n".join("> **1** Verse" for _ in range(6))
        self.assertIn("scripture_block_candidate",[x["type"] for x in audit(text)])
        self.assertEqual(len(text.splitlines()),6)
    def test_approved_modules_need_canonical_edition(self):
        self.m["quality"]["status"] = "approved"
        self.m["rights"]["redistribution_allowed"] = True
        self.m.pop("canonical_edition_id", None)
        self.create()
        errors = validate(self.root)[1]
        self.assertTrue(any("canonical_edition_id" in e for e in errors))

    def test_no_duplicate_canonical_edition_variant_in_catalogue(self):
        self.m["quality"]["status"] = "approved"
        self.m["rights"]["redistribution_allowed"] = True
        self.m["canonical_edition_id"] = "matthew-henry-en-concise-verified"
        self.create()
        self.m = dict(self.m, id="second-copy", sword_id="OtherCom")
        self.create()
        errors = validate(self.root)[1]
        self.assertTrue(any("duplicate curated edition variant" in e for e in errors))

    def test_same_canonical_edition_can_have_separate_reading_variant(self):
        self.m["quality"]["status"] = "approved"
        self.m["rights"]["redistribution_allowed"] = True
        self.m["canonical_edition_id"] = "matthew-henry-en-concise-verified"
        self.create()
        self.m = dict(self.m, id="optimized-copy", sword_id="OtherCom")
        self.m["quality"] = dict(self.m["quality"], edition="reader_optimized")
        self.m["rights"] = dict(self.m["rights"], derivatives_allowed=True)
        self.create()
        errors = validate(self.root)[1]
        self.assertFalse(any("duplicate curated edition variant" in e for e in errors))

    def test_identical_build(self):
        build(self.root,self.root/"dist","https://example.org/")
        one=(self.root/"dist/sword/mods.d.tar.gz").read_bytes()
        build(self.root,self.root/"dist","https://example.org/")
        self.assertEqual(one,(self.root/"dist/sword/mods.d.tar.gz").read_bytes())

if __name__=="__main__":unittest.main()
