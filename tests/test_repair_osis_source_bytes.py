"""Synthetic byte-exact OSIS source edits, no full-file XML serialization."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from lxml import etree
from repair_osis_source_bytes import (patch_exact_original, LexicalPatchError,
                                      patch_reviewed_osis_reference_attributes)
from repair_osis_note_links import propose as link_propose
from source_osis_inventory import OSIS, _source_tree

SOURCE = b"""<?xml version='1.0' encoding='UTF-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'>
<osisText><div type='book' osisID='Gen'><chapter osisID='Gen.1'>
<verse sID='Gen.1.1' osisID='Gen.1.1'/>Keep   exact poetic serialization
<note n='a'>Measurements <m>4.5 l</m> and <m>3.7 l</m>
<reference osisRef='Gen.9.1'>Other book</reference>
<reference osisRef='Gen.1.2'>intentionally absent</reference>.
</note><verse eID='Gen.1.1'/>
<verse sID='Gen.1.3' osisID='Gen.1.3'/>Second.<verse eID='Gen.1.3'/>
</chapter></div><div type='book' osisID='Exod'><chapter osisID='Exod.2'>
<verse osisID='Exod.2.1' sID='Exod.2.1'/>Other.<verse eID='Exod.2.1'/>
</chapter></div></osisText></osis>
"""


def plans(src=SOURCE):
    evidence="https://example.org/source-review"
    link={
        "schema_version":1,"purpose":"research_only_not_approved",
        "resource_id":"synthetic-test",
        "source_sha256":sha256(src).hexdigest(),
        "edits":[
            {"note_host":"Gen.1.1","note_index":1,"old_target":"Gen.9.1",
             "new_target":"Exod.2.1","action":"replace_target",
             "reason":"Other book is the original displayed label",
             "evidence_url":evidence},
            {"note_host":"Gen.1.1","note_index":1,"old_target":"Gen.1.2",
             "new_target":None,"action":"disable_absent_target",
             "reason":"An intentionally omitted source verse cannot be made up",
             "evidence_url":evidence},
        ],
    }
    serialized,_=link_propose(src,link)
    nodes=[n for n in _source_tree(serialized).iter() if n.tag==OSIS+"m"]
    inline={
        "schema_version":1,"purpose":"private_research_not_approved",
        "publisher_original_sha256":sha256(src).hexdigest(),
        "private_input_sha256":sha256(serialized).hexdigest(),
        "resource_id":"synthetic-test",
        "note_host":"Gen.1.1","note_index":1,
        "old_local_tag":"m","new_local_tag":"seg","new_type":"x-measure",
        "expected_count":2,
        "old_direct_text_sha256":[sha256((n.text or "").encode()).hexdigest() for n in nodes],
        "old_tail_sha256":[sha256((n.tail or "").encode()).hexdigest() for n in nodes],
        "reason":"Two unknown original tags mark measures and require standard OSIS segments",
        "evidence_url":evidence,
    }
    return link,inline


class TestLexicalSourcePatches(unittest.TestCase):
    def test_private_source_link_target_harmonization_preserves_all_other_bytes(self):
        root=etree.fromstring(SOURCE)
        refs=[n for n in root.iter() if n.tag==OSIS+"reference"]
        self.assertEqual(len(refs),2)
        edits=[]
        for node,target in zip(refs,("Exod.2.1","Gen.1.1 Exod.2.1")):
            original_book=next(
                a.get("osisID") for a in node.iterancestors()
                if a.tag==OSIS+"div" and a.get("type")=="book")
            edits.append({
                "original_line":node.sourceline,
                "source_book":original_book,
                "old_target":node.get("osisRef"),
                "new_target":target,
                "visible_label_sha256":sha256(
                    "".join(node.itertext()).strip().encode("utf-8")).hexdigest(),
                "evidence_url":"https://example.org/verified-label",
            })
        plan={"schema_version":1,
              "status":"research_only_private_not_release",
              "source_sha256":sha256(SOURCE).hexdigest(),
              "edits":edits}
        before=SOURCE
        result,receipt=patch_reviewed_osis_reference_attributes(
            before,plan,{"Gen.1.1","Exod.2.1"})
        expected=SOURCE.replace(b"osisRef='Gen.9.1'",b"osisRef='Exod.2.1'")
        expected=expected.replace(b"osisRef='Gen.1.2'",
                                  b"osisRef='Gen.1.1 Exod.2.1'")
        self.assertEqual(result,expected)
        self.assertEqual(receipt["exact_reference_attribute_only_changes"],2)
        self.assertTrue(receipt["entire_original_commentary_characters_unchanged"])
        self.assertEqual(before,SOURCE)
        tampered=dict(plan,edits=[dict(edits[0],original_line=9999),edits[1]])
        with self.assertRaises(LexicalPatchError):
            patch_reviewed_osis_reference_attributes(
                SOURCE,tampered,{"Gen.1.1","Exod.2.1"})
        tampered=dict(plan,edits=[dict(edits[0],new_target="Exod.2.99"),edits[1]])
        with self.assertRaises(LexicalPatchError):
            patch_reviewed_osis_reference_attributes(
                SOURCE,tampered,{"Gen.1.1","Exod.2.1"})
        tampered=dict(plan,edits=[dict(edits[0],
            visible_label_sha256="0"*64),edits[1]])
        with self.assertRaises(LexicalPatchError):
            patch_reviewed_osis_reference_attributes(
                SOURCE,tampered,{"Gen.1.1","Exod.2.1"})

    def test_real_indexed_osis_ranges_are_preserved_and_missing_verses_rejected(self):
        root=etree.fromstring(SOURCE)
        refs=[n for n in root.iter(OSIS+"reference")]
        edit={
            "original_line":refs[1].sourceline,
            "source_book":"Gen",
            "old_target":"Gen.1.2",
            "new_target":"Gen.1.1-Gen.1.3",
            "visible_label_sha256":sha256(
                "".join(refs[1].itertext()).strip().encode()).hexdigest(),
            "evidence_url":"https://example.org/reviewed-range",
        }
        plan={"schema_version":1,"status":"research_only_private_not_release",
              "source_sha256":sha256(SOURCE).hexdigest(),"edits":[edit]}
        full={"Gen.1.1","Gen.1.2","Gen.1.3","Exod.2.1"}
        revised,receipt=patch_reviewed_osis_reference_attributes(SOURCE,plan,full)
        self.assertEqual(receipt["exact_reference_attribute_only_changes"],1)
        self.assertEqual(revised,SOURCE.replace(
            b"osisRef='Gen.1.2'",b"osisRef='Gen.1.1-Gen.1.3'"))
        self.assertEqual("".join(etree.fromstring(revised).itertext()),
                         "".join(root.itertext()))
        # A range may not pretend a missing native verse is included.
        with self.assertRaises(LexicalPatchError):
            patch_reviewed_osis_reference_attributes(SOURCE,plan,full-{"Gen.1.2"})
        for invalid in ("Gen.1.3-Gen.1.1", "Gen.1.1-Exod.2.1",
                        "Gen.1.1-Gen.2.1", "Gen.1.1-Gen.1.9",
                        "Gen.1.1-Gen.1.1", "Gen.1.1-Gen.1.3-Gen.1.4",
                        "Gen.1.1-Gen.1.0", "Gen.1.1-Gen.1.202"):
            with self.subTest(invalid=invalid),self.assertRaises(LexicalPatchError):
                patch_reviewed_osis_reference_attributes(
                    SOURCE,dict(plan,edits=[dict(edit,new_target=invalid)]),full)

    def test_only_fourteen_original_byte_spans_changed_and_no_wholesale_serialization(self):
        link,inline=plans()
        result,report=patch_exact_original(SOURCE,link,inline)
        self.assertEqual(report["approved_byte_span_changes_only"],{
            "inline_start":2,"inline_end":2,"target_replace":1,"absent_target_remove":1})
        self.assertTrue(result.startswith(b"<?xml version='1.0' encoding='UTF-8'?>\n"))
        self.assertTrue(result.endswith(b"</chapter></div></osisText></osis>\n"))
        self.assertIn(b"Keep   exact poetic serialization\n",result)
        self.assertEqual("".join(_source_tree(SOURCE).itertext()),
                         "".join(_source_tree(result).itertext()))
        root=_source_tree(result)
        self.assertEqual([n.get("osisRef") for n in root.iter(OSIS+"reference")],
                         ["Exod.2.1",None])
        self.assertEqual(len(list(root.iter(OSIS+"seg"))),2)
        self.assertFalse(report["released"])

    def test_wrong_source_sha_and_inline_shapes_rejected(self):
        link,inline=plans()
        link["source_sha256"]="0"*64
        with self.assertRaises(ValueError):
            patch_exact_original(SOURCE,link,inline)
        link,inline=plans()
        inline["old_direct_text_sha256"][0]="0"*64
        with self.assertRaises(ValueError):
            patch_exact_original(SOURCE,link,inline)

    def test_alias_or_unexpected_unsupported_tag_fails_closed(self):
        changed=SOURCE.replace(b"<m>4.5 l</m>",b'<m style="a">4.5 l</m>')
        link,inline=plans(changed)
        with self.assertRaises(ValueError):
            patch_exact_original(changed,link,inline)


if __name__=="__main__":
    unittest.main()
