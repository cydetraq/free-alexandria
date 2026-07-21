# Jurisdictional access

An offline archive is built for a particular distribution jurisdiction. A work can be public domain in Canada or the United Kingdom while remaining protected in the United States or Mexico. Free Alexandria therefore keeps country-specific access facts in `catalog/jurisdictional-access.json`.

## What the tool does

```sh
python3 tools/build_jurisdiction_manifest.py --jurisdiction CA --record nineteen-eighty-four
```

This writes a local `jurisdictional-acquisition-manifest.json` with the rights status, source page, and instructions relevant to the declared jurisdiction. It does **not** download files, bypass location restrictions, or add an item to a distribution automatically.

After a lawful acquisition, the user still adds the exact file, hash, local provenance, and rights basis to `catalog/published-editions.json` before a distribution build can include it.

## Current example: *Nineteen Eighty-Four*

- **Canada:** Project Gutenberg Canada supplies a Canadian-public-domain edition and warns non-Canadian users to check their own law.
- **United Kingdom:** the general known-author term is 70 years after death; this supports a UK review path for Orwell, who died in 1950. Use a UK-cleared source edition, not a Canadian link by assumption.
- **United States:** renewal `R641953` means this work remains link-only until January 1, 2045.
- **Mexico:** the general term is life plus 100 years, so it is not currently a Mexican public-domain candidate.

Sources: [Project Gutenberg Canada](https://gutenberg.ca/ebooks/orwellg-nineteeneightyfour/orwellg-nineteeneightyfour-00-e.html), [Government of Canada copyright guide](https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en/guide-copyright), [UK IPO guidance](https://www.gov.uk/copyright/how-long-copyright-lasts), and [Mexico's Federal Law on Copyright via WIPO Lex](https://www.wipo.int/wipolex/en/legislation/details/11495).

This is jurisdictional metadata, not legal advice. A profile may use it to guide acquisition, but the local operator remains responsible for selecting and attesting to their own edition and use.
