# Solver C ablation artifact

`solver_c_ablation_complete.csv` contains 500 rows: 100 deterministic
order-16 graph IDs times five variants. Every row preserves three raw timing
repetitions plus search-node and pruning counts.

The sample-selection and variant implementation are frozen in
`scripts/run_solver_c_ablation_complete.py`. No random sampling was used.

Verify the manuscript aggregates with:

```bash
python scripts/verify_paper_numbers.py
```

