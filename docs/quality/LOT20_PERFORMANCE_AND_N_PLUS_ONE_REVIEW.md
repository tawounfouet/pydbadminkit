# LOT-20 / T20-013 — Performance and N+1 Review

## Status

```text
Ticket: T20-013
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Result: PASS with documented bounded-query contracts
```

## Review principle

The 1.0 path must avoid database round trips that grow linearly with the number of rows
returned by a list operation.

The review therefore distinguishes:

```text
bounded multi-query description
        from
N + 1 query behavior
```

A description operation may use a small fixed query budget when each query retrieves a
different relation of the aggregate. It becomes N+1 only when additional database calls are
performed once per returned item.

## Catalog

List operations for databases, schemas, tables, views and indexes each delegate to one
set-oriented PostgreSQL query.

Description operations have fixed budgets independent of result cardinality:

| Operation | Query budget |
| --- | ---: |
| database get | 1 |
| schema get | 1 |
| table describe | 3 |
| view describe | 3 |
| index describe | 2 |

Table description retrieves the table, all columns and all constraints in three set-oriented
queries. It does not query once per column or constraint.

Existing adapter tests freeze the table-description query sequence.

## Security

Role listing, memberships, direct access, effective access and ownership use set-oriented
queries.

Role description has a fixed two-query budget:

```text
role row
+ membership set
```

Membership filtering into `member_of` and `members` happens in memory and does not issue
one query per membership.

Existing security adapter tests freeze that two-query sequence.

## Runtime

Sessions, queries, transactions, waits, locks and blocking relations each use one
set-oriented PostgreSQL query per requested view. Filters are pushed into SQL parameters.

There is no per-session follow-up query.

## Monitoring

`MonitoringService.collect_metrics()` performs:

```text
1 × connection statistics
1 × database sizes
```

The number of database-size rows changes only in-memory metric construction, not the number
of port calls. T20-013 adds a regression test with 100 database-size rows and verifies that
the call budget remains exactly 2.

Table and index statistics are also collected set-wise.

## Health checks

The default health suite intentionally executes independent checks for connectivity,
connection usage, queries, transactions, idle transactions and locks.

This is a **fixed check budget**, not N+1 behavior. Independent execution also preserves the
health model's failure isolation: one failed check can become UNKNOWN/CRITICAL without
preventing unrelated checks from running.

## Monitoring snapshot

A snapshot currently runs metric collection and the health suite sequentially. Connection
statistics may therefore be sampled once for metrics and again for health.

This is bounded duplicate work, not row-dependent N+1 behavior. It is retained in 0.6/1.0
because the snapshot explicitly does not claim atomic consistency and health-check
independence is part of the current behavior.

A future optimization may introduce a request-scoped observation cache, but such a cache
must not silently change health failure isolation or freshness semantics.

## Result-size consideration

Catalog and runtime list commands currently materialize complete result tuples. Filters are
available, but pagination/streaming is not part of the frozen 0.6 public API.

This is recorded as a scale consideration rather than an N+1 defect. Introducing pagination
before 1.0 would expand the CLI/API contract and is outside LOT-20 hardening scope.

## Frozen performance rule

```text
List operations must remain set-oriented.
Description operations may use a documented fixed query budget.
No adapter may add one database round trip per returned child item.
Monitoring row cardinality must not increase collection round trips.
```

## Next ticket

```text
T20-014 — PostgreSQL version matrix
```
