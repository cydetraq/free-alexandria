#!/usr/bin/env python3
"""Validate the stable canonical reading list and its primary links."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "catalog" / "curated-reading.lock.json"


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    errors: list[str] = []
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    canonical = ROOT / lock["canonical_path"]
    data = canonical.read_bytes()
    actual_sha = git_blob_sha1(data)
    expected_sha = lock["git_blob_sha1"]

    if actual_sha != expected_sha:
        errors.append(
            "canonical reading list changed without an explicit lock update: "
            f"expected {expected_sha}, got {actual_sha}"
        )

    text = data.decode("utf-8")
    forbidden_hosts = {
        host.casefold()
        for host in lock.get("policy", {}).get("forbidden_primary_link_hosts", [])
    }

    row_pattern = re.compile(
        r"^\|\s*(?P<title>[^|]+?)\s*\|\s*(?P<creator>[^|]+?)\s*\|"
        r"\s*(?P<reason>[^|]+?)\s*\|\s*\[(?P<label>[^]]+)]\((?P<url>[^)]+)\)\s*\|$"
    )
    seen_rows = 0
    for line_number, line in enumerate(text.splitlines(), 1):
        match = row_pattern.match(line)
        if not match:
            continue
        seen_rows += 1
        title = match.group("title").strip()
        url = match.group("url").strip()
        host = (urlparse(url).hostname or "").casefold()
        if host in forbidden_hosts:
            errors.append(
                f"{canonical.relative_to(ROOT)}:{line_number}: {title!r} uses "
                f"forbidden generic primary-link host {host!r}"
            )
        if not url.startswith(("https://", "http://")):
            errors.append(
                f"{canonical.relative_to(ROOT)}:{line_number}: {title!r} has invalid URL {url!r}"
            )

    if seen_rows == 0:
        errors.append("canonical reading list contains no parseable work rows")

    if errors:
        print("Curated reading-list validation failed:", *errors, sep="\n- ")
        return 1

    print(
        "Curated reading-list validation passed: "
        f"{seen_rows} rows, locked at Git blob {actual_sha}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
