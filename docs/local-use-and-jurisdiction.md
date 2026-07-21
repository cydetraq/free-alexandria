# Local use and jurisdiction

Free Alexandria has two deliberately separate layers. It is not a legal service or a global copyright-clearance authority.

## Publisher archive and portable tool

1. **Free Alexandria's publisher archive** contains the files the archive owner chooses to make available under the rules of the archive owner's jurisdiction. That archive may be served, copied, and maintained as the owner decides.
2. **The portable catalog and build tool** contains the broader list of titles, descriptions, source options, curation profiles, and selection tools. A person can clone it, choose any subset, and build their own archive from the sources and editions they choose.

The second layer does not control the first, and it does not create a duty for the archive owner to make legal decisions for every possible user or jurisdiction.

## The operating boundary

- The catalog may record where an edition was found, what a source says about it, and what an archive operator recorded at acquisition time.
- Jurisdiction presets are best-effort recommendations for a user to consider, not legal determinations.
- The person building a separate archive chooses their own books, editions, sources, and distribution decisions.
- The catalog tool does not guarantee that a work is lawful in every jurisdiction or for every use.

## Why the catalog still retains rights metadata

Offline users need context. Source-provided rights notices, publication dates, edition and translator information, and acquisition evidence help an operator make a decision later, without returning to an online catalog. These fields are evidence and research notes—not legal advice or a permission grant.

## Acquisition behavior

The acquisition tools default to **plan only**. They display the exact edition, source URL, canonical source ID, and intended local path without downloading anything. The operator can then choose to acquire selected items:

```sh
python3 tools/acquire_project_gutenberg.py --all-identified --acquire
```

The tool records source and file provenance for offline maintenance. It does not act as a jurisdictional decision-maker.

## Profiles

A profile selects records and files. It does not determine their legal status. The operator may maintain their own private profile or acquisition manifest for their jurisdiction, language, and risk tolerance. Public profiles in this repository are examples of technical selection and reproducibility only.

## Local selection workflow

1. Build a catalog preview and open its `index.html`.
2. Filter by collection, language, or availability; then select individual cards, filtered records, all records, or none.
3. Download the resulting `free-alexandria-selection.json` from the portal.
4. Turn it into a private local profile:

```sh
python3 tools/create_profile_from_selection.py free-alexandria-selection.json --output profiles/local/my-selection.json
python3 tools/build_profile.py profiles/local/my-selection.json
```

The selection is a list of desired works, not a download order. The operator can acquire a particular source, purchase a commercial copy, use library lending, skip it, or substitute a different edition later.
