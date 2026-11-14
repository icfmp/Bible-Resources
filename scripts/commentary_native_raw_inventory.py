#!/usr/bin/env python3
"""Read every exact unfiltered occupied stock SWORD commentary entry privately.

Generic RawCom/zCom companion to the Bible native raw-corpus guard.  Never
rebuilds or rewrites the module, normalizes text, or publishes a commentary.
A full corpus SHA/occupancy audit is NOT a source-to-compiled fidelity proof.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

from commentary_intake import load_manifest
from commentary_native_inventory import parse_index
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import RawCorpusError, parse_native_raw_corpus

MAX_KEY_REPORT = 20
MAX_TOTAL_SECONDS = 360



# These tags are observations of unchanged stock XML, not a canonical content
# schema. Unknown element names are counted without exposing source strings.
MARKUP_TAGS = ("p", "div", "title", "table", "row", "cell", "reference",
               "note", "hi", "q", "quote", "list", "item", "lb", "br",
               "milestone", "seg", "verse", "chapter")
MAX_RAW_MARKUP_BYTES = 2 * 1024 * 1024

# Observational *forms*, not a full OSIS reference validator or verse-key
# existence test. Keep literal source attributes private and untouched.
_OSIS_BOOK = r"[1-4]?[A-Za-z][A-Za-z0-9]*"
_OSIS_CHAPTER = rf"{_OSIS_BOOK}\.[1-9][0-9]{{0,2}}"
_OSIS_VERSE = rf"{_OSIS_CHAPTER}\.[1-9][0-9]{{0,2}}"
_REFERENCE_FORMS = (
    "single_osis_verse",
    "verse_range_like",
    "book_or_chapter_like",
    "compound_target",
    "other_unclassified",
)


def original_osisref_form(value: str) -> str:
    """Classify the *original* target shape without normalizing or guessing.

    A recognized shape is NOT a valid existence-checked verse. Unrecognized
    forms could be valid OSIS extensions or authorial markup; never call them
    errors or rewrite them merely because the classifier lacks grammar.
    """
    if not isinstance(value, str) or not value:
        raise PilotError("Original source reference target is absent")
    candidate = value[len("Bible:"):] if value.startswith("Bible:") else value
    if re.fullmatch(_OSIS_VERSE, candidate):
        return "single_osis_verse"
    if "-" in candidate:
        parts = candidate.split("-", 1)
        if (len(parts) == 2 and re.fullmatch(_OSIS_VERSE, parts[0])
                and (re.fullmatch(_OSIS_VERSE, parts[1])
                     or re.fullmatch(r"[1-9][0-9]{0,2}", parts[1]))):
            return "verse_range_like"
    if re.fullmatch(_OSIS_BOOK, candidate) or re.fullmatch(_OSIS_CHAPTER, candidate):
        return "book_or_chapter_like"
    if any(ch in candidate for ch in (",", " ", ";", "\\t")):
        return "compound_target"
    return "other_unclassified"




class NativeCommentaryMarkupCensus:
    """Inventory source-native markup on the complete original SWORD stream.

    Every populated K/I payload is parsed as a strict XML fragment in a
    synthetic root. Unknown or malformed XML is *classified*, never repaired.
    Opaque TOP metadata is not presumed to be XML. Reports contain only
    fixed category names, aggregate counts and boolean scope flags, never
    raw text, original attributes, literal reference targets or key names.
    """

    def __init__(self) -> None:
        self.entries_observed = 0
        self.opaque_top_entries = 0
        self.empty_nonopaque_entries = 0
        self.valid_nonopaque_entries = 0
        self.invalid_nonopaque_entries = 0
        self.excessive_nonopaque_entries = 0
        self.entries_with_titles = 0
        self.entries_with_paragraphs = 0
        self.entries_with_tables = 0
        self.entries_with_references = 0
        self.entries_with_notes = 0
        self.refs_with_osisref = 0
        self.refs_without_osisref = 0
        self.reference_forms = Counter()
        self.literal_bible_work_qualified = 0
        self.reference_label_with_visible_text = 0
        self.reference_label_without_visible_text = 0
        self.title_with_visible_text = 0
        self.title_without_visible_text = 0
        self.elements = Counter()

    def observe(self, kind: str, key: str, raw: bytes) -> None:
        """Read one original record only; keep neither keys nor source words."""
        if kind not in ("K", "I", "U") or not isinstance(key, str) or not isinstance(raw, bytes):
            raise PilotError("Unreviewed native commentary markup frame")
        self.entries_observed += 1
        if kind == "U":
            self.opaque_top_entries += 1
            return
        if not raw.strip():
            self.empty_nonopaque_entries += 1
            return
        if len(raw) > MAX_RAW_MARKUP_BYTES or b"\x00" in raw:
            self.excessive_nonopaque_entries += 1
            return
        try:
            root = etree.fromstring(
                b"<stock>" + raw + b"</stock>",
                parser=etree.XMLParser(
                    resolve_entities=False, no_network=True,
                    load_dtd=False, recover=False, huge_tree=False,
                    remove_blank_text=False,
                ),
            )
            if any(isinstance(node, etree._Entity) for node in root.iter()):
                self.invalid_nonopaque_entries += 1
                return
        except (ValueError, etree.XMLSyntaxError):
            self.invalid_nonopaque_entries += 1
            return
        self.valid_nonopaque_entries += 1
        observed = Counter()
        for node in root.iter():
            if node is root or not isinstance(node.tag, str):
                continue
            local_name = node.tag.rsplit("}", 1)[-1]
            category = local_name if local_name in MARKUP_TAGS else "other"
            observed[category] += 1
            if local_name == "title":
                if "".join(node.itertext()).strip():
                    self.title_with_visible_text += 1
                else:
                    self.title_without_visible_text += 1
            if local_name == "reference":
                # Count only *literal* original OSIS attributes, never link
                # destinations inferred from a nearby key or display label.
                original_target = node.get("osisRef")
                if original_target:
                    self.refs_with_osisref += 1
                    self.reference_forms[original_osisref_form(original_target)] += 1
                    self.literal_bible_work_qualified += original_target.startswith("Bible:")
                else:
                    self.refs_without_osisref += 1
                if "".join(node.itertext()).strip():
                    self.reference_label_with_visible_text += 1
                else:
                    self.reference_label_without_visible_text += 1
        self.elements.update(observed)
        self.entries_with_titles += bool(observed["title"])
        self.entries_with_paragraphs += bool(observed["p"])
        self.entries_with_tables += bool(observed["table"])
        self.entries_with_references += bool(observed["reference"])
        self.entries_with_notes += bool(observed["note"])

    def report(self, expected_entries: int) -> dict:
        """Reconcile every source frame without making text/GUI claims."""
        if (type(expected_entries) is not int or expected_entries < 0
                or self.entries_observed != expected_entries
                or self.entries_observed != (
                    self.opaque_top_entries + self.empty_nonopaque_entries
                    + self.valid_nonopaque_entries + self.invalid_nonopaque_entries
                    + self.excessive_nonopaque_entries
                )
                or sum(self.reference_forms.values()) != self.refs_with_osisref
                or self.reference_label_with_visible_text
                   + self.reference_label_without_visible_text
                   != self.elements["reference"]
                or self.title_with_visible_text + self.title_without_visible_text
                   != self.elements["title"]):
            raise PilotError("Unreconciled complete original commentary XML observations")
        return {
            "all_original_native_entries_accounted_for": True,
            "raw_entries_observed": self.entries_observed,
            "opaque_top_entries_not_assumed_to_be_xml": self.opaque_top_entries,
            "empty_numbered_or_intro_entries": self.empty_nonopaque_entries,
            "strict_xml_parseable_numbered_or_intro_entries": self.valid_nonopaque_entries,
            "unparseable_numbered_or_intro_entries": self.invalid_nonopaque_entries,
            "oversized_or_binary_numbered_or_intro_entries": self.excessive_nonopaque_entries,
            "entries_with_title_markup": self.entries_with_titles,
            "entries_with_paragraph_markup": self.entries_with_paragraphs,
            "entries_with_table_markup": self.entries_with_tables,
            "entries_with_reference_markup": self.entries_with_references,
            "entries_with_note_markup": self.entries_with_notes,
            "reference_elements_with_osisref_attribute": self.refs_with_osisref,
            "reference_elements_without_osisref_attribute": self.refs_without_osisref,
            "original_osisref_form_count_by_fixed_category": {
                name: self.reference_forms[name] for name in _REFERENCE_FORMS
            },
            "original_reference_elements_with_literal_Bible_work_prefix":
                self.literal_bible_work_qualified,
            "original_reference_labels_with_visible_text":
                self.reference_label_with_visible_text,
            "original_reference_labels_without_visible_text":
                self.reference_label_without_visible_text,
            "original_title_elements_with_visible_text":
                self.title_with_visible_text,
            "original_title_elements_without_visible_text":
                self.title_without_visible_text,
            "no_osisref_value_normalization_or_verse_existence_claim": True,
            "original_element_counts_by_fixed_category": {
                name: self.elements[name] for name in (*MARKUP_TAGS, "other")
            },
            "no_original_words_keys_or_reference_values_reported": True,
            "no_original_source_bytes_rewritten": True,
            "source_to_other_digital_edition_parity_proven": False,
            "real_reader_layout_or_click_navigation_proven": False,
        }


def _safe_stock_install(zip_path: Path, records: list[dict], root: Path) -> None:
    """Install the independently preflighted original in disposable storage."""
    root.mkdir()
    with zipfile.ZipFile(zip_path) as archive:
        for member in records:
            name = member["name"]
            target = root / PurePosixPath(name)
            if not target.resolve().is_relative_to(root.resolve()):
                raise PilotError("Untrusted original SWORD archive member path")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not name.endswith("/"):
                with archive.open(name) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=256 * 1024)


def private_crosscheck(index: bytes, module_id: str, content_rows: list[tuple[str,str]],
                       raw_stats: dict) -> dict:
    """A second native tool must independently agree on every occupied slot."""
    index_report = parse_index(index, module_id)
    try:
        rows = [tuple(line.split("\t")) for line in index.decode("ascii").splitlines()[1:-1]]
    except UnicodeError:
        raise PilotError("Native occupied keys are not verified ASCII") from None
    if any(len(row)!=2 for row in rows) or rows!=content_rows:
        raise PilotError("Full raw-entry stream diverged from independently enumerated stock SWORD keys")
    if (raw_stats["actual_occupied_numbered_entry_count"] != index_report["occupied_numbered_slots"]
        or raw_stats["actual_occupied_intro_entry_count"] != index_report["occupied_intro_slots"]
        or raw_stats["actual_occupied_anonymous_top_entry_count"] != index_report["occupied_anonymous_top_slots"]):
        raise PilotError("Native raw content stream counts disagree with complete independent index")
    return {
        "native_key_order_sha256": index_report["ordered_occupied_key_sha256"],
        "native_engine_version": index_report["libsword_version"],
        "native_versification": index_report["native_versification"],
        "native_driver": index_report["driver"],
        "exact_all_occupied_stock_keys_read_and_crosschecked": True,
        "all_stock_occupied_keys_count": len(rows),
    }


def inspect_raw_content(resource_id: str, *, index_binary: Path, raw_binary: Path,
                        directory: Path | None = None) -> dict:
    manifest = load_manifest(resource_id, directory)
    expected_sha = manifest.get("archive_sha256")
    if not expected_sha:
        raise PilotError("Official SWORD original must be SHA-pinned")
    if any(not path.is_file() or path.is_symlink() for path in (index_binary, raw_binary)):
        raise PilotError("Trusted native index and raw-frame binaries required")
    with tempfile.TemporaryDirectory(prefix="commentary-stock-full-raw-") as temp:
        root = Path(temp)
        original = root/"stock.zip"
        download = fetch(manifest["sword_zip_url"], original, manifest["provider"])
        if download["sha256"]!=expected_sha:
            raise PilotError("Upstream stock SWORD commentary archive changed; abort")
        archive=inspect_archive(original,source_kind="sword",
                                expected_module_id=manifest["module_id"],
                                expected_category="commentary")
        conf=archive["sword_conf"]
        if conf["version"]!=manifest["version"] or conf["language"]!=manifest["language"]:
            raise PilotError("Stock module identity changed")
        installed=root/"installed"
        _safe_stock_install(original,archive["members"],installed)
        env=dict(os.environ,SWORD_PATH=str(installed))
        try:
            key_probe=subprocess.run([str(index_binary),manifest["module_id"]],
                                    capture_output=True,timeout=60,env=env,check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Independent commentary index timed out") from None
        if key_probe.returncode or len(key_probe.stdout)>12*1024*1024:
            raise PilotError("Independent commentary index failed or exceeded output bounds")
        # The original source text leaves the subprocess ONLY via this private
        # pipe, never through a shell step, job log or public artifact.
        command=["timeout",f"{MAX_TOTAL_SECONDS}s",str(raw_binary),manifest["module_id"]]
        process=None
        ordered_rows=[]
        raw_sha_count=Counter()
        zero_length_count=0
        whitespace_only_count=0
        per_book=defaultdict(lambda: {"entries":0,"raw_bytes":0,"nonempty_raw_entries":0})
        markup = NativeCommentaryMarkupCensus()
        try:
            process=subprocess.Popen(command,stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL,env=env)
            if process.stdout is None:
                raise PilotError("Cannot privately receive SWORD raw-entry stream")
            def examine(kind: str, ref: str, content: bytes) -> None:
                nonlocal zero_length_count, whitespace_only_count
                ordered_rows.append((kind,ref))
                markup.observe(kind,ref,content)
                raw_sha_count[sha256(content).hexdigest()]+=1
                if not content:
                    zero_length_count+=1
                if not content.strip():
                    whitespace_only_count+=1
                name=ref.split(".",1)[0] if kind!="U" else "_OPAQUE_TOP"
                stats=per_book[name]
                stats["entries"]+=1
                stats["raw_bytes"]+=len(content)
                if content.strip():
                    stats["nonempty_raw_entries"]+=1
            raw, keys, intros, top=parse_native_raw_corpus(process.stdout,on_entry=examine)
            process.stdout.close()
            result_code=process.wait(timeout=15)
            if result_code!=0:
                raise PilotError("Native commentary raw reader stopped before complete corpus terminator")
        except BaseException:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            raise
        proof=private_crosscheck(key_probe.stdout, manifest["module_id"],ordered_rows,raw)
        if proof["native_driver"]!=conf["driver"] or proof["native_versification"]!=(conf["versification"] or "KJV"):
            raise PilotError("Real SWORD driver or versification differs from pinned source metadata")
        duplicates=sum(count-1 for count in raw_sha_count.values() if count>1)
        return {
            "schema_version":1,
            "status":"all_stock_native_raw_commentary_entries_hashed_not_authorial_parity",
            "resource_id":resource_id,
            "stock_sword_original_sha256":download["sha256"],
            "stock_sword_conf_sha256":conf["conf_sha256"],
            "native_raw_corpus_ordered_sha256":raw["all_native_raw_entries_ordered_sha256"],
            "total_native_raw_entry_bytes":raw["actual_native_unfiltered_raw_bytes_total"],
            "raw_entry_count":raw["all_actual_raw_entries_scanned"],
            "raw_numbered_slots":raw["actual_occupied_numbered_entry_count"],
            "raw_introduction_slots":raw["actual_occupied_intro_entry_count"],
            "raw_opaque_top_slots":raw["actual_occupied_anonymous_top_entry_count"],
            "zero_length_native_raw_entries":zero_length_count,
            "raw_entries_with_only_whitespace":whitespace_only_count,
            "number_of_identical_raw_hash_extra_occurrences":duplicates,
            "by_book_or_special":{
                key:per_book[key] for key in sorted(per_book)
            },
            "native_correspondence":proof,
            "original_stock_markup_census": markup.report(raw["all_actual_raw_entries_scanned"]),
            "source_scripCom_references_compared":False,
            "source_text_punctuation_semantics_compared":False,
            "source_and_stock_paragraph_order_compared":False,
            "source_and_stock_note_bodies_compared":False,
            "edition_equivalence_approved":False,
            "rights_review_approved":False,
            "reader_GUI_testing_completed":False,
            "published":False,
            "original_text_disclosed":False,
            "original_bytes_changed":False,
        }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id",required=True)
    p.add_argument("--native-index-binary",required=True,type=Path)
    p.add_argument("--native-raw-binary",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        result=inspect_raw_content(a.resource_id,index_binary=a.native_index_binary,
                                    raw_binary=a.native_raw_binary)
        code=0
    except (ValueError,OSError,RuntimeError,zipfile.BadZipFile,RawCorpusError) as exc:
        result={"status":"blocked","resource_id":a.resource_id,"reason":str(exc),
                "published":False,"source_text_punctuation_semantics_compared":False}
        code=1
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Read-only commentary stock raw corpus: "+result["status"]+" (text never logged)")
    return code


if __name__=="__main__":
    raise SystemExit(main())
