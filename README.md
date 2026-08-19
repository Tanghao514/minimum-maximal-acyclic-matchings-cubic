# Minimum Maximal Acyclic Matchings in Connected Cubic Graphs

This repository is the computational reproducibility package for the JCO
manuscript *Minimum Maximal Acyclic Matchings in Connected Cubic Graphs:
Exhaustive Enumeration and a Sharp Bound* by Hao Tang.

## Main result

For every even integer `n >= 4`, the manuscript proves

```text
f₃(n) = ceil((n - 1) / 5).
```

Here `f₃(n)` is the minimum, over connected simple cubic graphs of order `n`,
of the minimum cardinality of a maximal acyclic matching. The mathematical
proof is independent of the exhaustive computation. The computation supplies
an exhaustive census through order 16, four counterexamples to the earlier
quarter benchmark, independent solver comparisons, and performance evidence.

> **Completeness notice.** The complete Solver B/C census and benchmark
> artifacts are present. The separately written endpoint-set audit source and
> the raw GENREG collection were not found in the supplied project. They have
> not been reconstructed or fabricated; see [MISSING_FOR_RELEASE.md](MISSING_FOR_RELEASE.md).

## Repository contents

- `src/`: exact publication versions of the definition checker, Solvers A/B/C,
  equality constructions, and structural-certificate helpers.
- `scripts/`: reviewer-facing commands plus the original publication scripts.
- `tests/`: the 12-test publication suite.
- `data/census/canonical/`: seven canonical graph6 census files, 4,681 graphs.
- `data/counterexamples/`: the four paper graph6 records, matchings, invariants,
  and mappings to the independent `geng` census.
- `data/equality_family/`: exact graph6 inputs and certificates for Table 8.
- `results/per_graph/`: all 4,681 paired Solver B/C rows, including raw timing
  repetitions and search diagnostics.
- `results/benchmarks/`: preserved raw and processed publication timing data.
- `results/ablations/`: 500 rows (100 graphs × 5 variants), with all three raw
  timing repetitions and search counts.
- `results/tables/`: machine-readable reproductions of manuscript tables.
- `paper/`: the exact final PDF and final LaTeX source snapshot.
- `archive/publication_snapshot/`: the supplied project layout before release
  cleanup, excluding caches and compiled Python files.

See [PAPER_TO_ARTIFACTS.md](PAPER_TO_ARTIFACTS.md) for a result-by-result map.

## Quick start

```bash
git clone https://github.com/Tanghao514/minimum-maximal-acyclic-matchings-cubic.git
cd minimum-maximal-acyclic-matchings-cubic
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows or
`source .venv/bin/activate` on Linux/macOS), then run:

```bash
python -m pip install -r requirements.txt
python scripts/verify_release.py
```

The short verification runs 12 tests, verifies all hashes and census records,
checks the four counterexamples and representative constructions, reproduces
the tables, and compares Solvers A/B/C on standard cubic graphs. It does not
rerun the expensive benchmark. Its final line is:

```text
RELEASE VERIFICATION PASSED
```

Conda users may instead run:

```bash
conda env create -f environment.yml
conda activate mmam-cubic-jco
python scripts/verify_release.py
```

## Verify the four counterexamples

```bash
python scripts/verify_counterexamples.py
```

The command checks simple/connected/cubic structure, the listed matching,
acyclicity, maximality, absence of solutions of size 0, 1, or 2, optimum 3,
all Table 3 invariants, and the isomorphism mapping between paper and `geng`
identifiers. Expected output contains:

```text
graph 4055: PASS
graph 4056: PASS
graph 4058: PASS
graph 4059: PASS
```

## Run Solver A, B, or C

The following examples use the first graph in the order-4 census:

```bash
python scripts/solve_graph.py --solver A --input data/census/canonical/connected_cubic_n4.g6
python scripts/solve_graph.py --solver B --input data/census/canonical/connected_cubic_n4.g6
python scripts/solve_graph.py --solver C --input data/census/canonical/connected_cubic_n4.g6
```

Use `--graph6 "..."` for a literal record, or `--index N` for a zero-based
record in a graph6 file. Solver A is deliberately naive and should only be used
on small graphs. Solver C requires a nonempty connected cubic graph and uses
the proved one-fifth theorem; it is not independent evidence for that theorem.

## Reproduce the complete census

The preserved graph6 files can be checked without external software:

```bash
python scripts/verify_census_counts.py
```

To regenerate them, install nauty 2.9.3 and point to `geng`:

```bash
python scripts/generate_census.py --geng /path/to/geng
```

This runs the equivalent of `geng -c -q -d3 -D3 n 3n/2` at orders 4, 6,
8, 10, 12, 14, and 16, then checks counts `1, 2, 5, 19, 85, 509, 4060`.
Canonical labels and line order may differ across generator/canonicalization
workflows even when the multisets of isomorphism classes are identical.

## Independent endpoint-set audit

The final manuscript reports an independent endpoint-set audit, with a
separate graph6 decoder and no calls to Solvers A/B. Its source and raw audit
outputs were not present in the supplied package. Consequently this repository
does not offer a fake replacement command. The exact missing items and the
manuscript-reported protocol are recorded in
[MISSING_FOR_RELEASE.md](MISSING_FOR_RELEASE.md).

## Reproduce tables

```bash
python scripts/reproduce_tables/reproduce_all.py
python scripts/verify_paper_numbers.py
```

The first command writes Tables 1--8 as CSV files under `results/tables/`.
For Table 6, it produces an artifact-availability matrix so unavailable
independent evidence cannot be mistaken for a reproduced result. The second
command checks all census counts, histograms, benchmark medians and candidates,
equality statuses, ablation ratios/counts, source hashes, census hashes, and
the final PDF hash. Any failure creates `RESULT_MISMATCH_REPORT.md`.

## Equality construction

```bash
python scripts/construct.py --n 16
python scripts/construct.py --n 20
python scripts/construct.py --n 56
```

Any even `n >= 4` is accepted. The command emits graph6, a matching certificate,
the value `ceil((n-1)/5)`, structural identities, and verification of
simple/connected/cubic/matching/acyclic/maximal conditions. The implementation
includes the direct base construction, residue adjustments, the `k₀=1` path--
cycle family, and special cases `n=4,8,12`.

## Benchmarks

Correctness reproduction and performance reproduction are distinct:

```bash
# Short correctness gate only
python scripts/reproduce_full_census.py --phase correctness

# Full paired census using the preserved inputs
python scripts/reproduce_full_census.py --phase all
```

The publication protocol is single-threaded. Solver order alternates between
repetitions; whole-order medians use five repetitions through order 12 and
three at orders 14 and 16. The exact publication timing CSV/JSON is preserved.

**Correctness results should reproduce exactly; timing values are
hardware-dependent.** Do not expect bit-for-bit timing agreement on another
machine. The full equality-family experiment uses a 300-second timeout and can
take substantially longer because Solver B times out at orders 46 and 56.

## External software

The census was generated with nauty 2.9.3 `geng`; the manuscript additionally
reports a GENREG census canonicalized with nauty `labelg`. These tools are
third-party software and are not redistributed here. Installation sources,
commands, and the boundary between preserved and unavailable artifacts are in
[docs/external_tools.md](docs/external_tools.md).

## Data and reproducibility

Graph data uses one headerless graph6 record per line. CSV schemas and ID
semantics are documented in [docs/data_format.md](docs/data_format.md).
Detailed section/table reproduction instructions, inputs, outputs, expected
values, and runtime guidance are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

Publication environment: Windows 11 build 26200; AMD Ryzen 7 7435H; 8 physical
and 16 logical cores; 15.74 GiB RAM; CPython 3.11.7; NetworkX 3.1; nauty 2.9.3;
single-threaded solver calls; benchmark date 19 August 2026.

`PUBLICATION_SHA256SUMS.txt` identifies the frozen paper/code/data core.
`SHA256SUMS.txt` covers the release-cleanup repository contents. Verify both:

```bash
python scripts/verify_hashes.py
```

Publication snapshot commit:
`e48b90d21fc9dc28d94bc0e2410fe220bba6feda`. The release is also marked by
the `jco-submission-v1` tag. No paper or repository DOI is claimed.

## Citation

GitHub can read [CITATION.cff](CITATION.cff). Until the manuscript has a DOI,
cite the paper title, Hao Tang, this repository URL, and the commit or release
used. Do not invent a DOI.

## License

- Python code, scripts, and tests: MIT, see [LICENSE](LICENSE).
- Author-created datasets, certificates, result tables, and repository
  documentation: CC BY 4.0, see [LICENSE-DATA](LICENSE-DATA).
- Manuscript PDF and LaTeX source: retained rights and future publisher terms,
  see [paper/RIGHTS.md](paper/RIGHTS.md).
- Third-party software is excluded and remains under its own license.
