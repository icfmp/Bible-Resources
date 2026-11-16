#!/usr/bin/env python3
"""Generate an *experimental* OSIS commentary from SHA-pinned section drafts.

The output is a disposable SWORD/reader paragraph-layout prototype only.
It is NOT a reconstructed source-faithful derivative: independent semantic
review, original inline-note/reference fidelity, complete introductions,
and publication approval are explicitly outside this prototype. This tool
cannot publish files or change the authoritative compiled source.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from commentary_modern_draft_guard import read_chapter_draft, verify_draft_against_native_map

NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"
XML = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", NS)
ET.register_namespace("xml", XML)
_EMPH = re.compile(r"(\*\*([^*\r\n]+)\*\*|\*([^*\r\n]+)\*)")


def _inline(parent: ET.Element, source: str) -> None:
    # Deliberately narrow Markdown parser: no external Markdown HTML, links,
    # scripts, raw tags or embedded user-supplied XML; ElementTree escapes.
    pos = 0
    previous = None
    for m in _EMPH.finditer(source):
        plain = source[pos:m.start()]
        if previous is None:
            parent.text = (parent.text or "") + plain
        else:
            previous.tail = (previous.tail or "") + plain
        previous = ET.SubElement(parent, f"{{{NS}}}hi",
            {"type": "bold" if m[2] is not None else "italic"})
        previous.text = m[2] if m[2] is not None else m[3]
        pos = m.end()
    tail = source[pos:]
    if previous is None:
        parent.text = (parent.text or "") + tail
    else:
        previous.tail = (previous.tail or "") + tail


def _range(keys: list[str]) -> str:
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("Missing or duplicate original source section keys")
    parsed = []
    for key in keys:
        try:
            book, chapter, verse = key.rsplit(".", 2)
            parsed.append((book, int(chapter), int(verse)))
        except (ValueError, IndexError) as exc:
            raise ValueError("Invalid original native key") from exc
    if {(b, c) for b, c, _ in parsed} != {(parsed[0][0], parsed[0][1])}:
        raise ValueError("A source section spans multiple chapters; review separately")
    ordered = sorted(v for _, _, v in parsed)
    ranges = []
    start = end = ordered[0]
    for v in ordered[1:]:
        if v == end + 1:
            end = v
        else:
            ranges.append((start, end))
            start = end = v
    ranges.append((start, end))
    prefix = parsed[0][0] + "." + str(parsed[0][1]) + "."
    return " ".join(prefix+str(s) if s == e else
                    prefix+str(s)+"-"+prefix+str(e) for s,e in ranges)


def _chapters(root: Path, ledger: dict):
    native = ledger["chapters"]
    payload=[]
    for path in sorted(root.rglob("*.DRAFT.md")):
        heading = path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
        if not re.search(r"(?m)^chapter_osis: ", heading):
            continue
        draft = read_chapter_draft(path)
        ch = draft["chapter"]
        if ch not in native:
            raise ValueError("Chapter not source-mapped in the complete receipt: "+ch)
        verify_draft_against_native_map(draft,native[ch],
            source_zip_sha256=ledger["package_sha256"],
            source_native_sha256=ledger["whole_native_source_sha256"])
        body=path.read_text(encoding="utf-8").split("\n---\n", 1)[1].split("\n---\n", 1)[0]
        heads=list(re.finditer(r"(?m)^## (.+)\s*$",body))
        sections=[]
        for i,h in enumerate(heads):
            text=body[h.end(): heads[i+1].start() if i+1<len(heads) else len(body)]
            paras=[p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n",text) if p.strip()]
            if not paras:
                raise ValueError("Source section has no modern draft paragraphs")
            sections.append((h[1].strip(),paras))
        if len(sections)!=len(native[ch]["units"]):
            raise ValueError("Missing/extra draft sections")
        payload.append((ch, sections, native[ch]["units"]))
    if len(payload)!=len(native):
        raise ValueError("Not all source-mapped chapters were included")
    return payload


def generate(root: Path, ledger: dict, *, work_id: str) -> tuple[bytes, dict]:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,32}", work_id):
        raise ValueError("Invalid temporary test-only module identifier")
    if ledger.get("semantic_translation_review_approved") is not False:
        raise ValueError("Preview cannot reuse a semantic-approved release scope")
    doc=ET.Element(f"{{{NS}}}osis")
    text=ET.SubElement(doc,f"{{{NS}}}osisText",{
        "osisIDWork":work_id,"osisRefWork":"Bible",
        f"{{{XML}}}lang":"en","canonical":"false"
    })
    header=ET.SubElement(text,f"{{{NS}}}header")
    work=ET.SubElement(header,f"{{{NS}}}work",{"osisWork":work_id})
    ET.SubElement(work,f"{{{NS}}}title").text="Unvalidated Modern Commentary Layout Preview"
    ET.SubElement(work,f"{{{NS}}}identifier",{"type":"OSIS"}).text=work_id
    ET.SubElement(work,f"{{{NS}}}language",{"type":"IETF"}).text="en"
    group=ET.SubElement(text,f"{{{NS}}}div",{"type":"bookGroup"})
    book_nodes={}
    total_sections=total_paragraphs=0
    claimed=[]
    for ch, sections, source_units in _chapters(root,ledger):
        book=ch.split(".",1)[0]
        if book not in book_nodes:
            book_nodes[book]=ET.SubElement(group,f"{{{NS}}}div",{
                "type":"book","osisID":book
            })
        chapter=ET.SubElement(book_nodes[book],f"{{{NS}}}chapter",{"osisID":ch})
        for (heading, paragraphs), native in zip(sections,source_units):
            ref=_range(native["native_keys"])
            sec=ET.SubElement(chapter,f"{{{NS}}}div",{
                "type":"section","annotateType":"commentary","annotateRef":ref
            })
            ET.SubElement(sec,f"{{{NS}}}title",{
                "type":"sub","resp":"BibleResourcesPilotEditorial"
            }).text=heading
            for paragraph in paragraphs:
                p=ET.SubElement(sec,f"{{{NS}}}p")
                _inline(p,paragraph)
                total_paragraphs+=1
            claimed.append({"chapter":ch,"source_section_ref":ref,
                            "source_sha256":native["raw_sha256"],
                            "paragraph_count":len(paragraphs)})
            total_sections+=1
    payload=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    # Authoritative XML bytes may never be reconstructed from this preview.
    # This is *not* an archive or an approved source replacement.
    ET.fromstring(payload)
    return payload, {
        "status":"TECHNICAL_ONLY_UNVALIDATED_OSIS_PREVIEW",
        "temporary_module_id":work_id,
        "modern_chapter_count":len(ledger["chapters"]),
        "annotated_commentary_sections":total_sections,
        "new_reading_paragraphs":total_paragraphs,
        "original_book_and_chapter_introductions_included":False,
        "original_inline_reference_or_note_fidelity_approved":False,
        "semantic_translation_independently_approved":False,
        "sword_publication_authorized":False,
        "sections":claimed,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--native-map",type=Path,required=True)
    p.add_argument("--osis",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--temp-module-id",default="MHCCWORK")
    a=p.parse_args()
    meta=json.loads(a.native_map.read_text(encoding="utf-8"))
    data, report=generate(a.root,meta,work_id=a.temp_module_id)
    a.osis.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.osis.write_bytes(data)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Unvalidated OSIS layout preview produced: "+
          str(report["modern_chapter_count"])+" chapters; "+
          str(report["annotated_commentary_sections"])+" original section anchors; "+
          str(report["new_reading_paragraphs"])+" draft paragraph blocks")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
