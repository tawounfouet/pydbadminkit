# LOT-21 / T21-005 — Security Qualification

## Decision

```text
Ticket: T21-005
Result: PASS
Basis: LOT-20 hardening reviews + unit regression guards + live PostgreSQL security tests
```

## Security invariants qualified

The release qualification covers the project's core security invariants:

```text
No plaintext persisted secret by default
No secret in logs/output/audit
Security mutations require explicit intent
Critical changes require guardrails
Read-only profiles cannot mutate
Privilege types are validated
SQL identifiers use safe composition
Ownership remains distinct from grants
```

## Credential boundary

Connection profiles persist a `SecretReference`, not a resolved password.

A resolved `SecretValue` may cross only explicit execution boundaries:

- Psycopg connection password parameter;
- `PGPASSWORD` in the child environment for PostgreSQL native tools.

Passwords are excluded from native-tool argv. Machine serialization maps `SecretValue`
to `<redacted>`, and native-tool stderr is redacted before public exception construction.

## Injection qualification

### SQL

The PostgreSQL adapter follows:

```text
runtime value       → bind parameter
database identifier → psycopg.sql.Identifier
SQL keyword         → static fragment / explicit whitelist
```

Hostile-input regression tests cover roles, principals, schema/table/index names,
maintenance targets and restore target database names.

### Native commands

Native PostgreSQL utilities follow:

```text
argv list
shell=False
explicit option/value binding
-- before user-controlled positional archive paths
password outside argv
```

Regression tests cover shell metacharacters and option-looking values.

## Guardrail qualification

Live PostgreSQL mutation tests verify:

- `--dry-run` produces a plan without changing PostgreSQL;
- ordinary guarded mutations require explicit execution intent;
- `--yes` does not bypass typed-target confirmation for critical operations;
- critical superuser creation is blocked without the target confirmation;
- read-only profiles block mutations;
- role/access/membership mutations change PostgreSQL only when authorized by the guardrail;
- started/succeeded audit events are written for executed mutations.

## Authorization/effective-access qualification

Live PostgreSQL tests verify:

- login-role filtering;
- membership graph inspection;
- direct privileges;
- inherited privileges;
- PUBLIC privileges;
- ownership-derived access;
- superuser-derived access;
- ownership inventory.

## Audit qualification

The audit sink repairs existing files to mode `0600`.

Mutation audit records use stable operation names and are regression-tested to exclude
password material.

## Cross-version evidence

Security read and mutation integration tests execute inside the PostgreSQL 14–18 matrix.

The Tier A PostgreSQL 15–18 security path is therefore exercised on every claimed Tier A
server major.

## Release gate

The 1.0 condition:

```text
security review green
```

is satisfied by the current implementation and executable regression suite.

## Next ticket

```text
T21-006 — machine interface qualification
```
