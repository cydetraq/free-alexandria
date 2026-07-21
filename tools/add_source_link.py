#!/usr/bin/env python3
"""Add one ad-hoc source link directly to a catalog work's resolved source list."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from build_profile import CATALOG, load_records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_id")
    parser.add_argument("url")
    parser.add_argument("--label", required=True, help="Reader-facing source label, for example 'Library of Congress scan'")
    parser.add_argument("--source-id", default="ad-hoc")
    parser.add_argument("--source-item-id")
    args = parser.parse_args()
    if args.work_id not in {record["id"] for record in load_records()}:
        parser.error("unknown catalog work ID")
    path = CATALOG / "resolved-sources.json"
    data = json.loads(path.read_text())
    entry = data.setdefault("records", {}).setdefault(args.work_id, {"resolved_at": None, "source_options": []})
    entry["source_options"].insert(0, {
        "source_id": args.source_id,
        "source_item_id": args.source_item_id,
        "source_url": args.url,
        "label": args.label,
        "resolution_method": "ad-hoc-source-link",
    })
    entry["resolved_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Added source for {args.work_id}: {args.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
