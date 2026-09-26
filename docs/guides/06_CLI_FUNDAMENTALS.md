# PyDBAdminKit 1.0 — CLI Fundamentals

## Objective

Understand how the `pydbadmin` command-line interface is structured, how global options propagate
to subcommands, how to discover commands safely, and how inspection, mutation, machine output and
exit semantics fit together.

This guide is a navigation guide. Detailed administration workflows are covered later.

## Executable

The installed CLI entry point is:

```text
pydbadmin
```

Run it without arguments:

```bash
pydbadmin
```

The root application is configured with `no_args_is_help=True`, so the command displays help
instead of attempting an operation.

You can also request help explicitly:

```bash
pydbadmin --help
```

## Command shape

The normal structure is:

```text
pydbadmin [root options] <group> <command> [command options] [arguments]
```

Example:

```bash
pydbadmin \
  --config ./config.toml \
  --connection local \
  --output table \
  database list
```

Root options are parsed once and stored in the shared CLI context. Subcommands then consume that
same context.

## Root options

The stable 1.0 root options are:

| Option | Meaning |
| --- | --- |
| `--connection, -c` | select a named connection profile |
| `--config` | select the TOML configuration file |
| `--output, -o` | choose `table`, `json` or `yaml` |
| `--dry-run` | plan supported mutations without applying them |
| `--yes, -y` | approve simple/explicit confirmations |
| `--non-interactive` | never prompt |
| `--version` | print the installed version and exit |
| `--help` | show command help |

Example:

```bash
pydbadmin \
  --config ./config.toml \
  -c prod \
  -o json \
  server info
```

## Shared CLI context

The root CLI stores the following execution state:

```text
connection_profile
config_path
output_format
dry_run
assume_yes
non_interactive
```

This means a root option such as:

```bash
--connection prod
```

does not belong specifically to `server info`, `database list` or `health check`. It belongs
to the entire command invocation.

Prefer the documented shape:

```bash
pydbadmin -c prod --output json database list
```

rather than scattering root options after nested commands.

## Version

Check the installed version with:

```bash
pydbadmin --version
```

The output format is:

```text
pydbadminkit <version>
```

For this guide curriculum, the intended baseline is PyDBAdminKit 1.0.0.

## Help discovery

Use help progressively.

Root help:

```bash
pydbadmin --help
```

Group help:

```bash
pydbadmin database --help
pydbadmin role --help
pydbadmin postgres --help
```

Command help:

```bash
pydbadmin database list --help
pydbadmin role create --help
pydbadmin postgres reindex --help
```

This is the safest way to discover command-local arguments and options without relying on an old
example.

## Command groups

PyDBAdminKit 1.0 registers 21 command groups:

```text
connection
backup
server
database
schema
table
view
index
role
access
effective-access
ownership
postgres
session
query
transaction
wait
lock
blocking
capability
health
```

These groups fall naturally into several operational families.

## Connection and server

```text
connection
server
```

Implemented commands:

```text
connection test
server info
```

Examples:

```bash
pydbadmin -c local connection test
pydbadmin -c local server info
```

The connection group does not provide profile CRUD in 1.0.

## Catalog exploration

The object-explorer groups are:

```text
database
schema
table
view
index
```

Examples:

```bash
pydbadmin -c local database list
pydbadmin -c local database describe postgres

pydbadmin -c local schema list
pydbadmin -c local schema describe public

pydbadmin -c local table list --schema public
pydbadmin -c local table describe public.orders

pydbadmin -c local view list --schema public
pydbadmin -c local view describe public.active_orders

pydbadmin -c local index list --schema public
pydbadmin -c local index describe public.orders_pkey
```

These commands are inspection-oriented.

## Security administration

Security inspection is exposed through:

```text
role
access
effective-access
ownership
```

Examples:

```bash
pydbadmin -c local role list
pydbadmin -c local role describe app_user

pydbadmin -c local access list --role app_user
pydbadmin -c local effective-access list --role app_user
pydbadmin -c local ownership list --owner app_owner
```

The `role` and `access` groups also contain mutation commands.

Examples include:

```text
role create
role alter
role drop
role membership-add
role membership-remove
access grant
access revoke
```

Mutation safety is covered later in
[Dry-run, guardrails and confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md).

## Runtime inspection

Runtime-oriented groups are:

```text
session
query
transaction
wait
lock
blocking
```

Examples:

```bash
pydbadmin -c prod session list
pydbadmin -c prod query list
pydbadmin -c prod transaction list
pydbadmin -c prod wait list
pydbadmin -c prod lock list
pydbadmin -c prod blocking list
```

Filters vary by command and include database, user, state, wait type and self-inclusion controls.

Use command help for the exact supported options:

```bash
pydbadmin session list --help
pydbadmin lock list --help
```

## Runtime mutations

Two runtime commands intentionally change server state:

```text
query cancel <pid>
session terminate <pid>
```

Examples:

```bash
pydbadmin -c prod --dry-run query cancel 12345
pydbadmin -c prod --dry-run session terminate 12345
```

These are guarded and audited mutation paths.

## Backup and restore

The `backup` group provides:

```text
backup create
backup validate
backup restore
```

Examples:

```bash
pydbadmin -c prod backup create app
pydbadmin backup validate ./app.dump
pydbadmin -c staging --dry-run backup restore ./app.dump --database app_restore
```

Backup/restore behavior, native tools and safety constraints are covered in guides 18 and 19.

## PostgreSQL maintenance

PostgreSQL-specific maintenance lives under:

```text
postgres
```

Implemented operations include:

```text
postgres vacuum
postgres analyze
postgres reindex
postgres progress vacuum
postgres progress reindex
```

Examples:

```bash
pydbadmin -c prod --dry-run postgres vacuum --table public.orders
pydbadmin -c prod --dry-run postgres reindex --index public.orders_pkey
pydbadmin -c prod postgres progress vacuum
```

The first three can mutate PostgreSQL state and therefore participate in the guardrail model.

## Capability discovery

Use:

```text
capability list
capability get <name>
```

Examples:

```bash
pydbadmin capability list
pydbadmin capability get runtime.cancel-query
```

Capability names are part of the frozen 1.0 machine contract.

Use capability discovery when automation needs to determine whether an operation is supported
instead of inferring support from a server version string alone.

## Health

Health is exposed through:

```text
health check
```

Example:

```bash
pydbadmin -c prod health check
```

Machine output:

```bash
pydbadmin -c prod --output json health check
```

The health command has its own status-to-exit semantics, covered below.

## Commands that require a connection profile

Most server/database operations require:

```text
--connection <profile>
```

If a command requires a profile and none is selected, the CLI emits:

```text
Error: Select a profile with --connection.
```

and exits with code:

```text
2
```

Example correction:

```bash
pydbadmin -c local server info
```

A missing execution context is therefore treated as a CLI/configuration usage failure, not a
database connection failure.

## Configuration selection

Select a configuration file explicitly with:

```bash
pydbadmin \
  --config /absolute/path/config.toml \
  -c prod \
  connection test
```

If `--config` is omitted, the standard platform-specific PyDBAdminKit config path is used.

For production scripts and CI/CD, an explicit config path is usually easier to reason about.

## Output formats

The root output option accepts:

```text
table
json
yaml
```

Human-oriented example:

```bash
pydbadmin -c local --output table database list
```

Machine-oriented examples:

```bash
pydbadmin -c local --output json database list
pydbadmin -c local --output yaml database list
```

JSON is the primary frozen machine interface.

The next guide covers output contracts in detail.

## Inspection versus mutation

A useful mental model is:

```text
inspection
    → read state
    → no approval flow

mutation
    → build operation plan
    → evaluate safety policy
    → confirmation / dry-run rules
    → execute or block
    → audit lifecycle
```

Examples of inspection commands:

```text
server info
database list
role list
session list
blocking list
health check
```

Examples of mutation commands:

```text
role create
access grant
query cancel
session terminate
backup restore
postgres vacuum
postgres reindex
```

Do not assume every command under a group has the same safety category.

## Dry-run

For supported mutation commands:

```bash
pydbadmin -c staging --dry-run <mutation>
```

returns/plans the mutation without applying the database change.

Examples:

```bash
pydbadmin -c staging --dry-run role create reporting_user

pydbadmin -c staging --dry-run   access grant   --role reporting_user   --object public.orders   --access select
```

Dry-run is a root option, so place it before the group in documentation and runbooks.

Dry-run does not make an incorrectly selected profile safe. Verify the profile first.

## `--yes`

The root option:

```text
--yes, -y
```

approves simple/explicit confirmations where allowed.

Example shape:

```bash
pydbadmin -c staging --yes <mutation>
```

However, critical typed-target confirmation is intentionally stronger.

`--yes` does **not** bypass a required exact target confirmation.

## Typed target confirmation

Critical operations may expose a command-local option:

```text
--confirm-target <target>
```

Examples occur in security mutations, runtime mutations, restore and maintenance commands.

The CLI safety layer handles typed-target confirmation before ordinary `--yes` approval.

Therefore:

```text
--yes
```

cannot substitute for an exact target value when the operation requires one.

This is deliberate safety behavior.

## Non-interactive mode

Use:

```text
--non-interactive
```

when the process must never prompt.

Example:

```bash
pydbadmin   -c staging   --non-interactive   --dry-run   role create reporting_user
```

If an operation requires approval that has not been supplied explicitly, non-interactive mode does
not invent consent. The mutation remains unapproved or is blocked according to the safety model.

For typed-target operations, automation must provide the required `--confirm-target` value
explicitly where execution is intended.

## Exit codes

PyDBAdminKit freezes process exit codes as a machine interface.

| Code | Meaning |
| ---: | --- |
| 0 | success / non-failing health result |
| 1 | general operational failure or failing health result |
| 2 | configuration / CLI usage failure |
| 3 | database connection failure |
| 4 | authentication / authorization failure |
| 5 | requested resource not found |
| 6 | requested capability unavailable |
| 7 | safety / guardrail policy failure |
| 8 | external tool, backup, restore or maintenance failure |
| 9 | connection or operation timeout |

Shell example:

```bash
pydbadmin -c prod connection test
status=$?

echo "$status"
```

Automation should branch on exit codes and machine error identifiers rather than parse
human-readable messages.

## Error codes versus exit codes

These are different interfaces.

```text
ErrorCode
    → precise machine classification of what happened

process exit code
    → compact shell/CI outcome category
```

For example, several specific backup/restore/tool errors may map to exit code `8`.

The frozen error identifiers are documented in:

```text
docs/contracts/ERROR_CODE_CONTRACT.md
```

The frozen process mapping is documented in:

```text
docs/contracts/EXIT_CODE_CONTRACT.md
```

## Health exit semantics

`health check` deliberately differs from a simple success/failure command.

Default:

```text
OK       → 0
WARNING  → 0
CRITICAL → 1
UNKNOWN  → 0
```

With:

```text
--fail-on-warning
```

a warning becomes:

```text
WARNING → 1
```

Example:

```bash
pydbadmin -c prod health check --fail-on-warning
```

This makes the command usable as a CI/monitoring gate when warnings should fail the step.

## Human versus machine usage

Interactive operator:

```bash
pydbadmin -c prod server info
```

Automation:

```bash
pydbadmin   --config /etc/pydbadminkit/config.toml   -c prod   --output json   --non-interactive   health check
```

For scripts, prefer:

- explicit `--config`;
- explicit `--connection`;
- `--output json`;
- `--non-interactive`;
- exit-code checks;
- no parsing of decorative human output.

## Worked inspection session

Test the connection:

```bash
pydbadmin   --config ./config.toml   -c local   connection test
```

Inspect the server:

```bash
pydbadmin   --config ./config.toml   -c local   server info
```

Explore databases:

```bash
pydbadmin   --config ./config.toml   -c local   database list
```

Explore public tables:

```bash
pydbadmin   --config ./config.toml   -c local   table list   --schema public
```

Inspect sessions:

```bash
pydbadmin   --config ./config.toml   -c local   session list
```

Run health checks:

```bash
pydbadmin   --config ./config.toml   -c local   health check
```

Switch to JSON:

```bash
pydbadmin   --config ./config.toml   -c local   --output json   health check
```

## Worked mutation-preflight session

Suppose you intend to create a role in staging.

First inspect the target:

```bash
pydbadmin -c staging server info
```

Inspect existing roles:

```bash
pydbadmin -c staging role list
```

Plan the mutation:

```bash
pydbadmin   -c staging   --dry-run   role create reporting_user   --login
```

Only after reviewing the plan should you consider execution using the confirmation mechanism
required by that specific operation.

The detailed safety workflow is covered in guide 24.

## Troubleshooting

### `pydbadmin` command not found

Verify installation and environment activation.

Try:

```bash
python -m pydbadminkit --help
```

if you are working from a source checkout or environment where the console entry point is not on
`PATH`.

### Missing connection profile

Symptom:

```text
Error: Select a profile with --connection.
```

Fix:

```bash
pydbadmin -c local ...
```

### Wrong configuration file

Use an explicit path:

```bash
pydbadmin --config /absolute/path/config.toml -c local connection test
```

### Unknown command or option

Do not infer syntax from older planning documents.

Use:

```bash
pydbadmin --help
pydbadmin <group> --help
pydbadmin <group> <command> --help
```

### Automation unexpectedly prompts

Add:

```text
--non-interactive
```

and supply all required execution intent explicitly.

Do not use `--yes` as a blanket replacement for typed-target confirmation.

### Command returns non-zero

Inspect the numeric code first, then consume the machine error contract where available.

Do not branch on English error-message text.

## Production considerations

For production CLI use:

1. make `--config` explicit;
2. make `--connection` explicit;
3. inspect the target before mutations;
4. prefer read-only profiles for diagnosis;
5. use `--dry-run` before supported mutations;
6. do not assume `--yes` bypasses critical confirmation;
7. use `--non-interactive` in automation;
8. use JSON rather than human table output in scripts;
9. branch on exit codes and stable error identifiers;
10. keep credentials outside command arguments;
11. preserve audit and guardrail behavior rather than wrapping commands in ways that bypass it.

## Best practices

Prefer:

```text
pydbadmin --config ... -c ... <inspection>
pydbadmin --config ... -c ... --dry-run <mutation>
pydbadmin --config ... -c ... --output json --non-interactive <automation>
```

Avoid:

```text
implicit production target selection
parsing human table output in CI
assuming every group is read-only
using --yes as a universal safety bypass
copying commands from pre-1.0 planning documents without checking --help
ignoring exit codes
embedding passwords in CLI arguments
```

## Key takeaways

- `pydbadmin` is a Typer-based hierarchical CLI with a shared root execution context.
- PyDBAdminKit 1.0 registers 21 command groups.
- `--connection`, `--config`, `--output`, `--dry-run`, `--yes` and
  `--non-interactive` are root options.
- Most database operations require a selected connection profile.
- Table output is human-oriented; JSON/YAML are machine-oriented.
- Inspection and mutation commands have different execution semantics.
- `--dry-run` plans supported mutations without applying them.
- `--yes` does not bypass required typed-target confirmation.
- `--non-interactive` prevents prompting rather than silently approving operations.
- Exit codes are a frozen machine contract and are distinct from `ErrorCode`.
- Use `--help` at root, group and command level to discover exact 1.0 syntax.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md)
- [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md)
- [Table, JSON and YAML Output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md)
- [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Automation and Machine Interface](27_AUTOMATION_AND_MACHINE_INTERFACE.md)
- [Shell Scripting and CI/CD](28_SHELL_SCRIPTING_AND_CI_CD.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Error-code contract](../contracts/ERROR_CODE_CONTRACT.md)
- [Exit-code contract](../contracts/EXIT_CODE_CONTRACT.md)

## Next

Continue with [Table, JSON and YAML Output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md).
