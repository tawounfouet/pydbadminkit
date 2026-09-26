# PyDBAdminKit 1.0 — Sessions, Queries and Transactions

## Objective

Diagnose live PostgreSQL activity by distinguishing:

```text
session
query
transaction
```

These are related but different runtime concepts.

This guide focuses on the read-only commands:

```text
session list
query list
transaction list
```

and their public Python API equivalents.

For waits, locks and blocking chains, continue with guide 16.
For cancel/terminate operations, continue with guide 17.

## Prerequisites

Before continuing, understand the Runtime Administration overview from guide 14.

A useful first check is:

```bash
pydbadmin -c prod server info
pydbadmin -c prod session list
```

## Mental model

PyDBAdminKit exposes three different runtime lenses:

```text
Session
    → one visible PostgreSQL backend

Query
    → one currently active statement

Transaction
    → one backend with an open transaction
```

These sets overlap, but they are not identical.

A backend can be:

```text
session only
session + query
session + transaction
session + query + transaction
```

For example:

```text
idle connection
    → session
    → no active query
    → possibly no open transaction

active SELECT
    → session
    → active query
    → transaction may or may not be open explicitly

idle in transaction
    → session
    → no active query
    → open transaction
```

# PostgreSQL data source

All three surfaces are built from:

```text
pg_catalog.pg_stat_activity
```

but with different selection rules.

## Sessions

The session query reads visible rows from `pg_stat_activity` and optionally filters by:

```text
database
user
state
self
```

## Active queries

The query surface adds:

```text
state = 'active'
query_start IS NOT NULL
```

Therefore it does not represent idle sessions.

## Open transactions

The transaction surface adds:

```text
xact_start IS NOT NULL
```

Therefore it represents sessions currently associated with an open transaction.

# Session inspection

## CLI

```bash
pydbadmin -c prod session list
```

Available filters:

```text
--database <database>
--user <user>
--state <state>
--include-self
```

Examples:

```bash
pydbadmin -c prod session list --database analytics
```

```bash
pydbadmin -c prod session list --user app_user
```

```bash
pydbadmin -c prod session list --state active
```

```bash
pydbadmin -c prod session list --state idle_in_transaction
```

## Self exclusion

By default, the PostgreSQL query includes:

```text
pid <> pg_backend_pid()
```

so PyDBAdminKit's own inspection backend is excluded.

Use:

```bash
pydbadmin -c prod session list --include-self
```

only when needed.

## SessionState

The normalized public enum is:

```text
active
idle
idle_in_transaction
idle_in_transaction_aborted
fastpath_function_call
disabled
unknown
```

PostgreSQL states are mapped as:

```text
active
    → active

idle
    → idle

idle in transaction
    → idle_in_transaction

idle in transaction (aborted)
    → idle_in_transaction_aborted

fastpath function call
    → fastpath_function_call

disabled
    → disabled
```

Any unrecognized future/raw state maps to:

```text
unknown
```

This keeps the public API stable even if PostgreSQL introduces a new state.

## SessionInfo

The public model contains:

```text
pid
database
username
application_name
client_address
backend_type
state
backend_started_at
state_changed_at
wait_event_type
wait_event
```

### pid

Backend process identifier.

Constraint:

```text
pid > 0
```

### database

Database associated with the session when PostgreSQL exposes one.

### username

Database role associated with the backend.

### application_name

Client-provided PostgreSQL application name.

This can be useful for distinguishing:

```text
psql
application server
ETL process
scheduler
admin tool
```

when clients set it meaningfully.

### client_address

Remote client address when exposed by PostgreSQL.

It may be `None`.

### backend_type

PostgreSQL backend type.

Typical client sessions report:

```text
client backend
```

Other PostgreSQL processes can expose different backend types.

### backend_started_at

Timestamp corresponding to PostgreSQL `backend_start`.

This indicates when the backend/session started.

### state_changed_at

Timestamp corresponding to PostgreSQL `state_change`.

This is not the same as backend start time.

It helps answer:

```text
How long has this session remained in its current state?
```

### wait_event_type / wait_event

These fields expose the backend's current PostgreSQL wait event information when present.

Detailed interpretation belongs to guide 16.

## Human session output

Columns:

```text
PID
DATABASE
USER
APPLICATION
CLIENT
STATE
WAIT
BACKEND_TYPE
BACKEND_STARTED
```

The human renderer combines wait fields into:

```text
TYPE:EVENT
```

when both exist.

# Session filtering semantics

## Database

```bash
pydbadmin -c prod session list --database analytics
```

uses exact PostgreSQL database-name equality.

## User

```bash
pydbadmin -c prod session list --user app_user
```

uses exact PostgreSQL role-name equality.

## State

```bash
pydbadmin -c prod session list --state idle_in_transaction
```

uses the public normalized enum, translated back to PostgreSQL's raw state string.

For example:

```text
idle_in_transaction
    → idle in transaction
```

# Query inspection

## CLI

```bash
pydbadmin -c prod query list
```

Filters:

```text
--database
--user
--include-self
```

Unlike `session list`, there is no `--state` filter because the query itself already requires:

```text
state = active
```

## QueryInfo

The public model contains:

```text
pid
database
username
query_id
state
query_text
query_started_at
elapsed_ms
wait_event_type
wait_event
```

## query_id

The value comes directly from PostgreSQL's `pg_stat_activity.query_id`.

It is nullable:

```text
int | None
```

PyDBAdminKit does not synthesize a query ID when PostgreSQL returns none.

Do not treat `query_id` as a guaranteed non-null primary key for application logic.

## query_text

The query text comes from PostgreSQL's activity view.

It is nullable in the public model.

The human renderer normalizes it to one line and truncates the preview at 160 characters.

Machine JSON/YAML preserves the actual model field rather than the human preview.

## query_started_at

Derived from PostgreSQL:

```text
query_start
```

It is nullable in the public model.

## elapsed_ms

Calculated in PostgreSQL as:

```text
clock_timestamp() - query_start
```

converted to milliseconds.

Conceptually:

```text
elapsed_ms =
    EXTRACT(EPOCH FROM (clock_timestamp() - query_start))
    * 1000
```

Constraint:

```text
elapsed_ms >= 0
```

when present.

## Query ordering

Rows are ordered by:

```text
query_start
pid
```

so older active queries appear first for a stable snapshot.

# Query diagnosis

A useful first-pass workflow is:

```bash
pydbadmin -c prod query list
```

then filter:

```bash
pydbadmin \
  -c prod \
  query list \
  --database analytics \
  --user app_user
```

Pay attention to:

```text
PID
ELAPSED_MS
WAIT
QUERY
```

Long elapsed time does not by itself prove a problem.

It indicates duration, not cause.

A long query can be:

```text
CPU-bound
waiting on I/O
waiting on a lock
performing expected large work
```

Use wait/lock/blocking inspection for cause analysis.

# Transaction inspection

## CLI

```bash
pydbadmin -c prod transaction list
```

Filters:

```text
--database
--user
--include-self
```

## Selection rule

The PostgreSQL query includes:

```text
xact_start IS NOT NULL
```

This is the key distinction from active-query inspection.

## TransactionInfo

The public model contains:

```text
pid
transaction_started_at
elapsed_ms
database
username
state
backend_xid
backend_xmin
query_text
```

## transaction_started_at

Required timestamp mapped from PostgreSQL:

```text
xact_start
```

## elapsed_ms

Calculated as:

```text
clock_timestamp() - xact_start
```

in milliseconds.

Unlike `QueryInfo.elapsed_ms`, this field is required.

Constraint:

```text
elapsed_ms >= 0
```

## backend_xid

Mapped from:

```text
backend_xid
```

and converted to string when present.

It can be `None`.

## backend_xmin

Mapped from:

```text
backend_xmin
```

and converted to string when present.

It can be `None`.

These values are surfaced for diagnosis; PyDBAdminKit does not reinterpret them into another identifier model.

## query_text in transactions

The transaction view also includes PostgreSQL's current activity query field.

A transaction can remain open while the backend is not actively executing a statement.

Therefore do not infer:

```text
TransactionInfo.query_text
    == currently active query
```

Use `query list` to determine whether the backend currently has an active query.

# Idle in transaction

One of the most important runtime distinctions is:

```text
idle
vs
idle in transaction
```

An `idle` backend is connected but not currently executing.

An `idle in transaction` backend also has an open transaction.

PyDBAdminKit surfaces this through:

```text
SessionState.IDLE_IN_TRANSACTION
```

and through `transaction list`, because `xact_start` remains present.

A useful investigation is:

```bash
pydbadmin -c prod session list --state idle_in_transaction
```

followed by:

```bash
pydbadmin -c prod transaction list
```

# Aborted idle transactions

PostgreSQL can report:

```text
idle in transaction (aborted)
```

PyDBAdminKit normalizes this as:

```text
idle_in_transaction_aborted
```

Inspect it with:

```bash
pydbadmin \
  -c prod \
  session list \
  --state idle_in_transaction_aborted
```

This is distinct from a healthy idle connection.

# Session vs query duration

Do not confuse:

```text
backend_started_at
query_started_at
transaction_started_at
state_changed_at
```

They answer different questions.

```text
backend_started_at
    → when the session/backend began

query_started_at
    → when the current active query began

transaction_started_at
    → when the current open transaction began

state_changed_at
    → when the backend entered its current session state
```

# Practical timeline

A single backend can conceptually move through:

```text
backend_start
    ↓
idle
    ↓
BEGIN
    ↓
xact_start
    ↓
active query
    ↓
query_start
    ↓
idle in transaction
    ↓
state_change
    ↓
COMMIT / ROLLBACK
    ↓
idle
```

The three runtime commands expose different parts of that lifecycle.

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

## List sessions

```python
sessions = runtime.list_sessions()
```

Filter:

```python
from pydbadminkit.domain.runtime import SessionState

sessions = runtime.list_sessions(
    database="analytics",
    username="app_user",
    state=SessionState.IDLE_IN_TRANSACTION,
)
```

Return type:

```text
tuple[SessionInfo, ...]
```

## List active queries

```python
queries = runtime.list_queries(
    database="analytics",
    username="app_user",
)
```

Return type:

```text
tuple[QueryInfo, ...]
```

## List open transactions

```python
transactions = runtime.list_transactions(
    database="analytics",
    username="app_user",
)
```

Return type:

```text
tuple[TransactionInfo, ...]
```

# Correlating by PID

The key join field across these read models is:

```text
pid
```

A useful Python pattern is:

```python
sessions = {
    item.pid: item
    for item in runtime.list_sessions(database="analytics")
}

queries = {
    item.pid: item
    for item in runtime.list_queries(database="analytics")
}

transactions = {
    item.pid: item
    for item in runtime.list_transactions(database="analytics")
}

for pid, session in sessions.items():
    query = queries.get(pid)
    transaction = transactions.get(pid)

    print(
        pid,
        session.state,
        query.elapsed_ms if query else None,
        transaction.elapsed_ms if transaction else None,
    )
```

This is preferable to parsing human-formatted output.

# Machine output

## Session JSON

```bash
pydbadmin -c prod --output json session list
```

Representative shape:

```json
[
  {
    "pid": 101,
    "database": "analytics",
    "username": "app",
    "application_name": "psql",
    "client_address": "127.0.0.1",
    "backend_type": "client backend",
    "state": "idle_in_transaction",
    "backend_started_at": "2026-09-22T15:00:00+00:00",
    "state_changed_at": "2026-09-22T15:30:00+00:00",
    "wait_event_type": "Client",
    "wait_event": "ClientRead"
  }
]
```

## Query JSON

```bash
pydbadmin -c prod --output json query list
```

Representative fields:

```text
pid
database
username
query_id
state
query_text
query_started_at
elapsed_ms
wait_event_type
wait_event
```

## Transaction JSON

```bash
pydbadmin -c prod --output json transaction list
```

Representative fields:

```text
pid
transaction_started_at
elapsed_ms
database
username
state
backend_xid
backend_xmin
query_text
```

Machine output preserves dataclass field declaration order.

# Human output versus machine output

Human output prioritizes compact diagnosis.

For example, query text is truncated to a preview.

JSON/YAML preserve the full serialized public model.

Therefore:

```text
interactive diagnosis
    → table output

automation / evidence
    → JSON
```

# Worked diagnostic scenario: long active query

List active queries:

```bash
pydbadmin \
  -c prod \
  query list \
  --database analytics
```

Suppose PID 4281 has a large `ELAPSED_MS`.

Inspect its session:

```bash
pydbadmin \
  -c prod \
  session list \
  --database analytics \
  --state active
```

Then inspect waits:

```bash
pydbadmin \
  -c prod \
  wait list \
  --database analytics
```

Then locks/blocking if necessary.

Do not jump immediately to cancellation based only on elapsed time.

# Worked diagnostic scenario: idle in transaction

Find idle transactions:

```bash
pydbadmin \
  -c prod \
  session list \
  --state idle_in_transaction
```

Then inspect open transactions:

```bash
pydbadmin -c prod transaction list
```

Correlate by PID.

Important fields:

```text
transaction_started_at
elapsed_ms
backend_xid
backend_xmin
query_text
```

Then inspect waits and locks before deciding on intervention.

# Worked diagnostic scenario: application connection inventory

```bash
pydbadmin \
  -c prod \
  session list \
  --user app_user
```

Useful fields:

```text
application_name
client_address
backend_type
state
backend_started_at
```

This is useful for identifying where sessions originate when clients populate PostgreSQL metadata.

# Ordering guarantees

The PostgreSQL queries use deterministic ordering for each snapshot.

Sessions:

```text
ORDER BY pid
```

Queries:

```text
ORDER BY query_start, pid
```

Transactions:

```text
ORDER BY xact_start, pid
```

This supports stable human inspection and deterministic automation for a fixed underlying snapshot.

# Runtime state is volatile

Even with deterministic ordering, runtime state can change between commands.

For example:

```text
query list
    → PID 4281 active

one second later
    → query finished

transaction list
    → PID 4281 may now be idle or gone
```

Do not assume multiple CLI calls form one atomic snapshot.

# Permissions and visibility

PyDBAdminKit reads PostgreSQL runtime catalog views through the selected connection.

What is visible depends on PostgreSQL permissions and server configuration.

Nullable fields in public models must be handled as actual unknown/unavailable values.

Do not replace them with guessed values.

# Errors

These commands are read-only and use the standard PyDBAdminKit error hierarchy for:

```text
connection failures
authentication failures
authorization failures
database operation failures
internal mapping failures
```

List commands naturally return empty collections when no row matches the filters.

An empty result is not itself an error.

# Troubleshooting

## session list returns rows but query list is empty

Expected when sessions exist but none is currently `active`.

## transaction list is non-empty but query list is empty

Expected for idle-in-transaction backends.

## query_id is null

Allowed by the public model.

Do not invent a replacement identifier.

Use PID and the other runtime fields according to your integration needs.

## state becomes unknown

PyDBAdminKit maps any unrecognized PostgreSQL state string to:

```text
unknown
```

This preserves compatibility rather than failing the whole runtime query.

## application_name is missing

The client may not have populated it.

The field is nullable.

## client_address is missing

Possible for some connection/backend contexts.

Treat it as unavailable rather than erroneous.

## query text looks truncated

Human output intentionally limits the preview.

Use:

```bash
--output json
```

for the serialized model value.

## transaction query text appears to be an old statement

The transaction surface reads PostgreSQL's current activity query field.

Do not use that field alone to infer that the statement is currently executing.

Check `query list`.

# Production considerations

For production diagnosis:

1. begin with `session list`;
2. use database/user filters;
3. separate connection count from active-query count;
4. inspect `idle_in_transaction` explicitly;
5. compare query duration with transaction duration;
6. correlate models by PID;
7. treat `query_id` as optional;
8. use JSON when preserving evidence;
9. inspect waits/locks before intervention;
10. remember each CLI call is a point-in-time snapshot.

# Best practices

Prefer:

```text
session → query → transaction correlation
PID-based correlation
normalized SessionState
database/user filters
JSON for automation
wait/lock follow-up for slow queries
```

Avoid:

```text
equating session count with active query count
equating transaction query_text with active execution
treating elapsed_ms as root cause
assuming query_id is always present
assuming multiple commands are one atomic snapshot
terminating a backend before diagnosing its state
```

## Key takeaways

- Sessions, active queries and open transactions are different runtime sets.
- All three are currently sourced from PostgreSQL `pg_stat_activity`.
- `session list` is the broadest view.
- `query list` requires `state = 'active'`.
- `transaction list` requires `xact_start IS NOT NULL`.
- `SessionState` normalizes PostgreSQL state strings.
- Unknown future states map to `unknown`.
- Query duration and transaction duration are calculated independently.
- `query_id`, `backend_xid` and `backend_xmin` are nullable.
- PID is the practical correlation key across the runtime models.
- Human query text is preview-oriented; machine output preserves the model field.
- Runtime inspection is point-in-time and non-atomic across separate commands.
- Guide 16 continues with waits, locks and blocking chains.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [Locks, Waits and Blocking Chains](16_LOCKS_WAITS_AND_BLOCKING_CHAINS.md)
- [Cancel and Terminate Operations](17_CANCEL_AND_TERMINATE_OPERATIONS.md)
- [Monitoring](21_MONITORING_GUIDE.md)
- [Health Checks](22_HEALTH_CHECKS.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Locks, Waits and Blocking Chains](16_LOCKS_WAITS_AND_BLOCKING_CHAINS.md).
