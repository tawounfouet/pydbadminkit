# PyDBAdminKit 1.0 — Schemas, Tables, Views and Indexes

## Objective

Explore schemas and relational objects inside the database selected by the active PyDBAdminKit
connection profile.

This guide covers the stable 1.0 object-explorer commands:

```text
schema list
schema describe <name>

table list
table describe <name>

view list
view describe <name>

index list
index describe <name>
```

All operations in this guide are read-only.

## Prerequisites

Before continuing, you should be comfortable with:

- connection profiles;
- database exploration;
- CLI root options;
- table/JSON/YAML output;
- the public Python API.

Verify the target first:

```bash
pydbadmin -c local connection test
pydbadmin -c local server info
pydbadmin -c local database list
```

## Object-explorer model

The implemented 1.0 catalog flow is:

```text
selected database connection
        ↓
CatalogService
        ↓
PostgreSQL catalog metadata
        ↓
SchemaInfo
TableInfo / TableDescription
ViewInfo / ViewDescription
IndexInfo / IndexDescription
```

The list commands return summaries.

The describe commands return richer typed descriptions.

## Selected database boundary

Schemas, tables, views and indexes are explored inside the database selected by the active
PostgreSQL session.

That matters because PostgreSQL does not provide transparent cross-database relation inspection
through one normal session.

PyDBAdminKit therefore treats:

```text
schema.table
```

as a local object in the selected database.

A three-part name such as:

```text
otherdb.public.orders
```

can be parsed into a `QualifiedName`, but table/view/index describe operations reject
cross-database inspection with:

```text
CapabilityNotAvailableError
```

Use a profile connected to the target database instead.

## Qualified names

PyDBAdminKit uses the public:

```text
QualifiedName
```

model.

Supported parser forms are:

```text
name
schema.name
database.schema.name
```

Examples:

```text
orders
public.orders
analytics.public.orders
```

For table/view/index describe commands, prefer:

```text
schema.name
```

The initial parser does not implement SQL-quoted identifier parsing.

Names containing dots as literal quoted identifier content are therefore outside this parser's
scope.

## Default schema for unqualified describe names

When a table, view or index describe call receives only:

```text
orders
```

the PostgreSQL catalog adapter resolves it against:

```text
public
```

Therefore:

```text
orders
```

is treated like:

```text
public.orders
```

for these describe operations.

To avoid ambiguity, use an explicit schema name.

# Schemas

## List schemas

Run:

```bash
pydbadmin -c local schema list
```

By default, PostgreSQL system schemas are excluded.

Include them with:

```bash
pydbadmin -c local schema list --include-system
```

## What counts as a system schema

The PostgreSQL implementation marks the following as system schemas:

```text
pg_catalog
information_schema
pg_toast
pg_temp_*
pg_toast_temp_*
```

This classification is reflected in the public `SchemaInfo.is_system` field.

## SchemaInfo model

```text
SchemaInfo
```

contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | `str` | schema name |
| `owner` | `str | None` | owner role |
| `is_system` | `bool` | whether the schema matches the system-schema rules |

Example Python:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service("local", Path("config.toml"))

schemas = catalog.list_schemas()

for schema in schemas:
    print(schema.name, schema.owner, schema.is_system)
```

## Describe one schema

CLI:

```bash
pydbadmin -c local schema describe public
```

Python:

```python
schema = catalog.get_schema("public")

print(schema.name)
print(schema.owner)
print(schema.is_system)
```

A missing or non-visible schema raises:

```text
ResourceNotFoundError
```

# Tables

## List tables

Run:

```bash
pydbadmin -c local table list
```

Filter to one schema:

```bash
pydbadmin -c local table list --schema public
```

Include system schemas:

```bash
pydbadmin -c local table list --include-system
```

Combine both:

```bash
pydbadmin -c local table list --schema pg_catalog --include-system
```

## Table kinds

The PostgreSQL implementation exposes these table-like relation kinds:

```text
table
partitioned_table
foreign_table
```

They map to the public enum:

```text
TableKind
```

The list query includes PostgreSQL relkinds:

```text
r  → ordinary table
p  → partitioned table
f  → foreign table
```

## TableInfo model

A table summary is represented by:

```text
TableInfo
```

with:

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | `QualifiedName` | schema-qualified logical name |
| `owner` | `str | None` | owner |
| `kind` | `TableKind` | table kind |
| `estimated_rows` | `int | None` | PostgreSQL row estimate |
| `size_bytes` | `int | None` | total relation size |

## Estimated rows are estimates

The table list uses PostgreSQL relation statistics.

The public field is intentionally named:

```text
estimated_rows
```

Do not treat it as an exact `COUNT(*)`.

It is catalog/statistics metadata suitable for exploration and sizing context.

## Table size

`size_bytes` uses PostgreSQL total relation size metadata.

It is exposed in bytes.

This can include more than just the table heap, according to PostgreSQL's total-relation-size
semantics.

PyDBAdminKit preserves the raw byte value rather than formatting it into MB/GB in the public model.

## Human table-list output

The human renderer uses:

```text
NAME
OWNER
KIND
EST_ROWS
SIZE_BYTES
```

Example shape:

```text
NAME           OWNER      KIND               EST_ROWS   SIZE_BYTES
public.orders  app_owner  table              120000     25165824
public.events  app_owner  partitioned_table  4500000    536870912
```

## Describe a table

CLI:

```bash
pydbadmin -c local table describe public.orders
```

The detailed result contains:

```text
TableInfo
columns
constraints
```

Python:

```python
from pydbadminkit.domain.common import parse_qualified_name

description = catalog.describe_table(
    parse_qualified_name("public.orders")
)

print(description.table.name)

for column in description.columns:
    print(column.position, column.name, column.data_type)

for constraint in description.constraints:
    print(constraint.name, constraint.constraint_type)
```

## ColumnInfo model

Table and view descriptions use:

```text
ColumnInfo
```

Fields:

| Field | Type |
| --- | --- |
| `name` | `str` |
| `position` | `int` |
| `data_type` | `str` |
| `nullable` | `bool` |
| `default` | `str | None` |
| `identity` | `bool` |
| `generated` | `bool` |
| `comment` | `str | None` |

Positions start at 1.

The type string comes from PostgreSQL's formatted type representation.

## Table column metadata

For tables, the implementation retrieves:

```text
column name
ordinal position
formatted data type
nullable
default expression
identity flag
generated flag
column comment
```

The human renderer shows:

```text
POSITION
NAME
TYPE
NULLABLE
DEFAULT
IDENTITY
GENERATED
```

The `comment` field remains part of the public model and machine output even though the compact
human table description does not display it.

## Constraint types

PyDBAdminKit exposes:

```text
primary_key
foreign_key
unique
check
exclusion
```

through:

```text
ConstraintType
```

A `ConstraintInfo` contains:

```text
name
constraint_type
columns
definition
```

The PostgreSQL implementation reads these from `pg_constraint` and preserves PostgreSQL's
constraint definition text.

## Table not found

A missing or non-visible table raises:

```text
ResourceNotFoundError
```

with semantics equivalent to:

```text
Table 'schema.name' was not found or is not visible.
```

# Views

## List views

Run:

```bash
pydbadmin -c local view list
```

Filter to a schema:

```bash
pydbadmin -c local view list --schema public
```

Include system schemas:

```bash
pydbadmin -c local view list --include-system
```

## View kinds

The implementation includes both:

```text
view
materialized_view
```

through:

```text
ViewKind
```

The PostgreSQL relation kinds are:

```text
v → view
m → materialized view
```

## ViewInfo model

A view summary contains:

```text
name
owner
kind
```

where `name` is a `QualifiedName`.

Human list columns:

```text
NAME
OWNER
KIND
```

## Describe a view

CLI:

```bash
pydbadmin -c local view describe public.active_orders
```

Python:

```python
from pydbadminkit.domain.common import parse_qualified_name

description = catalog.describe_view(
    parse_qualified_name("public.active_orders")
)

print(description.view.name)
print(description.view.kind)

for column in description.columns:
    print(column.name, column.data_type)

print(description.definition)
```

A `ViewDescription` contains:

```text
view
columns
definition
```

## View definition

The PostgreSQL implementation retrieves the view definition using PostgreSQL's native metadata
function.

The result is stored as:

```text
definition: str | None
```

For human output, the definition is displayed in a dedicated section.

## View columns

View columns use the same public `ColumnInfo` model.

For views:

```text
default   → None
identity  → False
generated → PostgreSQL-generated flag
```

where applicable.

## View not found

A missing or non-visible view raises:

```text
ResourceNotFoundError
```

# Indexes

## List indexes

Run:

```bash
pydbadmin -c local index list
```

Filter by schema:

```bash
pydbadmin -c local index list --schema public
```

Filter by table name:

```bash
pydbadmin -c local index list --table orders
```

Combine filters:

```bash
pydbadmin -c local index list --schema public --table orders
```

Include system schemas:

```bash
pydbadmin -c local index list --include-system
```

The `--table` filter accepts the table **name**, while `--schema` scopes it to a schema.

## IndexInfo model

An index summary contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | `QualifiedName` | index name |
| `table` | `QualifiedName` | indexed table |
| `method` | `str` | PostgreSQL access method |
| `owner` | `str | None` | owner |
| `unique` | `bool` | unique index |
| `primary` | `bool` | backs a primary key |
| `valid` | `bool` | PostgreSQL validity flag |
| `ready` | `bool` | PostgreSQL readiness flag |
| `size_bytes` | `int | None` | index relation size |

## Human index-list output

The human renderer uses:

```text
NAME
TABLE
METHOD
UNIQUE
PRIMARY
VALID
READY
SIZE_BYTES
```

Example shape:

```text
NAME                TABLE          METHOD  UNIQUE  PRIMARY  VALID  READY  SIZE_BYTES
public.orders_pkey  public.orders  btree   yes     yes      yes    yes    2097152
```

## Describe an index

CLI:

```bash
pydbadmin -c local index describe public.orders_pkey
```

Python:

```python
from pydbadminkit.domain.common import parse_qualified_name

description = catalog.describe_index(
    parse_qualified_name("public.orders_pkey")
)

print(description.index.name)
print(description.index.table)
print(description.index.method)
print(description.definition)
print(description.predicate)
```

An `IndexDescription` contains:

```text
index
definition
predicate
```

The `definition` field is required and non-blank.

The `predicate` is optional and is useful for partial indexes.

## Index method

The method is obtained from PostgreSQL access-method metadata.

Typical examples can include:

```text
btree
hash
gin
gist
brin
```

PyDBAdminKit exposes the PostgreSQL-reported method string rather than constraining it to a fixed
cross-engine enum.

## Valid and ready flags

The public model preserves PostgreSQL's:

```text
indisvalid
indisready
```

semantics as:

```text
valid
ready
```

These flags are particularly useful when investigating index build/reindex state.

Do not collapse them into one generic `usable` boolean.

## Partial indexes

For a partial index, `predicate` contains the PostgreSQL predicate expression.

For a non-partial index:

```text
predicate = None
```

In JSON, that becomes:

```json
"predicate": null
```

## Index not found

A missing or non-visible index raises:

```text
ResourceNotFoundError
```

# System-object filtering

Schemas, tables, views and indexes share a PostgreSQL system-schema predicate.

By default, objects in these schemas are excluded:

```text
pg_catalog
information_schema
pg_toast
pg_temp_*
pg_toast_temp_*
```

Use:

```text
--include-system
```

when you intentionally need those objects.

This is a presentation/query-scope choice, not a privilege escalation mechanism.

## Python equivalents

Build the public catalog service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service(
    "local",
    Path("config.toml"),
)
```

Then:

```python
schemas = catalog.list_schemas()
tables = catalog.list_tables(schema="public")
views = catalog.list_views(schema="public")
indexes = catalog.list_indexes(schema="public")
```

Describe objects:

```python
from pydbadminkit.domain.common import parse_qualified_name

table = catalog.describe_table(
    parse_qualified_name("public.orders")
)

view = catalog.describe_view(
    parse_qualified_name("public.active_orders")
)

index = catalog.describe_index(
    parse_qualified_name("public.orders_pkey")
)
```

## CLI-to-Python mapping

```text
CLI                                      Python

schema list                              list_schemas(...)
schema describe <name>                   get_schema(name)

table list                               list_tables(...)
table describe <schema.table>            describe_table(QualifiedName)

view list                                list_views(...)
view describe <schema.view>              describe_view(QualifiedName)

index list                               list_indexes(...)
index describe <schema.index>            describe_index(QualifiedName)
```

## JSON examples

### Table list

```bash
pydbadmin -c local --output json table list --schema public
```

Representative shape:

```json
[
  {
    "name": {
      "name": "orders",
      "schema": "public",
      "database": null
    },
    "owner": "app_owner",
    "kind": "table",
    "estimated_rows": 120000,
    "size_bytes": 25165824
  }
]
```

Because `QualifiedName` is a dataclass, machine output preserves its structure rather than
flattening it into a string.

### Schema list

```bash
pydbadmin -c local --output json schema list
```

Representative shape:

```json
[
  {
    "name": "public",
    "owner": "postgres",
    "is_system": false
  }
]
```

### View describe

```bash
pydbadmin -c local --output json view describe public.active_orders
```

The result contains:

```text
view
columns
definition
```

### Index describe

```bash
pydbadmin -c local --output json index describe public.orders_pkey
```

The result contains:

```text
index
definition
predicate
```

## Machine-output note about QualifiedName

Human output renders a `QualifiedName` as:

```text
public.orders
```

Machine output serializes the dataclass structurally:

```json
{
  "name": "orders",
  "schema": "public",
  "database": null
}
```

Automation should consume the structured fields.

Do not assume machine output uses the human string representation.

## Invalid qualified names

The parser accepts at most three dot-separated components.

Invalid examples include:

```text
a.b.c.d
public..orders
.
```

These raise `ValueError`.

In the CLI, table/view/index describe commands translate such parsing errors into usage failure:

```text
exit code 2
```

## Cross-database describe limitation

This input parses:

```text
analytics.public.orders
```

but PostgreSQL relation inspection through the current session does not support crossing into
another database.

For table/view/index description, PyDBAdminKit raises:

```text
CapabilityNotAvailableError
```

That error maps to CLI exit code:

```text
6
```

The correct workflow is to connect a profile to the other database and inspect it there.

## Missing resource semantics

For schemas, tables, views and indexes, missing describe targets use:

```text
ResourceNotFoundError
```

The semantics remain:

```text
not found or not visible
```

This maps to CLI exit code:

```text
5
```

## Read-only nature

All commands in this guide are inspection operations.

They do not:

- create schemas;
- alter tables;
- create/drop views;
- create/drop indexes;
- change owners;
- modify constraints.

They therefore do not use mutation confirmation or audit execution flows.

## Worked exploration session

Inspect schemas:

```bash
pydbadmin -c local schema list
```

Inspect public tables:

```bash
pydbadmin -c local table list --schema public
```

Describe a table:

```bash
pydbadmin -c local table describe public.orders
```

Inspect public views:

```bash
pydbadmin -c local view list --schema public
```

Describe a view:

```bash
pydbadmin -c local view describe public.active_orders
```

Inspect indexes on a table:

```bash
pydbadmin -c local index list --schema public --table orders
```

Describe the primary index:

```bash
pydbadmin -c local index describe public.orders_pkey
```

## Worked Python exploration

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.domain.common import parse_qualified_name

catalog = build_catalog_service(
    "local",
    Path("config.toml"),
)

schemas = catalog.list_schemas()

tables = catalog.list_tables(schema="public")
views = catalog.list_views(schema="public")
indexes = catalog.list_indexes(schema="public", table="orders")

orders = catalog.describe_table(
    parse_qualified_name("public.orders")
)

for column in orders.columns:
    print(
        column.position,
        column.name,
        column.data_type,
        column.nullable,
    )

for constraint in orders.constraints:
    print(
        constraint.name,
        constraint.constraint_type,
        constraint.columns,
    )

for index in indexes:
    print(
        index.name,
        index.method,
        index.unique,
        index.primary,
        index.valid,
        index.ready,
    )
```

## Object-explorer workflow

A useful progression is:

```text
database list
    ↓
database describe
    ↓
schema list
    ↓
table list
    ↓
table describe
    ↓
view list / describe
    ↓
index list / describe
```

This creates a read-only structural picture of the selected PostgreSQL database.

## Troubleshooting

### Object list is empty

Check:

- selected profile;
- selected database;
- schema filter;
- PostgreSQL visibility;
- whether system objects are excluded;
- object kind.

For example, a materialized view appears under:

```text
view list
```

not `table list`.

### Table exists but describe without schema fails

Use:

```text
schema.table
```

because an unqualified describe defaults to the `public` schema.

### Need system objects

Add:

```text
--include-system
```

to list operations.

### Need another database

Do not use a three-part name as a cross-database shortcut.

Create/select a profile connected to that database.

### Need exact row count

`estimated_rows` is not an exact count.

PyDBAdminKit's catalog explorer intentionally exposes PostgreSQL estimates for this surface.

### View definition is null

The public model permits:

```text
definition = None
```

Handle it explicitly in Python/automation.

### Index predicate is null

Expected for a non-partial index.

### Qualified name parser rejects quoted syntax

SQL-quoted identifier parsing is outside the initial parser scope.

The supported parser is deliberately simple and dot-component based.

## Production considerations

For production exploration:

1. prefer a read-only profile;
2. scope list operations by schema when the catalog is large;
3. keep system objects excluded unless intentionally investigating them;
4. treat row counts as estimates;
5. treat size metrics as point-in-time metadata;
6. use explicit schema-qualified names;
7. use JSON for automation;
8. handle nullable metadata explicitly;
9. use a database-specific profile rather than attempting cross-database object inspection;
10. remember that visibility reflects the connected PostgreSQL principal.

## Best practices

Prefer:

```text
schema-qualified names
read-only profiles
schema filters
list before describe
JSON for scripts
typed QualifiedName in Python
ResourceNotFoundError handling
CapabilityNotAvailableError handling
```

Avoid:

```text
assuming public is always the intended schema
treating estimated_rows as COUNT(*)
cross-database relation inspection through one session
parsing human QualifiedName strings in automation
assuming system objects are included by default
depending on internal PostgreSQL query modules
```

## Key takeaways

- Schema, table, view and index exploration is read-only in 1.0.
- System schemas are excluded by default.
- `--include-system` explicitly adds PostgreSQL system schemas.
- Tables include ordinary, partitioned and foreign tables.
- Views include regular and materialized views.
- Table descriptions include columns and constraints.
- View descriptions include columns and definition.
- Index descriptions include definition and optional predicate.
- `QualifiedName` supports one-, two- and three-part logical names.
- Unqualified table/view/index describes default to `public`.
- Cross-database object description is rejected with `CapabilityNotAvailableError`.
- Missing/non-visible objects raise `ResourceNotFoundError`.
- Machine output preserves `QualifiedName` structurally.
- The Object Explorer portion of the guide set is now complete.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Database Exploration](09_DATABASE_EXPLORATION.md)
- [CLI Fundamentals](06_CLI_FUNDAMENTALS.md)
- [Table, JSON and YAML Output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md)
- [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Security Administration](11_SECURITY_ADMINISTRATION.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Security Administration](11_SECURITY_ADMINISTRATION.md).
