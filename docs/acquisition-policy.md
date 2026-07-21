# Acquisition policy

## Mirror locally only when

1. The work is public domain in the United States and the specific edition is verified; or
2. The rights holder has granted redistribution permission; or
3. A license on the actual work permits redistribution under the intended use.

“Free to read” does not mean “free to redistribute.” Keep a source URL, date accessed, edition or version, rights basis, attribution requirements, local license or permission copy, and SHA-256 hashes with every downloaded artifact.

Use `catalog/edition-queue.yaml` to identify a candidate edition before downloading. Once acquired, create a sibling `provenance.json` in the edition directory defined by `docs/content-naming.md`.

Follow `docs/identifier-policy.md`: keep the source-native identifier in the edition record and resolve established work-level identifiers before publication.

## Do not acquire

- Restricted or authentication-only government publications.
- Material with unclear provenance or rights.
- Current medical, food-safety, or emergency guidance without a source date.
- A modern translation simply because the original text is public domain.

Historical practical material is valuable, but the portal must visibly caution users when newer safety guidance supersedes it.
