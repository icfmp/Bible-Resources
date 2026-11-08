#!/usr/bin/env python3
"""Independent source-key coverage audit against installed SWORD v11n tables.

The small companion C++ tool reads chapter ceilings through libsword's
VersificationMgr. No Bible text, custom canon or revised verses are produced.
This is a *screening* step, never a replacement for a complete SWORD
source-to-module round-trip or authorial verse-boundary review.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import subprocess

from lxml import etree
from pilot_preflight import PilotError
from lsg_source_compare import scan_usfx

OSIS="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
REGISTRY_NAME=re.compile(r"^[A-Za-z][A-Za-z0-9]{0,31}$")
OSIS_BOOK_NAME=re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]{0,31}$")


def parse_ceilings(output: str) -> dict[str,dict[tuple[str,int],int]]:
    """Reject malformed/partial library inventories rather than guessing."""
    systems=defaultdict(dict)
    for line_number,line in enumerate(output.splitlines(),1):
        cols=line.split("\t")
        if len(cols)!=4:
            raise PilotError(f"Malformed SWORD v11n line {line_number}")
        v11n,book,chapter,verse_max=cols
        if not REGISTRY_NAME.fullmatch(v11n) or not OSIS_BOOK_NAME.fullmatch(book):
            raise PilotError(f"Unreviewed SWORD registry/book at line {line_number}")
        if not chapter.isdecimal() or not verse_max.isdecimal():
            raise PilotError(f"Non-numeric SWORD v11n chapter at line {line_number}")
        chapter_num=int(chapter)
        max_num=int(verse_max)
        if not (1<=chapter_num<=200 and 1<=max_num<=500):
            raise PilotError(f"Out-of-range SWORD v11n row {line_number}")
        key=(book,chapter_num)
        if key in systems[v11n]:
            raise PilotError(f"Duplicate chapter in SWORD v11n: {v11n} {book}.{chapter_num}")
        systems[v11n][key]=max_num
    if not systems or "Segond" not in systems or "NRSV" not in systems:
        raise PilotError("Installed SWORD library did not report reviewed baseline registries")
    for name,chapters in systems.items():
        per_book=defaultdict(set)
        for book,chapter in chapters:
            per_book[book].add(chapter)
        for book,numbers in per_book.items():
            if numbers!=set(range(1,max(numbers)+1)):
                raise PilotError(f"SWORD registry {name} skips {book} chapter identifiers")
    return dict(systems)


def compare_source_keys(keys: list[tuple[str,int,int]] | set[tuple[str,int,int]],
                        usfm_to_osis: dict[str,str],
                        inventory: dict[str,dict[tuple[str,int],int]]) -> dict:
    """Compare every original reference with registered numeric chapter limits.

    Extra registry slots can be ordinary omitted verses or editorial blanks.
    Missing source keys are blocking. Exact numeric coverage does *not* certify
    SWORD's verse-to-verse mapping or word/markup placement.
    """
    source_set=set(keys)
    if not source_set or len(source_set)!=len(keys):
        raise PilotError("Missing or repeated source verse IDs in SWORD v11n screen")
    source_books={x[0] for x in source_set}
    if set(usfm_to_osis)!=source_books or len(set(usfm_to_osis.values()))!=len(usfm_to_osis):
        raise PilotError("Source-to-OSIS book mapping is incomplete or duplicated")
    source_chapters=defaultdict(set)
    for code,ch,verse in source_set:
        if not (isinstance(ch,int) and isinstance(verse,int) and ch>=1 and verse>=1):
            raise PilotError("Unsupported authored chapter/verse identifier")
        source_chapters[(usfm_to_osis[code],ch)].add(verse)
    result=[]
    for system,chapters in sorted(inventory.items()):
        missing=[]
        extras=[]
        unknown_chapters=[]
        allowed=0
        extra_count=0
        for (book,chapter),original in sorted(source_chapters.items()):
            ceiling=chapters.get((book,chapter))
            if ceiling is None:
                unknown_chapters.append(f"{book}.{chapter}")
                missing.extend(f"{book}.{chapter}.{n}" for n in sorted(original))
                continue
            over=[v for v in original if v>ceiling]
            missing.extend(f"{book}.{chapter}.{v}" for v in sorted(over))
            allowed+=len(original)-len(over)
            free=[v for v in range(1,ceiling+1) if v not in original]
            extra_count+=len(free)
            if len(extras)<50:
                extras.extend(f"{book}.{chapter}.{v}" for v in free[:50-len(extras)])
        result.append({
            "system":system,
            "source_references_representable_by_numeric_slots":allowed,
            "source_references_outside_registry":len(missing),
            "registry_slots_unoccupied_by_original_in_authored_chapters":extra_count,
            "source_chapters_not_in_registry":len(unknown_chapters),
            "first_source_references_outside_registry":missing[:70],
            "first_unoccupied_registry_slots":extras[:50],
            "all_original_reference_numbers_have_slots":not missing,
            "exact_source_slot_set":not missing and extra_count==0,
            "original_verse_content_and_boundaries_verified":False,
            "approved_for_publication":False,
        })
    result.sort(key=lambda x:(
        x["source_references_outside_registry"],
        x["source_chapters_not_in_registry"],
        x["registry_slots_unoccupied_by_original_in_authored_chapters"],
        x["system"],
    ))
    return {
        "source_reference_count":len(source_set),
        "original_chapter_count":len(source_chapters),
        "source_book_count":len(source_books),
        "registered_system_count":len(result),
        "registry_source":"actual installed CrossWire SWORD VersificationMgr",
        "candidate_registry_comparisons":result,
        "exact_numeric_slot_candidate_names":[
            x["system"] for x in result if x["exact_source_slot_set"]
        ],
        "full_verse_mapping_verified":False,
        "approved_for_publication":False,
        "limitation":"Chapter maxima alone do not prove verse order, alternate "
                     "versification mappings, empty editorial slots or display fidelity.",
    }


def audit_publisher_usfx_against_installed_sword(
        usfx: bytes, converted_osis_path: Path,
        helper_binary: Path) -> dict:
    """On a disposable CI runner, query libsword; export metadata only."""
    source,keys=scan_usfx(usfx)
    original_codes=source["original_books"]
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False)
    document=etree.parse(str(converted_osis_path),parser=parser)
    candidate_books=[
        e.get("osisID") for e in document.iter(OSIS+"div")
        if e.get("type")=="book"
    ]
    if (len(original_codes)!=66 or len(candidate_books)!=66
            or len(set(candidate_books))!=66 or not all(candidate_books)):
        raise PilotError("Source/candidate books not independently aligned for v11n")
    mapping=dict(zip(original_codes,candidate_books))
    helper=Path(helper_binary)
    if not helper.is_file() or helper.is_symlink():
        raise PilotError("Missing/unsafe installed-SWORD registry inspector")
    try:
        check=subprocess.run([str(helper)],capture_output=True,check=False,
                             text=True,timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise PilotError("Timed out reading installed SWORD registries") from exc
    if check.returncode or check.stderr.strip() or len(check.stdout)>8_000_000:
        raise PilotError("Installed SWORD registry enumeration failed")
    inventory=parse_ceilings(check.stdout)
    return compare_source_keys(keys,mapping,inventory)
