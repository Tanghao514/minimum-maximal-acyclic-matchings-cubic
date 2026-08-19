# Solver C: theory-guided exact solver for connected cubic graphs

This package adds a third exact solver for the minimum maximal acyclic matching problem.

## Main entry points

```python
from src.solver_c import (
    minimum_maximal_acyclic_matching_cubic,
    find_maximal_acyclic_matching_at_most_k_cubic,
)
```

`minimum_maximal_acyclic_matching_cubic(G)` returns the exact optimum and one witness for a nonempty connected simple cubic NetworkX graph.

`find_maximal_acyclic_matching_at_most_k_cubic(G, K)` implements the decision/search form and rejects immediately when `|V(G)| > 5K+1`.

## Algorithmic ideas

- contract every selected matching edge;
- precompute endpoint conflicts, cycle conflicts, and one-cross-edge links;
- maintain the contracted link forest with rollback DSU;
- use the theorem-derived defect budget `delta <= 5k+1-n`;
- use a specialized independent-domination search when the defect budget is zero;
- use near-leaf rigid-maximality hitting-set pruning otherwise;
- verify every returned witness with the independent definition-level routine.

The solver intentionally uses the proved cubic lower bound. It is therefore a post-theorem exact algorithm and must not replace Solver A/B or the endpoint-set audit as an independent validation of that theorem.

## Install and test

```bash
python -m pip install networkx pytest
PYTHONPATH=. pytest -q
```

Expected result in the supplied environment:

```text
12 passed
```

## Reproduce the audits and benchmarks

```bash
PYTHONPATH=. python scripts/audit_solver_c.py
PYTHONPATH=. python scripts/benchmark_solver_c_medians.py
PYTHONPATH=. python scripts/ablate_solver_c.py
```

Key outputs:

- `results/solver_c_audit.json`
- `results/solver_c_benchmark_medians.csv`
- `results/solver_c_benchmark_medians.json`
- `results/solver_c_ablation.csv`
- `results/solver_c_zero_defect_scaling.csv`

The benchmark is a controlled development benchmark rather than a universal performance claim. General worst-case running time remains exponential.
