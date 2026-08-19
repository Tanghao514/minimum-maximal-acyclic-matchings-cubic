# Data formats and identifiers

## graph6

Every `.g6` file is ASCII text with one headerless graph6 record per line.
NetworkX reads a record with `nx.from_graph6_bytes(record.encode("ascii"))`.

## Census identifiers

In `results/per_graph/full_census.csv`, `graph_id=n16_0708` means zero-based
line 708 of this repository's preserved `geng` order-16 file. It is not a
universal canonical identifier.

The manuscript counterexample IDs 4055, 4056, 4058, and 4059 refer to the
separately generated GENREG/`labelg` ordering. `data/counterexamples/metadata.json`
stores both namespaces and an isomorphic graph6 representative for each.

## Full per-graph CSV

Important columns:

- `n`, `graph_id`, `graph6`: input identity.
- `mu_solver_b`, `mu_solver_c`: exact optimums.
- `runtime_solver_b`, `runtime_solver_c`: median per-graph time across the
  layer's repetitions.
- `solver_b_times`, `solver_c_times`: JSON arrays of all raw repetitions.
- `search_nodes_solver_b`, `search_nodes_solver_c`: complete candidates.
- `solver_c_recursion_nodes`: Solver C recursive search nodes.
- `speedup`, `node_reduction`, `defect_budget`, `repetitions`: derived or
  protocol fields.

No original column was removed in the release-cleanup copy.

## Ablation CSV

There are 500 rows. `raw_times` is a JSON array of three timings. Variants are
`c_full`, `c_without_defect_budget`,
`c_without_zero_defect_special_solver`,
`c_without_failed_state_memoization`, and
`c_without_near_leaf_maximality_pruning`.

## JSON certificates

Construction JSON files contain the graph6 record, matching edge list,
construction metadata, definition checks, and a structural certificate.
Vertex labels are zero-based integers.

