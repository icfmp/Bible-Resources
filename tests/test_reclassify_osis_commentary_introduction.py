#!/usr/bin/env python3
"""Source-faithful, generic OSIS introduction reclassification fixtures."""
from hashlib import sha256
from pathlib import Path
import sys
import unittest

from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from reclassify_osis_commentary_introduction import (
    IntroRepairError, repair_private_bytes,
)

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"
SOURCE=("""<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="%s"><osisText osisIDWork="Example" xml:lang="fr">
<div type="book" osisID="Gen" canonical="true">
<chapter sID="Gen.1" osisID="Gen.1" n="1"/>
<p><verse sID="Gen.1.1" osisID="Gen.1.1" n="1"/>
Chapter foreword — préface originale. <hi type="italic">Ω</hi></p>
<div type="introduction"><p subType="x-introduction">
Further introduction: <reference osisRef="Exod.1.1">see Exodus</reference>
<note n="a">Footnote, unchanged.</note>
<verse eID="Gen.1.1"/><verse sID="Gen.1.1-2" osisID="Gen.1.1 Gen.1.2" n="1-2"/></p></div>
<p>Separate authored exposition 1–2. <verse eID="Gen.1.1-2"/></p>
<chapter eID="Gen.1"/>
</div></osisText></osis>""" % NS).encode("utf-8")


def reviewed(raw=SOURCE):
    root=etree.fromstring(raw)
    def line(attr,value):
        found=root.xpath(
            "//*[local-name()='verse' and @%s='%s']" % (attr,value))
        assert len(found)==1
        return found[0].sourceline
    div=root.xpath("//*[local-name()='div' and @type='introduction']")
    assert len(div)==1
    return {
        "schema_version":1,
        "status":"PRIVATE_REVIEWED_CHAPTER_INTRO_RECLASSIFICATION",
        "source_sha256":sha256(raw).hexdigest(),
        "source_text_edit_approved":False,
        "chapter_introduction_remapping_approved":True,
        "old_intro_source_sid":"Gen.1.1",
        "following_commentary_source_sid":"Gen.1.1-2",
        "old_intro_opening_line":line("sID","Gen.1.1"),
        "old_intro_closing_line":line("eID","Gen.1.1"),
        "existing_introduction_div_line":div[0].sourceline,
        "following_section_opening_line":line("sID","Gen.1.1-2"),
    }


class IntroductionMoveTests(unittest.TestCase):
    def test_existing_osis_introduction_wraps_all_original_preface_not_verse_section(self):
        plan=reviewed()
        revised,receipt=repair_private_bytes(SOURCE,plan)
        root=etree.fromstring(revised)
        orig=etree.fromstring(SOURCE)
        self.assertEqual("".join(root.itertext()),"".join(orig.itertext()))
        intro=root.xpath("//*[local-name()='div' and @type='introduction']")[0]
        self.assertEqual([etree.QName(child).localname for child in intro],["p","p"])
        self.assertIn("Chapter foreword", "".join(intro.itertext()))
        self.assertIn("Further introduction", "".join(intro.itertext()))
        self.assertNotIn("Separate authored exposition", "".join(intro.itertext()))
        self.assertEqual(len(root.xpath("//*[local-name()='verse' and @sID='Gen.1.1']")),0)
        self.assertEqual(len(root.xpath("//*[local-name()='verse' and @eID='Gen.1.1']")),0)
        section=root.xpath("//*[local-name()='verse' and @sID='Gen.1.1-2']")[0]
        self.assertIs(section.getparent(),intro.getparent())
        self.assertIs(section.getprevious(),intro)
        self.assertEqual(section.get("osisID"),"Gen.1.1 Gen.1.2")
        self.assertEqual(receipt["removed_source_verse_milestone_count"],2)
        self.assertTrue(receipt["all_original_source_text_whitespace_and_punctuation_identical"])
        self.assertTrue(receipt["all_original_source_notes_references_and_titles_identical"])
        self.assertFalse(receipt["published"])
        self.assertEqual(sha256(revised).hexdigest(),receipt["candidate_sha256"])
        self.assertEqual(repair_private_bytes(SOURCE,plan)[0],revised)

    def test_wrong_checksum_line_or_approval_fails_closed(self):
        good=reviewed()
        cases=[
            dict(good,source_sha256="0"*64),
            dict(good,old_intro_opening_line=999),
            dict(good,existing_introduction_div_line=1),
            dict(good,chapter_introduction_remapping_approved=False),
            dict(good,source_text_edit_approved=True),
            dict(good,following_commentary_source_sid="Gen.2.1-2"),
        ]
        for op in cases:
            with self.subTest(op=op),self.assertRaises(IntroRepairError):
                repair_private_bytes(SOURCE,op)

    def test_missing_original_introduction_markup_fails_without_editing(self):
        altered=SOURCE.replace(b'<div type="introduction">',b'<div type="section">')
        plan=reviewed()
        plan["source_sha256"]=sha256(altered).hexdigest()
        with self.assertRaises(IntroRepairError):
            repair_private_bytes(altered,plan)


if __name__=="__main__":
    unittest.main()
