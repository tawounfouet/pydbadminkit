# PyDBAdminKit 1.0 — Effective Access and Ownership

## Objective

Understand **why** a PostgreSQL role can access a relation and **which objects it owns** before changing privileges, memberships or roles.

This guide covers the read-only commands:

```text
effective-access list --role <role>
ownership list --owner <role>
```

and their public Python equivalents.

It completes the Security Administration section of the 1.0 guide set.

## Prerequisites

Before continuing, understand:

- roles and memberships;
- direct relation privileges;
- the difference between inspection and mutation;
- the security mutation guardrails from guides 11 and 12.

A useful starting sequence is:

```bash
pydbadmin -c prod role describe app_user
pydbadmin -c prod access list --role app_user
```

Then compare that with effective access.

# Direct access is not effective access

A direct grant answers:

```text
What privilege is explicitly granted to this principal?
```

Effective access answers:

```text
What privilege can this principal actually exercise,
and why?
```

These are not equivalent.

A role may have no direct `SELECT` grant and still effectively have `SELECT` because of:

```text
inherited role membership
PUBLIC
object ownership
superuser
```

That distinction is the core purpose of `effective-access`.

# Access sources

The public enum:

```text
AccessSource
```

contains:

```text
direct
inherited
public
owner
superuser
```

An effective privilege may contain more than one source at the same time.

## DIRECT

```text
direct
```

means the target role itself has the relation privilege in the relation ACL.

Conceptually:

```text
GRANT SELECT ON public.orders TO app_user;
```

Then:

```text
app_user
  SELECT
    source = direct
```

## INHERITED

```text
inherited
```

means effective access comes through another role relationship recognized by PostgreSQL role membership semantics.

The 1.0 PostgreSQL implementation considers two inherited cases:

1. an ACL grant exists for another role usable by the principal;
2. the principal can use the relation owner's role and is not itself the owner.

This is evaluated with PostgreSQL's role-membership capability checks.

## PUBLIC

```text
public
```

means the relation ACL grants the privilege to PostgreSQL's special `PUBLIC` grantee.

Conceptually:

```text
GRANT SELECT ON public.reference_data TO PUBLIC;
```

A role can therefore have effective access without any role-specific direct grant.

## OWNER

```text
owner
```

means the principal owns the relation.

Ownership is a distinct authorization source and should not be confused with an explicit ACL grant.

## SUPERUSER

```text
superuser
```

means the principal is a PostgreSQL superuser.

This is surfaced explicitly rather than hiding superuser-derived effective access behind a generic boolean.

# How effective access is computed

The PostgreSQL implementation evaluates the supported relation privileges:

```text
SELECT
INSERT
UPDATE
DELETE
TRUNCATE
REFERENCES
TRIGGER
```

across relation kinds:

```text
ordinary tables
partitioned tables
foreign tables
views
materialized views
```

For each relation and access type, PostgreSQL's:

```text
has_table_privilege(...)
```

determines whether the principal has the privilege.

If the privilege is effective, PyDBAdminKit attributes one or more source flags.

Conceptually:

```text
principal
    +
relation
    +
access type
    ↓
has_table_privilege
    ↓
source attribution
    ├── direct
    ├── inherited
    ├── public
    ├── owner
    └── superuser
```

# EffectiveAccess model

The public model is:

```text
EffectiveAccess
```

with:

| Field | Type | Meaning |
| --- | --- | --- |
| `principal` | `str` | role being analyzed |
| `access_type` | `AccessType` | effective relation privilege |
| `object` | `DatabaseObjectRef` | table/view target |
| `sources` | `tuple[AccessSource, ...]` | one or more contributing sources |

The model requires at least one source.

## Example Python object

Conceptually:

```python
EffectiveAccess(
    principal="alice",
    access_type=AccessType.SELECT,
    object=...,
    sources=(
        AccessSource.INHERITED,
        AccessSource.PUBLIC,
    ),
)
```

This means the same effective privilege is explained by two independent paths.

# CLI: effective-access list

Basic use:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role app_user
```

Filter by schema:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role app_user \
  --schema public
```

Filter by relation name:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role app_user \
  --object orders
```

Combine filters:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role app_user \
  --schema public \
  --object orders
```

Include system schemas:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role app_user \
  --include-system
```

# System-schema filtering

By default, the effective-access query excludes:

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

only when those objects are intentionally part of the analysis.

This flag changes query scope; it does not elevate privileges.

# Human output

The human renderer uses:

```text
PRINCIPAL
OBJECT
TYPE
ACCESS
SOURCES
```

Representative shape:

```text
PRINCIPAL  OBJECT         TYPE   ACCESS  SOURCES
alice      public.orders  table  SELECT  inherited
alice      public.lookup  table  SELECT  public
alice      public.report  view   SELECT  owner
```

When multiple sources contribute, they are rendered together.

# JSON output

Use:

```bash
pydbadmin \
  -c prod \
  --output json \
  effective-access list \
  --role alice \
  --schema public
```

Representative shape:

```json
[
  {
    "principal": "alice",
    "access_type": "SELECT",
    "object": {
      "object_type": "table",
      "name": {
        "name": "orders",
        "schema": "public",
        "database": null
      }
    },
    "sources": [
      "inherited"
    ]
  }
]
```

The object reference remains structured in machine output.

# Python API

Build the read-only security service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_service

security = build_security_service(
    "prod",
    Path("config.toml"),
)
```

Then:

```python
effective = security.list_effective_access(
    "alice",
    schema="public",
    object_name="orders",
)

for entry in effective:
    print(
        entry.principal,
        entry.object.name,
        entry.access_type,
        entry.sources,
    )
```

Return type:

```text
tuple[EffectiveAccess, ...]
```

# Compare direct and effective access

A reliable investigation pattern is:

```python
direct = security.list_direct_access(
    "alice",
    schema="public",
    object_name="orders",
)

effective = security.list_effective_access(
    "alice",
    schema="public",
    object_name="orders",
)
```

Then compare:

```text
direct
    → explicit ACL entries for alice

effective
    → privileges PostgreSQL says alice can exercise
      plus source attribution
```

# Why this matters before revoke

Suppose:

```text
alice has direct SELECT
alice also inherits SELECT from reporting_readers
```

Revoking the direct grant:

```text
REVOKE SELECT FROM alice
```

does not necessarily remove effective `SELECT`.

The inherited source can keep the privilege effective.

Therefore the safe flow is:

```text
access list
    ↓
effective-access list
    ↓
membership inspection
    ↓
revoke dry-run
    ↓
execute
    ↓
effective-access list again
```

# Why this matters before role alteration

Changing:

```text
INHERIT
```

or membership structure can alter effective privileges without changing relation ACLs.

Use effective-access analysis before and after role/membership mutations when the operational goal is authorization change.

# Why PUBLIC matters

A role-specific revoke may appear to succeed but the role can still retain the privilege through:

```text
PUBLIC
```

If the effective-access source contains:

```text
public
```

then removing a role-specific direct grant alone is not sufficient to remove the effective privilege.

# Why ownership matters

Owners are an independent source of effective authorization.

If:

```text
sources = (owner,)
```

a direct ACL revoke does not change the fact that the role owns the relation.

Ownership analysis must therefore accompany destructive or privilege-reduction workflows.

# Ownership command

Use:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner
```

The command is read-only.

# Ownership scope in PostgreSQL 1.0 implementation

The current PostgreSQL ownership query covers:

```text
database
schema
table-like relations
view-like relations
```

Table-like relations include:

```text
ordinary tables
partitioned tables
foreign tables
```

View-like relations include:

```text
views
materialized views
```

In the ownership mapper:

```text
r / p / f → table
v / m     → view
```

The public `DatabaseObjectType` enum is broader, but this ownership query does not produce every possible enum member.

For example, the current query does not emit index ownership rows.

# OwnershipInfo model

The public model is:

```text
OwnershipInfo
```

with:

```text
owner
object
```

where:

```text
object → DatabaseObjectRef
```

and that reference contains:

```text
object_type
name
```

# DatabaseObjectType

The public enum includes:

```text
server
database
schema
table
view
index
```

The ownership command can accept a filter from this enum.

However, the actual PostgreSQL ownership rows are limited to the object categories returned by the current ownership query.

That means requesting a valid enum filter does not imply the adapter can necessarily produce rows of that type.

# CLI ownership filters

Filter by type:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --type table
```

Filter relation ownership by schema:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --schema public
```

Include system schemas:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --include-system
```

Combine filters:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --type table \
  --schema public
```

# Schema filter semantics

The ownership query applies `--schema` to relation ownership rows.

Database and schema ownership rows do not carry a relation schema component in the same way.

Therefore use `--schema` primarily when investigating owned tables/views.

# System-object filtering in ownership

By default, system filtering applies to:

```text
schemas
tables
views
```

using the same familiar PostgreSQL system-schema exclusions.

Database ownership rows are not filtered by that schema predicate because databases are not schema-contained objects.

# Human ownership output

The human renderer uses:

```text
OWNER
OBJECT
TYPE
```

Representative shape:

```text
OWNER      OBJECT          TYPE
app_owner  analytics       database
app_owner  public          schema
app_owner  public.orders   table
app_owner  public.report   view
```

# JSON ownership output

Use:

```bash
pydbadmin \
  -c prod \
  --output json \
  ownership list \
  --owner app_owner
```

Representative shape:

```json
[
  {
    "owner": "app_owner",
    "object": {
      "object_type": "table",
      "name": {
        "name": "orders",
        "schema": "public",
        "database": null
      }
    }
  }
]
```

# Python ownership inspection

```python
from pydbadminkit.domain.common import DatabaseObjectType

owned_tables = security.list_ownership(
    "app_owner",
    object_type=DatabaseObjectType.TABLE,
    schema="public",
)

for entry in owned_tables:
    print(
        entry.owner,
        entry.object.object_type,
        entry.object.name,
    )
```

Return type:

```text
tuple[OwnershipInfo, ...]
```

# Ownership filtering implementation

The PostgreSQL adapter retrieves ownership rows and then applies the `object_type` filter to the mapped public models.

Conceptually:

```text
PostgreSQL ownership rows
    ↓
OwnershipInfo objects
    ↓
optional DatabaseObjectType filter
```

This means the filter operates on the normalized public object type.

# Role drop preflight

Before:

```text
role drop app_owner
```

inspect:

```bash
pydbadmin -c prod ownership list --owner app_owner
```

because PostgreSQL may reject role deletion while ownership/dependencies remain.

Then inspect direct and effective access as needed:

```bash
pydbadmin -c prod access list --role app_owner
pydbadmin -c prod effective-access list --role app_owner
```

A robust role-drop assessment is:

```text
role describe
    ↓
ownership list
    ↓
access list
    ↓
effective-access list
    ↓
role drop --dry-run
```

# Privilege-reduction preflight

Before reducing access:

```text
1. inspect direct access
2. inspect effective access
3. inspect membership relationships
4. inspect ownership
5. identify the actual source to remove
6. dry-run the mutation
```

This prevents changing the wrong authorization layer.

# Worked scenario: direct + inherited

Assume:

```text
alice has direct SELECT on public.orders
alice is member of reporting_readers
reporting_readers has SELECT on public.orders
```

Inspect direct access:

```bash
pydbadmin \
  -c staging \
  access list \
  --role alice \
  --schema public \
  --object orders
```

Inspect effective access:

```bash
pydbadmin \
  -c staging \
  effective-access list \
  --role alice \
  --schema public \
  --object orders
```

The effective sources may include:

```text
direct,inherited
```

After revoking only the direct privilege, effective access may remain because the inherited path still exists.

# Worked scenario: PUBLIC

Inspect:

```bash
pydbadmin \
  -c staging \
  effective-access list \
  --role app_user \
  --schema public \
  --object reference_data
```

If:

```text
SOURCES = public
```

then a role-specific grant is not the source of the effective privilege.

# Worked scenario: owner

Inspect ownership:

```bash
pydbadmin \
  -c staging \
  ownership list \
  --owner report_owner \
  --schema reporting
```

Then inspect effective access:

```bash
pydbadmin \
  -c staging \
  effective-access list \
  --role report_owner \
  --schema reporting
```

Owner-derived privileges can explain effective access even without matching direct ACL rows.

# Worked Python analysis

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_service
from pydbadminkit.domain.common import DatabaseObjectType

security = build_security_service(
    "prod",
    Path("config.toml"),
)

role = "app_user"

direct = security.list_direct_access(
    role,
    schema="public",
)

effective = security.list_effective_access(
    role,
    schema="public",
)

owned = security.list_ownership(
    role,
    object_type=DatabaseObjectType.TABLE,
    schema="public",
)

print("Direct privileges:")
for entry in direct:
    print(entry.object.name, entry.access_type)

print("Effective privileges:")
for entry in effective:
    print(entry.object.name, entry.access_type, entry.sources)

print("Owned tables:")
for entry in owned:
    print(entry.object.name)
```

# Effective-access result ordering

The PostgreSQL query orders results by:

```text
schema
relation
access type
```

This makes human and machine inspection deterministic for a stable database state.

# Ownership result ordering

Ownership rows are ordered by:

```text
object type
schema
object name
```

with non-schema objects ordered before schema-qualified relation names where applicable.

# Effective access and inherited ownership-role capability

One subtle implementation detail matters:

```text
source_inherited
```

is true not only for explicit ACL grants to inherited roles, but also when the principal can use the owner's role and is not itself the relation owner.

Therefore source attribution reflects the implemented PostgreSQL role semantics, not just a recursive list of ACL membership edges.

# Effective access is relation-focused

The 1.0 effective-access query evaluates relation privileges.

It does **not** claim to model every PostgreSQL authorization category.

For example, this guide does not treat the current effective-access result as a universal model for:

```text
database CONNECT
schema USAGE
function EXECUTE
sequence privileges
tablespace privileges
configuration privileges
```

The supported vocabulary is the relation-level `AccessType` set used by PyDBAdminKit 1.0.

# Visibility and connected principal

Security inspection is performed through the selected PostgreSQL connection.

Results depend on:

- target database;
- connected role;
- PostgreSQL catalog visibility;
- supported query scope.

Do not treat one profile's result as automatically representative of another security principal or database.

# Read-only behavior

Both:

```text
effective-access list
ownership list
```

are inspection commands.

They do not require:

```text
--dry-run
--yes
--confirm-target
```

because they do not mutate PostgreSQL.

# Errors

The methods use the standard PyDBAdminKit error hierarchy for connection, authorization and database-operation failures.

Unlike `role describe`, the list-style effective-access and ownership surfaces naturally return empty tuples/arrays when the query yields no matching entries.

Therefore:

```text
[]
```

can mean:

```text
no matching effective relation access
or
no matching ownership entries
```

for the requested filters.

Do not convert an empty list into a missing-resource error in your integration logic unless your own application contract requires that behavior.

# Troubleshooting

## Direct access exists but effective access is missing

Check:

- target database;
- exact role;
- schema/object filters;
- PostgreSQL authorization semantics;
- whether the requested privilege belongs to the supported relation-level access vocabulary.

## Effective access exists but direct access is empty

Inspect the `sources` field.

Likely explanations include:

```text
inherited
public
owner
superuser
```

## Revoke completed but access still works

Run effective-access again.

A different source may still grant the privilege.

## Ownership list is empty

Check:

- owner role name;
- target database;
- object-type filter;
- schema filter;
- system filtering;
- whether the object category is covered by the current ownership query.

## --type index returns no rows

The public enum includes `index`, but the current PostgreSQL ownership query does not emit index ownership rows.

This is expected for the current 1.0 implementation.

## Schema filter seems not to affect database ownership

Expected.

The schema filter applies to relation ownership rows; a database is not inside a schema.

## Need database/schema privileges rather than relation privileges

The current effective-access surface is relation-oriented.

Do not infer unsupported privilege categories from it.

# Production considerations

For production security analysis:

1. inspect effective access before revoking privileges;
2. inspect ownership before dropping roles;
3. inspect membership paths before altering `INHERIT` or removing memberships;
4. distinguish direct ACL state from PostgreSQL-effective access;
5. pay attention to `PUBLIC`;
6. treat owner-derived access as structurally different from ACL grants;
7. treat superuser-derived access as exceptional;
8. scope queries by schema/object on large catalogs;
9. preserve JSON evidence for sensitive authorization reviews when appropriate;
10. re-run effective-access after every privilege/membership mutation intended to reduce access.

# Best practices

Prefer:

```text
direct access + effective access comparison
ownership preflight before role drop
schema/object filters
source-aware privilege analysis
JSON for automation/evidence
post-mutation verification
```

Avoid:

```text
assuming direct grants equal effective privileges
assuming revoke removes all access paths
ignoring PUBLIC
ignoring ownership
ignoring inherited roles
treating superuser like ordinary ACL access
assuming ownership covers every DatabaseObjectType
using relation effective-access as a universal PostgreSQL privilege model
```

## Key takeaways

- Effective access answers what a role can actually do on supported relations and why.
- Sources are `direct`, `inherited`, `public`, `owner` and `superuser`.
- One effective privilege can have multiple sources.
- PyDBAdminKit uses PostgreSQL `has_table_privilege(...)` as the effective relation-access check.
- Direct privilege revocation does not guarantee effective privilege removal.
- Ownership is a separate authorization source.
- Ownership inspection currently covers databases, schemas, table-like relations and view-like relations.
- The public object-type enum is broader than the current PostgreSQL ownership query.
- Effective-access in 1.0 is relation-focused, not a universal PostgreSQL privilege model.
- Effective access and ownership should be part of preflight before destructive security mutations.
- The Part IV — Security Administration guide set is now complete.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Security Administration](11_SECURITY_ADMINISTRATION.md)
- [Roles, Memberships and Privileges](12_ROLES_MEMBERSHIPS_AND_PRIVILEGES.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Runtime Administration](14_RUNTIME_ADMINISTRATION.md).
