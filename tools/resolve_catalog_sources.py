#!/usr/bin/env python3
"""Resolve exact Project Gutenberg editions into committed catalog source data."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import re
import urllib.parse
import urllib.request

from build_profile import CATALOG, load_records

OUT = CATALOG / "resolved-sources.json"
OVERRIDES = CATALOG / "source-overrides.json"
RESULT = re.compile(r'<li class="booklink">.*?href="/ebooks/(\d+)".*?<span class="title">(.*?)</span>.*?<span class="subtitle">(.*?)</span>.*?</li>', re.S)
LANGUAGE_SUFFIX = re.compile(r"\(([^)]+)\)\s*$", re.I)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def comparable_title(value: str) -> str:
    """Normalize harmless catalog-title differences without accepting unrelated works."""
    value = normalize(value)
    return re.sub(r"^(the|a|an) ", "", value)


def title_matches(record_title: str, source_title: str) -> bool:
    """Allow an exact work title or a clearly labeled expanded edition of it."""
    requested = comparable_title(record_title)
    offered = comparable_title(source_title)
    return offered == requested or offered.startswith(requested + " ")


def language_matches(record: dict, source_title: str) -> bool:
    """Avoid presenting a labeled foreign-language edition as an English source."""
    suffix = LANGUAGE_SUFFIX.search(source_title)
    if not suffix or record.get("original_language") != "English":
        return True
    return suffix.group(1).strip().lower() in {"english", "eng"}


def has_downloadable_text(item_id: str) -> bool:
    """Verify that at least one real Gutenberg EPUB or text endpoint is live."""
    for url in (
        f"https://www.gutenberg.org/ebooks/{item_id}.epub.images",
        f"https://www.gutenberg.org/ebooks/{item_id}.epub.noimages",
        f"https://www.gutenberg.org/cache/epub/{item_id}/pg{item_id}.txt",
    ):
        request = urllib.request.Request(url, headers={"User-Agent": "FreeAlexandria/1.0 source verifier", "Range": "bytes=0-31"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.read(1):
                    return True
        except Exception:
            continue
    return False


def libby_fallback(record: dict, author: str) -> dict:
    """Return the library handoff retained even when source resolution is offline."""
    search_terms = " ".join(part for part in (record["title"], author) if part)
    libby_query = urllib.parse.urlencode({"query": search_terms})
    return {"source_id":"libby","source_item_id":None,"source_url":f"https://libbyapp.com/search?{libby_query}","label":"Search in Libby","edition_title":record["title"],"edition_creator":author,"search_terms":search_terms,"resolution_method":"library-search-fallback"}


def resolve(record: dict) -> tuple[str, list[dict]]:
    author = record.get("author", "")
    overrides = json.loads(OVERRIDES.read_text()).get("records", {}).get(record["id"], []) if OVERRIDES.exists() else []
    query = urllib.parse.urlencode({"query": f"{record['title']} {author}"})
    request = urllib.request.Request(f"https://www.gutenberg.org/ebooks/search/?{query}", headers={"User-Agent": "FreeAlexandria/1.0 catalog resolver"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            page = response.read().decode("utf-8", "replace")
    except Exception:
        return record["id"], [*overrides, libby_fallback(record, author)]
    surname = normalize(author).split(" ")[-1:]
    options = list(overrides)
    for item_id, title, creator in RESULT.findall(page):
        title = html.unescape(re.sub(r"<.*?>", "", title)).strip()
        creator = html.unescape(re.sub(r"<.*?>", "", creator)).strip()
        if title_matches(record["title"], title) and language_matches(record, title) and (not surname or surname[0] in normalize(creator)) and has_downloadable_text(item_id):
            option = {"source_id":"project-gutenberg","source_item_id":item_id,"source_url":f"https://www.gutenberg.org/ebooks/{item_id}","label":"Project Gutenberg","edition_title":title,"edition_creator":creator,"resolution_method":"exact-title-and-creator-match"}
            if not any(existing.get("source_id") == option["source_id"] and existing.get("source_item_id") == option["source_item_id"] for existing in options):
                options.append(option)
    options.append(libby_fallback(record, author))
    return record["id"], options


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", action="append", help="Resolve only this catalog work ID; may be repeated")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    records = load_records()
    if args.work:
        wanted = set(args.work)
        records = [record for record in records if record["id"] in wanted]
        missing = wanted - {record["id"] for record in records}
        if missing:
            parser.error("unknown work ID: " + ", ".join(sorted(missing)))
    result = json.loads(OUT.read_text()) if OUT.exists() else {"format_version": 1, "records": {}}
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for work_id, options in pool.map(resolve, records):
            result["records"][work_id] = {"resolved_at": timestamp, "source_options": options}
            print(f"RESOLVED {work_id}: {len(options)} exact Project Gutenberg edition(s)")
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
