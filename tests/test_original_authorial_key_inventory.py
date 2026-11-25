"""Synthetic original numbering fixtures: labels never expanded."""
import sys
from pathlib import Path
import io,zipfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from research.bible.original_authorial_key_inventory import usfm,usfx,compare,summary

def archive(entries):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        for k,v in entries.items(): z.writestr(k,v)
    b.seek(0)
    return zipfile.ZipFile(b)

class AuthorialKeyTests(unittest.TestCase):
    def test_exact_bridge_suffix_and_punctuation_after_note(self):
        with archive({"book.usfm":r"\id GEN"+ "\n"+r"\c 1 \v 1a text \f + \ft note\f*, \v 2-3 text"}) as z:
            a,_=usfm(z)
        with archive({"chosen.xml":'<usfx><book id="GEN"><c id="1"/><v id="1a"/>text<v id="2-3"/>text</book></usfx>',"metadata.xml":"<metadata/>"}) as z:
            b,_=usfx(z,"chosen.xml")
        self.assertEqual(a,{"GEN":[("1","1a"),("1","2-3")]})
        self.assertTrue(compare(a,b)["ordered_labels_within_every_book_equal"])
        self.assertEqual(summary(a)["raw_verse_labels"],2)
        self.assertEqual(summary(a)["bridges"],1)
        self.assertEqual(summary(a)["suffixes"],1)
    def test_duplicate_or_missing_numbering_fails(self):
        for source in (r"\id GEN \c 1 \v 1 x \v 1 y",r"\id GEN \v 1 x",r"\id GEN \c 1 \v 4-2 x",r"\id GEN \c 1 \v 1 \f + note \v 2"):
            with archive({"book.usfm":source}) as z, self.assertRaises(ValueError):
                usfm(z)
    def test_namespaced_usfx_and_explicit_member(self):
        with archive({"actual.xml":'<usfx xmlns="urn:test"><book id="GEN"><c id="1"/><v id="2a"/></book></usfx>',"other.xml":"<metadata/>"}) as z:
            self.assertEqual(usfx(z,"actual.xml")[0],{"GEN":[("1","2a")]})
            with self.assertRaises(ValueError): usfx(z,"missing.xml")
    def test_duplicate_usfx_labels_and_dtd_fail(self):
        for xml in ('<usfx><book id="GEN"><c id="1"/><v id="1"/><v id="1"/></book></usfx>','<!DOCTYPE usfx><usfx/>'):
            with archive({"x.xml":xml}) as z,self.assertRaises(ValueError): usfx(z,"x.xml")
    def test_order_not_just_set(self):
        self.assertFalse(compare({"GEN":[("1","1"),("1","2")]},{"GEN":[("1","2"),("1","1")]})["ordered_labels_within_every_book_equal"])
