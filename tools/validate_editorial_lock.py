#!/usr/bin/env python3
"""Reject silent editorial-list drift and placeholder-only recommendation links."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "catalog" / "editorial-lock.json"
GENERIC_PRIMARY_LINK = re.compile(r"\]\(https://libbyapp\.com/search\?", re.IGNORECASE)


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    errors: list[str] = []
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    for item in lock.get("locked_files", []):
        relative = item.get("path")
        expected = item.get("git_blob_sha1")
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append("editorial-lock.json contains an invalid locked_files entry")
            continue
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing locked editorial input: {relative}")
            continue
        actual = git_blob_sha1(path)
        if actual != expected:
            errors.append(
                f"editorial input changed without updating the lock: {relative} "
                f"(expected {expected}, found {actual})"
            )

    catalog_path = ROOT / "catalog" / "catalog.json"
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        records = catalog.get("records", []) if isinstance(catalog, dict) else []
        locked_count = next(
            (
                item.get("record_count")
                for item in lock.get("locked_files", [])
                if item.get("path") == "catalog/catalog.json"
            ),
            None,
        )
        if isinstance(locked_count, int) and len(records) != locked_count:
            errors.append(
                f"catalog record count drifted: lock says {locked_count}, catalog has {len(records)}"
            )

    reading_path = ROOT / "docs" / "curated-reading.md"
    if reading_path.is_file():
        text = reading_path.read_text(encoding="utf-8")
        generic_count = len(GENERIC_PRIMARY_LINK.findall(text))
        if generic_count:
            errors.append(
                f"curated reading list still contains {generic_count} generic Libby search links; "
                "replace each with an exact authoritative primary link before release"
            )

    if errors:
        print("Editorial validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Editorial lock and curated links passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
