#!/usr/bin/env python3
"""Verify that every recorded remote source is actionable and every local edition exists."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from build_profile import CATALOG, ROOT, load_source_options
from resolve_catalog_sources import has_downloadable_text


def main() -> int:
    errors: list[str] = []
    options = load_source_options()
    gutenberg_sources: list[tuple[str, str]] = []
    for work_id, sources in sorted(options.items()):
        if not any(source.get("source_id") == "libby" for source in sources):
            errors.append(f"{work_id}: missing Libby library fallback")
        for source in sources:
            if source.get("source_id") == "project-gutenberg":
                gutenberg_sources.append((work_id, str(source["edition_id"])))

    # Remote verification is intentionally concurrent: source linting is a routine
    # release check, not a multi-minute serial crawl.
    with ThreadPoolExecutor(max_workers=12) as pool:
        checks = pool.map(lambda item: (*item, has_downloadable_text(item[1])), gutenberg_sources)
        for work_id, edition_id, available in checks:
            if not available:
                errors.append(f"{work_id}: Gutenberg {edition_id} has no live EPUB or text endpoint")

    editions = json.loads((CATALOG / "published-editions.json").read_text()).get("editions", {})
    for work_id, work_editions in sorted(editions.items()):
        for edition in work_editions:
            if not (ROOT / edition.get("provenance_path", "")).is_file():
                errors.append(f"{work_id}: missing provenance record")
            for file in edition.get("files", []):
                if not (ROOT / file["path"]).is_file():
                    errors.append(f"{work_id}: missing local {file.get('role', 'file')}")

    exported_catalog = json.loads((CATALOG / "catalog.json").read_text())
    exported_ids = {record["id"] for record in exported_catalog.get("records", [])}
    if exported_ids != set(editions):
        errors.append("catalog export does not exactly match the supplied local-edition registry")
    for record in exported_catalog.get("records", []):
        if "source_options" in record:
            errors.append(f"{record['id']}: catalog exposes resolver search results instead of included-edition sources")
        sources = record.get("edition_sources", [])
        if not sources or not sources[0].get("primary"):
            errors.append(f"{record['id']}: catalog lacks a primary included-edition source")

    if errors:
        print("Source lint failed:", *errors, sep="\n")
        return 1
    print(f"Source lint passed: {len(options)} records have Libby fallbacks; {len(editions)} works have verified local editions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
