# Algorithms

## Definition

A matching `M` is acyclic when the graph induced by all endpoints of `M` is a
forest. It is maximal when no additional graph edge can be added while
preserving both the matching and acyclicity conditions. The objective is the
minimum cardinality among maximal acyclic matchings.

`src/acyclic_matching.py` implements these definitions directly. All solver
certificates are checked by this reference implementation before return.

## Solver A

`minimum_maximal_acyclic_matching_bruteforce` enumerates edge subsets in
increasing cardinality with `itertools.combinations`, filters matchings, and
calls the reference maximal-acyclic predicate. It is intentionally slow and is
used only for small independent comparisons.

## Solver B

`minimum_maximal_acyclic_matching` relabels vertices to bit positions,
enumerates matchings in increasing cardinality, evaluates the complete induced
endpoint graph, and caches forest/maximality tests. It does not replace the
endpoint-induced graph with the selected matching edges.

Solver B is theorem-independent and supplies the benchmark reference optimum.

## Solver C

`minimum_maximal_acyclic_matching_cubic` is specialized to connected cubic
graphs. It contracts selected matching edges conceptually and precomputes:

- hard conflicts (shared endpoints or a two-edge interaction that makes an
  induced cycle), and
- links (one cross edge between endpoint pairs).

A rollback disjoint-set union structure maintains whether the linked
interaction graph is a forest. The theorem gives the defect budget
`delta <= 5k + 1 - n`; at the lower-bound target this budget is at most four.
The solver also has a specialized zero-defect domination search, failed-state
memoization, capacity/profile bounds, and near-leaf maximality pruning.

Because Solver C uses the proved theorem, its agreement with Solver B validates
the implementation but is not independent evidence for the theorem.

## Construction and structure

`src/constructions.py` constructs a connected simple cubic graph with a
certificate of size `ceil((n-1)/5)` for every even `n >= 4`. The direct
constructor handles base and residue cases, the path--cycle special family,
and exceptional orders 4, 8, and 12.

`src/structure.py` turns a maximal acyclic matching into a machine-checkable
decomposition and checks the identities and inequalities used in the proof.

