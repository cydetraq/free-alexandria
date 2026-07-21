#!/usr/bin/env python3
"""Verify that every recorded remote source is actionable and every local edition exists."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from build_profile import CATALOG, ROOT, load_collections, load_records, load_source_options, presentation_files


def main() -> int:
    online = "--online" in sys.argv[1:]
    errors: list[str] = []
    collection_ids = [item.get("id") for item in load_collections()]
    if len(collection_ids) != len(set(collection_ids)):
        errors.append("collection taxonomy has duplicate IDs")
    defined_collections = set(collection_ids)
    for record in load_records():
        missing_collections = set(record.get("collections", [])) - defined_collections
        if missing_collections:
            errors.append(f"{record['id']}: undefined collection IDs: {', '.join(sorted(missing_collections))}")
    options = load_source_options()
    gutenberg_sources: list[tuple[str, str]] = []
    for work_id, sources in sorted(options.items()):
        if not any(source.get("source_id") == "libby" for source in sources):
            errors.append(f"{work_id}: missing Libby library fallback")
        for source in sources:
            if source.get("source_id") == "project-gutenberg":
                gutenberg_sources.append((work_id, str(source["edition_id"])))

    if online:
        # A source-health check is deliberately opt-in. The ordinary release check
        # must prove that a cloned archive is intact without requiring the internet.
        from concurrent.futures import ThreadPoolExecutor
        from resolve_catalog_sources import has_downloadable_text

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
        _, selected_editions, visible_files = presentation_files(work_editions)
        visible_roles = [file.get("role") for file in visible_files]
        if not selected_editions:
            errors.append(f"{work_id}: has no selected reader edition")
        if visible_roles.count("epub") != 1:
            errors.append(f"{work_id}: reader view must provide exactly one EPUB")
        if visible_roles.count("pdf") + visible_roles.count("text-pdf") != 1:
            errors.append(f"{work_id}: reader view must provide exactly one PDF")
        if "pdf" in visible_roles and "text-pdf" in visible_roles:
            errors.append(f"{work_id}: reader view mixes a scan and text-PDF fallback")
        has_facsimile = any(
            file.get("role") == "facsimile-pdf"
            for edition in selected_editions for file in edition.get("files", [])
        )
        if has_facsimile and "pdf" not in visible_roles:
            errors.append(f"{work_id}: supplied facsimile was not selected as the reader PDF")

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
        roles = [file.get("role") for file in record.get("download_files", [])]
        if roles.count("epub") != 1 or roles.count("pdf") + roles.count("text-pdf") != 1:
            errors.append(f"{record['id']}: API download_files is not a single EPUB/PDF pair")
        for field in ("author", "publisher", "original_language", "description", "why_included"):
            if field in {"author", "publisher"}:
                if not (record.get("author") or record.get("publisher")):
                    errors.append(f"{record['id']}: API lacks author or publisher")
            elif not record.get(field):
                errors.append(f"{record['id']}: API lacks reader-facing {field}")
    exported_collections = [item.get("id") for item in exported_catalog.get("collections", [])]
    if exported_collections != collection_ids:
        errors.append("catalog export does not preserve the canonical collection taxonomy")

    if errors:
        print("Source lint failed:", *errors, sep="\n")
        return 1
    scope = "including live Project Gutenberg endpoints; " if online else ""
    print(f"Source lint passed: {scope}{len(options)} records have Libby fallbacks; {len(editions)} works have verified local editions and one unambiguous EPUB/PDF pair.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
