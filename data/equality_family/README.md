# Equality-family inputs

Each `nNN.g6` file is the exact deterministic graph produced by
`extremal_graph_for_order_direct(NN)`, the constructor used by the publication
Table 8 script. Each matching JSON file contains the graph6 record, matching,
construction parameters, definition checks, and structural certificate.

Regenerate an entry with:

```bash
python scripts/construct.py --n 26 --output-json reproduced/n26.json --output-g6 reproduced/n26.g6
```

The equality-family timing CSV preserves medians and statuses. See
`MISSING_FOR_RELEASE.md` for the unavailable individual repetitions at orders
16 through 28.

