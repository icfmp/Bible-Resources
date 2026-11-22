#!/usr/bin/env python3
"""Package and verify PRIVATE, immutable, source-pinned BSI work snapshots.

A successful build is NOT a public release or a semantic editorial approval.
Never upload these archives to the public Bible-Resources repository.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

SCHEMA = "bsi.private-working-snapshot.v1"
REVISION = re.compile(r"^[0-9a-f]{40}$")
SOURCE_LOCKS = {
    "entity": {
        "acai": "e80a874e8282f996199c595378a3b3b9a43aac22",
        "macula_wlc": "47db250bd55d0d8577f2a94fba114ef16c35b23c",
        "macula_sblgnt": "8423afe47b9e8f24b7772e808af45c7159a6fe7e",
    },
    "ubs-greek": {
        "ubs_dictionary": "a15a96cfaa4ca18a6c0339016645ba1e534db3c8",
        "macula_sblgnt": "8423afe47b9e8f24b7772e808af45c7159a6fe7e",
    },
    "ubs-hebrew": {
        "ubs_dictionary": "a15a96cfaa4ca18a6c0339016645ba1e534db3c8",
        "macula_wlc": "47db250bd55d0d8577f2a94fba114ef16c35b23c",
    },
}
# The explicitly selected COMPLETE internal states; the public releases
# contain strictly narrower projections. No arbitrary file upload allowed.
REQUIRED = {
    "entity": {"complete-entity-index.json", "public-projection.json", "public-labels-en.json"},
    "ubs-greek": {"complete-word-review-index.json", "context-review-batches.json"},
    "ubs-hebrew": {"reviewed-lexical-candidate.json", "semantic-feasibility-audit.json",
                   "contextual-pilot-witnesses.json"},
}
MAX_FILE = 300 * 1024 * 1024
MAX_ARCHIVE = 600 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def archive_name(kind: str, source_commit: str) -> str:
    if kind not in REQUIRED or not REVISION.fullmatch(source_commit):
        raise ValueError("Unknown resource kind or noncanonical immutable Git commit")
    return f"bsi-work-{kind}-{source_commit}.tar.gz"


def parse_files(values: list[str], kind: str) -> dict[str, Path]:
    files = {}
    for item in values:
        name, sep, raw = item.partition("=")
        if not sep or name not in REQUIRED[kind] or name in files or not raw:
            raise ValueError("Expected unique, explicitly allowlisted NAME=PATH")
        files[name] = Path(raw)
    if set(files) != REQUIRED[kind]:
        raise ValueError("Incomplete private working state: " + repr(sorted(REQUIRED[kind] - set(files))))
    return files


def inspect_source_state(kind: str, name: str, data: bytes) -> None:
    try:
        obj = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Non-JSON or malformed internal {name}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"Expected top-level object for {name}")
    if kind == "entity" and name == "complete-entity-index.json":
        if obj.get("format") != "bible-entity-index" or obj.get("schema_version") != 1:
            raise ValueError("Not original-data audited BSI entity index")
        if not isinstance(obj.get("entities"), list) or not isinstance(obj.get("by_word"), dict):
            raise ValueError("Incomplete BSI entity index")
    if kind == "ubs-greek" and name == "complete-word-review-index.json":
        if (obj.get("original_word_ids") != 137741
                or obj.get("provisional_semantic_word_ids") != 123195
                or len(obj.get("by_original_macula_word_id", {})) != 137741
                or obj.get("publication_approved") is not False):
            raise ValueError("Not the exact source-checked private Greek full index")
    if kind == "ubs-hebrew" and name == "semantic-feasibility-audit.json":
        if (obj.get("candidate_word_count") != 53981
                or obj.get("independently_contextually_validated") != 0
                or obj.get("publication_approved") is not False):
            raise ValueError("Not the private unapproved Hebrew feasibility census")
    if kind == "ubs-hebrew" and name == "contextual-pilot-witnesses.json":
        if (obj.get("sample_words") != 72
                or obj.get("candidate_lexids_approved") != 0
                or obj.get("publication_approved") is not False):
            raise ValueError("Not the 72-word private Hebrew contextual witness set")


def pack(kind: str, source_commit: str, files: dict[str, Path], output: Path) -> dict:
    expected_name = archive_name(kind, source_commit)
    if output.name != expected_name:
        raise ValueError("Snapshot filename must encode the full exact source commit")
    if set(files) != REQUIRED[kind]:
        raise ValueError("Refusing incomplete internal working state")
    blobs = {}
    for name in sorted(files):
        path = files[name]
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE:
            raise ValueError(f"Unsafe/missing/oversized source file: {name}")
        data = path.read_bytes()
        if len(data) > MAX_FILE:
            raise ValueError(f"Oversized work-state file: {name}")
        inspect_source_state(kind, name, data)
        blobs["data/" + name] = data
    manifest = {
        "schema": SCHEMA,
        "kind": kind,
        "git_source_commit": source_commit,
        "source_revisions": SOURCE_LOCKS[kind],
        "privacy": "PRIVATE_REPOSITORY_ONLY",
        "editorial_state": "WORKING_WITNESSES_NOT_CONTEXTUAL_SEMANTIC_APPROVAL",
        "redistribution": "NOT_AUTHORIZED",
        "public_release": False,
        "contents": {
            name: {"bytes": len(blobs[name]), "sha256": sha(blobs[name])}
            for name in sorted(blobs)
        },
    }
    blobs["manifest.json"] = encode_json(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Fixed ordering/uid/gid/mtime enables byte-identical re-creation.
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in sorted(blobs):
            b = blobs[name]
            info = tarfile.TarInfo(name=name)
            info.size = len(b)
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o600
            tar.addfile(info, io.BytesIO(b))
    with output.open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, mtime=0, fileobj=stream) as gz:
            gz.write(raw.getvalue())
    if output.stat().st_size > MAX_ARCHIVE:
        output.unlink()
        raise ValueError("Private archive size exceeds limit")
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{sha(output.read_bytes())}  {output.name}\n", encoding="ascii"
    )
    output.with_suffix(output.suffix + ".manifest.json").write_bytes(encode_json(manifest))
    verify(output)
    return manifest


def verify(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ARCHIVE:
        raise ValueError("Invalid private snapshot file")
    checks = path.with_suffix(path.suffix + ".sha256")
    if not checks.is_file() or checks.read_text(encoding="ascii") != f"{sha(path.read_bytes())}  {path.name}\n":
        raise ValueError("Private archive digest is missing or mismatched")
    with tarfile.open(path, mode="r:gz") as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names) or not all(
                m.isfile() and not m.issym() and m.name == Path(m.name).as_posix()
                and not m.name.startswith("/") and ".." not in Path(m.name).parts
                and 0 < m.size <= MAX_FILE for m in members):
            raise ValueError("Unsafe or duplicate archive member")
        if "manifest.json" not in names:
            raise ValueError("Missing private working-state manifest")
        manifest = json.load(tar.extractfile("manifest.json"))
        kind = manifest.get("kind")
        commit = manifest.get("git_source_commit")
        if path.name != archive_name(kind, commit):
            raise ValueError("Git commit/kind archive filename mismatch")
        if manifest.get("schema") != SCHEMA or manifest.get("source_revisions") != SOURCE_LOCKS[kind]:
            raise ValueError("Wrong snapshot source revision locks")
        if (manifest.get("privacy") != "PRIVATE_REPOSITORY_ONLY"
                or manifest.get("redistribution") != "NOT_AUTHORIZED"
                or manifest.get("public_release") is not False):
            raise ValueError("Unsafe private/public status metadata")
        expected = {"data/" + x for x in REQUIRED[kind]}
        if set(names) != expected | {"manifest.json"} or set(manifest.get("contents", {})) != expected:
            raise ValueError("Incomplete or unexpected private snapshot archive content")
        total = 0
        for name in expected:
            m = tar.getmember(name)
            total += m.size
            if total > MAX_ARCHIVE:
                raise ValueError("Oversized extracted private data")
            data = tar.extractfile(m).read()
            if manifest["contents"][name] != {"bytes": len(data), "sha256": sha(data)}:
                raise ValueError("Snapshot internal payload digest mismatch")
            inspect_source_state(kind, name.removeprefix("data/"), data)
    sidecar = path.with_suffix(path.suffix + ".manifest.json")
    if not sidecar.is_file() or sidecar.read_bytes() != encode_json(manifest):
        raise ValueError("Private snapshot manifest sidecar mismatch")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("pack")
    build.add_argument("--kind", required=True, choices=sorted(REQUIRED))
    build.add_argument("--source-commit", required=True)
    build.add_argument("--file", action="append", default=[])
    build.add_argument("--output", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "pack":
        pack(args.kind, args.source_commit, parse_files(args.file, args.kind), args.output)
        print("PRIVATE_BSI_WORK_SNAPSHOT_VERIFIED", args.output)
    else:
        m = verify(args.archive)
        print("PRIVATE_BSI_WORK_SNAPSHOT_REVERIFIED", m["kind"], m["git_source_commit"])


if __name__ == "__main__":
    main()
