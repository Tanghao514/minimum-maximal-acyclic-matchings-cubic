# Solver B vs Solver C: complete cubic-census benchmark report

## Outcome

The core experiment completed successfully. Solver B and Solver C agreed on all 4,681 connected simple cubic graphs through order 16, with no invalid witnesses, discrepancies, or timeouts. At n=16, whole-layer median time decreased from 94.1762 s to 32.4600 s (2.90x), while the median per-graph speedup was 4.58x.

## Protocol and reproducibility

- Generator: nauty 2.9.3 `geng -c -q -d3 -D3 n (3n/2)`, graph6 output.
- Verified census sizes: 1, 2, 5, 19, 85, 509, 4,060; total 4,681.
- Correctness gate: 10 standard/prism graphs, four supplied n=16 counterexamples, and 50 fixed-seed random connected cubic graphs. Both solvers' witnesses were checked by the definition-level predicate.
- Timing: `time.perf_counter`, graph loading excluded, one warm-up, alternating solver order, five whole-layer repetitions through n=12 and three at n=14,16.
- Execution: single-threaded calls, no concurrent benchmark jobs. Two previously running stress jobs were stopped before formal timing.
- Machine: Windows 11 build 26200, AMD Ryzen 7 7435H (8 physical/16 logical cores), 15.74 GiB RAM, CPython 3.11.7, NetworkX 3.1.
- Exact source and census SHA-256 values are in `environment.json`.

## Main census results

| n | graphs | B total (s) | C total (s) | speedup | B candidates | C candidates | reduction | discrepancies |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 1 | 0.0008 | 0.0010 | 0.88x | 2 | 1 | 50.00% | 0 |
| 6 | 2 | 0.0053 | 0.0040 | 1.33x | 5 | 2 | 60.00% | 0 |
| 8 | 5 | 0.0127 | 0.0126 | 1.01x | 70 | 5 | 92.86% | 0 |
| 10 | 19 | 0.0839 | 0.0896 | 0.94x | 989 | 358 | 63.80% | 0 |
| 12 | 85 | 0.4467 | 0.3775 | 1.18x | 11,151 | 179 | 98.39% | 0 |
| 14 | 509 | 5.9727 | 4.8901 | 1.22x | 224,027 | 43,691 | 80.50% | 0 |
| 16 | 4,060 | 94.1762 | 32.4600 | 2.90x | 4,832,310 | 40,158 | 99.17% | 0 |
| All | 4,681 | 100.6984 | 37.8348 | 2.66x | 5,068,554 | 84,394 | 98.34% | 0 |

The node columns count complete candidates in both implementations. Solver C recursion nodes are retained separately in the per-graph CSV; they are not substituted for Solver B's complete-candidate count.

## Per-graph distribution

- Across all 4,681 graphs: median speedup 4.41x, geometric mean 3.81x, arithmetic mean 4.14x.
- At n=16: median 4.58x, geometric mean 4.46x, interquartile range 4.00x--5.11x, range 1.08x--8.22x.
- Solver C was slower on 127 graphs: 1 at n=4, 4 at n=8, 9 at n=10, 5 at n=12, and 108 at n=14. It was not slower on either n=6 graph or any n=16 graph.
- Slowest relative case: `n14_0369`, speedup 0.479x (B 0.00421 s, C 0.00879 s).
- Fastest census case: `n16_2873`, speedup 8.219x (B 0.02425 s, C 0.00295 s).

Tiny-instance results are dominated by interpreter, object-construction, and pruning-overhead costs, so the n=4--10 ratios should not be overinterpreted.

## Optimum and defect-budget groups

The defect budget was recorded as `5 mu + 1 - n`, with values at least five placed in one bin. Within n=10, the budget-one group had geometric-mean speedup 1.09x, whereas the at-least-five group had 0.70x. Within n=14, the budget-two and at-least-five groups had geometric means 1.44x and 1.14x. These comparisons support the expected tendency that tighter structural budgets help Solver C, although optimum and graph structure remain confounders.

Only four n=16 census graphs have optimum 3 and zero defect. Their geometric-mean speedup was 5.23x, compared with 4.46x for the 4,056 optimum-four graphs. This is consistent with a useful zero-defect specialization but is too small a census stratum for a broad standalone statistical claim.

## Equality family

Both solvers used a common 300 s timeout. Orders through 28 used three repetitions; larger orders used one run. Solver B completed n=36 in 290.51 s but timed out at n=46 and n=56. Solver C solved every case, including n=46 in 0.0214 s and n=56 in 0.0297 s. The 16,894x ratio at n=36 is a structured equality-instance result and must not be reported as average census performance.

## Ablation

Five variants were run three times on a deterministic, stratified 100-graph sample from n=16 (four zero-defect graphs and 96 defect-five graphs).

- On the four zero-defect graphs, full Solver C had median search time 0.000075 s and median 4 recursion nodes.
- Disabling the structural defect budget raised the zero-defect median to 0.001136 s (about 15.2x) and 24 nodes.
- Replacing the zero-defect special solver with generic interaction-forest search raised the median to 0.000728 s (about 9.7x) and 20.5 nodes.
- Removing failed-state memoization made essentially no difference on these four found-solution searches; no general claim about hard unsatisfiable states follows.
- On the 96 defect-five graphs, the theorem defect expression exceeds the universal `k-1` cap, so the defect-budget ablation is intentionally identical to full search. Removing near-leaf pruning increased total recursion nodes from 1,853 to 3,268, but its median microbenchmark time was slightly lower because the pruning check has overhead.

## Answers to the required questions

1. **Do the solvers always agree?** Yes, on all 4,681 census graphs and all 64 gate cases.
2. **Was the entire 4,681-graph census covered?** Yes; every expected layer count matched exactly.
3. **What are the total runtimes?** Summed layer medians are 100.6984 s for B and 37.8348 s for C.
4. **What is the aggregate speedup?** 2.66x across all layers and 2.90x at n=16.
5. **What are median/geometric-mean per-graph speedups?** 4.41x/3.81x overall; 4.58x/4.46x at n=16.
6. **Is C ever slower?** Yes, on 127 small-order graphs, but on no n=16 graph.
7. **What are the extremes?** 0.479x on `n14_0369`; 8.219x on `n16_2873` within the census.
8. **How does defect relate to speedup?** Tighter within-order budgets generally correspond to greater speedup, with the caveats above.
9. **Is zero-defect useful?** Yes on the four n=16 zero-defect graphs and especially on zero-defect equality instances; the census stratum is small.
10. **Which components contribute most?** The zero-defect specialization and structural budget dominate the zero-defect sample; near-leaf pruning reduces nodes but not measured micro-time; memoization was inactive here.
11. **Where do timeouts begin?** No core-census timeouts. Solver B first timed out at n=46 in the equality family; C had none.
12. **What belongs in the main text?** Census correctness, the main table, n=16 aggregate/distribution results, and the theorem-dependence caveat.
13. **What belongs in the supplement?** Equality-family scaling, full distributions, defect groups, ablation details, hashes, raw repetitions, and graph6 rows.
14. **What threatens validity?** One machine/software stack, canonical input ordering only, timer noise on tiny graphs, single runs for equality orders above 28, censored timeout data, and theorem dependence of Solver C.

## Scope decisions

The optional exhaustive n=18 census was not run. Core n<=16 coverage, equality-family scaling, and the requested small ablation were completed first; a reliable full n=18 input would be much larger and was not needed for the stated core claim.
