# Solver B vs Solver C full-census benchmark

## Research question

On the complete census of connected simple cubic graphs of orders 4 through 16, does Solver C return the same optimum as the theorem-independent Solver B, and what reproducible runtime/search-effort improvement does it provide under a paired protocol?

## Baselines and scope

- Baseline: `minimum_maximal_acyclic_matching` (Solver B).
- Treatment: `minimum_maximal_acyclic_matching_cubic` (Solver C).
- Core dataset: all non-isomorphic connected simple cubic graphs for n = 4, 6, 8, 10, 12, 14, 16.
- Generator: nauty 2.9.3 `geng`, exact degree 3 and connectedness constraints.
- Expected layer counts: 1, 2, 5, 19, 85, 509, 4060 (total 4681).
- Optional n = 18 census is out of core scope unless the required resources remain reasonable after core completion.

## Metrics

- Exact optimum agreement and independent witness validity.
- Per-graph and per-order wall time from `perf_counter` around solver calls only.
- Solver-reported complete candidates for both solvers.
- Solver C recursion nodes as an additional implementation-specific measure.
- Speedup, candidate reduction, distributions by order, optimum, and theorem defect budget.

## Timing protocol

- Graph files are generated and loaded before timed stages.
- One untimed warm-up per solver.
- Five paired repetitions for n <= 12 and three for n = 14, 16.
- Solver order alternates by repetition; garbage collection is performed before and disabled within each timed stage.
- The per-graph record uses the median across repetitions. The paper-facing per-order total is the median of whole-stage totals.
- Both solvers receive the same in-memory NetworkX graph objects in the same canonical graph6 order.

## Correctness gates

- Existing unit tests must pass.
- Standard named graphs, supplied n=16 counterexamples, and at least 50 fixed-seed random connected cubic graphs must agree.
- Every returned witness is checked using the definition-level checker.
- Census layer counts must match the expected values exactly.
- Any optimum or witness discrepancy aborts the performance run.

## Risks and interpretation

- Solver C uses the proved cubic structural theorem, so its results are performance evidence, not independent evidence for the theorem.
- Solver B complete-candidate counts and Solver C recursion-node counts are not identical concepts; the report will not treat them as directly interchangeable.
- Wall-clock results are machine- and software-stack-specific; raw repetitions and environment metadata will be retained.
