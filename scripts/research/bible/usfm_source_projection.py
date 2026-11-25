"""Source-attested conversion projections, independent of publication.

Only exact original-witness spacing, table and paragraph deltas are permitted.
This implementation deliberately fails closed on unsupported source grammar.
"""
from collections import Counter, defaultdict
from hashlib import sha256
from lxml import etree
import sys
from source_osis_inventory import source_inventory, _source_tree, OSIS
from research.bible.original_authorial_content_parity import (
    verify_numbered_content, parse_usfx, source_verses,
)
from research.bible.source_osis_verse_notes import original_osis_verses_and_notes
from research.bible import source_usfx_editorial as editorial

def project(source_xml, xml, mapping, zfm, report):
    """Return a private source-attested candidate; report exact supported proofs."""
    if sys.flags.optimize:
        raise RuntimeError("Conversion requires active validation assertions")
    keys,_=source_inventory(xml)
    report["candidate_numbered_keys"]=len(keys.splitlines())
    proof=verify_numbered_content(source_xml,xml,mapping,{},zfm)
    report["numbered_content_diagnostic"]=proof
    source_root=parse_usfx(source_xml)
    original,_,_,_=source_verses(source_root,mapping)
    converted,_,_=original_osis_verses_and_notes(xml)
    target=_source_tree(xml)
    selah_hosts=Counter()
    for book in target.iter(OSIS+"div"):
        if book.get("type")!="book":continue
        current=None
        for node in book.iter():
            if node.tag==OSIS+"verse":
                if node.get("eID"):current=None
                elif node.get("sID"):current=node.get("sID")
            if node.tag==OSIS+"l" and node.get("type")=="selah":
                assert current is not None
                selah_hosts[current]+=1
    mismatch={k for k in original if " ".join(original[k].split())!=" ".join(converted[k].split())}
    report["selah_spacing_diagnostic"]={
        "mismatch_count":len(mismatch),"selah_count":sum(selah_hosts.values()),
        "selah_host_count":len(selah_hosts),"mismatches_exactly_selah_hosts":mismatch==set(selah_hosts),
        "non_selah_mismatches":sorted(mismatch-set(selah_hosts))[:20],
        "unchanged_selah_hosts":sorted(set(selah_hosts)-mismatch)[:20]}
    refs=[]
    for book in source_root.iter("book"):
        chapter=None
        for node in book.iter():
            if node.tag=="c":chapter=int(node.get("id"))
            if node.tag=="v":refs.append((book.get("id"),chapter,int(node.get("id"))))
    report["poetry_diagnostic"]=editorial.audit_segments(source_root,target,mapping,refs)
    report["table_paragraph_diagnostic"]=editorial.compare_original_tables_and_paragraphs(source_root,target,mapping)
    report["editorial_diagnostic"]=editorial.editorial_diagnostic(source_root,target,mapping)
    # Derive missing whitespace boundaries from the
    # independent original witness, never from a list
    # of Psalms or the previously corrected master.
    def gaps(text):
        result=set();pos=0;pending=False
        for char in text:
            if char.isspace():pending=True
            else:
                if pos and pending:result.add(pos)
                pos+=1;pending=False
        return result
    edits=[];unsupported=[]
    for book in target.iter(OSIS+"div"):
        if book.get("type")!="book":continue
        def append(value):
            state["position"]+=sum(not c.isspace() for c in (value or "")) if state["current"] else 0
        state={"current":None,"position":0}
        def visit(node):
            if not isinstance(node.tag,str):return
            kind=etree.QName(node).localname
            if kind in {"note","title","header"}:return
            container=False
            if kind=="verse":
                if node.get("eID"):
                    assert state["current"]==node.get("eID")
                    state["current"]=None;return
                state["current"]=node.get("osisID");state["position"]=0
                container=not bool(node.get("sID"))
            ref=state["current"];start=state["position"]
            append(node.text)
            for child in node:
                visit(child);append(child.tail)
            end=state["position"]
            if kind=="l" and node.get("type")=="selah" and ref in mismatch:
                missing=gaps(original[ref])-gaps(converted[ref])
                extra=gaps(converted[ref])-gaps(original[ref])
                if extra or not missing or not missing<={start,end}:
                    unsupported.append({"ref":ref,"missing":sorted(missing),"extra":sorted(extra),"marker_offsets":[start,end]})
                else:
                    if start in missing:
                        # Place separation outside the
                        # marker, in its preceding XML text slot.
                        prev=node.getprevious()
                        if prev is not None:prev.tail=(prev.tail or "")+" "
                        else:
                            parent=node.getparent()
                            parent.text=(parent.text or "")+" "
                        edits.append((ref,start,"before"))
                    if end in missing:
                        node.tail=" "+(node.tail or "")
                        edits.append((ref,end,"after"))
            if container:state["current"]=None
        visit(book)
    report["selah_whitespace_projection"]={"edits":len(edits),"source_attested_offsets":[{"ref":r,"offset":o,"side":s} for r,o,s in edits],"unsupported":unsupported[:20]}
    if not unsupported:
        revised=etree.tostring(target,encoding="utf-8",xml_declaration=True)
        result=verify_numbered_content(source_xml,revised,mapping,{},zfm)
        report["selah_whitespace_projection"]["numbered_parity"]=result["all_supported_content_checks_equal"]
        report["selah_whitespace_projection"]["mismatch_counts"]=result["mismatch_counts"]
        report["selah_whitespace_projection"]["poetry_unchanged"]=editorial.audit_segments(source_root,_source_tree(revised),mapping,refs)==report["poetry_diagnostic"]
        report["selah_whitespace_projection"]["candidate_sha256"]=sha256(revised).hexdigest()
        # Reconcile table rows independently, allowing only
        # source-attested removal of leaked format controls
        # and restoration of missing table separators.
        from itertools import accumulate
        table_edits=Counter();table_changes=[]
        old_books={mapping[n.get("id")]:n for n in source_root.iter("book")}
        new_books={n.get("osisID"):n for n in target.iter(OSIS+"div") if n.get("type")=="book"}
        assert list(old_books)==list(new_books)
        def repair_tables(source_book,candidate_book):
            original_tables=list(source_book.iter("table"))
            candidate_tables=list(candidate_book.iter(OSIS+"table"))
            source_rows=[row for table in original_tables for row in table]
            candidate_rows=[row for table in candidate_tables for row in table]
            assert len(source_rows)==len(candidate_rows)
            for row_index,(sr,cr) in enumerate(zip(source_rows,candidate_rows,strict=True),1):
                assert len(sr)==len(cr)
                for cell_index,(sc,cc) in enumerate(zip(sr,cr,strict=True),1):
                    assert (sc.tag=="th")== (cc.get("role")=="label")
                    old=" ".join("".join(sc.itertext()).split())
                    new=" ".join("".join(cc.itertext()).split())
                    if old==new:continue
                    assert r"\i" in new and " ".join(new.replace(r"\i","").split())==old
                    # No blanket cleanup: edit only the
                    # mismatching independently paired cell.
                    for n in cc.iter():
                        for field in ("text","tail"):
                            if n is cc and field=="tail":continue
                            val=getattr(n,field)
                            if val and r"\i" in val:
                                table_edits["removed_literal_controls"]+=val.count(r"\i")
                                setattr(n,field,val.replace(r"\i",""))
                    assert " ".join("".join(cc.itertext()).split())==old
                    table_changes.append({"kind":"remove_source_absent_literal_control","book":candidate_book.get("osisID"),"row":row_index,"cell":cell_index,"removed":new.count(r"\i")})
            expected=list(accumulate(len(t) for t in original_tables))
            actual=list(accumulate(len(t) for t in candidate_tables))
            assert not set(actual)-set(expected)
            offset=0
            for table in candidate_tables:
                rows=list(table)
                bounds=[n-offset for n in expected if offset<n<offset+len(rows)]
                if bounds:
                    assert not table.attrib
                    assert not (table.text or "").strip()
                    assert all(not (row.tail or "").strip() for row in rows)
                    tail=table.tail;table.tail=None
                    parent=table.getparent();previous=table
                    for lo,hi in zip(bounds,bounds[1:]+[len(rows)]):
                        new=etree.Element(OSIS+"table")
                        parent.insert(parent.index(previous)+1,new)
                        for row in rows[lo:hi]:new.append(row)
                        previous=new
                        table_edits["restored_table_separators"]+=1
                        table_changes.append({"kind":"restore_source_table_boundary","book":candidate_book.get("osisID"),"after_row":offset+lo})
                    previous.tail=tail
                offset+=len(rows)
            assert editorial.table_signature(source_book,True)==editorial.table_signature(candidate_book,False)
        for ident in old_books:repair_tables(old_books[ident],new_books[ident])
        table_revised=etree.tostring(target,encoding="utf-8",xml_declaration=True)
        checked=verify_numbered_content(source_xml,table_revised,mapping,{},zfm)
        report["table_projection"]={
            "edits":dict(table_edits),"source_attested_changes":table_changes,
            "numbered_parity":checked["all_supported_content_checks_equal"],
            "mismatch_counts":checked["mismatch_counts"],
            "layout":editorial.compare_original_tables_and_paragraphs(source_root,target,mapping),
            "editorial":editorial.editorial_diagnostic(source_root,target,mapping),
            "poetry_unchanged":editorial.audit_segments(source_root,target,mapping,refs)==report["poetry_diagnostic"],
            "candidate_sha256":sha256(table_revised).hexdigest()}
        # Replay the reviewed generic boundary algorithm in
        # disposable bytes. Obtain exact XML byte offsets
        # from Expat rather than regex matching nested tags.
        from xml.parsers import expat
        raw=table_revised
        root=_source_tree(raw)
        def local(node):return editorial._name(node) if node is not None else ""
        def ns(value):return editorial._no_space(value or "")
        NOTE={"x","f","fe","ef","ex"}
        TITLE={"s","s1","s2","s3","s4","r","sr","mr","ms","ms1","ms2","ms3","mt","mt1","mt2","mt3","imt","imt1","imt2","imt3","is","is1","is2"}
        SRC_STYLE={"p":None,"m":"x-noindent","pi":"x-indented-1","pi1":"x-indented-1"}
        parser=expat.ParserCreate(namespace_separator="|")
        begins=[];ends=[];stack=[]
        def begin_element(name,attrs):
            i=len(begins);begins.append((name.split("|")[-1],parser.CurrentByteIndex));ends.append(None);stack.append(i)
        def end_element(name):
            i=stack.pop();assert begins[i][0]==name.split("|")[-1];ends[i]=parser.CurrentByteIndex
        parser.StartElementHandler=begin_element;parser.EndElementHandler=end_element
        parser.Parse(raw,True)
        nodes=[n for n in root.iter() if isinstance(n.tag,str)]
        assert len(nodes)==len(begins)==len(ends) and not stack
        positions={}
        for node,(tag,offset),end_offset in zip(nodes,begins,ends,strict=True):
            assert local(node)==tag
            positions[node]=(offset,end_offset)
        def scan(book,src):
            pos=0;ref=None;chapter=None;last=None
            starts=[];spans=[];events=defaultdict(list)
            def append(s,owner,field):
                nonlocal pos
                if ref and ns(s):
                    begin=pos;pos+=len(ns(s));spans.append((begin,pos,owner,field,ref,s))
            def walk(n):
                nonlocal ref,chapter,last
                k=local(n)
                if not k:return
                style=n.get('sfm') or n.get('style') or k
                if src and (k in NOTE|{'id','h','toc'}|TITLE or k=='p' and style in TITLE) or not src and k in {'note','title','header'}:
                    if not src and k=='note' and ref:events[pos].append(n)
                    return
                if src and k=='c':chapter=n.get('id')
                if src and k=='v':ref=chapter+'.'+n.get('id');last=ref
                if src and k=='ve':ref=None
                if not src and k=='verse':
                    if n.get('eID'):ref=None
                    else:ref=n.get('osisID').split('.',1)[1];last=ref
                if src and k=='p' and style in SRC_STYLE and pos>0:
                    starts.append((pos,SRC_STYLE[style],n,last))
                if not src and k=='p' and pos>0:
                    assert n.get('type') in set(SRC_STYLE.values())
                    starts.append((pos,n.get('type'),n,last))
                if not src and pos>0:events[pos].append(n)
                append(n.text,n,'text')
                for c in n:
                    walk(c);append(c.tail,c,'tail')
                if not src and k=='verse' and n.get('osisID') and not n.get('sID'):ref=None
            walk(book)
            return starts,spans,events
        books={n.get('osisID'):n for n in root.iter(OSIS+'div') if n.get('type')=='book'}
        patches=[];paragraph_edits=[];expected={}
        inventory=[]
        for book in source_root.iter("book"):
            ident=mapping[book.get("id")]
            ss,_,_=scan(book,True);tt,_,_=scan(books[ident],False)
            surplus=Counter((o,st) for o,st,_,_ in tt)-Counter((o,st) for o,st,_,_ in ss)
            for offset,style,node,ref in tt:
                if surplus[(offset,style)]<=0:continue
                surplus[(offset,style)]-=1
                prev=node.getprevious()
                inventory.append({"book":ident,"ref":ref,"offset":offset,"style":style,
                    "parent":local(node.getparent()),"previous":local(prev),"next":local(node.getnext()),
                    "children":[local(c) for c in node][:12],"text_nonspace":len(ns(node.text)),
                    "body_nonspace":len(ns("".join(node.itertext()))),"tail_nonspace":len(ns(node.tail)),
                    "previous_tail_nonspace":len(ns(prev.tail)) if prev is not None else 0,
                    "attributes":sorted(node.attrib)})
        report["paragraph_boundary_inventory"]=inventory
        for book in source_root.iter('book'):
            ident=mapping[book.get('id')]
            source_starts,_,_=scan(book,True);b,spans,events=scan(books[ident],False)
            expected[ident]=[(pos,style) for pos,style,_,_ in source_starts]
            x=Counter((pos,style) for pos,style,_,_ in source_starts);y=Counter((pos,style) for pos,style,_,_ in b)
            # Distinguish repeated equivalent positions rather than silently skipping them.
            missing=x-y;extra=y-x
            for offset,style,node,ref in b:
                key=(offset,style)
                if extra[key]<=0:continue
                extra[key]-=1
                prev=node.getprevious()
                # Moving a boundary may only remove a direct adjacent paragraph pair.
                if not node.attrib and len(node)==0 and not ns(node.text):
                    op,end=positions[node]
                    if raw[op:op+4]==b'<p/>':
                        patches.append((op,b'<p/>',b''))
                    else:
                        assert raw[op:op+3]==b'<p>' and raw[end:end+4]==b'</p>'
                        payload=raw[op:end+4]
                        assert not payload[3:-4].strip()
                        patches.append((op,payload,payload[3:-4]))
                    paragraph_edits.append({"kind":"remove_surplus_empty_paragraph","book":ident,"ref":ref,"nonspace_offset":offset})
                    continue
                assert local(prev)=='p' and prev.getparent() is node.getparent(),(ident,ref,'nonadjacent paragraph')
                assert set(node.attrib)<= {'type'} and set(prev.attrib)<= {'type'}
                op,end=positions[node];prev_end=positions[prev][1]
                assert raw[prev_end:prev_end+4]==b'</p>'
                opening=raw[op:raw.index(b'>',op)+1]
                assert opening in (b'<p>',b'<p type="x-noindent">',b'<p type="x-indented-1">')
                patches.extend([(prev_end,b'</p>',b''),(op,opening,b'')])
                paragraph_edits.append({'kind':'remove_displaced_boundary','book':ident,'ref':ref,'nonspace_offset':offset,'style':style})
            assert not +extra
            for offset,style,node,ref in source_starts:
                key=(offset,style)
                if missing[key]<=0:continue
                missing[key]-=1
                first=next((n for n in node if isinstance(n.tag,str)),None)
                assert first is not None
                name=local(first)
                desired={'w':'w','wj':'q','it':'hi','x':'note'}.get(name)
                assert desired,(ident,ref,'unsupported source boundary child',name)
                # Prefer the exact direct child (including source-first note).
                candidates=[]
                for n in events[offset]:
                    if local(n)!=desired or local(n.getparent())!='p':continue
                    if desired=='note' and n.get('n')!=first.get('caller'):continue
                    candidates.append(n)
                if candidates:
                    assert len(candidates)==1,(ident,ref,'ambiguous direct-child anchor')
                    point=positions[candidates[0]][0]
                else:
                    # A paragraph start can bisect unannotated prose in a
                    # direct child tail, without changing either text stream.
                    tails=[(lo,hi,n,s) for lo,hi,n,field,r,s in spans if lo<offset<hi and field=='tail' and local(n.getparent())=='p']
                    assert desired=='w' and len(tails)==1,(ident,ref,'no exact safe paragraph anchor',desired)
                    lo,hi,n,s=tails[0]
                    count=0;idx=0
                    while idx<len(s) and count<offset-lo:
                        if not s[idx].isspace():count+=1
                        idx+=1
                    while idx<len(s) and s[idx].isspace():idx+=1
                    assert count==offset-lo and idx<len(s)
                    endpos=positions[n][1]
                    close=b'</'+local(n).encode()+b'>'
                    assert raw[endpos:endpos+len(close)]==close
                    tail_start=endpos+len(close)
                    encoded=s.encode('utf-8')
                    assert raw[tail_start:tail_start+len(encoded)]==encoded,(ident,ref,'nonliteral XML tail')
                    point=tail_start+len(s[:idx].encode('utf-8'))
                opening=b'<p>' if style is None else b'<p type="'+style.encode()+b'">'
                patches.append((point,b'',b'</p>'+opening))
                paragraph_edits.append({'kind':'restore_source_boundary','book':ident,'ref':ref,'nonspace_offset':offset,'style':style,'anchor_kind':desired})
            assert not +missing
        # Verify nonoverlapping edits and reconstruct
        # the exact input from inverse edits before auditing.
        assert len({p[0] for p in patches})==len(patches)
        pieces=[];inverse=[];cursor=0;outpos=0
        for offset,old,new in sorted(patches):
            assert offset>=cursor and raw[offset:offset+len(old)]==old
            prefix=raw[cursor:offset]
            pieces.extend((prefix,new));outpos+=len(prefix)
            inverse.append((outpos,new,old));outpos+=len(new)
            cursor=offset+len(old)
        pieces.append(raw[cursor:])
        final=b"".join(pieces)
        restored=final
        for offset,new,old in reversed(inverse):
            assert restored[offset:offset+len(new)]==new
            restored=restored[:offset]+old+restored[offset+len(new):]
        assert restored==raw
        final_root=_source_tree(final)
        def other_elements(tree):
            return [(n.tag,dict(n.attrib)) for n in tree.iter() if isinstance(n.tag,str) and n.tag!=OSIS+"p"]
        assert other_elements(root)==other_elements(final_root)
        checked=verify_numbered_content(source_xml,final,mapping,{},zfm)
        report["paragraph_projection"]={
            "edits":dict(Counter(e["kind"] for e in paragraph_edits)),
            "source_attested_changes":paragraph_edits,
            "inverse_exact":True,"nonparagraph_elements_unchanged":True,
            "numbered_parity":checked["all_supported_content_checks_equal"],
            "mismatch_counts":checked["mismatch_counts"],
            "layout":editorial.compare_original_tables_and_paragraphs(source_root,final_root,mapping),
            "editorial":editorial.editorial_diagnostic(source_root,final_root,mapping),
            "poetry_unchanged":editorial.audit_segments(source_root,final_root,mapping,refs)==report["poetry_diagnostic"],
            "candidate_sha256":sha256(final).hexdigest()}
        assert checked["all_supported_content_checks_equal"], "Numbered fidelity failed"
        layout=report["paragraph_projection"]["layout"]
        assert layout["supported_table_and_numbered_paragraph_parity"], "Editorial layout fidelity failed"
        assert not report["paragraph_projection"]["editorial"]["findings"], "Editorial fidelity failed"
        assert report["paragraph_projection"]["poetry_unchanged"], "Poetry changed during projection"
        assert report["poetry_diagnostic"]["all_poetry_segments_and_levels_verified"]
        assert report["poetry_diagnostic"]["all_selah_text_and_verse_positions_verified"]
        assert report["poetry_diagnostic"]["source_poetry"]==report["poetry_diagnostic"]["candidate_poetry"]
        return final
    raise ValueError("Unresolved source whitespace boundaries")
