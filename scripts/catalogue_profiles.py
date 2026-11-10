#!/usr/bin/env python3
"""Publish only separately approved, source-pinned reader profile descriptions.

A descriptive profile is independent of the immutable SWORD module version.
Use the original reviewed Markdown, not a second manually retyped copy.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


class ProfileError(ValueError):
    """The reader description has no valid, matching approval receipt."""


_ALLOWED = {
    "schema_version", "module_id", "sword_id", "module_version",
    "locale", "revision", "approved_at", "approved_by", "approval_url",
    "source_path", "source_git_blob_sha1", "sections", "evidence_urls",
}


def _https_url(value):
    if not isinstance(value, str) or len(value) > 2000:
        return False
    uri = urlsplit(value)
    return (uri.scheme == "https" and bool(uri.netloc)
            and not uri.username and not uri.password
            and not uri.fragment)


def _git_blob_sha1(content: bytes) -> str:
    return sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def _read_one(root: Path, file: Path, module: dict) -> tuple[str, dict]:
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 32 * 1024:
        raise ProfileError(f"{file}: unsafe or oversized approval receipt")
    try:
        declaration = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProfileError(f"{file}: invalid JSON approval receipt") from exc
    if not isinstance(declaration, dict) or set(declaration) != _ALLOWED:
        raise ProfileError(f"{file}: missing or unrecognized approval fields")
    if declaration["schema_version"] != 1:
        raise ProfileError(f"{file}: unsupported approval schema")
    for key, expected in (
        ("module_id", module["id"]), ("sword_id", module["sword_id"]),
        ("module_version", module["version"]),
    ):
        if declaration[key] != expected:
            raise ProfileError(f"{file}: {key} does not match released module")
    locale = declaration["locale"]
    if (not isinstance(locale, str)
            or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]+)*", locale)
            or file.name != locale + ".json"):
        raise ProfileError(f"{file}: locale/file identity mismatch")
    for key, pattern in (
        ("revision", r"\d{4}-\d{2}-\d{2}\.\d+"),
        ("approved_at", r"\d{4}-\d{2}-\d{2}"),
        ("source_git_blob_sha1", r"[a-f0-9]{40}"),
    ):
        value = declaration[key]
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ProfileError(f"{file}: invalid {key}")
    reviewer = declaration["approved_by"]
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer.upper() == "PENDING":
        raise ProfileError(f"{file}: explicit human editorial approval required")
    if not _https_url(declaration["approval_url"]):
        raise ProfileError(f"{file}: valid HTTPS approval reference required")
    source = declaration["source_path"]
    if not isinstance(source, str) or not re.fullmatch(r"docs/profiles/[a-z0-9-]+\.md", source):
        raise ProfileError(f"{file}: source must be an approved repository profile document")
    source_file = root / source
    if (source_file.is_symlink() or not source_file.is_file()
            or source_file.stat().st_size > 128 * 1024):
        raise ProfileError(f"{file}: source document missing or unsafe")
    body = source_file.read_bytes()
    if _git_blob_sha1(body) != declaration["source_git_blob_sha1"]:
        raise ProfileError(f"{file}: source document changed since editorial approval")
    try:
        markdown = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProfileError(f"{file}: profile must be UTF-8") from exc
    if "**EDITORIALLY APPROVED READER TEXT" not in markdown[:512]:
        raise ProfileError(f"{file}: source document is not editor-approved")
    sections = declaration["sections"]
    if (not isinstance(sections, dict)
            or set(sections) != {"short", "long", "end"}
            or any(not isinstance(marker, str) or not marker.startswith("## ")
                   or markdown.count(marker + "\n") != 1
                   for marker in sections.values())):
        raise ProfileError(f"{file}: ambiguous or missing approved section markers")
    a, b, c = (markdown.index(sections[k] + "\n") for k in ("short", "long", "end"))
    if not (a < b < c):
        raise ProfileError(f"{file}: reversed or overlapping description sections")
    short = markdown[a + len(sections["short"]) + 1:b].strip()
    long = markdown[b + len(sections["long"]) + 1:c].strip()
    if not short or not long or len(short.encode()) > 10_000 or len(long.encode()) > 50_000:
        raise ProfileError(f"{file}: empty or oversized reviewed description")
    evidence = declaration["evidence_urls"]
    if (not isinstance(evidence, dict) or not 2 <= len(evidence) <= 20
            or any(not isinstance(k, str) or not re.fullmatch(r"[a-z][a-z0-9_]+", k)
                   or not _https_url(url) for k, url in evidence.items())):
        raise ProfileError(f"{file}: invalid source and citation URLs")
    return locale, {
        "revision": declaration["revision"],
        "approved_at": declaration["approved_at"],
        "approved_by": reviewer,
        "approval_url": declaration["approval_url"],
        "source_path": source,
        "source_git_blob_sha1": declaration["source_git_blob_sha1"],
        "format": "markdown",
        "content_sha256": sha256((short + "\n" + long).encode("utf-8")).hexdigest(),
        "short_markdown": short,
        "long_markdown": long,
        "evidence_urls": evidence,
    }


def approved_profiles(root: Path, directory: Path, module: dict) -> dict:
    """Return independent, approved locale profiles or raise without publishing."""
    folder = directory / "profiles"
    if not folder.exists() and not folder.is_symlink():
        return {}
    if folder.is_symlink() or not folder.is_dir():
        raise ProfileError(f"{folder}: unsafe profile directory")
    if module["quality"]["status"] != "approved":
        raise ProfileError(f"{folder}: draft modules cannot publish profiles")
    profiles = {}
    for file in sorted(folder.iterdir()):
        if file.is_symlink() or not file.is_file() or file.suffix != ".json":
            raise ProfileError(f"{file}: unexpected profile file")
        locale, entry = _read_one(root, file, module)
        if locale in profiles:
            raise ProfileError(f"{file}: duplicate profile locale")
        profiles[locale] = entry
    if not profiles:
        raise ProfileError(f"{folder}: empty profile directory is not an approval")
    return profiles
