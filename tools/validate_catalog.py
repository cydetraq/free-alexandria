#!/usr/bin/env python3
"""Dependency-free structural checks for Free Alexandria YAML catalogs."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
ID = re.compile(r"^- id: ([a-z0-9]+(?:-[a-z0-9]+)*)$")
WORK_ID = re.compile(r"^  work_id: ([a-z0-9]+(?:-[a-z0-9]+)*)$")

errors = []
seen = set()
work_ids = set()
for path in sorted(CATALOG.glob("*.yaml")):
    if path.name in {"tags.yaml", "sources.yaml", "edition-queue.yaml"}:
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

queue_path = CATALOG / "edition-queue.yaml"
if queue_path.exists():
    for number, line in enumerate(queue_path.read_text().splitlines(), 1):
        match = WORK_ID.match(line)
        if match and match.group(1) not in work_ids:
            errors.append(f"{queue_path}:{number}: unknown work_id '{match.group(1)}'")

for path in sorted(CATALOG.glob("*.yaml")):
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip() == "rights_status: public-domain-us":
            errors.append(
                f"{path}:{number}: public-domain-us is edition-only; use a candidate or review status in source records"
            )

if errors:
    print("Catalog validation failed:", *errors, sep="\n")
    sys.exit(1)
print(f"Catalog validation passed: {len(seen)} records with unique IDs.")
