"""Offline regression for the generic U2O intro-table closing defect."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch as mock_patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import patch_u2o_intro as module


SOURCE=(
'''import re
from unicodedata import normalize

def markintroend(lines):
    newlines = []
    intro = False
    for i in enumerate(lines):
        tmp = i[1].partition(" ")
'''+module.OLD_END+
'''        elif tmp[0][:3] in {
            r"\\ib",
            r"\\il",
            r"\\im",
            r"\\io",
            r"\\ip",
            r"\\iq",
'''+module.OLD_TABLE+
'''                newlines.append("\\ufde0")
                intro = True
            newlines.append(i[1])
        elif intro:
            intro = False
            newlines.append(i[1])
            newlines.append("\\ufde1")
        else:
            newlines.append(i[1])
    if intro:
        newlines.append("\\ufde1")
    return newlines
'''
+ '''
def note_cleanup(text):
    return (
        text
''' + module.OLD_NOTE_SPACE +
'''    )
'''

+ '''
import re
from contextlib import suppress

def relocate_poetry_end(lines):
    for i in (_ for _ in range(len(lines)) if lines[_].startswith("<verse eID")):
        with suppress(IndexError):
''' + module.OLD_MULTILINE_MOVE + module.OLD_POETRY_MOVE +
'''    return lines
'''

+ '''
# Minimal executable USFM note extraction using the pinned upstream anchors.
NOTERE = re.compile(
    r"""
        (?P<tag>\\\\x)
        \s+
''' + module.OLD_CALLER_CAPTURE +
'''     \s+
        (?P<osis>.*?)
        (?P=tag)\*
    """, re.U | re.VERBOSE | re.S
)

def note_replace(text):
    def simplerepl(match):
        tag=('<note type="crossReference">','</note>')
        notetext=match.group("osis").replace("\\n"," ")
''' + module.OLD_CALLER_OUTPUT +
'''    return NOTERE.sub(simplerepl,text)
'''

+ '''
CHAPFIXRE = re.compile(
''' + module.OLD_CHAP_REGEX +
'''    re.U,
)

def reflow(text):
    return CHAPFIXRE.sub("\ufdd0\\1\ufdd0", text)

def doconvert(text: str, log_level: int) -> tuple[str, ...]:
    newtext=text
    return (reflow(newtext),)
'''
).encode("utf-8")


def evaluate(source):
    ns={}
    exec(compile(source,"reviewed-generic-intro-fixture.py","exec"),ns)
    return ns["markintroend"]


class U2OIntroTests(unittest.TestCase):
    def test_real_generic_bug_is_reproduced_then_fixed(self):
        source=SOURCE
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(source).hexdigest()):
            result=module.patch(source)
        first=evaluate(source)
        fixed=evaluate(result)
        lines=["\\ip Intro text","\\tr table row","\\tc1 first cell",
               "\\tc2 second cell","\\ip More intro",
               "\\tr second table row","\\tc1 value","\\ie","\\c 1"]
        before=first(lines)
        after=fixed(lines)
        # Original closes before a table and again at the final explicit \ie.
        self.assertGreater(before.count("\ufde1"),after.count("\ufde1"))
        self.assertEqual(after.count("\ufde0"),1)
        self.assertEqual(after.count("\ufde1"),1)
        self.assertEqual(after[:2],["\ufde0",lines[0]])
        self.assertIn(lines[-2],after)
        self.assertEqual([x for x in after if x in lines],lines)
        self.assertNotEqual(source,result)

    def test_note_preceding_space_is_not_removed(self):
        source=SOURCE
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(source).hexdigest()):
            fixed=module.patch(source)
        before={}
        after={}
        exec(compile(source,"original-fixture.py","exec"),before)
        exec(compile(fixed,"patched-fixture.py","exec"),after)
        sample='Au <note type="crossReference">citation</note>commencement'
        self.assertNotEqual(before["note_cleanup"](sample),sample)
        self.assertEqual(after["note_cleanup"](sample),sample)
        self.assertNotIn(module.OLD_NOTE_SPACE.encode(),fixed)

    def test_verse_end_stays_after_text_bearing_poetry_line(self):
        original=SOURCE
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(original).hexdigest()):
            fixed=module.patch(original)
        before={}
        after={}
        exec(compile(original,"unpatched-verse-fixture.py","exec"),before)
        exec(compile(fixed,"reviewed-verse-fixture.py","exec"),after)
        quoted=[
            "</p>","<lg>",
            '<l level="1"><w lemma="strong:G1">Quoted words</w>.</l>',
            '<verse eID="Acts.13.35"/>',
            '<verse sID="Acts.13.36"/>',
        ]
        broken=before["relocate_poetry_end"](quoted.copy())
        preserved=after["relocate_poetry_end"](quoted.copy())
        self.assertTrue(broken[0].startswith("<verse eID"))
        self.assertEqual(preserved,quoted)
        # Keep the original legitimate movement when no verse text is crossed.
        empty=[
            "</p>","<lg>",'<l level="1">',
            '<verse eID="Acts.13.35"/>','<verse sID="Acts.13.36"/>',
        ]
        self.assertTrue(after["relocate_poetry_end"](empty.copy())[0].startswith("<verse eID"))

    def test_end_marker_never_skips_last_text_bearing_poetry_line(self):
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(SOURCE).hexdigest()):
            reviewed=module.patch(SOURCE)
        before={}
        after={}
        exec(compile(SOURCE,"original-multiline.py","exec"),before)
        exec(compile(reviewed,"reviewed-multiline.py","exec"),after)
        verse=[
            '<l level="1"><w lemma="strong:H1">First line</w>.</l>',
            '<l level="1"><w lemma="strong:H2">Final line</w>.</l>',
            '<verse eID="Isa.25.2"/>',
            '<verse sID="Isa.25.3"/>',
        ]
        self.assertNotEqual(before["relocate_poetry_end"](verse.copy()),verse)
        self.assertEqual(after["relocate_poetry_end"](verse.copy()),verse)


    def test_original_note_caller_is_preserved_and_xml_escaped(self):
        source=SOURCE
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(source).hexdigest()):
            reviewed=module.patch(source)
        original={}
        patched={}
        exec(compile(source,"note-callout-original.py","exec"),original)
        exec(compile(reviewed,"note-callout-reviewed.py","exec"),patched)
        for glyph, expected in (("a",'n="a"'),("+",'n="+"'),("&",'n="&amp;"')):
            raw="\\x "+glyph+" \\xo 1.1 \\xt Ref 1:1.\\x*"
            before=original["note_replace"](raw)
            after=patched["note_replace"](raw)
            self.assertNotIn(" n=",before)
            self.assertIn(expected,after)
            self.assertEqual(before.replace('>',' '+expected+'>',1),after)
            self.assertIn("Ref 1:1.",after)


    def test_chapter_separator_does_not_absorb_poetry_paragraph_newline(self):
        source=SOURCE
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(source).hexdigest()):
            reviewed=module.patch(source)
        before={}
        after={}
        exec(compile(source,"original-chap-regex.py","exec"),before)
        exec(compile(reviewed,"reviewed-chap-regex.py","exec"),after)
        original="\\c 11\n\\q1\n\\v 1 First words\n\\q1 Second words"
        old_output=before["doconvert"](original,0)[0]
        new_output=after["doconvert"](original,0)[0]
        self.assertIn("\ufdd0\\c 11\ufdd0\\q1",old_output)
        self.assertIn("\ufdd0\\c 11\ufdd0\n\\q1",new_output)
        self.assertEqual(old_output.replace("\ufdd0\\q1","\ufdd0\n\\q1"),
                         new_output)
        self.assertEqual(before["doconvert"]("\\c 5  \n\\p Prose",0)[0]
                         .count("\n"),0)
        self.assertIn("\n\\p Prose",
                      after["doconvert"]("\\c 5  \n\\p Prose",0)[0])

    def test_upstream_sha_change_fails_closed(self):
        with self.assertRaisesRegex(module.ConverterPatchError,"SHA-256 changed"):
            module.patch(SOURCE)

    def test_missing_or_ambiguous_anchor_fails_closed(self):
        source=(SOURCE+module.OLD_END.encode())
        with mock_patch.object(module,"EXPECTED_UPSTREAM_SHA256",hashlib.sha256(source).hexdigest()):
            with self.assertRaisesRegex(module.ConverterPatchError,"missing or ambiguous"):
                module.patch(source)


if __name__=="__main__":
    unittest.main()
