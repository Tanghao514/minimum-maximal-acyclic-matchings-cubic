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

## Reproducibility boundary

The preserved `geng` files are sufficient to reproduce the complete Solver B/C
census. Regenerating the dual-generator comparison additionally requires the
missing GENREG snapshot. Graph labels and output order are generator-dependent;
isomorphism-class multisets must be canonicalized before comparison.

