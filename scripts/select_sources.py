#!/usr/bin/env python3
"""Choose one SWORD upstream per *verified identical edition*, by explicit priority.

Read-only inventory selection; never downloads, modifies, or publishes texts.
Unverified collisions and unavailable higher-priority sources fail closed.
The result is a selection proposal for a future reviewed import pipeline,
not authorization to import or redistribute third-party content.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

from check_updates import ROOT, provider_catalog

ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")
EDITION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,100}$")
LANG = re.compile(r"^[A-Za-z]{2,8}(?:[-_][A-Za-z0-9]{1,8})*$")


def _unique_provider_ids(providers: list[dict]) -> dict[str, dict]:
    index = {}
    for p in providers:
        if p.get("kind", "sword") != "sword":
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not pid or pid in index:
            raise ValueError("Duplicate or missing SWORD provider ID")
        index[pid] = p
    return index


def validate_priority(providers: list[dict], policy: dict) -> list[str]:
    lookup = _unique_provider_ids(providers)
    order = policy.get("priority")
    if policy.get("schema_version") != 1 or not isinstance(order, list) or (
        len(order) != len(lookup) or len(set(order)) != len(order) or set(order) != set(lookup)
    ):
        raise ValueError("Provider priority must list every SWORD provider exactly once")
    return order


def _edition_map(registry: dict, provider_ids: set[str]) -> tuple[dict, dict]:
    """Only explicit, reviewed edition aliases justify silent de-duplication."""
    if registry.get("schema_version") != 1 or not isinstance(registry.get("editions"), list):
        raise ValueError("Invalid edition identity registry")
    by_source = {}
    by_edition = {}
    for entry in registry["editions"]:
        edition_id = entry.get("edition_id")
        if (not isinstance(edition_id, str) or not EDITION_ID.fullmatch(edition_id)
                or edition_id in by_edition):
            raise ValueError(f"Duplicate or invalid canonical edition ID: {edition_id!r}")
        if (entry.get("category") not in {"bible", "commentary", "dictionary", "general_book"}
                or not isinstance(entry.get("language"), str)
                or not LANG.fullmatch(entry["language"])):
            raise ValueError(f"{edition_id}: category and language are required")
        if (not isinstance(entry.get("verified_by"), str)
                or not entry["verified_by"].strip()
                or entry["verified_by"].strip().casefold() == "pending"
                or not isinstance(entry.get("evidence_url"), str)
                or not entry["evidence_url"].startswith("https://")):
            raise ValueError(f"{edition_id}: verified reviewer and HTTPS evidence required")
        aliases = entry.get("sources")
        if not isinstance(aliases, list) or len(aliases) < 2:
            raise ValueError(f"{edition_id}: at least two verified source aliases required")
        seen_in_group = set()
        for alias in aliases:
            if not isinstance(alias, dict):
                raise ValueError(f"{edition_id}: malformed source alias")
            provider, module_id = alias.get("provider"), alias.get("module_id")
            if (provider not in provider_ids or not isinstance(module_id, str)
                    or not ID.fullmatch(module_id)):
                raise ValueError(f"{edition_id}: invalid provider or SWORD module ID")
            key = (provider, module_id.casefold())
            if key in by_source or key in seen_in_group:
                raise ValueError(f"{edition_id}: duplicate or conflicting source alias {key}")
            seen_in_group.add(key)
            by_source[key] = edition_id
        by_edition[edition_id] = entry
    return by_source, by_edition


def _title_key(item: dict):
    """A conservative collision signal, NEVER an identity proof."""
    title = " ".join((item.get("description") or "").casefold().split())
    lang = (item.get("language") or "").casefold().replace("_", "-")
    category = item.get("category")
    if title and lang and category and category != "unknown":
        return (category, lang, title)
    return None


def _display_record(provider: str, item: dict) -> dict:
    return {
        "provider": provider,
        "module_id": item["module_id"],
        "category": item.get("category"),
        "language": item.get("language"),
        "description": item.get("description"),
        "versification": item.get("versification"),
        "upstream_version": item.get("version"),
        "conf_sha256": item.get("conf_sha256"),
    }


def select_sources(providers: list[dict], inventories: dict[str, dict],
                   registry: dict, policy: dict, provider_status: dict | None = None) -> dict:
    """Resolve eligible upstreams deterministically, blocking identity ambiguity.

    Inventories contain parsed SWORD .conf metadata indexed by casefolded ID.
    A candidate without a verified multi-provider alias can only be selected
    when no same-ID/title collisions or higher-provider outages exist.
    """
    by_provider = _unique_provider_ids(providers)
    order = validate_priority(providers, policy)
    by_source, by_edition = _edition_map(registry, set(by_provider))
    rank = {pid: i for i, pid in enumerate(order)}
    enabled = {pid for pid in order if by_provider[pid].get("enabled", False)}
    if provider_status is None:
        provider_status = {pid: ("ok" if pid in inventories else "unavailable")
                           if pid in enabled else "disabled" for pid in order}
    for pid in order:
        state = provider_status.get(pid, "unavailable")
        if state not in {"ok", "unavailable", "disabled"}:
            raise ValueError(f"{pid}: invalid provider status {state!r}")
        if pid in enabled and state == "disabled":
            raise ValueError(f"{pid}: enabled provider cannot be declared disabled")
        if pid not in enabled and state == "ok":
            raise ValueError(f"{pid}: disabled provider cannot be treated as available")

    groups = defaultdict(list)
    seen = set()
    for pid in order:
        if pid not in enabled or provider_status.get(pid) != "ok":
            continue
        entries = inventories.get(pid)
        if not isinstance(entries, dict):
            raise ValueError(f"{pid}: catalogue marked available without inventory")
        for key, item in entries.items():
            module_id = item.get("module_id") if isinstance(item, dict) else None
            if not isinstance(module_id, str) or not ID.fullmatch(module_id):
                raise ValueError(f"{pid}: invalid or missing module ID in inventory")
            if key.casefold() != module_id.casefold():
                raise ValueError(f"{pid}: catalogue key does not match module ID {module_id}")
            source_key = (pid, module_id.casefold())
            if source_key in seen:
                raise ValueError(f"{pid}: repeated module entry {module_id}")
            seen.add(source_key)
            canonical = by_source.get(source_key)
            group = ("verified", canonical) if canonical else ("unreviewed", pid, module_id.casefold())
            groups[group].append((pid, item))

    problems = defaultdict(set)
    collision_evidence = defaultdict(set)
    by_id = defaultdict(list)
    by_title = defaultdict(list)
    for group, members in groups.items():
        for pid, item in members:
            by_id[item["module_id"].casefold()].append(group)
            title = _title_key(item)
            if title:
                by_title[title].append(group)

    # Same ID across separate families cannot be safely installed without
    # identity review, even if metadata looks plausible.
    for module_id, candidates in by_id.items():
        unique = set(candidates)
        if len(unique) > 1:
            for group in unique:
                problems[group].add("same_module_id_unverified")
                collision_evidence[group].add("id:" + module_id)

    # Identical display title/category/language is a *candidate*, not a proof.
    # Two distinct explicitly reviewed edition families may legitimately share
    # a title; they were deliberately documented as distinct.
    for title, candidates in by_title.items():
        unique = set(candidates)
        if len(unique) <= 1:
            continue
        unreviewed = {group for group in unique if group[0] != "verified"}
        if unreviewed:
            for group in unique:
                problems[group].add("same_title_identity_review")
                collision_evidence[group].add("title:" + " / ".join(title))

    for group, members in groups.items():
        if group[0] == "verified":
            entry = by_edition[group[1]]
            for pid, item in members:
                if (item.get("category") != entry["category"] or
                    (item.get("language") or "").casefold() != entry["language"].casefold()):
                    problems[group].add("verified_identity_metadata_mismatch")
                if item.get("category") == "unknown":
                    problems[group].add("unsupported_module_category")
            member_providers = [pid for pid, _ in members]
            if len(member_providers) != len(set(member_providers)):
                problems[group].add("multiple_same_provider_aliases")
        else:
            _, item = members[0]
            if item.get("category") == "unknown":
                problems[group].add("unsupported_module_category")

        best = min(rank[pid] for pid, _ in members)
        for higher_pid in order[:best]:
            if higher_pid in enabled and provider_status.get(higher_pid) != "ok":
                problems[group].add("higher_priority_catalog_unavailable")

    selected, skipped, blocked = [], [], []
    for group, members in sorted(
        groups.items(),
        key=lambda pair: (min(rank[p] for p, _ in pair[1]),
                          str(pair[0]).casefold())
    ):
        candidates = sorted(members, key=lambda member: (rank[member[0]], member[1]["module_id"].casefold()))
        records = [_display_record(pid, item) for pid, item in candidates]
        canonical = group[1] if group[0] == "verified" else None
        if problems.get(group):
            blocked.append({
                "edition_id": canonical,
                "candidates": records,
                "reasons": sorted(problems[group]),
                "possible_collisions": sorted(collision_evidence.get(group, set())),
                "action": "review_edition_identity_before_import",
            })
            continue
        preferred = records[0]
        selected.append({
            "edition_id": canonical,
            "source": preferred,
            "identity": "reviewer_verified" if canonical else "single_catalog_candidate",
            "rights_review_required": True,
        })
        for lower in records[1:]:
            skipped.append({
                "edition_id": canonical,
                "source": lower,
                "preferred_source": {
                    "provider": preferred["provider"],
                    "module_id": preferred["module_id"],
                },
                "reason": "verified_identical_edition_at_higher_priority_provider",
            })

    unavailable = [pid for pid in order if pid in enabled and provider_status.get(pid) != "ok"]
    # A partial inventory is NEVER reported as complete, even when there are
    # no entries to block.
    return {
        "schema_version": 1,
        "priority": order,
        "provider_status": {pid: provider_status.get(pid, "unavailable") for pid in order},
        "complete": not unavailable and not blocked,
        "unavailable_providers": unavailable,
        "counts": {
            "selected_candidates": len(selected),
            "lower_priority_skipped": len(skipped),
            "blocked_groups": len(blocked),
        },
        "selected": selected,
        "skipped_lower_priority": skipped,
        "blocked": blocked,
        "note": "Read-only source selection, not import, redistribution approval or content identity verification.",
    }


def scan(providers: list[dict], registry: dict, policy: dict, fetch_catalog=provider_catalog) -> dict:
    inventories, statuses = {}, {}
    for provider in providers:
        pid = provider["id"]
        if provider.get("kind", "sword") != "sword":
            continue
        if not provider.get("enabled"):
            statuses[pid] = "disabled"
            continue
        try:
            inventories[pid] = fetch_catalog(provider)
            statuses[pid] = "ok"
        except Exception:
            # This is a read-only data source report. Don't quietly fall back
            # to lower priorities when an upstream could not be checked.
            statuses[pid] = "unavailable"
    report = select_sources(providers, inventories, registry, policy, statuses)
    report["checked_at"] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-only", action="store_true",
                        help="Monitor without failing on unresolved candidates; never allows importing them")
    args = parser.parse_args(argv)
    try:
        registry = json.loads((args.root / "config/edition-identities.json").read_text(encoding="utf-8"))
        policy = json.loads((args.root / "config/source-priority.json").read_text(encoding="utf-8"))
        sources = json.loads((args.root / "config/upstreams.json").read_text(encoding="utf-8"))
        report = scan(sources["providers"], registry, policy)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Source selection policy failure: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.output}: {report['counts']}")
    else:
        print(payload, end="")
    if not report["complete"] and not args.report_only:
        print("Import selection blocked: resolve ambiguities and upstream outages first", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
