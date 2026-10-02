# External graph generators

Third-party generator source and binaries are not vendored in this repository.

## nauty 2.9.3

Official source: https://users.cecs.anu.edu.au/~bdm/nauty/

The publication Solver B/C input was generated with `geng` from nauty 2.9.3.
For each supported order `n`, the recorded command is equivalent to:

```bash
geng -c -q -d3 -D3 n 3n/2
```

For example:

```bash
geng -c -q -d3 -D3 16 24 > connected_cubic_n16.g6
```

The repository wrapper avoids shell redirection and checks record counts:

```bash
python scripts/generate_census.py --geng /path/to/geng
```

`labelg` is nauty's canonical-labeling/filter utility. The manuscript reports
using it to canonicalize both generator outputs before sorted multiset
comparison.

## GENREG

Official project page: https://sourceforge.net/projects/genreg/

The final manuscript reports an independent GENREG enumeration, but its raw
files, exact version/build, commands, and comparison log were absent from the
supplied package. They are listed in `MISSING_FOR_RELEASE.md`. This repository
does not invent a command and label it as the publication invocation.

A new October 2026 rerun builds hash-pinned GENREG trunk files and nauty 2.9.3,
regenerates every layer, and compares both outputs with the preserved census.
It includes raw ASCII/graph6 outputs, canonical-class bijections, source
URLs/hashes, build logs, compiler information, and executable hashes.
See [the full guide](../verification/README.md) and the
[toolchain record](../results/post_submission/2026-10-02/generator_audit/toolchain.json).

## Reproducibility boundary

The preserved `geng` files are sufficient to reproduce the complete Solver B/C
census. The original dual-generator run cannot be reproduced without its missing
records. A fresh independent comparison can now be reproduced with
`scripts/prepare_verification_tools.py` and `scripts/run_generator_audit.py`.
Graph labels and output order are generator-dependent; isomorphism-class
multisets must be canonicalized before comparison.
