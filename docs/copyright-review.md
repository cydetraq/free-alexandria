# Copyright review policy (United States)

This project distributes only editions that have a documented, edition-specific U.S. rights review. It does not treat a work title, an author death date, a repository download button, or a pre-1978 publication date as sufficient permission by itself.

## Practical rules for this catalog

1. **Works first published in the United States before January 1, 1931:** the Copyright Office currently identifies these as public domain. That supports an eligibility lead for the underlying text, but the selected file must still be reviewed for later translation, introduction, illustrations, annotations, restoration, or other protected additions.
2. **Works published from 1931 through 1977:** never infer public-domain status from age alone. The applicable analysis can depend on publication, notice, registration, renewal, and other historical facts.
3. **Unpublished pre-1978 material:** do not use the publication-year shortcut. Current law generally applies a life-plus-70-years analysis, with statutory minimum terms for some previously unpublished works.
4. **Foreign works and translations:** review the specific English translation or source-language edition. Foreign-status restoration rules and the independent copyright in translations make a title-level conclusion unsafe.
5. **U.S. government material:** a work created by a U.S. Government officer or employee as part of official duties generally is not protected by U.S. copyright, but a hosted file may contain contractor, third-party, or restricted material. Review the actual publication and distribution statement.
6. **Open-licensed material:** retain the exact license, version, attribution, and modification/redistribution terms; being free to read is not a license to mirror.

## Publication gate

Only `catalog/published-editions.json` can authorize a distribution build. Each entry must identify its source-native ID, a local `provenance.json`, hashes and sizes, and a `rights_review` with an approved basis. The build verifies the local provenance file and hashes before copying an edition to a release.

## Primary references

- U.S. Copyright Office, [What is Copyright?](https://copyright.gov/what-is-copyright/) — its current public-domain guidance says that works published in the United States before January 1, 1931 are public domain.
- U.S. Copyright Office, [Duration FAQ](https://www.copyright.gov/help/faq/faq-duration.html) and [Circular 15A](https://www.copyright.gov/circs/circ15a.pdf) — duration varies for pre-1978 works.
- U.S. Copyright Office, [17 U.S.C. chapter 3](https://www.copyright.gov/title17/92chap3.html) — including section 303 on previously unpublished works.
- U.S. Copyright Office, [17 U.S.C. section 105](https://www.copyright.gov/title17/92chap1.html) — U.S. Government works.
- U.S. Copyright Office, [Circular 38b](https://www.copyright.gov/circs/circ38b.pdf) — copyright restoration under the URAA.

This is a project-control policy, not legal advice. Escalate borderline or commercially important cases for qualified legal review.
