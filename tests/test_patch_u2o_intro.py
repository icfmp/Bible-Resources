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
'''def markintroend(lines):
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
