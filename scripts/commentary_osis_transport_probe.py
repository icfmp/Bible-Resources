#!/usr/bin/env python3
"""Research-only transport of selected *original* numbered SWORD raw XML to OSIS.

The output is private temporary test material, NEVER a curated commentary
edition. Original K raw fragments are inserted verbatim, without HTML escaping,
punctuation normalization or re-authoring. Contiguous native keys whose bytes
are exactly identical can be represented by one range; this is a transport
compression only, NOT proof that an author intended a joint editorial section.

I introductions and U TOP are deliberately NOT included; this script MUST NOT
be used to create a distributable module. The caller must separately check all
original native entries and the independently determined editorial scopes.
"""
from __future__ import annotations

from hashlib import sha256
from collections import Counter
import re
from lxml import etree

KEY = re.compile(r"^([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9]\d*)\.([1-9]\d*)$")
WORK = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,39}$")
MAX_FRAGMENTS = 12000
MAX_BYTES = 160 * 1024 * 1024
OSIS_NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def _strict_parser():
    return etree.XMLParser(resolve_entities=False, no_network=True,
                           load_dtd=False, recover=False, huge_tree=False,
                           remove_blank_text=False, strip_cdata=False)


def _source_visible_text(raw: bytes) -> str:
    try:
        root = etree.fromstring(b"<fragment>" + raw + b"</fragment>",
                               parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Original SWORD XML is not safely parseable") from None
    if any(isinstance(node, etree._Entity) for node in root.iter()):
        raise ValueError("Unresolved source XML entity")
    return "".join(root.itertext())


def build_numbered_transport_sample(entries: list[tuple[str, bytes]],
                                    *, work_id: str) -> tuple[bytes, dict]:
    """Return private syntactically parsed OSIS bytes plus text-free receipt."""
    if not WORK.fullmatch(work_id):
        raise ValueError("Invalid isolated synthetic transport module work ID")
    if not entries or len(entries) > MAX_FRAGMENTS:
        raise ValueError("Empty or excessive sampled commentary K records")

    groups = []
    seen = set()
    total_bytes = 0
    last_pos = None
    last_book_chapter = None
    for ref, raw in entries:
        matched = KEY.fullmatch(ref) if isinstance(ref, str) else None
        if (matched is None or ref in seen or not isinstance(raw, bytes)
                or b"\x00" in raw or not raw.strip()):
            raise ValueError("Unreviewed original sampled K frame")
        seen.add(ref)
        book, chapter, verse = matched.group(1), int(matched.group(2)), int(matched.group(3))
        location = (book, chapter, verse)
        if last_pos is not None and (book, chapter) == last_book_chapter and verse <= last_pos[2]:
            raise ValueError("Original native K frame order is not increasing within chapter")
        # The independent full raw stream controls canonical inter-book order.
        if last_pos is not None and (book, chapter) != last_book_chapter:
            if (book, chapter) in {group["chapter_key"] for group in groups}:
                raise ValueError("Original chapter appeared non-contiguously in sampled stream")
        total_bytes += len(raw)
        if total_bytes > MAX_BYTES:
            raise ValueError("Selected original raw content exceeds bounded private OSIS probe")
        _source_visible_text(raw)
        digest = sha256(raw).hexdigest()
        if (groups and groups[-1]["chapter_key"] == (book, chapter)
                and groups[-1]["digest"] == digest
                and groups[-1]["last_verse"] + 1 == verse):
            groups[-1]["last_verse"] = verse
            groups[-1]["native_key_count"] += 1
        else:
            groups.append({
                "chapter_key": (book, chapter),
                "first_verse": verse, "last_verse": verse,
                "digest": digest, "raw": raw, "native_key_count": 1
            })
        last_book_chapter = book, chapter
        last_pos = location

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>'.encode(),
        f'<osis xmlns="{OSIS_NS}">'.encode(),
        f'<osisText osisIDWork="{work_id}" osisRefWork="Commentary" xml:lang="en" canonical="true">'.encode(),
        (f'<header><work osisWork="{work_id}"><title>Synthetic temporary original-'
         f'raw OSIS transport probe</title><identifier type="OSIS">'
         f'{work_id}</identifier><refSystem>Bible.KJV</refSystem></work></header>').encode(),
        b'<div type="bookGroup">',
    ]
    current_book = None
    current_chapter = None
    for group in groups:
        book, chapter = group["chapter_key"]
        if book != current_book:
            if current_chapter is not None:
                parts.append(b"</div>")
            if current_book is not None:
                parts.append(b"</div>")
            parts.append(f'<div type="book" osisID="{book}">'.encode())
            current_book = book
            current_chapter = None
        if chapter != current_chapter:
            if current_chapter is not None:
                parts.append(b"</div>")
            parts.append(f'<div type="chapter" osisID="{book}.{chapter}">'.encode())
            current_chapter = chapter
        first, last = group["first_verse"], group["last_verse"]
        ref = f"{book}.{chapter}.{first}"
        if last != first:
            ref += f"-{book}.{chapter}.{last}"
        parts.append(
            f'<div type="section" annotateType="commentary" annotateRef="{ref}">'.encode()
        )
        parts.append(group["raw"])
        parts.append(b"</div>")
    if current_chapter is not None:
        parts.append(b"</div>")
    if current_book is not None:
        parts.append(b"</div>")
    parts.extend([b"</div>", b"</osisText>", b"</osis>"])
    # Do not insert formatting newlines into original commentary XML.
    # Even one artificial separator would change the authorial whitespace.
    xml = b"".join(parts)
    if len(xml) > MAX_BYTES + MAX_FRAGMENTS * 320:
        raise ValueError("Private transport document exceeds safe length")

    try:
        parsed = etree.fromstring(xml, parser=_strict_parser())
    except (ValueError, etree.XMLSyntaxError):
        raise ValueError("Verbatim source fragments do not form a valid OSIS XML document") from None
    if any(isinstance(node, etree._Entity) for node in parsed.iter()):
        raise ValueError("Unsafe entity in selected transport OSIS document")
    wrapped_sections = parsed.xpath(
        "//*[local-name()='div' and @annotateType='commentary']"
    )
    if len(wrapped_sections) != len(groups):
        raise ValueError("Verbatim source sections were not preserved in standard OSIS wrapper")
    for group, section in zip(groups, wrapped_sections):
        if "".join(section.itertext()) != _source_visible_text(group["raw"]):
            raise ValueError("Original fragment lost or changed Unicode characters in OSIS wrapper")
    return xml, {
        "status": "ORIGINAL_NUMBERED_ONLY_TEMPORARY_TRANSPORT_NOT_EDITION",
        "input_numbered_native_keys": len(entries),
        "contiguous_identical_raw_body_groups": len(groups),
        "groups_with_multiple_original_native_verse_keys":
            sum(group["native_key_count"] > 1 for group in groups),
        "source_original_raw_bytes_in_reviewed_input": total_bytes,
        "source_original_raw_bytes_included_verbatim_in_osis": sum(
            len(group["raw"]) for group in groups
        ),
        "temporary_osis_bytes": len(xml),
        "source_unmodified_unicode_visible_text_in_syntax_approved_osis": True,
        "original_introductions_preserved_in_candidate": False,
        "original_top_preserved_in_candidate": False,
        "compiler_roundtrip_parity_proven": False,
        "authorial_scope_approved": False,
        "no_publication": True,
    }


def classify_native_osis_roundtrip_delta(original_raw: bytes, compiled_raw: bytes) -> dict:
    """Bounded metadata-only classification of an osis2mod transport delta."""
    from collections import Counter
    from commentary_nonlink_word_alignment import plain_word_alignment

    original_text = _source_visible_text(original_raw)
    compiled_text = _source_visible_text(compiled_raw)
    source_words = re.findall(r"\w+", original_text.casefold())
    compiled_words = re.findall(r"\w+", compiled_text.casefold())
    if len(source_words) > 200000 or len(compiled_words) > 200000:
        raise ValueError("Oversize compiled commentary word comparison")
    if source_words == compiled_words:
        category = "EXACT_ORIGINAL_WORD_SEQUENCE"
    else:
        aligned = plain_word_alignment(source_words, compiled_words)
        if aligned["original_plain_words_not_matched_in_exact_order"] == 0:
            category = "ALL_ORIGINAL_WORDS_IN_ORDER_WITH_ADDITIONAL_COMPILED_WORDS"
        elif aligned["stock_plain_words_not_matched_in_exact_order"] == 0:
            category = "COMPILED_WORDS_A_SUBSEQUENCE_OF_ORIGINAL"
        else:
            category = "MISSING_OR_REORDERED_OR_CHANGED_WORDS"
    def element_counts(raw):
        root = etree.fromstring(b"<fragment>" + raw + b"</fragment>",
                              parser=_strict_parser())
        result = Counter()
        for node in root.iter():
            if node is root or not isinstance(node.tag, str):
                continue
            result[node.tag.rsplit("}", 1)[-1]] += 1
        return result
    original_tags = element_counts(original_raw)
    compiled_tags = element_counts(compiled_raw)

    def element_signatures(raw):
        root = etree.fromstring(b"<fragment>" + raw + b"</fragment>",
                              parser=_strict_parser())
        ordinary = []
        divs = Counter()
        references = []
        for el in root.iter():
            if el is root or not isinstance(el.tag, str):
                continue
            local = el.tag.rsplit("}", 1)[-1]
            attrs = tuple(sorted(el.attrib.items()))
            if local == "div":
                divs[attrs] += 1
            else:
                ordinary.append((local, attrs))
            if local == "reference":
                references.append(tuple(sorted(el.attrib.items())))
        return ordinary, divs, references

    def non_div_text_ownership(raw):
        """Preserve semantic XML nesting AND exact text/tail boundaries.

        Build a balanced sequence of opening/closing non-div semantic tags and
        original non-whitespace text tokens between those boundaries. Standard
        SWORD can insert div containers without moving authorial content, so
        only div *boundaries* are ignored; their contained text, children and
        tail positions remain in their original document order. This rejects
        moving text into a reference link, between sibling text/tail slots or
        into a different original paragraph, even if all flattened words,
        element counts, attributes and reference destinations still match.

        The return value is compared only in memory; neither source words nor
        markup structure is logged in a diagnostic receipt.
        """
        root = etree.fromstring(b"<fragment>" + raw + b"</fragment>",
                              parser=_strict_parser())
        sequence = []

        def add(value):
            if value:
                sequence.extend(("text", token)
                                for token in re.findall(r"\S+", value))

        def walk(node):
            local = node.tag.rsplit("}", 1)[-1]
            semantic = node is not root and local != "div"
            if semantic:
                sequence.append(("open", local))
            add(node.text)
            for child in node:
                if isinstance(child.tag, str):
                    walk(child)
                add(child.tail)
            if semantic:
                sequence.append(("close", local))

        walk(root)
        return sequence

    source_attrs, source_div_attrs, source_references = element_signatures(original_raw)
    compiled_attrs, compiled_div_attrs, compiled_references = element_signatures(compiled_raw)
    original_divs_preserved = all(
        compiled_div_attrs[attrs] >= count
        for attrs, count in source_div_attrs.items()
    )
    only_added_div_wrappers_by_local_name = (
        all(compiled_tags[name] == count
            for name, count in original_tags.items() if name != "div")
        and all(name == "div" or name in original_tags
                for name in compiled_tags)
        and compiled_tags["div"] >= original_tags["div"]
    )
    return {
        "source_original_unfiltered_raw_bytes": len(original_raw),
        "compiled_candidate_unfiltered_raw_bytes": len(compiled_raw),
        "source_original_visible_text_characters": len(original_text),
        "compiled_visible_text_characters": len(compiled_text),
        "source_original_unicode_word_tokens": len(source_words),
        "compiled_unicode_word_tokens": len(compiled_words),
        "word_sequence_relation": category,
        "normalized_whitespace_visible_unicode_equal": (
            " ".join(original_text.split()) == " ".join(compiled_text.split())
        ),
        "all_original_markup_element_names_and_counts_preserved": (
            original_tags == compiled_tags
        ),
        "original_markup_element_counts": dict(sorted(original_tags.items())),
        "compiled_markup_element_counts": dict(sorted(compiled_tags.items())),
        "non_div_element_order_and_exact_attribute_values_preserved":
            source_attrs == compiled_attrs,
        "original_div_elements_exact_attribute_multiset_preserved":
            original_divs_preserved,
        "reference_attribute_values_in_original_document_order_preserved":
            source_references == compiled_references,
        "original_nondiv_text_and_tail_ownership_preserved":
            non_div_text_ownership(original_raw) == non_div_text_ownership(compiled_raw),
        "only_div_element_count_added_not_other_element_names":
            only_added_div_wrappers_by_local_name,
        "original_xml_bytes_modified": original_raw != compiled_raw,
        "source_prose_and_markup_parity_approved": False,
    }


def isolated_osis2mod_original_sample_roundtrip(
    entries: list[tuple[str, bytes]], *, scratch, native_raw_binary,
    osis2mod_binary="osis2mod", work_id="BRTransportProbe"
) -> dict:
    """Compile ONLY temporary K samples and privately compare native readbacks.

    The original module is never opened as a writable target. Original I/TOP
    and original metadata are omitted by definition, so even an exact K sample
    match is not an authorial, publication or complete edition parity proof.
    """
    from io import BytesIO
    import os
    from pathlib import Path
    import subprocess
    from sword_native_raw_corpus_inventory import parse_native_raw_corpus

    scratch = Path(scratch)
    reader = Path(native_raw_binary)
    if (not scratch.is_dir() or scratch.is_symlink()
            or not reader.is_file() or reader.is_symlink()):
        raise ValueError("Unverified isolated sample directory or native inspector")
    raw_osis, original_report = build_numbered_transport_sample(
        entries, work_id=work_id
    )
    root = scratch / "temporary-numbered-transport"
    if root.exists() or root.is_symlink():
        raise ValueError("Temporary OSIS transport proof destination already exists")
    conf = root / "mods.d" / (work_id + ".conf")
    destination = root / "modules" / "comments" / "zcom" / work_id
    destination.mkdir(parents=True)
    conf.parent.mkdir()
    input_file = root / "input-private.osis.xml"
    input_file.write_bytes(raw_osis)
    if input_file.stat().st_size != len(raw_osis):
        raise ValueError("Private OSIS source was not written completely")
    args = [
        str(osis2mod_binary), str(destination), str(input_file),
        "-z", "z", "-b", "3", "-v", "KJV"
    ]
    try:
        compiled = subprocess.run(
            args, cwd=root, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=False, timeout=150
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            **original_report,
            "status": "TEMPORARY_NUMBERED_SAMPLE_COMPILER_UNAVAILABLE_OR_TIMEOUT",
            "compiled_native_readback_completed": False,
            "all_original_intros_and_top_preserved": False,
            "publication_authorized": False,
        }
    if compiled.returncode != 0:
        return {
            **original_report,
            "status": "TEMPORARY_NUMBERED_SAMPLE_COMPILER_RETURNED_ERROR",
            "compiled_native_readback_completed": False,
            "all_original_intros_and_top_preserved": False,
            "publication_authorized": False,
        }
    conf.write_text(
        f"[{work_id}]\n"
        f"DataPath=./modules/comments/zcom/{work_id}\n"
        "ModDrv=zCom\nCompressType=ZIP\nBlockType=CHAPTER\n"
        "SourceType=OSIS\nVersification=KJV\nLang=en\n"
        "Description=Private original-native transport diagnostic only\n",
        encoding="utf-8"
    )
    env = dict(os.environ, SWORD_PATH=str(root))
    try:
        native = subprocess.run(
            [str(reader), work_id], cwd=root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=False, timeout=90
        )
    except (OSError, subprocess.TimeoutExpired):
        native = None
    if native is None or native.returncode or len(native.stdout) > MAX_BYTES:
        return {
            **original_report,
            "status": "TEMPORARY_NUMBERED_SAMPLE_NATIVE_READBACK_FAILED",
            "compiled_native_readback_completed": False,
            "all_original_intros_and_top_preserved": False,
            "publication_authorized": False,
        }
    rebuilt = {}
    def receive(kind, key, raw):
        if kind == "K":
            rebuilt[key] = raw
    parsed, _, intros, top = parse_native_raw_corpus(
        BytesIO(native.stdout), on_entry=receive
    )
    original = dict(entries)
    if len(original) != len(entries):
        raise ValueError("Duplicate original numbered input reference")
    matched = original.keys() & rebuilt.keys()
    exact_bytes = sum(original[key] == rebuilt[key] for key in matched)
    exact_visible = 0
    unparseable_candidate = 0
    delta_classes = Counter()
    normalized_text_equal = 0
    tags_equal = 0
    exact_nondiv_attributes = 0
    original_div_attributes_preserved = 0
    original_reference_attributes_preserved = 0
    only_extra_div_tags = 0
    original_total_element_names = Counter()
    compiled_total_element_names = Counter()
    changed_element_name_entry_counts = Counter()
    delta_cases = []
    for key in sorted(matched):
        try:
            exact_visible += _source_visible_text(original[key]) == _source_visible_text(rebuilt[key])
            comparison = classify_native_osis_roundtrip_delta(original[key], rebuilt[key])
            delta_classes[comparison["word_sequence_relation"]] += 1
            normalized_text_equal += comparison["normalized_whitespace_visible_unicode_equal"]
            tags_equal += comparison["all_original_markup_element_names_and_counts_preserved"]
            exact_nondiv_attributes += comparison[
                "non_div_element_order_and_exact_attribute_values_preserved"
            ]
            original_div_attributes_preserved += comparison[
                "original_div_elements_exact_attribute_multiset_preserved"
            ]
            original_reference_attributes_preserved += comparison[
                "reference_attribute_values_in_original_document_order_preserved"
            ]
            only_extra_div_tags += comparison[
                "only_div_element_count_added_not_other_element_names"
            ]
            source_elements = Counter(comparison["original_markup_element_counts"])
            converted_elements = Counter(comparison["compiled_markup_element_counts"])
            original_total_element_names.update(source_elements)
            compiled_total_element_names.update(converted_elements)
            changed_element_name_entry_counts.update(
                name for name in source_elements.keys() | converted_elements.keys()
                if source_elements[name] != converted_elements[name]
            )
            delta_cases.append({
                "original_native_key": key,
                "word_sequence_relation": comparison["word_sequence_relation"],
                "source_word_count": comparison["source_original_unicode_word_tokens"],
                "compiled_word_count": comparison["compiled_unicode_word_tokens"],
                "source_markup_elements": comparison["original_markup_element_counts"],
                "compiled_markup_elements": comparison["compiled_markup_element_counts"],
                "normalized_whitespace_text_identical":
                    comparison["normalized_whitespace_visible_unicode_equal"],
            })
        except ValueError:
            unparseable_candidate += 1
    return {
        **original_report,
        "status": "TEMPORARY_NUMBERED_NATIVE_TRANSPORT_READBACK_COMPLETED",
        "compiled_native_readback_completed": True,
        "original_numbered_keys_in_compiled_sample": len(matched),
        "original_numbered_keys_missing_from_compiled_sample": len(original) - len(matched),
        "additional_numbered_keys_in_compiled_sample": len(rebuilt.keys() - original.keys()),
        "original_raw_xml_exact_byte_matches": exact_bytes,
        "original_raw_xml_visible_unicode_text_matches": exact_visible,
        "compiled_entries_unparseable_as_original_fragments": unparseable_candidate,
        "original_vs_compiled_word_sequence_classes": dict(sorted(delta_classes.items())),
        "original_vs_compiled_whitespace_normalized_visible_text_exact_matches":
            normalized_text_equal,
        "original_vs_compiled_element_name_count_exact_matches": tags_equal,
        "original_non_div_element_order_and_attribute_value_exact_matches":
            exact_nondiv_attributes,
        "original_div_element_attribute_multiset_preserved_entry_count":
            original_div_attributes_preserved,
        "original_reference_attribute_value_exact_order_matches":
            original_reference_attributes_preserved,
        "only_additional_div_tags_other_markup_names_unchanged":
            only_extra_div_tags,
        "original_native_element_name_total_counts_in_sample":
            dict(sorted(original_total_element_names.items())),
        "compiled_native_element_name_total_counts_in_sample":
            dict(sorted(compiled_total_element_names.items())),
        "source_to_compiled_element_name_count_changed_entry_counts":
            dict(sorted(changed_element_name_entry_counts.items())),
        "per_original_key_text_free_delta_classes": delta_cases,
        "compiled_numbered_entry_count": parsed["actual_occupied_numbered_entry_count"],
        "compiled_introduction_entry_count_not_parity_approved": len(intros),
        "compiled_opaque_top_entry_count_not_parity_approved": len(top),
        "original_module_content_or_metadata_modified": False,
        "all_original_intros_and_top_preserved": False,
        "source_to_original_digital_edition_fidelity_proven": False,
        "publication_authorized": False,
    }
