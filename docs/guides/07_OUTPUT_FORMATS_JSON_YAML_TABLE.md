# PyDBAdminKit 1.0 — Table, JSON and YAML Output

## Objective

Choose the right output format for operators, scripts and CI/CD, understand the 1.0 machine
serialization contract, and avoid treating human-readable output as a stable machine interface.

PyDBAdminKit 1.0 supports three CLI output formats:

```text
table
json
yaml
```

The default is:

```text
table
```

JSON is the **primary frozen machine contract** for the 1.0 line.

## Prerequisites

Before continuing, you should understand the root CLI options described in
[CLI Fundamentals](06_CLI_FUNDAMENTALS.md).

The output option is selected at the root:

```text
--output, -o
```

Examples:

```bash
pydbadmin -c local --output table database list
pydbadmin -c local --output json database list
pydbadmin -c local --output yaml database list
```

## Output architecture

The CLI separates the underlying public value from its presentation.

Conceptually:

```text
domain/application value
        ↓
CLI command
        ↓
emit_output(...)
        ├── table → dedicated human renderer
        ├── json  → render_json(...)
        └── yaml  → render_yaml(...)
```

The CLI emits exactly one representation to stdout for a successful command.

This is important because machine modes do not prepend human labels before JSON/YAML.

## OutputFormat contract

The stable output-format enum is:

```text
table
json
yaml
```

The default CLI context uses:

```text
table
```

Use:

```bash
pydbadmin -o json ...
```

or:

```bash
pydbadmin --output yaml ...
```

to opt into machine-readable output.

## Table output

Table mode is intended primarily for human operators.

Example:

```bash
pydbadmin -c local database list
```

Representative output shape:

```text
NAME    OWNER    ENCODING    CONNECTIONS    SIZE_BYTES
postgres postgres UTF8        yes            8192000
```

Human renderers may use:

- tab-separated rows;
- label/value lines;
- section headings;
- `yes` / `no`;
- `-` for missing values;
- shortened query previews;
- explanatory headings such as `WARNINGS`, `COLUMNS`, `CONSTRAINTS`.

These choices are optimized for readability.

## Do not parse table output in automation

Avoid:

```bash
pydbadmin -c prod database list | awk ...
```

or code that assumes exact spacing or human labels.

Human rendering is not the primary frozen machine contract.

Prefer:

```bash
pydbadmin -c prod --output json database list
```

and parse the JSON structure.

## JSON output

JSON is the primary stable machine format for PyDBAdminKit 1.0.

Example:

```bash
pydbadmin -c local --output json connection test
```

Representative shape:

```json
{
  "engine": "postgresql",
  "version": {
    "major": 18,
    "minor": 0,
    "patch": 0
  },
  "current_database": "analytics",
  "current_user": "app",
  "latency_ms": 12.5
}
```

The exact values depend on the connected server.

## YAML output

YAML uses the same machine-value conversion boundary as JSON.

Example:

```bash
pydbadmin -c local --output yaml connection test
```

Representative shape:

```yaml
engine: postgresql
version:
  major: 18
  minor: 0
  patch: 0
current_database: analytics
current_user: app
latency_ms: 12.5
```

JSON and YAML therefore describe the same public model with different textual encodings.

For long-lived automation contracts, prefer JSON because it is the primary frozen 1.0 machine
contract.

## Stable machine conversion rules

The shared serializer converts supported public values according to these rules:

```text
None                 → null
bool                 → boolean
int                  → integer
float                → number
str                  → string
datetime/date        → ISO-8601 string
Enum/StrEnum         → enum wire value
RiskLevel            → lowercase label
SecretValue          → "<redacted>"
dataclass            → object in declaration order
tuple/list           → array
Mapping[str, ...]    → object
```

Unsupported values are rejected rather than silently converted with `str()`.

Mappings with non-string keys are also rejected.

This fail-explicitly behavior avoids accidental creation of unstable machine payloads.

## Primitive values

Python primitives remain equivalent machine primitives.

Conceptually:

```text
True       → true
42         → 42
3.14       → 3.14
"postgres" → "postgres"
None       → null
```

No human formatting is added in JSON/YAML modes.

## Enums

Enums serialize using their wire value.

Example conceptually:

```text
DatabaseEngine.POSTGRESQL
    ↓
"postgresql"
```

This means automation should consume documented enum wire values rather than Python enum names.

## Risk levels

`RiskLevel` has a deliberate special machine representation:

```text
lowercase label
```

For example:

```json
{
  "risk": "low"
}
```

Consumers should treat these labels as part of the machine contract.

## Dates and timestamps

`date` and `datetime` values become ISO-8601 strings.

Conceptually:

```text
datetime(...)
    ↓
"2026-09-26T09:30:00+02:00"
```

Do not expect epoch timestamps unless a specific public field explicitly defines one.

## Dataclasses become objects

Public immutable domain/application dataclasses serialize structurally.

Field names become object keys.

Example database list item:

```json
{
  "name": "analytics",
  "owner": "app",
  "encoding": "UTF8",
  "collation": null,
  "allow_connections": true,
  "connection_limit": -1,
  "size_bytes": 1024
}
```

The serializer does not maintain a separate JSON-only DTO hierarchy.

Machine output is derived from the public models themselves.

## Lists and tuples become arrays

A list-style CLI command emits an array.

Example:

```bash
pydbadmin -c local --output json database list
```

Shape:

```json
[
  {
    "name": "postgres",
    "owner": "postgres",
    "encoding": "UTF8"
  },
  {
    "name": "app",
    "owner": "app_owner",
    "encoding": "UTF8"
  }
]
```

The real items include the complete public model fields.

## Empty collections

An empty list command returns:

```json
[]
```

not:

```json
null
```

and not an object wrapper invented by the CLI.

This distinction is part of the frozen machine behavior.

## Nullability

Nullable dataclass fields are serialized explicitly as:

```json
null
```

They are not omitted simply because their value is `None`.

Example:

```json
{
  "collation": null
}
```

For PyDBAdminKit 1.0:

```text
null ≠ missing key
```

Changing from explicit nulls to omitted fields would be a machine-contract change.

## Field ordering

JSON fields preserve dataclass declaration order.

`render_json()` uses:

```text
2-space indentation
no key sorting
declaration order preserved
unescaped Unicode
```

Consumers should still parse by key rather than rely on position.

Deterministic ordering exists primarily for:

- reproducible output;
- snapshot tests;
- diffs;
- operational artifacts;
- easier human review of machine payloads.

## Unicode

JSON output preserves Unicode rather than forcing ASCII escapes.

For example, a legitimate Unicode database/object value may remain readable directly in the JSON
payload.

This behavior is part of the qualified machine serialization path.

## Secret redaction

If a `SecretValue` reaches the machine serializer, it becomes:

```text
<redacted>
```

Example conceptual payload:

```json
{
  "password": "<redacted>"
}
```

This is defense in depth.

The preferred design remains to avoid placing resolved secrets into public output DTOs at all.

See [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md).

## Query text is operational data

Runtime inspection models may intentionally contain query text.

For example:

```bash
pydbadmin -c prod --output json query list
```

may expose query text because the command is explicitly an administrative inspection surface.

Do not assume every machine payload is safe to publish merely because credentials are redacted.

Operational SQL text may itself contain sensitive business data or literals.

Treat runtime output according to your operational data-handling policy.

## CLI machine-output purity

The CLI routes output so that JSON/YAML modes receive only the machine representation on stdout.

Conceptually:

```text
if output == json:
    emit JSON
elif output == yaml:
    emit YAML
else:
    emit human rendering
```

It does not intentionally produce:

```text
Database list:
[ ...json... ]
```

in JSON mode.

This makes stdout parseable by automation.

## Representative payload families

The frozen inventory maps CLI surfaces to public payload families.

| CLI surface | Machine payload |
| --- | --- |
| `connection test` | one `ConnectionTestResult` object |
| `server info` | one `ServerInfo` object |
| catalog `list` commands | arrays of read models |
| catalog `describe` commands | one description/read model |
| `role list` | array of `RoleInfo` |
| `role describe` | one `RoleDescription` |
| `access list` | array of `DirectAccess` |
| `effective-access list` | array of `EffectiveAccess` |
| `ownership list` | array of `OwnershipInfo` |
| runtime `list` commands | arrays of runtime models |
| `capability list` | array of `CapabilityStatus` |
| `capability get` | one `CapabilityStatus` |
| `health check` | one `HealthReport` |
| `backup create` | `Backup` or operation plan in dry-run |
| `backup validate` | one `BackupValidation` |
| `backup restore` | `RestoreOperation` or operation plan in dry-run |
| guarded mutations | operation result or operation plan |
| maintenance progress | arrays of `MaintenanceProgress` |

The detailed fields of each model are documented by the relevant domain/API reference and
contract tests.

## Dry-run output

A mutation can return a different payload family in dry-run mode.

Example:

```bash
pydbadmin   -c staging   --dry-run   --output json   role create reporting_user
```

The machine payload represents the **operation plan**, not the executed mutation result.

Conceptually:

```text
dry-run
    → OperationPlan

execution
    → OperationResult or operation-specific result
```

Automation must understand this distinction.

## Operation result shape

A generic operation result has a representative frozen shape like:

```json
{
  "operation": "example",
  "status": "succeeded",
  "changed": true,
  "message": "completed",
  "metadata": {
    "risk": "low"
  }
}
```

Specific operations may return more specialized public result models.

## Health-report shape

The stable health-report top-level machine shape includes:

```text
overall_status
checks
captured_at
```

Each check includes:

```text
name
status
message
details
captured_at
evidence
```

Health has separate exit semantics in addition to the payload.

Do not infer process success only from the textual status field; also respect the documented exit
contract.

## JSON versus YAML for automation

Both formats are machine-readable.

Use JSON when:

- writing shell/CI integrations;
- using strict parsers;
- persisting contract fixtures;
- building long-lived consumers;
- validating against the primary 1.0 machine contract.

Use YAML when:

- human readability matters;
- configuration-style inspection is useful;
- the consuming tool already expects YAML.

For compatibility-sensitive automation, JSON is the safer default because it is explicitly the
primary frozen contract.

## Shell examples

JSON database list:

```bash
pydbadmin   --config ./config.toml   -c prod   --output json   database list
```

YAML health check:

```bash
pydbadmin   --config ./config.toml   -c prod   --output yaml   health check
```

JSON runtime inspection:

```bash
pydbadmin   --config ./config.toml   -c prod   --output json   session list
```

## Python parsing example

A shell command can write machine output to a file:

```bash
pydbadmin -c prod --output json database list > databases.json
```

Then ordinary Python can consume it:

```python
import json
from pathlib import Path

databases = json.loads(Path("databases.json").read_text())

for database in databases:
    print(database["name"])
```

The consumer should parse fields, not scrape human labels.

## jq example

When `jq` is available:

```bash
pydbadmin -c prod --output json database list |
  jq -r '.[].name'
```

This is preferable to parsing table columns.

## Redirecting output

Machine stdout can be redirected:

```bash
pydbadmin -c prod --output json health check > health.json
```

Remember that successful machine output and process exit status are separate concerns.

A robust script should capture both.

Example shape:

```bash
if pydbadmin -c prod --output json health check > health.json; then
    echo "command completed"
else
    status=$?
    echo "command failed with exit code $status" >&2
fi
```

## Errors and machine output

Stable error identifiers and process exit codes are separate contracts from successful output
serialization.

Do not assume every failure is represented as the same successful DTO shape with an `error`
field.

Use:

- process exit code;
- stable error semantics;
- stderr/error handling documented in guide 26.

This guide focuses on successful output serialization.

## Unsupported machine values

The serializer intentionally raises rather than silently stringifies unsupported Python objects.

This protects the machine interface from accidental payload drift.

Likewise, this mapping is rejected:

```python
{1: "value"}
```

because machine-output mappings require string keys.

Extension authors should convert custom result types into supported public machine values rather
than depend on arbitrary `str(object)` behavior.

## Human rendering conventions

Human renderers are deliberately presentation-oriented.

Examples include:

```text
yes / no
-
NAME	OWNER	...
COLUMNS
CONSTRAINTS
WARNINGS
METADATA
```

These conventions may be useful in terminals but should not be treated as JSON field names or
machine contracts.

The underlying public model is the source for machine serialization.

## Production automation pattern

A production automation invocation should usually look like:

```bash
pydbadmin   --config /etc/pydbadminkit/config.toml   -c prod   --output json   --non-interactive   health check
```

For mutation preflight:

```bash
pydbadmin   --config /etc/pydbadminkit/config.toml   -c prod   --output json   --non-interactive   --dry-run   postgres vacuum   --table public.orders
```

The resulting JSON can be archived, inspected or consumed by another process.

## Compatibility expectations

For the 1.0 machine contract, the following require compatibility review:

- removing a field;
- renaming a field;
- changing a field type;
- changing an enum wire value;
- changing `null` into field omission;
- changing omission into `null`;
- changing an array payload into an object;
- changing an object payload into an array;
- changing ISO-8601 date/time encoding;
- changing risk labels;
- changing secret redaction behavior;
- adding credential material;
- changing deterministic field order;
- even adding fields where strict consumers may reject unknown keys.

Machine consumers should nevertheless be designed defensively where possible.

## Troubleshooting

### JSON contains human labels before the object

With a supported 1.0 command, this should not happen in normal machine mode.

Verify:

```bash
pydbadmin --version
```

and make sure the root option is:

```text
--output json
```

### Parser sees `null`

This may be expected.

Nullable dataclass fields are emitted explicitly as `null` rather than omitted.

### Expected list but received object

Check the CLI surface.

Typical rule:

```text
list      → array
describe  → object
get       → object
```

Mutation dry-run may return an `OperationPlan` object instead of the executed result model.

### Secret appears as `<redacted>`

This is expected and intentional.

Do not attempt to reconstruct or scrape the secret from machine output.

### YAML consumer disagrees about formatting

Parse YAML structurally rather than comparing raw whitespace.

The semantic model is shared with JSON, but JSON is the primary frozen contract.

### Automation depends on table headers

Migrate it to JSON.

Human table headers are for operator readability, not the primary machine interface.

## Best practices

Prefer:

```text
table for humans
json for automation
yaml for machine-readable human-friendly inspection
parse JSON by key
check process exit status separately
treat null as distinct from missing
expect list commands to return arrays
preserve secret redaction
archive machine output when operational evidence is useful
```

Avoid:

```text
scraping table spacing
parsing human labels
assuming missing fields when value is null
assuming dry-run and execution return identical payload types
printing SecretValue.reveal()
treating runtime query text as non-sensitive
depending on arbitrary object stringification
ignoring exit codes
```

## Key takeaways

- PyDBAdminKit 1.0 supports `table`, `json` and `yaml`.
- Table is the default and is intended for human operators.
- JSON is the primary frozen machine contract.
- YAML uses the same machine-value conversion model as JSON.
- Machine modes emit one clean representation to stdout without human rendering prefixes.
- Dataclasses become objects; tuples/lists become arrays.
- Empty list results are `[]`, not `null`.
- Nullable dataclass fields remain present as explicit `null`.
- Dates/timestamps use ISO-8601.
- Enums use stable wire values.
- `RiskLevel` uses lowercase labels.
- `SecretValue` becomes `"<redacted>"`.
- Unsupported objects and non-string mapping keys fail explicitly.
- Dry-run mutation output can be an operation plan rather than an execution result.
- Automation should combine machine payload parsing with stable exit-code handling.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [CLI Fundamentals](06_CLI_FUNDAMENTALS.md)
- [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md)
- [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Health Checks](22_HEALTH_CHECKS.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Automation and Machine Interface](27_AUTOMATION_AND_MACHINE_INTERFACE.md)
- [Shell Scripting and CI/CD](28_SHELL_SCRIPTING_AND_CI_CD.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [JSON contract inventory](../contracts/JSON_CONTRACT_INVENTORY.md)
- [Machine-interface qualification](../releases/T21_006_MACHINE_INTERFACE_QUALIFICATION.md)

## Next

Continue with [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md).
