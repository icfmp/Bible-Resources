"""Synthetic XML-defined SWORD v11n delta tests: no Bible original content."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from lsg_source_v11n_delta import build_v11n_delta
from pilot_preflight import PilotError


class OriginalSourceVerseGridTests(unittest.TestCase):
    def fixture(self):
        keys=[("JOB",1,1),("JOB",1,2),("MRK",1,1),
              ("MRK",1,2),("MRK",1,3)]
        mapping={"JOB":"Job","MRK":"Mark"}
        base={("Job",1):3,("Mark",1):2}
        order=["JOB","MRK"]
        return keys,mapping,base,order

    def build(self,**override):
        keys,names,baseline,order=self.fixture()
        args={"keys":keys,"names":names,"baseline":baseline,
              "book_order":order,"base_name":"Segond",
              "edition_id":"BRLSGTest","new_testament_first":"Mark"}
        args.update(override)
        return build_v11n_delta(**args)

    def test_xml_delta_only_lists_source_authenticated_chapter_maxima(self):
        raw,audit=self.build()
        root=ET.fromstring(raw)
        self.assertEqual(root.attrib,{"v11nID":"BRLSGTest","base":"Segond"})
        self.assertEqual([(x.get("osisID"),x.get("verseMax"))
                          for x in root.iter("chapter")],
                         [("Job.1","2"),("Mark.1","3")])
        self.assertEqual(audit["source_verse_key_count"],5)
        self.assertEqual(audit["changed_chapter_count"],2)
        self.assertTrue(audit["effective_reference_slot_set_exactly_matches_source"])
        self.assertFalse(audit["editorial_approval"])
        self.assertFalse(audit["published"])
        self.assertNotIn("chapter text",raw.decode())
        self.assertEqual(raw,self.build()[0])

    def test_missing_internal_verse_does_not_get_fabricated(self):
        with self.assertRaisesRegex(PilotError,"internal verse omissions"):
            self.build(keys=[("JOB",1,1),("MRK",1,1),("MRK",1,3)])

    def test_source_does_not_mysteriously_gain_other_chapters(self):
        with self.assertRaisesRegex(PilotError,"chapter sets differ"):
            self.build(baseline={("Job",1):3,("Mark",1):2,("Mark",2):1})

    def test_reject_duplicate_or_incomplete_authored_inputs(self):
        keys,names,base,order=self.fixture()
        for changes in (
            {"keys":keys+[keys[-1]]},
            {"names":{"JOB":"Job"}},
            {"names":{"JOB":"Job","MRK":"Job"}},
            {"book_order":["MRK","JOB","SYNTHETIC"]},
            {"base_name":"Not an identifier"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(PilotError):
                    self.build(**changes)

    def test_different_books_do_not_get_hardcoded_into_output(self):
        keys=[("GEN",1,1),("GEN",1,2),("MAT",1,1),("MAT",1,2)]
        names={"GEN":"Gen","MAT":"Matt"}
        baseline={("Gen",1):1,("Matt",1):3}
        raw,audit=build_v11n_delta(keys,names,baseline,base_name="Segond",
                                   edition_id="AnotherEdition",book_order=["GEN","MAT"])
        root=ET.fromstring(raw)
        self.assertEqual(
            [(c.get("collectionID"),b.get("osisID"))
             for c in root for b in c],
            [("1","Gen"),("2","Matt")])
        self.assertEqual(audit["changed_chapter_count"],2)


if __name__=="__main__":
    unittest.main()
