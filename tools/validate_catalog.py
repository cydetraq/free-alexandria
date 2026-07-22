#!/usr/bin/env python3
"""Dependency-free structural checks, with strict editorial and release validation."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
ID = re.compile(r"^- id: ([a-z0-9]+(?:-[a-z0-9]+)*)$")

parser = argparse.ArgumentParser()
parser.add_argument("--strict", action="store_true", help="also verify release-critical registries and editorial invariants")
parser.add_argument("--strict-links", action="store_true", help="reject generic primary links for linked-only works")
args = parser.parse_args()

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

canonical_command = [sys.executable, str(ROOT / "tools" / "validate_canonical_lock.py")]
if args.strict_links:
    canonical_command.append("--strict-links")
canonical_result = subprocess.run(canonical_command, cwd=ROOT)
if canonical_result.returncode:
    raise SystemExit(canonical_result.returncode)

if args.strict:
    commands = [
        [sys.executable, str(ROOT / "tools" / "export_catalog.py"), "--check"],
        [sys.executable, str(ROOT / "tools" / "validate_curated_reading.py")],
        [sys.executable, str(ROOT / "tools" / "lint_sources.py")],
        [sys.executable, str(ROOT / "tools" / "audit_original_requirements.py")],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            raise SystemExit(result.returncode)
