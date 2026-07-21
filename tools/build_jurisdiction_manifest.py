#!/usr/bin/env python3
"""Create a local acquisition plan for one declared copyright jurisdiction."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jurisdiction", required=True, help="Two-letter jurisdiction code, e.g. CA")
    parser.add_argument("--record", action="append", required=True, help="Catalog record ID; may be repeated")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "jurisdictional-acquisition-manifest.json")
    args = parser.parse_args()

    registry = json.loads((CATALOG / "jurisdictional-access.json").read_text())
    jurisdiction = args.jurisdiction.upper()
    if jurisdiction not in registry["jurisdictions"]:
        raise ValueError(f"unknown jurisdiction: {jurisdiction}")
    records = {record["id"]: record for record in load_records()}
    unknown = set(args.record) - set(records)
    if unknown:
        raise ValueError("unknown catalog record IDs: " + ", ".join(sorted(unknown)))
    access = {item["work_id"]: item["jurisdictions"] for item in registry["access"]}
    items = []
    for record_id in args.record:
        rights = access.get(record_id, {}).get(jurisdiction, {
            "status": "no-jurisdictional-determination",
            "note": "No jurisdiction-specific acquisition determination has been recorded yet."
        })
        items.append({"record": records[record_id], "jurisdiction": jurisdiction, "access": rights})
    manifest = {
        "format_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "jurisdiction": {"code": jurisdiction, **registry["jurisdictions"][jurisdiction]},
        "offline_notice": "This file is a local acquisition plan. It does not itself authorize redistribution or include a downloaded work.",
        "items": items
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote jurisdictional acquisition manifest for {jurisdiction}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
