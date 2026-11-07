"""Offline tests for official-source-key probe, with no Bible text."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from probe_lsg_v11n import make_fixture, compile_probe, run
from pilot_preflight import PilotError


CONFIG={
  "schema_version":1,
  "schemes":["NRSV","Segond"],
  "cases":[
    {"source_usfx_book":"EXO","osis_book":"Exod","sword_book":"Exodus","chapter":7,"verses":[25,26,27,28,29]},
    {"source_usfx_book":"PSA","osis_book":"Ps","sword_book":"Psalms","chapter":3,"verses":[8,9]},
  ],
}
KEYS=[("EXO",7,i) for i in range(25,30)]+[("PSA",3,i) for i in (8,9)]


class LSGVersificationFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.fake=self.root/"osis2mod"
        self.fake.write_text("#!/usr/bin/env python3\n"
              "import os,sys\n"
              "from pathlib import Path\n"
              "assert sys.argv[-2]=='-v'\n"
              "assert sys.argv[-1] in ['NRSV','Segond']\n"
              "Path(sys.argv[1],'ot').write_text('SYNTHETIC',encoding='utf-8')\n"
              "if sys.argv[-1]=='NRSV':\n"
              "  print('INFO(V11N): Exod.7.26 is not in NRSV versification. Appending content to Exod.7.25')\n"
              "  print('INFO(V11N): Ps.3.9 is not in NRSV versification. Appending content to Ps.3.8')\n")
        self.fake.chmod(0o700)
        self.fake_reader=self.root/"diatheke"
        self.fake_reader.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "key=sys.argv[-1].split()\n"
            "book='Exod' if key[0]=='Exodus' else 'Ps'\n"
            "chapter,verse=key[-1].split(':')\n"
            "print(f'{sys.argv[-1]}:')\n"
            "print(f'SYNTHETIC_{book}_{chapter}_{verse}')\n"
        )
        self.fake_reader.chmod(0o700)
        self.archive=self.root/"usfx.zip"
        xml=b'<usfx><book id="EXO"><c id="7"/>'+b''.join(
            b'<v id="'+str(i).encode()+b'"/>TEST<ve id="'+str(i).encode()+b'"/>'
            for i in range(25,30))+b'</book><book id="PSA"><c id="3"/>'+b''.join(
            b'<v id="'+str(i).encode()+b'"/>TEST<ve id="'+str(i).encode()+b'"/>'
            for i in (8,9))+b'</book></usfx>'
        with zipfile.ZipFile(self.archive,"w") as z:
            z.writestr("fraLSG_usfx.xml",xml)

    def test_generated_fixture_has_synthetic_words_not_bible(self):
        xml,refs=make_fixture(CONFIG,KEYS)
        self.assertEqual(len(refs),7)
        self.assertIn(b"Exod.7.29",xml)
        self.assertIn(b"Ps.3.9",xml)
        self.assertIn(b"SYNTHETIC",xml)
        self.assertNotIn(b"Eternel",xml)

    def test_unknown_verse_is_not_silently_added(self):
        wrong=json.loads(json.dumps(CONFIG))
        wrong["cases"][0]["verses"]=[25,26,27,28,29,30]
        with self.assertRaisesRegex(PilotError,"not present"):
            make_fixture(wrong,KEYS)

    def test_official_command_and_explicit_scheme_are_used(self):
        fixture,_=make_fixture(CONFIG,KEYS)
        a=compile_probe(fixture,"NRSV",exe=str(self.fake))
        b=compile_probe(fixture,"Segond",exe=str(self.fake))
        self.assertTrue(a["module_created"])
        self.assertEqual(a["v11n_diagnostics"]["outside_versification_diagnostics"],2)
        self.assertEqual(b["v11n_diagnostics"],{})

    def test_generated_report_never_claims_the_actual_bible_is_fixed(self):
        result=run(self.archive,CONFIG,compiler=str(self.fake),reader=str(self.fake_reader))
        self.assertEqual(result["source_verse_keys"],7)
        self.assertTrue(result["preferred_scheme_not_approved"])
        self.assertTrue(result["schemes"][0]["reader_was_checked"])
        self.assertTrue(result["schemes"][0]["reader_key_evidence"][0]["marker_for_original_key_present"])
        self.assertTrue(result["schemes"][0]["reader_key_evidence"][0]["requested_reference_preserved"])
        self.assertFalse(result["real_module_recompiled"])
        self.assertFalse(result["source_text_modified"])
        self.assertEqual(result["schemes"][0]["sample_out_of_range_source_keys"],
                         ["Exod.7.26","Ps.3.9"])

    def test_invalid_schema_or_scheme_blocks(self):
        wrong=dict(CONFIG,schemes=["KJV","Segond"])
        with self.assertRaisesRegex(PilotError,"Unreviewed"):
            make_fixture(wrong,KEYS)


if __name__=="__main__":
    unittest.main()
