#!/usr/bin/env python3
"""Add a source-faithful PDF scan as an optional local edition.

The scan is rejected above GitHub's 100 MB single-file limit. It is stored beside
the normal reading edition, with independent provenance, so the offline release
can offer both a compact reading PDF and a facsimile of the source volume.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records

GITHUB_FILE_LIMIT = 100 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_id")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-item-id", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--edition-page", required=True)
    parser.add_argument("--download-url", required=True)
    parser.add_argument("--language", default="English")
    parser.add_argument("--registry", type=Path, default=CATALOG / "published-editions.json")
    args = parser.parse_args()

    records = {record["id"]: record for record in load_records()}
    record = records.get(args.work_id)
    if not record:
        parser.error(f"unknown work ID: {args.work_id}")

    edition_dir = ROOT / "content" / "books" / args.work_id / f"{args.source_id}-{args.source_item_id}"
    edition_dir.mkdir(parents=True, exist_ok=True)
    pdf = edition_dir / "facsimile.pdf"
    request = urllib.request.Request(args.download_url, headers={"User-Agent": "FreeAlexandria/1.0 facsimile curator"})
    with urllib.request.urlopen(request, timeout=120) as response, pdf.open("wb") as output:
        shutil.copyfileobj(response, output)
    if pdf.stat().st_size == 0 or pdf.stat().st_size > GITHUB_FILE_LIMIT:
        pdf.unlink(missing_ok=True)
        parser.error("facsimile must be a nonempty PDF at or below GitHub's 100 MB single-file limit")
    if pdf.read_bytes()[:5] != b"%PDF-":
        pdf.unlink(missing_ok=True)
        parser.error("download did not produce a PDF")

    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    relative_pdf = str(pdf.relative_to(ROOT))
    edition_id = f"{args.work_id}-{args.language.lower()}-facsimile-{args.source_id}-{args.source_item_id}"
    file = {"role": "facsimile-pdf", "path": relative_pdf, "sha256": sha256(pdf), "bytes": pdf.stat().st_size}
    provenance = edition_dir / "provenance.json"
    provenance.write_text(json.dumps({
        "format_version": 1, "work_id": args.work_id, "edition_id": edition_id,
        "source": {"name": args.source_name, "item_id": args.source_item_id, "edition_page": args.edition_page, "download_url": args.download_url, "acquired_at": timestamp},
        "files": [file], "operator_note": "Source-faithful PDF scan retained as an optional facsimile alongside the compact reading edition."
    }, indent=2) + "\n")
    registry = json.loads(args.registry.read_text())
    edition = {"edition_id": edition_id, "language": args.language, "source_id": args.source_id, "source_item_id": args.source_item_id, "provenance_path": str(provenance.relative_to(ROOT)), "rights_review": {"status": "operator-selected", "basis": "Operator-selected source-faithful scan; source page and local provenance retained.", "reviewed_at": dt.date.today().isoformat(), "evidence_url": args.edition_page}, "files": [file]}
    editions = registry.setdefault("editions", {}).setdefault(args.work_id, [])
    registry["editions"][args.work_id] = [item for item in editions if item.get("edition_id") != edition_id] + [edition]
    args.registry.write_text(json.dumps(registry, indent=2) + "\n")
    print(f"ADDED {record['title']} facsimile: {args.source_name} {args.source_item_id} ({file['bytes']} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
