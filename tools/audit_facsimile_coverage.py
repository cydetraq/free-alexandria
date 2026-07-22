#!/usr/bin/env python3
"""Audit what the repository actually knows about facsimile coverage.

This deliberately does not equate a missing local file with unavailability. It
classifies stored facsimiles as local-reviewed and everything else as not-audited
unless a separate reviewed audit record supplies a stronger status.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_profile import CATALOG, ROOT, load_records

AUDIT_PATH = CATALOG / "facsimile-audit.json"
REGISTRY_PATH = CATALOG / "published-editions.json"
VALID_STATUSES = {
    "local-reviewed",
    "candidate-reviewed",
    "available-oversize",
    "available-restricted",
    "needs-edition-review",
    "searched-none-found",
    "not-a-facsimile-target",
    "not-audited",
}


def has_facsimile(editions: list[dict]) -> bool:
    return any(
        file.get("role") == "facsimile-pdf"
        for edition in editions
        for file in edition.get("files", [])
    )


def load_existing() -> dict[str, dict]:
    if not AUDIT_PATH.exists():
        return {}
    payload = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    return payload.get("records", {})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write/update catalog/facsimile-audit.json")
    parser.add_argument("--fail-not-audited", action="store_true", help="fail if any facsimile target remains not-audited")
    args = parser.parse_args()

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("editions", {})
    existing = load_existing()
    records: dict[str, dict] = {}
    errors: list[str] = []

    for record in sorted(load_records(), key=lambda item: item["id"]):
        work_id = record["id"]
        editions = registry.get(work_id, [])
        current = dict(existing.get(work_id, {}))
        stored = has_facsimile(editions)

        if stored:
            current.update({
                "status": "local-reviewed",
                "reason": "A registered local edition contains a facsimile-pdf file with provenance.",
            })
        elif current.get("status") not in VALID_STATUSES - {"local-reviewed"}:
            current = {
                "status": "not-audited",
                "reason": "No stored facsimile is registered and no systematic source-search result has been recorded.",
            }

        current["original_language"] = record.get("original_language")
        current["stored_edition_languages"] = sorted({
            str(edition.get("language"))
            for edition in editions
            if edition.get("language")
        })
        current["local_facsimile"] = stored
        records[work_id] = current

        if current["status"] not in VALID_STATUSES:
            errors.append(f"{work_id}: invalid status {current['status']!r}")

    counts: dict[str, int] = {status: 0 for status in sorted(VALID_STATUSES)}
    for item in records.values():
        counts[item["status"]] += 1

    payload = {
        "format_version": 1,
        "policy": "Missing local facsimile does not establish unavailability. not-audited is the default until a systematic exact-source search is recorded.",
        "records": records,
        "counts": counts,
    }

    if args.write:
        AUDIT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Facsimile coverage audit:")
    for status, count in sorted(counts.items()):
        if count:
            print(f"- {status}: {count}")

    if errors:
        print(*errors, sep="\n")
        return 1
    if args.fail_not_audited and counts["not-audited"]:
        print(f"Incomplete: {counts['not-audited']} works remain not-audited.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
