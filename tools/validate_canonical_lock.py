#!/usr/bin/env python3
"""Validate that generated/build inputs do not drift from the PKB canonical list."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "catalog" / "canonical-lock.json"
PROFILE_PATH = ROOT / "profiles" / "free-alexandria-v1.json"
CURATED_READING_PATH = ROOT / "docs" / "curated-reading.md"
GENERIC_SEARCH_PATTERNS = ("libbyapp.com/search?", "google.com/search?", "amazon.com/s?")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")


def duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-links", action="store_true")
    args = parser.parse_args()
    lock = load_json(LOCK_PATH)
    profile = load_json(PROFILE_PATH)
    errors: list[str] = []
    categories = ("required_local", "linked_only", "open_license_local", "preparedness_required_local")
    all_ids: list[str] = []
    for category in categories:
        values = lock.get(category)
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            errors.append(f"canonical-lock.json: {category} must be a list of string IDs")
            continue
        dupes = duplicates(values)
        if dupes:
            errors.append(f"canonical-lock.json: duplicate IDs in {category}: {', '.join(dupes)}")
        all_ids.extend(values)
    cross_category_dupes = duplicates(all_ids)
    if cross_category_dupes:
        errors.append("canonical-lock.json: IDs appear in multiple categories: " + ", ".join(cross_category_dupes))
    expected_profile = lock.get("required_local", [])
    actual_profile = profile.get("include_record_ids", [])
    if actual_profile != expected_profile:
        expected_set = set(expected_profile)
        actual_set = set(actual_profile)
        added = sorted(actual_set - expected_set)
        missing = sorted(expected_set - actual_set)
        if added:
            errors.append("profile silently adds noncanonical IDs: " + ", ".join(added))
        if missing:
            errors.append("profile omits canonical IDs: " + ", ".join(missing))
        if not added and not missing:
            errors.append("profile order differs from canonical lock")
    source = lock.get("source", {})
    if not source.get("repository") or not source.get("path") or not source.get("commit"):
        errors.append("canonical-lock.json: source repository, path, and commit are required")
    if args.strict_links:
        try:
            text = CURATED_READING_PATH.read_text(encoding="utf-8").lower()
        except FileNotFoundError:
            errors.append("docs/curated-reading.md is missing")
        else:
            hits = sorted(pattern for pattern in GENERIC_SEARCH_PATTERNS if pattern in text)
            if hits:
                errors.append("linked-only list still contains generic primary search URLs: " + ", ".join(hits))
    if errors:
        print("Canonical collection validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "Canonical collection validation passed: "
        f"{len(lock.get('required_local', []))} required-local, "
        f"{len(lock.get('linked_only', []))} linked-only, "
        f"{len(lock.get('open_license_local', []))} open-license-local, and "
        f"{len(lock.get('preparedness_required_local', []))} preparedness records locked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
