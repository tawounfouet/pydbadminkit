# LOT-20 / T20-002 — CLI Contract Inventory

## Status

```text
Ticket: T20-002
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Purpose: inventory the CLI surface before the 1.0 freeze
```

This inventory records the command hierarchy and root cross-cutting options that users and
automation can rely on today. It is a hardening baseline, not yet the final 1.0 freeze.

## Executable

```text
pydbadmin
```

The root command is implemented with Typer and is intentionally CLI-first while all
business logic remains behind application services.

## Root options

```text
--connection, -c     select a named connection profile
--config             select config.toml
--output, -o         table | json | yaml
--dry-run            plan mutations without applying them
--yes, -y            approve simple/explicit confirmations
--non-interactive    never prompt
--version            print the installed version and exit
--help               Typer/Click help
```

The first six options above are cross-cutting execution context. `--version` is eager.
`--help` is framework-provided.

## Command tree

```text
pydbadmin
├── connection
│   └── test
├── backup
│   ├── create
│   ├── validate
│   └── restore
├── server
│   └── info
├── database
│   ├── list
│   └── describe
├── schema
│   ├── list
│   └── describe
├── table
│   ├── list
│   └── describe
├── view
│   ├── list
│   └── describe
├── index
│   ├── list
│   └── describe
├── role
│   ├── list
│   ├── describe
│   ├── create
│   ├── alter
│   ├── drop
│   ├── membership-add
│   └── membership-remove
├── access
│   ├── list
│   ├── grant
│   └── revoke
├── effective-access
│   └── list
├── ownership
│   └── list
├── postgres
│   ├── vacuum
│   ├── analyze
│   ├── reindex
│   └── progress
│       ├── vacuum
│       └── reindex
├── session
│   ├── list
│   └── terminate
├── query
│   ├── list
│   └── cancel
├── transaction
│   └── list
├── wait
│   └── list
├── lock
│   └── list
├── blocking
│   └── list
├── capability
│   ├── list
│   └── get
└── health
    └── check
```

## Read-only versus mutation commands

Read-only inspection commands include the catalog, security inspection, runtime inspection,
capability and health surfaces.

The current mutation surface is:

```text
backup create
backup restore
role create
role alter
role drop
role membership-add
role membership-remove
access grant
access revoke
postgres vacuum
postgres analyze
postgres reindex
session terminate
query cancel
```

Mutation commands are routed through the safety/guardrail pipeline. The root `--dry-run`,
`--yes` and `--non-interactive` options therefore form part of the cross-cutting CLI
contract.

`backup validate` is read-only validation of an artifact.

## Output contract

The root `--output` option selects:

```text
table
json
yaml
```

Machine-readable payload shape is inventoried separately by T20-003. T20-002 freezes only
the presence and spelling of the root output selector.

## Health-specific CI semantics

```text
pydbadmin health check
pydbadmin health check --fail-on-warning
```

The default health exit policy remains:

```text
OK       → 0
WARNING  → 0
CRITICAL → 1
UNKNOWN  → 0
```

Exit-code freeze is handled separately by T20-005.

## Compatibility policy for hardening

Before 1.0, a change is considered a CLI contract change when it:

- removes or renames a command path;
- removes or renames a root option;
- changes a command from read-only to mutation semantics;
- changes the meaning of a cross-cutting safety option;
- removes a machine output format.

Adding a new command or option is additive, but must still be reviewed for naming,
machine-interface and safety consistency.

## Automated drift guard

`tests/cli/test_cli_contract_inventory.py` introspects the Typer application through its
Click command tree and freezes:

- all current command paths;
- all explicit root option spellings.

This makes accidental command renames/removals visible in CI.

## Next ticket

```text
T20-003 — JSON contract inventory
```
