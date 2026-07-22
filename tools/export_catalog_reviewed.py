#!/usr/bin/env python3
"""Regenerate reader-facing exports while excluding explicitly rejected works."""
from __future__ import annotations

import export_catalog

REJECTED_WORK_IDS = {
    "down-and-out-in-the-magic-kingdom",
    "content-doctorow",
}

_original_load_records = export_catalog.load_records


def reviewed_load_records(*args, **kwargs):
    return [
        record
        for record in _original_load_records(*args, **kwargs)
        if record.get("id") not in REJECTED_WORK_IDS
    ]


def main() -> int:
    export_catalog.load_records = reviewed_load_records
    return export_catalog.main()


if __name__ == "__main__":
    raise SystemExit(main())
