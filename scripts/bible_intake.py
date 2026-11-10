#!/usr/bin/env python3
"""Research-only Bible intake: strict manifest, bounded HTTPS and ZIP hashes.

The outputs are metadata. No source Scripture or original publisher ZIP is
committed, uploaded, echoed or put into the GitHub Actions cache.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from jsonschema import Draft202012Validator, FormatChecker
from pilot_preflight import inspect_archive

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "config/bible-intake"
SCHEMA = ROOT / "schemas/bible-intake.schema.json"
IDS = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
HOSTS = {
    "ebible": frozenset({"ebible.org", "www.ebible.org"}),
    "crosswire": frozenset({"crosswire.org", "www.crosswire.org", "ftp.crosswire.org"}),
    "step": frozenset({"public.modules.stepbible.org"}),
    "andbible": frozenset({"andbible.github.io"}),
    "andbible-extra": frozenset({"andbible.github.io"}),
}
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_REDIRECTS = 5


class IntakeError(ValueError):
    """The source identity, safety requirements or evidence did not pass."""


def _safe_url(url: str, provider: str) -> None:
    if not isinstance(url, str) or len(url) > 1200:
        raise IntakeError("Invalid or overlong source URL")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in HOSTS[provider]
            or parts.username or parts.password or parts.port not in (None, 443)
            or parts.query or parts.fragment or not parts.path.startswith("/")):
        raise IntakeError("Source URL/redirect is not an approved provider HTTPS archive")


class ProviderRedirects(HTTPRedirectHandler):
    def __init__(self, provider: str):
        self.provider = provider
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        if self.redirects > MAX_REDIRECTS:
            raise IntakeError("Exceeded maximum archive redirects")
        _safe_url(newurl, self.provider)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_manifest(resource_id: str, *, root: Path = ROOT) -> dict:
    if not isinstance(resource_id, str) or not IDS.fullmatch(resource_id):
        raise IntakeError("Invalid resource identifier")
    manifest_path = root / "config/bible-intake" / (resource_id + ".json")
    schema_path = root / "schemas/bible-intake.schema.json"
    if (manifest_path.is_symlink() or not manifest_path.is_file()
            or manifest_path.stat().st_size > 24 * 1024):
        raise IntakeError("Missing, linked or oversized Bible research manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errs = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest))
    if errs:
        err = sorted(errs, key=lambda item: str(item.path))[0]
        raise IntakeError("Invalid reviewed manifest field: " + ".".join(map(str, err.path)))
    if manifest["resource_id"] != resource_id or manifest["purpose"] != "research_only":
        raise IntakeError("Resource id/authorization mismatch")
    for key in ("source", "sword"):
        _safe_url(manifest[key]["url"], manifest["provider"])
    if manifest["source"]["format"] == "OSIS" and not manifest["source"].get("member"):
        raise IntakeError("Original zipped OSIS requires an explicit XML member")
    if manifest["source"]["format"] == "USFX":
        relative = manifest["crosswalk"]
        target = root / relative
        if (target.is_symlink() or not target.is_file()
                or target.stat().st_size > 100_000):
            raise IntakeError("Missing or unsafe reviewed source book crosswalk")
    return manifest


def fetch_pinned(url: str, expected_sha256: str, provider: str, destination: Path, *, opener=None) -> dict:
    """Stream a pinned upstream archive into a new private path, never overwrite."""
    _safe_url(url, provider)
    if not SHA.fullmatch(expected_sha256):
        raise IntakeError("Invalid expected SHA-256")
    if destination.is_symlink() or destination.exists() or destination.parent.is_symlink():
        raise IntakeError("Refuse to overwrite source archives or symlink paths")
    destination.parent.mkdir(parents=True, exist_ok=True)
    opener = opener or build_opener(ProviderRedirects(provider))
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".intake-", delete=False) as out:
            staged = Path(out.name)
            digest = sha256()
            total = 0
            req = Request(url, headers={"User-Agent": "BibleResources-OriginalSourceAudit/1.0"})
            with closing(opener.open(req, timeout=75)) as response:
                _safe_url(response.geturl(), provider)
                while data := response.read(256 * 1024):
                    total += len(data)
                    if total > MAX_ARCHIVE_BYTES:
                        raise IntakeError("Original archive exceeds bounded download size")
                    digest.update(data)
                    out.write(data)
            out.flush()
            os.fsync(out.fileno())
        if total == 0 or digest.hexdigest() != expected_sha256:
            raise IntakeError("Upstream original archive SHA-256 drift or empty file")
        os.replace(staged, destination)
        staged = None
        return {"sha256":digest.hexdigest(),"bytes":total,"provider":provider}
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def acquire(manifest: dict, root: Path, *, source: bool, sword: bool, opener=None) -> tuple[dict, dict]:
    """Original ZIPs are confined to the caller's disposable directory."""
    receipts = {}
    archives = {}
    for label, enabled in (("source", source), ("sword", sword)):
        if not enabled:
            continue
        item = manifest[label]
        archive = root / (label + ".zip")
        receipt = fetch_pinned(item["url"], item["sha256"], manifest["provider"], archive, opener=opener)
        proof = inspect_archive(
            archive, source_kind="sword" if label == "sword" else "authored",
            expected_module_id=item["module_id"] if label == "sword" else None,
            expected_category="bible" if label == "sword" else None,
        )
        if proof["archive_sha256"] != item["sha256"]:
            raise IntakeError("Safe ZIP proof no longer matches pinned original")
        if label == "sword":
            conf = proof["sword_conf"]
            if conf["driver"] != item["driver"]:
                raise IntakeError("Original SWORD driver differs from reviewed manifest")
            if item.get("versification") and conf["versification"] != item["versification"]:
                raise IntakeError("Original SWORD versification differs from reviewed manifest")
            receipt["sword"] = {
                "module_id":conf["module_id"],"version":conf["version"],
                "driver":conf["driver"],"versification":conf["versification"],
            }
        receipt["member_count"] = proof["member_count"]
        receipt["unpacked_bytes"] = proof["total_unpacked_bytes"]
        receipts[label] = receipt
        archives[label] = archive
    return receipts, archives


def parse_audit_comment(body: str) -> tuple[str, int]:
    """Strict owner-only issue-comment command parser; never execute shell text."""
    if not isinstance(body, str) or len(body) > 150 or "\n" in body or "\r" in body:
        raise IntakeError("Expected one bounded /bible-audit command")
    match = re.fullmatch(r"/bible-audit ([a-z][a-z0-9-]{1,63}) ([1-7])", body.strip())
    if not match:
        raise IntakeError("Expected /bible-audit <resource-id> <stage 1-7>")
    return match.group(1), int(match.group(2))


def observe_current_upstream(resource_id: str, *, opener=None) -> dict:
    """Metadata-only *unapproved* remote identity discovery for human re-pinning.

    Never writes, redistributes, extracts or trusts these archives as equivalent.
    Only the separately reviewed manifest may authorize pinned acquisition.
    """
    m = load_manifest(resource_id)
    opener = opener or build_opener(ProviderRedirects(m["provider"]))
    reports = {}
    for label in ("source","sword"):
        url = m[label]["url"]
        _safe_url(url,m["provider"])
        digest = sha256()
        total = 0
        req = Request(url,headers={"User-Agent":"BibleResources-UpstreamRevisionObservation/1.0"})
        with closing(opener.open(req,timeout=75)) as response:
            _safe_url(response.geturl(),m["provider"])
            while chunk := response.read(256*1024):
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise IntakeError("Unapproved remote source exceeds inspection size limit")
                digest.update(chunk)
        if not total:
            raise IntakeError("Empty upstream observation cannot become a release pin")
        reports[label] = {
            "observed_sha256":digest.hexdigest(),
            "observed_bytes":total,
            "previously_pinned_sha256":m[label]["sha256"],
            "still_pinned":digest.hexdigest()==m[label]["sha256"],
            "rights_or_edition_equivalence_verified":False,
        }
    return {"schema_version":1,"resource_id":resource_id,"status":"remote_observation_only_needs_source_review",
            "archives":reports,"published":False,"source_zip_not_retained":True}


def main(argv=None) -> int:
    import argparse
    parser=argparse.ArgumentParser(description="Observe original upstream archive identities without repinning them")
    parser.add_argument("--resource-id",required=True)
    parser.add_argument("--observe-only",action="store_true",required=True)
    args=parser.parse_args(argv)
    try:
        report=observe_current_upstream(args.resource_id)
    except Exception as exc:
        # Preserve no unexpected third-party content in public error messages.
        parser.error(str(exc)[:200] if isinstance(exc,IntakeError) else type(exc).__name__)
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
