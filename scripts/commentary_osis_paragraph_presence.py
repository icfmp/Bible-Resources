#!/usr/bin/env python3
"""Private source-neutral CCEL paragraph versus authenticated authoring OSIS probe.

Original source words and source binary are kept exclusively in the runner.
This is a whole-document *location* comparison of the precise authored CCEL
paragraphs, not proof of an authorial edition, reference ownership, copyright
permission, corrected commentary source, or published SWORD binary parity.

Input cases are exact original source marker, body and paragraph fingerprints.
A matching OSIS word run may be in an unrelated biblical passage; the probe
NEVER reassigns it to the referenced verse and never exports prose or OSIS keys.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import re

from lxml import etree

from commentary_unresolved_lexical_triage import WORD

SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_SOURCE_BYTES = 90 * 1024 * 1024
MAX_CCEL_BYTES = 32 * 1024 * 1024
MAX_ORIGINAL_CASES = 8
MAX_ORIGINAL_P_WORDS = 5000
MAX_OSIS_WORDS = 10_000_000
MAX_MATCHING_ANCHOR_POSITIONS = 100_000
ANCHOR_WORDS = 8


def _safe_root(raw: bytes, digest: str, limit: int) -> etree._Element:
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= limit
            or not isinstance(digest, str) or not SHA.fullmatch(digest)
            or sha256(raw).hexdigest() != digest):
        raise ValueError("Unauthenticated or oversized original XML")
    try:
        root = etree.fromstring(raw, parser=etree.XMLParser(
            resolve_entities=False, no_network=True, load_dtd=False,
            recover=False, huge_tree=True, remove_blank_text=False,
            strip_cdata=False))
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original XML cannot be parsed without recovery") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError("Original XML contains unresolved entities")
    return root


def original_ccel_paragraph_words(
        original_xml: bytes, *, expected_xml_sha256: str, case: dict) -> list[str]:
    """Locate a whole original paragraph by exact marker line/ref/body/p hash."""
    root = _safe_root(original_xml, expected_xml_sha256, MAX_CCEL_BYTES)
    required = ("original_full_reference_sha256", "original_body_sha256",
                "original_paragraph_word_sha256")
    if (not isinstance(case, dict)
            or any(not isinstance(case.get(k), str)
                   or not SHA.fullmatch(case[k]) for k in required)
            or type(case.get("original_marker_line")) is not int
            or case["original_marker_line"] <= 0
            or type(case.get("original_paragraph_ordinal")) is not int
            or not 1 <= case["original_paragraph_ordinal"] <= 1000
            or type(case.get("original_paragraph_visible_word_count")) is not int
            or not 8 <= case["original_paragraph_visible_word_count"] <= MAX_ORIGINAL_P_WORDS):
        raise ValueError("Unreviewed source paragraph identity")
    matches = [
        node for node in root.iter()
        if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "scripCom"
        and node.sourceline == case["original_marker_line"]
        and sha256(node.get("osisRef", "").encode("utf-8")).hexdigest()
        == case["original_full_reference_sha256"]
    ]
    if len(matches) != 1:
        raise ValueError("Exact original source marker not found")
    marker = matches[0]
    body = marker.getnext()
    if (body is None or not isinstance(body.tag, str)
            or body.tag.rsplit("}", 1)[-1] != "div"
            or (marker.tail and marker.tail.strip())):
        raise ValueError("Original source section adjacency invalid")
    if sha256("".join(body.itertext()).encode("utf-8")).hexdigest() != case[
            "original_body_sha256"]:
        raise ValueError("Original source body hash changed")
    paragraphs = [
        node for node in body.iter()
        if isinstance(node.tag, str) and node.tag.rsplit("}", 1)[-1] == "p"
    ]
    ordinal = case["original_paragraph_ordinal"]
    if ordinal > len(paragraphs):
        raise ValueError("Original source paragraph ordinal absent")
    words = WORD.findall("".join(paragraphs[ordinal-1].itertext()))
    if (len(words) != case["original_paragraph_visible_word_count"]
            or sha256(" ".join(words).encode("utf-8")).hexdigest() != case[
                "original_paragraph_word_sha256"]):
        raise ValueError("Original source paragraph words differ from reviewed SHA")
    return words



 
def original_authoring_chapter_scope_metadata(
        book_div: etree._Element, chapter_ref: str) -> dict:
    """Audit real chapter milestone bounds; never expose or rewrite source words.

    Book ownership and section starts are independent of any proposed missing
    CCEL paragraph; this detects only the authentic OSIS chapter's structural
    span, not historical authorial paragraphs or their verse attribution.
    """
    if (not isinstance(book_div, etree._Element)
            or book_div.tag.rsplit("}",1)[-1]!="div"
            or book_div.get("type")!="book"
            or not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*",
                                chapter_ref)
            or book_div.get("osisID")!=chapter_ref.rsplit(".",1)[0]):
        raise ValueError("Unreviewed original authoring OSIS book/chapter scope")
    from collections import Counter
    state=0
    opens=0
    closes=0
    parts=[]
    elements=Counter()
    def visit(node):
        nonlocal state,opens,closes
        if not isinstance(node.tag,str):
            raise ValueError("Unexpected original OSIS markup node")
        tag=node.tag.rsplit("}",1)[-1]
        if tag=="chapter":
            first=(node.get("sID")==chapter_ref or (
                node.get("osisID")==chapter_ref and not node.get("eID")))
            last=node.get("eID")==chapter_ref
            if first and last:
                raise ValueError("Source chapter start/end conflated")
            if first:
                if opens or state:
                    raise ValueError("Duplicate original source chapter start")
                opens+=1
                state=1
            if last:
                if state!=1 or closes:
                    raise ValueError("Unreviewed original chapter close")
                closes+=1
                state=2
        if state==1:
            if tag in ("p","verse","chapter","title","div","reference","note","q"):
                elements[tag]+=1
            if node.text:
                parts.append(node.text)
        for child in node:
            visit(child)
            if state==1 and child.tail:
                parts.append(child.tail)
    visit(book_div)
    if state!=2 or opens!=1 or closes!=1:
        raise ValueError("Original source chapter milestones incomplete")
    visible="".join(parts)
    words=WORD.findall(visible)
    if not words or len(words)>100_000:
        raise ValueError("Original OSIS chapter prose length unreviewed")
    return {
        "authentic_chapter_milestone_start_end_count":[opens,closes],
        "bounded_original_chapter_visible_words":len(words),
        "original_chapter_visible_text_sha256":sha256(visible.encode("utf-8")).hexdigest(),
        "original_chapter_element_start_counts_by_tag":dict(sorted(elements.items())),
        "no_original_chapter_words_exported":True,
        "not_a_proof_of_original_paragraph_or_verse_ownership":True,
        "no_edits_or_release":True,
    }


def _case_insensitive_length_is_not_used(words: list[str]) -> int:
    """Do not replace exact authorial case by a lossy casefold comparison."""
    return len(words)


def exact_original_paragraph_runs_in_osis(
        original_osis_bytes: bytes, *, expected_osis_sha256: str,
        original_cases: list[tuple[dict, list[str]]]) -> dict:
    """Return only exact-token whole/partial textual *locations* anywhere in OSIS."""
    if not isinstance(original_cases, list) or not 1 <= len(
            original_cases) <= MAX_ORIGINAL_CASES:
        raise ValueError("No authenticated bounded original paragraph cases")
    root = _safe_root(original_osis_bytes, expected_osis_sha256, MAX_SOURCE_BYTES)
    if root.tag.rsplit("}", 1)[-1] != "osis":
        raise ValueError("Official authoring source is not an OSIS XML root")
    # Exact document order of visible source text; OSIS attributes are not
    # displayed prose and are not silently interpolated into comparison.
    osis_text = "".join(root.itertext())
    osis_words = WORD.findall(osis_text)
    del osis_text, root
    if not 1 <= len(osis_words) <= MAX_OSIS_WORDS:
        raise ValueError("Original authoring OSIS visible word count unreviewed")
    anchors = defaultdict(list)
    checked = set()
    results = []
    for n,(identity,paragraph) in enumerate(original_cases):
        if (not isinstance(identity, dict) or not isinstance(paragraph, list)
                or not 8 <= len(paragraph) <= MAX_ORIGINAL_P_WORDS
                or any(not isinstance(w,str) or not w for w in paragraph)
                or not isinstance(identity.get("original_paragraph_word_sha256"),str)
                or sha256(" ".join(paragraph).encode("utf-8")).hexdigest()
                != identity["original_paragraph_word_sha256"]):
            raise ValueError("Unauthenticated comparison case or original prose")
        ref = (identity.get("source_volume"),identity.get("original_marker_line"),
               identity["original_paragraph_word_sha256"])
        if ref in checked:
            raise ValueError("Duplicate original source paragraph identity")
        checked.add(ref)
        results.append({
            "source_volume":identity.get("source_volume"),
            "original_marker_line":identity.get("original_marker_line"),
            "original_paragraph_word_sha256":identity["original_paragraph_word_sha256"],
            "original_paragraph_visible_word_count":len(paragraph),
            "exact_8_word_anchor_occurrences_anywhere_in_osis":0,
            "longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis":0,
            "complete_original_paragraph_exact_word_tokens_anywhere_in_osis":False,
            "source_or_print_edition_identity_not_inferred":True,
        })
        for offset in range(len(paragraph) - ANCHOR_WORDS + 1):
            anchors[tuple(paragraph[offset:offset + ANCHOR_WORDS])].append((n,offset))
    checked_windows = 0
    for start in range(len(osis_words) - ANCHOR_WORDS + 1):
        matched = anchors.get(tuple(osis_words[start:start + ANCHOR_WORDS]))
        if not matched:
            continue
        checked_windows += 1
        if checked_windows > MAX_MATCHING_ANCHOR_POSITIONS:
            raise ValueError("Unreviewed many-to-many original source anchor volume")
        for idx,offset in matched:
            words = original_cases[idx][1]
            tail=ANCHOR_WORDS
            while (offset+tail < len(words) and start+tail < len(osis_words)
                   and words[offset+tail] == osis_words[start+tail]):
                tail += 1
            head=0
            while (offset-head > 0 and start-head > 0
                   and words[offset-head-1] == osis_words[start-head-1]):
                head += 1
            total=head+tail
            row=results[idx]
            row["exact_8_word_anchor_occurrences_anywhere_in_osis"] += 1
            row["longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis"] = max(
                row["longest_exact_case_sensitive_contiguous_word_run_anywhere_in_osis"],
                total)
            if total == len(words):
                row["complete_original_paragraph_exact_word_tokens_anywhere_in_osis"] = True
    return {
        "status":"ORIGINAL_CCEl_PARAGRAPH_AUTHORED_OSIS_ANYWHERE_LOCATION_ONLY",
        "authoring_osis_sha256":expected_osis_sha256,
        "original_osis_visible_word_tokens":len(osis_words),
        "minimum_exact_contiguous_partial_anchor_words":ANCHOR_WORDS,
        "original_ccel_paragraph_cases":results,
        "no_original_source_words_or_osis_keys_exported":True,
        "no_authorial_bible_reference_ownership_proven":True,
        "no_original_source_or_sword_binary_changed":True,
        "no_redistribution_rights_or_publication_approved":True,
    }
