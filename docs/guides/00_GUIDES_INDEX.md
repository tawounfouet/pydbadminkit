# PyDBAdminKit Guides

This directory is the task-oriented documentation for **PyDBAdminKit 1.0**.

The guides answer **how to use the framework**. Normative contracts remain under
`docs/reference/` and `docs/contracts/`; architecture, security reviews, qualification
evidence and release records remain in their dedicated documentation directories.

## Documentation model

```text
README.md
    What is PyDBAdminKit? How do I start quickly?

docs/guides/
    How do I use PyDBAdminKit safely and effectively?

docs/reference/
    What exactly is the supported CLI/Python contract?

docs/contracts/
    Which machine/error/exit/config contracts are frozen?

docs/design/, docs/security/, docs/quality/, docs/releases/
    Why is the framework designed this way and how was it qualified?
```

A guide may explain a contract, but it does not redefine it. If a guide and a normative
reference ever disagree, the 1.0 reference/contract documentation is authoritative.

## Supported baseline

The 1.0 guide set targets:

| Component | 1.0 support |
| --- | --- |
| Python | 3.11, 3.12, 3.13, 3.14 |
| PostgreSQL 15–18 | Tier A |
| PostgreSQL 14 | Transitional |
| Psycopg | >=3.3,<4 |
| CLI | `pydbadmin` |
| Human output | table |
| Machine output | JSON, YAML |
| License | Apache-2.0 |

Linux is the authoritative automated CI environment. macOS and Windows are portability
targets. Managed PostgreSQL services are best-effort semantic targets and may restrict
privileged operations.

## Guide map

### Part I — Start here

1. [Getting started](01_GETTING_STARTED.md)
2. [Installation](02_INSTALLATION.md)
3. [First connection](03_FIRST_CONNECTION.md)
4. [Configuration and profiles](04_CONFIGURATION_AND_PROFILES.md)
5. [Credentials and secrets](05_CREDENTIALS_AND_SECRETS.md)

### Part II — Interfaces

6. [CLI fundamentals](06_CLI_FUNDAMENTALS.md)
7. [Table, JSON and YAML output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md)
8. [Python API fundamentals](08_PYTHON_API_FUNDAMENTALS.md)

### Part III — Object Explorer

9. [Database exploration](09_DATABASE_EXPLORATION.md)
10. [Schemas, tables, views and indexes](10_SCHEMA_TABLE_VIEW_AND_INDEX_EXPLORATION.md)

### Part IV — Security Administration

11. [Security administration](11_SECURITY_ADMINISTRATION.md)
12. [Roles, memberships and privileges](12_ROLES_MEMBERSHIPS_AND_PRIVILEGES.md)
13. [Effective access and ownership](13_EFFECTIVE_ACCESS_AND_OWNERSHIP.md)

### Part V — Runtime Administration

14. [Runtime administration](14_RUNTIME_ADMINISTRATION.md)
15. [Sessions, queries and transactions](15_SESSIONS_QUERIES_AND_TRANSACTIONS.md)
16. [Locks, waits and blocking chains](16_LOCKS_WAITS_AND_BLOCKING_CHAINS.md)
17. [Cancel and terminate operations](17_CANCEL_AND_TERMINATE_OPERATIONS.md)

### Part VI — Operations

18. [Backup](18_BACKUP_GUIDE.md)
19. [Restore](19_RESTORE_GUIDE.md)
20. [Maintenance](20_MAINTENANCE_GUIDE.md)

### Part VII — Monitoring and health

21. [Monitoring](21_MONITORING_GUIDE.md)
22. [Health checks](22_HEALTH_CHECKS.md)
23. [Observability and metrics](23_OBSERVABILITY_AND_METRICS.md)

### Part VIII — Safety and failure semantics

24. [Dry-run, guardrails and confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
25. [Audit and operation traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
26. [Error handling and exit codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)

### Part IX — Automation

27. [Automation and machine interface](27_AUTOMATION_AND_MACHINE_INTERFACE.md)
28. [Shell scripting and CI/CD](28_SHELL_SCRIPTING_AND_CI_CD.md)
29. [Python automation patterns](29_PYTHON_AUTOMATION_PATTERNS.md)

### Part X — Production and troubleshooting

30. [PostgreSQL version compatibility](30_POSTGRESQL_VERSION_COMPATIBILITY.md)
31. [Production usage and safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
32. [Troubleshooting](32_TROUBLESHOOTING.md)
33. [Common recipes](33_COMMON_RECIPES.md)
34. [End-to-end scenarios](34_END_TO_END_SCENARIOS.md)
35. [Next steps](35_NEXT_STEPS.md)

Files are added progressively. A link in this index represents the planned 1.0 guide
curriculum; use the status table below to see which guides have been written.

## Suggested learning paths

### New user

```text
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08
```

Goal: install the framework, connect safely, understand profiles, use the CLI and start
with the stable Python API.

### DBA / operations

```text
01 → 03 → 09 → 10 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22
```

Goal: inspect a PostgreSQL server, diagnose runtime state, operate backups/restores and
perform guarded maintenance.

### Security administrator

```text
01 → 04 → 05 → 11 → 12 → 13 → 24 → 25 → 26 → 31
```

Goal: understand effective access and perform mutations without bypassing the framework's
safety model.

### Automation / Data Engineering

```text
01 → 04 → 07 → 08 → 26 → 27 → 28 → 29
```

Goal: consume deterministic machine output and integrate PyDBAdminKit into scripts and
Python applications.

### Production operator

```text
01 → 04 → 05 → 18 → 19 → 20 → 22 → 24 → 25 → 26 → 30 → 31 → 32
```

Goal: understand operational preflight, confirmation, failure, compatibility and audit
semantics before performing production mutations.

## Guide conventions

Each detailed guide should use the following structure when applicable:

```text
Objective
Prerequisites
Concepts
Configuration
CLI usage
Python API usage
Table output
JSON/YAML output
Worked example
Dry-run and safety
Errors
Troubleshooting
Production considerations
Best practices
Key takeaways
See also
```

Commands must reflect the current 1.0 CLI reference. Python examples must use the public
1.0 surface: bootstrap builders, domain objects, application services, ports and public
errors. Examples must not teach consumers to depend on `adapters.*`,
`infrastructure.*` or `cli.*` internals.

Mutation examples should prefer `--dry-run` before execution and must preserve the
framework's confirmation, read-only, environment and audit semantics.

Secrets must never be embedded in committed configuration examples. Persist secret
references and provide secret values at the execution boundary.

## Current authoring status

| Guide | Status |
| --- | --- |
| 00 — Guides index | Complete |
| 01 — Getting started | Complete |
| 02 — Installation | Complete |
| 03 — First connection | Complete |
| 04 — Configuration and profiles | Complete |
| 05 — Credentials and secrets | Complete |
| 06 — CLI fundamentals | Complete |
| 07 — Table, JSON and YAML output | Complete |
| 08 — Python API fundamentals | Complete |
| 09 — Database exploration | Complete |
| 10 — Schemas, tables, views and indexes | Complete |
| 11 — Security administration | Complete |
| 12 — Roles, memberships and privileges | Complete |
| 13 — Effective access and ownership | Complete |
| 14 — Runtime administration | Complete |
| 15–35 | Planned |

## Normative references

- `../reference/CLI_REFERENCE.md`
- `../reference/PYTHON_API_REFERENCE.md`
- `../reference/SUPPORT_MATRIX.md`
- `../reference/MIGRATION_AND_DEPRECATION_POLICY.md`
- `../contracts/ERROR_CODE_CONTRACT.md`
- `../contracts/EXIT_CODE_CONTRACT.md`

## Version

This guide curriculum starts with **PyDBAdminKit 1.0.0**.
