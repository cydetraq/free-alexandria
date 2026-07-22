#!/usr/bin/env python3
"""Create the committed, dependency-free catalog exports for GitHub and API consumers."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from build_profile import (
    CATALOG,
    ROOT,
    edition_sources,
    load_collections,
    load_records,
    load_source_options,
    presentation_files,
    reader_metadata,
    rights_guidance,
)

API_PATH = CATALOG / "catalog.json"
MARKDOWN_PATH = ROOT / "docs" / "catalog.md"
CURATED_LIST_PATH = ROOT / "lists" / "curated-reading.json"
CURATED_LIST_MARKDOWN_PATH = ROOT / "docs" / "curated-reading.md"

LEGACY_COLLECTION_ALIASES = {
    "preparedness": "practical-preparedness",
    "practical-library": "practical-preparedness",
}


def load_published_editions() -> dict[str, list[dict]]:
    """Return the committed local editions keyed by work ID."""
    return json.loads((CATALOG / "published-editions.json").read_text()).get("editions", {})


def effective_collections(record: dict, editions: list[dict]) -> list[str]:
    """Return reader-facing collections based on the editions actually stored.

    The old practical/preparedness categories are merged. Original-language is not
    inferred from the work's history; it is present only when a non-English edition
    matching the work's declared original language is actually stored.
    """
    result: list[str] = []
    for collection in record.get("collections", []):
        normalized = LEGACY_COLLECTION_ALIASES.get(collection, collection)
        if normalized == "original-language":
            continue
        if normalized not in result:
            result.append(normalized)

    original_language = str(record.get("original_language") or "").strip()
    stored_languages = {
        str(edition.get("language") or "").strip().casefold()
        for edition in editions
        if edition.get("language")
    }
    if (
        original_language
        and original_language.casefold() != "english"
        and original_language.casefold() in stored_languages
        and "original-language" not in result
    ):
        result.append("original-language")
    return result


def exported_record(record: dict, editions: list[dict]) -> dict:
    enriched = reader_metadata(record)
    enriched["collections"] = effective_collections(enriched, editions)
    return enriched


def render_api() -> str:
    published_editions = load_published_editions()
    records = [
        {
            **exported_record(record, published_editions[record["id"]]),
            "download_files": presentation_files(published_editions[record["id"]])[2],
            "edition_sources": edition_sources(published_editions[record["id"]]),
            "rights_guidance": rights_guidance(
                record, edition_sources(published_editions[record["id"]])
            ),
        }
        for record in load_records()
        if record["id"] in published_editions
    ]
    payload = {
        "format_version": 2,
        "offline_notice": "This file contains only works supplied by this repository as local EPUB/PDF editions. It has no runtime dependency on external catalogs or URLs.",
        "collection_policy": {
            "practical_preparedness": "Legacy preparedness and practical-library memberships are merged into practical-preparedness.",
            "original_language": "Membership requires a stored non-English edition whose language matches the work's declared original language; an English translation alone does not qualify.",
        },
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
    descriptions = {item["id"]: item.get("description", "") for item in collection_defs}
    collection_order = [item["id"] for item in collection_defs]
    published_editions = load_published_editions()
    lines = [
        "# Catalog",
        "",
        "This is the committed, readable Free Alexandria catalog. Every listed work is included locally and remains usable offline after cloning the repository. A supplied scan is used for the PDF whenever available; **Text PDF** means a compact generated fallback.",
        "A work can appear in more than one collection because the collections are separate ways to browse the same local edition, not duplicate files.",
        "",
        "**Collection rules:** Practical and preparedness material is one collection. Original-Language Editions contains only works for which the archive actually stores a non-English edition matching the work's original language.",
        "",
        f"**Included works:** {len(records)}<br>",
        "**Machine-readable export:** [`catalog/catalog.json`](../catalog/catalog.json)<br>",
        "**Stored editions:** [`catalog/published-editions.json`](../catalog/published-editions.json)",
        "",
    ]
    for collection in [item for item in collection_order if item in grouped] + sorted(
        set(grouped) - set(collection_order)
    ):
        lines.extend(
            [
                f"## {labels.get(collection, collection)}",
                "",
                descriptions.get(collection, ""),
                "",
                "| Title | Author / publisher | Year | Local files |",
                "| --- | --- | ---: | --- |",
            ]
        )
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
    lines.extend(
        [
            "## How to consume this catalog",
            "",
            "- Read this file for a GitHub-friendly inventory.",
            "- Use `catalog/catalog.json` as the stable V1 API for scripts and other catalog tools.",
            "- Browse [`curated-reading.md`](curated-reading.md) for recommendations that are not supplied in this archive.",
            "",
        ]
    )
    return "\n".join(lines)


def render_curated_list(records: list[dict]) -> str:
    """Keep useful recommendations separate from the downloadable catalog."""
    source_options = load_source_options()
    entries = [
        {
            "id": record["id"],
            "title": record["title"],
            "author": record.get("author") or record.get("publisher"),
            "original_year": record.get("original_year"),
            "collections": record.get("collections", []),
            "description": record.get("description") or record.get("civilian_relevance", ""),
            "why_included": record.get("why_included") or record.get("civilian_relevance", ""),
            "library_link": next(
                (
                    option["url"]
                    for option in source_options.get(record["id"], [])
                    if option.get("source_id") == "libby"
                ),
                None,
            ),
        }
        for record in records
    ]
    return json.dumps(
        {
            "format_version": 1,
            "notice": "Curated recommendations only. These works are not supplied by this repository.",
            "records": entries,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def render_curated_markdown(records: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        for collection in record.get("collections", ["other"]):
            normalized = LEGACY_COLLECTION_ALIASES.get(collection, collection)
            if normalized == "original-language":
                continue
            grouped[normalized].append(record)
    collection_defs = load_collections()
    labels = {item["id"]: item["name"] for item in collection_defs}
    descriptions = {item["id"]: item.get("description", "") for item in collection_defs}
    collection_order = [item["id"] for item in collection_defs]
    source_options = load_source_options()
    lines = [
        "# Curated reading lists",
        "",
        "These are recommendations retained for their relevance. They are not part of the downloadable Free Alexandria catalog because this repository does not currently supply their EPUB/PDF editions.",
        "",
    ]
    for collection in [item for item in collection_order if item in grouped] + sorted(
        set(grouped) - set(collection_order)
    ):
        lines.extend(
            [
                f"## {labels.get(collection, collection)}",
                "",
                descriptions.get(collection, ""),
                "",
                "| Title | Author / publisher | Why it is on this list | Find / borrow |",
                "| --- | --- | --- | --- |",
            ]
        )
        for record in sorted(grouped[collection], key=lambda item: item.get("title", item["id"])):
            library_url = next(
                (
                    option["url"]
                    for option in source_options.get(record["id"], [])
                    if option.get("source_id") == "libby"
                ),
                None,
            )
            access = markdown_links([("Search in Libby", library_url)]) if library_url else "—"
            why = record.get("why_included") or record.get("civilian_relevance")
            lines.append(
                f"| {table_cell(record.get('title'))} | {table_cell(record.get('author') or record.get('publisher'))} | {table_cell(why)} | {access} |"
            )
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
    published_editions = load_published_editions()
    all_records = [reader_metadata(record) for record in load_records()]
    published_ids = set(published_editions)
    records = [
        exported_record(record, published_editions[record["id"]])
        for record in all_records
        if record["id"] in published_ids
    ]
    curated_records = [record for record in all_records if record["id"] not in published_ids]
    api_ok = write_or_check(API_PATH, render_api(), args.check)
    markdown_ok = write_or_check(MARKDOWN_PATH, render_markdown(records), args.check)
    curated_json_ok = write_or_check(CURATED_LIST_PATH, render_curated_list(curated_records), args.check)
    curated_markdown_ok = write_or_check(
        CURATED_LIST_MARKDOWN_PATH, render_curated_markdown(curated_records), args.check
    )
    if not api_ok or not markdown_ok or not curated_json_ok or not curated_markdown_ok:
        print("Catalog exports are stale. Run: python3 tools/export_catalog.py", file=sys.stderr)
        return 1
    print("Catalog exports are current." if args.check else "Catalog exports written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
