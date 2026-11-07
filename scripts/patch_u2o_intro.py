#!/usr/bin/env python3
"""Patch pinned public-domain u2o converter's generic intro state logic.

The exact reviewed upstream bytes must match before applying any patch.
The upstream file itself is never changed. No Bible text is touched.

Problem: an introductory table row (\tr, \tc, \th) ends intro prematurely,
and a later explicit \ie still emits a closing </div> even though no intro
is open. Fix both generic state transitions in a separately hashed copy.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

EXPECTED_UPSTREAM_SHA256 = "a345a9904249af913c8e5ccf9d53839c20ae01dc8e6bf2b4294f3f23cd916ba8"

OLD_END = '''        if tmp[0][0:3] == r"\\ie":
            intro = False
            newlines.append(i[1])
            newlines.append("\\ufde1")
'''
NEW_END = '''        if tmp[0][0:3] == r"\\ie":
            newlines.append(i[1])
            if intro:
                newlines.append("\\ufde1")
            intro = False
'''
OLD_TABLE = '''            r"\\is",
            r"\\ie",
        }:
            if not intro:
'''
NEW_TABLE = '''            r"\\is",
            r"\\ie",
        } or (intro and tmp[0][:3] in {r"\\tr", r"\\tc", r"\\th"}):
            if not intro:
'''


OLD_NOTE_SPACE = '            .replace(" <note", "<note")\n'


OLD_POETRY_MOVE = "            if (\n                lines[i + 1].startswith(\"<verse sID\")\n                and lines[i - 1].startswith(\"<l \")\n                and lines[i - 2].startswith(\"<lg\")\n                and lines[i - 3] == \"</p>\"\n            ):\n                lines.insert(i - 3, lines.pop(i))\n"
NEW_POETRY_MOVE = "            if (\n                lines[i + 1].startswith(\"<verse sID\")\n                and lines[i - 1].startswith(\"<l \")\n                and lines[i - 2].startswith(\"<lg\")\n                and lines[i - 3] == \"</p>\"\n                # Reposition only across an EMPTY opening <l>. When the\n                # line contains quotation text, moving eID before the\n                # paragraph would orphan canonical words and references.\n                and re.fullmatch(r\"<l\\b[^<>]*>\", lines[i - 1]) is not None\n            ):\n                lines.insert(i - 3, lines.pop(i))\n"

class ConverterPatchError(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def patch(source: bytes) -> bytes:
    if sha(source)!=EXPECTED_UPSTREAM_SHA256:
        raise ConverterPatchError("Upstream converter SHA-256 changed: manual review required")
    original=source.decode("utf-8")
    for needle in (OLD_END,OLD_TABLE,OLD_NOTE_SPACE,OLD_POETRY_MOVE):
        if original.count(needle)!=1:
            raise ConverterPatchError("Reviewed converter patch anchor is missing or ambiguous")
    converted=(original.replace(OLD_END,NEW_END)
               .replace(OLD_TABLE,NEW_TABLE)
               .replace(OLD_NOTE_SPACE,"")
               .replace(OLD_POETRY_MOVE,NEW_POETRY_MOVE))
    if converted==original or converted.count("def markintroend(")!=1:
        raise ConverterPatchError("Generic introductory table patch not applied")
    return converted.encode("utf-8")


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(argv)
    if args.output.exists() or args.output.is_symlink() or args.original.is_symlink():
        raise SystemExit("Refusing to overwrite converter source/patch output")
    original=args.original.read_bytes()
    fixed=patch(original)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(fixed)
    print(f"u2o reviewed intro/note/verse-boundary fixes: original SHA-256 {sha(original)}, patched SHA-256 {sha(fixed)}")
    return 0


if __name__=="__main__":
    sys.exit(main())
