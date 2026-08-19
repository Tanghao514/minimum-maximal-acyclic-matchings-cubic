# Solver C implementation notes

Solver C is an exact, post-theorem branch-and-bound procedure for nonempty
connected simple cubic graphs.

For each pair of candidate matching edges it precomputes endpoint conflicts,
cycle conflicts, and single-edge links. A selected set is an acyclic matching
exactly when it has no hard conflict and its induced link graph is a forest.
Rollback DSU operations make this invariant incremental.

For target size `k`, the structural theorem supplies a defect limit
`min(k-1, 5k+1-n)`. A negative limit rejects the target. Limit zero is handled
by a specialized domination search over a zero-defect compatibility graph;
positive limits use the generic interaction-forest search.

The implementation records:

- complete candidates and total recursive nodes;
- cycle, defect, capacity, defect-lower-bound, profile, and rigid-maximality
  prunes;
- zero-defect nodes, cache hits, and failed states;
- each attempted target and its outcome.

The final matching is always validated by `src/acyclic_matching.py`.

The full ablation script toggles the theorem defect budget, zero-defect
specialization, failed-state memoization, and near-leaf maximality pruning.

