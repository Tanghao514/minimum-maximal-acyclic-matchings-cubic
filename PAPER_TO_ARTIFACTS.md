# Paper-to-artifact map

This map follows the final 27-page manuscript. “Reproduced” means derivable
from a preserved artifact by a command in this repository; it does not imply
that hardware-dependent wall times will be identical.

The [October 2026 supplement](verification/README.md) supplies new independent
verification. It does not recover the missing original Table 6 records.

| Paper item | Primary artifact | Reproduction/check | Status |
|---|---|---|---|
| Main formula | `src/constructions.py`, `src/structure.py` | `python scripts/verify_structural_certificates.py` | Code and certificates present |
| Table 1 census summary | `results/per_graph/full_census.csv` | `python scripts/reproduce_tables/reproduce_all.py` | Complete |
| Table 2 histogram | same as Table 1 | same command | Complete |
| Tables 3--4 counterexamples | `data/counterexamples/metadata.json` | `python scripts/verify_counterexamples.py` | Complete |
| Figure 1 | graph 4055 and matching in counterexample metadata | verification command above | Data complete; TikZ embedded in paper source |
| Figure 2 | local blocking lemma | `paper/main_jco.tex` near line 688 | Hand-written TikZ source present |
| Figure 3 | equality-family incidence skeleton | `paper/main_jco.tex` near line 984; construction certificates | Hand-written TikZ and machine data present |
| Solver A | `src/exact_solver.py` | `python scripts/solve_graph.py --solver A ...` | Complete |
| Solver B | `src/exact_solver.py` | `python scripts/solve_graph.py --solver B ...` | Complete |
| Solver C | `src/solver_c.py` | `python scripts/solve_graph.py --solver C ...` | Complete |
| Definition checker | `src/acyclic_matching.py` | `python -m pytest -q` | Complete |
| Structural identities | `src/structure.py` | `python scripts/verify_structural_certificates.py` | Complete |
| Table 5 Solver B/C census | raw layer JSON, per-graph CSV, processed summary | `python scripts/verify_paper_numbers.py` or full rerun | Complete |
| Table 6 generator comparison | new `results/post_submission/2026-10-02/generator_audit/` | `python scripts/verify_post_submission.py`; fresh-run guide in `verification/README.md` | New full rerun passes; original records missing |
| Table 6 endpoint audit | new `verification/endpoint_audit.cpp` and dated JSONL records | `python scripts/run_endpoint_audit.py` | New independent 4,681-graph audit passes; original source/output missing |
| Table 6 A/B and B/C checks | source/tests/full per-graph CSV | tests and paper-number verification | Available evidence present |
| Table 7 environment | `results/benchmarks/publication_environment.json` | table reproduction command | Complete |
| Table 8 equality scaling | exact generated inputs and publication CSV | table reproduction; `scripts/construct.py` | Medians/statuses complete; some raw repetitions missing |
| Solver C ablation | `results/ablations/solver_c_ablation_complete.csv` | `python scripts/verify_paper_numbers.py` | Complete, including 500 raw rows |
| All seven census files | `data/census/canonical/*.g6` | `python scripts/verify_census_counts.py` | Complete |
| Source/census hashes | publication environment and hash manifests | `python scripts/verify_hashes.py` | Complete |
| Preserved manuscript | `paper/*.pdf`, `paper/main_jco.tex` | SHA-256 manifest; visually checked during release | PDF snapshot preserved; source contains the corrected public URL, as explained in `paper/README.md` |

The three figures are hand-written TikZ in `paper/main_jco.tex`; they were not
generated from the timing CSVs. `figures/source/README.md` records the exact
source locations.
