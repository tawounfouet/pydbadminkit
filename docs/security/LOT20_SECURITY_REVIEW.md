# LOT-20 / T20-009 — Security Review

## Status

```text
Ticket: T20-009
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Review result: core controls present; dedicated injection/redaction reviews remain open
```

## Review basis

The review uses the project security invariants and qualification rules as its checklist:

```text
INV-SEC-001  No plaintext persisted secret by default.
INV-SEC-002  No secret in logs/output/audit.
INV-SEC-003  Security mutations require explicit intent.
INV-SEC-004  Critical changes require guardrails.
INV-SEC-005  Read-only profiles cannot mutate.
INV-SEC-006  Privilege types are validated.
INV-SEC-007  SQL identifiers use safe composition.
INV-SEC-008  Authorization errors are distinct from unsupported capabilities.
INV-SEC-009  Ownership is distinct from grants.
INV-SEC-010  Security audit is read-only by default.
```

The dedicated T20-010, T20-011 and T20-012 reviews remain responsible for exhaustive SQL
injection, command injection and redaction analysis.

## Control matrix

| Area | Current control | Review |
| --- | --- | --- |
| Persisted credentials | `ConnectionProfile` stores `SecretReference`, not raw password | PASS |
| Runtime secret wrapper | `SecretValue.__str__` / `__repr__` redact | PASS |
| Env secret resolution | explicit `EnvironmentSecretProvider` | PASS |
| CLI password argument | no root plaintext password option | PASS |
| Read-only mutation block | security/runtime/maintenance/restore enforce `read_only` | PASS |
| Unknown environment | sensitive mutations fail closed | PASS |
| Production escalation | mutation risk escalates in production | PASS |
| Critical intent | `TYPE_TARGET` confirmation used for critical plans | PASS |
| Dry-run | mutation services return `OperationPlan` before execution | PASS |
| Audit lifecycle | started/succeeded/failed/blocked events | PASS |
| Audit storage mode | JSONL file forced to mode `0600` | PASS after T20-009 fix |
| SQL identifiers | psycopg `sql.Identifier` used in security mutation adapter | REVIEWED, exhaustive T20-010 pending |
| Privilege keyword | `AccessType` enum feeds controlled SQL keyword | REVIEWED, exhaustive T20-010 pending |
| Native process execution | argument arrays + `shell=False` | REVIEWED, exhaustive T20-011 pending |
| Native-tool password | password passed through `PGPASSWORD`, not argv | PASS |
| Error/audit redaction | DTO boundaries are secret-aware | PARTIAL; exhaustive failure-path review T20-012 |

## Finding SEC-20-009-01 — Existing audit file permissions

### Before review

`os.open(..., 0o600)` guarantees mode `0600` only when the audit file is created.
An existing file with broader permissions keeps its existing mode.

### Risk

A pre-created or accidentally relaxed audit file could remain readable by users outside the
intended owner despite the sink describing itself as restricted-permission.

### Remediation

T20-009 now calls:

```python
os.fchmod(descriptor, 0o600)
```

immediately after opening the audit file.

A regression test starts with a `0644` file and verifies that the sink repairs it to
`0600`.

### Status

```text
CLOSED
```

## Finding SEC-20-009-02 — Redaction is distributed

Audit events and tool-error messages are constructed upstream and the JSONL sink does not
perform a final redaction pass.

This is not treated as closed by T20-009 because changing the redaction boundary without an
inventory could hide useful diagnostics or miss other output paths.

### Status

```text
OPEN → T20-012 redaction review
```

## Finding SEC-20-009-03 — Injection reviews need repository-wide proof

The reviewed security adapter uses safe identifier composition and the process runner uses
`shell=False`, but T20-009 intentionally does not claim repository-wide injection proof
from spot checks.

### Status

```text
OPEN → T20-010 SQL injection review
OPEN → T20-011 command injection review
```

## Security posture after T20-009

The implemented core follows the project's main security architecture:

```text
Credentials are externalized
Authorization remains database-native
Privileges are explicitly modeled
Sensitive mutations are guarded and audited
```

No new feature is introduced by this ticket. The only runtime hardening change repairs
audit-file permissions deterministically.

## Next ticket

```text
T20-010 — SQL injection review
```
