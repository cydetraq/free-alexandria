# Source-evidence policy

Free Alexandria records source and edition evidence for a local operator; it does not make a global legal decision. A work title, author death date, repository download button, or pre-1978 publication date is not a universal permission statement.

## Research prompts for a local operator

1. **Underlying work versus file:** note later translation, introduction, illustrations, annotations, restoration, or other additions that may matter to the operator.
2. **Publication facts:** preserve exact edition, publication, source, and translator details rather than treating a title as a single legal object.
3. **Foreign and translated works:** record the selected language and translation; rules may vary by jurisdiction and by edition.
4. **Government and open material:** preserve the actual distribution statement, license, attribution, and version from the source.

An unresolved rights question is not an exclusion. Keep the work in the catalog and review queue, provide a legitimate external link if available, and promote it to a local edition if the review establishes a lawful distribution basis.

## Local-build gate

Only `catalog/published-editions.json` can select a file for a local distribution build. Each entry must identify its source-native ID, a local `provenance.json`, hashes and sizes, and a dated source/eligibility note recorded by the local operator. The build verifies the local provenance file and hashes before copying an edition to a release; it does not decide whether the operator's use is lawful.

Completed determinations live in `catalog/rights-determinations.yaml`; unresolved but potentially eligible works stay in `catalog/rights-review-queue.yaml`. The latter is an acquisition opportunity list, not an exclusion list.

## Primary references

- U.S. Copyright Office, [What is Copyright?](https://copyright.gov/what-is-copyright/) — its current public-domain guidance says that works published in the United States before January 1, 1931 are public domain.
- U.S. Copyright Office, [Duration FAQ](https://www.copyright.gov/help/faq/faq-duration.html) and [Circular 15A](https://www.copyright.gov/circs/circ15a.pdf) — duration varies for pre-1978 works.
- U.S. Copyright Office, [Circular 22](https://www.copyright.gov/circs/circ22.pdf) — works first published or copyrighted before 1964 must be checked for timely renewal; it explains how to investigate the Copyright Office records.
- U.S. Copyright Office, [17 U.S.C. chapter 3](https://www.copyright.gov/title17/92chap3.html) — including section 303 on previously unpublished works.
- U.S. Copyright Office, [17 U.S.C. section 105](https://www.copyright.gov/title17/92chap1.html) — U.S. Government works.
- U.S. Copyright Office, [Circular 38b](https://www.copyright.gov/circs/circ38b.pdf) — copyright restoration under the URAA.

This is a source-preservation policy, not legal advice. See [local use and jurisdiction](local-use-and-jurisdiction.md) for the project's operating boundary.
