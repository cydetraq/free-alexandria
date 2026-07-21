#!/usr/bin/env python3
"""Normalize stored editions to readable work folders plus source-native IDs.

Layout:
    content/books/<work-id>/<source-id>-<source-item-id>/

For example:
    content/books/don-quixote/gutenberg-996/book.epub

The title-derived work ID is for people; the source-native ID identifies the
particular edition. Provenance remains the authority for language, translator,
source URL, acquisition time, hashes, and replacement history.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from build_profile import ROOT


def source_directory(item: dict) -> str:
    source = item.get("source", {})
    if source.get("name") == "Project Gutenberg" and source.get("item_id"):
        return f"gutenberg-{source['item_id']}"
    return f"local-{source.get('item_id', 'edition')}"


def update_provenance(path: Path) -> None:
    item = json.loads(path.read_text())
    for file in item.get("files", []):
        file["path"] = str((path.parent / Path(file["path"]).name).relative_to(ROOT))
    path.write_text(json.dumps(item, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rename directories and update their provenance records")
    args = parser.parse_args()
    sources = sorted((ROOT / "content" / "books").glob("*/*/provenance.json"))
    moves: list[tuple[Path, Path]] = []
    for provenance in sources:
        item = json.loads(provenance.read_text())
        target = ROOT / "content" / "books" / item["work_id"] / source_directory(item)
        if provenance.parent != target:
            moves.append((provenance.parent, target))
    for old, new in moves:
        print(f"{old.relative_to(ROOT)} -> {new.relative_to(ROOT)}")
    if not args.apply:
        print(f"{len(moves)} edition directories would be normalized. Re-run with --apply to make changes.")
        return 0
    targets = [new for _, new in moves]
    duplicates = [target for target in targets if targets.count(target) > 1]
    if duplicates or any(target.exists() for _, target in moves):
        raise RuntimeError("normalization has conflicting source IDs; remove duplicate source copies before applying")
    for old, new in moves:
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), str(new))
        update_provenance(new / "provenance.json")
    print(f"Normalized {len(moves)} edition directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
