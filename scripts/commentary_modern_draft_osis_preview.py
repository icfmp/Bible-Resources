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


def _chapters(root: Path, ledger: dict, *, include_candidates: bool = False):
    native = ledger["chapters"]
    payload=[]
    paths = list(root.rglob("*.DRAFT.md"))
    if include_candidates:
        paths += list(root.rglob("*.CANDIDATE.md"))
    for path in sorted(paths):
        heading = path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
        if not re.search(r"(?m)^chapter_osis: ", heading):
            continue
        draft = read_chapter_draft(path,allow_production_candidate=include_candidates)
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
    # Files live in separate pilots/ and chapters/ directories. OSIS chapters
    # must follow canonical chapter order, not lexicographic file-path order.
    return sorted(payload, key=lambda item: (item[0].split(".", 1)[0],
                                             int(item[0].split(".", 1)[1])))


def generate(root: Path, ledger: dict, *, work_id: str,
             include_candidates: bool = False) -> tuple[bytes, dict]:
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
    for ch, sections, source_units in _chapters(root,ledger,include_candidates=include_candidates):
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



# Full-canon *structural* export, deliberately separate from the old 24-chapter
# pilot. No source hyperlink is silently copied or guessed in this mode.
_CANON = ("Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr "
          "2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa Jer Lam Ezek Dan Hos "
          "Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke "
          "John Acts Rom 1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim "
          "Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude Rev").split()
_HEADING = re.compile(r"(?m)^(#{2,5}) ([^\n]+?)\s*$")
_FIELD = re.compile(r'^([a-z_][a-z0-9_]*): "([^"\r\n]*)"$')
_FIELD_INT = re.compile(r"^([a-z_][a-z0-9_]*): ([0-9]+)$")
_SOURCE_ZIP = "a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746"
_SOURCE_CORPUS = "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"


def _modern_front(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise ValueError("Modern manuscript frontmatter absent: " + path.name)
    head, rest = raw[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        if not line.strip():
            continue
        match = _FIELD.fullmatch(line) or _FIELD_INT.fullmatch(line)
        if not match or match[1] in fields:
            raise ValueError("Unexpected or duplicate modern manuscript field: " + path.name)
        fields[match[1]] = match[2]
    if "\n---\n" not in rest:
        raise ValueError("Modern manuscript review delimiter absent: " + path.name)
    prose, audit = rest.split("\n---\n", 1)
    if not audit.strip() or any(x in prose for x in ("\x00", "\ufffd")):
        raise ValueError("Missing editorial notes or invalid original manuscript Unicode")
    return fields, prose


def _modern_items(prose: str) -> list[dict]:
    heads = list(_HEADING.finditer(prose))
    if not heads or not re.search(r"(?m)^# [^\n]+$", prose[:heads[0].start()]):
        raise ValueError("Missing canonical modern reading title/exposition sections")
    lead = re.sub(r"(?m)^# [^\n]+$", "", prose[:heads[0].start()]).strip()
    if lead:
        raise ValueError("Unowned modern prose before the first section")
    out = []
    for i, h in enumerate(heads):
        next_head = heads[i+1] if i+1 < len(heads) else None
        body = prose[h.end():next_head.start() if next_head else len(prose)].strip()
        heading = h[2].strip()
        lower = heading.lower()
        if lower.startswith("original ") or "book introduction" in lower:
            kind = "prelude"
        elif next_head and len(next_head[1]) > len(h[1]):
            kind = "parent"
        else:
            kind = "leaf"
        if kind == "leaf" and not body:
            raise ValueError("Empty modern authorial exposition: " + heading)
        out.append({"kind":kind, "title":heading, "body":body})
    return out


def _write_reading_blocks(parent: ET.Element, source: str) -> dict:
    """Preserve authored paragraph/table/list ordering. Unsupported syntax stops."""
    lines = source.splitlines()
    counts = {"paragraphs":0, "tables":0, "table_cells":0, "lists":0}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if (line.startswith((">", "![", chr(96)*3, "~~~"))
                or re.match(r"^#{1,6} ", line)):
            raise ValueError("Unsupported Markdown block must not be silently flattened")
        if line.startswith("|"):
            if i+2 >= len(lines):
                raise ValueError("Truncated original-outline Markdown table")
            cols = [x.strip() for x in line.strip("|").split("|")]
            rule = [x.strip() for x in lines[i+1].strip().strip("|").split("|")]
            if (len(cols) < 2 or len(cols) != len(rule)
                    or any(not re.fullmatch(r":?-{2,}:?", x) for x in rule)):
                raise ValueError("Original-outline table delimiter/column drift")
            table = ET.SubElement(parent, f"{{{NS}}}table",
                                  {"resp":"BibleResourcesModernManuscriptNotNativeVerified"})
            counts["tables"] += 1
            i += 2
            cells = [cols]
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if len(row) != len(cols):
                    raise ValueError("Original-outline table row changed column count")
                cells.append(row)
                i += 1
            if len(cells) < 2:
                raise ValueError("Original-outline table lacks actual rows")
            for row in cells:
                element = ET.SubElement(table, f"{{{NS}}}row")
                for value in row:
                    _inline(ET.SubElement(element, f"{{{NS}}}cell"), value)
                    counts["table_cells"] += 1
            continue
        if re.match(r"^[-*] ", line):
            node = ET.SubElement(parent, f"{{{NS}}}list")
            counts["lists"] += 1
            while i < len(lines) and re.match(r"^[-*] ", lines[i].strip()):
                item = ET.SubElement(node, f"{{{NS}}}item")
                _inline(item, lines[i].strip()[2:].strip())
                i += 1
            continue
        para=[]
        while i < len(lines):
            value = lines[i].strip()
            if (not value or value.startswith(("|", ">", "![", chr(96)*3, "~~~"))
                    or re.match(r"^(?:#{1,6}|[-*]) ", value)):
                break
            para.append(value)
            i += 1
        if not para:
            raise ValueError("Unsupported Markdown cannot be exported without loss")
        _inline(ET.SubElement(parent, f"{{{NS}}}p"), " ".join(para))
        counts["paragraphs"] += 1
    return counts


def _original_intro_candidates(root: Path, receipt: dict) -> dict:
    intros={}
    candidates=sorted(root.glob("*-book-introduction.CANDIDATE.md"))
    for path in candidates:
        fields, prose = _modern_front(path)
        book=fields.get("book_osis")
        if (book in intros or book not in _CANON
                or fields.get("source_module") != "MHCC 0.1.1"
                or fields.get("source_zip_sha256") != _SOURCE_ZIP
                or fields.get("source_native_corpus_sha256") != _SOURCE_CORPUS
                or not fields.get("status","").startswith("PRODUCTION CANDIDATE")
                or fields.get("source_native_intro_key") != "I:"+book+".1"):
            raise ValueError("Unverified original chapter-I introduction candidate")
        sources=[i for i in receipt["chapters"][book+".1"][
            "native_introductions_not_assumed_to_be_exposition"]
            if i["key"]==book+".1" and i["visible_word_tokens"]>=20]
        if (len(sources)!=1 or sources[0]["raw_sha256"]!=
                fields.get("source_native_intro_raw_sha256")):
            raise ValueError("Modern introduction does not belong to original chapter-I")
        title = re.search(r"(?m)^# ([^\n]+)$", prose)
        if not title or not prose[title.end():].strip():
            raise ValueError("Empty source-linked modern introduction")
        intros[book]=(title[1],prose[title.end():].strip())
    expected={x["key"].split(".",1)[0]
              for c in receipt["chapters"].values()
              for x in c["native_introductions_not_assumed_to_be_exposition"]
              if x["key"].count(".")==1 and x["visible_word_tokens"]>=20
              and c["source_placement"]!="INTRO_ONLY_NEEDS_INDEPENDENT_REVIEW"}
    if set(intros)!=expected:
        raise ValueError("Original chapter-I prefaces do not match candidates")
    return intros


def generate_accepted_canon_osis(accepted: Path, source: dict,
                                  topology: dict, ionly: dict, intro_root: Path,
                                  *, work_id: str) -> tuple[bytes, dict]:
    """Build complete **unlinked/unapproved** OSIS; never change published SWORD."""
    import hashlib
    from commentary_modern_draft_guard import _claimed_verse_keys_in_heading
    if (not re.fullmatch(r"MHCC[A-Z0-9]{2,20}", work_id)
            or source.get("status")!="SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL"
            or source.get("original_compiled_corpus_sha256")!=_SOURCE_CORPUS
            or source.get("semantic_translation_independently_approved") is not False
            or source.get("source_prose_or_original_markup_exported") is not False):
        raise ValueError("Original real-native source receipt is not authentic")
    originals=source.get("chapters")
    if (not isinstance(originals,dict) or len(originals)!=1189
            or {s.split(".",1)[0] for s in originals}!=set(_CANON)):
        raise ValueError("Whole canonical real-source chapter set is missing")
    if (topology.get("status") !=
        "REVIEWED_SOURCE_VS_EDITORIAL_TOPOLOGY_EXCEPTIONS_NOT_RELEASE_APPROVAL"
        or topology.get("original_compiled_corpus_sha256")!=_SOURCE_CORPUS
        or topology.get("publication_authorized") is not False
        or topology.get("derived_markup_and_links_independently_approved") is not False):
        raise ValueError("Non-reviewed modern source-topology manifest")
    cases=topology.get("cases")
    if not isinstance(cases,list):
        raise ValueError("No source-vs-modern topology attestations")
    overrides={item["chapter"]:item for item in cases}
    if len(overrides)!=len(cases) or any(k not in originals for k in overrides):
        raise ValueError("Duplicate/foreign modern topology case")
    if (ionly.get("status")!="PRIVATE_TECHNICAL_PREVIEW_ONLY_NOT_EDITORIAL_APPROVAL"
            or ionly.get("source_native_corpus_sha256")!=_SOURCE_CORPUS
            or ionly.get("source_zip_sha256")!=_SOURCE_ZIP
            or ionly.get("publication_authorized") is not False
            or ionly.get("semantic_translation_independently_approved") is not False):
        raise ValueError("I-only original source chapter manifest is not authentic")
    i_rows=ionly.get("chapters")
    if not isinstance(i_rows,list):
        raise ValueError("I-only original chapter source mapping absent")
    i_map={row["chapter_osis"]:row for row in i_rows}
    if (len(i_map)!=len(i_rows) or set(i_map)!=
            set(source.get("intro_only_chapters_needing_editorial_review",[]))):
        raise ValueError("Wrong chapter-I-only original source selection")
    files=sorted(accepted.glob("*.md"))
    if len(files)!=1189:
        raise ValueError("Incomplete 1189 modern manuscript inventory")
    modern={}
    for path in files:
        fields,main=_modern_front(path)
        chapter=fields.get("chapter_osis")
        if (chapter not in originals or chapter in modern
                or fields.get("source_module")!="MHCC 0.1.1"
                or fields.get("source_zip_sha256")!=_SOURCE_ZIP
                or fields.get("source_native_corpus_sha256")!=_SOURCE_CORPUS
                or not fields.get("publication_status","").startswith("NOT RELEASED")):
            raise ValueError("Modern manuscript source/version/status drift: "+path.name)
        modern[chapter]=_modern_items(main)
    if set(modern)!=set(originals):
        raise ValueError("Missing/duplicate canonical modern chapters")
    intros=_original_intro_candidates(intro_root,source)
    doc=ET.Element(f"{{{NS}}}osis")
    osis=ET.SubElement(doc,f"{{{NS}}}osisText",{
        "osisIDWork":work_id,"osisRefWork":"Bible",
        f"{{{XML}}}lang":"en","canonical":"false"})
    header=ET.SubElement(osis,f"{{{NS}}}header")
    work=ET.SubElement(header,f"{{{NS}}}work",{"osisWork":work_id})
    ET.SubElement(work,f"{{{NS}}}title").text=(
        "Unlinked Modern MHCC — source fidelity and release NOT APPROVED")
    ET.SubElement(work,f"{{{NS}}}identifier",{"type":"OSIS"}).text=work_id
    ET.SubElement(work,f"{{{NS}}}language",{"type":"IETF"}).text="en"
    ET.SubElement(work,f"{{{NS}}}description").text=(
        "All 1189 modern manuscripts; source-native Bible links and layout "
        "not transferred; authorial meaning not independently certified")
    group=ET.SubElement(osis,f"{{{NS}}}div",{"type":"bookGroup"})
    totals=dict(chapters=0,groups=0,leaves=0,keys=0,
                paragraphs=0,tables=0,table_cells=0,lists=0,unscoped=0)
    used_cases=set()
    for book in _CANON:
        book_node=ET.SubElement(group,f"{{{NS}}}div",{"type":"book","osisID":book})
        book_chapters=sorted((k for k in originals if k.startswith(book+".")),
                             key=lambda key:int(key.rsplit(".",1)[1]))
        if [int(k.rsplit(".",1)[1]) for k in book_chapters]!=list(
                range(1,len(book_chapters)+1)):
            raise ValueError("Missing/surplus canonical source chapter: "+book)
        for chapter in book_chapters:
            info=originals[chapter]
            items=modern[chapter]
            leaves=[item for item in items if item["kind"]=="leaf"]
            if chapter in i_map:
                case=i_map[chapter]
                ii=[r for r in info["native_introductions_not_assumed_to_be_exposition"]
                    if r["key"]==chapter and r["visible_word_tokens"]>40]
                if (info["original_units"] or len(leaves)!=1 or len(ii)!=1
                        or info["source_placement"]!="INTRO_ONLY_NEEDS_INDEPENDENT_REVIEW"
                        or ii[0]["raw_sha256"]!=case["intro_raw_sha256"]
                        or type(case.get("verse_count")) is not int
                        or not 1<=case["verse_count"]<=200):
                    raise ValueError("Unverified full-chapter I-only original: "+chapter)
                keys=[[chapter+"."+str(n) for n in range(
                    1,case["verse_count"]+1)]]
                mapping=[[0]]
            else:
                if (not info["original_units"] or
                        info["source_placement"]!="NUMBERED_KEYS_WITH_SEPARATE_INTRO"):
                    raise ValueError("Unmapped genuine original K body in "+chapter)
                keys=[u["keys"] for u in info["original_units"]]
                if chapter in overrides:
                    mapping=overrides[chapter].get("modern_leaf_indices_by_original_K")
                    used_cases.add(chapter)
                    if (not isinstance(mapping,list) or len(mapping)!=len(keys)
                            or any(not isinstance(row,list) or not row for row in mapping)
                            or sum(mapping,[])!=list(range(len(leaves)))):
                        raise ValueError("Modern topical groups do not map to original K: "+chapter)
                else:
                    if len(leaves)!=len(keys):
                        raise ValueError("Undeclared modern/original source topology drift: "+chapter)
                    mapping=[[i] for i in range(len(keys))]
            for n,ids in enumerate(mapping):
                claim=[_claimed_verse_keys_in_heading(leaves[i]["title"]) for i in ids]
                original_verses=[int(k.rsplit(".",1)[1]) for k in keys[n]]
                if len(ids)>1:
                    if any(row is None for row in claim) or set(sum(claim,[]))!=set(original_verses):
                        raise ValueError("Joined modern headings fail original K span: "+chapter)
                elif claim[0] is None:
                    totals["unscoped"]+=1
                elif claim[0]!=original_verses and chapter not in overrides:
                    raise ValueError("Undeclared modern verse range differs from native K: "+chapter)
            chapter_node=ET.SubElement(book_node,f"{{{NS}}}chapter",{"osisID":chapter})
            if book in intros and chapter.endswith(".1"):
                title,body=intros[book]
                intro=ET.SubElement(chapter_node,f"{{{NS}}}div",{
                    "type":"introduction",
                    "resp":"BibleResourcesModernCandidateExactOriginalChapterI"})
                ET.SubElement(intro,f"{{{NS}}}title").text=title
                _write_reading_blocks(intro,body)
            group_for_leaf={leaf:n for n,idxs in enumerate(mapping) for leaf in idxs}
            first_for_group={idxs[0]:n for n,idxs in enumerate(mapping)}
            if len(group_for_leaf)!=len(leaves):
                raise ValueError("Unassigned modern authorial section")
            current=None
            leaf_index=0
            for item in items:
                if item["kind"]!="leaf":
                    pre=ET.SubElement(chapter_node,f"{{{NS}}}div",{
                        "type":"introduction",
                        "resp":"BibleResourcesModernManuscriptEditorialGrouping"})
                    ET.SubElement(pre,f"{{{NS}}}title").text=item["title"]
                    count=_write_reading_blocks(pre,item["body"])
                else:
                    source_n=group_for_leaf[leaf_index]
                    if leaf_index in first_for_group:
                        current=ET.SubElement(chapter_node,f"{{{NS}}}div",{
                            "type":"section","annotateType":"commentary",
                            "annotateRef":_range(keys[source_n])})
                        totals["groups"]+=1
                        totals["keys"]+=len(keys[source_n])
                    if current is None:
                        raise ValueError("Missing source-bound commentary unit")
                    ET.SubElement(current,f"{{{NS}}}title",{
                        "type":"sub",
                        "resp":"BibleResourcesModernEditorialHeading"}).text=item["title"]
                    count=_write_reading_blocks(current,item["body"])
                    totals["leaves"]+=1
                    leaf_index+=1
                for field in ("paragraphs","tables","table_cells","lists"):
                    totals[field]+=count[field]
            totals["chapters"]+=1
    if used_cases!=set(overrides):
        raise ValueError("Unreconciled explicitly reviewed source topology exception")
    if (totals["chapters"]!=1189 or totals["groups"]!=4049
            or totals["leaves"]!=4052 or
            totals["keys"]!=28742+sum(c["verse_count"] for c in i_rows)):
        raise ValueError("Whole-canon authorial structure/key coverage incomplete")
    result=ET.tostring(doc,encoding="utf-8",xml_declaration=True)
    ET.fromstring(result)
    return result,{
        "status":"FULL_CANON_UNLINKED_MODERN_ENGLISH_OSIS_TECHNICAL_CANDIDATE_NOT_RELEASE",
        "books":len(_CANON),"chapters":totals["chapters"],
        "original_K_authorial_bodies":totals["groups"]-len(i_rows),
        "source_I_only_chapter_bodies":len(i_rows),
        "annotated_sections":totals["groups"],
        "modern_topical_expositions":totals["leaves"],
        "total_source_and_I_only_verse_alias_keys":totals["keys"],
        "chapter_I_preface_candidates":len(intros),
        "paragraphs":totals["paragraphs"],
        "tables":totals["tables"],"table_cells":totals["table_cells"],
        "lists":totals["lists"],
        "headings_without_exact_parsed_verse_scope":totals["unscoped"],
        "source_topology_exceptions_used":sorted(used_cases),
        "source_native_corpus_sha256":_SOURCE_CORPUS,
        "osis_sha256":hashlib.sha256(result).hexdigest(),
        "original_1204_reference_links_transferred":False,
        "original_native_inline_markup_and_notes_verified":False,
        "independent_semantic_signoff":False,
        "sword_publication_authorized":False,
        "original_sword_changed":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    sources=p.add_mutually_exclusive_group(required=True)
    sources.add_argument("--native-map",type=Path)
    sources.add_argument("--single-chapter-source-map",type=Path)
    sources.add_argument("--accepted-native-receipt",type=Path)
    p.add_argument("--source-topology-manifest",type=Path)
    p.add_argument("--ionly-manifest",type=Path)
    p.add_argument("--book-intro-candidate-root",type=Path)
    p.add_argument("--include-production-candidates",action="store_true")
    p.add_argument("--osis",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--temp-module-id",default="MHCCWORK")
    a=p.parse_args()
    if a.accepted_native_receipt:
        if (not a.source_topology_manifest or not a.ionly_manifest
                or not a.book_intro_candidate_root
                or a.include_production_candidates):
            p.error("Full-canon mode requires topology, I-only and chapter-I candidates")
        data, report=generate_accepted_canon_osis(
            a.root,
            json.loads(a.accepted_native_receipt.read_text(encoding="utf-8")),
            json.loads(a.source_topology_manifest.read_text(encoding="utf-8")),
            json.loads(a.ionly_manifest.read_text(encoding="utf-8")),
            a.book_intro_candidate_root,work_id=a.temp_module_id)
        a.osis.parent.mkdir(parents=True,exist_ok=True)
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.osis.write_bytes(data)
        a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("FULL-CANON MODERN MHCC UNLINKED OSIS: 66 books, 1189 chapters, " +
              str(report["annotated_sections"])+" original-indexed sections, " +
              "SHA256="+report["osis_sha256"]+
              "; source hyperlinks, source markup and publication NOT approved")
        return 0
    if a.source_topology_manifest or a.ionly_manifest or a.book_intro_candidate_root:
        p.error("Whole-canon manifests require --accepted-native-receipt")
    if a.single_chapter_source_map:
        raw=json.loads(a.single_chapter_source_map.read_text(encoding="utf-8"))
        scope=raw.get("scope")
        units=raw.get("sections")
        if not scope or not isinstance(units,list) or not units:
            raise ValueError("Missing single-chapter native source evidence")
        meta={
            "package_sha256":raw["published_zip_sha256"],
            "whole_native_source_sha256":raw["verified_entire_native_corpus_sha256"],
            "semantic_translation_review_approved":False,
            "chapters":{
                scope:{"units":[{"native_keys":u["native_keys"],
                                 "raw_sha256":u["source_sha256"]}
                                for u in units]}
            }
        }
    else:
        meta=json.loads(a.native_map.read_text(encoding="utf-8"))
    data, report=generate(a.root,meta,work_id=a.temp_module_id,
                          include_candidates=a.include_production_candidates)
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
