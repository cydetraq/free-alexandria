#!/usr/bin/env python3
"""Create a distribution profile from the editions already present in a local registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("catalog/local-editions.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", default="My Free Alexandria Archive")
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text())
    ids = sorted(registry.get("editions", {}))
    if not ids:
        parser.error("the local edition registry contains no editions")
    profile = {
        "$schema": "../metadata/curation-profile.schema.json",
        "format_version": 1,
        "id": "local-archive",
        "name": args.name,
        "description": "Distribution profile generated from editions in the local archive registry.",
        "curator": {"name": "Local operator"},
        "build_mode": "distribution",
        "language_preferences": [],
        "include_record_ids": ids,
        "exclude_record_ids": [],
        "constraints": {"require_local_files": True, "allow_link_only": False},
        "notes": "Generated from local-editions.json; only files already present in this archive are included."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2) + "\n")
    print(f"Wrote {args.output}: {len(ids)} locally populated works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
