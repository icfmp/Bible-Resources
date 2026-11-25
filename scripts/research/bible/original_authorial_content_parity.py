"""Independent original USFM/USFX and approved OSIS numbered-content diagnostics.

The callers must hash-pin and preflight archives and supply explicit source
member/crosswalk and approved repair data. Unsupported grammar is a blocker,
not a silent fallback. Reports contain counts and reference IDs, never prose.
This is not an importer, a visual-reader check or full structural certification.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import re
from lxml import etree
from source_osis_inventory import OSIS, _source_tree
from research.bible.source_osis_verse_notes import original_osis_verses_and_notes

NOTE={'x','f','fe','ex','ef'}
EXCLUDED={'fig','s','r','toc','h','id'}
EXCLUDED_PARAGRAPH={'r','s','s1','s2','s3','s4','sr','h','toc1','toc2','toc3'}
def local(n): return etree.QName(n).localname if isinstance(n.tag,str) else ""
def ns(s): return ''.join(c for c in (s or '') if not c.isspace())
def require(ok,reason):
    if not ok: raise ValueError(reason)
def strong(value,osis=False):
    if not value: return ()
    if osis:
        parts=value.split()
        if any(not x.startswith('strong:') for x in parts): return None
        parts=[x[7:] for x in parts if x.startswith('strong:')]
    else: parts=[x for x in re.split(r'[\s,]+',value) if x]
    return tuple(parts) if all(re.fullmatch(r'[HG]\d+[a-z]?',x) for x in parts) else None
def source_verses(root,mapping):
    verses={}; notes=defaultdict(list); words=defaultdict(list); outside=0; books=set()
    for book in root.iter():
        if local(book)!='book': continue
        code=book.get('id')
        require(code in mapping and code not in books,'Unreviewed or duplicate book')
        books.add(code)
        chapter=None; key=None; position=0
        def append(value):
            nonlocal position
            if key is not None and value:
                verses[key].append(value)
                position+=len(ns(value))
        def walk(n):
            nonlocal key,chapter,position,outside
            kind=local(n)
            if not kind: return
            if kind=='c':
                require(key is None and re.fullmatch(r'[1-9][0-9]*',n.get('id','')),'Unclosed verse or invalid chapter')
                chapter=n.get('id')
            elif kind=='v':
                require(key is None and chapter and re.fullmatch(r'[0-9]+[a-z]?(?:-[0-9]+[a-z]?)?',n.get('id','')),'Unsupported opening')
                key='.'.join((mapping[code],chapter,n.get('id')))
                require(key not in verses,'Duplicate verse')
                verses[key]=[];position=0
            elif kind=='ve':
                require(key is not None,'Unexpected verse end')
                key=None
            if kind in NOTE:
                if key is None: outside+=1
                else: notes[key].append((position,kind,n.get('caller'),ns(''.join(n.itertext()))))
                return
            if kind in EXCLUDED or (kind=='p' and (n.get('sfm') or n.get('style')) in EXCLUDED_PARAGRAPH):
                return
            word_key=key if kind=='w' else None
            start=position
            if word_key:
                require(not any(local(x) in NOTE|{'w','v','ve','c'} for x in n.iterdescendants()),'Unsupported nested USFX word')
            append(n.text)
            for c in n:
                walk(c);append(c.tail)
            if word_key:
                require(key==word_key and position>start,'Invalid USFX word scope')
                words[word_key].append((start,position,ns(''.join(n.itertext())),strong(n.get('s'))))
        walk(book)
        require(key is None,'Unclosed verse at book boundary')
    return {k:''.join(v) for k,v in verses.items()},notes,outside,words
def usfm_numbered_content(archive,mapping):
    marker=re.compile(r'\\(\+?[a-z][a-z0-9-]*)(\*|(?=\s|\\|$))|\\\*')
    # USFM paragraph/poetry markers start a new logical block.
    body_blocks={'p','m','pi1','q1','b','tr','tc1','tc2','tc3','th1','th2'}
    apparatus={'h','toc1','toc2','imt1','imt2','imt3','io1','io2','ip','ipi','ib','ie','is1','mt1','mt2','mr','ms1','ms2','s1','r'}
    inline={'wj','it','ord','qs','ior'}
    texts={}; words=defaultdict(list); note_rows=defaultdict(list); books=set()
    for member in archive.infolist():
        if member.is_dir() or not member.filename.lower().endswith(('.usfm','.sfm')):continue
        raw=archive.read(member).decode('utf-8-sig')
        matches=list(marker.finditer(raw))
        require(bool(matches) and not raw[:matches[0].start()].strip(),'USFM content before initial marker')
        code=None; chapter=None; key=None; enabled=False
        stack=[]; current_word=None; current_note=None
        pos=0
        def append(text):
            nonlocal pos
            if key and enabled:
                texts[key].append(text);pos+=len(ns(text))
        for i,m in enumerate(matches):
            tag=m[1]; closing=bool(m[2])
            tail=raw[m.end():matches[i+1].start() if i+1<len(matches) else len(raw)]
            require(tag is not None,'Unsupported standalone USFM milestone close')
            # A start marker consumes its single syntactic whitespace separator.
            if not closing:
                require(bool(tail) and tail[0].isspace(),'USFM start marker lacks separator')
                tail=tail[1:]
            if tag in {'id','c','v'}:
                require(not closing and not stack and current_note is None and current_word is None,'Invalid USFM numbering scope')
                match=re.match(r'([^\s]+)(?:[ \t]|\r?\n|$)',tail)
                require(match is not None,'Missing USFM numbering label')
                val=match[1]; rest=tail[match.end():]
                if tag=='id':
                    require(code is None and val in mapping and val not in books,'Unknown or duplicate USFM book')
                    code=val;books.add(code);enabled=False
                elif tag=='c':
                    require(code and re.fullmatch(r'[1-9][0-9]*',val),'Invalid USFM chapter')
                    chapter=val;key=None;enabled=False
                else:
                    require(code and chapter and re.fullmatch(r'[0-9]+[a-z]?(?:-[0-9]+[a-z]?)?',val),'Unsupported USFM verse')
                    key='.'.join((mapping[code],chapter,val));require(key not in texts,'Duplicate USFM verse')
                    texts[key]=[];pos=0;enabled=True;append(rest)
                continue
            if tag in apparatus|body_blocks:
                require(not closing and not stack and current_word is None and current_note is None,'Block inside inline scope')
                # Headings/introductions end the current numbered content.
                if tag in apparatus:enabled=False
                # Tables preceding the first verse are not numbered text.
                elif key:
                    # A paragraph can resume the same verse after an intervening section heading.
                    enabled=True;append(tail)
                continue
            if tag in NOTE:
                require(current_word is None,'Note inside lexical word')
                if not closing:
                    require(current_note is None,'Nested USFM note')
                    caller=re.match(r'(\S+)(?:\s|$)',tail)
                    require(caller is not None,'Missing USFM note caller')
                    current_note=[tag,caller[1],pos,[]]
                    if caller.end()<len(tail):current_note[3].append(caller.string[caller.end():])
                else:
                    require(current_note is not None and current_note[0]==tag,'Unpaired USFM note')
                    if key and enabled:note_rows[key].append((current_note[2],tag,current_note[1],ns(''.join(current_note[3]))))
                    current_note=None;append(tail)
                continue
            if current_note is not None:
                require(tag in {'xo','xt','fr','ft','fq','fqa','fk','fl','fp','fv','fdc','xq','xot','xnt','xdc'},'Unsupported note component')
                current_note[3].append(tail);continue
            if tag in {'w','+w'}:
                if not closing:
                    require(current_word is None,'Nested USFM word')
                    parts=tail.split('|')
                    require(len(parts)==2,'Unsupported USFM word attribute syntax')
                    pairs=re.findall(r'([a-z][a-z0-9-]*)="([^"]*)"',parts[1])
                    attrs=dict(pairs)
                    require(len(attrs)==len(pairs) and set(attrs)<={'strong','s'},'Unreviewed USFM lexical attributes')
                    # Reject unparsed attributes, not merely ignore them.
                    remaining=re.sub(r'[a-z][a-z0-9-]*="[^"]*"','',parts[1])
                    require(not remaining.strip(),'Unsupported USFM word attribute')
                    current_word=(tag,key if enabled else None,pos,parts[0],attrs)
                    append(parts[0])
                else:
                    require(current_word is not None and current_word[0]==tag,'Unpaired USFM word')
                    _,word_key,start,surface,attrs=current_word
                    if word_key:
                        require(key==word_key,'USFM word crosses verse')
                        ids=strong(attrs.get('strong') or attrs.get('s'))
                        words[key].append((start,pos,ns(surface),ids))
                    current_word=None;append(tail)
                continue
            if tag in inline:
                require(current_word is None,'Inline marker inside word')
                if closing:
                    require(stack and stack[-1]==tag,'Unpaired USFM inline marker');stack.pop()
                else:stack.append(tag)
                append(tail);continue
            raise ValueError('Unreviewed USFM marker '+tag)
        require(code and current_word is None and current_note is None and not stack,'Unclosed USFM structure')
    return {k:''.join(v) for k,v in texts.items()},words,note_rows
def osis_numbered_words(root):
    rows=defaultdict(list); keys=set()
    for book in root.iter(OSIS+'div'):
        if book.get('type')!='book':continue
        key=None; pos=0
        def append(value):
            nonlocal pos
            if key is not None:pos+=len(ns(value))
        def visit(n):
            nonlocal key,pos
            kind=local(n)
            if not kind or kind in {'note','title','header'}:return
            container=False
            if kind=='verse':
                if n.get('eID'):
                    require(key==n.get('eID'),'OSIS closing mismatch')
                    key=None
                    return
                require(key is None and n.get('osisID') and n.get('osisID') not in keys,'Invalid OSIS opening')
                key=n.get('osisID');keys.add(key);pos=0
                container=not bool(n.get('sID'))
            word_key=key if kind=='w' else None
            start=pos
            if word_key:
                require(not any(local(x) in {'w','verse','note','title'} for x in n.iterdescendants()),'Unsupported nested OSIS word')
            append(n.text)
            for child in n:
                visit(child);append(child.tail)
            if word_key:
                require(key==word_key and pos>start,'Invalid OSIS word scope')
                rows[word_key].append((start,pos,ns(''.join(n.itertext())),strong(n.get('lemma'),True)))
            if container:key=None
        visit(book)
        require(key is None,'Unclosed OSIS verse')
    return rows,keys
def lexical(root,osis):
    rows=[]; unknown=Counter(); fields=Counter()
    for n in root.iter():
        if local(n)!='w':continue
        fields.update(etree.QName(a).localname for a in n.attrib)
        ids=strong(n.get('lemma' if osis else 's'),osis)
        if ids is None: unknown['unparsed_strong']+=1
        rows.append((ns(''.join(n.itertext())),ids))
    return rows,unknown,fields

def parse_usfx(raw):
    require(not re.search(rb"<!DOCTYPE\b",raw,re.I),"Forbidden USFX DTD")
    root=etree.fromstring(raw,etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    require(local(root)=="usfx" and not any(isinstance(x,etree._Entity) for x in root.iter()),"Invalid USFX root or entity")
    return root

def verify_numbered_content(raw, xml, mapping, approved_repairs=None, usfm_archive=None):
    """Compare independent numbered prose, notes and Strong spans.

    approved_repairs maps (OSIS verse, caller) to (old label, new label).
    Caller is responsible for verifying immutable original and editorial
    authorization. This routine independently checks every exact replacement
    against the complete note, not a whitelist of verse IDs.
    """
    approved_repairs=approved_repairs or {}
    require(mapping and len(mapping)==len(set(mapping.values())),"Ambiguous crosswalk")
    root=parse_usfx(raw)
    original,notes,outside,source_words=source_verses(root,mapping)
    target,target_notes,meta=original_osis_verses_and_notes(xml)
    require(original and set(original)==set(target),"Original/OSIS key mismatch")
    target_root=_source_tree(xml)
    target_words,word_keys=osis_numbered_words(target_root)
    require(word_keys==set(target),"Independent OSIS word walker key mismatch")
    counts=Counter(); findings=defaultdict(list); matched_repairs=set()
    def check(kind,ok,ref):
        counts[kind+"_compared"]+=1
        counts[kind+"_equal"]+=bool(ok)
        if not ok and len(findings[kind])<20:findings[kind].append(ref)
    for ref in original:
        a,b=original[ref],target[ref]
        check("verse_nonspace",ns(a)==ns(b),ref)
        check("verse_folded_whitespace"," ".join(a.split())==" ".join(b.split()),ref)
        sw,tw=source_words[ref],target_words[ref]
        check("verse_ordered_word_spans",sw==tw and all(x[3] is not None for x in sw),ref)
        x,y=notes[ref],target_notes[ref]
        check("verse_note_count",len(x)==len(y),ref)
        for i,(old,new) in enumerate(zip(x,y),1):
            loc=ref+"#"+str(i)
            unchanged=old[3]==ns(new["body"])
            check("note_body_nonspace",unchanged,loc)
            repair_key=(ref,old[2])
            if repair_key in approved_repairs:
                before,after=map(ns,approved_repairs[repair_key])
                require(before and before!=after and old[3].count(before)==1 and old[3].replace(before,after,1)==ns(new["body"]),"Exact approved note repair does not explain complete note")
                require(new["caller"]==old[2] and repair_key not in matched_repairs,"Ambiguous repair application")
                matched_repairs.add(repair_key)
            check("note_body_equal_or_reviewed_repair",unchanged or repair_key in matched_repairs,loc)
            check("note_anchor_nonspace",old[0]==new["point"],loc)
            check("note_caller",old[2]==new["caller"],loc)
            check("note_kind",old[1]=="x" and new["type"]=="crossReference",loc)
    require(matched_repairs==set(approved_repairs),"Unaccounted approved note repair")
    a,au,af=lexical(root,False); b,bu,bf=lexical(target_root,True)
    check("global_lexical_count",len(a)==len(b),"all_books")
    for i,(left,right) in enumerate(zip(a,b),1):
        check("global_word_and_strong",left==right and left[1] is not None,i)
    check("source_word_attribute_scope",set(af)<={"s"} and set(bf)<={"lemma"} and not au and not bu,"all_books")
    check("outside_verse_notes_absent",outside==0 and meta["publisher_notes_outside_numbered_verses"]==0,"all_books")
    if usfm_archive is not None:
        fm_text,fm_words,fm_notes=usfm_numbered_content(usfm_archive,mapping)
        require(set(fm_text)==set(original),"Original USFM/USFX key mismatch")
        for ref in original:
            fm=fm_text[ref]
            check("usfm_verse_nonspace",ns(fm)==ns(original[ref]),ref)
            check("usfm_verse_folded_whitespace"," ".join(fm.split())==" ".join(original[ref].split()),ref)
            check("usfm_note_rows",fm_notes[ref]==notes[ref],ref)
            check("usfm_word_span_rows",fm_words[ref]==source_words[ref] and all(x[3] is not None for x in fm_words[ref]),ref)
    mismatches={k:v-counts[k.replace("_compared","_equal")] for k,v in counts.items() if k.endswith("_compared") and k!="note_body_nonspace_compared" and v!=counts[k.replace("_compared","_equal")]}
    return {"all_supported_content_checks_equal":not mismatches,"mismatch_counts":mismatches,"counts":dict(sorted(counts.items())),"bounded_findings":dict(findings),"original_usfx_xml_sha256":sha256(raw).hexdigest(),"cleaned_osis_sha256":sha256(xml).hexdigest(),"source_numbered_word_elements":sum(map(len,source_words.values())),"osis_numbered_word_elements":sum(map(len,target_words.values())),"global_source_word_elements":len(a),"global_osis_word_elements":len(b),"reviewed_note_repairs_verified":len(matched_repairs),"independent_usfm_numbered_content_checked":usfm_archive is not None,"scope":"numbered prose, cross-reference note bodies/callers/anchors, numbered Strong spans, global word sequence; not full USFM grammar, destination mappings, outside-verse lexical placement, exact whitespace or editorial layout"}
