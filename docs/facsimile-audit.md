# Facsimile PDF availability audit

## Finding

The repository did not have a facsimile-availability audit.

A facsimile was treated as "available" only after someone had already located an exact PDF URL and manually passed it to `tools/add_facsimile_pdf.py`. That tool then checked only that the response was nonempty, began with a PDF header, and was no larger than GitHub's 100 MB single-file limit.

That is an ingestion check, not an availability determination.

Consequences:

- works without manually supplied URLs were effectively treated as though no facsimile had been found;
- Internet Archive, HathiTrust, Google Books, Library of Congress, university repositories, and other scan sources were not systematically searched;
- a scan larger than 100 MB was treated as unusable rather than recorded as available but unsuitable for direct Git storage;
- title matching, author matching, edition date, language, completeness, scan quality, and rights evidence were not systematically scored;
- generated text PDFs and source-faithful scans could be confused unless the registry role was manually correct;
- no machine-readable record explained why a work had no facsimile.

## Correct definition

A facsimile candidate is available when all of the following have been established:

1. the item is an edition of the intended work, not merely a title collision;
2. the page-image scan is complete enough to be useful;
3. an exact item page and exact downloadable file are known;
4. the file format is a page-image PDF or another source-faithful scan derivative, not a reflowed/generated text PDF;
5. language, publication facts, and edition notes are recorded;
6. rights or access evidence is recorded separately from technical availability;
7. size is recorded as a packaging constraint, not used to redefine availability.

## Required statuses

Every canonical locally mirrored book should eventually have one facsimile audit record with one of these statuses:

- `local-reviewed`: reviewed facsimile is stored locally;
- `candidate-reviewed`: exact candidate verified but not yet stored;
- `available-oversize`: exact candidate verified but exceeds the current Git transport limit;
- `available-restricted`: exact candidate exists but access or redistribution does not permit mirroring;
- `needs-edition-review`: candidates exist but edition identity or quality is unresolved;
- `searched-none-found`: named sources were searched and no suitable candidate was found;
- `not-a-facsimile-target`: the item is born-digital or otherwise unsuitable for this requirement;
- `not-audited`: no systematic search has been completed.

`not-audited` must never be rendered as "no facsimile available."

## Discovery order

For historical books and manuals, the audit should search and record results from:

1. Internet Archive item search and item metadata;
2. Library of Congress digital collections;
3. HathiTrust bibliographic and access records;
4. Google Books full-view records;
5. university and national-library repositories;
6. source-specific repositories appropriate to military and government manuals.

Project Gutenberg is useful for reading editions but is not sufficient evidence that no page-image facsimile exists.

## Internet Archive evaluation

The Internet Archive audit must not guess a download URL from an identifier alone. It should retrieve item metadata and inspect the actual file list.

A candidate should record:

- item identifier and item page;
- title, creator, date, language, and contributing library;
- exact PDF filename and reported byte size;
- whether scan-data files are present;
- whether the PDF is identified as a scan derivative rather than a generated text export;
- access restrictions;
- match confidence and reasons;
- rejection reasons for near matches.

## Packaging policy

GitHub's 100 MB file limit is only one delivery constraint. A verified 140 MB public-domain facsimile remains available. It should be recorded as `available-oversize` and can later be compressed, split, stored with Git LFS, included in a release asset, or acquired during device-image construction.

The project must not equate "cannot commit this exact file directly to Git" with "no facsimile exists."

## Current audit state

The committed `published-editions.json` proves only which facsimiles have already been ingested. It does not prove completeness of facsimile coverage.

Until the new audit registry has been populated by a systematic source search, all canonical locally mirrored books without a stored `facsimile-pdf` must be treated as `not-audited`, not as unavailable.
