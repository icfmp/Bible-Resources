#!/usr/bin/env python3
"""Review and conservatively clean source OSIS without altering its edition.

The output is a *private candidate*, not a new authoritative edition. Read
source SHA pins, leave the source unchanged, count suspicious punctuation and
markup (never output prose), and apply only precisely specified cosmetic
transformations. Do not remove asterisks or note callers on heuristics.
Works with all OSIS languages and is independent of CrossWire/MHC.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from lxml import etree

MAX_BYTES = 128 * 1024 * 1024
MAX_ELEMENTS = 800_000
SHA = re.compile(r"[0-9a-f]{64}\Z")
INTERNAL_SPACES = re.compile(r"(?<=\S) {2,}(?=\S)")
PROTECTED = frozenset({"note", "reference", "lg", "l", "q", "table", "row", "cell"})
DISPLAY_ONLY_HI = frozenset({"italic", "bold", "small-caps", "super", "underline"})


class CleanupError(ValueError):
    pass


def _local(node) -> str:
    return node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else "#other"


def _tree(raw: bytes):
    if b"<!DOCTYPE" in raw.upper():
        raise CleanupError("OSIS DTD must not be present")
    parser = etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        recover=False, remove_blank_text=False, remove_comments=False,
        strip_cdata=False, huge_tree=True
    )
    try:
        root = etree.fromstring(raw, parser=parser)
    except (etree.XMLSyntaxError, ValueError):
        raise CleanupError("Original OSIS XML is invalid") from None
    if _local(root) != "osis":
        raise CleanupError("Input is not an OSIS source")
    if any(isinstance(n, etree._Entity) for n in root.iter()):
        raise CleanupError("Unresolved XML entity in source")
    return root


def _load(path: Path, digest: str) -> bytes:
    if (path.is_symlink() or not path.is_file()
            or not isinstance(digest, str) or not SHA.fullmatch(digest)
            or not 100 <= path.stat().st_size <= MAX_BYTES):
        raise CleanupError("Missing, unsafe or unpinned source")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise CleanupError("Original source SHA-256 differs from reviewed pin")
    return raw


def _inert_hi(node) -> bool:
    """Only a truly empty styling leaf, outside protected note/reference data."""
    return (
        _local(node) == "hi"
        and not len(node)
        and node.text in (None, "")
        and set(node.attrib) == {"type"}
        and node.get("type") in DISPLAY_ONLY_HI
        and node.getparent() is not None
        and not any(_local(parent) in PROTECTED
                    for parent in node.iterancestors())
    )


def _text_hashes(root) -> tuple[str, str]:
    """Hash exact text and all text without ASCII spaces, in XML document order."""
    exact = sha256()
    no_ascii_spaces = sha256()
    for fragment in root.itertext():
        exact.update(fragment.encode("utf-8"))
        no_ascii_spaces.update(fragment.replace(" ", "").encode("utf-8"))
    return exact.hexdigest(), no_ascii_spaces.hexdigest()


def _remove_empty_hi(node) -> None:
    """Splice an inert styling leaf without altering a single text character."""
    if not _inert_hi(node):
        raise CleanupError("Attempt to remove a non-inert emphasis element")
    parent = node.getparent()
    previous = node.getprevious()
    if node.tail:
        if previous is None:
            parent.text = (parent.text or "") + node.tail
        else:
            previous.tail = (previous.tail or "") + node.tail
    parent.remove(node)


def _structure(root, *, skip_inert_hi: bool = False):
    items = []
    for node in root.iter():
        if skip_inert_hi and _inert_hi(node):
            continue
        if len(items) >= MAX_ELEMENTS:
            raise CleanupError("Too many source XML nodes")
        if isinstance(node.tag, str):
            items.append((node.tag, tuple(sorted(node.attrib.items()))))
        else:
            # Do not erase comments or processing instructions.
            items.append((type(node).__name__, node.text or ""))
    return tuple(items)


def _protected_text(root):
    # Node-by-node exact Unicode semantics of notes and cited links.
    return tuple((_local(node), "".join(node.itertext()))
                 for node in root.iter()
                 if _local(node) in {"note", "reference"})


def _census(root):
    hits = Counter()
    by_owner = Counter()
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        owner = _local(node)
        for value in (node.text, node.tail):
            if not value:
                continue
            hits["literal_escaped_asterisks"] += value.count(r"\*")
            hits["triple_asterisk_runs"] += value.count("***")
            hits["double_asterisk_runs"] += value.count("**")
            hits["standalone_asterisk_characters"] += value.count("*")
            hits["nonbreaking_spaces"] += value.count("\u00a0")
            hits["zero_width_spaces"] += value.count("\u200b")
            hits["tab_characters"] += value.count("\t")
            hits["repeated_internal_ascii_spaces"] += len(INTERNAL_SPACES.findall(value))
            by_owner[owner] += len(value)
    return dict(sorted(hits.items())), dict(sorted(by_owner.items()))


def _markup_profile(root):
    """Metadata-only source markup risk profile, never a deletion instruction."""
    elements = Counter()
    emphasis = Counter()
    emphasis_parent = Counter()
    emphasis_text_size = Counter()
    nbsp_owner = Counter()
    empty_emphasis_shape = Counter()
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        name = _local(node)
        elements[name] += 1
        for fragment in (node.text, node.tail):
            if fragment:
                nbsp_owner[name] += fragment.count("\u00a0")
        if name == "hi":
            if not len(node) and not (node.text or ""):
                if set(node.attrib)=={"type"}:
                    empty_emphasis_shape["empty_leaf_with_type_only"] += 1
                else:
                    empty_emphasis_shape["empty_leaf_has_other_attributes"] += 1
            emphasis[node.get("type") or "(unspecified)"] += 1
            parent = node.getparent()
            emphasis_parent[_local(parent) if parent is not None else "(root)"] += 1
            length = len("".join(node.itertext()))
            label = ("no_visible_text" if length == 0 else
                     "short_1_to_40" if length <= 40 else
                     "medium_41_to_500" if length <= 500 else
                     "long_over_500")
            emphasis_text_size[label] += 1
    return {
        "xml_element_counts": dict(sorted(elements.items())),
        "hi_emphasis_type_counts": dict(sorted(emphasis.items())),
        "hi_direct_parent_counts": dict(sorted(emphasis_parent.items())),
        "hi_visible_length_band_counts": dict(sorted(emphasis_text_size.items())),
        "truly_empty_hi_leaf_shape_counts": dict(sorted(empty_emphasis_shape.items())),
        "nonbreaking_spaces_by_xml_owner": dict(sorted(
            (key, value) for key, value in nbsp_owner.items() if value
        )),
        "markup_profile_is_diagnostic_only": True,
    }


def clean(source: Path, expected_sha: str, *, output: Path | None = None) -> dict:
    """Inspect original; optionally write an independently checked new XML.

    Safe automatic edits are intentionally narrow:
    - collapse internal doubled ASCII spaces in plain leaf <p> text only;
    - trim leading/trailing ASCII spaces in plain leaf <title> text only;
    - remove zero-content, presentation-only <hi> leaves outside notes/refs.
    Text with star symbols, protected descendants or nested markup is not
    rewritten. All source note/reference bodies and attributes remain exact.
    """
    raw = _load(source, expected_sha)
    root = _tree(raw)
    before = _structure(root)
    before_without_inert = _structure(root, skip_inert_hi=True)
    original_exact_text_sha, original_nonspace_sha = _text_hashes(root)
    protected = _protected_text(root)
    original_census, by_owner = _census(root)
    markup_profile = _markup_profile(root)
    changes = Counter()
    candidate = root
    for node in candidate.iter():
        if not isinstance(node.tag, str) or len(node) or node.text is None:
            continue
        local = _local(node)
        if local not in {"p", "title"}:
            continue
        if any(_local(parent) in PROTECTED for parent in node.iterancestors()):
            continue
        text = node.text
        if "*" in text or r"\*" in text:
            continue
        if local == "p":
            revised, n = INTERNAL_SPACES.subn(" ", text)
            if n:
                changes["plain_paragraph_internal_space_runs_collapsed"] += n
        else:
            revised = text.strip(" ")
            if revised != text and revised:
                changes["plain_title_edge_spaces_trimmed"] += len(text) - len(revised)
        if revised != text:
            node.text = revised
            changes["changed_plain_nodes"] += 1

    for node in list(root.iter()):
        if _inert_hi(node):
            _remove_empty_hi(node)
            changes["empty_display_hi_elements_removed"] += 1

    after_exact_text_sha, after_nonspace_sha = _text_hashes(root)
    if (before_without_inert != _structure(root)
            or protected != _protected_text(root)
            or original_nonspace_sha != after_nonspace_sha
            or (not changes.get("changed_plain_nodes")
                and original_exact_text_sha != after_exact_text_sha)):
        raise CleanupError("Cleanup altered protected markup or non-space text")

    result = {
        "status": "PRIVATE_OSIS_COSMETIC_CANDIDATE_NOT_EDITORIALLY_APPROVED",
        "source_sha256": expected_sha,
        "source_bytes": len(raw),
        "source_element_count": len(before),
        "original_suspicious_token_census": original_census,
        "text_character_counts_by_xml_owner": by_owner,
        "original_markup_profile": markup_profile,
        "cleanup_changes": dict(sorted(changes.items())),
        "all_nonempty_osis_elements_and_attributes_preserved": True,
        "only_verified_inert_display_elements_removed": True,
        "all_source_nonspace_text_preserved": True,
        "original_nonspace_text_sha256": original_nonspace_sha,
        "cleaned_nonspace_text_sha256": after_nonspace_sha,
        "all_note_and_reference_text_preserved": True,
        "asterisks_and_potential_note_markers_unmodified": True,
        "text_collated_against_independent_edition": False,
        "permission_to_republish_this_digital_source_verified": False,
        "published": False,
    }
    if output is not None:
        if source.absolute() == output.absolute() or output.is_symlink() or output.exists():
            raise CleanupError("Private cleaned output must be a fresh separate file")
        if not output.parent.is_dir() or output.parent.is_symlink():
            raise CleanupError("Private output parent must already exist")
        if changes:
            xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
            rebuilt = _tree(xml)
            serialized_exact, serialized_nonspace = _text_hashes(rebuilt)
            if (before_without_inert != _structure(rebuilt)
                    or protected != _protected_text(rebuilt)
                    or serialized_nonspace != original_nonspace_sha
                    or serialized_exact != after_exact_text_sha):
                raise CleanupError("Serialized candidate changed source text or protected markup")
        else:
            xml = raw
        output.write_bytes(xml)
        result["cleaned_sha256"] = sha256(xml).hexdigest()
        result["cleaned_bytes"] = len(xml)
        result["cleaned_file_written_privately"] = True
    else:
        result["cleaned_file_written_privately"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--private-output", type=Path)
    arguments = parser.parse_args()
    result = clean(arguments.source, arguments.sha256,
                   output=arguments.private_output)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
