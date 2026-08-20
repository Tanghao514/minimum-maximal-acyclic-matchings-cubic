# Release audit — 2026-08-19

## Outcome

The repository is technically uploadable and the preserved computational core
passes its automated checks. It is not described as a complete reproduction of
every Table 6 independence claim because the original endpoint-set audit and
GENREG artifacts are unavailable. The gaps are explicit in
`MISSING_FOR_RELEASE.md` and the README.

## Verified

- Final manuscript: 27 pages; key pages visually rendered and inspected; no
  clipping or table/figure overflow observed.
- Final PDF SHA-256:
  `80d26c7699bc75c7d26a5dce7b6c835fe120d13c9a60d0e030bdb250fd03d48a`.
- Unit tests: 12 passed.
- Census: 4,681/4,681 graph6 records decoded and checked as connected simple
  cubic graphs; counts `1,2,5,19,85,509,4060`.
- Counterexamples: IDs 4055, 4056, 4058, 4059 all passed definition,
  lower-cardinality exclusion, optimum, invariant, structural, and isomorphism
  mapping checks.
- Solver B/C: zero discrepancies over all 4,681 preserved rows.
- Paper numerics: census histograms, layer medians, candidate counts, equality
  statuses, ablation ratios/counts, source hashes, census hashes, and PDF hash
  all matched.
- Equality construction: exact inputs/certificates produced and verified for
  orders 16, 20, 24, 26, 28, 32, 36, 46, and 56; structural constructions
  verified for every even order 4 through 56.
- One-command clean-root check ended with `RELEASE VERIFICATION PASSED`.

## Hygiene

- No hard-coded `C:\Users\...`, workspace drive path, Unix home path, API key,
  GitHub token, password assignment, private key, `.env`, or credential file was
  found by the release scan.
- Python/test caches and LaTeX build by-products are ignored.
- Largest release file is approximately 1.21 MiB; Git LFS is unnecessary.
- No GENREG/nauty executable or third-party source bundle is redistributed.

## Licensing

- Code/scripts/tests: MIT, confirmed by the author.
- Author-created data, certificates, results, and repository documentation:
  CC BY 4.0, confirmed by the author.
- Manuscript PDF/LaTeX: retained rights and future publisher terms.

## Declared gaps

See `MISSING_FOR_RELEASE.md` for the critical independent endpoint-set audit and
GENREG raw/comparison workflow, the noncritical missing equality raw repetition
arrays, and the external Springer class files. The manuscript repository URL
has been resolved in `paper/main_jco.tex`.
