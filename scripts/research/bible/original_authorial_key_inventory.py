"""Read-only exact raw USFM/USFX numbering inventory, not a format converter.
Callers must preflight and hash-pin ZIPs before reading; USFX member is explicit.
Unsupported label forms fail closed. No claim of prose/notes or canon equivalence.
"""
from collections import Counter
import re
from lxml import etree

BOOK=re.compile(r'[A-Z0-9]{3}\Z')
LABEL=re.compile(r'[0-9]+[a-z]?(?:-[0-9]+[a-z]?)?\Z')
MARKER=re.compile(r'\\(\+?[a-z][a-z0-9-]*)(\*|(?=\s|\\|$))|\\\*')
# Closing markers may be immediately followed by punctuation or text.
# This is valid USFM, not an unclosed note or a new verse in a note.
NOTE={'f','fe','ef','x','ex'}
def require(condition,reason):
    if not condition: raise ValueError(reason)
def label(value):
    require(bool(value and LABEL.fullmatch(value)), 'Unsupported original verse label')
    # Preserve labels literally. Reject descending numeric bridges instead of expanding.
    parts=value.split('-')
    if len(parts)==2:
        require(int(re.match(r'\d+',parts[0])[0])<=int(re.match(r'\d+',parts[1])[0]),'Descending original verse bridge')
    return value
def word_after(text,pos):
    match=re.match(r'[ \t]+([^ \t\r\n\\]+)',text[pos:])
    require(match is not None,'Missing marker label')
    return match[1]
def usfm(archive):
    books={}
    markers=Counter()
    for member in archive.infolist():
        if member.is_dir() or not member.filename.lower().endswith(('.sfm','.usfm')):continue
        text=archive.read(member).decode('utf-8-sig')
        book=None; chapter=None; keys=[]; chapters=[]; notes=[]
        for m in MARKER.finditer(text):
            kind=m[1]
            if kind is None: continue
            markers[kind+('*' if m[2] else '')]+=1
            if kind in NOTE:
                if m[2]:
                    require(notes and notes[-1]==kind,'Unpaired USFM note marker')
                    notes.pop()
                else: notes.append(kind)
            if kind not in {'id','c','v'} or m[2]:continue
            require(not notes,'Key marker nested inside note: '+str(book)+' chapter '+str(chapter)+' marker '+kind+' open note types '+','.join(notes))
            value=word_after(text,m.end())
            if kind=='id':
                require(book is None and BOOK.fullmatch(value),'Invalid or duplicate USFM book marker')
                book=value
            elif kind=='c':
                require(book and re.fullmatch(r'[1-9][0-9]*',value),'Invalid USFM chapter')
                require(value not in chapters,'Duplicate USFM chapter')
                chapter=value;chapters.append(value)
            else:
                require(book and chapter,'USFM verse outside book/chapter')
                keys.append((chapter,label(value)))
        require(book and book not in books and not notes,'Missing/duplicate book or unclosed note')
        require(len(keys)==len(set(keys)),'Duplicate exact USFM verse label')
        books[book]=keys
    require(bool(books),'No USFM books')
    return books,markers
def usfx(archive, member_name):
    # Selection belongs to the provider adapter, not the format parser.
    members=[m for m in archive.infolist() if not m.is_dir() and m.filename==member_name]
    require(len(members)==1,'Expected one explicit USFX XML member')
    raw=archive.read(members[0])
    require(not re.search(rb'<!DOCTYPE\b',raw,re.I),'Unexpected USFX DTD')
    root=etree.fromstring(raw,etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,recover=False))
    require(etree.QName(root).localname=='usfx','Wrong source root')
    require(not any(isinstance(x,etree._Entity) for x in root.iter()),'Unresolved USFX entity')
    books={};markers=Counter()
    for book in root.iter():
        if not isinstance(book.tag,str) or etree.QName(book).localname!='book': continue
        require(not any(isinstance(a.tag,str) and etree.QName(a).localname=='book' for a in book.iterancestors()),'Nested USFX book')
        ident=book.get('id')
        require(ident and BOOK.fullmatch(ident) and ident not in books,'Invalid or duplicate USFX book')
        chapter=None;keys=[];chapters=[]
        for n in book.iter():
            if not isinstance(n.tag,str):continue
            kind=etree.QName(n).localname
            markers[kind]+=1
            if kind not in {'c','v'}:continue
            require(not any(etree.QName(a).localname in NOTE for a in n.iterancestors()),'USFX numbering inside note')
            value=n.get('id')
            if kind=='c':
                require(value and re.fullmatch(r'[1-9][0-9]*',value),'Invalid USFX chapter')
                require(value not in chapters,'Duplicate USFX chapter')
                chapter=value;chapters.append(value)
            else:
                require(chapter,'USFX verse before chapter')
                keys.append((chapter,label(value)))
        require(len(keys)==len(set(keys)),'Duplicate exact USFX verse label')
        books[ident]=keys
    require(bool(books),'No USFX books')
    return books,markers
def compare(a,b):
    diffs=[]
    for book in sorted(set(a)|set(b)):
        if a.get(book)==b.get(book):continue
        x,y=a.get(book,[]),b.get(book,[])
        diffs.append({'book':book,'left_count':len(x),'right_count':len(y),'left_only':sorted(set(x)-set(y))[:8],'right_only':sorted(set(y)-set(x))[:8]})
    return {'book_sets_equal':set(a)==set(b),'ordered_labels_within_every_book_equal':not diffs,'different_books':len(diffs),'findings':diffs[:20]}
def summary(books):
    return {'books':len(books),'raw_verse_labels':sum(map(len,books.values())),'bridges':sum('-' in v for rows in books.values() for _,v in rows),'suffixes':sum(bool(re.search('[a-z]',v)) for rows in books.values() for _,v in rows)}
