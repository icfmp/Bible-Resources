"""Independent source/content corruption fixtures (no published text)."""
import io,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from research.bible.original_authorial_content_parity import verify_numbered_content,usfm_numbered_content

USFX=b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/><w s="H1">alpha</w> <x caller="a"><xo>1.1</xo><xt>old</xt></x> <w s="H2">beta</w><ve/></p></book></usfx>'
OSIS=b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText osisIDWork="test" osisRefWork="Bible"><div type="book" osisID="Gen"><chapter osisID="Gen.1" sID="Gen.1"/><p><verse osisID="Gen.1.1" sID="Gen.1.1"/><w lemma="strong:H1">alpha</w> <note n="a" type="crossReference"><reference type="annotateRef" subType="x-origin">1.1</reference><reference>old</reference></note> <w lemma="strong:H2">beta</w><verse eID="Gen.1.1"/></p><chapter eID="Gen.1"/></div></osisText></osis>'
MAP={"GEN":"Gen"}
def archive(text):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:z.writestr("book.usfm",text)
    b.seek(0)
    return zipfile.ZipFile(b)
class OriginalContentTests(unittest.TestCase):
    def test_exact_body_note_and_strong(self):
        with archive(r'\id GEN'+ '\n'+r'\c 1 \v 1 \w alpha|strong="H1"\w* \x a \xo 1.1 \xt old\x* \w beta|strong="H2"\w*') as z:
            result=verify_numbered_content(USFX,OSIS,MAP,usfm_archive=z)
        self.assertTrue(result["all_supported_content_checks_equal"],result)
    def test_repaired_note_requires_exact_full_body(self):
        changed=OSIS.replace(b'>old<',b'>new<')
        self.assertFalse(verify_numbered_content(USFX,changed,MAP)["all_supported_content_checks_equal"])
        self.assertTrue(verify_numbered_content(USFX,changed,MAP,{("Gen.1.1","a"):("old","new")})["all_supported_content_checks_equal"])
        with self.assertRaises(ValueError):
            verify_numbered_content(USFX,changed.replace(b'>1.1<',b'>9.9<'),MAP,{("Gen.1.1","a"):("old","new")})
    def test_changed_text_note_anchor_and_lemma_detected(self):
        for change in (OSIS.replace(b'alpha',b'other'),OSIS.replace(b'strong:H1',b'strong:H2'),OSIS.replace(b'n="a"',b'n="b"'),OSIS.replace(b'alpha</w> <note',b'alpha</w> x<note')):
            self.assertFalse(verify_numbered_content(USFX,change,MAP)["all_supported_content_checks_equal"])
    def test_section_title_does_not_end_resumed_verse(self):
        with archive(r'\id GEN'+ '\n'+r'\c 1 \v 1 alpha \s1 heading \p beta') as z:
            body,_,_=usfm_numbered_content(z,MAP)
        self.assertEqual("".join(body["Gen.1.1"].split()),"alphabeta")
    def test_unknown_usfm_marker_fails(self):
        with archive(r'\id GEN'+ '\n'+r'\c 1 \v 1 alpha \unknown beta') as z,self.assertRaises(ValueError):
            usfm_numbered_content(z,MAP)
