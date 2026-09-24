# LOT-20 / T20-010 — SQL Injection Review

## Status

```text
Ticket: T20-010
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Result: PASS after hardening
```

## Review scope

The PostgreSQL adapter surface was reviewed by separating SQL input into three classes:

1. **values** — must use driver parameters;
2. **identifiers** — must use `psycopg.sql.Identifier`;
3. **SQL keywords/fragments** — must be static or selected from an explicit enum-backed
   whitelist.

The review covers catalog, security, runtime, monitoring, maintenance and restore target
operations.

## Findings

### Values

Read/query filters use PostgreSQL parameters (`%s`) and pass values separately to
`cursor.execute()` / `PostgreSQLExecutor`.

Examples include:

- schema/table/view/index filters;
- role/access inspection filters;
- runtime database/user/state filters;
- monitoring filters;
- restore target existence checks;
- maintenance target preflight;
- runtime backend PID operations;
- timeout settings through `pg_catalog.set_config`.

No user value needs SQL string interpolation.

### Identifiers

The dynamic identifier surfaces use `psycopg.sql.Identifier`:

- role names;
- role membership names;
- principals;
- relation schema/name;
- maintenance table/index targets;
- ANALYZE column names;
- restore target database names.

Regression tests use payloads containing quotes, semicolons, comments and destructive SQL
text and assert that the entire payload remains a quoted PostgreSQL identifier.

### SQL keywords

Two enum-derived keyword surfaces existed:

```text
AccessType
ReindexTargetType
```

They were already constrained by `StrEnum`, but T20-010 removes the remaining
`sql.SQL(enum.value)` construction and replaces it with explicit SQL fragment maps:

```text
_ACCESS_TYPE_SQL
_REINDEX_TARGET_SQL
```

This makes the trusted keyword boundary visible and prevents a future enum value from
silently becoming executable SQL text without an adapter change.

### Static query-module f-strings

Some catalog query modules compose module constants with f-strings, notably reusable
system-schema predicates. These substitutions are source-code constants, not runtime
operator input, and therefore do not form an injection boundary.

## Regression coverage

`tests/unit/test_sql_injection_review.py` verifies malicious payload handling for:

- role creation;
- relation GRANT principal/schema/table identifiers;
- restore database creation;
- VACUUM relation identifiers;
- ANALYZE relation and column identifiers;
- REINDEX target identifiers;
- explicit REINDEX keyword selection.

## Security rule frozen by this review

```text
runtime value       -> bind parameter
database identifier -> sql.Identifier
SQL keyword         -> static fragment / explicit whitelist
```

New PostgreSQL adapter code must preserve this distinction.

## Result

No exploitable string-interpolation path was found in the reviewed PostgreSQL execution
surface. T20-010 nevertheless produced defense-in-depth hardening by replacing dynamic
enum-to-SQL conversion with explicit whitelists and by adding hostile-input regression
tests.

## Next ticket

```text
T20-011 — command injection review
```
