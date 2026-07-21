#!/usr/bin/env python3
"""Dependency-free structural checks for Free Alexandria YAML catalogs."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
ID = re.compile(r"^- id: ([a-z0-9]+(?:-[a-z0-9]+)*)$")

errors = []
seen = set()
work_ids = set()
for path in sorted(CATALOG.glob("*.yaml")):
    if path.name in {"tags.yaml", "sources.yaml"}:
        continue
    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = ID.match(line)
        if not match:
            continue
        value = match.group(1)
        if value in seen:
            errors.append(f"{path}:{number}: duplicate id '{value}'")
        seen.add(value)
        work_ids.add(value)

if errors:
    print("Catalog validation failed:", *errors, sep="\n")
    sys.exit(1)
print(f"Catalog validation passed: {len(seen)} records with unique IDs.")
