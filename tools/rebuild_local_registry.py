#!/usr/bin/env python3
"""Rebuild a private local edition registry from downloaded provenance files."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from build_profile import ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "catalog" / "local-editions.json")
    args = parser.parse_args()
    registry = {"format_version": 1, "editions": {}}
    for path in sorted((ROOT / "content" / "books").glob("*/*/provenance.json")):
        item = json.loads(path.read_text())
        source = item.get("source", {})
        files = []
        for file in item.get("files", []):
            if (ROOT / file["path"]).is_file():
                files.append({key: file[key] for key in ("role", "path", "sha256", "bytes")})
        if not files:
            continue
        registry["editions"].setdefault(item["work_id"], []).append({
            "edition_id": item["edition_id"],
            "language": "English",
            "source_id": "project-gutenberg" if source.get("name") == "Project Gutenberg" else "local-source",
            "source_item_id": str(source.get("item_id", "local")),
            "provenance_path": str(path.relative_to(ROOT)),
            "rights_review": {
                "status": "operator-selected",
                "basis": "Rebuilt from locally downloaded provenance; the archive operator selected this stored source edition.",
                "reviewed_at": dt.date.today().isoformat(),
                "evidence_url": source.get("edition_page", ""),
            },
            "files": files,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, indent=2) + "\n")
    print(f"Wrote {args.output}: {len(registry['editions'])} works, {sum(len(x) for x in registry['editions'].values())} editions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
