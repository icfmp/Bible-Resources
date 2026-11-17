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
        book_div: etree._Element, chapter_ref: str,
        *, _private_words_sink: list[str] | None = None,
        _private_visible_text_sink: list[str] | None = None,
        _private_reference_targets_sink: list[str] | None = None,
        _private_before_first_chapter_words_sink: list[str] | None = None,
        _private_word_owner_classes_sink: list[str] | None = None) -> dict:
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
    if (_private_before_first_chapter_words_sink is not None
            and not chapter_ref.endswith(".1")):
        raise ValueError("Book prechapter witness requires real chapter one")
    from collections import Counter
    state=0
    opens=0
    closes=0
    parts=[]
    prechapter_parts=[]
    reference_targets=[]
    elements=Counter()
    owner_fragments=[]
    need_owners=_private_word_owner_classes_sink is not None
    if need_owners and (
            type(_private_word_owner_classes_sink) is not list
            or _private_word_owner_classes_sink):
        raise ValueError("Original private word owner sink must be empty")
    def owner_class(path):
        if "note" in path:
            return "note"
        if "title" in path:
            return "title"
        if "p" in path:
            return "paragraph_reference" if "reference" in path else "paragraph"
        if "q" in path or "l" in path:
            return "poetry"
        if "div" in path:
            return "unwrapped_div"
        return "unwrapped_other"
    def visit(node,path=()):
        nonlocal state,opens,closes
        if not isinstance(node.tag,str):
            # XML comments/processing instructions are not visible authored
            # prose. Their following tails are consumed by the parent walker.
            # Keep genuine unresolved entities fail-closed.
            if isinstance(node,(etree._Comment,etree._ProcessingInstruction)):
                return
            raise ValueError("Unexpected original OSIS markup node")
        tag=node.tag.rsplit("}",1)[-1]
        own_path=path+(tag,) if need_owners else ()
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
            if tag == "reference":
                # Preserve the exact original OSIS link target, including
                # absent/empty attributes as empty strings. No normalization.
                reference_targets.append(node.get("osisRef") or "")
                if len(reference_targets)>5000:
                    raise ValueError("Unreviewed original OSIS reference volume")
            if node.text:
                parts.append(node.text)
                if need_owners:
                    owner_fragments.append((node.text,owner_class(own_path)))
        elif (state==0 and opens==0
              and _private_before_first_chapter_words_sink is not None
              and node.text):
            prechapter_parts.append(node.text)
        for child in node:
            visit(child,own_path)
            if state==1 and child.tail:
                parts.append(child.tail)
                if need_owners:
                    owner_fragments.append((child.tail,owner_class(own_path)))
            elif (state==0 and opens==0
                  and _private_before_first_chapter_words_sink is not None
                  and child.tail):
                prechapter_parts.append(child.tail)
    visit(book_div)
    if state!=2 or opens!=1 or closes!=1:
        raise ValueError("Original source chapter milestones incomplete")
    visible="".join(parts)
    words=WORD.findall(visible)
    if need_owners:
        spans=[]
        offset=0
        for segment,owner in owner_fragments:
            next_offset=offset+len(segment)
            spans.append((offset,next_offset,owner))
            offset=next_offset
        if offset!=len(visible):
            raise ValueError("Private original word owners do not reconstruct source visible text")
        pos=0
        for word in WORD.finditer(visible):
            while pos<len(spans) and word.start()>=spans[pos][1]:
                pos+=1
            if pos>=len(spans) or word.start()<spans[pos][0]:
                raise ValueError("Unowned original source visible word")
            owner=(spans[pos][2] if word.end()<=spans[pos][1]
                   else "cross_fragment_visible_word")
            _private_word_owner_classes_sink.append(owner)
        if len(_private_word_owner_classes_sink)!=len(words):
            raise ValueError("Original private XML word ownership did not align")
    if not words or len(words)>100_000:
        raise ValueError("Original OSIS chapter prose length unreviewed")
    # Only a deliberate in-process private caller can receive the original
    # tokens; JSON metadata/audit reports never contain this sink.
    if _private_words_sink is not None:
        if type(_private_words_sink) is not list or _private_words_sink:
            raise ValueError("Original chapter private word sink must be an empty list")
        _private_words_sink.extend(words)
    if _private_visible_text_sink is not None:
        if (type(_private_visible_text_sink) is not list
                or _private_visible_text_sink):
            raise ValueError("Original chapter private visible text sink must be empty")
        _private_visible_text_sink.append(visible)
    if _private_reference_targets_sink is not None:
        if (type(_private_reference_targets_sink) is not list
                or _private_reference_targets_sink):
            raise ValueError("Original private reference sink must be empty")
        _private_reference_targets_sink.extend(reference_targets)
    original_pre_chapter_words=None
    if _private_before_first_chapter_words_sink is not None:
        if (type(_private_before_first_chapter_words_sink) is not list
                or _private_before_first_chapter_words_sink):
            raise ValueError("Original prechapter word sink must be empty")
        original_pre_chapter_words=WORD.findall("".join(prechapter_parts))
        if len(original_pre_chapter_words)>100_000:
            raise ValueError("Unreviewed original first-chapter prelude size")
        _private_before_first_chapter_words_sink.extend(
            original_pre_chapter_words)
    return {
        "authentic_chapter_milestone_start_end_count":[opens,closes],
        "bounded_original_chapter_visible_words":len(words),
        "bounded_original_chapter_reference_elements":len(reference_targets),
        "private_original_word_ownership_verified":need_owners,
        "original_book_text_before_first_chapter_visible_words":(
            None if original_pre_chapter_words is None
            else len(original_pre_chapter_words)),
        "book_prelude_not_inferred_as_chapter_intro_owner":True,
        "original_chapter_visible_text_sha256":sha256(visible.encode("utf-8")).hexdigest(),
        "original_chapter_element_start_counts_by_tag":dict(sorted(elements.items())),
        "no_original_chapter_words_exported":True,
        "not_a_proof_of_original_paragraph_or_verse_ownership":True,
        "no_edits_or_release":True,
    }




def _private_whole_token_contiguous(
        original: list[str], candidate: list[str]) -> bool:
    """Exact whole-token contiguous match via KMP; no text is returned."""
    if not candidate or len(candidate) > len(original):
        return False
    failure = [0] * len(candidate)
    match = 0
    for i in range(1, len(candidate)):
        while match and candidate[i] != candidate[match]:
            match = failure[match-1]
        if candidate[i] == candidate[match]:
            match += 1
            failure[i] = match
    match = 0
    for word in original:
        while match and word != candidate[match]:
            match = failure[match-1]
        if word == candidate[match]:
            match += 1
            if match == len(candidate):
                return True
    return False


def _private_exact_token_match_offsets(
        original: list[str], candidate: list[str], *,
        maximum_positions: int = 1000) -> list[int]:
    """All exact full-body positions, bounded; no source tokens returned.

    This deliberately checks the WHOLE candidate. Short shared anchors are
    not enough to assign a real native body to an authored source interval.
    """
    if not candidate or len(candidate) > len(original):
        return []
    failure = [0] * len(candidate)
    matched = 0
    for pos in range(1, len(candidate)):
        while matched and candidate[pos] != candidate[matched]:
            matched = failure[matched-1]
        if candidate[pos] == candidate[matched]:
            matched += 1
            failure[pos] = matched
    matched = 0
    offsets = []
    for pos, word in enumerate(original):
        while matched and word != candidate[matched]:
            matched = failure[matched-1]
        if word == candidate[matched]:
            matched += 1
            if matched == len(candidate):
                offsets.append(pos + 1 - len(candidate))
                if len(offsets) > maximum_positions:
                    raise ValueError(
                        "Repeated exact original source body locations exceed reviewed bounds")
                matched = failure[matched-1]
    return offsets


def _private_whole_token_subsequence(
        original: list[str], candidate: list[str]) -> bool:
    """All candidate words in order; skipped source words remain unclaimed."""
    if not candidate or len(candidate) > len(original):
        return False
    position = 0
    for word in original:
        if word == candidate[position]:
            position += 1
            if position == len(candidate):
                return True
    return False


def _private_native_word_relation(source: list[str], native: list[str]) -> str:
    """Conservative token-only category; never maps back to a verse or p."""
    if not native:
        return "native_empty_visible_text"
    if native == source:
        return "native_whole_chapter_exact_tokens"
    if _private_whole_token_contiguous(source, native):
        return "native_contiguous_exact_tokens_in_chapter"
    if _private_whole_token_subsequence(source, native):
        return "native_ordered_exact_subsequence_only"
    source_folded = [word.casefold() for word in source]
    native_folded = [word.casefold() for word in native]
    if _private_whole_token_contiguous(source_folded, native_folded):
        return "native_contiguous_casefold_only"
    if _private_whole_token_subsequence(source_folded, native_folded):
        return "native_ordered_casefold_subsequence_only"
    return "native_full_ordered_token_relation_unresolved"



def _private_interior_character_relation(
        original_visible: str, source_word_spans: list[tuple[int, int]],
        word_offset: int, candidate_visible: str, candidate_words: list[str]) -> str:
    """Interior visible chars only: retains punctuation *between* word tokens.

    Leading/trailing nonword characters at section boundaries are excluded;
    paragraph/note/reference XML structure is never inferred from text.
    """
    if (not isinstance(original_visible, str) or not candidate_words
            or type(word_offset) is not int or word_offset < 0
            or word_offset + len(candidate_words) > len(source_word_spans)):
        raise ValueError("Unverified source/native interior-character comparison")
    candidate_spans = [match.span() for match in WORD.finditer(candidate_visible)]
    if len(candidate_spans) != len(candidate_words):
        raise ValueError("Native visible word boundaries changed during comparison")
    start = source_word_spans[word_offset][0]
    end = source_word_spans[word_offset + len(candidate_words)-1][1]
    source_middle = original_visible[start:end]
    native_middle = candidate_visible[candidate_spans[0][0]:candidate_spans[-1][1]]
    if WORD.findall(source_middle) != candidate_words:
        raise ValueError("Original source word offsets do not match native exact body")
    if source_middle == native_middle:
        return "all_interior_visible_characters_exact"
    if (re.sub(r"\s+", " ", source_middle)
            == re.sub(r"\s+", " ", native_middle)):
        return "interior_whitespace_only_difference"
    return "interior_nonword_punctuation_or_spacing_difference"



def _private_native_reference_targets(root: etree._Element) -> list[str]:
    """Read exact original SWORD OSIS link targets; never export their values."""
    targets=[]
    for node in root.iter():
        if not isinstance(node.tag, str):
            if isinstance(node,(etree._Comment,etree._ProcessingInstruction)):
                continue
            raise ValueError("Unreviewed native reference markup node")
        if node.tag.rsplit("}",1)[-1]=="reference":
            targets.append(node.get("osisRef") or "")
            if len(targets)>5000:
                raise ValueError("Unreviewed native OSIS reference volume")
    return targets


def _private_reference_sequence_sha256(targets: list[str]) -> str:
    """Unambiguous length-framed link target digest, no raw targets published."""
    h=sha256()
    for value in targets:
        if not isinstance(value,str) or len(value)>8192:
            raise ValueError("Invalid source/native reference target")
        raw=value.encode("utf-8")
        h.update(len(raw).to_bytes(4,"big"))
        h.update(raw)
    return h.hexdigest()



def original_authoring_native_chapter_index_receipt(
        book_divisions: dict[str, etree._Element],
        native_numbered_keys: list[str],
        native_intro_keys: list[str]) -> dict:
    """All-book OSIS chapter milestones vs the *actual* original native index.

    This checks only authenticated book/chapter identities and native K coverage,
    never inferred ranges or the lexical, XML or historical editorial contents.
    It does not print original verse/intro addresses or chapter names.
    """
    from collections import Counter
    chapter_re=re.compile(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\Z")
    numbered_re=re.compile(
        r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]*)\.[1-9][0-9]*\Z")
    intro_re=re.compile(
        r"[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.[1-9][0-9]*(?:\.0)?)?\Z")
    if (not isinstance(book_divisions,dict) or len(book_divisions)!=66
            or not isinstance(native_numbered_keys,list)
            or not 1<=len(native_numbered_keys)<=50000
            or not isinstance(native_intro_keys,list)
            or len(native_intro_keys)>10000):
        raise ValueError("Unverified full original authoring/native index inventory")

    source_chapters=set()
    source_books=set()
    total_start=0
    total_end=0
    for book,node in book_divisions.items():
        if (not isinstance(book,str) or not re.fullmatch(
                r"[1-4]?[A-Za-z][A-Za-z0-9]*",book)
                or not isinstance(node,etree._Element)
                or node.tag.rsplit("}",1)[-1]!="div"
                or node.get("type")!="book" or node.get("osisID")!=book):
            raise ValueError("Original source OSIS book division mismatch")
        source_books.add(book)
        opened=None
        for child in node.iter():
            if not isinstance(child.tag,str):
                continue
            if child.tag.rsplit("}",1)[-1]!="chapter":
                continue
            start=child.get("sID")
            if not start and child.get("osisID") and not child.get("eID"):
                start=child.get("osisID")
            end=child.get("eID")
            if bool(start)==bool(end):
                raise ValueError("Source chapter milestone not a unique start/end")
            key=start or end
            match=chapter_re.fullmatch(key)
            if match is None or match.group(1)!=book:
                raise ValueError("Original book contains invalid chapter milestone")
            if start:
                if opened is not None or key in source_chapters:
                    raise ValueError("Nested or repeated authored OSIS chapter start")
                source_chapters.add(key)
                opened=key
                total_start+=1
            else:
                if opened!=key:
                    raise ValueError("Original chapter end does not match start")
                opened=None
                total_end+=1
        if opened is not None:
            raise ValueError("Original OSIS book missing final chapter close")

    native_chapters=Counter()
    seen_K=set()
    for key in native_numbered_keys:
        if not isinstance(key,str) or not numbered_re.fullmatch(key) or key in seen_K:
            raise ValueError("Duplicate or invalid genuine native K address")
        seen_K.add(key)
        native_chapters[key.rsplit(".",1)[0]]+=1
    native_intro_chapters=set()
    seen_I=set()
    for key in native_intro_keys:
        if not isinstance(key,str) or not intro_re.fullmatch(key) or key in seen_I:
            raise ValueError("Duplicate or invalid genuine native I address")
        seen_I.add(key)
        # Only authentically chapter-shaped I slots can be compared here;
        # book-wide I and edition-specific .0 ownership stay separate.
        if chapter_re.fullmatch(key):
            native_intro_chapters.add(key)
        elif key.endswith(".0") and chapter_re.fullmatch(key[:-2]):
            native_intro_chapters.add(key[:-2])

    missing_K=source_chapters-set(native_chapters)
    unexpected_K=set(native_chapters)-source_chapters
    missing_I=source_chapters-native_intro_chapters
    extra_I=native_intro_chapters-source_chapters

    def _digest_refs(refs: set[str]) -> str:
        digest=sha256()
        for ref in sorted(refs):
            data=ref.encode("ascii")
            digest.update(len(data).to_bytes(4,"big"))
            digest.update(data)
        return digest.hexdigest()

    return {
        "status":"ORIGINAL_AUTHORED_CHAPTER_MILESTONES_VS_NATIVE_OCCUPANCY_ONLY",
        "original_osis_book_divisions":len(source_books),
        "original_osis_unique_chapters":len(source_chapters),
        "original_chapter_start_milestones":total_start,
        "original_chapter_end_milestones":total_end,
        "original_chapter_ref_set_sha256":_digest_refs(source_chapters),
        "actual_native_numbered_K_slots":len(seen_K),
        "native_unique_chapters_with_numbered_K":len(native_chapters),
        "source_chapters_without_native_K":len(missing_K),
        "native_K_chapters_absent_from_authoring_OSIS":len(unexpected_K),
        "source_only_chapter_ref_set_sha256":_digest_refs(missing_K),
        "native_only_chapter_ref_set_sha256":_digest_refs(unexpected_K),
        "actual_native_I_slots":len(seen_I),
        "actual_native_chapter_I_loci":len(native_intro_chapters),
        "source_chapters_without_chapter_I":len(missing_I),
        "native_chapter_I_loci_not_source_chapters":len(extra_I),
        "original_chapter_prose_punctuation_structure_verified":False,
        "native_I_book_level_and_TOP_editorial_ownership_verified":False,
        "source_or_compiled_text_changed":False,
    }


class PrivateOriginalChapterNativeAnchorCoverage:
    """Read-only visible-word *anchor* overlap of original OSIS vs native K.

    The caller pins the source/ZIP hashes and supplies authentically milestone-
    bounded original OSIS chapter words. Only genuine K records from a complete
    independent libSWORD raw stream are accepted. Repeated original K bodies
    count once for lexical coverage, not once per occupied verse key.
    This is explicitly NOT content, authorial section, I/TOP or markup parity.
    """

    ANCHOR = 8
    MAX_SCOPES = 12
    MAX_COMPLETE_CORPUS_SCOPES = 1500
    MAX_CHAPTER_WORDS = 100_000
    MAX_NATIVE_RAW_BYTES = 2 * 1024 * 1024
    INTRO = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.0\.0|\.[1-9][0-9]*(?:\.0)?)?\Z")
    KEY = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*\.[1-9][0-9]*\Z")

    def __init__(self, chapter_words: dict[str, list[str]], *,
                 private_chapter_visible_texts: dict[str, str] | None = None,
                 private_chapter_reference_targets: dict[str, list[str]] | None = None,
                 private_book_pre_chapter_words: dict[str, list[str]] | None = None,
                 full_corpus_mode: bool = False):
        if private_book_pre_chapter_words is not None:
            if (not isinstance(chapter_words,dict)
                    or not isinstance(private_book_pre_chapter_words,dict)
                    or not set(private_book_pre_chapter_words).issubset(chapter_words)):
                raise ValueError("Unreviewed original book prechapter word scopes")
            for chapter,prelude in private_book_pre_chapter_words.items():
                if (not chapter.endswith(".1") or not isinstance(prelude,list)
                        or len(prelude)>100_000
                        or any(not isinstance(word,str) or not word
                               for word in prelude)):
                    raise ValueError("Invalid original pre-first-chapter word witness")

        if (private_chapter_reference_targets is not None
                and (not isinstance(chapter_words,dict)
                     or not isinstance(private_chapter_reference_targets,dict)
                     or set(private_chapter_reference_targets)!=set(chapter_words))):
            raise ValueError("Original chapter reference sample identities disagree")
        if (private_chapter_visible_texts is not None
                and (not isinstance(chapter_words, dict)
                     or not isinstance(private_chapter_visible_texts, dict)
                     or set(private_chapter_visible_texts) != set(chapter_words))):
            raise ValueError("Original chapter visible text scope identities disagree")
        if type(full_corpus_mode) is not bool:
            raise ValueError("Full corpus mode must be explicit")
        if (not isinstance(chapter_words, dict)
                or not (100 <= len(chapter_words) <= self.MAX_COMPLETE_CORPUS_SCOPES
                        if full_corpus_mode
                        else 1 <= len(chapter_words) <= self.MAX_SCOPES)
                or (full_corpus_mode and (
                    private_chapter_visible_texts is None
                    or len({chapter.split(".",1)[0] for chapter in chapter_words})<20))):
            raise ValueError("Unreviewed original chapter coverage case set")
        self._full_corpus_mode=full_corpus_mode
        self._scopes = {}
        for chapter, words in chapter_words.items():
            if (not isinstance(chapter, str)
                    or not re.fullmatch(
                        r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*", chapter)
                    or not isinstance(words, list)
                    or not self.ANCHOR <= len(words) <= self.MAX_CHAPTER_WORDS
                    or any(not isinstance(word, str) or not word for word in words)):
                raise ValueError("Unverified private OSIS chapter words")
            # Full-corpus proof uses stronger whole-body positions and final
            # complete character parity. Avoid millions of redundant eight-
            # word anchor tuples, whose memory adds no independent evidence.
            windows = (None if full_corpus_mode else {
                tuple(words[i:i+self.ANCHOR])
                for i in range(len(words)-self.ANCHOR+1)
            })
            source_visible = (
                None if private_chapter_visible_texts is None
                else private_chapter_visible_texts[chapter])
            if source_visible is not None and (
                    not isinstance(source_visible, str)
                    or len(source_visible) > 5 * 1024 * 1024
                    or WORD.findall(source_visible) != words):
                raise ValueError("Original chapter visible text not token-identical")
            source_spans = (
                [] if source_visible is None or full_corpus_mode else
                [match.span() for match in WORD.finditer(source_visible)])
            if private_chapter_reference_targets is not None:
                targets=private_chapter_reference_targets[chapter]
                if (not isinstance(targets,list) or len(targets)>5000
                        or any(not isinstance(ref,str) or len(ref)>8192
                               for ref in targets)):
                    raise ValueError("Unreviewed original chapter reference targets")
            self._scopes[chapter] = {
                "source_visible_text": source_visible,
                "source_word_spans": source_spans,
                "native_K_interior_character_relation_classes": defaultdict(int),
                "native_I_interior_character_relation_classes": defaultdict(int),
                "source_book_pre_chapter_words":(
                    None if private_book_pre_chapter_words is None
                    else private_book_pre_chapter_words.get(chapter)),
                "intro_book_prelude_exact_location_classes":defaultdict(int),
                "source_reference_targets": (
                    None if private_chapter_reference_targets is None
                    else list(private_chapter_reference_targets[chapter])),
                "native_reference_target_segments": [],
                "native_unlocated_reference_target_count": 0,
                "source_words": words,
                "source_windows": windows,
                "matching_windows": set(),
                "native_raw_digests": set(),
                "native_numbered_slots": 0,
                "native_distinct_visible_word_total": 0,
                "native_exact_whole_chapter_equal": False,
                "distinct_native_relation_classes": defaultdict(int),
                "native_exact_location_classes": defaultdict(int),
                "native_unique_whole_body_intervals": [],
                "source_located_native_visible_segments": [],
                "unlocated_original_native_K_private_words": [],
                "intro_occupied_slots": 0,
                "intro_distinct_raw_digests": set(),
                "intro_exact_source_location_classes": defaultdict(int),
                "intro_unique_exact_intervals": [],
            }

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        """Private callback for fully indexed original SWORD K/I/TOP scan."""
        if kind not in ("K", "I", "U"):
            raise ValueError("Unexpected original SWORD raw frame kind")
        if kind == "I":
            if not isinstance(key, str) or not self.INTRO.fullmatch(key):
                raise ValueError("Invalid original commentary introduction key")
            matching = [scope for scope in self._scopes
                        if key == scope or key == scope + ".0"]
            if not matching:
                return
            if len(matching) != 1:
                raise ValueError("Ambiguous original chapter introduction")
            state = self._scopes[matching[0]]
            if (not isinstance(raw, bytes)
                    or not 0 < len(raw) <= self.MAX_NATIVE_RAW_BYTES
                    or b"\x00" in raw):
                raise ValueError("Invalid original chapter introduction raw frame")
            state["intro_occupied_slots"] += 1
            digest = sha256(raw).hexdigest()
            if digest in state["intro_distinct_raw_digests"]:
                return
            try:
                root = etree.fromstring(
                    b"<fragment>" + raw + b"</fragment>",
                    parser=etree.XMLParser(
                        resolve_entities=False, no_network=True,
                        load_dtd=False, recover=False, huge_tree=False,
                        remove_blank_text=False, strip_cdata=False))
            except (ValueError, etree.XMLSyntaxError):
                raise ValueError("Unparseable original chapter introduction XML") from None
            if any(isinstance(node, etree._Entity) for node in root.iter()):
                raise ValueError("Unresolved original chapter introduction XML entity")
            native_visible = "".join(root.itertext())
            words = WORD.findall(native_visible)
            state["intro_distinct_raw_digests"].add(digest)
            offsets = _private_exact_token_match_offsets(
                state["source_words"], words)
            if not offsets and state["source_book_pre_chapter_words"] is not None:
                before_chapter=_private_exact_token_match_offsets(
                    state["source_book_pre_chapter_words"], words)
                if len(before_chapter)==1:
                    state["intro_book_prelude_exact_location_classes"][
                        "one_unique_complete_exact_prelude_word_location"]+=1
                elif before_chapter:
                    state["intro_book_prelude_exact_location_classes"][
                        "multiple_exact_prelude_word_locations_ambiguous"]+=1
                else:
                    state["intro_book_prelude_exact_location_classes"][
                        "not_exactly_in_original_book_pre_first_chapter_words"]+=1
            native_references=_private_native_reference_targets(root)
            if len(offsets)==1:
                state["native_reference_target_segments"].append(
                    (offsets[0],native_references))
            else:
                state["native_unlocated_reference_target_count"]+=len(
                    native_references)
            if len(offsets) == 1:
                state["intro_exact_source_location_classes"][
                    "one_unique_exact_source_interval"] += 1
                state["intro_unique_exact_intervals"].append(
                    (offsets[0], offsets[0] + len(words)))
                state["source_located_native_visible_segments"].append(
                    (offsets[0], offsets[0] + len(words), "I", native_visible))
            elif offsets:
                state["intro_exact_source_location_classes"][
                    "multiple_exact_source_intervals_ambiguous"] += 1
            else:
                state["intro_exact_source_location_classes"][
                    "no_full_exact_source_interval"] += 1
            if (len(offsets) == 1 and state["source_visible_text"] is not None
                    and not self._full_corpus_mode):
                character_relation = _private_interior_character_relation(
                    state["source_visible_text"], state["source_word_spans"],
                    offsets[0], native_visible, words)
            elif len(offsets) == 1 and self._full_corpus_mode:
                character_relation = "not_needed_full_corpus_complete_visible_character_check"
            elif len(offsets) == 1:
                character_relation = "not_assessed_no_original_source_character_stream"
            else:
                character_relation = "not_assessed_without_unique_exact_word_location"
            state["native_I_interior_character_relation_classes"][character_relation] += 1
            return
        if kind != "K":
            return
        if not isinstance(key, str) or not self.KEY.fullmatch(key):
            raise ValueError("Invalid original SWORD K reference")
        chapter = key.rsplit(".", 1)[0]
        state = self._scopes.get(chapter)
        if state is None:
            return
        if (not isinstance(raw, bytes)
                or not 0 < len(raw) <= self.MAX_NATIVE_RAW_BYTES
                or b"\x00" in raw):
            raise ValueError("Invalid original SWORD raw XML frame")
        state["native_numbered_slots"] += 1
        digest = sha256(raw).hexdigest()
        if digest in state["native_raw_digests"]:
            return
        state["native_raw_digests"].add(digest)
        try:
            root = etree.fromstring(
                b"<fragment>" + raw + b"</fragment>",
                parser=etree.XMLParser(
                    resolve_entities=False, no_network=True, load_dtd=False,
                    recover=False, huge_tree=False, remove_blank_text=False,
                    strip_cdata=False))
        except (ValueError, etree.XMLSyntaxError):
            raise ValueError("Unparseable authenticated original native raw XML") from None
        if any(isinstance(node, etree._Entity) for node in root.iter()):
            raise ValueError("Unresolved original native raw XML entity")
        native_visible = "".join(root.itertext())
        words = WORD.findall(native_visible)
        state["native_distinct_visible_word_total"] += len(words)
        if words == state["source_words"]:
            state["native_exact_whole_chapter_equal"] = True
        relation = _private_native_word_relation(state["source_words"], words)
        state["distinct_native_relation_classes"][relation] += 1
        offsets = _private_exact_token_match_offsets(
            state["source_words"], words)
        native_references=_private_native_reference_targets(root)
        if len(offsets)==1:
            state["native_reference_target_segments"].append(
                (offsets[0],native_references))
        else:
            state["native_unlocated_reference_target_count"]+=len(
                native_references)
        if len(offsets) == 1:
            state["native_exact_location_classes"]["one_unique_exact_source_interval"] += 1
            state["native_unique_whole_body_intervals"].append(
                (offsets[0], offsets[0] + len(words)))
            state["source_located_native_visible_segments"].append(
                (offsets[0], offsets[0] + len(words), "K", native_visible))
        elif offsets:
            state["native_exact_location_classes"][
                "multiple_exact_source_intervals_ambiguous"] += 1
        else:
            state["native_exact_location_classes"][
                "no_full_exact_source_interval"] += 1
        if len(offsets)!=1:
            pending=state["unlocated_original_native_K_private_words"]
            if (len(pending)>=32 or
                    sum(len(v) for v in pending)+len(words)>200_000):
                raise ValueError("Unreviewed original unmatched native K volume")
            pending.append(words)
        if (len(offsets) == 1 and state["source_visible_text"] is not None
                and not self._full_corpus_mode):
            character_relation = _private_interior_character_relation(
                state["source_visible_text"], state["source_word_spans"],
                offsets[0], native_visible, words)
        elif len(offsets) == 1 and self._full_corpus_mode:
            character_relation = "not_needed_full_corpus_complete_visible_character_check"
        elif len(offsets) == 1:
            character_relation = "not_assessed_no_original_source_character_stream"
        else:
            character_relation = "not_assessed_without_unique_exact_word_location"
        state["native_K_interior_character_relation_classes"][character_relation] += 1
        source_windows = state["source_windows"]
        if source_windows is not None:
            state["matching_windows"].update(
                tuple(words[i:i+self.ANCHOR])
                for i in range(len(words)-self.ANCHOR+1)
                if tuple(words[i:i+self.ANCHOR]) in source_windows
            )

    def private_unmatched_native_K_original_book_location(
            self, book_divisions: dict[str, etree._Element]) -> dict:
        """Where do unmatched original native K words occur within their book?

        This is NOT proof of source chapter/body ownership or safe remapping.
        No actual native key, original text, or source-book address is exported.
        The independently authentic original authored book is read privately.
        """
        from collections import Counter
        if (not isinstance(book_divisions,dict)
                or len(book_divisions)>66):
            raise ValueError("Unreviewed original source books for unmatched native K")
        cases=[]
        cached_books={}
        for chapter,state in self._scopes.items():
            pending=state["unlocated_original_native_K_private_words"]
            if not pending:
                continue
            book=chapter.rsplit(".",1)[0]
            book_div=book_divisions.get(book)
            if (not isinstance(book_div,etree._Element)
                    or book_div.tag.rsplit("}",1)[-1]!="div"
                    or book_div.get("type")!="book"
                    or book_div.get("osisID")!=book):
                raise ValueError("Unmatched native K has no genuine source book")
            if book not in cached_books:
                # Original entire book text is private and never logged.
                book_words=WORD.findall("".join(book_div.itertext()))
                if not 1<=len(book_words)<=1_000_000:
                    raise ValueError("Unreviewed original book visible text length")
                cached_books[book]=book_words
            book_words=cached_books[book]
            source_positions=_private_exact_token_match_offsets(
                book_words,state["source_words"],maximum_positions=20)
            if len(source_positions)==1:
                original_start=source_positions[0]
                original_end=original_start+len(state["source_words"])
            else:
                original_start=original_end=None
            classifications=Counter()
            candidates=[]
            for native_words in pending:
                offsets=_private_exact_token_match_offsets(
                    book_words,native_words,maximum_positions=20)
                if len(offsets)==1:
                    native_start=offsets[0]
                    native_end=native_start+len(native_words)
                    if original_start is None:
                        relation="native_unique_in_book_chapter_scope_ambiguous"
                    elif native_start>=original_start and native_end<=original_end:
                        relation="native_within_authoring_chapter_but_not_exact_source_chapter"
                    elif native_start<original_end and native_end>original_end:
                        relation="native_whole_body_crosses_authored_chapter_end"
                    elif native_start<original_start and native_end>original_start:
                        relation="native_whole_body_crosses_authored_chapter_start"
                    elif native_end<=original_start:
                        relation="native_entirely_before_authored_chapter"
                    elif native_start>=original_end:
                        relation="native_entirely_after_authored_chapter"
                    else:
                        relation="native_unreviewed_partial_chapter_relation"
                elif offsets:
                    relation="native_multiple_exact_whole_book_positions_ambiguous"
                else:
                    relation="native_not_exact_whole_word_body_in_original_book"
                classifications[relation]+=1
                candidates.append({
                    "unlocated_native_K_visible_word_count":len(native_words),
                    "complete_native_K_original_book_location_class":relation,
                    "native_K_entire_body_unique_in_book":len(offsets)==1,
                    "native_K_complete_token_sha256":sha256(
                        " ".join(native_words).encode("utf-8")).hexdigest(),
                })
            cases.append({
                "authored_chapter_ref_sha256":sha256(chapter.encode("utf-8")).hexdigest(),
                "original_authored_book_visible_words":len(book_words),
                "original_chapter_full_word_body_locations_in_book":len(source_positions),
                "unlocated_original_native_K_body_count":len(pending),
                "native_original_book_whole_body_location_classes":
                    dict(sorted(classifications.items())),
                "candidate_original_native_K_bodies":candidates,
                "same_book_whole_word_match_not_authored_chapter_ownership":True,
                "no_original_text_or_native_verse_key_emitted":True,
            })
        return {
            "status":"ORIGINAL_UNMATCHED_NATIVE_K_WHOLE_BOOK_EXACT_WORD_LOCATIONS_ONLY",
            "original_chapter_cases_checked":len(cases),
            "cases":cases,
            "original_source_or_binary_transformed":False,
            "no_book_ending_or_authorial_edition_remap_approved":True,
        }

    def private_uncovered_source_gaps_in_other_original_chapters(self) -> dict:
        """Diagnose any genuine OSIS word gaps between exact original native K/I.

        A gap can be interior OR terminal. Check other original chapters in
        the same book and their source-located K/I text. This does NOT search
        every original native raw frame or infer missing authored exposition.
        """
        candidates=[]
        distinct_chapters=set()
        for chapter,state in self._scopes.items():
            if (len(state["native_unique_whole_body_intervals"])
                    != len(state["native_raw_digests"])
                    or len(state["intro_unique_exact_intervals"])
                    != len(state["intro_distinct_raw_digests"])
                    or not state["intro_distinct_raw_digests"]):
                continue
            intervals=sorted(
                (start,end) for start,end,kind,visible in
                state["source_located_native_visible_segments"])
            if not intervals:
                continue
            words=state["source_words"]
            gaps=[]
            cursor=0
            for start,stop in intervals:
                if start<0 or stop<=start or stop>len(words):
                    raise ValueError("Invalid original source-located K/I word interval")
                if start>cursor:
                    gaps.append((cursor,start))
                cursor=max(cursor,stop)
            if cursor<len(words):
                gaps.append((cursor,len(words)))
            for gap_start,gap_end in gaps:
                unaccounted=words[gap_start:gap_end]
                if len(unaccounted)<self.ANCHOR:
                    # Short source gaps need their own carefully reviewed
                    # matching policy; do not mistake common few-word
                    # phrases in other chapters for uniquely located prose.
                    continue
                if len(candidates)>=40:
                    raise ValueError("Unreviewed many original source gap probes")
                distinct_chapters.add(chapter)
                book,num=chapter.rsplit(".",1)
                next_key=f"{book}.{int(num)+1}"
                next_state=self._scopes.get(next_key)
                same_book_source_hits=0
                same_book_native_hits=0
                first_source_offsets=0
                first_native_offsets=0
                anchor_hits=None
                anchors=[
                    unaccounted[:self.ANCHOR],
                    unaccounted[(len(unaccounted)-self.ANCHOR)//2:
                                (len(unaccounted)-self.ANCHOR)//2+self.ANCHOR],
                    unaccounted[-self.ANCHOR:],
                ]
                for neighbor,other in self._scopes.items():
                    if neighbor==chapter or not neighbor.startswith(book+"."):
                        continue
                    source_hits=_private_exact_token_match_offsets(
                        other["source_words"],unaccounted,maximum_positions=20)
                    if source_hits:
                        same_book_source_hits+=1
                        if neighbor==next_key:
                            first_source_offsets=len(source_hits)
                    segment_words=[]
                    for first,last,kind,visible in sorted(
                            other["source_located_native_visible_segments"],
                            key=lambda item:(item[0],item[1])):
                        segment_words.extend(WORD.findall(visible))
                    native_hits=_private_exact_token_match_offsets(
                        segment_words,unaccounted,maximum_positions=20)
                    if native_hits:
                        same_book_native_hits+=1
                        if neighbor==next_key:
                            first_native_offsets=len(native_hits)
                    if neighbor==next_key:
                        anchor_hits=[
                            sum(bool(_private_exact_token_match_offsets(
                                segment_words,anchor,maximum_positions=20))
                                for anchor in anchors),
                            sum(bool(_private_exact_token_match_offsets(
                                other["source_words"],anchor,maximum_positions=20))
                                for anchor in anchors),
                        ]
                candidates.append({
                    "authored_chapter_ref_sha256":sha256(
                        chapter.encode("ascii")).hexdigest(),
                    "source_gap_location_class":(
                        "source_initial_prefix" if gap_start==0
                        else "source_terminal_suffix" if gap_end==len(words)
                        else "source_internal_interval"),
                    "source_gap_word_offset_not_verse_key":gap_start,
                    "source_gap_visible_word_tokens":len(unaccounted),
                    "source_gap_exact_ordered_word_sha256":sha256(
                        " ".join(unaccounted).encode("utf-8")).hexdigest(),
                    "next_original_chapter_source_has_entire_gap":
                        bool(first_source_offsets),
                    "next_original_chapter_located_native_has_entire_gap":
                        bool(first_native_offsets),
                    "other_same_book_source_chapters_with_entire_gap":
                        same_book_source_hits,
                    "other_same_book_located_native_chapters_with_entire_gap":
                        same_book_native_hits,
                    "next_chapter_located_native_eight_word_anchor_hits_of_three":
                        anchor_hits[0] if next_state is not None else None,
                    "next_chapter_source_eight_word_anchor_hits_of_three":
                        anchor_hits[1] if next_state is not None else None,
                    "not_a_whole_original_module_or_note_ownership_search":True,
                    "no_authorial_prose_or_real_verse_addresses_exported":True,
                })
        return {
            "status":"ORIGINAL_UNCOVERED_SOURCE_WORD_INTERVALS_SAME_BOOK_KI_ONLY",
            "genuine_authored_chapter_uncovered_gap_scopes":len(distinct_chapters),
            "genuine_authored_chapter_uncovered_word_intervals":len(candidates),
            "cases":candidates,
            "sub_eight_word_intervals_not_searchable_by_this_probe":True,
            "full_original_native_K_I_TOP_corpus_global_search_not_performed":True,
            "source_or_stock_module_changed":False,
        }

    def private_authentic_uncovered_source_word_fragments(self) -> list[tuple[str,int,list[str]]]:
        """Only genuine source word gaps after uniquely placed original K/I.

        The return value contains original authoring words and MUST remain
        inside the private CI process; never serialize or log it.
        """
        results=[]
        for chapter,state in self._scopes.items():
            if (len(state["native_unique_whole_body_intervals"])
                    != len(state["native_raw_digests"])
                    or len(state["intro_unique_exact_intervals"])
                    != len(state["intro_distinct_raw_digests"])
                    or not state["intro_distinct_raw_digests"]):
                continue
            boundaries=sorted(
                (start,end) for start,end,kind,visible in
                state["source_located_native_visible_segments"])
            if not boundaries:
                continue
            cursor=0
            original=state["source_words"]
            gaps=[]
            for start,end in boundaries:
                if start<0 or end<=start or end>len(original):
                    raise ValueError("Unreviewed source/native interval")
                if start>cursor:
                    gaps.append((cursor,start))
                cursor=max(cursor,end)
            if cursor<len(original):
                gaps.append((cursor,len(original)))
            for start,end in gaps:
                fragment=original[start:end]
                if len(fragment)<12:
                    continue
                if len(results)>=40 or len(fragment)>100_000:
                    raise ValueError("Unreviewed large original source gap collection")
                results.append((chapter,start,list(fragment)))
        return results

    def report(self) -> dict:
        """Closed metadata only; never includes words, XML or actual native keys."""
        rows = []
        for chapter, state in self._scopes.items():
            if not state["native_numbered_slots"] or not state["native_raw_digests"]:
                raise ValueError("Selected original chapter missing native occupied K")
            if (state["source_windows"] is not None
                    and len(state["matching_windows"]) > len(state["source_windows"])):
                raise ValueError("Original source/native lexical anchor accounting mismatch")
            if sum(state["distinct_native_relation_classes"].values()) != len(state["native_raw_digests"]):
                raise ValueError("Unique original native word relation classification incomplete")
            if sum(state["native_exact_location_classes"].values()) != len(state["native_raw_digests"]):
                raise ValueError("Unique original native source location classification incomplete")
            all_exact_unique = (
                len(state["native_unique_whole_body_intervals"])
                == len(state["native_raw_digests"]))
            uncovered_spans = None
            uncovered_word_count = None
            exact_native_interval_overlap_words = None
            if all_exact_unique:
                intervals = sorted(state["native_unique_whole_body_intervals"])
                if len(intervals) > 512:
                    raise ValueError("Original chapter contains too many distinct K body locations")
                merged = []
                for start, end in intervals:
                    if merged and start <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
                    else:
                        merged.append((start, end))
                native_interval_words = sum(end-start for start, end in intervals)
                covered = sum(end-start for start, end in merged)
                exact_native_interval_overlap_words = native_interval_words-covered
                original = state["source_words"]
                uncovered_spans = []
                cursor = 0
                for start, end in merged:
                    if start > cursor:
                        fragment = original[cursor:start]
                        uncovered_spans.append({
                            "original_chapter_word_offset_not_verse_key": cursor,
                            "source_uncovered_visible_word_tokens": len(fragment),
                            "original_ordered_source_word_sha256": sha256(
                                " ".join(fragment).encode("utf-8")).hexdigest(),
                        })
                    cursor = end
                if cursor < len(original):
                    fragment = original[cursor:]
                    uncovered_spans.append({
                        "original_chapter_word_offset_not_verse_key": cursor,
                        "source_uncovered_visible_word_tokens": len(fragment),
                        "original_ordered_source_word_sha256": sha256(
                            " ".join(fragment).encode("utf-8")).hexdigest(),
                    })
                uncovered_word_count = len(original)-covered
                if sum(x["source_uncovered_visible_word_tokens"]
                       for x in uncovered_spans) != uncovered_word_count:
                    raise ValueError("Authentic source/native interval accounting failed")
            intro_digests = state["intro_distinct_raw_digests"]
            intro_intervals = state["intro_unique_exact_intervals"]
            if sum(state["intro_exact_source_location_classes"].values()) != len(intro_digests):
                raise ValueError("Original chapter introduction classification incomplete")
            if (sum(state["native_K_interior_character_relation_classes"].values())
                    != len(state["native_raw_digests"])
                    or sum(state["native_I_interior_character_relation_classes"].values())
                    != len(intro_digests)):
                raise ValueError("Original native K/I interior-character classification incomplete")
            all_intro_unique = bool(intro_digests) and (
                len(intro_intervals) == len(intro_digests))
            combined_uncovered = None
            intro_covers_K_prefix = None
            if all_exact_unique and all_intro_unique:
                merged = []
                for start, end in sorted(
                        state["native_unique_whole_body_intervals"] + intro_intervals):
                    if merged and start <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
                    else:
                        merged.append((start, end))
                combined_uncovered = len(state["source_words"]) - sum(
                    end-start for start, end in merged)
                prefix = next((span for span in uncovered_spans or []
                               if span["original_chapter_word_offset_not_verse_key"] == 0),
                              None)
                intro_covers_K_prefix = (
                    prefix is not None and any(
                        start == 0 and end >=
                        prefix["source_uncovered_visible_word_tokens"]
                        for start, end in intro_intervals))
            # When authentic source-located original native K/I bodies form
            # a *strict exact partition* of all genuine original chapter word
            # positions, compare entire visible chapter character streams,
            # including punctuation before/after individual bodies. Only
            # whitespace is removed. Do not treat a duplicated/ambiguous
            # introduction as proof of editorial chapter ownership.
            whole_nonwhitespace_relation=None
            source_flat_sha=None
            native_flat_sha=None
            source_flat_len=None
            native_flat_len=None
            first_flat_mismatch=None
            segments=sorted(
                state["source_located_native_visible_segments"],
                key=lambda segment:(segment[0],segment[1]))
            if all_exact_unique and state["source_visible_text"] is not None:
                cursor=0
                partition=True
                for start,end,kind,content in segments:
                    if (start!=cursor or end<=start
                            or kind not in ("K","I")
                            or not isinstance(content,str)):
                        partition=False
                        break
                    cursor=end
                if partition and cursor==len(state["source_words"]):
                    source_flat=re.sub(r"\s+","",state["source_visible_text"])
                    native_flat=re.sub(
                        r"\s+","", "".join(segment[3] for segment in segments))
                    source_flat_len=len(source_flat)
                    native_flat_len=len(native_flat)
                    source_flat_sha=sha256(source_flat.encode("utf-8")).hexdigest()
                    native_flat_sha=sha256(native_flat.encode("utf-8")).hexdigest()
                    whole_nonwhitespace_relation=(source_flat==native_flat)
                    if not whole_nonwhitespace_relation:
                        first_flat_mismatch=next(
                            (idx for idx,(left,right) in enumerate(zip(
                                source_flat,native_flat)) if left!=right),
                            min(source_flat_len,native_flat_len))
                    del source_flat,native_flat
            source_book_pre_chapter=state["source_book_pre_chapter_words"]
            source_reference_targets=state["source_reference_targets"]
            reference_scope_complete=(
                all_exact_unique and
                (uncovered_word_count==0 or (
                    all_intro_unique and combined_uncovered==0)))
            reference_targets_exact=None
            native_located_reference_count=None
            native_reference_targets_sha=None
            source_reference_targets_sha=None
            if source_reference_targets is not None:
                source_reference_targets_sha=_private_reference_sequence_sha256(
                    source_reference_targets)
                if reference_scope_complete:
                    ordered=[]
                    for offset,refs in sorted(
                            state["native_reference_target_segments"],
                            key=lambda row: row[0]):
                        ordered.extend(refs)
                    native_located_reference_count=len(ordered)
                    native_reference_targets_sha=_private_reference_sequence_sha256(ordered)
                    reference_targets_exact=(
                        len(ordered)==len(source_reference_targets)
                        and native_reference_targets_sha==source_reference_targets_sha
                        and ordered==source_reference_targets)
            rows.append({
                "original_chapter_reference_sha256": sha256(
                    chapter.encode("utf-8")).hexdigest(),
                "original_chapter_visible_words": len(state["source_words"]),
                "complete_source_chapter_nonwhitespace_visible_characters_equal":
                    whole_nonwhitespace_relation,
                "complete_source_chapter_nonwhitespace_characters":source_flat_len,
                "complete_native_chapter_nonwhitespace_characters":native_flat_len,
                "complete_source_chapter_visible_nonwhitespace_sha256":source_flat_sha,
                "complete_native_chapter_visible_nonwhitespace_sha256":native_flat_sha,
                "first_nonwhitespace_character_mismatch_offset_not_verse":
                    first_flat_mismatch,
                "complete_character_audit_requires_strict_exact_native_word_partition":True,
                "complete_character_audit_ignores_whitespace_not_xml_structure":True,
                "original_book_before_first_chapter_visible_words":(
                    None if source_book_pre_chapter is None
                    else len(source_book_pre_chapter)),
                "native_chapter_I_book_prelude_exact_location_classes":
                    dict(sorted(state["intro_book_prelude_exact_location_classes"].items())),
                "book_pre_first_chapter_location_not_editorial_owner_proof":True,
                "source_chapter_reference_elements": (
                    None if source_reference_targets is None
                    else len(source_reference_targets)),
                "source_reference_target_sequence_sha256":source_reference_targets_sha,
                "native_located_reference_elements":native_located_reference_count,
                "native_located_reference_target_sequence_sha256":
                    native_reference_targets_sha,
                "exact_original_reference_target_sequence_equal_in_source_and_native":
                    reference_targets_exact,
                "native_unlocated_original_reference_elements":
                    state["native_unlocated_reference_target_count"],
                "reference_attribute_sequence_not_proof_of_link_navigation":True,
                "original_unique_eight_word_windows": (
                    None if state["source_windows"] is None
                    else len(state["source_windows"])),
                "exact_unique_source_eight_word_windows_in_original_native_K": (
                    None if state["source_windows"] is None
                    else len(state["matching_windows"])),
                "actual_occupied_original_numbered_K_slots":
                    state["native_numbered_slots"],
                "distinct_original_native_raw_payloads":
                    len(state["native_raw_digests"]),
                "summed_visible_words_in_distinct_original_native_raw_payloads":
                    state["native_distinct_visible_word_total"],
                "one_original_native_raw_payload_matches_entire_original_chapter":
                    state["native_exact_whole_chapter_equal"],
                "native_distinct_whole_body_ordered_word_relation_classes":
                    dict(sorted(state["distinct_native_relation_classes"].items())),
                "native_distinct_whole_body_exact_source_location_classes":
                    dict(sorted(state["native_exact_location_classes"].items())),
                "all_distinct_native_K_bodies_have_unique_exact_source_intervals":
                    all_exact_unique,
                "source_uncovered_word_tokens_after_unique_native_K_body_intervals":
                    uncovered_word_count,
                "source_uncovered_word_spans_metadata_only":
                    uncovered_spans,
                "overlap_word_tokens_among_exact_native_K_body_intervals":
                    exact_native_interval_overlap_words,
                "actual_chapter_specific_original_I_slots":
                    state["intro_occupied_slots"],
                "distinct_chapter_specific_original_I_raw_payloads":
                    len(intro_digests),
                "chapter_I_whole_body_exact_source_location_classes":
                    dict(sorted(state["intro_exact_source_location_classes"].items())),
                "native_K_body_interior_visible_character_relation_classes":
                    dict(sorted(state["native_K_interior_character_relation_classes"].items())),
                "native_chapter_I_body_interior_visible_character_relation_classes":
                    dict(sorted(state["native_I_interior_character_relation_classes"].items())),
                "all_chapter_I_bodies_uniquely_located_in_source":
                    all_intro_unique,
                "source_uncovered_words_after_unique_K_plus_chapter_I_intervals":
                    combined_uncovered,
                "original_source_K_prefix_fully_covered_by_chapter_I":
                    intro_covers_K_prefix,
                "book_level_I_and_opaque_TOP_not_source_compared": True,
                "uncovered_osis_tokens_not_proven_missing_authored_exposition": True,
                "whole_body_word_relation_not_equivalent_to_authorial_unit": True,
                "anchor_overlap_is_not_exact_text_or_structural_parity": True,
                "unmatched_anchors_not_proven_historical_authorial_omissions": True,
            })
        return {
            "status": "ORIGINAL_AUTHORING_OSIS_TO_COMPILED_NATIVE_K_LEXICAL_ANCHORS_ONLY",
            "minimum_exact_case_sensitive_anchor_words": self.ANCHOR,
            "original_chapter_cases": rows,
            "full_intro_and_top_payload_parity_not_proven": True,
            "book_pre_first_chapter_word_location_not_intro_owner_proof":True,
            "chapter_I_key_filter_not_editorial_owner_proof": True,
            "original_verse_key_range_and_paragraph_owner_not_inferred": True,
            "casefold_only_categories_do_not_authorize_case_changes": True,
            "exact_containment_does_not_prove_punctuation_or_markup": True,
            "visible_character_test_excludes_section_boundary_nonword_chars": True,
            "interior_character_test_excludes_section_boundary_nonword_chars": True,
            "complete_chapter_nonwhitespace_character_probe_includes_boundaries_if_partition":True,
            "reference_attributes_checked_only_for_uniquely_located_exact_native_bodies": True,
            "matching_reference_target_attributes_not_proof_of_working_links": True,
            "markup_and_structure_parity_not_proven_by_reference_attributes": True,
            "source_uncovered_intervals_are_not_scripture_verse_mappings": True,
            "source_uncovered_spans_not_automatically_missing_in_sword": True,
            "original_punctuation_markup_notes_and_links_not_compared": True,
            "original_source_or_compiled_binary_changed": False,
            "no_original_words_raw_xml_or_verse_keys_exported": True,
            "no_source_edition_or_redistribution_rights_approved": True,
        }


class PrivateOriginalNativeWholeCorpusGapSearch:
    """Scan genuine original K/I *raw bodies*, once per distinct kind+SHA.

    The original source gap words never leave this in-memory object. The
    second full libSWORD scan must be separately SHA-reconciled by the caller.
    Unknown opaque TOP/U payloads are counted but NOT text-searched.
    """

    ANCHOR=12

    def __init__(self, original_source_fragments: list[tuple[str,int,list[str]]]):
        if (not isinstance(original_source_fragments,list)
                or not 1<=len(original_source_fragments)<=40):
            raise ValueError("Unreviewed original source gap search set")
        self._sources=[]
        self._index=defaultdict(list)
        self._seen=set()
        self._kinds={"K":0,"I":0,"U":0}
        self._parse_failures={"K":0,"I":0}
        total=0
        unique=set()
        for chapter,start,words in original_source_fragments:
            if (not isinstance(chapter,str) or not re.fullmatch(
                    r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*",chapter)
                    or type(start) is not int or start<0
                    or not isinstance(words,list)
                    or not self.ANCHOR<=len(words)<=100_000
                    or any(not isinstance(word,str) or not word for word in words)
                    or (chapter,start) in unique):
                raise ValueError("Unverified original source word interval for native search")
            unique.add((chapter,start))
            total+=len(words)
            if total>200_000:
                raise ValueError("Unbounded original source word gaps in memory")
            raw=" ".join(words).encode("utf-8")
            source={
                "reference_sha256":sha256(chapter.encode("ascii")).hexdigest(),
                "source_word_offset":start,
                "word_count":len(words),
                "source_words_sha256":sha256(raw).hexdigest(),
                "words":words,
                "found_anchor_kinds":defaultdict(set),
                "raw_bodies_with_any_anchor":{"K":0,"I":0},
                "exact_complete_fragment_raw_bodies":{"K":0,"I":0},
            }
            index=len(self._sources)
            self._sources.append(source)
            for name,position in (
                    ("first",0),
                    ("middle",(len(words)-self.ANCHOR)//2),
                    ("last",len(words)-self.ANCHOR)):
                self._index[tuple(words[position:position+self.ANCHOR])].append(
                    (index,name))

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        if kind not in ("K","I","U") or not isinstance(raw,bytes):
            raise ValueError("Invalid genuine native frame kind/bytes")
        if kind=="U":
            self._kinds["U"]+=1
            return
        if (not isinstance(key,str)
                or not (PrivateOriginalChapterNativeAnchorCoverage.KEY.fullmatch(key)
                        if kind=="K" else
                        PrivateOriginalChapterNativeAnchorCoverage.INTRO.fullmatch(key))
                or not 0<len(raw)<=2*1024*1024 or b"\x00" in raw):
            raise ValueError("Unreviewed original native K/I whole-corpus frame")
        digest=sha256(raw).hexdigest()
        if (kind,digest) in self._seen:
            return
        self._seen.add((kind,digest))
        self._kinds[kind]+=1
        try:
            root=etree.fromstring(
                b"<fragment>"+raw+b"</fragment>",
                parser=etree.XMLParser(resolve_entities=False,
                    no_network=True,load_dtd=False,recover=False,
                    huge_tree=False,remove_blank_text=False,strip_cdata=False))
            if any(isinstance(item,etree._Entity) for item in root.iter()):
                raise ValueError("Unresolved original native XML entity")
        except (ValueError,etree.XMLSyntaxError):
            self._parse_failures[kind]+=1
            return
        native=WORD.findall("".join(root.itertext()))
        matching=defaultdict(set)
        for index in range(max(0,len(native)-self.ANCHOR+1)):
            key=tuple(native[index:index+self.ANCHOR])
            for case,which in self._index.get(key,()):
                matching[case].add(which)
        for index,parts in matching.items():
            source=self._sources[index]
            source["raw_bodies_with_any_anchor"][kind]+=1
            source["found_anchor_kinds"][kind].update(parts)
            if "first" in parts and _private_exact_token_match_offsets(
                    native,source["words"],maximum_positions=20):
                source["exact_complete_fragment_raw_bodies"][kind]+=1

    def report(self) -> dict:
        return {
            "status":"EXACT_ORIGINAL_GAP_PROSE_AGAINST_ALL_GENUINE_NATIVE_K_I_RAW_BODIES",
            "original_source_word_intervals":len(self._sources),
            "distinct_genuine_original_native_K_I_raw_frames_scanned":
                dict(self._kinds),
            "original_genuine_native_K_I_unparseable_raw_frames":
                dict(self._parse_failures),
            "original_opaque_TOP_U_slots_not_text_searched":
                self._kinds["U"],
            "cases":[{
                "authored_chapter_ref_sha256":case["reference_sha256"],
                "source_word_offset_not_verse_key":case["source_word_offset"],
                "original_unaccounted_visible_word_tokens":case["word_count"],
                "source_word_interval_sha256":case["source_words_sha256"],
                "distinct_original_native_raw_bodies_with_any_12word_anchor":
                    dict(case["raw_bodies_with_any_anchor"]),
                "native_K_found_first_middle_last_12word_anchors":
                    sorted(case["found_anchor_kinds"].get("K",set())),
                "native_I_found_first_middle_last_12word_anchors":
                    sorted(case["found_anchor_kinds"].get("I",set())),
                "original_native_raw_bodies_containing_entire_original_gap":
                    dict(case["exact_complete_fragment_raw_bodies"]),
                "not_a_cross_native_frame_or_historic_print_parity_proof":True,
            } for case in self._sources],
            "no_original_text_native_keys_or_raw_xml_exported":True,
            "no_source_module_or_edition_revised":True,
        }


def private_original_osis_gap_against_pinned_ccel_volume(
        original_xml: bytes, *,
        expected_xml_sha256: str, original_volume_number: int,
        source_fragments: list[tuple[str,int,list[str]]]) -> dict:
    """Exact original OSIS gap words vs a separately pinned CCEL digital volume.

    This is a LEXICAL witness only; a full-volume match does not prove its
    editorial attribution to a verse, original printed edition or permission
    to correct and redistribute any derived electronic source.
    """
    if (type(original_volume_number) is not int
            or not 1<=original_volume_number<=6
            or not isinstance(source_fragments,list)
            or not 1<=len(source_fragments)<=40):
        raise ValueError("Unreviewed authentic CCEL source volume gap study")
    root=_safe_root(original_xml,expected_xml_sha256,MAX_CCEL_BYTES)
    words=WORD.findall("".join(root.itertext()))
    if not 1<=len(words)<=4_000_000:
        raise ValueError("Unreviewed original digital volume visible word count")
    anchors=defaultdict(list)
    identities=[]
    for chapter,start,original in source_fragments:
        if (not isinstance(chapter,str) or not re.fullmatch(
                r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*",chapter)
                or type(start) is not int or start<0
                or not isinstance(original,list)
                or not 12<=len(original)<=100_000
                or any(not isinstance(token,str) or not token for token in original)):
            raise ValueError("Unreviewed source word interval for CCEL comparison")
        idx=len(identities)
        identities.append((chapter,start,original))
        for label,offset in (
                ("first",0),("middle",(len(original)-12)//2),
                ("last",len(original)-12)):
            anchors[tuple(original[offset:offset+12])].append((idx,label))
    hits=defaultdict(set)
    anchor_offsets=defaultdict(lambda:defaultdict(list))
    for pos in range(max(0,len(words)-11)):
        for idx,label in anchors.get(tuple(words[pos:pos+12]),()):
            hits[idx].add(label)
            # Bounded, exact whole-word first/mid/last anchor positions.
            # Repeated generic wording must NOT be used to infer a unique
            # textual owner or silently collate unrelated paragraphs.
            found=anchor_offsets[idx][label]
            if len(found)<=20:
                found.append(pos)
    cases=[]
    for idx,(chapter,start,original) in enumerate(identities):
        whole=(
            _private_exact_token_match_offsets(
                words,original,maximum_positions=20)
            if "first" in hits[idx] else [])
        # A source-only gap can differ by one electronic-edition word yet
        # share all three original 12-word witnesses. Only uniquely ordered,
        # size-bounded first/middle/last witnesses permit exact PRIVATE
        # source-vs-CCEL lexical comparison of the enclosed digital span.
        collated=None
        pos=anchor_offsets[idx]
        if (all(len(pos.get(label,()))==1
                for label in ("first","middle","last"))
                and pos["first"][0]<pos["middle"][0]<pos["last"][0]):
            first=pos["first"][0]
            after=pos["last"][0]+12
            candidate=words[first:after]
            if len(original)//2<=len(candidate)<=len(original)*2:
                prefix=0
                while (prefix<min(len(original),len(candidate))
                       and original[prefix]==candidate[prefix]):
                    prefix+=1
                suffix=0
                while (suffix<min(len(original),len(candidate))-prefix
                       and original[-1-suffix]==candidate[-1-suffix]):
                    suffix+=1
                original_inside=len(original)-prefix-suffix
                candidate_inside=len(candidate)-prefix-suffix
                collated={
                    "original_authored_source_word_tokens":len(original),
                    "independently_bounded_ccel_digital_word_tokens":len(candidate),
                    "ccel_minus_source_visible_word_count_delta":
                        len(candidate)-len(original),
                    "identical_case_sensitive_prefix_word_tokens":prefix,
                    "identical_case_sensitive_suffix_word_tokens":suffix,
                    "original_inner_unaligned_word_tokens":original_inside,
                    "ccel_inner_unaligned_word_tokens":candidate_inside,
                    "all_bounded_ccel_source_word_tokens_exact":
                        candidate==original,
                    "original_source_gap_ordered_word_sha256":sha256(
                        " ".join(original).encode("utf-8")).hexdigest(),
                    "independent_ccel_bounded_word_sha256":sha256(
                        " ".join(candidate).encode("utf-8")).hexdigest(),
                    "candidate_anchored_by_three_unique_ordered_12word_windows":
                        True,
                    "not_a_proof_of_historical_edition_or_para_owner":True,
                }
        cases.append({
            "original_authored_chapter_ref_sha256":sha256(
                chapter.encode("ascii")).hexdigest(),
            "source_gap_word_offset_not_verse_key":start,
            "source_gap_visible_word_tokens":len(original),
            "independent_ccel_volume":original_volume_number,
            "full_exact_word_sequence_occurrences_in_original_volume":len(whole),
            "first_middle_last_12word_anchors_in_original_ccel":
                sorted(hits[idx]),
            "three_unique_ordered_CCEl_anchor_word_positions_verified":
                collated is not None,
            "bounded_original_source_against_ccel_word_collation":collated,
            "authored_original_OSIS_gap_not_proven_CCEl_editorial_owner":True,
            "no_original_text_or_native_address_exported":True,
        })
    return {
        "status":"PINNED_ORIGINAL_CCEL_VOLUME_AS_INDEPENDENT_DIGITAL_WORD_WITNESS",
        "ccel_volume_number":original_volume_number,
        "original_ccel_volume_sha256":expected_xml_sha256,
        "ccel_visible_word_token_count":len(words),
        "original_source_gap_cases":cases,
        "historical_print_or_derivative_redistribution_not_approved":True,
        "original_ccel_and_osis_bytes_unmodified":True,
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
