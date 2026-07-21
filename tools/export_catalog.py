#!/usr/bin/env python3
"""Create the committed, dependency-free catalog exports for GitHub and API consumers."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from build_profile import CATALOG, ROOT, edition_sources, load_collections, load_records, load_source_options, presentation_files, rights_guidance

API_PATH = CATALOG / "catalog.json"
MARKDOWN_PATH = ROOT / "docs" / "catalog.md"
CURATED_LIST_PATH = ROOT / "lists" / "curated-reading.json"
CURATED_LIST_MARKDOWN_PATH = ROOT / "docs" / "curated-reading.md"


def load_published_editions() -> dict[str, list[dict]]:
    """Return the committed local editions keyed by work ID."""
    return json.loads((CATALOG / "published-editions.json").read_text()).get("editions", {})


def render_api() -> str:
    published_editions = load_published_editions()
    records = [
        {
            **record,
            "download_files": presentation_files(published_editions[record["id"]])[2],
            "edition_sources": edition_sources(published_editions[record["id"]]),
            "rights_guidance": rights_guidance(record, edition_sources(published_editions[record["id"]])),
        }
        for record in load_records() if record["id"] in published_editions
    ]
    payload = {
        "format_version": 1,
        "offline_notice": "This file contains only works supplied by this repository as local EPUB/PDF editions. It has no runtime dependency on external catalogs or URLs.",
        "collections": load_collections(),
        "records": sorted(records, key=lambda item: item["id"]),
        "published_editions": {"format_version": 1, "editions": published_editions},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def table_cell(value: object) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def markdown_links(items: list[tuple[str, str]]) -> str:
    return " · ".join(f"[{label}]({url})" for label, url in items) or "—"


def local_file_links(editions: list[dict]) -> str:
    """Render usable relative EPUB/PDF links for GitHub and an offline clone."""
    links: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    _, _, files = presentation_files(editions)
    for file in files:
        raw_role = str(file.get("role", "file"))
        role = {"text-pdf": "Text PDF"}.get(raw_role, raw_role.upper())
        key = (role, file["path"])
        if key not in seen:
            seen.add(key)
            links.append((role, "../" + file["path"]))
    return markdown_links(links)


def render_markdown(records: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        for collection in record.get("collections", ["uncategorized"]):
            grouped[collection].append(record)
    collection_defs = load_collections()
    labels = {item["id"]: item["name"] for item in collection_defs}
    collection_order = [item["id"] for item in collection_defs]
    published_editions = load_published_editions()
    lines = [
        "# Catalog",
        "",
        "This is the committed, readable Free Alexandria catalog. Every listed work is included locally and remains usable offline after cloning the repository. A supplied scan is used for the PDF whenever available; **Text PDF** means a compact generated fallback.",
        "A work can appear in more than one collection because the collections are separate ways to browse the same local edition, not duplicate files.",
        "",
        f"**Included works:** {len(records)}<br>",
        "**Machine-readable export:** [`catalog/catalog.json`](../catalog/catalog.json)<br>",
        "**Stored editions:** [`catalog/published-editions.json`](../catalog/published-editions.json)",
        "",
    ]
    for collection in [item for item in collection_order if item in grouped] + sorted(set(grouped) - set(collection_order)):
        lines.extend([f"## {labels.get(collection, collection)}", "", "| Title | Author / publisher | Year | Local files |", "| --- | --- | ---: | --- |"])
        for record in sorted(grouped[collection], key=lambda item: item.get("title", item["id"])):
            lines.append(
                "| {title} | {creator} | {year} | {files} |".format(
                    title=table_cell(record.get("title")),
                    creator=table_cell(record.get("author") or record.get("publisher")),
                    year=table_cell(record.get("original_year")),
                    files=local_file_links(published_editions.get(record["id"], [])),
                )
            )
        lines.append("")
    lines.extend([
        "## How to consume this catalog",
        "",
        "- Read this file for a GitHub-friendly inventory.",
        "- Use `catalog/catalog.json` as the stable V1 API for scripts and other catalog tools.",
        "- Browse [`curated-reading.md`](curated-reading.md) for recommendations that are not supplied in this archive.",
        "",
    ])
    return "\n".join(lines)


def render_curated_list(records: list[dict]) -> str:
    """Keep useful recommendations separate from the downloadable catalog."""
    source_options = load_source_options()
    entries = [
        {
            "id": record["id"], "title": record["title"], "author": record.get("author") or record.get("publisher"),
            "original_year": record.get("original_year"), "collections": record.get("collections", []),
            "description": record.get("description", ""), "why_included": record.get("why_included", ""),
            "library_link": next((option["url"] for option in source_options.get(record["id"], []) if option.get("source_id") == "libby"), None),
        }
        for record in records
    ]
    return json.dumps({"format_version": 1, "notice": "Curated recommendations only. These works are not supplied by this repository.", "records": entries}, ensure_ascii=False, indent=2) + "\n"


def render_curated_markdown(records: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        for collection in record.get("collections", ["other"]):
            grouped[collection].append(record)
    labels = {"banned-challenged": "Banned & Challenged Literature", "suppressed-knowledge": "Suppressed Knowledge", "preparedness": "Preparedness & Field Manuals", "essential-reading": "Essential Reading", "original-language": "Original-Language Reading", "essential-literature": "Essential Literature"}
    source_options = load_source_options()
    lines = ["# Curated reading lists", "", "These are recommendations retained for their relevance. They are not part of the downloadable Free Alexandria catalog because this repository does not currently supply their EPUB/PDF editions.", ""]
    for collection in sorted(grouped, key=lambda value: labels.get(value, value)):
        lines.extend([f"## {labels.get(collection, collection)}", "", "| Title | Author / publisher | Why it is on this list |", "| --- | --- | --- |"])
        for record in sorted(grouped[collection], key=lambda item: item.get("title", item["id"])):
            lines.append(f"| {table_cell(record.get('title'))} | {table_cell(record.get('author') or record.get('publisher'))} | {table_cell(record.get('why_included'))} |")
        lines.append("")
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    if check:
        return path.exists() and path.read_text() == content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed exports are stale")
    args = parser.parse_args()
    all_records = load_records()
    published_ids = set(load_published_editions())
    records = [record for record in all_records if record["id"] in published_ids]
    curated_records = [record for record in all_records if record["id"] not in published_ids]
    api_ok = write_or_check(API_PATH, render_api(), args.check)
    markdown_ok = write_or_check(MARKDOWN_PATH, render_markdown(records), args.check)
    curated_json_ok = write_or_check(CURATED_LIST_PATH, render_curated_list(curated_records), args.check)
    curated_markdown_ok = write_or_check(CURATED_LIST_MARKDOWN_PATH, render_curated_markdown(curated_records), args.check)
    if not api_ok or not markdown_ok or not curated_json_ok or not curated_markdown_ok:
        print("Catalog exports are stale. Run: python3 tools/export_catalog.py", file=sys.stderr)
        return 1
    print("Catalog exports are current." if args.check else "Catalog exports written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
