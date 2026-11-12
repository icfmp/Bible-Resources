"""Synthetic byte-exact OSIS source edits, no full-file XML serialization."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from lxml import etree
from repair_osis_source_bytes import patch_exact_original, LexicalPatchError
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
