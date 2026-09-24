# LOT-21 / T21-004 — Runtime Concurrency Qualification

## Decision

```text
Ticket: T21-004
Result: PASS
Concurrency primitive: real concurrent PostgreSQL backends
Qualified behaviors: waits, locks, blocking graph, query cancel, session terminate
```

## Real contention scenario

The runtime integration suite creates real PostgreSQL contention with two independent
backends.

```text
backend A
  acquires advisory lock
        │
        ├──────── blocks ────────┐
        │                        ↓
backend B                  waits for same lock
                                 │
                                 ↓
                        pg_stat_activity
                        pg_locks
                        pg_blocking_pids()
                                 │
                                 ↓
                        PyDBAdminKit runtime
```

The test waits until PostgreSQL itself confirms the blocking edge before querying the
framework.

## Read-side concurrency qualification

The live integration tests verify that:

- `wait list` detects the waiting backend;
- `lock list --waiting-only` exposes the waiting advisory lock;
- `blocking list --output json` exposes the blocker → waiter edge;
- the blocking graph reports the expected root, blocked PID, blocking PID and depth.

The fixture releases the advisory lock and joins the waiter thread, preventing leaked
concurrent backends after the test.

## Mutation concurrency qualification

A separate real backend executes `pg_sleep(30)`.

### Query cancel

```text
active query
   ↓
runtime.query.cancel
   ↓
pg_cancel_backend
   ↓
query interrupted
   ↓
session remains usable
```

The integration test verifies both interruption and subsequent session usability.

### Session terminate

```text
active backend
   ↓
runtime.session.terminate
   ↓
pg_terminate_backend
   ↓
backend disconnected
```

The integration test verifies that the target backend no longer exists.

Both guarded mutations also verify started/succeeded audit events and stable operation
names.

## Cross-version execution

The runtime concurrency suite is included in the PostgreSQL integration matrix and
therefore executes against PostgreSQL 14, 15, 16, 17 and 18.

This is an actual concurrency qualification, not a unit-level simulation.

## Release gate

The 1.0 condition:

```text
runtime concurrency green
```

is satisfied when the PostgreSQL matrix is green with these runtime integration tests
enabled.

## Next ticket

```text
T21-005 — security qualification
```
