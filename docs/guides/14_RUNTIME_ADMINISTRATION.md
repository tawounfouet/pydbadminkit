# PyDBAdminKit 1.0 — Runtime Administration

## Objective

Inspect and administer live PostgreSQL runtime state through PyDBAdminKit.

This guide introduces the runtime surface:

```text
session
query
transaction
wait
lock
blocking
```

and the two guarded runtime mutations:

```text
query cancel <pid>
session terminate <pid>
```

Detailed runtime topics are continued in guides 15, 16 and 17.

## Prerequisites

Before runtime administration:

- verify the selected profile;
- verify the target server/database;
- understand JSON/YAML machine output;
- understand dry-run and confirmation semantics for mutations.

Start with:

```bash
pydbadmin -c prod server info
pydbadmin -c prod session list
```

## Runtime architecture

PyDBAdminKit separates read-only inspection from mutation:

```text
RuntimeService
    → sessions
    → active queries
    → open transactions
    → waits
    → locks
    → blocking chains

RuntimeMutationService
    → cancel query
    → terminate session
```

Inspection and mutation are intentionally distinct public services.

## Read-only commands

The stable 1.0 runtime inspection commands are:

```text
session list
query list
transaction list
wait list
lock list
blocking list
```

These do not modify PostgreSQL.

## Runtime mutations

The guarded runtime mutation commands are:

```text
query cancel <pid>
session terminate <pid>
```

Both are planned, guarded, confirmed and audited.

# Sessions

## CLI

List visible sessions:

```bash
pydbadmin -c prod session list
```

Filters:

```text
--database <database>
--user <user>
--state <state>
--include-self
```

Example:

```bash
pydbadmin \
  -c prod \
  session list \
  --database analytics \
  --user app_user \
  --state active
```

By default PyDBAdminKit excludes its own inspection backend.

Use:

```text
--include-self
```

when you intentionally want it included.

## SessionState

The public normalized enum contains:

```text
active
idle
idle_in_transaction
idle_in_transaction_aborted
fastpath_function_call
disabled
unknown
```

PostgreSQL states are normalized into these cross-engine values.

For example:

```text
idle in transaction
    → idle_in_transaction
```

Unexpected PostgreSQL state values map to:

```text
unknown
```

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

PID must be positive.

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

Wait output is rendered as:

```text
wait_event_type:wait_event
```

when both values exist.

# Active queries

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

The PostgreSQL query selects rows where:

```text
state = active
query_start IS NOT NULL
```

so this surface represents currently active queries, not all session query text.

## QueryInfo

Fields:

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

`elapsed_ms` is computed from PostgreSQL's current clock minus `query_start`.

It must be non-negative when present.

## Human query output

Columns:

```text
PID
DATABASE
USER
QUERY_ID
STATE
ELAPSED_MS
WAIT
QUERY
```

Human query text is normalized to one line and truncated to a preview of up to 160 characters.

Machine output preserves the full `query_text` value exposed by the model.

# Open transactions

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

The PostgreSQL runtime query selects rows where:

```text
xact_start IS NOT NULL
```

## TransactionInfo

Fields:

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

`transaction_started_at` and `elapsed_ms` are required.

This is useful for identifying long-running and idle-in-transaction work.

## Human transaction output

Columns:

```text
PID
DATABASE
USER
STATE
ELAPSED_MS
XID
XMIN
STARTED_AT
QUERY
```

# Waits

## CLI

```bash
pydbadmin -c prod wait list
```

Filters:

```text
--database
--user
--type <wait-event-type>
--include-self
```

The PostgreSQL query includes rows where:

```text
wait_event IS NOT NULL
```

## WaitInfo

Fields:

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

Both `wait_event_type` and `wait_event` are required non-blank strings in the public model.

# Locks

## CLI

List all visible backend locks:

```bash
pydbadmin -c prod lock list
```

Only waiting/ungranted locks:

```bash
pydbadmin -c prod lock list --waiting-only
```

Other filters:

```text
--database
--user
--include-self
```

`--waiting-only` maps to:

```text
granted = false
```

in the Python service.

## LockInfo

Fields include:

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

This preserves PostgreSQL lock detail rather than collapsing everything into relation locks only.

# Blocking chains

## CLI

```bash
pydbadmin -c prod blocking list
```

Filters:

```text
--database
--user
--include-self
```

The PostgreSQL implementation builds recursive blocking chains using:

```text
pg_blocking_pids(...)
```

## BlockingRelation

Each result is one edge in a blocking chain:

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

The model permits:

```text
blocking_pid = 0
```

for engine-specific sentinel cases such as prepared transactions.

## Blocking chain model

Conceptually:

```text
root waiter
    ↓ depth 1
blocker A
    ↓ depth 2
blocker B
    ↓ depth 3
blocker C
```

The recursive query prevents cycles by tracking the path.

# Python API

Build the public runtime service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_runtime_service

runtime = build_runtime_service(
    "prod",
    Path("config.toml"),
)
```

Examples:

```python
sessions = runtime.list_sessions()
queries = runtime.list_queries()
transactions = runtime.list_transactions()
waits = runtime.list_waits()
locks = runtime.list_locks()
blocking = runtime.list_blocking()
```

## Filtering in Python

```python
from pydbadminkit.domain.runtime import SessionState

active = runtime.list_sessions(
    database="analytics",
    username="app_user",
    state=SessionState.ACTIVE,
)

waiting_locks = runtime.list_locks(
    database="analytics",
    granted=False,
)

io_waits = runtime.list_waits(
    wait_event_type="IO",
)
```

# CLI-to-Python mapping

```text
session list       → RuntimeService.list_sessions(...)
query list         → RuntimeService.list_queries(...)
transaction list   → RuntimeService.list_transactions(...)
wait list          → RuntimeService.list_waits(...)
lock list          → RuntimeService.list_locks(...)
blocking list      → RuntimeService.list_blocking(...)
```

# JSON output

All runtime inspection commands support JSON.

Example:

```bash
pydbadmin -c prod --output json query list
```

The result is an array of typed runtime objects.

Datetimes serialize as ISO-8601 strings.

Enums serialize to their public values.

## Why JSON is preferable for runtime automation

Human output may:

- truncate query text;
- combine wait type/event for readability;
- render missing values as `-`.

JSON preserves the structured fields and should be used for automation.

# Runtime mutation model

The public mutation builder is:

```python
from pydbadminkit.bootstrap import build_runtime_mutation_service

runtime_mutation = build_runtime_mutation_service(
    "prod",
    Path("config.toml"),
)
```

Command models:

```text
CancelQueryCommand
TerminateSessionCommand
```

Both require:

```text
pid > 0
```

# Cancel query

CLI:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  query cancel 12345
```

The plan target is:

```text
pid:12345
```

Base risk:

```text
medium
```

In production:

```text
medium → high
```

The plan warns that:

- the backend remains connected;
- a cancelled statement can leave its transaction requiring rollback.

## Cancel eligibility

Execution is allowed only when the target:

```text
exists
is not PyDBAdminKit's own backend
is a client backend
has an active query
```

If these conditions are not met, the service raises an appropriate policy/resource error.

# Terminate session

CLI:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  session terminate 12345
```

Base risk:

```text
high
```

In production:

```text
high → critical
```

Therefore production termination requires exact typed-target confirmation.

Example:

```bash
pydbadmin \
  -c prod \
  session terminate 12345 \
  --confirm-target 'pid:12345'
```

## Termination warnings

The plan warns that:

- the target client is disconnected;
- any active transaction on the target session is rolled back.

## Termination eligibility

The target must:

```text
exist
not be PyDBAdminKit's own backend
be a client backend
```

PyDBAdminKit blocks signals to non-client backends.

# BackendSignalResult

The PostgreSQL adapter returns an atomic guard/result model:

```text
pid
target_exists
self_target
client_backend
changed
backend_type
active_query
```

The application service validates this result before reporting success.

This avoids treating a failed PostgreSQL signal request as a successful mutation.

# Mutation policy guards

Runtime mutations are blocked when:

```text
profile.read_only == true
environment == unknown
target is self
target is not a client backend
```

Query cancellation additionally requires:

```text
active_query == true
```

# Confirmation semantics

The standard risk mapping applies:

```text
medium   → simple
high     → explicit
critical → type_target
```

Therefore:

```text
cancel query in non-production
    → medium / simple

cancel query in production
    → high / explicit

terminate session in non-production
    → high / explicit

terminate session in production
    → critical / type_target
```

# Audit lifecycle

Executed runtime mutations are audited with:

```text
BLOCKED
STARTED
FAILED
SUCCEEDED
```

and include:

```text
actor
profile
environment
database
operation
target
risk
status
correlation_id
```

# Worked diagnostic workflow

Start broad:

```bash
pydbadmin -c prod session list
```

Inspect active work:

```bash
pydbadmin -c prod query list
```

Inspect transactions:

```bash
pydbadmin -c prod transaction list
```

Inspect waiting backends:

```bash
pydbadmin -c prod wait list
```

Inspect ungranted locks:

```bash
pydbadmin -c prod lock list --waiting-only
```

Inspect blocking chains:

```bash
pydbadmin -c prod blocking list
```

Only after diagnosis should cancellation/termination be considered.

# Runtime diagnostic mental model

```text
session
  ↓
active query
  ↓
open transaction
  ↓
wait event
  ↓
lock
  ↓
blocking chain
  ↓
cancel or terminate
```

This is a useful escalation path for incident diagnosis.

# Troubleshooting

## session list does not show PyDBAdminKit itself

Expected.

Self is excluded by default.

Use:

```text
--include-self
```

if needed.

## query list shows fewer rows than session list

Expected.

`query list` only returns active queries.

Idle sessions remain visible through `session list`.

## transaction list includes idle-in-transaction sessions

Expected when `xact_start` remains present.

This is one reason transaction inspection is separate from active-query inspection.

## lock list is noisy

Use:

```text
--waiting-only
```

to focus on ungranted locks.

## blocking list is empty while locks exist

A lock can exist without being part of a current blocking chain.

Use `lock list` and `wait list` alongside `blocking list`.

## cancel returns policy denied because no active query exists

Expected.

Cancellation requires an active query on a client backend.

## terminate returns policy denied for a background process

Expected.

Runtime mutation is restricted to client backends.

## PID disappeared between inspection and mutation

Runtime state is inherently volatile.

PyDBAdminKit can return:

```text
ResourceNotFoundError
```

if the backend no longer exists or is no longer visible.

# Production considerations

For production runtime administration:

1. begin with read-only inspection;
2. filter by database/user where possible;
3. use JSON when collecting incident evidence;
4. compare sessions, queries, transactions, waits, locks and blocking chains;
5. remember runtime state can change between commands;
6. dry-run before cancel/terminate;
7. prefer query cancellation before session termination when appropriate;
8. understand transaction consequences;
9. preserve exact target confirmation for production termination;
10. verify the runtime state after any mutation.

# Best practices

Prefer:

```text
inspect first
filter aggressively
query cancel before session terminate when sufficient
dry-run
exact PID targeting
JSON for automation
post-action verification
```

Avoid:

```text
terminating sessions from a stale snapshot
assuming every wait is a lock wait
assuming every lock is blocking
using terminate as the first diagnostic step
signaling background/server processes
including self unless needed
scraping truncated human query previews
```

## Key takeaways

- Runtime inspection is exposed through `RuntimeService`.
- Runtime mutations are exposed through `RuntimeMutationService`.
- Sessions, active queries, open transactions, waits, locks and blocking chains are separate views.
- PyDBAdminKit excludes its own inspection backend by default.
- Session states are normalized through `SessionState`.
- Query output contains active queries only.
- Blocking chains are recursive and based on PostgreSQL `pg_blocking_pids(...)`.
- Query cancellation is medium-risk by default.
- Session termination is high-risk by default.
- Production escalates cancel to high and terminate to critical.
- Runtime mutations only target client backends.
- Query cancellation additionally requires an active query.
- Guide 15 deep-dives sessions, queries and transactions.
- Guide 16 deep-dives waits, locks and blocking chains.
- Guide 17 deep-dives cancellation and termination.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Security Administration](11_SECURITY_ADMINISTRATION.md)
- [Sessions, Queries and Transactions](15_SESSIONS_QUERIES_AND_TRANSACTIONS.md)
- [Locks, Waits and Blocking Chains](16_LOCKS_WAITS_AND_BLOCKING_CHAINS.md)
- [Cancel and Terminate Operations](17_CANCEL_AND_TERMINATE_OPERATIONS.md)
- [Monitoring](21_MONITORING_GUIDE.md)
- [Health Checks](22_HEALTH_CHECKS.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Sessions, Queries and Transactions](15_SESSIONS_QUERIES_AND_TRANSACTIONS.md).
