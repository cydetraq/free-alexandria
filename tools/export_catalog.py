#!/usr/bin/env python3
"""Create the committed, dependency-free catalog exports for GitHub and API consumers."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records

API_PATH = CATALOG / "catalog.json"
MARKDOWN_PATH = ROOT / "docs" / "catalog.md"


def render_api() -> str:
    source_documents = {
        path.name: path.read_text()
        for path in sorted(CATALOG.glob("*.yaml"))
    }
    source_documents["published-editions.json"] = (CATALOG / "published-editions.json").read_text()
    payload = {
        "format_version": 1,
        "offline_notice": "This file is a complete metadata snapshot. It has no runtime dependency on external catalogs or URLs.",
        "normalized_records_notice": "The records field is a convenient V1 index. source_documents retains the complete, authoritative source text, including nested translation and acquisition details.",
        "records": sorted(load_records(), key=lambda item: item["id"]),
        "sources": sorted(load_records([CATALOG / "sources.yaml"], skip=set()), key=lambda item: item["id"]),
        "edition_queue": sorted(load_records([CATALOG / "edition-queue.yaml"], skip=set()), key=lambda item: item["id"]),
        "published_editions": json.loads((CATALOG / "published-editions.json").read_text()),
        "jurisdictional_access": json.loads((CATALOG / "jurisdictional-access.json").read_text()),
        "source_documents": source_documents,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def table_cell(value: object) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ")


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
    lines = [
        "# Catalog",
        "",
        "This is a committed, readable snapshot of the current Free Alexandria metadata catalog. It is useful offline after cloning the repository; it does not imply that every listed work has a locally mirrored file yet.",
        "",
        f"**Records:** {len(records)}<br>",
        "**Machine-readable export:** [`catalog/catalog.json`](../catalog/catalog.json)<br>",
        "**Source registry:** [`catalog/sources.yaml`](../catalog/sources.yaml)<br>",
        "**Edition acquisition queue:** [`catalog/edition-queue.yaml`](../catalog/edition-queue.yaml)",
        "",
    ]
    for collection in sorted(grouped, key=lambda item: labels.get(item, item)):
        lines.extend([f"## {labels.get(collection, collection)}", "", "| Title | Author / publisher | Year | Rights | Status |", "| --- | --- | ---: | --- | --- |"])
        for record in sorted(grouped[collection], key=lambda item: item.get("title", item["id"])):
            lines.append(
                "| {title} | {creator} | {year} | {rights} | {status} |".format(
                    title=table_cell(record.get("title")),
                    creator=table_cell(record.get("author") or record.get("publisher")),
                    year=table_cell(record.get("original_year")),
                    rights=table_cell(record.get("rights_status")),
                    status=table_cell(record.get("catalog_status", "candidate")),
                )
            )
        lines.append("")
    lines.extend([
        "## How to consume this catalog",
        "",
        "- Read this file for a GitHub-friendly inventory.",
        "- Use `catalog/catalog.json` as the stable V1 API for scripts and other catalog tools. Its `source_documents` field retains the complete authoritative YAML text.",
        "- Use the source YAML records for editorial detail, including translations and acquisition planning.",
        "- Use a profile in `profiles/` to create an offline catalog preview from a clone.",
        "",
    ])
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    if check:
        return path.exists() and path.read_text() == content
    path.write_text(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed exports are stale")
    args = parser.parse_args()
    records = load_records()
    api_ok = write_or_check(API_PATH, render_api(), args.check)
    markdown_ok = write_or_check(MARKDOWN_PATH, render_markdown(records), args.check)
    if not api_ok or not markdown_ok:
        print("Catalog exports are stale. Run: python3 tools/export_catalog.py", file=sys.stderr)
        return 1
    print("Catalog exports are current." if args.check else "Catalog exports written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
