# PyDBAdminKit CLI Reference

## Executable

```text
pydbadmin
```

All command groups use the root execution context. Run `pydbadmin <group> <command> --help`
for Typer-generated parameter details.

## Root options

| Option | Meaning |
| --- | --- |
| `--connection, -c` | named connection profile |
| `--config` | path to TOML configuration |
| `--output, -o` | `table`, `json` or `yaml` |
| `--dry-run` | plan a mutation without applying it |
| `--yes, -y` | approve simple/explicit confirmations |
| `--non-interactive` | never prompt |
| `--version` | print installed version and exit |
| `--help` | command help |

Typer also provides shell-completion options.

## Connection and server

```text
connection test
server info
```

Both require a selected connection profile.

## Catalog

```text
database list
database describe <name>

schema list [--include-system]
schema describe <name>

table list [--schema <schema>] [--include-system]
table describe <schema.table>

view list [--schema <schema>] [--include-system]
view describe <schema.view>

index list [--schema <schema>] [--table <table>] [--include-system]
index describe <schema.index>
```

## Security inspection

```text
role list [--include-system] [--login-only]
role describe <name>

access list --role <role>
            [--schema <schema>]
            [--object <relation>]
            [--include-system]

effective-access list --role <role>
                      [--schema <schema>]
                      [--object <relation>]
                      [--include-system]

ownership list --owner <role>
               [--type <object-type>]
               [--schema <schema>]
               [--include-system]
```

## Security mutations

```text
role create <name>
  [--login]
  [--superuser]
  [--createdb]
  [--createrole]
  [--replication]
  [--inherit / --no-inherit]
  [--bypass-rls]
  [--connection-limit <n>]
  [--confirm-target <target>]

role alter <name>
  [--login enable|disable]
  [--superuser enable|disable]
  [--createdb enable|disable]
  [--createrole enable|disable]
  [--replication enable|disable]
  [--inherit enable|disable]
  [--bypass-rls enable|disable]
  [--connection-limit <n>]
  [--confirm-target <target>]

role drop <name> [--confirm-target <target>]

role membership-add <role> <member>
  [--admin-option]
  [--confirm-target <target>]

role membership-remove <role> <member>
  [--confirm-target <target>]

access grant
  --role <role>
  --object <schema.relation>
  --access <access-type>
  [--grant-option]
  [--confirm-target <target>]

access revoke
  --role <role>
  --object <schema.relation>
  --access <access-type>
  [--confirm-target <target>]
```

These commands use the root mutation controls `--dry-run`, `--yes` and
`--non-interactive`. Critical plans may require exact `--confirm-target` proof;
`--yes` does not bypass it.

## Runtime inspection

```text
session list
  [--database <database>]
  [--user <user>]
  [--state <state>]
  [--include-self]

query list
  [--database <database>]
  [--user <user>]
  [--include-self]

transaction list
  [--database <database>]
  [--user <user>]
  [--include-self]

wait list
  [--database <database>]
  [--user <user>]
  [--type <wait-event-type>]
  [--include-self]

lock list
  [--database <database>]
  [--user <user>]
  [--waiting-only]
  [--include-self]

blocking list
  [--database <database>]
  [--user <user>]
  [--include-self]
```

## Runtime mutations

```text
query cancel <pid> [--confirm-target <target>]
session terminate <pid> [--confirm-target <target>]
```

These are guarded/audited mutations.

## Backup and restore

```text
backup create <database>
  [--format <format>]
  [--output-path <path>]
  [--compress]
  [--checksum / --no-checksum]
  [--jobs <n>]
  [--timeout <seconds>]
  [--force]

backup validate <path>
  [--timeout <seconds>]

backup restore <path>
  --database <target>
  [--clean]
  [--create]
  [--jobs <n>]
  [--timeout <seconds>]
  [--confirm-target <target>]
```

Implemented backup formats are custom and plain SQL. Restore uses `pg_restore` for custom
archives and `psql` for plain SQL.

## PostgreSQL maintenance

```text
postgres vacuum
  [--table <schema.table>]
  [--full]
  [--freeze]
  [--analyze]
  [--statement-timeout <seconds>]
  [--lock-timeout <seconds>]
  [--confirm-target <target>]

postgres analyze
  [--table <schema.table>]
  [--column <column>]...
  [--statement-timeout <seconds>]
  [--lock-timeout <seconds>]
  [--confirm-target <target>]

postgres reindex
  (--index <schema.index> | --table <schema.table>)
  [--concurrently]
  [--statement-timeout <seconds>]
  [--lock-timeout <seconds>]
  [--confirm-target <target>]

postgres progress vacuum
postgres progress reindex
```

## Capability discovery

```text
capability list
capability get <name>
```

Capability names are a frozen 1.0 machine contract.

## Health

```text
health check
  [--fail-on-warning]
  [--connection-warning-ratio <float>]
  [--connection-critical-ratio <float>]
  [--query-warning-seconds <float>]
  [--query-critical-seconds <float>]
  [--transaction-warning-seconds <float>]
  [--transaction-critical-seconds <float>]
  [--idle-transaction-warning-seconds <float>]
  [--idle-transaction-critical-seconds <float>]
  [--lock-warning-count <int>]
  [--lock-critical-count <int>]
```

Default exit semantics:

```text
OK       0
WARNING  0
CRITICAL 1
UNKNOWN  0
```

`--fail-on-warning` makes WARNING return 1.

## Machine output

Select machine output at the root:

```bash
pydbadmin --connection local --output json database list
pydbadmin --connection local --output yaml health check
```

JSON is the primary frozen machine contract. Machine output does not mix human table
labels into stdout.

## Exit/error contracts

Stable exit codes and machine error identifiers are documented separately in:

```text
docs/contracts/EXIT_CODE_CONTRACT.md
docs/contracts/ERROR_CODE_CONTRACT.md
```

## 1.0 compatibility

Removing/renaming a command or root option, changing a command from inspection to mutation,
changing safety-option semantics, or removing a machine-output format is a compatibility
change for the 1.0 line.
