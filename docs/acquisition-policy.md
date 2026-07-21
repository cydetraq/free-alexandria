# Acquisition policy

## Mirror locally only when

1. The work is public domain in the United States and the specific edition is verified; or
2. The rights holder has granted redistribution permission; or
3. A license on the actual work permits redistribution under the intended use.

“Free to read” does not mean “free to redistribute.” Keep a source URL, date accessed, edition or version, rights basis, attribution requirements, local license or permission copy, and SHA-256 hashes with every downloaded artifact.

The source URL is not a substitute for local documentation. Preserve enough human-readable provenance, rights evidence, and edition information beside the artifact for an offline user to understand what it is and why it is present.

Use `catalog/edition-queue.yaml` to identify a candidate edition before downloading. Once acquired, create a sibling `provenance.json` in the edition directory defined by `docs/content-naming.md`.

Follow `docs/identifier-policy.md`: keep the source-native identifier in the edition record and resolve established work-level identifiers before publication.

Follow `docs/copyright-review.md` before classifying an edition as public domain, government work, openly licensed, or permission-granted.

After verification, add the edition to `catalog/published-editions.json`. A distribution build reads only this registry; an acquisition-queue record alone can never place a file in an offline release.

## Initial Project Gutenberg importer

For the edition-identified Project Gutenberg records in the queue, run a local plan first:

```sh
python3 tools/acquire_project_gutenberg.py --all-identified
```

To acquire the selected source editions into an archive, use:

```sh
python3 tools/acquire_project_gutenberg.py --all-identified --acquire
```

The importer writes a human-readable edition directory, a canonical Gutenberg EPUB, a searchable PDF derived from Gutenberg's UTF-8 text, and a sibling `provenance.json` that records source URLs, the retrieval time, hashes, and byte counts. It never publishes files to Git or silently changes `published-editions.json`. The source and rights notes are evidence for the operator, not a repository-wide authorization.

## Populate a personal archive from a selection

Export a selection from the catalog portal, then use the population tool to resolve the selected titles against exact Project Gutenberg results:

```sh
python3 tools/populate_from_gutenberg.py free-alexandria-selection.json
python3 tools/populate_from_gutenberg.py free-alexandria-selection.json --acquire
```

Plan mode prints every exact edition it found and explicitly skips only ambiguous or unmatched records. Acquisition mode creates EPUB/PDF/provenance directories and writes `catalog/local-editions.json` for the archive owner's private build. It never silently substitutes a near-title match or makes a jurisdictional decision for the operator.

Turn the populated local registry into an actual static distribution:

```sh
python3 tools/create_profile_from_registry.py --registry catalog/local-editions.json --output profiles/local/my-archive.json
python3 tools/build_profile.py profiles/local/my-archive.json --edition-registry catalog/local-editions.json
```

The resulting `dist/local-archive/` directory contains the portal and every locally populated EPUB/PDF selected by that registry.

## Add an ad-hoc source

If a source is not already listed, add it directly to the work's stored catalog links:

```sh
python3 tools/add_source_link.py fm-21-76-survival 'https://example.gov/exact-manual.pdf' --label 'Agency PDF' --source-id agency
python3 tools/export_catalog.py
```

Every work also receives an Internet Archive title-and-creator fallback link during source resolution. Exact sources appear first; the fallback is there when an exact link fails or no exact source has been catalogued yet.

## Do not acquire

- Restricted or authentication-only government publications.
- Material with unclear provenance or rights.
- Current medical, food-safety, or emergency guidance without a source date.
- A modern translation simply because the original text is public domain.

Historical practical material is valuable, but the portal must visibly caution users when newer safety guidance supersedes it.
