# Missing original publication artifacts and new verification

## Status on 2 October 2026

The historical files listed below remain missing. New, explicitly dated
supplementary verification now supports the two principal computational claims:

- A standalone endpoint-set audit recomputed all 4,681 optima, without the
  theorem lower bound or imports from Solvers A/B/C: zero discrepancies.
- Fresh GENREG and geng runs produced the same canonical multisets as each
  other and the preserved census at all seven orders: 4,681 classes.

Source, raw output, lower-cardinality counts, witnesses, input/build hashes,
and commands are linked from [verification/README.md](verification/README.md).
These are **new post-submission runs**, not recovered historical artifacts.
They do not establish the provenance of the original reported runs.

## Historical missing-file inventory

This file is intentionally explicit. The items below were described by the
final manuscript but were not found in the supplied project, adjacent working
directories, or preserved result tree. They have not been reconstructed and
must not be represented as original publication artifacts.

## 1. Independent endpoint-set audit — critical

Missing:

- the independently written graph6 decoder;
- endpoint-set enumeration source;
- the independent perfect-matching routine for `G[S]`;
- its separate forest and maximality routines;
- exact input manifests and raw per-order outputs for orders 14 and 16;
- hashes and the frozen environment for that audit.

The manuscript reports that every even endpoint set was considered in
increasing cardinality, `G[S]` was checked as a forest, a perfect matching of
`G[S]` was sought, and every two-vertex extension was tested directly. It also
reports 509 audited order-14 graphs and 4,060 audited order-16 graphs. The
historical audit itself is not rerunnable from its original files. The same
census optima are now independently reproduced by the new auditor described
above, whose full source and outputs are included.

Required author action: provide the original audit directory or a frozen
archive with source, inputs, raw outputs, environment, and hashes.

## 2. GENREG raw census and comparison workflow — critical for dual-generator reproduction

Missing:

- the raw GENREG files at orders 4 through 16;
- the exact GENREG version/build and command lines;
- the `labelg` invocation used for canonicalization;
- sorted comparison manifests/reports;
- GENREG-side hashes.

The complete, independently generated nauty 2.9.3 `geng` census is present and
verifiable. In addition, the new generator audit reproduces the graph-set
agreement with fresh GENREG/geng builds and runs. It does not recover the
historical generator records.

Required author action: provide the original GENREG archive and comparison
script/log. Do not substitute a newly downloaded generator run and call it the
publication raw artifact.

## 3. Equality-family raw repetition arrays for orders 16--28 — noncritical

The publication CSV preserves medians, statuses, solved repetition counts,
search counts, and the exact deterministic construction. For `n <= 28`, three
repetitions were performed, but their individual timing arrays were not written
to that CSV. Orders 32 and above used a single repetition, so the preserved
value is itself the raw value.

Required author action, if available: provide the original console log or raw
per-repetition file. A new rerun may be added as a separate validation artifact
but must not be labeled as the missing publication timings.

## 4. Final manuscript availability URL — resolved

The public repository URL and complete data and code availability statement
have been inserted in `paper/main_jco.tex`. The preserved PDF remains the
earlier release snapshot; the submitted manuscript contains the corrected
statement recorded in `paper/DATA_AVAILABILITY_UPDATE.md`. This item is
resolved.

## 5. Springer LaTeX class files — external

The manuscript source uses Springer's `svjour3` class. The class files were not
redistributed in the release-cleanup tree because they are third-party template
material. Obtain the current authorized JCO/Springer template from the journal.
The exact compiled PDF is included, so source compilation is not required to
verify the paper's archived appearance.
