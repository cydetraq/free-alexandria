#!/usr/bin/env python3
"""Create the committed, dependency-free catalog exports for GitHub and API consumers."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records, load_source_options

API_PATH = CATALOG / "catalog.json"
MARKDOWN_PATH = ROOT / "docs" / "catalog.md"
CURATED_LIST_PATH = ROOT / "lists" / "curated-reading.json"
CURATED_LIST_MARKDOWN_PATH = ROOT / "docs" / "curated-reading.md"


def load_published_editions() -> dict[str, list[dict]]:
    """Return the committed local editions keyed by work ID."""
    return json.loads((CATALOG / "published-editions.json").read_text()).get("editions", {})


def rights_guidance(record: dict, options: list[dict]) -> dict:
    """Evidence-oriented guidance, never a legal conclusion or permission grant."""
    year = record.get("original_year")
    language = record.get("original_language")
    notes: list[str] = []
    if options:
        notes.append("An exact edition source is recorded in this catalog; inspect that source's own rights statement before use.")
    if isinstance(year, int) and year <= 1930 and language == "English":
        signal = "strong-us-public-domain-signal"
        notes.append("The underlying English-language work predates the current U.S. public-domain cutoff, but later additions in a specific file can differ.")
    elif isinstance(year, int) and 1931 <= year <= 1963:
        signal = "us-renewal-research-needed"
        notes.append("For U.S. use, publication and renewal facts for the specific work and edition can matter.")
    elif language and language != "English":
        signal = "translation-and-jurisdiction-review-needed"
        notes.append("The original work and any English translation are separate editions; jurisdiction and translator details matter.")
    else:
        signal = "edition-and-jurisdiction-review-needed"
        notes.append("Use the recorded edition and source facts to assess your own intended use.")
    return {
        "not_a_legal_ruling": True,
        "signal": signal,
        "evidence_notes": notes,
        "operator_question": "May I download, keep, share, or publish this specific edition where and how I intend to use it?"
    }


def render_api() -> str:
    source_options = load_source_options()
    published_editions = load_published_editions()
    records = [
        {
            **record,
            "source_options": source_options.get(record["id"], []),
            "rights_guidance": rights_guidance(record, source_options.get(record["id"], [])),
        }
        for record in load_records() if record["id"] in published_editions
    ]
    payload = {
        "format_version": 1,
        "offline_notice": "This file contains only works supplied by this repository as local EPUB/PDF editions. It has no runtime dependency on external catalogs or URLs.",
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
    for edition in editions:
        for file in edition.get("files", []):
            raw_role = str(file.get("role", "file"))
            role = {"facsimile-pdf": "Facsimile PDF"}.get(raw_role, raw_role.upper())
            key = (role, file["path"])
            if key not in seen:
                seen.add(key)
                links.append((role, "../" + file["path"]))
    return markdown_links(links)


def source_links(options: list[dict]) -> str:
    return markdown_links([(option["label"], option["url"]) for option in options])


def render_markdown(records: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        for collection in record.get("collections", ["uncategorized"]):
            grouped[collection].append(record)
    labels = {
        "banned-challenged": "Banned & Challenged Literature",
        "suppressed-knowledge": "Suppressed Knowledge",
        "preparedness": "Preparedness & Field Manuals",
        "essential-reading": "Essential Reading — External Links",
        "original-language": "Original-Language Library",
        "essential-literature": "Essential Literature",
    }
    source_options = load_source_options()
    published_editions = load_published_editions()
    published_ids = set(published_editions)
    lines = [
        "# Catalog",
        "",
        "This is the committed, readable Free Alexandria catalog. Every listed work is included locally as EPUB and PDF and remains usable offline after cloning the repository.",
        "",
        f"**Included works:** {len(records)}<br>",
        "**Machine-readable export:** [`catalog/catalog.json`](../catalog/catalog.json)<br>",
        "**Stored editions:** [`catalog/published-editions.json`](../catalog/published-editions.json)",
        "",
    ]
    for collection in sorted(grouped, key=lambda item: labels.get(item, item)):
        lines.extend([f"## {labels.get(collection, collection)}", "", "| Title | Author / publisher | Year | Local files | Sources |", "| --- | --- | ---: | --- | --- |"])
        for record in sorted(grouped[collection], key=lambda item: item.get("title", item["id"])):
            lines.append(
                "| {title} | {creator} | {year} | {files} | {sources} |".format(
                    title=table_cell(record.get("title")),
                    creator=table_cell(record.get("author") or record.get("publisher")),
                    year=table_cell(record.get("original_year")),
                    files=local_file_links(published_editions.get(record["id"], [])),
                    sources=source_links(source_options.get(record["id"], [])),
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
