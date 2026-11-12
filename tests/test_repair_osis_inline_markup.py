"""Synthetic content-faithfulness and fail-closed inline OSIS repairs."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_osis_inventory import OSIS, _source_tree
from repair_osis_inline_markup import propose, InlineMarkupRepairError

ORIGINAL = b"""<?xml version='1.0' encoding='UTF-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'><osisText>
<div type='book' osisID='Ezek'><chapter osisID='Ezek.4'>
<verse osisID='Ezek.4.11' sID='Ezek.4.11'/>Secret Scripture text
<note n='a'>Unknown <m>4.5 l</m> or <m>3.7 l</m> exactly
<hi type='italic'>Display emphasis</hi></note>
<verse eID='Ezek.4.11'/>
</chapter></div></osisText></osis>"""


def make_plan(original=ORIGINAL):
    root=_source_tree(original)
    m=[n for n in root.iter() if n.tag==OSIS+"m"]
    return {
        "schema_version":1,
        "purpose":"private_research_not_approved",
        "publisher_original_sha256":"a"*64,
        "private_input_sha256":sha256(original).hexdigest(),
        "resource_id":"synthetic-test",
        "note_host":"Ezek.4.11","note_index":1,
        "old_local_tag":"m","new_local_tag":"seg","new_type":"x-measure",
        "expected_count":2,
        "old_direct_text_sha256":[sha256((n.text or "").encode()).hexdigest() for n in m],
        "old_tail_sha256":[sha256((n.tail or "").encode()).hexdigest() for n in m],
        "evidence_url":"https://example.org/review",
        "reason":"Independent example shows source m tags are invalid but measurement text is original",
    }


class TestInlineRepair(unittest.TestCase):
    def test_exactly_two_inline_tags_and_same_all_original_character_data(self):
        plan=make_plan()
        out,receipt=propose(ORIGINAL,plan)
        a,b=_source_tree(ORIGINAL),_source_tree(out)
        self.assertEqual("".join(a.itertext()),"".join(b.itertext()))
        self.assertEqual(len(list(a.iter())),len(list(b.iter())))
        self.assertEqual([n.tag for n in b.iter() if n.tag==OSIS+"seg"],
                         [OSIS+"seg",OSIS+"seg"])
        self.assertEqual([n.get("type") for n in b.iter(OSIS+"seg")],
                         ["x-measure","x-measure"])
        self.assertEqual(receipt["edit_count"],2)
        self.assertFalse(receipt["editorial_approval"])
        self.assertFalse(receipt["schema_validation_tested"])
        self.assertIn(b"<m>4.5 l</m>",ORIGINAL)
        self.assertNotIn(b"<m>",out)

    def test_wrong_original_or_pinned_input_rejected(self):
        plan=make_plan()
        plan["private_input_sha256"]="0"*64
        with self.assertRaises(InlineMarkupRepairError):
            propose(ORIGINAL,plan)
        with self.assertRaises(InlineMarkupRepairError):
            propose(ORIGINAL.replace(b"Secret",b"Edited"),make_plan())

    def test_wrong_host_ordinal_count_and_shape_rejected(self):
        for key,value in [
            ("note_host","Ezek.4.12"),
            ("note_index",2),
            ("note_index",True),
            ("expected_count",3),
            ("old_direct_text_sha256",["a"*64,"a"*64]),
            ("old_tail_sha256",["a"*64,"a"*64]),
            ("new_local_tag","hi"),
            ("new_type","unsafe-tag"),
            ("purpose","approved_for_release"),
        ]:
            with self.subTest(key=key,value=value),self.assertRaises(InlineMarkupRepairError):
                plan=make_plan()
                plan[key]=value
                propose(ORIGINAL,plan)

    def test_old_tag_elsewhere_in_book_blocks(self):
        src=ORIGINAL.replace(b"<hi type='italic'>Display emphasis</hi>",
                              b"<hi type='italic'>Display emphasis</hi><m>unreviewed</m>")
        plan=make_plan(src)
        plan["expected_count"]=2
        plan["old_direct_text_sha256"]=plan["old_direct_text_sha256"][:2]
        plan["old_tail_sha256"]=plan["old_tail_sha256"][:2]
        with self.assertRaises(InlineMarkupRepairError):
            propose(src,plan)

    def test_cannot_repair_nested_or_attributed_tag(self):
        for old,new in [
            (b"<m>4.5 l</m>",b"<m type='x'>4.5 l</m>"),
            (b"<m>4.5 l</m>",b"<m><hi>4.5 l</hi></m>"),
        ]:
            src=ORIGINAL.replace(old,new)
            with self.subTest(new=new),self.assertRaises(InlineMarkupRepairError):
                propose(src,make_plan(src))


if __name__=="__main__":
    unittest.main()
