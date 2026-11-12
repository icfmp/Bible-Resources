"""Synthetic exact-source absent-verse note and native metadata checks."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lxml import etree
from audit_omitted_verse_notes import (
    OmittedNoteAuditError, source_cases, native_cases
)
from repair_osis_note_links import _source_note_nodes
from source_osis_inventory import _source_tree


def sample():
    original=b"""<?xml version='1.0' encoding='UTF-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'>
<osisText>
<div type='book' osisID='Matt'><chapter osisID='Matt.23'>
<verse sID='Matt.23.13' osisID='Matt.23.13'/>Text
<note n='a' type='explanation'>Earlier edition verse <reference osisRef='Matt.23.14'>14</reference> is absent.</note>
<verse eID='Matt.23.13'/></chapter></div>
<div type='book' osisID='Acts'><chapter osisID='Acts.8'>
<verse sID='Acts.8.36' osisID='Acts.8.36'/>Text
<note n='b' type='explanation'>Earlier edition verse <reference osisRef='Acts.8.37'>37</reference> is absent.</note>
<verse eID='Acts.8.36'/></chapter><chapter osisID='Acts.15'>
<verse sID='Acts.15.33' osisID='Acts.15.33'/>Text
<note n='c' type='explanation'>Earlier edition verse <reference osisRef='Acts.15.34'>34</reference> is absent.</note>
<verse eID='Acts.15.33'/></chapter></div>
</osisText></osis>
"""
    mapping=[
        ("Matt.23.13","Matt.23.14"),
        ("Acts.8.36","Acts.8.37"),
        ("Acts.15.33","Acts.15.34"),
    ]
    corrected=original
    for _host,target in mapping:
        corrected=corrected.replace(b" osisRef='"+target.encode()+b"'",b"")
    plan={"edits":[{"note_host":host,"note_index":1,
                   "old_target":target, "new_target":None,
                   "action":"disable_absent_target"}
                  for host,target in mapping]}
    return original,corrected,plan


def native_frames(xml):
    parsed=_source_tree(xml)
    notes=_source_note_nodes(parsed)
    return {host:etree.tostring(notes[host][0],encoding="UTF-8")
            for host in ("Matt.23.13","Acts.8.36","Acts.15.33")}


class OmittedVerseNotesTest(unittest.TestCase):
    def test_preserves_three_authored_notes_but_not_dead_targets(self):
        source,corrected,plan=sample()
        cases=source_cases(source,corrected,plan)
        self.assertEqual(len(cases),3)
        self.assertTrue(all(x["source_note_all_characters_equal"] for x in cases.values()))
        report=native_cases(cases,corrected,native_frames(corrected))
        self.assertEqual(report["missing_verse_note_count"],3)
        self.assertFalse(report["actual_reader_visual_state_verified"])
        self.assertTrue(report["no_omitted_verses_fabricated"])
        self.assertFalse(report["published"])

    def test_no_silent_source_reference_or_note_body_modification(self):
        original,corrected,plan=sample()
        wrong=corrected.replace(b"Earlier edition verse ",b"Earlier edition annotation ")
        self.assertNotEqual(wrong,corrected)
        with self.assertRaises(OmittedNoteAuditError):
            source_cases(original,wrong,plan)
        bad=corrected.replace(b"<reference>37</reference>",
                              b"<reference osisRef='Acts.8.37'>37</reference>")
        with self.assertRaises(OmittedNoteAuditError):
            source_cases(original,bad,plan)
        bad=corrected.replace(b">34</reference>",b">35</reference>")
        with self.assertRaises(OmittedNoteAuditError):
            source_cases(original,bad,plan)

    def test_compiled_note_caller_and_missing_navigation_cannot_drift(self):
        source,corrected,plan=sample()
        cases=source_cases(source,corrected,plan)
        native=native_frames(corrected)
        native["Acts.8.36"]=native["Acts.8.36"].replace(b"n=\"b\"",b"n=\"x\"")
        # Attribute quoting is compiler/serializer-dependent; set deterministically.
        note=etree.fromstring(native["Acts.8.36"])
        note.set("n","x")
        native["Acts.8.36"]=etree.tostring(note)
        with self.assertRaises(OmittedNoteAuditError):
            native_cases(cases,corrected,native)
        native=native_frames(corrected)
        note=etree.fromstring(native["Matt.23.13"])
        link=next(n for n in note.iter() if etree.QName(n).localname=="reference")
        link.set("osisRef","Matt.23.14")
        native["Matt.23.13"]=etree.tostring(note)
        with self.assertRaises(OmittedNoteAuditError):
            native_cases(cases,corrected,native)

    def test_missing_native_verse_or_conjectural_plan_rejected(self):
        original,corrected,plan=sample()
        cases=source_cases(original,corrected,plan)
        native=native_frames(corrected)
        native.pop("Acts.15.33")
        with self.assertRaises(OmittedNoteAuditError):
            native_cases(cases,corrected,native)
        plan["edits"][0]["new_target"]="Matt.23.15"
        with self.assertRaises(OmittedNoteAuditError):
            source_cases(original,corrected,plan)


if __name__=="__main__":
    unittest.main()
