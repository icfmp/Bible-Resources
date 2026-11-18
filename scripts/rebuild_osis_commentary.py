#!/usr/bin/env python3
"""Recompile pinned, original OSIS commentary as private native SWORD.

Phase 1 ONLY: compile the supplied OSIS bytes without editorial corrections,
then independently enumerate every occupied native commentary entry. No
comparison with historical/alternate editions, rights approval or publication.
All input, compiler logs and output stay in caller-provided private storage.
Generic across languages, providers and commentary titles.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from xml.parsers import expat

from sword_native_raw_corpus_inventory import parse_native_raw_corpus

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,63}\Z")
LANGUAGE = re.compile(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*\Z")
VERSIFICATION = re.compile(r"[A-Za-z][A-Za-z0-9]{1,31}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_SOURCE = 200 * 1024 * 1024
MAX_MARKUP = 1500000


class RebuildFailure(ValueError):
    pass


def source_census(source: Path, expected_sha: str) -> dict:
    """Prove source identity and parse OSIS without DTD/external entities.

    Count all markup events; never export original prose, references or notes.
    """
    if (source.is_symlink() or not source.is_file()
            or not DIGEST.fullmatch(expected_sha)
            or not 100 <= source.stat().st_size <= MAX_SOURCE):
        raise RebuildFailure("Missing, unpinned or oversized original OSIS source")
    digest = sha256()
    parser = expat.ParserCreate(namespace_separator="}")
    counts = Counter()
    root = []
    depth = [0]
    lang = [None]

    def begin(tag, attrs):
        depth[0] += 1
        name = tag.rsplit("}", 1)[-1]
        counts[name] += 1
        if sum(counts.values()) > MAX_MARKUP:
            raise RebuildFailure("Excessive source markup events")
        if depth[0] == 1:
            root.append(name)
        if name == "osisText":
            lang[0] = attrs.get("http://www.w3.org/XML/1998/namespace}lang")

    def end(_tag):
        depth[0] -= 1

    def forbidden(*_args):
        raise RebuildFailure("DTD or entity declarations are not permitted")

    parser.StartElementHandler = begin
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = forbidden
    parser.EntityDeclHandler = forbidden
    parser.ExternalEntityRefHandler = lambda *_args: 0
    with source.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            parser.Parse(chunk, False)
        parser.Parse(b"", True)
    if (digest.hexdigest() != expected_sha or root != ["osis"]
            or counts["osisText"] != 1 or counts["div"] == 0
            or depth[0] != 0):
        raise RebuildFailure("Source hash or complete OSIS structure invalid")
    return {
        "source_sha256": expected_sha,
        "source_bytes": source.stat().st_size,
        "source_language_declared": lang[0],
        "osis_div_elements": counts["div"],
        "osis_sections_annotated": counts["div"],
        "osis_reference_elements": counts["reference"],
        "osis_note_elements": counts["note"],
        "osis_title_elements": counts["title"],
        "all_source_prose_retained_as_original_input": True,
    }


def build(source: Path, expected_sha: str, work: Path, *,
          module: str, lang: str, versification: str,
          native_reader: Path, compiler: str = "osis2mod",
          minimum_numbered_entries: int = 1) -> dict:
    if (not IDENTIFIER.fullmatch(module) or not LANGUAGE.fullmatch(lang)
            or not VERSIFICATION.fullmatch(versification)
            or not isinstance(minimum_numbered_entries, int)
            or minimum_numbered_entries < 1):
        raise RebuildFailure("Invalid module, language or versification configuration")
    if work.exists() or work.is_symlink():
        raise RebuildFailure("Refuse to overwrite an existing private SWORD directory")
    if not native_reader.is_file() or native_reader.is_symlink():
        raise RebuildFailure("Missing independent compiled native reader")
    exe = shutil.which(compiler)
    if not exe:
        raise RebuildFailure("Standard OSIS compiler not installed")
    observed = source_census(source, expected_sha)
    if observed["source_language_declared"] not in (None, lang):
        raise RebuildFailure("Source XML language differs from configured edition")
    work.mkdir(parents=True, mode=0o700)
    name = module.lower()
    data = work / "modules" / "comments" / "zcom4" / name
    data.mkdir(parents=True)
    conf = work / "mods.d" / (name + ".conf")
    conf.parent.mkdir()
    conf.write_text(
        "[" + module + "]\n"
        + "DataPath=./modules/comments/zcom4/" + name + "\n"
        + "ModDrv=zCom4\nBlockType=CHAPTER\nCompressType=ZIP\n"
        + "Encoding=UTF-8\nSourceType=OSIS\n"
        + "Lang=" + lang + "\nVersification=" + versification + "\n"
        + "Version=0.0.0-research\n"
        + "Description=Private unapproved original-source technical reconstruction\n",
        encoding="utf-8",
    )
    # -C commentary; -s 4 for zCom4; -N disables silent UTF-8 NFC editing.
    # Original source is read-only. Never execute upstream build scripts.
    command = [
        exe, str(data), str(source), "-C", "-z", "z", "-s", "4",
        "-b", "3", "-v", versification, "-N"
    ]
    with (work / "compiler-private.log").open("xb") as logfile:
        try:
            result = subprocess.run(command, stdout=logfile, stderr=logfile,
                                    timeout=480, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RebuildFailure("SWORD OSIS compilation unavailable or timed out") from exc
    if result.returncode:
        raise RebuildFailure("SWORD compiler failed; private log retained locally")
    files = sorted(p for p in data.rglob("*") if p.is_file())
    if not files:
        raise RebuildFailure("Compiler produced no SWORD data")
    # Read *every* occupied native entry, not merely one diatheke sample.
    env = dict(os.environ, SWORD_PATH=str(work.resolve(strict=True)))
    try:
        scan = subprocess.Popen(
            [str(native_reader.resolve(strict=True)), module],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise RebuildFailure("Cannot launch independent native reader") from exc
    try:
        assert scan.stdout is not None
        observed_native, _keys, _intro, _opaque = parse_native_raw_corpus(scan.stdout)
        if scan.wait(timeout=25) != 0:
            raise RebuildFailure("Independent native readback terminated abnormally")
    finally:
        if scan.stdout:
            scan.stdout.close()
        if scan.poll() is None:
            scan.kill()
        scan.wait()
    counts = observed_native["actual_occupied_numbered_entry_count"], \
             observed_native["actual_occupied_intro_entry_count"], \
             observed_native["actual_occupied_anonymous_top_entry_count"]
    if counts[0] < minimum_numbered_entries:
        raise RebuildFailure("Compiled module has insufficient native commentary content")
    return {
        "stage": "1_technical_reconstruction",
        "status": "COMPILED_AND_FULL_NATIVE_INDEX_READBACK_ONLY",
        "source": observed,
        "candidate_module": module,
        "candidate_language": lang,
        "candidate_versification": versification,
        "candidate_driver": "zCom4",
        "native_occupied_numbered_keys": counts[0],
        "native_occupied_introduction_keys": counts[1],
        "native_occupied_opaque_top_keys": counts[2],
        "compiled_member_sha256": {
            str(p.relative_to(work)): sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "editorial_text_changes_performed": False,
        "historical_edition_text_comparison_performed": False,
        "complete_source_to_compiled_content_parity_proven": False,
        "rights_and_redistribution_approved": False,
        "publication_or_release_performed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--private-work", required=True, type=Path)
    parser.add_argument("--module", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--versification", required=True)
    parser.add_argument("--native-reader", required=True, type=Path)
    parser.add_argument("--min-numbered", type=int, default=1)
    args = parser.parse_args()
    result = build(args.source, args.sha256, args.private_work,
                   module=args.module, lang=args.language,
                   versification=args.versification,
                   native_reader=args.native_reader,
                   minimum_numbered_entries=args.min_numbered)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
