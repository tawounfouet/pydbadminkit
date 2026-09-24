# LOT-21 / T21-007 — Installation Smoke Tests

## Status

```text
Ticket: T21-007
Result: PASS
Python matrix: 3.11, 3.12, 3.13, 3.14
Artifacts: wheel + sdist
```

All four Package matrix jobs are green. Each interpreter successfully builds the
distribution, passes Twine validation, installs the wheel in a clean virtual environment,
installs the source distribution in a second clean environment, imports `pydbadminkit`,
and executes `pydbadmin --version` / `pydbadmin --help`.

## Qualification objective

A release artifact is not qualified merely because the source-tree tests pass.

T21-007 verifies installation from the actual artifacts produced by:

```text
python -m build
```

after `twine check`.

## Matrix

The Package workflow now runs independently on every supported Python interpreter:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

For each interpreter, both distribution forms are tested.

## Wheel smoke

A clean virtual environment installs only the generated wheel and then verifies:

```text
import pydbadminkit
pydbadminkit.__version__
pydbadmin --version
pydbadmin --help
```

This catches missing package files, broken runtime dependencies, bad entry points and
version-loading problems.

## Source-distribution smoke

A second clean virtual environment installs the generated `.tar.gz` source distribution
and repeats the same import/version/CLI checks.

This qualifies the source archive independently from the wheel.

## Release gate

The 1.0 condition:

```text
package installation validated
```

requires every Package matrix job to be green.

A source checkout that passes tests while either built artifact cannot be installed is a
release blocker.

## Next ticket

```text
T21-008 — README final
```
