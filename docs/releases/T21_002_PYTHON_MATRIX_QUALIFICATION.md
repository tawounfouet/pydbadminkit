# LOT-21 / T21-002 — Python Matrix Qualification

## Status

```text
Ticket: T21-002
Result: PASS
Supported Python: 3.11, 3.12, 3.13, 3.14
Qualification mechanism: full unit suite on every supported interpreter
```

## Qualified result

```text
Python 3.11  419 passed / 44 deselected / coverage 86.15%
Python 3.12  419 passed / 44 deselected / coverage 86.15%
Python 3.13  419 passed / 44 deselected / coverage 86.15%
Python 3.14  419 passed / 44 deselected / coverage 85.64%
```

Every supported interpreter clears the required 85% coverage gate.

## Contract

The package declares:

```text
requires-python = ">=3.11"
```

and advertises Python 3.11 through 3.14 classifiers.

T21-002 aligns executable CI with that metadata. The Unit Tests workflow now runs the
complete unit suite independently on:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

with `fail-fast: false` so one interpreter failure cannot hide the status of the others.

## Axis separation

The release matrix deliberately separates compatibility dimensions:

```text
Python matrix
    3.11 → 3.14
    unit/domain/application/adapter contract qualification

PostgreSQL matrix
    PostgreSQL 14 → 18
    Python fixed at 3.13
    live database integration qualification
```

This avoids a 4 × 5 Cartesian CI matrix while still making both compatibility promises
executable.

## Release gate

A Python version is not considered qualified for 1.0 unless its Unit Tests matrix job is
green.

The package build and clean-wheel installation remain separate release-artifact gates and
are expanded in T21-007.

## Next ticket

```text
T21-003 — backup → restore qualification
```
