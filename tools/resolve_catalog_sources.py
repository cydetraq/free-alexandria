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
RESULT = re.compile(r'<li class="booklink">.*?href="/ebooks/(\d+)".*?<span class="title">(.*?)</span>.*?<span class="subtitle">(.*?)</span>.*?</li>', re.S)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def resolve(record: dict) -> tuple[str, list[dict]]:
    author = record.get("author", "")
    query = urllib.parse.urlencode({"query": f"{record['title']} {author}"})
    request = urllib.request.Request(f"https://www.gutenberg.org/ebooks/search/?{query}", headers={"User-Agent": "FreeAlexandria/1.0 catalog resolver"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            page = response.read().decode("utf-8", "replace")
    except Exception:
        return record["id"], []
    surname = normalize(author).split(" ")[-1:]
    options = []
    for item_id, title, creator in RESULT.findall(page):
        title = html.unescape(re.sub(r"<.*?>", "", title)).strip()
        creator = html.unescape(re.sub(r"<.*?>", "", creator)).strip()
        if normalize(title) == normalize(record["title"]) and (not surname or surname[0] in normalize(creator)):
            options.append({"source_id":"project-gutenberg","source_item_id":item_id,"source_url":f"https://www.gutenberg.org/ebooks/{item_id}","label":"Project Gutenberg","edition_title":title,"edition_creator":creator,"resolution_method":"exact-title-and-creator-match"})
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
