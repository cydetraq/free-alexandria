#!/usr/bin/env python3
"""Acquire approved Project Gutenberg editions into an offline Free Alexandria workspace.

This intentionally small importer is for the explicit Gutenberg records in
catalog/edition-queue.yaml.  It downloads the canonical EPUB, derives a simple
searchable PDF from Gutenberg's UTF-8 text, and writes offline provenance with
hashes and an acquisition timestamp.  It does not publish anything to Git and
does not decide copyright law: the queue entry must already be edition-identified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "catalog" / "edition-queue.yaml"


def parse_queue() -> list[dict]:
    """Parse the deliberately limited queue YAML without adding a runtime dependency."""
    records: list[dict] = []
    current: dict | None = None
    paths: dict | None = None
    for raw in QUEUE.read_text().splitlines():
        if raw.startswith("- id: "):
            if current:
                records.append(current)
            current = {"id": raw.split(": ", 1)[1]}
            paths = None
            continue
        if current is None or not raw or raw.lstrip().startswith("#"):
            continue
        if raw == "  intended_paths:":
            paths = {}
            current["intended_paths"] = paths
            continue
        if raw.startswith("    ") and paths is not None and ": " in raw:
            key, value = raw.strip().split(": ", 1)
            paths[key] = value.strip("'\"")
        elif raw.startswith("  ") and ": " in raw:
            key, value = raw.strip().split(": ", 1)
            current[key] = value.strip("'\"")
    if current:
        records.append(current)
    return records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "FreeAlexandria/1.0 acquisition tool"})
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def approved(record: dict) -> bool:
    # Queue membership is editorial review. Gutenberg records are allowed here only when they
    # are a pre-1931 candidate or the queue contains source-specific rights evidence.
    return record.get("source_id") == "project-gutenberg" and record.get("acquisition_status") == "edition-identified"


def acquire(record: dict, root: Path) -> dict:
    source_id = record["source_item_id"]
    if not source_id.isdigit():
        raise ValueError(f"{record['id']}: non-numeric Gutenberg item id")
    paths = record.get("intended_paths", {})
    if "epub" not in paths:
        raise ValueError(f"{record['id']}: an EPUB destination is required")
    epub = root / paths["epub"]
    pdf = root / paths.get("pdf", str(Path(paths["epub"]).with_name("book.pdf")))
    provenance = epub.parent / "provenance.json"
    epub.parent.mkdir(parents=True, exist_ok=True)
    epub_url = f"https://www.gutenberg.org/ebooks/{source_id}.epub.images"
    text_url = f"https://www.gutenberg.org/cache/epub/{source_id}/pg{source_id}.txt"
    fetch(epub_url, epub)
    with tempfile.TemporaryDirectory(prefix="free-alexandria-") as directory:
        text = Path(directory) / f"pg{source_id}.txt"
        fetch(text_url, text)
        with pdf.open("wb") as output:
            completed = subprocess.run(
                ["/usr/sbin/cupsfilter", "-m", "application/pdf", str(text)],
                stdout=output,
                stderr=subprocess.PIPE,
                text=True,
            )
        if completed.returncode:
            raise RuntimeError(f"{record['id']}: PDF conversion failed: {completed.stderr.strip()}")
    acquired_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "format_version": 1,
        "work_id": record["work_id"],
        "edition_id": record["id"],
        "source": {
            "name": "Project Gutenberg",
            "item_id": source_id,
            "edition_page": record.get("source_url", f"https://www.gutenberg.org/ebooks/{source_id}"),
            "epub_url": epub_url,
            "text_url_used_for_pdf": text_url,
            "acquired_at": acquired_at,
        },
        "files": [
            {"path": str(epub.relative_to(root)), "bytes": epub.stat().st_size, "sha256": sha256(epub), "format": "epub"},
            {"path": str(pdf.relative_to(root)), "bytes": pdf.stat().st_size, "sha256": sha256(pdf), "format": "pdf", "derived_from": text_url},
        ],
        "rights_note": "This acquisition tool is limited to explicitly reviewed Project Gutenberg queue records. Confirm the edition's rights statement and preserve any required source notice before publishing a distribution.",
    }
    provenance.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", action="append", help="Queue edition ID; may be supplied more than once.")
    parser.add_argument("--all-approved", action="store_true", help="Select every approved Project Gutenberg queue record.")
    parser.add_argument("--acquire", action="store_true", help="Perform downloads. Without this flag, print an offline-safe plan only.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Workspace root receiving content (default: repository root).")
    args = parser.parse_args()
    if not args.edition and not args.all_approved:
        parser.error("select --edition ID or --all-approved")
    records = parse_queue()
    requested = set(args.edition or [])
    selected = [record for record in records if (args.all_approved and approved(record)) or record["id"] in requested]
    unknown = requested - {record["id"] for record in records}
    if unknown:
        parser.error("unknown queue ID: " + ", ".join(sorted(unknown)))
    rejected = [record["id"] for record in selected if not approved(record)]
    if rejected:
        parser.error("not an approved Project Gutenberg acquisition: " + ", ".join(rejected))
    if not selected:
        parser.error("no approved Project Gutenberg editions selected")
    if not args.acquire:
        for record in selected:
            print(f"PLAN {record['id']} -> {record['intended_paths'].get('epub')}")
        print("No files downloaded. Re-run with --acquire after confirming local legal eligibility.")
        return 0
    for record in selected:
        payload = acquire(record, args.root.resolve())
        print(f"ACQUIRED {record['id']}: {len(payload['files'])} files with provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
