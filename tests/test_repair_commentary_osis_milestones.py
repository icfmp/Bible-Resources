#!/usr/bin/env python3
"""Offline tests for source-pinned, byte-preserving commentary milestone edits."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from lxml import etree
from repair_commentary_osis_milestones import (
    MilestoneRepairError, repair_private_bytes
)

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
<osisText osisIDWork="Sample" xml:lang="fr"><div type="book" osisID="Prov">
<chapter sID="Prov.31" osisID="Prov.31" n="31"/>
<verse sID="Prov.31.10-33" osisID="{}" n="10-33"/>
<p>Le texte original est conservé — avec des <note n="1">notes, signes et 2 espaces.</note>
<reference osisRef="Gen.1.1">référence fidèle</reference>.</p>
<verse eID="Prov.31.10-33"/><chapter eID="Prov.31"/>
</div></osisText></osis>""".format(" ".join("Prov.31."+str(i) for i in range(10,34))).encode("utf-8")


def plan(raw, **overrides):
    from lxml import etree
    root=etree.fromstring(raw)
    section=next(n for n in root.iter() if isinstance(n.tag,str) and
                 n.tag.endswith("}verse") and n.get("sID"))
    row={"old_sid":"Prov.31.10-33","new_end_verse":31,
         "original_line":section.sourceline,
         "source_witness":"https://example.org/independent-edition"}
    row.update(overrides)
    return {"schema_version":1,
            "status":"RESEARCH_ONLY_PRIVATE_MILESTONE_CORRECTIONS",
            "source_sha256":sha256(raw).hexdigest(),
            "edits":[row]}


class MilestoneRepairTests(unittest.TestCase):
    def test_changes_only_four_values_of_two_matched_milestones(self):
        result, receipt=repair_private_bytes(FIXTURE,plan(FIXTURE))
        expected=FIXTURE.replace(b'Prov.31.10-33',b'Prov.31.10-31')
        expected=expected.replace(
            b' '.join(("Prov.31."+str(i)).encode() for i in range(10,34)),
            b' '.join(("Prov.31."+str(i)).encode() for i in range(10,32))
        ).replace(b'n="10-33"',b'n="10-31"')
        self.assertEqual(result,expected)
        self.assertEqual(receipt["corrected_source_verse_groups"],1)
        self.assertEqual(receipt["original_machine_attribute_values_replaced"],4)
        self.assertEqual(receipt["removed_invalid_verse_assignments"],2)
        self.assertTrue(receipt["all_source_text_notes_links_and_other_markup_identical"])
        self.assertFalse(receipt["original_text_or_module_released"])
        self.assertEqual(
            "".join(etree.fromstring(result).itertext()),
            "".join(etree.fromstring(FIXTURE).itertext())
        )

    def test_must_match_line_original_hash_and_paired_eid(self):
        invalid=plan(FIXTURE,original_line=1)
        with self.assertRaises(MilestoneRepairError):
            repair_private_bytes(FIXTURE,invalid)
        invalid=plan(FIXTURE)
        invalid["source_sha256"]=sha256(b"wrong").hexdigest()
        with self.assertRaises(MilestoneRepairError):
            repair_private_bytes(FIXTURE,invalid)
        broken=FIXTURE.replace(
            b'<verse eID="Prov.31.10-33"/>',
            b'<verse eID="Prov.31.10-32"/>'
        )
        with self.assertRaises(MilestoneRepairError):
            repair_private_bytes(broken,plan(broken))

    def test_rejects_non_reduction_and_duplicate_same_source_range(self):
        with self.assertRaises(MilestoneRepairError):
            repair_private_bytes(FIXTURE,plan(FIXTURE,new_end_verse=34))
        invalid=plan(FIXTURE)
        invalid["edits"]*=2
        with self.assertRaises(MilestoneRepairError):
            repair_private_bytes(FIXTURE,invalid)

    def test_keeps_unlisted_other_sibling_milestones(self):
        original=FIXTURE.replace(
            b'<verse eID="Prov.31.10-33"/>',
            b'<verse eID="Prov.31.10-33"/>'
            b'<verse sID="Prov.31.2" osisID="Prov.31.2" n="2"/>'
            b'<p>Unrelated source.</p><verse eID="Prov.31.2"/>')
        repaired,_=repair_private_bytes(original,plan(original))
        self.assertIn(b'<verse sID="Prov.31.2" osisID="Prov.31.2" n="2"/>',repaired)
        self.assertIn(b'<p>Unrelated source.</p>',repaired)


if __name__=="__main__":
    unittest.main()
