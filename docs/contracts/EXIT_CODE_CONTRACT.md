# LOT-20 / T20-005 — CLI Exit-Code Freeze

## Status

```text
Ticket: T20-005
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Contract: frozen for the route to 1.0
```

Exit codes are a machine interface. They are therefore distinct from `ErrorCode`: a
specific error code classifies *what happened*, while the process exit code gives shell and
CI automation a compact outcome category.

## Frozen process exit codes

| Code | Meaning |
| ---: | --- |
| 0 | success / non-failing health result |
| 1 | general operational failure or failing health result |
| 2 | configuration / CLI usage failure |
| 3 | database connection failure |
| 4 | authentication / authorization failure |
| 5 | requested resource not found |
| 6 | requested capability unavailable |
| 7 | safety/guardrail policy failure |
| 8 | external tool, backup, restore or maintenance failure |
| 9 | connection or operation timeout |

## Error-to-exit mapping

```text
ConfigurationError                           → 2
DatabaseConnectionError                     → 3
AuthenticationError / AuthorizationError    → 4
ResourceNotFoundError                       → 5
CapabilityNotAvailableError                 → 6
SafetyPolicyError                           → 7
ExternalToolError                           → 8
BackupError / RestoreError / MaintenanceError → 8
DatabaseConnectionTimeoutError              → 9
OperationTimeoutError                       → 9
other PyDBAdminError                        → 1
```

Subclass ordering matters: timeout and authentication errors are checked before the broader
`DatabaseConnectionError` category.

## CLI usage failures

Typer/Click syntax failures and PyDBAdminKit validation of invalid CLI arguments use exit
code `2`.

Missing required PyDBAdminKit execution context, such as a connection profile where one is
required, also uses `2`.

## Health semantics

`health check` has a deliberate status-to-exit policy:

```text
OK       → 0
WARNING  → 0 by default
CRITICAL → 1
UNKNOWN  → 0 by default
```

With `--fail-on-warning`:

```text
WARNING → 1
```

A future `--fail-on-unknown` option remains deferred and is not part of the current
contract.

## Compatibility rules

Before a future major-version compatibility break:

- existing numeric meanings must not be reassigned;
- an existing public error category must not silently move to another exit code;
- new specific error codes should map into an existing exit category when semantically
  possible;
- adding a new exit category requires an explicit contract change and documentation;
- human-readable messages must never be parsed to infer exit semantics.

## Automated drift guard

`tests/cli/test_exit_code_contract.py` freezes representative exception-to-exit mappings.

Existing CLI tests additionally freeze:

- usage/configuration exit `2`;
- critical health exit `1`;
- default warning exit `0`;
- `--fail-on-warning` exit `1`.

## Next ticket

```text
T20-006 — config contract freeze
```
