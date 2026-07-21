#!/usr/bin/env python3
"""Populate a private archive from a Free Alexandria selection.

The tool resolves selected works against an exact-title Project Gutenberg result.
It deliberately skips ambiguous or unmatched results. Acquired editions live in the
normal human-browsable content tree and are registered in a private local registry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from build_profile import ROOT, load_records, load_source_options

RESULT = re.compile(r'<li class="booklink">.*?href="/ebooks/(\d+)".*?<span class="title">(.*?)</span>.*?<span class="subtitle">(.*?)</span>.*?</li>', re.S)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, destination: Path | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "FreeAlexandria/1.0 local archive builder"})
    with urllib.request.urlopen(request, timeout=90) as response:
        if destination is None:
            return response.read()
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    if destination.stat().st_size == 0:
        raise RuntimeError(f"empty response from {url}")
    return b""


def make_epub(text: Path, destination: Path, title: str, creator: str) -> None:
    body = "\n".join(f"<p>{html.escape(line)}</p>" for line in text.read_text(errors="replace").splitlines() if line.strip())
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", "<?xml version='1.0'?><container version='1.0' xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OEBPS/content.opf' media-type='application/oebps-package+xml'/></rootfiles></container>")
        archive.writestr("OEBPS/content.xhtml", f"<?xml version='1.0' encoding='utf-8'?><html xmlns='http://www.w3.org/1999/xhtml'><head><title>{html.escape(title)}</title></head><body><h1>{html.escape(title)}</h1>{body}</body></html>")
        archive.writestr("OEBPS/content.opf", f"<?xml version='1.0'?><package xmlns='http://www.idpf.org/2007/opf' version='3.0' unique-identifier='book'><metadata xmlns:dc='http://purl.org/dc/elements/1.1/'><dc:identifier id='book'>free-alexandria</dc:identifier><dc:title>{html.escape(title)}</dc:title><dc:creator>{html.escape(creator)}</dc:creator><dc:language>en</dc:language></metadata><manifest><item id='text' href='content.xhtml' media-type='application/xhtml+xml'/></manifest><spine><itemref idref='text'/></spine></package>")


def resolve(record: dict) -> dict | None:
    query = urllib.parse.urlencode({"query": f"{record['title']} {record.get('author', '')}"})
    page = fetch(f"https://www.gutenberg.org/ebooks/search/?{query}").decode("utf-8", "replace")
    surname = normalize(record.get("author", "")).split(" ")[-1:]
    for item_id, title, creator in RESULT.findall(page):
        title = html.unescape(re.sub(r"<.*?>", "", title)).strip()
        creator = html.unescape(re.sub(r"<.*?>", "", creator)).strip()
        if normalize(title) == normalize(record["title"]) and (not surname or surname[0] in normalize(creator)):
            return {"item_id": item_id, "title": title, "creator": creator, "url": f"https://www.gutenberg.org/ebooks/{item_id}"}
    return None


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"format_version": 1, "editions": {}}


def acquire(record: dict, source: dict, root: Path, registry: dict) -> None:
    item_id = source["item_id"]
    edition_dir = root / "content" / "books" / record["id"] / f"en-source-{record.get('original_year', 'undated')}--gutenberg-{item_id}"
    epub = edition_dir / "book.epub"
    pdf = edition_dir / "book.pdf"
    provenance = edition_dir / "provenance.json"
    edition_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="free-alexandria-") as temporary:
        text = Path(temporary) / f"pg{item_id}.txt"
        text_url = f"https://www.gutenberg.org/cache/epub/{item_id}/pg{item_id}.txt"
        try:
            fetch(f"https://www.gutenberg.org/ebooks/{item_id}.epub.images", epub)
            if not zipfile.is_zipfile(epub):
                raise RuntimeError("source did not return an EPUB file")
        except Exception:
            try:
                fetch(f"https://www.gutenberg.org/ebooks/{item_id}.epub.noimages", epub)
                if not zipfile.is_zipfile(epub):
                    raise RuntimeError("source did not return an EPUB file")
            except Exception:
                fetch(text_url, text)
                make_epub(text, epub, record["title"], record.get("author", record.get("publisher", "")))
        if not text.exists():
            fetch(text_url, text)
        with pdf.open("wb") as output:
            completed = subprocess.run(["/usr/sbin/cupsfilter", "-m", "application/pdf", str(text)], stdout=output, stderr=subprocess.PIPE, text=True)
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip())
    files = [
        {"role": "epub", "path": str(epub.relative_to(root)), "sha256": sha256(epub), "bytes": epub.stat().st_size},
        {"role": "pdf", "path": str(pdf.relative_to(root)), "sha256": sha256(pdf), "bytes": pdf.stat().st_size},
    ]
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    edition_id = f"{record['id']}-en-source-{record.get('original_year', 'undated')}-gutenberg-{item_id}"
    provenance.write_text(json.dumps({
        "format_version": 1, "work_id": record["id"], "edition_id": edition_id,
        "source": {"name": "Project Gutenberg", "item_id": item_id, "edition_page": source["url"], "acquired_at": timestamp},
        "files": files,
        "operator_note": "Created by the private archive population tool from an exact-title Project Gutenberg result selected by the operator."
    }, indent=2) + "\n")
    registry["editions"][record["id"]] = [{
        "edition_id": edition_id, "language": "English", "source_id": "project-gutenberg", "source_item_id": item_id,
        "provenance_path": str(provenance.relative_to(root)),
        "rights_review": {"status": "operator-selected", "basis": "Operator-selected exact Project Gutenberg source; source and edition evidence retained locally.", "reviewed_at": dt.date.today().isoformat(), "evidence_url": source["url"]},
        "files": files
    }]
    print(f"ACQUIRED {record['title']} — Gutenberg {item_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("selection", type=Path, nargs="?", help="Selection JSON exported from the offline portal")
    parser.add_argument("--all-catalog", action="store_true", help="Use every record in the catalog that has a stored exact Project Gutenberg source")
    parser.add_argument("--work", action="append", help="Populate only this catalog work ID; may be repeated")
    parser.add_argument("--acquire", action="store_true", help="Download exact matches into this private archive")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=ROOT / "catalog" / "local-editions.json")
    args = parser.parse_args()
    records = {record["id"]: record for record in load_records()}
    resolved_sources = load_source_options()
    if not args.all_catalog and args.selection is None and not args.work:
        parser.error("provide a selection file, --work, or use --all-catalog")
    wanted = set(args.work) if args.work else (set(records) if args.all_catalog else set(json.loads(args.selection.read_text()).get("selected_record_ids", [])))
    for work_id in sorted(wanted):
        record = records.get(work_id)
        if not record:
            print(f"SKIP {work_id}: not in catalog")
            continue
        options = resolved_sources.get(work_id, [])
        option = next((item for item in options if item["label"] == "Project Gutenberg"), None)
        if not option:
            print(f"SKIP {record['title']}: no exact stored Project Gutenberg edition")
            continue
        source = {"item_id": option["edition_id"], "url": option["url"]}
        if not args.acquire:
            print(f"PLAN {record['title']} -> Project Gutenberg {source['item_id']} ({source['url']})")
            continue
        registry = load_registry(args.registry)
        try:
            acquire(record, source, args.root.resolve(), registry)
        except Exception as error:
            print(f"ERROR {record['title']}: {error}")
            continue
        args.registry.parent.mkdir(parents=True, exist_ok=True)
        args.registry.write_text(json.dumps(registry, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
