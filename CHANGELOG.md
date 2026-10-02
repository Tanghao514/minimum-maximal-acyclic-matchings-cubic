# Changelog

## 2026-10-02 — post-submission reproducibility supplement

- Added a standalone C++17 endpoint-set auditor with its own graph6 decoder,
  forest, perfect-matching, and maximality routines. All 4,681 census optima
  were recomputed without theorem-based pruning and agree with the publication.
- Added a separate Python edge-subset gate on 1,114 graphs, per-graph witnesses,
  exhaustive lower-cardinality counts, environment records, and source hashes.
- Rebuilt hash-pinned GENREG and nauty 2.9.3; regenerated every census layer
  with both generators. Their canonical multisets agree with each other and
  with all 4,681 preserved publication inputs. Raw output and class bijections
  are included.
- Added fresh-run commands, archived-record checks, and automated CI checks.
- Updated the documentation to distinguish new verification from missing
  historical artifacts. The original endpoint-set/GENREG records and some
  original equality-family timing repetitions remain unavailable.
- Preserved manuscript files, publication solvers, publication input data,
  publication benchmark records, and the frozen publication hash manifest.

See [verification/README.md](verification/README.md) for methods, results,
commands, and the provenance boundary.

## 1.0.0-jco-submission — 2026-08-19

- Added the final JCO manuscript PDF and its exact LaTeX source snapshot.
- Froze Solvers A, B, and C, the reference checker, construction code, tests,
  publication scripts, and the complete result snapshot.
- Added all seven canonical `geng` graph6 census files (4,681 graphs total).
- Added the full per-graph Solver B/C table, raw layer repetitions, equality
  scaling results, ablations, environment metadata, and verification records.
- Added reviewer-facing command-line interfaces, table reproduction scripts,
  counterexample and structural-certificate verification, release verification,
  and SHA-256 checking.
- Documented unavailable publication artifacts without reconstructing or
  fabricating them; see `MISSING_FOR_RELEASE.md`.
