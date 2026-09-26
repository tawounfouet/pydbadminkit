# PyDBAdminKit 1.0 — Cancel and Terminate Operations

## Objective

Safely interrupt PostgreSQL runtime activity with PyDBAdminKit by choosing between:

```text
query cancel <pid>
session terminate <pid>
```

These commands are not equivalent.

This guide explains:

- the difference between query cancellation and session termination;
- the public command models;
- risk and confirmation rules;
- backend eligibility checks;
- dry-run behavior;
- production escalation;
- PostgreSQL signal semantics;
- audit and error behavior;
- operational decision patterns.

This guide completes Part V — Runtime Administration.

## Prerequisites

Before cancelling or terminating anything, complete runtime diagnosis.

Recommended sequence:

```text
session list
    ↓
query list
    ↓
transaction list
    ↓
wait list
    ↓
lock list --waiting-only
    ↓
blocking list
    ↓
cancel or terminate only if justified
```

Review guides 14, 15 and 16 first.

# Cancel is not terminate

The core distinction is:

```text
query cancel
    → attempts to stop the current active statement
    → leaves the backend session connected

session terminate
    → terminates the client backend
    → disconnects the client
    → active transaction is rolled back
```

Operationally:

```text
cancel
    → narrower intervention

terminate
    → stronger intervention
```

When cancellation is sufficient, it is generally the less disruptive operation.

# Public CLI surface

## Cancel query

```bash
pydbadmin \
  -c staging \
  query cancel 12345
```

## Terminate session

```bash
pydbadmin \
  -c staging \
  session terminate 12345
```

Both commands also accept:

```text
--confirm-target <target>
```

for critical operations.

Global safety options apply:

```text
--dry-run
--yes
--non-interactive
```

# Public Python models

The public runtime mutation command models are:

```text
CancelQueryCommand
TerminateSessionCommand
```

Both contain:

```text
pid: int
```

and validate:

```text
pid > 0
```

Example:

```python
from pydbadminkit.domain.runtime import CancelQueryCommand

command = CancelQueryCommand(pid=12345)
```

Invalid PID values fail before the mutation is planned.

# RuntimeMutationService

Build the public mutation service with:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_runtime_mutation_service

service = build_runtime_mutation_service(
    "staging",
    Path("config.toml"),
)
```

The service exposes:

```text
plan_cancel_query(...)
cancel_query(...)

plan_terminate_session(...)
terminate_session(...)
```

The mutation lifecycle is:

```text
command
    ↓
plan
    ↓
policy
    ↓
confirmation
    ↓
audit STARTED
    ↓
adapter signal
    ↓
signal-result validation
    ↓
audit SUCCEEDED / FAILED / BLOCKED
    ↓
OperationResult
```

# Query cancellation

## Dry-run first

```bash
pydbadmin \
  -c staging \
  --dry-run \
  query cancel 12345
```

This returns an `OperationPlan`.

No PostgreSQL signal is sent.

## Plan target

The exact target is:

```text
pid:12345
```

This target string is also used for critical typed-target confirmation.

## Plan effect

The plan records:

```text
Request cancellation of the query on backend PID 12345.
```

## Plan warnings

Cancellation includes two important warnings:

```text
The backend session remains connected after a successful cancellation.

A cancelled statement can leave its transaction requiring rollback.
```

This is why cancellation must not be interpreted as "the session is now clean and idle".

## Base risk

Query cancellation starts at:

```text
medium
```

Therefore outside production:

```text
medium
    → simple confirmation
```

In production:

```text
medium
    → high
    → explicit confirmation
```

## Interactive execution

Outside production:

```bash
pydbadmin \
  -c staging \
  query cancel 12345
```

The CLI can request confirmation interactively.

## Approved non-interactive execution

For a plan requiring simple/explicit approval:

```bash
pydbadmin \
  -c staging \
  --non-interactive \
  --yes \
  query cancel 12345
```

In production, `--yes` can satisfy the high-risk explicit approval because cancellation escalates to high, not critical.

# Query-cancel eligibility

A successful cancel requires all of the following:

```text
target exists
target is not PyDBAdminKit itself
target is a client backend
target currently has an active query
PostgreSQL successfully delivers the cancel signal
```

If any condition fails, PyDBAdminKit does not report a successful mutation.

# Active-query requirement

Cancellation has an additional rule not required for termination:

```text
active_query is True
```

If the target session exists but is idle:

```text
PolicyDeniedError
```

is raised with the meaning:

```text
Query cancellation requires a client backend with an active query.
```

This prevents using `query cancel` as a vague session-level interrupt.

# PostgreSQL cancellation primitive

The PostgreSQL adapter ultimately uses:

```text
pg_catalog.pg_cancel_backend(pid)
```

but only after the guard query determines that:

- the target exists;
- it is not self;
- it is a client backend;
- it is active.

Conceptually:

```text
guard target
    ↓
eligible?
    ↓ yes
pg_cancel_backend(pid)
```

# Session termination

## Dry-run first

```bash
pydbadmin \
  -c staging \
  --dry-run \
  session terminate 12345
```

## Plan target

```text
pid:12345
```

## Plan effect

```text
Terminate client backend session PID 12345.
```

## Plan warnings

Termination warns:

```text
The target client will be disconnected.

Any active transaction on the target session will be rolled back.
```

This is materially stronger than query cancellation.

# Termination risk

Base risk:

```text
high
```

Outside production:

```text
high
    → explicit confirmation
```

In production:

```text
high
    → critical
    → type_target
```

# Production terminate example

Dry-run:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  session terminate 12345
```

Expected plan target:

```text
pid:12345
```

Execution:

```bash
pydbadmin \
  -c prod \
  session terminate 12345 \
  --confirm-target 'pid:12345'
```

For this critical operation:

```text
--yes
```

does not replace typed-target proof.

# Session-termination eligibility

Termination requires:

```text
target exists
target is not PyDBAdminKit itself
target is a client backend
PostgreSQL successfully delivers the terminate signal
```

Unlike cancellation, termination does not require an active query.

A client backend can be terminated whether it is:

```text
active
idle
idle in transaction
```

provided the other guards pass.

# PostgreSQL termination primitive

The PostgreSQL adapter ultimately uses:

```text
pg_catalog.pg_terminate_backend(pid)
```

after the target guard checks.

Conceptually:

```text
guard target
    ↓
eligible client backend?
    ↓ yes
pg_terminate_backend(pid)
```

# Self-protection

PyDBAdminKit explicitly blocks signaling its own execution backend.

The guard detects:

```text
target_pid == pg_backend_pid()
```

and the application layer raises:

```text
PolicyDeniedError
```

This applies to both:

```text
query cancel
session terminate
```

# Client-backend-only policy

Runtime mutations are restricted to:

```text
backend_type = client backend
```

If PostgreSQL reports another backend type, PyDBAdminKit blocks the mutation.

Conceptually:

```text
background worker
autovacuum worker
checkpointer
walwriter
other non-client process
    → blocked
```

The exact backend type returned by PostgreSQL is preserved in the error context and signal result.

# BackendSignalResult

The PostgreSQL adapter returns:

```text
BackendSignalResult
```

Fields:

```text
pid
target_exists
self_target
client_backend
changed
backend_type
active_query
```

This model is important because success is not inferred merely from issuing SQL.

PyDBAdminKit validates what PostgreSQL reports.

# Signal-result validation

The application service evaluates the result in this order:

```text
target exists?
    no → ResourceNotFoundError

self target?
    yes → PolicyDeniedError

client backend?
    no → PolicyDeniedError

cancel and active query?
    no → PolicyDeniedError

signal changed?
    no → DatabaseOperationError

otherwise
    → success
```

# Target disappeared

Runtime state is volatile.

A PID may exist during inspection and disappear before mutation.

Then PyDBAdminKit raises:

```text
ResourceNotFoundError
```

with the meaning:

```text
Backend PID <pid> was not found or is no longer visible.
```

This is an expected race condition in runtime administration.

# Signal not delivered

If the backend is eligible but PostgreSQL reports:

```text
changed = false
```

PyDBAdminKit raises:

```text
DatabaseOperationError
```

rather than returning success.

This prevents false-positive mutation results.

# Profile policy

Before execution, both runtime mutations enforce connection-profile policy.

Blocked cases:

```text
read_only = true
environment = unknown
```

Errors:

```text
Mutation blocked by read-only connection profile.

Mutation blocked because the connection environment is unknown.
```

Dry-run still returns the plan without execution.

# Risk matrix

The implemented matrix is:

| Operation | Base risk | Non-production confirmation | Production risk | Production confirmation |
| --- | --- | --- | --- | --- |
| query cancel | medium | simple | high | explicit |
| session terminate | high | explicit | critical | type_target |

Production escalation is:

```text
medium → high
high   → critical
```

# Confirmation model

General mapping:

```text
low      → none
medium   → simple
high     → explicit
critical → type_target
```

## --yes

`--yes` can approve:

```text
simple
explicit
```

It cannot satisfy:

```text
type_target
```

## --confirm-target

Critical runtime operations require the exact plan target.

Example:

```text
pid:12345
```

A mismatched value is rejected.

# Non-interactive automation

## Dry-run

```bash
pydbadmin \
  -c prod \
  --non-interactive \
  --output json \
  --dry-run \
  session terminate 12345
```

This safely emits the `OperationPlan`.

## Production cancel

Because production cancel is high:

```bash
pydbadmin \
  -c prod \
  --non-interactive \
  --yes \
  --output json \
  query cancel 12345
```

## Production terminate

Because production terminate is critical:

```bash
pydbadmin \
  -c prod \
  --non-interactive \
  --output json \
  session terminate 12345 \
  --confirm-target 'pid:12345'
```

# Python dry-run

## Cancel

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_runtime_mutation_service
from pydbadminkit.domain.runtime import CancelQueryCommand
from pydbadminkit.domain.safety import MutationOptions

service = build_runtime_mutation_service(
    "staging",
    Path("config.toml"),
)

command = CancelQueryCommand(pid=12345)

plan = service.plan_cancel_query(command)

outcome = service.cancel_query(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)

print(outcome.target)
print(outcome.risk)
print(outcome.confirmation)
```

## Terminate

```python
from pydbadminkit.domain.runtime import TerminateSessionCommand

command = TerminateSessionCommand(pid=12345)

plan = service.plan_terminate_session(command)

outcome = service.terminate_session(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)
```

# Python execution

For simple/explicit confirmation:

```python
result = service.cancel_query(
    command,
    MutationOptions(approved=True),
    plan=plan,
)
```

For critical typed-target confirmation:

```python
result = service.terminate_session(
    command,
    MutationOptions(
        confirmed_target=plan.target,
    ),
    plan=plan,
)
```

Application services do not prompt.

The caller must provide the required approval evidence.

# OperationPlan output

Dry-run returns:

```text
OperationPlan
```

with:

```text
operation
target
environment
risk
confirmation
effects
warnings
correlation_id
```

Example operation names:

```text
runtime.query.cancel
runtime.session.terminate
```

# OperationResult output

Successful execution returns:

```text
OperationResult
```

with:

```text
operation
status = succeeded
changed = true
message
metadata
```

Runtime metadata contains:

```text
target
pid
risk
correlation_id
backend_type
```

# Human output

Dry-run human output includes:

```text
Operation
Target
Environment
Risk
Confirmation
Correlation ID

EFFECTS

WARNINGS
```

Successful execution includes:

```text
Operation
Status
Changed
Message

METADATA
```

# JSON machine output

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  --output json \
  query cancel 12345
```

emits a machine-readable `OperationPlan`.

Execution:

```bash
pydbadmin \
  -c staging \
  --yes \
  --output json \
  query cancel 12345
```

emits a machine-readable `OperationResult`.

Automation must distinguish the two payload shapes.

# Audit lifecycle

Runtime mutations emit audit events.

Possible lifecycle:

```text
BLOCKED
STARTED
FAILED
SUCCEEDED
```

## Before PostgreSQL execution

Policy or approval failure:

```text
BLOCKED
```

## Before signal action

PyDBAdminKit emits:

```text
STARTED
status = RUNNING
```

## Signal policy rejection

For example:

```text
self target
non-client backend
no active query for cancel
```

is audited as:

```text
BLOCKED
```

## Operational failure

For example:

```text
backend disappeared
PostgreSQL signal not delivered
other PyDBAdminError
```

is recorded as failed according to the service's exception path.

## Success

A validated signal produces:

```text
SUCCEEDED
```

with the same correlation ID as the plan.

# Error and exit semantics

Relevant public error codes include:

```text
RESOURCE_NOT_FOUND
POLICY_DENIED
CONFIRMATION_REQUIRED
DATABASE_OPERATION_ERROR
```

Relevant CLI exit categories:

```text
2  → invalid CLI/command input
5  → resource not found
7  → safety/guardrail policy failure
1  → other operational failure
```

Authorization failures map separately to:

```text
4
```

Do not parse human messages to infer automation outcomes.

Use:

- exit codes in shell;
- public error codes/classes in Python.

# Operational decision: cancel or terminate?

Use runtime evidence rather than a fixed rule.

## Prefer cancel when

The operational goal is specifically to stop the current active query while preserving the client session.

Typical shape:

```text
problem = active statement
session itself can remain
```

## Consider terminate when

The operational goal requires disconnecting the backend itself.

Typical shape:

```text
session is the problematic resource
or
cancel is insufficient
or
idle/open transaction must be removed
```

Remember:

```text
terminate
    → client disconnect
    → transaction rollback
```

# Worked scenario: blocking query

Diagnose:

```bash
pydbadmin -c prod query list
pydbadmin -c prod wait list --type Lock
pydbadmin -c prod lock list --waiting-only
pydbadmin -c prod blocking list
```

Suppose PID 4321 is an active client query chosen for cancellation.

Dry-run:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  query cancel 4321
```

Review plan.

Execute:

```bash
pydbadmin \
  -c prod \
  --yes \
  query cancel 4321
```

Then re-inspect:

```bash
pydbadmin -c prod query list
pydbadmin -c prod blocking list
```

# Worked scenario: idle-in-transaction backend

Inspect:

```bash
pydbadmin \
  -c prod \
  session list \
  --state idle_in_transaction
```

Then:

```bash
pydbadmin -c prod transaction list
pydbadmin -c prod lock list
pydbadmin -c prod blocking list
```

Because the backend is idle, `query cancel` is not valid.

If operational policy justifies removing the session, dry-run termination:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  session terminate 4321
```

Then use the exact typed target:

```bash
pydbadmin \
  -c prod \
  session terminate 4321 \
  --confirm-target 'pid:4321'
```

# Worked scenario: PID disappears

You inspect:

```text
PID 5555
```

Before the mutation, the client disconnects.

Then:

```bash
pydbadmin -c staging --yes query cancel 5555
```

can fail with:

```text
ResourceNotFoundError
```

This is not necessarily a framework bug.

It reflects volatile runtime state.

# Worked scenario: background process

Suppose PostgreSQL reports a non-client backend.

A terminate request is blocked by PyDBAdminKit even if a PID exists.

Reason:

```text
Runtime mutation is restricted to client backends.
```

This prevents the generic runtime mutation surface from being used against PostgreSQL background/server processes.

# Troubleshooting

## cancel says target has no active query

The target may have completed its query between inspection and execution, or may be idle.

Re-run:

```bash
pydbadmin -c prod query list
```

## terminate requires typed target in production

Expected.

Production termination is critical.

Use exactly:

```text
pid:<pid>
```

## --yes does not terminate in production

Expected.

`--yes` cannot bypass `type_target`.

## target is not visible

The PID may have exited, visibility may differ, or runtime state changed.

Re-inspect sessions.

## target is a non-client backend

PyDBAdminKit intentionally blocks the signal.

Do not bypass the public mutation service through an internal adapter.

## PostgreSQL did not deliver the signal

PyDBAdminKit raises `DatabaseOperationError`.

The mutation is not reported as successful.

## read-only profile blocks mutation

Expected.

Use a deliberately mutation-capable profile if operational policy permits.

## environment unknown blocks mutation

Expected.

Classify the profile environment before runtime mutation.

# Production considerations

For production:

1. inspect before acting;
2. identify the exact PID and backend type;
3. determine whether the problem is statement-level or session-level;
4. prefer cancellation when session termination is unnecessary;
5. understand open-transaction consequences;
6. dry-run every intervention;
7. preserve operation plans for sensitive incidents;
8. remember production cancel is high-risk;
9. remember production terminate is critical;
10. use exact `pid:<pid>` typed confirmation for termination;
11. re-inspect runtime state after the operation;
12. preserve correlation IDs and audit evidence.

# Best practices

Prefer:

```text
diagnose first
cancel before terminate when sufficient
dry-run
exact PID
client backends only
post-action verification
machine output for automation
audit correlation
```

Avoid:

```text
terminating from stale runtime data
using cancel on idle sessions
using --yes as a universal bypass
signaling PyDBAdminKit itself
signaling PostgreSQL background processes
treating signal submission as success
bypassing RuntimeMutationService
ignoring transaction rollback consequences
```

## Key takeaways

- Query cancellation and session termination are different operations.
- Cancel preserves the client backend; terminate disconnects it.
- Cancel requires an active query.
- Both operations only support client backends.
- PyDBAdminKit blocks signaling its own backend.
- PID values must be positive.
- The operation target is `pid:<pid>`.
- Query cancel is medium-risk by default.
- Session terminate is high-risk by default.
- Production escalates cancel to high and terminate to critical.
- Production terminate requires exact typed-target confirmation.
- `--yes` does not bypass critical confirmation.
- `BackendSignalResult` is validated before success is reported.
- Missing targets raise `ResourceNotFoundError`.
- Failed signal delivery raises `DatabaseOperationError`.
- Runtime state can change between inspection and mutation.
- Part V — Runtime Administration is now complete.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [Sessions, Queries and Transactions](15_SESSIONS_QUERIES_AND_TRANSACTIONS.md)
- [Locks, Waits and Blocking Chains](16_LOCKS_WAITS_AND_BLOCKING_CHAINS.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Backup](18_BACKUP_GUIDE.md).
