# LOT-20 / T20-012 — Redaction Review

## Status

```text
Ticket: T20-012
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Result: PASS after diagnostic redaction hardening
```

## Secret boundaries reviewed

The runtime secret model is `SecretValue`. Its `str()` and `repr()` representations are
redacted, and raw access is limited to explicit `reveal()` calls at infrastructure or
adapter boundaries.

The repository contains two intentional raw-secret boundaries:

```text
psycopg connection parameter: password
PostgreSQL child environment: PGPASSWORD
```

No raw password is intentionally persisted in configuration, audit records, argv or
machine-readable output.

## Finding REDACT-20-012-01 — native-tool stderr

Before review, `pg_dump`, `pg_restore` and validation failures included a bounded stderr
excerpt in public error messages. PostgreSQL tools normally avoid echoing passwords, but an
external executable, wrapper or unexpected diagnostic could include the resolved password.

T20-012 introduces `redact_secret()` and applies it before stderr normalization,
truncation and public error construction. Regression tests simulate stderr containing the
exact runtime password and verify that only `<redacted>` reaches the public exception.

```text
Status: CLOSED
```

## Finding REDACT-20-012-02 — machine serialization

Previously, `SecretValue` was unsupported by the machine serializer, so direct
serialization failed rather than leaking the secret. This was safe-by-failure but not an
explicit output contract.

The machine serializer now maps every `SecretValue` to:

```text
<redacted>
```

JSON and YAML regression tests assert that the raw value never appears.

```text
Status: CLOSED
```

## Database errors

Psycopg errors are translated to stable public messages. Authentication failures become
`Database authentication failed.`; generic connection and database-operation failures are
also translated without copying raw driver diagnostics.

## Audit path

Mutation services audit public exception messages. With native-tool diagnostics redacted
before exception construction, those messages no longer provide a path for the resolved
password to reach JSONL audit output.

The audit sink itself does not know runtime credentials and therefore remains a persistence
boundary rather than a secret-discovery component.

## Frozen rule

```text
SecretValue may be revealed only at an explicit execution boundary.
Raw secrets must not enter argv, public errors, machine output or audit messages.
External diagnostic text must be redacted before it crosses the adapter boundary.
```

## Next ticket

```text
T20-013 — performance / N+1 review
```
