#!/usr/bin/env python3
"""Replace generated text PDFs with Internet Archive facsimile scans.

The script discovers unrestricted pre-1931 scanned editions for every catalog
record that still exposes a ``text-pdf`` and has no ``facsimile-pdf``. It then:

* downloads and validates the selected PDF;
* stores it under ``content/books/<work>/internet-archive-<identifier>/``;
* writes provenance metadata;
* removes the generated PDF from the repository working tree;
* updates ``catalog/catalog.json`` and ``catalog/published-editions.json``;
* updates reader-facing links in ``docs/catalog.md``; and
* writes a machine-readable acquisition report.

No third-party packages are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "catalog.json"
EDITIONS_PATH = ROOT / "catalog" / "published-editions.json"
DOC_PATH = ROOT / "docs" / "catalog.md"
REPORT_PATH = ROOT / "catalog" / "facsimile-acquisition-report.json"
IA_ADVANCED_SEARCH = "https://archive.org/advancedsearch.php"
IA_METADATA = "https://archive.org/metadata/{identifier}"
IA_DOWNLOAD = "https://archive.org/download/{identifier}/{filename}"
USER_AGENT = "Free-Alexandria-Facsimile-Acquirer/1.0"
MAX_PDF_BYTES = 99_000_000
MIN_PDF_BYTES = 100_000
PUBLIC_DOMAIN_CUTOFF = 1930


def request_bytes(url: str, timeout: int = 90) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def request_json(url: str, timeout: int = 90) -> dict[str, Any]:
    return json.loads(request_bytes(url, timeout).decode("utf-8"))


def normalize(value: Any) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold())
    return " ".join(value.split())


def similarity(left: Any, right: Any) -> float:
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def first_year(value: Any) -> int | None:
    match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(value or ""))
    return int(match.group(1)) if match else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def internet_archive_search(title: str, author: str, rows: int = 50) -> list[dict[str, Any]]:
    escaped_title = title.replace('"', "")
    escaped_author = author.replace('"', "")
    queries = [
        f'title:("{escaped_title}") AND creator:("{escaped_author}") AND mediatype:texts',
        f'title:("{escaped_title}") AND mediatype:texts',
    ]
    found: dict[str, dict[str, Any]] = {}
    for query in queries:
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "creator", "date", "year", "language", "downloads"],
            "rows": str(rows),
            "page": "1",
            "output": "json",
            "sort[]": "downloads desc",
        }
        payload = request_json(f"{IA_ADVANCED_SEARCH}?{urlencode(params, doseq=True)}")
        for doc in payload.get("response", {}).get("docs", []):
            identifier = str(doc.get("identifier", ""))
            if identifier:
                found.setdefault(identifier, doc)
        if found:
            break
    return list(found.values())


def choose_pdf_file(files: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for file in files:
        name = str(file.get("name", ""))
        lower = name.casefold()
        if not lower.endswith(".pdf"):
            continue
        if any(fragment in lower for fragment in ("_text.pdf", "searchtext", "encrypted", "restricted")):
            continue
        try:
            size = int(file.get("size", 0))
        except (TypeError, ValueError):
            size = 0
        if size and not (MIN_PDF_BYTES <= size <= MAX_PDF_BYTES):
            continue
        source = str(file.get("source", ""))
        format_name = str(file.get("format", ""))
        score = 0
        if source == "original":
            score += 40
        if "text pdf" not in format_name.casefold():
            score += 20
        if "bw" not in lower:
            score += 5
        if "djvu" not in lower:
            score += 5
        candidates.append((score, -size, file))
    return max(candidates, default=(0, 0, None), key=lambda item: (item[0], item[1]))[2]


def candidate_score(record: dict[str, Any], doc: dict[str, Any], metadata: dict[str, Any]) -> float:
    title = record.get("title", "")
    author = record.get("author", "")
    score = similarity(title, metadata.get("title") or doc.get("title")) * 70
    score += similarity(author, metadata.get("creator") or doc.get("creator")) * 25
    language = normalize(metadata.get("language") or doc.get("language"))
    if not language or "english" in language or language == "eng":
        score += 5
    year = first_year(metadata.get("date") or metadata.get("year") or doc.get("date") or doc.get("year"))
    if year is not None and year <= PUBLIC_DOMAIN_CUTOFF:
        score += 15
    elif year is not None:
        score -= 100
    if str(metadata.get("access-restricted-item", "false")).casefold() == "true":
        score -= 100
    return score


def discover_scan(record: dict[str, Any]) -> dict[str, Any] | None:
    best: tuple[float, dict[str, Any]] | None = None
    for doc in internet_archive_search(record["title"], record.get("author", "")):
        identifier = str(doc["identifier"])
        try:
            payload = request_json(IA_METADATA.format(identifier=quote(identifier, safe="")))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata", {})
        year = first_year(metadata.get("date") or metadata.get("year") or doc.get("date") or doc.get("year"))
        if year is not None and year > PUBLIC_DOMAIN_CUTOFF:
            continue
        if str(metadata.get("access-restricted-item", "false")).casefold() == "true":
            continue
        pdf = choose_pdf_file(payload.get("files", []))
        if not pdf:
            continue
        score = candidate_score(record, doc, metadata)
        if score < 62:
            continue
        selection = {
            "identifier": identifier,
            "filename": pdf["name"],
            "title": metadata.get("title") or doc.get("title") or record["title"],
            "creator": metadata.get("creator") or doc.get("creator") or record.get("author"),
            "year": year,
            "publisher": metadata.get("publisher"),
            "language": metadata.get("language") or doc.get("language") or record.get("original_language") or "English",
            "score": round(score, 3),
        }
        if best is None or score > best[0]:
            best = (score, selection)
        time.sleep(0.15)
    return best[1] if best else None


def download_pdf(selection: dict[str, Any], destination: Path) -> tuple[str, int, str]:
    identifier = selection["identifier"]
    filename = selection["filename"]
    url = IA_DOWNLOAD.format(identifier=quote(identifier, safe=""), filename=quote(filename))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(".part")
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=180) as response, temp.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    size = temp.stat().st_size
    if not (MIN_PDF_BYTES <= size <= MAX_PDF_BYTES):
        temp.unlink(missing_ok=True)
        raise RuntimeError(f"downloaded PDF size {size} is outside permitted range")
    with temp.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            temp.unlink(missing_ok=True)
            raise RuntimeError("download is not a PDF")
    temp.replace(destination)
    return sha256_file(destination), size, url


def has_role(record: dict[str, Any], role: str) -> bool:
    return any(file.get("role") == role for file in record.get("download_files", []))


def add_facsimile_to_record(record: dict[str, Any], selection: dict[str, Any], relative_path: str, digest: str, size: int) -> None:
    old_files = record.get("download_files", [])
    for old in old_files:
        if old.get("role") == "text-pdf":
            old_path = ROOT / str(old.get("path", ""))
            old_path.unlink(missing_ok=True)
    record["download_files"] = [file for file in old_files if file.get("role") != "text-pdf"]
    record["download_files"].append({"role": "facsimile-pdf", "path": relative_path, "sha256": digest, "bytes": size})
    sources = record.setdefault("edition_sources", [])
    for source in sources:
        source["primary"] = False
    identifier = selection["identifier"]
    sources.append({
        "source_id": "internet-archive",
        "source_item_id": identifier,
        "label": "Internet Archive scanned facsimile",
        "url": f"https://archive.org/details/{identifier}",
        "edition_id": f"{record['id']}-facsimile-internet-archive-{identifier}",
        "primary": True,
    })


def add_published_edition(registry: dict[str, Any], record: dict[str, Any], selection: dict[str, Any], provenance_path: str, relative_path: str, digest: str, size: int) -> None:
    identifier = selection["identifier"]
    editions = registry.setdefault("editions", {}).setdefault(record["id"], [])
    editions[:] = [edition for edition in editions if edition.get("source_id") != "internet-archive" or edition.get("source_item_id") != identifier]
    editions.append({
        "edition_id": f"{record['id']}-facsimile-internet-archive-{identifier}",
        "language": selection.get("language") or record.get("original_language") or "English",
        "source_id": "internet-archive",
        "source_item_id": identifier,
        "provenance_path": provenance_path,
        "rights_review": {
            "status": "operator-selected",
            "basis": "Automated selection of an unrestricted pre-1931 source-faithful scan; source page and local provenance retained.",
            "reviewed_at": time.strftime("%Y-%m-%d", time.gmtime()),
            "evidence_url": f"https://archive.org/details/{identifier}",
        },
        "files": [{"role": "facsimile-pdf", "path": relative_path, "sha256": digest, "bytes": size}],
    })


def write_provenance(path: Path, record: dict[str, Any], selection: dict[str, Any], relative_path: str, digest: str, size: int, download_url: str) -> None:
    payload = {
        "format_version": 1,
        "work_id": record["id"],
        "title": record["title"],
        "edition": {
            "language": selection.get("language") or record.get("original_language") or "English",
            "publication_year": selection.get("year"),
            "publisher": selection.get("publisher"),
            "creator": selection.get("creator"),
            "source_id": "internet-archive",
            "source_item_id": selection["identifier"],
            "source_url": f"https://archive.org/details/{selection['identifier']}",
            "download_url": download_url,
            "selection_score": selection["score"],
        },
        "rights_review": {
            "status": "operator-selected",
            "basis": "Unrestricted pre-1931 scanned edition selected from Internet Archive metadata.",
            "reviewed_at": time.strftime("%Y-%m-%d", time.gmtime()),
            "evidence_url": f"https://archive.org/details/{selection['identifier']}",
        },
        "files": [{"role": "facsimile-pdf", "path": relative_path, "sha256": digest, "bytes": size}],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_markdown(doc: str, record: dict[str, Any], old_paths: list[str], new_path: str) -> str:
    for old_path in old_paths:
        old_link = "../" + old_path
        doc = doc.replace(f"[Text PDF]({old_link})", f"[PDF](../{new_path})")
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="maximum replacements; 0 means all")
    parser.add_argument("--allow-unresolved", action="store_true", help="commit successful replacements even if some titles remain unresolved")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    editions = json.loads(EDITIONS_PATH.read_text(encoding="utf-8"))
    markdown = DOC_PATH.read_text(encoding="utf-8")
    targets = [record for record in catalog.get("records", []) if has_role(record, "text-pdf") and not has_role(record, "facsimile-pdf")]
    if args.limit:
        targets = targets[: args.limit]

    completed: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for index, record in enumerate(targets, 1):
        print(f"[{index}/{len(targets)}] {record['title']}", flush=True)
        old_paths = [str(file["path"]) for file in record.get("download_files", []) if file.get("role") == "text-pdf"]
        try:
            selection = discover_scan(record)
            if not selection:
                unresolved.append({"id": record["id"], "title": record["title"], "reason": "no sufficiently strong unrestricted pre-1931 scan found"})
                continue
            identifier = selection["identifier"]
            directory = ROOT / "content" / "books" / record["id"] / f"internet-archive-{identifier}"
            pdf_path = directory / "facsimile.pdf"
            relative_pdf = pdf_path.relative_to(ROOT).as_posix()
            relative_provenance = (directory / "provenance.json").relative_to(ROOT).as_posix()
            if args.dry_run:
                print(f"  would use {identifier}: {selection['filename']} (score {selection['score']})")
                completed.append({"id": record["id"], **selection, "dry_run": True})
                continue
            digest, size, download_url = download_pdf(selection, pdf_path)
            write_provenance(directory / "provenance.json", record, selection, relative_pdf, digest, size, download_url)
            add_facsimile_to_record(record, selection, relative_pdf, digest, size)
            add_published_edition(editions, record, selection, relative_provenance, relative_pdf, digest, size)
            markdown = update_markdown(markdown, record, old_paths, relative_pdf)
            completed.append({"id": record["id"], "title": record["title"], **selection, "path": relative_pdf, "sha256": digest, "bytes": size})
            print(f"  stored {relative_pdf} ({size:,} bytes)")
        except Exception as exc:
            unresolved.append({"id": record["id"], "title": record["title"], "reason": f"{type(exc).__name__}: {exc}"})

    report = {
        "format_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_count": len(targets),
        "completed_count": len(completed),
        "unresolved_count": len(unresolved),
        "completed": completed,
        "unresolved": unresolved,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not args.dry_run:
        CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        EDITIONS_PATH.write_text(json.dumps(editions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        DOC_PATH.write_text(markdown, encoding="utf-8")

    print(json.dumps({"completed": len(completed), "unresolved": len(unresolved)}, indent=2))
    if unresolved and not args.allow_unresolved:
        print("Unresolved titles remain; see catalog/facsimile-acquisition-report.json", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
