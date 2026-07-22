#!/usr/bin/env python3
"""Reconcile the Goodreads banned/public-domain discovery list against Free Alexandria.

The source list is not treated as rights evidence. This tool reports whether each
normalized work has a catalog record, a canonical editorial status, and at least
one local published edition. Edition-review decisions remain failures until a
specific eligible edition is selected and stored.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records

AUDIT = CATALOG / "source-audits" / "goodreads-1818.json"
LOCK = CATALOG / "canonical-lock.json"
REGISTRY = CATALOG / "published-editions.json"


def main() -> int:
    source = json.loads(AUDIT.read_text())
    lock = json.loads(LOCK.read_text())
    registry = json.loads(REGISTRY.read_text()).get("editions", {})
    records = {record["id"]: record for record in load_records()}

    canonical_local = set(lock.get("required_local", [])) | set(lock.get("open_license_local", [])) | set(lock.get("preparedness_required_local", []))
    canonical_linked = set(lock.get("linked_only", []))

    counts: Counter[str] = Counter()
    failures: list[str] = []
    rows: list[dict] = []

    for entry in source["entries"]:
        decision = entry["decision"]
        counts[decision] += 1
        for work_id in entry["work_ids"]:
            catalog = work_id in records
            local = bool(registry.get(work_id))
            canonical = "required-local" if work_id in canonical_local else "linked-only" if work_id in canonical_linked else "absent"
            rows.append({
                "rank": entry["rank"],
                "title": entry["title"],
                "work_id": work_id,
                "decision": decision,
                "canonical": canonical,
                "catalog": catalog,
                "local_edition": local,
            })

            if decision.startswith("accept-local"):
                if canonical != "required-local":
                    failures.append(f"{work_id}: accepted for local archive but absent from canonical required-local list")
                if not catalog:
                    failures.append(f"{work_id}: accepted for local archive but has no catalog record")
                if not local:
                    failures.append(f"{work_id}: accepted for local archive but has no published local edition")
            elif decision == "linked-only-us-copyright":
                if canonical != "linked-only":
                    failures.append(f"{work_id}: U.S.-copyrighted source entry is not canonical linked-only")
                if local:
                    failures.append(f"{work_id}: U.S.-copyrighted source entry unexpectedly has a published local edition")

    print(f"Source entries: {len(source['entries'])}")
    print(f"Normalized works: {len(rows)}")
    print("Decisions:")
    for decision, count in sorted(counts.items()):
        print(f"  {decision}: {count}")
    print("\nReconciliation:")
    for row in rows:
        print(
            f"  {row['work_id']}: decision={row['decision']} canonical={row['canonical']} "
            f"catalog={'yes' if row['catalog'] else 'no'} local={'yes' if row['local_edition'] else 'no'}"
        )

    if failures:
        print("\nOutstanding work:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nGoodreads 1818 reconciliation is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
