#!/usr/bin/env python3
"""Research-only exact original commentary paragraph vs independent USFM title audit.

Reads only SHA-pinned independent USFM and original source-bound metadata.
Exports no commentary text, biblical title words, XML or native SWORD content.
A lexical match is not authorial, edition, rights or publication approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

WORD = re.compile(r"\w+", re.UNICODE)
PIN = re.compile(r"[a-f0-9]{64}\Z")
BOOK = re.compile(r"[A-Z0-9]{3}\Z")
CHAPTER = re.compile(r"\\c\s+(\d+)\s*")
TITLE = re.compile(r"\\d\s+(.+?)\s*")
ID = re.compile(r"\\id\s+([A-Z0-9]{3})(?:\s|$)")
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_MEMBER_BYTES = 4 * 1024 * 1024


class WitnessError(ValueError):
    pass


def independent_usfm_titles(archive: Path, pinned_sha256: str,
                            *, book_id: str) -> dict[int, dict]:
    """Strict zip, original USFM marker and text identity validation, in memory."""
    if not isinstance(pinned_sha256, str) or not PIN.fullmatch(pinned_sha256):
        raise WitnessError("An independently observed SHA-256 pin is mandatory")
    if not BOOK.fullmatch(book_id):
        raise WitnessError("Unreviewed USFM book identifier")
    if (archive.is_symlink() or not archive.is_file()
            or not 0 < archive.stat().st_size <= MAX_ARCHIVE_BYTES):
        raise WitnessError("Missing, symlinked, empty or oversized independent source")
    if sha256(archive.read_bytes()).hexdigest() != pinned_sha256:
        raise WitnessError("Independent original USFM archive SHA-256 changed")
    matches = []
    try:
        with ZipFile(archive) as source:
            members = source.infolist()
            if not 1 <= len(members) <= 150:
                raise WitnessError("Unbounded original USFM archive inventory")
            for member in members:
                name = member.filename
                if member.is_dir() or not name.lower().endswith((".sfm", ".usfm")):
                    continue
                if (name.startswith("/") or "\\" in name or ".." in Path(name).parts
                        or member.file_size > MAX_MEMBER_BYTES
                        or member.compress_size > MAX_ARCHIVE_BYTES):
                    raise WitnessError("Unsafe original USFM member path or size")
                raw = source.read(member)
                if len(raw) != member.file_size or b"\x00" in raw:
                    raise WitnessError("Invalid original USFM member contents")
                text = raw.decode("utf-8-sig")
                identifiers = [
                    mark.group(1) for line in text.splitlines()
                    if (mark := ID.match(line.strip()))
                ]
                if identifiers == [book_id]:
                    matches.append(text)
    except (BadZipFile, UnicodeError) as exc:
        raise WitnessError("Unreviewed original USFM ZIP/UTF-8") from exc
    if len(matches) != 1:
        raise WitnessError("Original USFM book not uniquely identified")
    result = {}
    current = None
    seen = set()
    in_verse = False
    for raw in matches[0].splitlines():
        line = raw.strip()
        if line.startswith("\\c "):
            ch = CHAPTER.fullmatch(line)
            if not ch:
                raise WitnessError("Original USFM chapter has unreviewed syntax")
            current = int(ch.group(1))
            if not 1 <= current <= 200 or current in seen:
                raise WitnessError("Duplicate or out-of-bounds original USFM chapter")
            seen.add(current)
            in_verse = False
        elif line.startswith("\\v "):
            in_verse = True
        elif line.startswith("\\d "):
            found = TITLE.fullmatch(line)
            if current is None or in_verse or current in result or not found:
                raise WitnessError("Unreviewed, duplicated or misplaced original title")
            title = found.group(1)
            if "\\" in title or len(title) > 1024:
                result[current] = {"status": "unreviewed_inline_usfm_title_markup"}
                continue
            tokens = WORD.findall(title)
            if not 1 <= len(tokens) <= 100:
                raise WitnessError("Unbounded original biblical title")
            result[current] = {
                "status": "plain_original_d_title",
                "word_count": len(tokens),
                "exact_unicode_word_sha256":
                    sha256(" ".join(tokens).encode("utf-8")).hexdigest(),
            }
    if not seen or not result:
        raise WitnessError("Independent original USFM has no chapter/title inventory")
    return result


def compare_original_first_paragraphs(safe_receipt: dict, titles: dict[int, dict],
                                      *, source_book: str) -> dict:
    """Compare SHA-only exact source paragraph #1, never disclose source words."""
    if not re.fullmatch(r"[1-4]?[A-Za-z][A-Za-z0-9]{1,15}", source_book):
        raise WitnessError("Unsafe original commentary book code")
    if safe_receipt.get("original_source_words_or_binaries_exported") is not False:
        raise WitnessError("Full source or native text receipt is not export-safe")
    scope = safe_receipt.get(
        "source_longer_both_source_and_native_reference_label_word_scope")
    if (not isinstance(scope, dict) or scope.get(
            "excluded_only_original_scripRef_and_real_native_reference_labels") is not True):
        raise WitnessError("Missing two-sided genuine scripture-label provenance")
    rows = scope.get("source_extra_original_p_digest_source_line_sha_only_rows")
    expected_by_book = scope.get(
        "original_book_source_extra_original_p_digest_case_classes", {}).get(source_book)
    expected = (expected_by_book.get(
        "at_least_one_unique_entire_original_p_visible_word_match")
        if isinstance(expected_by_book, dict) else None)
    if not isinstance(rows, list) or len(rows) > 200 or type(expected) is not int:
        raise WitnessError("Source-extra paragraph census not authenticated")
    cases = []
    chapters = set()
    for row in rows:
        if row.get("original_book") != source_book or row.get(
                "source_extra_p_digest_case_class") != (
                "at_least_one_unique_entire_original_p_visible_word_match"):
            continue
        units = row.get("all_extra_gap_full_original_p_digest_candidate_classes")
        if not isinstance(units, list):
            raise WitnessError("Original whole-paragraph witness unavailable")
        matched = [
            u for u in units if u.get("single_matching_original_p_document_ordinal") == 1
            and u.get("distinct_full_original_p_exact_visible_word_matches") == 1
        ]
        if len(matched) != 1:
            raise WitnessError("Original source opening paragraph cannot be uniquely matched")
        paragraph = matched[0]
        chapter = row.get("original_source_chapter_number_from_actual_osis_start")
        orig_sha = row.get("original_full_reference_sha256")
        p_sha = paragraph.get("single_matching_original_p_exact_unicode_word_sha256")
        size = paragraph.get("original_extra_unlinked_word_count")
        if (type(chapter) is not int or not 1 <= chapter <= 200 or chapter in chapters
                or not isinstance(orig_sha, str) or not PIN.fullmatch(orig_sha)
                or not isinstance(p_sha, str) or not PIN.fullmatch(p_sha)
                or type(size) is not int or not 1 <= size <= 100):
            raise WitnessError("Source chapter/reference/paragraph SHA or count is invalid")
        chapters.add(chapter)
        title = titles.get(chapter)
        if title is None:
            verdict = "no_independent_usfm_d_title_for_original_chapter"
            title_size = None
        elif title["status"] == "unreviewed_inline_usfm_title_markup":
            verdict = "unreviewed_inline_usfm_d_title"
            title_size = None
        else:
            title_size = title["word_count"]
            if size != title_size:
                verdict = "source_p1_and_usfm_d_title_word_counts_differ"
            elif p_sha != title["exact_unicode_word_sha256"]:
                verdict = "same_word_count_but_different_case_sensitive_unicode_tokens"
            else:
                verdict = "exact_original_p1_equals_independent_usfm_d_title_word_tokens"
        cases.append({
            "original_chapter_from_pinned_source_reference": chapter,
            "original_source_full_reference_sha256": orig_sha,
            "original_source_first_p_word_count": size,
            "independent_usfm_d_title_word_count": title_size,
            "verdict": verdict,
        })
    if not cases or len(cases) != expected:
        raise WitnessError("Original source-book complete paragraph-case census changed")
    classes = Counter(c["verdict"] for c in cases)
    return {
        "status": "PINNED_INDEPENDENT_USFM_TITLE_AND_ORIGINAL_FIRST_P_TOKEN_PARITY_ONLY",
        "source_book": source_book,
        "original_first_paragraph_cases_checked": len(cases),
        "independent_usfm_d_titles_in_source_book": len(titles),
        "exact_original_title_case_classes": dict(sorted(classes.items())),
        "original_chapter_source_sha_and_closed_verdict_only":
            sorted(cases, key=lambda c: c["original_chapter_from_pinned_source_reference"]),
        "source_or_bible_text_or_native_verse_keys_exported": False,
        "matching_title_not_original_authorial_edition_or_redistribution_approval": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-safe-receipt", type=Path, required=True)
    parser.add_argument("--usfm-zip", type=Path, required=True)
    parser.add_argument("--usfm-archive-sha256", required=True)
    parser.add_argument("--usfm-book-id", required=True)
    parser.add_argument("--source-book", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    titles = independent_usfm_titles(
        args.usfm_zip, args.usfm_archive_sha256, book_id=args.usfm_book_id)
    receipt = json.loads(args.source_safe_receipt.read_text(encoding="utf-8"))
    result = compare_original_first_paragraphs(
        receipt, titles, source_book=args.source_book)
    args.report.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        key: value for key, value in result.items()
        if key != "original_chapter_source_sha_and_closed_verdict_only"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
