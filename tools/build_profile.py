#!/usr/bin/env python3
"""Build a V1 offline catalog preview and a reproducible curation lockfile.

The catalog currently uses a deliberately small YAML subset. This parser reads only
top-level records and fields emitted by this repository; it is not a general YAML parser.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
SKIP = {"tags.yaml", "sources.yaml", "edition-queue.yaml"}
RECORD_START = re.compile(r"^- id: (?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)$")
FIELD = re.compile(r"^  (?P<key>[a-z_]+): ?(?P<value>.*)$")
LIST = re.compile(r"^\[(.*)\]$")
INT_FIELDS = {"original_year"}


def scalar(value: str):
    value = value.strip()
    list_match = LIST.match(value)
    if list_match:
        inner = list_match.group(1).strip()
        return [] if not inner else [part.strip().strip("'\"") for part in inner.split(",")]
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "~"}:
        return None
    return value.strip("'\"")


def load_records(paths: list[Path] | None = None, skip: set[str] | None = None) -> list[dict]:
    records: list[dict] = []
    paths = paths or sorted(CATALOG.glob("*.yaml"))
    skip = SKIP if skip is None else skip
    for path in paths:
        if path.name in skip:
            continue
        current: dict | None = None
        for line in path.read_text().splitlines():
            start = RECORD_START.match(line)
            if start:
                if current:
                    records.append(current)
                current = {"id": start.group("id"), "catalog_file": path.name}
                continue
            field = FIELD.match(line)
            if field and current is not None:
                key, value = field.group("key"), scalar(field.group("value"))
                if key in INT_FIELDS and isinstance(value, str) and value.lstrip("-").isdigit():
                    value = int(value)
                current[key] = value
        if current:
            records.append(current)
    return records


def revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def select(profile: dict, records: list[dict]) -> list[dict]:
    by_id = {record["id"]: record for record in records}
    requested = set(profile.get("include_record_ids", []))
    wanted_collections = set(profile.get("include_collections", []))
    if wanted_collections:
        requested |= {
            record["id"] for record in records
            if wanted_collections.intersection(record.get("collections", []))
        }
    unknown = requested - set(by_id)
    if unknown:
        raise ValueError(f"profile references unknown record IDs: {', '.join(sorted(unknown))}")
    requested -= set(profile.get("exclude_record_ids", []))
    selected = [by_id[record_id] for record_id in sorted(requested)]
    if not profile["constraints"].get("allow_link_only", False):
        selected = [record for record in selected if record.get("rights_status") != "copyrighted-link-only"]
    return selected


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_editions(profile: dict, records: list[dict]) -> dict[str, dict]:
    registry = json.loads((CATALOG / "published-editions.json").read_text()).get("editions", {})
    preferences = profile.get("language_preferences", [])
    resolved: dict[str, dict] = {}
    missing: list[str] = []
    for record in records:
        candidates = registry.get(record["id"], [])
        candidate = next((item for language in preferences for item in candidates if item["language"] == language), None)
        candidate = candidate or (candidates[0] if candidates else None)
        if not candidate:
            missing.append(record["id"])
            continue
        for file in candidate["files"]:
            path = ROOT / file["path"]
            if not path.is_file():
                raise ValueError(f"missing local file for {record['id']}: {file['path']}")
            if path.stat().st_size != file["bytes"]:
                raise ValueError(f"size mismatch for {record['id']}: {file['path']}")
            if digest(path) != file["sha256"]:
                raise ValueError(f"checksum mismatch for {record['id']}: {file['path']}")
        resolved[record["id"]] = candidate
    if missing:
        raise ValueError("distribution build requires local published editions for: " + ", ".join(missing))
    total_bytes = sum(file["bytes"] for edition in resolved.values() for file in edition["files"])
    limit = profile["constraints"].get("max_total_bytes")
    if limit is not None and total_bytes > limit:
        raise ValueError(f"resolved editions need {total_bytes} bytes, exceeding profile limit of {limit}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    profile = json.loads(args.profile.read_text())
    records = select(profile, load_records())
    editions = resolve_editions(profile, records) if profile["build_mode"] == "distribution" else {}
    output = args.output / profile["id"]
    if output.exists():
        raise FileExistsError(
            f"refusing to overwrite existing build: {output}. Choose a new output directory or remove it explicitly."
        )
    output.mkdir(parents=True)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "format_version": 1,
        "profile": {"id": profile["id"], "name": profile["name"], "curator": profile["curator"]},
        "build_mode": profile["build_mode"],
        "offline_notice": "This manifest is self-contained. External source URLs are not required at runtime.",
        "records": records,
    }
    if editions:
        manifest["editions"] = editions
    lock = {
        "format_version": 1,
        "profile": profile,
        "catalog_revision": revision(),
        "generated_at": generated_at,
        "records": [{"id": record["id"], "catalog_file": record["catalog_file"]} for record in records],
        "edition_resolution": editions or "pending-acquisition"
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "build-lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    shutil.copy2(ROOT / "portal" / "index.html", output / "index.html")
    for edition in editions.values():
        for file in edition["files"]:
            destination = output / file["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / file["path"], destination)
    print(f"Built {profile['build_mode']} for {profile['id']}: {len(records)} records -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
