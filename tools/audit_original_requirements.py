#!/usr/bin/env python3
"""Audit the repository against the original Free Alexandria requirements.

This intentionally fails while the repository is only a literary bootstrap.
It is a release gate, not a progress counter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "catalog.json"
EDITIONS_PATH = ROOT / "catalog" / "published-editions.json"
PROFILE_PATH = ROOT / "profiles" / "free-alexandria-v1.json"

REQUIRED_PREPAREDNESS_TOPICS = {
    "water-sanitation": {"water", "sanitation", "hygiene"},
    "first-aid-health": {"first aid", "medical", "health", "diarrhea"},
    "food-safety": {"food safety", "food preservation", "food"},
    "navigation": {"navigation", "map", "compass"},
    "survival-shelter": {"survival", "shelter", "fieldcraft"},
    "rigging-repair": {"rigging", "knots", "repair", "construction"},
    "disaster-response": {"flood", "wildfire", "radiological", "disaster", "emergency"},
    "communications-power": {"communications", "radio", "generator", "power outage"},
}

OPEN_DISTRIBUTION_SENTINELS = {
    "surveillance-self-defense",
    "free-culture",
    "content-doctorow",
    "cryptoparty-handbook",
}

DEVICE_SENTINELS = (
    ROOT / "device",
    ROOT / "firmware",
    ROOT / "platformio.ini",
)

COVER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    FAILURES.append(message)


def passed(message: str) -> None:
    print(f"PASS: {message}")


def iter_records(catalog: Any) -> list[dict[str, Any]]:
    if isinstance(catalog, list):
        return [item for item in catalog if isinstance(item, dict)]
    if isinstance(catalog, dict):
        for key in ("records", "works", "items"):
            value = catalog.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    fail("catalog/catalog.json has no recognized record list")
    return []


def normalize_editions(document: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(document, dict):
        fail("catalog/published-editions.json is not an object")
        return {}
    candidate = document.get("editions", document)
    if not isinstance(candidate, dict):
        fail("published edition registry has no edition mapping")
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for record_id, value in candidate.items():
        if isinstance(value, list):
            result[str(record_id)] = [item for item in value if isinstance(item, dict)]
        elif isinstance(value, dict):
            result[str(record_id)] = [value]
    return result


def local_files(editions: dict[str, list[dict[str, Any]]], record_id: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for edition in editions.get(record_id, []):
        value = edition.get("files", [])
        if isinstance(value, list):
            files.extend(item for item in value if isinstance(item, dict))
    return files


def searchable_text(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("id", "title", "description", "why_included", "publisher", "author"):
        value = record.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ("tags", "collections", "subjects"):
        value = record.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return " ".join(values).casefold()


def verify_hashes(editions: dict[str, list[dict[str, Any]]]) -> None:
    checked = 0
    for record_id, record_editions in editions.items():
        for edition in record_editions:
            for file_info in edition.get("files", []):
                if not isinstance(file_info, dict):
                    continue
                raw_path = file_info.get("path")
                if not isinstance(raw_path, str):
                    fail(f"{record_id}: local file entry has no path")
                    continue
                path = ROOT / raw_path
                if not path.is_file():
                    fail(f"{record_id}: missing local file {raw_path}")
                    continue
                expected_bytes = file_info.get("bytes")
                actual_bytes = path.stat().st_size
                if isinstance(expected_bytes, int) and expected_bytes != actual_bytes:
                    fail(f"{record_id}: byte count mismatch for {raw_path}")
                expected_hash = file_info.get("sha256")
                if isinstance(expected_hash, str):
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest != expected_hash:
                        fail(f"{record_id}: SHA-256 mismatch for {raw_path}")
                checked += 1
    if checked:
        passed(f"verified existence and metadata for {checked} local files")
    else:
        fail("no local files were verified")


def audit() -> int:
    catalog = load_json(CATALOG_PATH)
    editions_doc = load_json(EDITIONS_PATH)
    records = iter_records(catalog)
    editions = normalize_editions(editions_doc)
    records_by_id = {str(record.get("id")): record for record in records if record.get("id")}

    if records:
        passed(f"catalog contains {len(records)} records")
    else:
        fail("catalog is empty")

    local_record_ids = {record_id for record_id in records_by_id if local_files(editions, record_id)}
    if local_record_ids:
        passed(f"{len(local_record_ids)} records have locally stored editions")
    else:
        fail("no records have locally stored editions")

    # Preparedness must be genuinely local and broad enough to be useful offline.
    local_preparedness = [
        record for record_id, record in records_by_id.items()
        if record_id in local_record_ids
        and any("preparedness" in str(value) or "practical" in str(value)
                for value in record.get("collections", []))
    ]
    if not local_preparedness:
        fail("no locally stored preparedness/practical records")
    else:
        corpus = " ".join(searchable_text(record) for record in local_preparedness)
        missing_topics = [
            label for label, terms in REQUIRED_PREPAREDNESS_TOPICS.items()
            if not any(term in corpus for term in terms)
        ]
        if missing_topics:
            fail("local preparedness corpus lacks required topics: " + ", ".join(missing_topics))
        else:
            passed("local preparedness corpus covers all required topic groups")

    # Open works named during planning should be mirrored when legally eligible.
    missing_open = sorted(record_id for record_id in OPEN_DISTRIBUTION_SENTINELS if record_id not in local_record_ids)
    if missing_open:
        fail("open-distribution works still not mirrored locally: " + ", ".join(missing_open))
    else:
        passed("required open-distribution works are stored locally")

    # Real stored thumbnails, not runtime text cards.
    cover_files = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.casefold() in COVER_SUFFIXES]
    if len(cover_files) < len(local_record_ids):
        fail(f"stored cover thumbnails are incomplete: {len(cover_files)} covers for {len(local_record_ids)} local works")
    else:
        passed("stored cover thumbnail count covers the local catalog")

    # At least one work must expose multiple languages/editions to prove the portal model supports it.
    multilingual = 0
    for record_id, record_editions in editions.items():
        languages = {str(item.get("language")) for item in record_editions if item.get("language")}
        if len(languages) > 1:
            multilingual += 1
    if multilingual:
        passed(f"{multilingual} works expose multiple stored languages")
    else:
        fail("no work exposes both an English translation and original-language local edition")

    # A static portal is not the requested ESP32 captive-portal deliverable.
    if any(path.exists() for path in DEVICE_SENTINELS):
        passed("device/firmware implementation is present")
    else:
        fail("missing ESP32 device/firmware implementation")

    device_docs = ROOT / "docs" / "device-build.md"
    if device_docs.is_file():
        passed("device build and flash documentation is present")
    else:
        fail("missing docs/device-build.md")

    # Release size must be measured and bounded.
    profile = load_json(PROFILE_PATH)
    max_bytes = None
    if isinstance(profile, dict):
        max_bytes = profile.get("maximum_bytes") or profile.get("max_bytes")
    if isinstance(max_bytes, int) and 0 < max_bytes <= 32_000_000_000:
        passed(f"profile declares a <=32 GB capacity ceiling ({max_bytes} bytes)")
    else:
        fail("profile does not declare an enforceable <=32 GB maximum_bytes ceiling")

    verify_hashes(editions)

    if FAILURES:
        print(f"\nOriginal-requirements audit failed with {len(FAILURES)} blocking issue(s).")
        return 1
    print("\nOriginal-requirements audit passed. This tree is eligible for device-release testing.")
    return 0


FAILURES: list[str] = []

if __name__ == "__main__":
    raise SystemExit(audit())
