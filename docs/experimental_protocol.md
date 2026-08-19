# Publication experimental protocol

## Hardware and software

- Microsoft Windows 11, build 26200, 64 bit.
- AMD Ryzen 7 7435H; 8 physical and 16 logical cores.
- 15.74 GiB RAM.
- CPython 3.11.7, Anaconda 64 bit, MSC v.1916.
- NetworkX 3.1.
- nauty 2.9.3 `geng`.
- Single-threaded Python solver calls; no concurrent benchmark jobs.
- `time.perf_counter`; benchmark date 19 August 2026.

The full environment JSON includes source and census SHA-256 values.

## Paired census benchmark

Both solvers receive the same in-memory graph object and input order. Garbage
collection is disabled only inside individual timed calls. Solver order
alternates between repetitions. Complete layers are repeated five times
through order 12 and three times at orders 14 and 16. Table 5 uses medians of
whole-layer totals. Per-graph CSV rows preserve raw repetition arrays.

Solver B's `states_examined` and Solver C's `complete_candidates` are both
complete candidates but are not a common level-by-level node metric. Solver C
recursion nodes are therefore stored separately.

## Equality scaling

Orders are 16, 20, 24, 26, 28, 32, 36, 46, and 56. Each solver runs in a
spawned process under a 300-second timeout. There are three alternating
repetitions through order 28 and one thereafter.

## Ablation

The deterministic stratified sample contains all four zero-defect order-16
graphs and 96 defect-five graphs. Each of five variants is run three times per
graph. No random seed is involved in sample selection.

## Interpretation

Correctness and integer search counts are deterministic for the frozen code and
input order. Timings are performance observations, not bit-for-bit reproducible
values. Compare trends and order-level magnitudes on new hardware and preserve
new results separately from the publication snapshot.

