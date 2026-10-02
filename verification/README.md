# Post-submission verification — 2 October 2026

This is **new supplementary verification**, completed after submission. It is
not the missing original endpoint-set audit or the original GENREG run. The
original missing files remain documented in [MISSING_FOR_RELEASE.md](../MISSING_FOR_RELEASE.md).
No manuscript, publication solver, census input, or publication timing result
was changed for this update.

## Results

| Check | Coverage | Result |
|---|---|---|
| Standalone endpoint-set optimization | All 4,681 graphs, orders 4 through 16 | Every optimum agrees with the publication |
| Smaller-value exclusion | Every endpoint cardinality below each returned optimum | Complete enumeration recorded for every graph |
| Independent checker gate | All 1,100 labeled simple graphs of orders 0–5 and 14 additional graphs | Agreement with separate Python edge-subset enumeration |
| Fresh GENREG versus fresh geng | All seven census layers | Equal canonical multisets, no duplicate classes |
| Both fresh generators versus preserved inputs | All 4,681 classes | Equal canonical multisets; row bijections archived |

The new order-14 histogram is **418 graphs with value 3 and 91 with value 4**.
The new order-16 histogram is **4 graphs with value 3 and 4,056 with value 4**.
There are no discrepancies with the manuscript census.

Browse the [endpoint report](../results/post_submission/2026-10-02/endpoint_audit/summary.json)
and [generator report](../results/post_submission/2026-10-02/generator_audit/summary.json).
Their directories also contain every per-graph result, raw generator output,
canonicalized input, stderr stream, and generator row mapping.

## Quick check of the archived evidence

From the repository root, with Python 3.11 or later:

```bash
python scripts/verify_post_submission.py
python scripts/verify_hashes.py
```

The first command checks the archived inputs, witnesses, lower-layer enumeration
counts, optima, histograms, source/output hashes, GENREG ASCII conversion, and
canonical-class bijections. It does **not** rerun the exponential endpoint
search or execute the external generators. Use the commands below for fresh runs.

## Rerun the endpoint audit

Requires Python 3.11+ and a C++17 compiler (`g++` by default), on Linux/WSL or
another environment providing that compiler. The audit itself has no third-party
Python dependencies.

```bash
python scripts/run_endpoint_audit.py --output reproduced/endpoint_audit
```

An existing output directory is rejected. Choose a fresh directory for another
run; publication records and previous runs are never overwritten automatically.
To run just the small independent test gate:

```bash
python scripts/run_endpoint_audit.py --gate-only --output reproduced/endpoint_gate
```

### What makes this check independent?

`endpoint_audit.cpp` contains its own graph6 decoder, union-find forest test,
recursive perfect-matching routine, and direct maximality test. It imports no
project code and links no graph library. It receives only graph6 inputs.

For each graph it starts at `k = 0` and visits all vertex subsets of size `2k`
in increasing bit-mask order. A subset is accepted exactly when:

1. The full vertex-induced graph is a forest.
2. It has a perfect matching, recorded as the witness.
3. For every graph edge with both endpoints outside the subset, adding its two
   vertices makes the full induced graph cyclic.

The search stops at the first accepted subset. The complete lower layers have
exactly `binomial(n, 2k)` visited subsets. There is no one-fifth lower bound,
defect budget, Solver A/B/C call, or supplied optimum in this search. The Python
runner loads publication answers only **after** the standalone process exits.

Before the census, the runner compares this C++ search with separate Python
edge-subset enumeration on 1,114 small graphs. The Python oracle uses BFS
component edge counts, not the C++ union-find implementation. The gate includes
disconnected graphs, isolates, cycles, paths, K3,3, K6, the cube, and Petersen.
Malformed graph6 records and both standard header forms are checked too.

### Output and limits

Each `nN.jsonl` row records the exact input, zero-based index, optimum, matching,
endpoint bit mask, visited/forest/perfect-matching counts per layer, and elapsed
time. The lower-layer counts are auditable **execution records**, not compact
formal infeasibility certificates: rerun the program to independently reproduce
the search. This finite check does not prove the all-orders theorem.

The executable accepts simple graph6 records of orders 0–24 and deliberately
rejects larger inputs. Search is exponential. Recorded C++/Linux times are new
verification timings and are not a rerun of the paper's Python B/C benchmark.

## Rerun the generator comparison

On Linux/WSL, with Python 3.11+, a C compiler, `make`, and network access:

```bash
python scripts/prepare_verification_tools.py --output tmp/verification-tools
python scripts/run_generator_audit.py \
  --genreg tmp/verification-tools/genreg/genreg \
  --geng tmp/verification-tools/nauty2_9_3/geng \
  --labelg tmp/verification-tools/nauty2_9_3/labelg \
  --toolchain-manifest tmp/verification-tools/toolchain.json \
  --output reproduced/generator_audit
```

The preparation script downloads official, SHA-256-pinned GENREG trunk sources
and nauty 2.9.3, records their URLs, builds them without editing the source, and
records compiler information, build logs, and executable hashes. The build
directory must be fresh. GENREG's old C source emits compiler warnings; those
warnings are preserved in the build log. Third-party source and binaries are
not redistributed in this repository.

For Windows plus WSL, downloads can be performed with `--download-only`, then
built from the same directory under WSL with `--build-only`.

At each order, the generator runner executes:

```text
genreg n 3 -a stdout
geng -c -q -d3 -D3 n 3n/2
labelg -q -g <each input file>
```

The GENREG parser checks consecutive graph labels, reciprocal adjacency,
simplicity, degree three, and connectivity. It reads only the adjacency rows,
not the later automorphism rows. Both freshly generated graph sets and the
preserved census are canonicalized with the **same** `labelg` binary. Their
multisets, counts, and uniqueness are checked, and the zero-based row bijection
is saved. The generators are independent; the canonicalizer is shared.

## Version and provenance boundary

- `jco-submission-v1`: existing August repository release tag, preserved.
- `pre-verification-2026-10-02`: repository state at commit
  `d82f335705a8cab5ec6f7b01b4aabc95e96bc78c`, before this supplement.
- `results/post_submission/2026-10-02/`: new execution records with actual UTC
  timestamps, separate from all publication results.
- `PUBLICATION_SHA256SUMS.txt`: unchanged frozen-core manifest.

The historical Table 6 artifacts are still missing. The new runs independently
support the reported census and the equality of the graph collections; they
cannot establish when or how the historical runs were performed. Raw timing
repetitions missing from the original equality-family benchmark remain missing.
The manuscript files and the submission-system PDF are outside this update.
