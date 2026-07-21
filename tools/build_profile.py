#!/usr/bin/env python3
"""Build a self-contained offline distribution and a reproducible curation lockfile.

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
SKIP = {"tags.yaml", "sources.yaml"}
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


def load_source_options() -> dict[str, list[dict]]:
    """Read exact edition-level source URLs resolved into catalog data."""
    path = CATALOG / "resolved-sources.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {
        work_id: [
            {
                "source_id": option["source_id"],
                "edition_id": option["source_item_id"],
                "url": option["source_url"],
                "label": option["label"],
                "edition_title": option.get("edition_title"),
                "edition_creator": option.get("edition_creator"),
                "search_terms": option.get("search_terms"),
                "resolution_method": option.get("resolution_method"),
            }
            for option in entry.get("source_options", [])
        ]
        for work_id, entry in data.get("records", {}).items()
    }


def load_collections() -> list[dict]:
    """Return the canonical, ordered collection taxonomy for every export."""
    return json.loads((CATALOG / "collections.json").read_text()).get("collections", [])


def reader_metadata(record: dict) -> dict:
    """Provide complete reader-facing text without exposing blank catalog fields."""
    enriched = dict(record)
    relevance = str(record.get("civilian_relevance") or "").strip()
    if not enriched.get("description") and relevance:
        enriched["description"] = relevance
    if not enriched.get("why_included") and relevance:
        enriched["why_included"] = relevance
    if not enriched.get("original_language") and record.get("publisher") == "United States Army":
        enriched["original_language"] = "English"
    return enriched


SOURCE_LABELS = {
    "project-gutenberg": "Project Gutenberg",
    "internet-archive": "Internet Archive",
    "library-of-congress": "Library of Congress",
    "standard-ebooks": "Standard Ebooks",
}


def edition_sources(editions: list[dict]) -> list[dict]:
    """Return only the sources for editions actually included in an archive."""
    sources: list[dict] = []
    seen: set[str] = set()
    for edition in editions:
        url = edition.get("rights_review", {}).get("evidence_url")
        if not url or url in seen:
            continue
        seen.add(url)
        source_id = edition.get("source_id", "source")
        sources.append({
            "source_id": source_id,
            "source_item_id": edition.get("source_item_id"),
            "label": SOURCE_LABELS.get(source_id, source_id.replace("-", " ").title()),
            "url": url,
            "edition_id": edition.get("edition_id"),
            "primary": not sources,
        })
    return sources


def presentation_files(editions: list[dict], preferences: list[str] | None = None) -> tuple[dict | None, list[dict], list[dict]]:
    """Choose one reader EPUB and one PDF for the user-facing archive.

    A source-faithful facsimile wins the PDF slot. The generated text PDF remains
    a clearly named fallback only when no scan has been supplied.
    """
    preferences = preferences or []
    primary = next((item for language in preferences for item in editions if item["language"] == language), None)
    primary = primary or (editions[0] if editions else None)
    if not primary:
        return None, [], []
    facsimiles = [item for item in editions if item is not primary and any(file.get("role") == "facsimile-pdf" for file in item.get("files", []))]
    epub = next((file for file in primary.get("files", []) if file.get("role") == "epub"), None)
    text_pdf = next((file for file in primary.get("files", []) if file.get("role") == "pdf"), None)
    scan = next((file for edition in facsimiles for file in edition.get("files", []) if file.get("role") == "facsimile-pdf"), None)
    files = []
    if epub:
        files.append({**epub, "role": "epub"})
    if scan:
        files.append({**scan, "role": "pdf"})
    elif text_pdf:
        files.append({**text_pdf, "role": "text-pdf"})
    return primary, [primary, *facsimiles], files


def rights_guidance(record: dict, options: list[dict]) -> dict:
    """Reader-facing evidence signals; these are intentionally not legal conclusions."""
    year = record.get("original_year")
    language = record.get("original_language")
    notes = []
    if options:
        notes.append("The source for the included edition is recorded with this archive; inspect that source's own rights statement before use.")
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
    return {"not_a_legal_ruling": True, "signal": signal, "evidence_notes": notes, "operator_question": "May I download, keep, share, or publish this specific edition where and how I intend to use it?"}


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


def resolve_editions(profile: dict, records: list[dict], registry_path: Path = CATALOG / "published-editions.json") -> dict[str, dict]:
    registry = json.loads(registry_path.read_text()).get("editions", {})
    preferences = profile.get("language_preferences", [])
    resolved: dict[str, dict] = {}
    missing: list[str] = []
    for record in records:
        editions = registry.get(record["id"], [])
        primary, selected_editions, files = presentation_files(editions, preferences)
        if not primary:
            missing.append(record["id"])
            continue
        rights_review = primary.get("rights_review", {})
        if not rights_review.get("basis") or not rights_review.get("reviewed_at"):
            raise ValueError(f"missing local eligibility evidence for {record['id']}")
        provenance_paths = []
        for edition in selected_editions:
            provenance_path = ROOT / edition.get("provenance_path", "")
            if not provenance_path.is_file():
                raise ValueError(f"missing local provenance record for {record['id']}: {edition.get('provenance_path')}")
            provenance_paths.append(edition["provenance_path"])
            for file in edition["files"]:
                path = ROOT / file["path"]
                if not path.is_file():
                    raise ValueError(f"missing local file for {record['id']}: {file['path']}")
                if path.stat().st_size != file["bytes"]:
                    raise ValueError(f"size mismatch for {record['id']}: {file['path']}")
                if digest(path) != file["sha256"]:
                    raise ValueError(f"checksum mismatch for {record['id']}: {file['path']}")
        for file in files:
            path = ROOT / file["path"]
            if not path.is_file():
                raise ValueError(f"missing selected local file for {record['id']}: {file['path']}")
            if path.stat().st_size != file["bytes"] or digest(path) != file["sha256"]:
                raise ValueError(f"invalid selected local file for {record['id']}: {file['path']}")
        resolved[record["id"]] = {**primary, "files": files, "provenance_paths": provenance_paths, "source_editions": selected_editions, "edition_sources": edition_sources(selected_editions)}
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
    parser.add_argument("--edition-registry", type=Path, default=CATALOG / "published-editions.json", help="Edition registry for a private distribution build")
    args = parser.parse_args()

    profile = json.loads(args.profile.read_text())
    if profile.get("build_mode") != "distribution":
        raise ValueError("Free Alexandria builds only downloadable distribution profiles")
    if not profile["constraints"].get("require_local_files") or profile["constraints"].get("allow_link_only"):
        raise ValueError("distribution profiles require local files and cannot include link-only records")
    records = [reader_metadata(record) for record in select(profile, load_records())]
    editions = resolve_editions(profile, records, args.edition_registry)
    records = [{**record, "edition_sources": editions[record["id"]]["edition_sources"], "rights_guidance": rights_guidance(record, editions[record["id"]]["edition_sources"])} for record in records]
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
        "collections": load_collections(),
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
        for provenance_path in edition.get("provenance_paths", [edition.get("provenance_path")]):
            if not provenance_path:
                continue
            destination = output / provenance_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / provenance_path, destination)
    print(f"Built {profile['build_mode']} for {profile['id']}: {len(records)} records -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
