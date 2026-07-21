#!/usr/bin/env python3
"""Turn a locally exported Free Alexandria selection into a private catalog profile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_profile import load_records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("selection", type=Path, help="JSON downloaded from the offline portal")
    parser.add_argument("--output", type=Path, required=True, help="Private profile JSON to create")
    parser.add_argument("--name", default="My Free Alexandria Selection")
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text())
    ids = selection.get("selected_record_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        parser.error("selection must contain selected_record_ids as a string list")
    known = {record["id"] for record in load_records()}
    unknown = sorted(set(ids) - known)
    if unknown:
        parser.error("unknown catalog IDs: " + ", ".join(unknown))
    profile = {
        "$schema": "../metadata/curation-profile.schema.json",
        "format_version": 1,
        "id": "local-selection",
        "name": args.name,
        "description": "Private selection created locally from the Free Alexandria offline portal.",
        "curator": {"name": "Local operator"},
        "build_mode": "catalog-preview",
        "language_preferences": [],
        "include_record_ids": sorted(set(ids)),
        "exclude_record_ids": [],
        "constraints": {"require_local_files": False, "allow_link_only": True},
        "notes": "This profile selects metadata only. The local operator decides whether and how to acquire any individual work."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2) + "\n")
    print(f"Wrote {args.output}: {len(profile['include_record_ids'])} selected records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
