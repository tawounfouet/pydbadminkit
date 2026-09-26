# PyDBAdminKit 1.0 — Locks, Waits and Blocking Chains

## Objective

Diagnose PostgreSQL contention by distinguishing three related but different runtime concepts:

```text
wait
lock
blocking chain
```

This guide focuses on the read-only commands:

```text
wait list
lock list
blocking list
```

and their public Python API equivalents.

For query/session interruption, continue with guide 17.

## Prerequisites

Before continuing, understand:

- runtime administration from guide 14;
- sessions, queries and transactions from guide 15;
- PID-based correlation between runtime models.

A useful initial sequence is:

```bash
pydbadmin -c prod query list
pydbadmin -c prod transaction list
```

Then inspect waits and locks.

## Mental model

These concepts are related but not interchangeable.

```text
Wait
    → backend is currently waiting on something

Lock
    → backend owns or is requesting a PostgreSQL lock

Blocking relation
    → one backend is preventing another backend from progressing
```

Therefore:

```text
a wait is not always a lock wait
a lock is not always blocking
a blocking chain is not equivalent to listing all locks
```

# Wait inspection

## CLI

```bash
pydbadmin -c prod wait list
```

Available filters:

```text
--database <database>
--user <user>
--type <wait-event-type>
--include-self
```

Example:

```bash
pydbadmin \
  -c prod \
  wait list \
  --database analytics \
  --user app_user
```

Filter by wait-event type:

```bash
pydbadmin \
  -c prod \
  wait list \
  --type Lock
```

## PostgreSQL selection rule

The 1.0 PostgreSQL query selects rows where:

```text
wait_event IS NOT NULL
```

from:

```text
pg_catalog.pg_stat_activity
```

This means `wait list` represents backends that PostgreSQL currently reports as waiting.

It does not mean every row is waiting on a heavyweight lock.

## WaitInfo

The public model contains:

```text
pid
wait_event_type
wait_event
database
username
state
state_changed_at
query_text
```

Required fields:

```text
pid > 0
wait_event_type non-blank
wait_event non-blank
```

## Wait-event type versus wait event

The two fields answer different questions.

```text
wait_event_type
    → broad PostgreSQL wait category

wait_event
    → specific event inside that category
```

Example:

```text
wait_event_type = Lock
wait_event      = transactionid
```

Human output keeps them as separate columns.

## Human wait output

Columns:

```text
PID
DATABASE
USER
STATE
WAIT_TYPE
WAIT_EVENT
QUERY
```

The query text is rendered as a one-line preview.

## Wait ordering

Rows are ordered by:

```text
wait_event_type
wait_event
pid
```

This groups similar waits together for a stable snapshot.

# Lock inspection

## CLI

List visible locks:

```bash
pydbadmin -c prod lock list
```

Show only ungranted/waiting locks:

```bash
pydbadmin -c prod lock list --waiting-only
```

Other filters:

```text
--database
--user
--include-self
```

## PostgreSQL data source

The 1.0 implementation reads:

```text
pg_catalog.pg_locks
```

and enriches lock rows with:

```text
pg_stat_activity
pg_class
pg_namespace
```

This provides session identity plus relation names when PostgreSQL can resolve them.

## granted

The most important lock-state field is:

```text
granted
```

Semantics:

```text
true
    → PostgreSQL has granted the lock

false
    → the backend is waiting for the lock
```

The CLI flag:

```text
--waiting-only
```

maps to:

```text
granted = false
```

## LockInfo

The public model contains:

```text
pid
lock_type
mode
granted
database
username
relation_schema
relation_name
transaction_id
virtual_transaction_id
virtual_transaction
page
tuple_id
fastpath
```

Required fields:

```text
pid
lock_type
mode
granted
```

## lock_type

The value comes directly from PostgreSQL `pg_locks.locktype`.

PyDBAdminKit does not replace PostgreSQL lock types with a reduced custom enum.

This preserves engine detail.

## mode

The lock mode also comes directly from PostgreSQL.

Examples can include PostgreSQL values such as:

```text
AccessShareLock
RowExclusiveLock
ExclusiveLock
AccessExclusiveLock
```

PyDBAdminKit does not infer blocking severity from the mode name alone.

## Relation information

When a lock is associated with a relation and PostgreSQL resolves it, PyDBAdminKit exposes:

```text
relation_schema
relation_name
```

Human output renders:

```text
schema.relation
```

when both exist.

Not every PostgreSQL lock is relation-backed, so these fields are nullable.

## Transaction identifiers

Lock rows can expose:

```text
transaction_id
virtual_transaction_id
virtual_transaction
```

These remain strings when present.

Do not assume every lock has all three values.

## Page and tuple

The public model preserves:

```text
page
tuple_id
```

when PostgreSQL supplies them.

Constraints:

```text
page >= 0
tuple_id >= 0
```

when present.

## fastpath

The PostgreSQL `fastpath` lock property is retained as:

```text
bool | None
```

Machine output preserves it even though the compact human table does not display it.

## Human lock output

Columns:

```text
PID
DATABASE
USER
LOCK_TYPE
MODE
GRANTED
RELATION
TXID
VIRTUAL_XID
PAGE
TUPLE
```

# Lock ordering

The PostgreSQL query orders by:

```text
granted
pid
locktype
mode
```

Because PostgreSQL boolean ordering places `false` before `true`, waiting/ungranted lock rows are naturally surfaced before granted rows in this ordering.

# Waiting lock versus blocking backend

An ungranted lock tells you:

```text
this backend is waiting for a lock
```

It does not by itself tell you:

```text
which backend is blocking it
```

For that, use:

```text
blocking list
```

# Blocking chains

## CLI

```bash
pydbadmin -c prod blocking list
```

Filters:

```text
--database <database>
--user <user>
--include-self
```

The database/user filters apply to the **root waiting backends** that seed the blocking-chain query.

## PostgreSQL primitive

PyDBAdminKit uses:

```text
pg_catalog.pg_blocking_pids(pid)
```

to determine immediate blockers.

It then recursively expands blockers of blockers.

## Recursive model

Conceptually:

```text
PID 100 waits for PID 200
PID 200 waits for PID 300
PID 300 runs / holds resource
```

PyDBAdminKit emits edges:

```text
root=100 blocked=100 blocking=200 depth=1
root=100 blocked=200 blocking=300 depth=2
```

This represents a chain rather than flattening everything into one row.

# BlockingRelation

The public model contains:

```text
root_pid
blocked_pid
blocking_pid
depth
database
blocked_username
blocking_username
wait_event_type
wait_event
blocked_query_text
blocking_query_text
```

## root_pid

The original waiting backend that started the recursive traversal.

Constraint:

```text
root_pid > 0
```

## blocked_pid

The backend blocked at this particular edge.

Constraint:

```text
blocked_pid > 0
```

## blocking_pid

The backend or engine sentinel that blocks the current edge.

Constraint:

```text
blocking_pid >= 0
```

Unlike ordinary runtime PID models, zero is allowed here.

## blocking_pid = 0

The public model intentionally permits:

```text
blocking_pid = 0
```

because PostgreSQL can represent certain non-session blockers, such as prepared transactions, with a sentinel identifier.

Do not automatically reject zero as invalid in blocking-chain integrations.

## depth

The first blocking edge has:

```text
depth = 1
```

and deeper recursive edges increment from there.

Constraint:

```text
depth > 0
```

# Cycle prevention

The recursive PostgreSQL query tracks a path:

```text
ARRAY[activity.pid, blocker.pid]
```

and extends it while recursing.

A next blocker is only followed when it is not already present in the path.

Conceptually:

```text
WHERE NOT blocker.pid = ANY(path)
```

This prevents recursive traversal from looping indefinitely on a cycle.

# Human blocking output

Columns:

```text
ROOT_PID
DEPTH
BLOCKED_PID
BLOCKING_PID
DATABASE
BLOCKED_USER
BLOCKING_USER
WAIT
BLOCKED_QUERY
BLOCKING_QUERY
```

The wait field combines:

```text
wait_event_type:wait_event
```

Query text is previewed in human output.

# Blocking ordering

Rows are ordered by:

```text
root_pid
depth
blocked_pid
blocking_pid
```

This keeps edges for one root waiter grouped in chain order.

# Python API

Build the runtime service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_runtime_service

runtime = build_runtime_service(
    "prod",
    Path("config.toml"),
)
```

## Waits

```python
waits = runtime.list_waits(
    database="analytics",
    username="app_user",
)
```

Filter by PostgreSQL wait-event type:

```python
lock_waits = runtime.list_waits(
    wait_event_type="Lock",
)
```

Return type:

```text
tuple[WaitInfo, ...]
```

## Locks

```python
locks = runtime.list_locks(
    database="analytics",
)
```

Only ungranted locks:

```python
waiting_locks = runtime.list_locks(
    database="analytics",
    granted=False,
)
```

Return type:

```text
tuple[LockInfo, ...]
```

## Blocking

```python
blocking = runtime.list_blocking(
    database="analytics",
    username="app_user",
)
```

Return type:

```text
tuple[BlockingRelation, ...]
```

# Correlating waits, locks and blocking

PID is the primary correlation field.

A useful Python pattern:

```python
waits = {
    item.pid: item
    for item in runtime.list_waits(database="analytics")
}

locks_by_pid = {}
for lock in runtime.list_locks(database="analytics"):
    locks_by_pid.setdefault(lock.pid, []).append(lock)

blocking = runtime.list_blocking(database="analytics")

for relation in blocking:
    print(
        "root",
        relation.root_pid,
        "blocked",
        relation.blocked_pid,
        "blocking",
        relation.blocking_pid,
        "depth",
        relation.depth,
    )
```

Use the structured models rather than parsing the human tables.

# Diagnostic workflow

A practical flow is:

```text
query list
    ↓
transaction list
    ↓
wait list
    ↓
lock list --waiting-only
    ↓
blocking list
```

This progressively answers:

```text
What is running?
Is a transaction open?
Is the backend waiting?
Is it waiting for a lock?
Who is actually blocking it?
```

# Worked scenario: lock wait

Suppose an application query is slow.

Inspect active queries:

```bash
pydbadmin -c prod query list --database analytics
```

Inspect waits:

```bash
pydbadmin \
  -c prod \
  wait list \
  --database analytics \
  --type Lock
```

Inspect waiting locks:

```bash
pydbadmin \
  -c prod \
  lock list \
  --database analytics \
  --waiting-only
```

Then identify blockers:

```bash
pydbadmin \
  -c prod \
  blocking list \
  --database analytics
```

Only after this chain is understood should a runtime mutation be considered.

# Worked scenario: wait but no blocking chain

A backend may appear in:

```text
wait list
```

but not:

```text
blocking list
```

This can be completely valid.

For example, its wait may be:

```text
client
I/O
IPC
timeout
other PostgreSQL wait categories
```

rather than a blocker represented by `pg_blocking_pids(...)`.

Therefore:

```text
wait != blocking
```

# Worked scenario: granted locks only

A backend can hold many granted locks while operating normally.

```bash
pydbadmin -c prod lock list --user app_user
```

Rows with:

```text
GRANTED = yes
```

are not by themselves evidence of contention.

Focus on:

```text
GRANTED = no
```

and blocking-chain evidence when investigating contention.

# Worked scenario: multi-hop blocking

Suppose:

```text
PID 101 → blocked by 202
PID 202 → blocked by 303
```

Then `blocking list` can expose:

```text
ROOT_PID  DEPTH  BLOCKED_PID  BLOCKING_PID
101       1      101          202
101       2      202          303
```

This distinguishes the immediate blocker from the upstream root cause candidate.

Do not assume the first blocker is always the final root blocker.

# Machine output

Use JSON for automation:

```bash
pydbadmin -c prod --output json wait list
pydbadmin -c prod --output json lock list
pydbadmin -c prod --output json blocking list
```

## Why machine output matters

Human output:

- truncates query text;
- combines some values for readability;
- omits some lower-level fields from the compact table.

JSON preserves the public dataclass structure.

For example, `LockInfo.fastpath` is preserved in machine output even though it is not a human table column.

# Point-in-time semantics

Waits, locks and blocking chains are volatile.

Between:

```text
wait list
```

and:

```text
blocking list
```

the underlying situation can change.

Examples:

```text
lock granted
transaction committed
backend exited
blocker changed
query completed
```

Separate CLI commands are not one atomic snapshot.

# Self exclusion

All three runtime inspection queries exclude PyDBAdminKit's own backend by default.

Use:

```text
--include-self
```

only when explicitly required.

This reduces diagnostic noise.

# Visibility and permissions

Runtime state comes from PostgreSQL catalog views.

Results depend on the permissions and visibility of the selected connection role.

Nullable user/query/relation fields should be treated as unavailable when PostgreSQL does not expose them.

Do not infer missing values.

# Errors

The commands are read-only.

Standard failures can include:

```text
connection error
authentication error
authorization error
database operation error
internal row-mapping error
```

Empty results are valid.

For example:

```text
blocking list → []
```

simply means no matching blocking-chain edges were visible at that moment.

# Troubleshooting

## wait list is empty

No matching backend currently has a non-null `wait_event`, or filters/visibility exclude the rows.

## lock list shows many rows

Expected.

PostgreSQL uses locks extensively during normal operation.

Use:

```text
--waiting-only
```

to focus on ungranted locks.

## waiting-only locks exist but blocking list is empty

Possible if runtime state changed between commands or visibility differs.

Re-run the snapshot sequence.

## wait type is not Lock

Then the backend may be waiting for something unrelated to heavyweight lock contention.

Use the wait fields as PostgreSQL reports them; do not force every wait into a lock explanation.

## relation is blank for a lock

Not every PostgreSQL lock targets a relation.

Inspect:

```text
lock_type
transaction_id
virtual_transaction_id
page
tuple_id
```

as applicable.

## blocking_pid is zero

Allowed by the public model for PostgreSQL sentinel/non-session blocker cases.

Do not treat it as a corrupted PID automatically.

## blocked query text is truncated

Only human output is preview-oriented.

Use JSON for the serialized public field.

# Production considerations

For production lock diagnosis:

1. begin with read-only runtime inspection;
2. identify active queries and open transactions;
3. inspect wait type before assuming lock contention;
4. use `lock list --waiting-only` to reduce noise;
5. use `blocking list` to identify actual blocker relationships;
6. follow recursive depth to distinguish immediate from upstream blockers;
7. correlate by PID;
8. capture JSON evidence when needed;
9. remember the runtime state is volatile;
10. only consider cancel/terminate after the chain is understood.

# Best practices

Prefer:

```text
wait → lock → blocking correlation
--waiting-only
PID-based analysis
recursive chain interpretation
JSON for incident evidence
post-action reinspection
```

Avoid:

```text
assuming every wait is a lock wait
assuming every granted lock is a problem
assuming first blocker is root blocker
assuming separate commands form an atomic snapshot
terminating a backend before identifying the chain
parsing truncated human query previews in automation
```

## Key takeaways

- Waits, locks and blocking relations are different runtime concepts.
- `wait list` reads backends with non-null PostgreSQL `wait_event`.
- `lock list` reads `pg_locks` and preserves PostgreSQL lock detail.
- `--waiting-only` means `granted = false`.
- A granted lock is not itself evidence of blocking.
- `blocking list` uses `pg_blocking_pids(...)`.
- Blocking chains are recursively expanded.
- Cycle prevention is built into the recursive query.
- `BlockingRelation.depth` starts at 1.
- `blocking_pid = 0` is intentionally valid for engine sentinel cases.
- Human output is compact; JSON preserves the full public model.
- Runtime state can change between inspection commands.
- Guide 17 continues with guarded query cancellation and session termination.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [Sessions, Queries and Transactions](15_SESSIONS_QUERIES_AND_TRANSACTIONS.md)
- [Cancel and Terminate Operations](17_CANCEL_AND_TERMINATE_OPERATIONS.md)
- [Monitoring](21_MONITORING_GUIDE.md)
- [Health Checks](22_HEALTH_CHECKS.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Cancel and Terminate Operations](17_CANCEL_AND_TERMINATE_OPERATIONS.md).
