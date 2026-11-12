#!/usr/bin/env python3
"""Research-only exact text comparison of source ThML body and stock zCom raw.

The trusted previous stages establish source scripCom→next <div> adjacency,
stock occupied anchors, and complete native stock raw corpus enumeration.
This step joins those EVIDENCES by exact original verse/range start anchors.
Original contents are never logged, committed, published or silently rewritten.
Differences are diagnostic; no text or structural parity is certified here.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import zipfile

from lxml import etree

from commentary_intake import load_manifest
from commentary_text_delta import punctuation_relationship, word_relationship, nonword_symbol_excess
from commentary_xml_witness import _parse_reference, WORK_REF, OSIS_LOC, xml_structure, MAX_XML
from commentary_native_raw_inventory import _safe_stock_install, private_crosscheck
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

MAX_DIAGNOSTICS=20


def _original_source_markers(xml_bytes: bytes) -> tuple[dict[str,list[dict]],dict]:
    # Must scan the entire actual original with network/entity resolution off.
    whole=xml_structure(xml_bytes)
    try:
        root=etree.fromstring(xml_bytes,parser=etree.XMLParser(
            resolve_entities=False,no_network=True,load_dtd=False,
            recover=False,huge_tree=False,remove_blank_text=False))
    except (ValueError,etree.XMLSyntaxError):
        raise PilotError("Invalid complete original XML; cannot form commentary units") from None
    sources={}
    counts=Counter()
    original_map_digest=sha256()
    for node in root.iter():
        if not isinstance(node.tag,str) or node.tag.rsplit("}",1)[-1]!="scripCom":
            continue
        original_ref=node.get("osisRef","")
        kind,book=_parse_reference(original_ref)
        counts[kind]+=1
        if kind not in ("work_qualified_verse","work_qualified_same_book_verse_range"):
            continue
        match=WORK_REF.fullmatch(original_ref)
        if not match:
            raise PilotError("Previously reviewed original annotation is no longer qualified")
        start=match.group(2).split("-",1)[0]
        if not OSIS_LOC.fullmatch(start):
            raise PilotError("Original chapter/verse start anchor is unreviewed")
        sibling=node.getnext()
        if sibling is None or not isinstance(sibling.tag,str) or sibling.tag.rsplit("}",1)[-1]!="div":
            raise PilotError("Original verse/range annotation has no exact adjacent div body")
        if node.tail and node.tail.strip():
            raise PilotError("Nonwhitespace original source text between marker and body")
        txt="".join(sibling.itertext())
        if not txt.strip():
            raise PilotError("Empty original source commentary div body")
        text_bytes=txt.encode("utf-8")
        full_ref_bytes=original_ref.encode("utf-8")
        original_map_digest.update(
            len(full_ref_bytes).to_bytes(4,"big")+full_ref_bytes
            +len(text_bytes).to_bytes(8,"big")
            +sha256(text_bytes).digest()
        )
        sources.setdefault(start,[]).append({
            "original_source_line":node.sourceline,
            "original_full_reference_sha256":sha256(full_ref_bytes).hexdigest(),
            "original_text":txt,
            "original_text_sha256":sha256(text_bytes).hexdigest(),
            "original_characters":len(txt)
        })
    if sum(len(rows) for rows in sources.values()) != (
        counts["work_qualified_verse"]+counts["work_qualified_same_book_verse_range"]
    ):
        raise PilotError("Original source annotation count diverged from body inventory")
    if original_map_digest.hexdigest()!=whole[
        "verse_or_range_immediate_div_ordered_unmodified_text_sha256"
    ]:
        raise PilotError("Original body text order and reference digest disagree with prior source scanner")
    return sources,{
        "source_xml_sha256":whole["xml_sha256"],
        "source_marker_total":whole["element_counts"]["scripCom"],
        "original_verse_or_range_body_count":sum(map(len,sources.values())),
        "distinct_original_start_anchors":len(sources),
        "original_ordered_verse_and_range_body_text_sha256":original_map_digest.hexdigest(),
        "chapter_source_markers_not_compared":counts["work_qualified_chapter"],
        "original_unmarked_chapter_division_content_compared":False,
    }


def raw_as_strict_xml_text(raw: bytes) -> str | None:
    """No HTML recovery: malformed raw markup remains unverified."""
    if len(raw)>2*1024*1024 or b"\x00" in raw:
        return None
    try:
        fragment=etree.fromstring(
            b"<original>" + raw + b"</original>",
            parser=etree.XMLParser(
                resolve_entities=False,no_network=True,load_dtd=False,
                recover=False,huge_tree=False,remove_blank_text=False))
        if any(isinstance(node,etree._Entity) for node in fragment.iter()):
            return None
        return "".join(fragment.itertext())
    except (ValueError,UnicodeError,etree.XMLSyntaxError):
        return None


def compare_private_texts(source:dict[str,list[dict]], stocked:dict[str,bytes]) -> dict:
    counters=Counter()
    issues=[]
    lexical_details=Counter()
    punctuation_change_subtypes=Counter()
    word_relationship_subtypes=Counter()
    word_overlap_buckets=Counter()
    stock_containment_locations=Counter()
    stock_extra_prefix_token_bins=Counter()
    stock_extra_suffix_token_bins=Counter()
    source_nonword_glyph_excess=Counter()
    stock_nonword_glyph_excess=Counter()
    bounded_priority_examples=[]
    priority_example_counts=Counter()
    per_book={}
    tested=0
    for start,items in source.items():
        book=start.split(".")[0]
        book_counts=per_book.setdefault(book,Counter())
        raw=stocked.get(start)
        for item in items:
            tested+=1
            if raw is None:
                status="missing_original_start_in_native_raw"
                compiled=None
            else:
                compiled=raw_as_strict_xml_text(raw)
                if compiled is None:
                    status="stock_raw_fragment_not_strict_xml"
                elif compiled==item["original_text"]:
                    status="exact_unicode_text_match"
                elif compiled.strip()==item["original_text"].strip():
                    status="edge_whitespace_difference_only"
                elif " ".join(compiled.split())==" ".join(item["original_text"].split()):
                    status="interior_whitespace_difference_only"
                else:
                    status="lexical_text_or_punctuation_difference"
            if status=="lexical_text_or_punctuation_difference" and compiled is not None:
                a=" ".join(item["original_text"].split())
                b=" ".join(compiled.split())
                if a and a in b:
                    lexical_details["full_original_whitespace_collapsed_body_inside_stock"]+=1
                elif b and b in a:
                    lexical_details["full_stock_whitespace_collapsed_body_inside_original"]+=1
                else:
                    source_tokens=re.findall(r"\w+",a)
                    stock_tokens=re.findall(r"\w+",b)
                    if source_tokens==stock_tokens:
                        lexical_details["same_unicode_word_tokens_different_punctuation"]+=1
                        punctuation_change_subtypes[punctuation_relationship(a,b)]+=1
                        extra_source,extra_stock=nonword_symbol_excess(a,b)
                        source_nonword_glyph_excess.update(extra_source)
                        stock_nonword_glyph_excess.update(extra_stock)
                    else:
                        if [t.casefold() for t in source_tokens]==[t.casefold() for t in stock_tokens]:
                            lexical_details["same_casefolded_word_tokens_different_case_or_punctuation"]+=1
                        else:
                            lexical_details["different_unicode_word_token_sequence_or_selection"]+=1
                        diagnostic=word_relationship(a,b)
                        category=diagnostic["relationship"]
                        word_relationship_subtypes[category]+=1
                        word_overlap_buckets[diagnostic["overlap_bucket"]]+=1
                        if category=="source_words_contiguous_inside_longer_stock":
                            position=diagnostic["original_words_contiguous_in_stock_location"]
                            stock_containment_locations[position]+=1
                            for value,bins in (
                                (diagnostic["additional_stock_word_tokens_before_source"],stock_extra_prefix_token_bins),
                                (diagnostic["additional_stock_word_tokens_after_source"],stock_extra_suffix_token_bins),
                            ):
                                if value==0: b="0"
                                elif value<=4: b="1_to_4"
                                elif value<=9: b="5_to_9"
                                elif value<=29: b="10_to_29"
                                else: b="30_or_more"
                                bins[b]+=1
                        if priority_example_counts[category]<4:
                            priority_example_counts[category]+=1
                            bounded_priority_examples.append({
                                "source_line":item["original_source_line"],
                                "original_reference_sha256":item["original_full_reference_sha256"],
                                "original_unicode_characters":item["original_characters"],
                                "stock_raw_sha256":sha256(raw).hexdigest(),
                                "original_word_token_count":diagnostic["original_word_token_count"],
                                "stock_word_token_count":diagnostic["stock_word_token_count"],
                                "shared_word_token_occurrences":diagnostic["shared_word_token_multiset_occurrences"],
                                "relationship":category,
                                "word_overlap_bucket":diagnostic["overlap_bucket"],
                            })
            counters[status]+=1
            book_counts[status]+=1
            if status!="exact_unicode_text_match" and len(issues)<MAX_DIAGNOSTICS:
                issues.append({
                    "source_line":item["original_source_line"],
                    "original_reference_sha256":item["original_full_reference_sha256"],
                    "original_text_sha256":item["original_text_sha256"],
                    "original_unicode_characters":item["original_characters"],
                    "stock_raw_sha256":sha256(raw).hexdigest() if raw is not None else None,
                    "stock_raw_bytes":len(raw) if raw is not None else None,
                    "status":status,
                })
    if tested!=sum(map(len,source.values())):
        raise PilotError("Original commentary text comparison was incomplete")
    if sum(counters.values())!=tested:
        raise PilotError("Original commentary text status totals are inconsistent")
    if sum(lexical_details.values())!=counters["lexical_text_or_punctuation_difference"]:
        raise PilotError("Detailed text discrepancy census does not reconcile with every source body")
    if sum(punctuation_change_subtypes.values())!=lexical_details["same_unicode_word_tokens_different_punctuation"]:
        raise PilotError("Punctuation discrepancy subtotals do not account for all matching word sequences")
    if sum(word_relationship_subtypes.values())!=(
        lexical_details["same_casefolded_word_tokens_different_case_or_punctuation"]
        +lexical_details["different_unicode_word_token_sequence_or_selection"]
    ):
        raise PilotError("Unequal-word relationships have incomplete full-corpus accounting")
    if sum(word_overlap_buckets.values())!=sum(word_relationship_subtypes.values()):
        raise PilotError("Word overlap ratio categories have incomplete accounting")
    if sum(stock_containment_locations.values())!=word_relationship_subtypes[
        "source_words_contiguous_inside_longer_stock"
    ]:
        raise PilotError("Full original-in-stock containment location census is incomplete")
    if (sum(stock_extra_prefix_token_bins.values())!=sum(stock_containment_locations.values())
            or sum(stock_extra_suffix_token_bins.values())!=sum(stock_containment_locations.values())):
        raise PilotError("Extra stock word prefix/suffix bins do not account for the complete containment group")
    if len(bounded_priority_examples)>40:
        raise PilotError("Private difference sample exceeds reviewed non-text bound")
    return {
        "source_verse_or_range_bodies_compared":tested,
        "same_words_different_punctuation_subtypes":dict(sorted(punctuation_change_subtypes.items())),
        "different_word_sequence_relationship_subtypes":dict(sorted(word_relationship_subtypes.items())),
        "different_word_sequence_overlap_buckets":dict(sorted(word_overlap_buckets.items())),
        "stock_containment_additional_word_position_counts":dict(sorted(stock_containment_locations.items())),
        "stock_containment_extra_stock_prefix_word_token_bins":dict(sorted(stock_extra_prefix_token_bins.items())),
        "stock_containment_extra_stock_suffix_word_token_bins":dict(sorted(stock_extra_suffix_token_bins.items())),
        "punctuation_nonword_glyph_excess_source_total":sum(source_nonword_glyph_excess.values()),
        "punctuation_nonword_glyph_excess_stock_total":sum(stock_nonword_glyph_excess.values()),
        "punctuation_nonword_glyph_excess_source_top_numeric_codepoints":dict(source_nonword_glyph_excess.most_common(16)),
        "punctuation_nonword_glyph_excess_stock_top_numeric_codepoints":dict(stock_nonword_glyph_excess.most_common(16)),
        "punctuation_codepoint_frequency_is_not_authorial_approval":True,
        "bounded_private_prioritized_hash_line_diagnostics":bounded_priority_examples,
        "all_detailed_difference_diagnostics_are_research_only":True,
        "lexical_disagreement_classification":dict(sorted(lexical_details.items())),
        "disagreement_categories_are_only_exploratory_not_text_parity":True,
        "per_source_marker_text_diagnostic_counts":dict(sorted(counters.items())),
        "book_counts":{name:dict(sorted(counts.items())) for name,counts in sorted(per_book.items())},
        "bounded_private_content_discrepancy_hash_samples":issues,
        "whitespace_only_status_is_not_exact_text_parity":True,
        "no_autocorrection_or_content_normalization_performed":True,
        "all_selected_verse_range_body_text_exact_matches":counters["exact_unicode_text_match"]==tested,
        "original_paragraphs_notes_and_quotations_verified":False,
        "full_authored_to_stock_parity_verified":False,
    }


def run(resource_id: str, index_binary: Path, raw_binary: Path) -> dict:
    manifest=load_manifest(resource_id)
    original_config=manifest.get("commentary_source",{})
    url=original_config.get("xml_witness_url")
    original_sha=original_config.get("xml_witness_sha256")
    stock_sha=manifest.get("archive_sha256")
    if not all(isinstance(v,str) and len(v)==64 for v in (original_sha,stock_sha)):
        raise PilotError("Exact original XML and SWORD SHA-256 pins required")
    if not isinstance(url,str) or not url.startswith("https://www.ccel.org/ccel/h/"):
        raise PilotError("Unreviewed original source URL")
    if any(path.is_symlink() or not path.is_file() for path in (index_binary,raw_binary)):
        raise PilotError("Trusted native engine executable unavailable")
    with tempfile.TemporaryDirectory(prefix="commentary-private-text-compare-") as temp:
        root=Path(temp)
        xml_file=root/"original.xml"
        stock_file=root/"stock.zip"
        obs_xml=fetch(url,xml_file,"ccel")
        obs_stock=fetch(manifest["sword_zip_url"],stock_file,manifest["provider"])
        if obs_xml["sha256"]!=original_sha or obs_stock["sha256"]!=stock_sha:
            raise PilotError("Original CCEL text or CrossWire ZIP changed; abort text comparison")
        if obs_xml["bytes"]>MAX_XML:
            raise PilotError("Pinned XML exceeds original-source maximum")
        source,source_proof=_original_source_markers(xml_file.read_bytes())
        stock_meta=inspect_archive(stock_file,source_kind="sword",
                                   expected_module_id=manifest["module_id"],
                                   expected_category="commentary")
        conf=stock_meta["sword_conf"]
        if conf["version"]!=manifest["version"] or conf["language"]!=manifest["language"]:
            raise PilotError("Unexpected stock SWORD version/language")
        installed=root/"installed"
        _safe_stock_install(stock_file,stock_meta["members"],installed)
        env=dict(os.environ,SWORD_PATH=str(installed))
        try:
            ix=subprocess.run([str(index_binary),manifest["module_id"]],
                              capture_output=True,timeout=60,env=env,check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Original native index timed out") from None
        if ix.returncode or len(ix.stdout)>12*1024*1024:
            raise PilotError("Original native occupied key index not independently available")
        process=None
        rows=[]
        matches={}
        try:
            process=subprocess.Popen(["timeout","360s",str(raw_binary),manifest["module_id"]],
                                     stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env)
            if process.stdout is None:
                raise PilotError("Cannot capture stock raw XML privately")
            def collect(kind,ref,raw):
                rows.append((kind,ref))
                if kind=="K" and ref in source:
                    matches[ref]=raw
            raw_summary,_,_,_=parse_native_raw_corpus(process.stdout,on_entry=collect)
            process.stdout.close()
            status=process.wait(timeout=15)
            if status!=0:
                raise PilotError("Stock SWORD native text reader failed to finish its complete stream")
        except BaseException:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            raise
        crosscheck=private_crosscheck(ix.stdout,manifest["module_id"],rows,raw_summary)
        analysis=compare_private_texts(source,matches)
    return {
        "schema_version":1,
        "resource_id":resource_id,
        "status":"full_source_verse_and_range_body_to_stock_raw_text_diagnostics_not_release_approval",
        "source_original_sha256":original_sha,
        "stock_sword_archive_sha256":stock_sha,
        "stock_sword_conf_sha256":conf["conf_sha256"],
        "stock_full_raw_content_sha256":raw_summary["all_native_raw_entries_ordered_sha256"],
        "stock_native_key_order_sha256":crosscheck["native_key_order_sha256"],
        "native_full_corpus_rechecked":True,
        "source_original_verse_and_range_body_evidence":source_proof,
        "text_diagnostic":analysis,
        "original_source_divisions_without_markers_compared":False,
        "chapter_intro_and_body_lexical_parity_compared":False,
        "original_exact_edition_proven":False,
        "original_structure_notes_quotes_and_paragraphs_parity_proven":False,
        "copyright_and_redistribution_approved":False,
        "editorial_approved":False,
        "published":False,
        "source_text_or_sword_bytes_in_receipt":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id",required=True)
    p.add_argument("--native-index-binary",required=True,type=Path)
    p.add_argument("--native-raw-binary",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        result=run(args.resource_id,args.native_index_binary,args.native_raw_binary)
        code=0
    except (ValueError,OSError,RuntimeError,zipfile.BadZipFile) as exc:
        result={"status":"blocked","resource_id":args.resource_id,"reason":str(exc),
                "full_authored_to_stock_parity_verified":False,"published":False}
        code=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Commentary original ↔ stock text diagnostics: "+result["status"]+" (no original text disclosed)")
    return code


if __name__=="__main__":
    raise SystemExit(main())
