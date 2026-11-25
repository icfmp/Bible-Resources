"""Independent original USFX editorial structure comparators.

Read-only; source/target tree inputs and reviewed crosswalk are explicit.
Checks supported grammar only; never grants editorial or release approval.
"""
from collections import Counter, defaultdict
import hashlib
import re
from lxml import etree
from pilot_preflight import PilotError
from source_osis_inventory import OSIS

NON_VERSE_TEXT_ELEMENTS={"x","f","fig","s","r","toc","h","id"}
NON_VERSE_PARAGRAPH_STYLES={"r","s","s1","s2","s3","s4","sr","h","toc1","toc2","toc3"}
SKIP_TARGET=frozenset(("title","header","note","revisionDesc","description"))
SKIP_SOURCE=frozenset(NON_VERSE_TEXT_ELEMENTS)|{'fe','ef','ex'}
def _name(node):
    return etree.QName(node).localname if isinstance(node.tag,str) else ""


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _no_space(text):
    return "".join(text.split())


POETRY_STYLES=re.compile(r"^(?:q[1-4]?|qm[1-4]?|qr|qc|qd)$")


def _source_poetry_style(node):
    """A poetic paragraph is identified by USFX marker/style, never guesswork."""
    name=_name(node)
    marker=node.get("sfm") or node.get("style") or name
    if name not in {"q","qr","qc","qd","qm","p"}:
        return None
    if not POETRY_STYLES.fullmatch(marker):
        if name in {"q","qr","qc","qd","qm"} or marker.startswith("q"):
            raise PilotError("Unreviewed source poetry paragraph style")
        return None
    if marker in {"qr","qc","qd"}:
        return {"qr":"right","qc":"center","qd":"hebrew-end"}[marker]
    embedded=marker.startswith("qm")
    level=marker[2:] if embedded else marker[1:]
    return ("embedded" if embedded else "indent") + ":" + (level or "1")


def _candidate_poetry_style(node):
    kind=node.get("type")
    if kind=="selah":
        # OSIS uses a separate <l> for the USFM inline \qs marker.
        # Audit it as editorial text, never as an ordinary poetic line.
        return None
    if kind in {"x-right","x-center","x-usfm-qd"}:
        return {"x-right":"right","x-center":"center",
                "x-usfm-qd":"hebrew-end"}[kind]
    if kind not in (None,"x-embedded"):
        return "unsupported-type:"+kind
    level=node.get("level")
    if not level or not level.isdecimal():
        return "unsupported-level:"+str(level)
    return ("embedded" if kind=="x-embedded" else "indent")+":"+level


def _read(root, *, source):
    """Read line text as XML events; verse ownership changes at milestones."""
    expected="usfx" if source else "osis"
    if _name(root)!=expected:
        raise PilotError(f"Poetry segment audit expected {expected} XML")
    book_iterator=root.iter("book") if source else (
        node for node in root.iter(OSIS+"div") if node.get("type")=="book")
    assigned=defaultdict(list)
    selah_by_verse=defaultdict(list)
    selah_nodes=0
    selah_unowned_nodes=0
    total_nodes=0
    with_text_unowned=0
    empty_nodes=0
    multiverse_nodes=0
    styles=Counter()
    for book in book_iterator:
        code=book.get("id") if source else book.get("osisID")
        if not code:
            raise PilotError("Unreviewed book identity in poetry segment audit")
        chapter=None
        current=None
        active_lines=[]
        active_selah=[]

        def emit(value):
            if not value or not value.strip():
                return
            if active_selah:
                marker=active_selah[-1]
                if current is None:
                    marker["unowned_text"]+=len(_no_space(value))
                else:
                    marker["parts"][current].append(value)
                return
            if not active_lines:
                return
            line=active_lines[-1]
            if current is None:
                line["unowned_text"]+=len(_no_space(value))
            else:
                line["parts"][current].append(value)

        def walk(node):
            nonlocal chapter,current,total_nodes,empty_nodes,multiverse_nodes,with_text_unowned
            nonlocal selah_nodes,selah_unowned_nodes
            if isinstance(node,etree._Comment):
                return
            if not isinstance(node.tag,str):
                raise PilotError("Unexpected non-element in poetry segmentation")
            kind=_name(node)
            if source:
                if kind=="c":
                    val=node.get("id")
                    if not val or not val.isdecimal():
                        raise PilotError("Unreviewed USFX chapter for poetry")
                    chapter=int(val)
                elif kind=="v":
                    val=node.get("id")
                    if not val or not val.isdecimal() or chapter is None:
                        raise PilotError("Unreviewed USFX verse for poetry")
                    current=(code,chapter,int(val))
                elif kind=="ve":
                    if current is None:
                        raise PilotError("USFX orphan verse close in poetry audit")
                    current=None
                if (kind in SKIP_SOURCE or
                        (kind=="p" and (node.get("sfm") or node.get("style"))
                         in NON_VERSE_PARAGRAPH_STYLES)):
                    return
            else:
                if kind=="verse":
                    start=node.get("osisID") or node.get("sID")
                    end=node.get("eID")
                    if start:
                        if current is not None:
                            raise PilotError("Overlapping OSIS verse in poetry segment audit")
                        current=start
                    elif end:
                        if current!=end:
                            raise PilotError("Mismatched OSIS verse ending in poetry segment audit")
                        current=None
                    else:
                        raise PilotError("Unknown OSIS verse marker in poetry segment audit")
                if kind in SKIP_TARGET:
                    return
            is_selah=(kind=="qs" if source else
                      kind=="l" and node.get("type")=="selah")
            if is_selah:
                if active_selah:
                    raise PilotError("Nested Selah markers require editorial review")
                selah_nodes+=1
                active_selah.append({"parts":defaultdict(list),"unowned_text":0})
            style=_source_poetry_style(node) if source else (
                _candidate_poetry_style(node) if kind=="l" else None)
            is_poetic_line=(style is not None)
            if is_poetic_line:
                if active_lines:
                    raise PilotError("Nested poetry line nodes require editorial review")
                total_nodes+=1
                styles[style]+=1
                active_lines.append({"level":style,
                                     "parts":defaultdict(list),"unowned_text":0})
            emit(node.text)
            for child in node:
                walk(child)
                emit(child.tail)
            if is_poetic_line:
                line=active_lines.pop()
                if not line["parts"] and not line["unowned_text"]:
                    empty_nodes+=1
                if line["unowned_text"]:
                    with_text_unowned+=1
                if len(line["parts"])>1:
                    multiverse_nodes+=1
                for ref, text_parts in line["parts"].items():
                    body="".join(text_parts)
                    compact=_no_space(body)
                    if not compact:
                        continue
                    assigned[ref].append({
                        "level":line["level"],
                        "text_sha256":_hash(compact),
                        "chars":len(compact),
                    })
            if is_selah:
                marker=active_selah.pop()
                if marker["unowned_text"]:
                    selah_unowned_nodes+=1
                for ref, chunks in marker["parts"].items():
                    compact=_no_space("".join(chunks))
                    selah_by_verse[ref].append({
                        "text_sha256":_hash(compact),"chars":len(compact)})
        walk(book)
        if active_selah:
            raise PilotError("Open Selah marker in poetry audit")
        if active_lines:
            raise PilotError("Open poetry line in source XML")
        if not source and current is not None:
            raise PilotError("Open OSIS verse at end of poetry audit book")
    return assigned, {
        "all_poetry_line_nodes":total_nodes,
        "selah_marker_nodes":selah_nodes,
        "selah_marker_nodes_outside_verse":selah_unowned_nodes,
        "line_nodes_containing_nonverse_text":with_text_unowned,
        "empty_poetry_line_nodes":empty_nodes,
        "line_nodes_spanning_multiple_verses":multiverse_nodes,
        "poetry_line_style_counts":dict(sorted(styles.items())),
    },selah_by_verse


def audit_segments(source_root, candidate_root, mapping, source_keys):
    if isinstance(candidate_root,etree._ElementTree):
        candidate_root=candidate_root.getroot()
    authored,source_meta,source_selah=_read(source_root,source=True)
    converted,target_meta,target_selah=_read(candidate_root,source=False)
    hist=Counter()
    mismatching_books=Counter()
    discrepancies=Counter()
    first=[]
    equal_counts=equal_text=equal_levels=0
    missing_line_patterns=Counter()
    initial_line_loss_refs=[]
    equal_selah=0
    first_selah_differences=[]
    for book,chapter,verse in source_keys:
        key=(book,chapter,verse)
        target_key=f"{mapping[book]}.{chapter}.{verse}"
        a=authored.get(key,())
        b=converted.get(target_key,())
        delta=len(b)-len(a)
        hist[delta]+=1
        if delta<0:
            matching_suffix=(
                [x["text_sha256"] for x in b]
                ==[x["text_sha256"] for x in a[-len(b):]]
                if b else True
            )
            if (delta==-1 and matching_suffix
                    and [x["level"] for x in b]
                    ==[x["level"] for x in a[1:]]):
                pattern="missing_first_source_line_other_lines_intact"
                if len(initial_line_loss_refs)<60:
                    initial_line_loss_refs.append({
                        "reference":f"{book}.{chapter}.{verse}",
                        "missing_line_text_sha256":a[0]["text_sha256"],
                        "missing_line_text_characters":a[0]["chars"],
                        "chapter_first_verse":verse==1,
                    })
            else:
                pattern="other_missing_line_or_merged_text"
            missing_line_patterns[pattern]+=1
        selah_a=source_selah.get(key,())
        selah_b=target_selah.get(target_key,())
        if selah_a==selah_b:
            equal_selah+=1
        elif len(first_selah_differences)<35:
            first_selah_differences.append({
                "reference":f"{book}.{chapter}.{verse}",
                "source_selah_count":len(selah_a),
                "candidate_selah_count":len(selah_b),
                "source_text_hashes":[x["text_sha256"] for x in selah_a],
                "candidate_text_hashes":[x["text_sha256"] for x in selah_b],
            })
        same_count=(delta==0)
        same_text=(same_count and
                   [x["text_sha256"] for x in a]==
                   [x["text_sha256"] for x in b])
        known_levels=all(x["level"] is not None for x in (*a,*b))
        same_levels=(same_count and known_levels
                     and [x["level"] for x in a]==[x["level"] for x in b])
        equal_counts+=same_count
        equal_text+=same_text
        equal_levels+=same_levels
        if same_text and same_levels:
            continue
        mismatching_books[book]+=1
        if not same_count:
            discrepancies["line_count"]+=1
        if not same_text:
            discrepancies["line_text_or_segmentation"]+=1
        if not same_levels:
            discrepancies["indentation_unknown_or_different"]+=1
        if len(first)<80:
            first.append({
                "reference":f"{book}.{chapter}.{verse}",
                "source_lines":len(a),"candidate_lines":len(b),
                "count_equal":same_count,
                "line_text_equal_ignoring_whitespace":same_text,
                "indentation_levels_equal":same_levels,
                "source_levels":[x["level"] for x in a],
                "candidate_levels":[x["level"] for x in b],
                "source_line_hashes":[x["text_sha256"] for x in a],
                "candidate_line_hashes":[x["text_sha256"] for x in b],
            })
    missing_source_keys=len(set(authored)-set(source_keys))
    allowed_target={f"{mapping[c]}.{ch}.{v}" for c,ch,v in source_keys}
    unexpected_target_keys=len(set(converted)-allowed_target)
    total=len(source_keys)
    return {
        "total_compared_verse_keys":total,
        "source_poetry":source_meta,
        "candidate_poetry":target_meta,
        "matching_verse_line_counts_with_text_ownership":equal_counts,
        "matching_verse_line_text_sequences_ignoring_whitespace":equal_text,
        "matching_verse_line_indentation_levels":equal_levels,
        "matching_verse_selah_marker_text_sequences":equal_selah,
        "first_selah_differences":first_selah_differences,
        "all_selah_text_and_verse_positions_verified":(
            equal_selah==total
            and source_meta["selah_marker_nodes"]==target_meta["selah_marker_nodes"]
            and not source_meta["selah_marker_nodes_outside_verse"]
            and not target_meta["selah_marker_nodes_outside_verse"]),
        "line_delta_histogram":dict(sorted(hist.items())),
        "missing_line_pattern_classification":dict(sorted(missing_line_patterns.items())),
        "first_source_line_loss_references":initial_line_loss_refs,
        "mismatching_books":dict(sorted(mismatching_books.items())),
        "difference_categories":dict(sorted(discrepancies.items())),
        "source_poetry_keys_outside_verse_index":missing_source_keys,
        "candidate_poetry_keys_outside_verse_index":unexpected_target_keys,
        "first_differences":first,
        "all_poetry_segments_and_levels_verified":(
            equal_counts==equal_text==equal_levels==total
            and not missing_source_keys and not unexpected_target_keys
            and not source_meta["line_nodes_containing_nonverse_text"]
            and not target_meta["line_nodes_containing_nonverse_text"]
        ),
        "full_editorial_poetry_layout_verified":False,
        "limitation":"Independent content-owner audit handles lines spanning milestones. "
                     "USFM inline \\qs and OSIS <l type=selah> are compared separately; "
                     "their presentation is not automatically equivalent. "
                     "Line grouping (<lg>), blank stanzas, headings and presentation "
                     "must still be reviewed; no original body text is exported.",
    }

def table_signature(book,source):
    def cell_spans(cell):
        pos=0; spans=[]
        def append(value):
            nonlocal pos
            pos+=len(_no_space(value or ""))
        def walk(node):
            kind=_name(node)
            if not kind:return
            start=pos
            if node is cell:style=None
            elif source and kind in {"it","bd","ord","wj"}:
                style={"it":"italic","bd":"bold","ord":"super","wj":"quotation"}[kind]
            elif not source and kind=="hi":style=node.get("type")
            elif not source and kind=="q":style="quotation"
            else:raise ValueError("Unsupported table inline element "+kind)
            append(node.text)
            for child in node:
                walk(child);append(child.tail)
            if style:spans.append((style,start,pos))
        walk(cell)
        return spans
    tables=[]
    for table in book.iter("table" if source else OSIS+"table"):
        rows=[]
        for row in table:
            assert _name(row)==("tr" if source else "row")
            cells=[]
            for cell in row:
                assert _name(cell) in ({"tc","th"} if source else {"cell"})
                cells.append((" ".join("".join(cell.itertext()).split()),
                    _name(cell)=="th" if source else cell.get("role")=="label",
                    cell_spans(cell)))
            rows.append(cells)
        tables.append(rows)
    return tables
def paragraph_signature(book,source):
    # Numbered nonspace coordinates remain stable across format
    # conversion, including in-verse paragraph openings.
    pos=0; current=None; chapter=None; starts=[]
    styles={"p":None,"m":"x-noindent","pi":"x-indented-1","pi1":"x-indented-1"}
    titles={"s","s1","s2","s3","s4","r","sr","mr","ms","ms1","ms2","ms3",
            "mt","mt1","mt2","mt3","imt","imt1","imt2","imt3","is","is1","is2"}
    def append(value):
        nonlocal pos
        if current is not None:pos+=len(_no_space(value or ""))
    def walk(n):
        nonlocal current,chapter
        k=_name(n)
        if not k:return
        style=n.get("sfm") or n.get("style") or k
        if source and (k in {"x","f","fe","ef","ex","id","h","toc"}|titles or k=="p" and style in titles):return
        if not source and k in {"note","title","header"}:return
        container=False
        if source and k=="c":
            assert current is None;chapter=n.get("id")
        elif source and k=="v":
            assert current is None and chapter;current=n.get("id")
        elif source and k=="ve":
            assert current is not None;current=None
        elif not source and k=="verse":
            if n.get("eID"):
                assert current==n.get("eID");current=None
            else:
                assert current is None and n.get("osisID")
                current=n.get("osisID");container=not bool(n.get("sID"))
        if source and k=="p" and style in styles and pos>0:
            starts.append((pos,styles[style]))
        if not source and k=="p" and pos>0:
            assert n.get("type") in set(styles.values())
            starts.append((pos,n.get("type")))
        append(n.text)
        for c in n:
            walk(c);append(c.tail)
        if container:current=None
    walk(book)
    assert current is None
    return starts,pos
def compare_original_tables_and_paragraphs(source,target,mapping):
    old={mapping[b.get("id")]:b for b in source.iter("book")}
    new={b.get("osisID"):b for b in target.iter(OSIS+"div") if b.get("type")=="book"}
    assert old and list(old)==list(new)
    counts=Counter(); findings=[]
    for ident in old:
        a=table_signature(old[ident],True);b=table_signature(new[ident],False)
        counts["source_tables"]+=len(a);counts["candidate_tables"]+=len(b)
        counts["source_cells"]+=sum(len(row) for table in a for row in table)
        counts["candidate_cells"]+=sum(len(row) for table in b for row in table)
        if a!=b:findings.append((ident,"tables"))
        x,n=paragraph_signature(old[ident],True);y,m=paragraph_signature(new[ident],False)
        counts["source_numbered_paragraph_starts_after_offset_zero"]+=len(x)
        counts["candidate_numbered_paragraph_starts_after_offset_zero"]+=len(y)
        if x!=y or n!=m:findings.append((ident,"numbered_paragraph_starts"))
    return {"books":len(old),"counts":dict(counts),"differences":findings,
            "supported_table_and_numbered_paragraph_parity":not findings,
            "scope":"ordered table rows/cell text/header roles/selected inline spans; paragraph starts and style at positive numbered offsets; not initial or intro paragraph boundaries or exact typography"}
def editorial_signature(book,source):
    # Compare source-authored title text at numbered coordinates,
    # and selected body inline spans. Retain nonnumbered text and
    # introduction paragraph offsets as a separate diagnostic.
    pos=0; fullpos=0; current=None; chapter=None
    titles=[]; spans=defaultdict(list); intro=[]; outside=[]
    title_styles={"s","s1","s2","s3","s4","r","sr","mr","ms","ms1","ms2","ms3",
                  "mt","mt1","mt2","mt3","imt","imt1","imt2","imt3","is","is1","is2"}
    def append(value):
        nonlocal pos,fullpos
        value=_no_space(value or "")
        fullpos+=len(value)
        if current is not None:pos+=len(value)
        elif value:outside.append(value)
    def walk(n):
        nonlocal current,chapter
        k=_name(n)
        if not k:return
        style=n.get("sfm") or n.get("style") or k
        if source and k in {"x","f","fe","ef","ex","id","h","toc"}:return
        if not source and k in {"note","header"}:return
        if source and (k in title_styles or k=="p" and style in title_styles) or not source and k=="title":
            value=_no_space("".join(n.itertext()))
            titles.append((pos,len(value),_hash(value)))
            return
        container=False
        if source and k=="c":assert current is None;chapter=n.get("id")
        elif source and k=="v":assert current is None and chapter;current=n.get("id")
        elif source and k=="ve":assert current is not None;current=None
        elif not source and k=="verse":
            if n.get("eID"):
                assert current==n.get("eID");current=None
                return
            assert current is None and n.get("osisID")
            current=n.get("osisID");container=not bool(n.get("sID"))
        start=pos; fullstart=fullpos
        kind=None
        if source and k=="wj" or not source and k=="q":kind="quotation"
        elif source and k=="it" or not source and k=="hi" and n.get("type")=="italic":kind="italic"
        elif source and k=="ord" or not source and k=="hi" and n.get("type")=="super":kind="superscript"
        is_intro=(source and k=="p" and style in {"ip","ipi"} or not source and k=="p" and
                  any(_name(a)=="div" and a.get("type")=="introduction" for a in n.iterancestors()))
        append(n.text)
        for c in n:
            walk(c);append(c.tail)
        if kind:spans[kind].append((start,pos))
        if is_intro:intro.append((fullstart,fullpos))
        if container:current=None
    walk(book)
    assert current is None
    return titles,dict(spans),intro,"".join(outside)
def project_reviewed_intro_text(source,mapping,edits):
    # Modify a private in-memory comparison tree only, never the
    # original archive. Require the exact authored introduction
    # reference, its book and a unique match in intro scope.
    from copy import deepcopy
    projected=deepcopy(source)
    books={mapping[b.get("id")]:b for b in projected.iter("book")}
    used=set()
    for edit in edits:
        if edit["type"]!="introduction_text_correction":continue
        case=edit["case_id"]
        assert case not in used and edit["book"] in books
        old,new=edit["original_label"],edit["new_label"]
        assert old and new and old!=new
        matches=[n for n in books[edit["book"]].iter("ior")
                 if len(n)==0 and (n.text or "").strip()==old
                 and any(_name(a)=="p" and (a.get("sfm") or a.get("style")) in {"ip","ipi","io","io1","io2","io3","io4"} for a in n.iterancestors())]
        assert len(matches)==1,(case,"approved intro label not uniquely found")
        node=matches[0]
        node.text=node.text.replace(old,new,1)
        used.add(case)
    return projected,len(used)
def editorial_diagnostic(source,target,mapping):
    old={mapping[b.get("id")]:b for b in source.iter("book")}
    new={b.get("osisID"):b for b in target.iter(OSIS+"div") if b.get("type")=="book"}
    assert old and list(old)==list(new)
    counts=Counter();findings=defaultdict(list)
    from difflib import SequenceMatcher
    for ident in old:
        t,s,i,o=editorial_signature(old[ident],True)
        tt,ss,ii,oo=editorial_signature(new[ident],False)
        for label,a,b in (("titles",t,tt),("intro_paragraphs",i,ii)):
            counts[label+"_source"]+=len(a);counts[label+"_target"]+=len(b)
            if a!=b:findings[label].append(ident)
        for label in sorted(set(s)|set(ss)):
            a,b=s.get(label,[]),ss.get(label,[])
            counts[label+"_source"]+=len(a);counts[label+"_target"]+=len(b)
            if a!=b:findings[label].append(ident)
        if o!=oo:
            # Retain only positions and hashes; do not leak text.
            diffs=[]
            for op,a,b,c,d in SequenceMatcher(None,o,oo,autojunk=False).get_opcodes():
                if op!="equal":
                    diffs.append({"kind":op,"source_offset":a,"target_offset":c,
                        "source_length":b-a,"target_length":d-c,
                        "source_sha256":_hash(o[a:b]),"target_sha256":_hash(oo[c:d])})
            findings["unnumbered_text"].append({"book":ident,"differences":diffs[:20]})
    return {"counts":dict(counts),"findings":dict(findings),
            "scope":"title text and numbered positions, selected inline numbered spans, intro paragraph offsets and nonnumbered nonspace text; approved text corrections projected separately; not exact typography or complete structure"}
