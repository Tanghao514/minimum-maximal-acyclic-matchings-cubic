# Order-16 counterexamples

`counterexamples.g6` contains the four canonical graph6 records printed in
Table 4 of the manuscript. `metadata.json` records the Table 3 matchings and
invariants, and maps each paper ID to the isomorphic record in the independent
`geng` census included in this repository.

The two identifiers are intentionally kept separate. The manuscript IDs come
from a GENREG collection canonicalized and sorted with `labelg`; the
`n16_NNNN` identifiers are line positions in the preserved `geng` collection.
The verification script checks graph isomorphism rather than assuming that the
two generators used the same vertex labels or ordering.

Run from the repository root:

```bash
python scripts/verify_counterexamples.py
```

