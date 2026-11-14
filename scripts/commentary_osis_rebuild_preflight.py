#!/usr/bin/env python3
"""Read-only source-native SWORD -> OSIS wrapper feasibility census.

This is NOT an importer or an edition. It consumes the already SHA-verified
private native raw stream (K numbered, I introduction, U opaque TOP). It tests
that each K/I raw XML fragment can be included verbatim in a standard OSIS
section wrapper while keeping visible Unicode text and local XML structure.
It cannot prove that osis2mod will produce byte-identical original entries;
that requires an independently compiled rebuild and full native readback.

No authorial text, literal attribute, notes or original raw XML are reported.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import re

from lxml import etree

MAX_RAW = 2 * 1024 * 1024
MAX_ENTRIES = 300000
OSIS_NS = b"http://www.bibletechnologies.net/2003/OSIS/namespace"
K = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9]\d*\.[1-9]\d*$")
I = re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*(?:\.(?:0|[1-9]\d*)(?:\.0)?)?$")
U = re.compile(r"^TOP:[1-9]\d*$")


class NativeOSISRebuildPreflight:
    """All checks are metadata-only; a blocker is never silently repaired."""

    def __init__(self):
        self.count = Counter()
        self.shape = Counter()
        self.blockers = Counter()
        self.tags = Counter()
        self.xml_attributes = Counter()
        self.digest_to_keys = defaultdict(list)
        self.opaque_digests = set()

    @staticmethod
    def _safe_parser():
        return etree.XMLParser(resolve_entities=False, no_network=True,
                               load_dtd=False, recover=False, huge_tree=False,
                               strip_cdata=False, remove_blank_text=False)

    @staticmethod
    def _local(tag):
        if not isinstance(tag, str):
            return "_NON_ELEMENT"
        return tag.rsplit("}", 1)[-1]

    def observe(self, kind: str, ref: str, raw: bytes) -> None:
        if (kind not in ("K", "I", "U") or not isinstance(ref, str)
                or not isinstance(raw, bytes) or len(raw) > MAX_RAW
                or b"\x00" in raw):
            raise ValueError("Invalid or oversized original native commentary frame")
        expected = {"K": K, "I": I, "U": U}[kind]
        if expected.fullmatch(ref) is None or sum(self.count.values()) >= MAX_ENTRIES:
            raise ValueError("Invalid original key or excessive number of records")
        self.count[kind] += 1
        if kind == "U":
            self.opaque_digests.add(sha256(raw).hexdigest())
            self.blockers["opaque_top_record_requires_distinct_preservation_plan"] += 1
            return
        digest = sha256(raw).hexdigest()
        self.digest_to_keys[digest].append((kind, ref))
        if not raw.strip():
            self.blockers["empty_original_native_fragment_requires_explicit_mapping"] += 1
            return
        # Many original native keys share one raw commentary entry. Parsing
        # only the first instance preserves the observed number of distinct
        # bodies without accidentally treating keys as authorial sections.
        if len(self.digest_to_keys[digest]) != 1:
            self.shape["duplicate_index_key_same_exact_raw_body"] += 1
            return
        self.shape["distinct_original_xml_body"] += 1
        if b"<!DOCTYPE" in raw.upper() or b"<?XML" in raw.upper():
            self.blockers["inline_document_declaration_requires_special_handling"] += 1
            return
        try:
            source = etree.fromstring(b"<original>" + raw + b"</original>",
                                     self._safe_parser())
            wrapped = etree.fromstring(
                b'<div xmlns="' + OSIS_NS + b'" type="section">' + raw + b"</div>",
                self._safe_parser()
            )
            if any(isinstance(node, etree._Entity)
                   for root in (source, wrapped) for node in root.iter()):
                self.blockers["entity_references_not_automatically_wrappable"] += 1
                return
        except (ValueError, etree.XMLSyntaxError):
            self.blockers["source_fragment_or_standard_osis_wrapper_invalid"] += 1
            return

        self.shape["strict_osis_wrapper_xml_parseable_distinct_bodies"] += 1
        # Verbatim Unicode visible-text comparison, including all whitespace,
        # without any casefold, punctuation normalization or other edits.
        if "".join(source.itertext()) != "".join(wrapped.itertext()):
            self.blockers["wrapping_changes_visible_unicode_text"] += 1
        else:
            self.shape["visible_unicode_text_exactly_preserved_in_wrapper"] += 1
        source_children = list(source)
        wrapped_children = list(wrapped)
        if (len(source_children) != len(wrapped_children)
                or [self._local(n.tag) for n in source_children]
                   != [self._local(n.tag) for n in wrapped_children]):
            self.blockers["wrapping_changes_immediate_element_names_or_counts"] += 1
        else:
            self.shape["immediate_child_element_names_preserved"] += 1
        # We do not claim namespace, byte, serialized or compiled equality:
        # the OSIS wrapper changes default namespaces by definition.
        if (source.text or "").strip():
            self.shape["leading_root_level_nonwhitespace_text"] += 1
        if any((node.tail or "").strip() for node in source):
            self.shape["direct_element_tail_nonwhitespace_text"] += 1
        if not source_children:
            self.shape["no_top_level_child_element"] += 1
        if any(isinstance(n, (etree._Comment, etree._ProcessingInstruction))
               for n in source.iter()):
            self.shape["comments_or_processing_instructions_to_preserve"] += 1
        if b"<![CDATA[" in raw:
            self.shape["cdata_lexical_boundaries_to_preserve"] += 1
        if b"xmlns:" in raw or b"xmlns=" in raw:
            self.shape["source_local_namespace_declaration_to_preserve"] += 1
        for node in source.iter():
            if node is source or not isinstance(node.tag, str):
                continue
            self.tags[self._local(node.tag)] += 1
            for attr in node.attrib:
                self.xml_attributes[self._local(attr)] += 1

    def report(self, *, expected_count: int) -> dict:
        if (type(expected_count) is not int
                or expected_count != sum(self.count.values())
                or expected_count <= 0):
            raise ValueError("Original full native SWORD stream preflight was incomplete")
        sizes = Counter(len(group) for group in self.digest_to_keys.values())
        multi_chapter = 0
        multi_book = 0
        k_i_shared = 0
        for entries in self.digest_to_keys.values():
            if len(entries) < 2:
                continue
            books = {key.split(".", 1)[0] for _, key in entries}
            chapters = {
                key.rsplit(".", 1)[0] if kind == "K" else key
                for kind, key in entries
            }
            multi_chapter += len(chapters) > 1
            multi_book += len(books) > 1
            k_i_shared += len({kind for kind, _ in entries}) > 1
        return {
            "status": "COMPLETE_NATIVE_OSIS_WRAPPER_PREFLIGHT_NOT_A_REBUILD",
            "raw_entries_observed": expected_count,
            "raw_record_kinds": dict(sorted(self.count.items())),
            "unique_nonopaque_payload_sha256_count": len(self.digest_to_keys),
            "payload_sharing_groups_by_number_of_index_keys": {
                str(size): number for size, number in sorted(sizes.items())
            },
            "same_raw_payload_across_chapter_group_count": multi_chapter,
            "same_raw_payload_across_book_group_count": multi_book,
            "same_raw_payload_shared_by_intro_and_numbered_keys_count": k_i_shared,
            "opaque_top_distinct_digest_count": len(self.opaque_digests),
            "original_markup_shape_counts": dict(sorted(self.shape.items())),
            "blocking_or_unresolved_structure_counts": dict(sorted(self.blockers.items())),
            "original_element_counts_by_name": dict(sorted(self.tags.items())),
            "original_attribute_name_counts": dict(sorted(self.xml_attributes.items())),
            "all_original_raw_text_is_unchanged_in_memory": True,
            "full_stock_original_raw_entries_preserved_in_new_module_proven": False,
            "source_to_original_digital_edition_parity_proven": False,
            "canonical_original_introductions_and_TOP_reconstructed": False,
            "compiled_osis_to_stock_byte_parity_proven": False,
            "original_content_or_module_changed": False,
            "publication_authorized": False,
        }
