# PyDBAdminKit 1.0 — Database Exploration

## Objective

Explore PostgreSQL databases visible through the selected PyDBAdminKit connection profile using the
stable CLI and Python API.

This guide focuses specifically on the database-level catalog surface:

```text
database list
database describe <name>
```

The next guide covers schemas, tables, views and indexes in detail.

## Prerequisites

Before continuing, you should understand:

- connection profiles;
- credentials and secret resolution;
- CLI root options;
- table/JSON/YAML output;
- the public Python API.

A working profile should already be available:

```bash
pydbadmin -c local connection test
```

## What database exploration means in PyDBAdminKit

PyDBAdminKit database exploration is read-only catalog inspection.

The implemented 1.0 flow is:

```text
selected profile
    ↓
CatalogService
    ↓
PostgreSQL catalog adapter
    ↓
pg_database metadata
    ↓
DatabaseInfo
```

No mutation is performed by the database explorer.

## Scope

The database list command is documented as listing:

```text
visible non-template databases
```

The PostgreSQL query excludes template databases with:

```text
NOT datistemplate
```

The result is ordered by database name.

The visibility and metadata available to the command are still governed by the connected
PostgreSQL principal and PostgreSQL itself.

Do not interpret the output as an abstract guarantee that every database existing anywhere in the
server environment is visible to the selected identity.

## CLI commands

The stable 1.0 database commands are:

```text
database list
database describe <name>
```

Both use the selected connection profile.

## List databases

Run:

```bash
pydbadmin -c local database list
```

With an explicit config file:

```bash
pydbadmin \
  --config ./config.toml \
  -c local \
  database list
```

The command returns visible non-template databases.

## Human output

The table renderer uses the columns:

```text
NAME
OWNER
ENCODING
CONNECTIONS
SIZE_BYTES
```

Representative output:

```text
NAME       OWNER      ENCODING    CONNECTIONS    SIZE_BYTES
analytics  app_owner  UTF8        yes            10485760
postgres   postgres   UTF8        yes            8192000
```

Human output intentionally shows a compact subset of the underlying `DatabaseInfo` model.

## Describe one database

Run:

```bash
pydbadmin -c local database describe analytics
```

The argument must be the exact database name.

Representative human output:

```text
Name: analytics
Owner: app_owner
Encoding: UTF8
Collation: en_US.UTF-8
Allow connections: yes
Connection limit: -1
Size bytes: 10485760
```

The exact values depend on the target PostgreSQL server.

## DatabaseInfo model

The public database model is:

```text
DatabaseInfo
```

with the fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | `str` | database name |
| `owner` | `str | None` | database owner |
| `encoding` | `str | None` | encoding |
| `collation` | `str | None` | collation |
| `allow_connections` | `bool | None` | whether PostgreSQL allows connections |
| `connection_limit` | `int | None` | configured connection limit |
| `size_bytes` | `int | None` | reported database size in bytes |

The model requires a non-blank database name.

If `size_bytes` is present, it must be non-negative.

## PostgreSQL metadata source

The implementation maps database information from PostgreSQL catalog metadata.

The selected fields correspond to:

```text
datname
database owner
encoding
collation
datallowconn
datconnlimit
pg_database_size(...)
```

This is intentionally exposed through the stable `DatabaseInfo` abstraction rather than making
users depend on PostgreSQL query internals.

## JSON output

Use:

```bash
pydbadmin -c local --output json database list
```

Representative shape:

```json
[
  {
    "name": "analytics",
    "owner": "app_owner",
    "encoding": "UTF8",
    "collation": "en_US.UTF-8",
    "allow_connections": true,
    "connection_limit": -1,
    "size_bytes": 10485760
  }
]
```

A list command returns an array.

If no visible non-template database is returned, the machine value is:

```json
[]
```

not `null`.

## JSON describe

Run:

```bash
pydbadmin \
  -c local \
  --output json \
  database describe analytics
```

Representative shape:

```json
{
  "name": "analytics",
  "owner": "app_owner",
  "encoding": "UTF8",
  "collation": "en_US.UTF-8",
  "allow_connections": true,
  "connection_limit": -1,
  "size_bytes": 10485760
}
```

The describe command returns one object rather than an array.

## YAML output

Run:

```bash
pydbadmin -c local --output yaml database describe analytics
```

Representative shape:

```yaml
name: analytics
owner: app_owner
encoding: UTF8
collation: en_US.UTF-8
allow_connections: true
connection_limit: -1
size_bytes: 10485760
```

YAML uses the same underlying public model as JSON.

## Python API

Start with the public bootstrap builder:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service(
    "local",
    Path("config.toml"),
)
```

The returned service is a public:

```text
CatalogService
```

## List databases in Python

```python
databases = catalog.list_databases()

for database in databases:
    print(database.name)
```

The return type is:

```text
tuple[DatabaseInfo, ...]
```

You therefore work with typed objects directly.

## Inspect database metadata

```python
for database in catalog.list_databases():
    print(
        database.name,
        database.owner,
        database.encoding,
        database.allow_connections,
        database.connection_limit,
        database.size_bytes,
    )
```

No JSON parsing is required when using the Python API.

## Get one database in Python

Use:

```python
database = catalog.get_database("analytics")

print(database.name)
print(database.owner)
print(database.encoding)
print(database.collation)
print(database.allow_connections)
print(database.connection_limit)
print(database.size_bytes)
```

The method returns one:

```text
DatabaseInfo
```

## CLI versus Python method names

The mapping is:

```text
CLI                             Python API

database list                   CatalogService.list_databases()
database describe <name>        CatalogService.get_database(name)
```

The public CLI intentionally uses the operator-friendly word `describe`.

The Python service uses `get_database`.

## Exact-name lookup

`database describe` and `CatalogService.get_database()` use an exact database name.

Example:

```bash
pydbadmin -c prod database describe analytics
```

The implementation parameterizes the database name rather than composing it into SQL text.

## Database not found or not visible

If the requested database cannot be returned by the catalog lookup, PyDBAdminKit raises:

```text
ResourceNotFoundError
```

The semantic message is:

```text
Database '<name>' was not found or is not visible.
```

The wording deliberately does not claim that the database definitively does not exist.

That distinction matters because the active PostgreSQL identity may affect what can be observed.

## CLI exit code for missing database

`ResourceNotFoundError` maps to process exit code:

```text
5
```

Automation should branch on the stable exit/error contract rather than parse the human message.

## Python error handling

Example:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.errors import ResourceNotFoundError

catalog = build_catalog_service(
    "prod",
    Path("config.toml"),
)

try:
    database = catalog.get_database("analytics")
except ResourceNotFoundError:
    print("database was not found or is not visible")
```

For broader handling:

```python
from pydbadminkit.errors import PyDBAdminError

try:
    databases = catalog.list_databases()
except PyDBAdminError as exc:
    print(exc.code.value)
    raise
```

## Size semantics

The `size_bytes` field is obtained through PostgreSQL's database-size metadata path.

It is expressed in bytes.

Example:

```python
database = catalog.get_database("analytics")

if database.size_bytes is not None:
    size_mib = database.size_bytes / 1024 / 1024
    print(f"{size_mib:.2f} MiB")
```

PyDBAdminKit preserves the raw byte value in the public model instead of imposing a display unit.

## Connection availability versus database visibility

The field:

```text
allow_connections
```

reflects PostgreSQL's catalog property for whether connections are allowed to that database.

It does not itself prove that the current principal can successfully authenticate to that
database.

Similarly:

```text
connection_limit
```

is catalog metadata and should not be interpreted as the current number of active sessions.

Runtime connection usage is covered by monitoring/runtime guides.

## Connection limit

PostgreSQL may expose values such as:

```text
-1
```

for database connection limits.

PyDBAdminKit preserves the reported integer rather than converting it into a custom semantic label.

Consumers should interpret the value according to PostgreSQL semantics when needed.

## Collation

The `collation` field is nullable in the public model.

In JSON/YAML, a missing Python value becomes:

```json
null
```

In human output, missing optional values are displayed as:

```text
-
```

This illustrates the difference between human presentation and machine representation.

## Read-only nature

Database exploration is inspection-only.

The following commands:

```text
database list
database describe
```

do not use the mutation planning or confirmation pipeline.

Therefore:

```text
--dry-run
```

has no meaningful mutation-planning role for these commands.

Use the selected connection profile's least-privilege/read-only identity where appropriate.

## Exploration workflow

A practical database-level workflow is:

```text
connection test
    ↓
server info
    ↓
database list
    ↓
database describe <name>
    ↓
schema list
    ↓
table/view/index exploration
```

Example:

```bash
pydbadmin -c prod connection test

pydbadmin -c prod server info

pydbadmin -c prod database list

pydbadmin -c prod database describe app
```

Then continue with the next guide for object-level exploration.

## Worked CLI session

List databases:

```bash
pydbadmin \
  --config ./config.toml \
  -c local \
  database list
```

Describe the current application database:

```bash
pydbadmin \
  --config ./config.toml \
  -c local \
  database describe app
```

Switch to JSON:

```bash
pydbadmin \
  --config ./config.toml \
  -c local \
  --output json \
  database describe app
```

## Worked Python session

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.errors import ResourceNotFoundError

CONFIG = Path("config.toml")
PROFILE = "local"

catalog = build_catalog_service(PROFILE, CONFIG)

databases = catalog.list_databases()

for item in databases:
    print(
        item.name,
        item.owner,
        item.encoding,
        item.size_bytes,
    )

try:
    database = catalog.get_database("app")
except ResourceNotFoundError:
    print("app is not visible through this profile")
else:
    print("database:", database.name)
    print("owner:", database.owner)
    print("connections allowed:", database.allow_connections)
```

## Automation pattern

Use JSON:

```bash
pydbadmin \
  --config /etc/pydbadminkit/config.toml \
  -c prod_ro \
  --output json \
  --non-interactive \
  database list
```

A script can then inspect the array structurally.

Example with `jq`:

```bash
pydbadmin -c prod_ro --output json database list |
  jq -r '.[].name'
```

Do not scrape the human table.

## Visibility and permissions

A key operational principle is:

```text
catalog output is observed through the selected PostgreSQL identity
```

Different profiles may therefore represent different operational viewpoints.

For example:

```text
prod_ro
prod_admin
```

may connect with different PostgreSQL roles and may not be equivalent from a visibility or
authorization perspective.

Use the profile that matches the operational purpose.

## Troubleshooting

### No databases are returned

Check:

- the selected profile;
- connectivity;
- PostgreSQL permissions/visibility;
- whether the environment contains only template databases relevant to the query;
- whether you are connecting to the intended server.

First verify:

```bash
pydbadmin -c local server info
```

### Database describe returns not found

Confirm the exact name:

```bash
pydbadmin -c local database list
```

Then use one of the returned names:

```bash
pydbadmin -c local database describe <exact-name>
```

Remember that the error means:

```text
not found or not visible
```

not necessarily globally absent.

### Size is null or unavailable

The public model permits `size_bytes = None`.

Do not force an integer conversion without checking for `None`.

### Table output differs from JSON

Expected.

Human output is condensed and may display:

```text
-
yes
no
```

while JSON preserves:

```text
null
true
false
```

### You need schemas/tables/views/indexes

Continue with:

```text
10_SCHEMA_TABLE_VIEW_AND_INDEX_EXPLORATION.md
```

Database exploration intentionally stays at the database summary level.

## Production considerations

For production exploration:

1. prefer a read-only profile;
2. make the config path and profile explicit;
3. verify `server info` before interpreting results;
4. use JSON in automation;
5. treat database size as point-in-time catalog information;
6. do not infer access rights from `allow_connections` alone;
7. do not infer active connection count from `connection_limit`;
8. treat “not found” as “not found or not visible”;
9. keep database inspection separate from mutation workflows;
10. use security/runtime guides when the question concerns authorization or live sessions.

## Best practices

Prefer:

```text
connection test
server info
database list
database describe
typed DatabaseInfo in Python
JSON in scripts
read-only profiles
exact database names
```

Avoid:

```text
assuming template databases are included
scraping table output
treating connection_limit as active sessions
treating allow_connections as proof of authentication rights
assuming missing means globally nonexistent
importing PostgreSQL catalog adapters directly
using administrative credentials for simple exploration
```

## Key takeaways

- PyDBAdminKit 1.0 exposes `database list` and `database describe <name>`.
- The list command returns non-template databases from the PostgreSQL catalog query.
- Database metadata is represented by the public `DatabaseInfo` model.
- `DatabaseInfo` includes owner, encoding, collation, connection metadata and size in bytes.
- CLI `database list` maps to `CatalogService.list_databases()`.
- CLI `database describe` maps to `CatalogService.get_database(name)`.
- Missing lookup results raise `ResourceNotFoundError`.
- The missing-resource semantics are “not found or not visible.”
- `ResourceNotFoundError` maps to CLI exit code 5.
- Database exploration is read-only.
- JSON is the preferred output for automation.
- Object-level exploration continues with schemas, tables, views and indexes.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [First Connection](03_FIRST_CONNECTION.md)
- [CLI Fundamentals](06_CLI_FUNDAMENTALS.md)
- [Table, JSON and YAML Output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md)
- [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Schemas, Tables, Views and Indexes](10_SCHEMA_TABLE_VIEW_AND_INDEX_EXPLORATION.md)
- [Security Administration](11_SECURITY_ADMINISTRATION.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [Monitoring Guide](21_MONITORING_GUIDE.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Schemas, Tables, Views and Indexes](10_SCHEMA_TABLE_VIEW_AND_INDEX_EXPLORATION.md).
