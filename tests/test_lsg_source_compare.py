"""Offline tests for the actual eBible LSG original-source comparison."""
import io
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lsg_source_compare import scan_osis, compare_originals, read_source_xml
from pilot_preflight import PilotError

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"


class LsgSourceTests(unittest.TestCase):
    def test_osis_parses_authored_line_and_note_structure(self):
        raw=f"""<osis xmlns="{NS}"><osisText>
           <div type="book" osisID="Ps"><chapter osisID="Ps.23">
           <verse osisID="Ps.23.1"/><lg><l>A line</l><l>Second line</l></lg>
           <note type="crossReference"><reference osisRef="John.10.11"/></note>
           </chapter></div></osisText></osis>""".encode()
        structure,keys=scan_osis(raw)
        self.assertEqual(structure["book_count"],1)
        self.assertEqual(structure["unique_verse_keys"],1)
        self.assertEqual(structure["source_elements"]["l"],2)
        self.assertEqual(structure["poetry_line_counts_by_book"]["Ps"],2)
        self.assertEqual(keys,["Ps.23.1"])

    def test_cross_format_book_order_and_verse_missing_report(self):
        usfm={
            "_book_order":["GEN","PSA"],
            "_keys":[{(1,1),(1,2)},{(23,1),(23,2)}],
        }
        osis={"original_books":["Gen","Ps"]}
        result=compare_originals(usfm,osis,
            ["Gen.1.1","Gen.1.2","Ps.23.1","Ps.23.3"])
        self.assertEqual(result["status"],"verse_key_difference_needs_review")
        missing=result["books_with_different_verse_keys"][0]
        self.assertEqual(missing["usfm_only_first_20"],["Ps.23.2"])
        self.assertEqual(missing["osis_only_first_20"],["Ps.23.3"])

    def test_zip_rejects_multiple_osis_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"original.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("one.xml","<osis/>")
                z.writestr("two.xml","<osis/>")
            with self.assertRaisesRegex(PilotError,"Multiple osis"):
                read_source_xml(path)

    def test_malformed_or_external_doctype_fails_closed(self):
        raw=b'<!DOCTYPE osis SYSTEM "http://attacker.example/dtd"><osis/>'
        with self.assertRaisesRegex(PilotError,"DOCTYPE"):
            scan_osis(raw)


if __name__=="__main__":
    unittest.main()
