# Missing publication artifacts

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
reports 509 audited order-14 graphs and 4,060 audited order-16 graphs. Those
claims remain claims in the manuscript, not independently rerunnable artifacts
in this repository.

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
verifiable. This supports the Solver B/C experiment, but it does not recreate
the manuscript's dual-generator evidence.

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

## 4. Final manuscript availability URL — administrative

The exact final PDF and LaTeX snapshot contain `Source code is available at
xxx.` They are preserved byte-for-byte and have not been silently edited.
After the GitHub repository is public, use the sentence in
`paper/DATA_AVAILABILITY_UPDATE.md` in the next manuscript revision.

## 5. Springer LaTeX class files — external

The manuscript source uses Springer's `svjour3` class. The class files were not
redistributed in the release-cleanup tree because they are third-party template
material. Obtain the current authorized JCO/Springer template from the journal.
The exact compiled PDF is included, so source compilation is not required to
verify the paper's archived appearance.

