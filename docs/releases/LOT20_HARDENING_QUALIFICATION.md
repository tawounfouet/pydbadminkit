# LOT-20 — Hardening Qualification

## Decision

```text
LOT-20: COMPLETE
Baseline: 0.6.0
Next: LOT-21 — Qualification / Documentation
```

LOT-20 closes the hardening implementation phase before the 1.0 release-candidate
qualification.

## Tickets

```text
T20-001 public API inventory             PASS
T20-002 CLI contract inventory           PASS
T20-003 JSON contract inventory          PASS
T20-004 error-code freeze                PASS
T20-005 exit-code freeze                 PASS
T20-006 config contract freeze           PASS
T20-007 capability-name freeze           PASS
T20-008 operation-name freeze            PASS
T20-009 security review                  PASS
T20-010 SQL injection review             PASS
T20-011 command injection review         PASS
T20-012 redaction review                 PASS
T20-013 performance/N+1 review           PASS
T20-014 PostgreSQL matrix                PASS
T20-015 package metadata review          PASS
```

## Security hardening evidence

The lot produced concrete runtime hardening, not documentation only:

- existing audit files are forced back to mode `0600`;
- PostgreSQL identifiers remain `sql.Identifier` values;
- SQL keywords selected from domain enums use explicit adapter whitelists;
- native utilities run with argv arrays and `shell=False`;
- user-controlled positional archive paths follow `--`;
- backup database names are bound to `--dbname`;
- passwords remain outside argv;
- native-tool stderr is redacted before becoming a public error;
- `SecretValue` serializes to `<redacted>` in machine output.

## Performance evidence

Catalog, security, runtime and monitoring reads remain set-oriented.

Documented fixed query budgets include:

```text
table describe   3
view describe    3
index describe   2
role describe    2
monitor metrics  2 port calls
```

The monitoring regression test proves that 100 database-size rows still require one
connection-statistics call and one database-size call.

## PostgreSQL matrix evidence

The integration workflow now qualifies the same 44-test PostgreSQL suite on every current
matrix member:

```text
PostgreSQL 14  44 passed
PostgreSQL 15  44 passed
PostgreSQL 16  44 passed
PostgreSQL 17  44 passed
PostgreSQL 18  44 passed
```

PostgreSQL 15–18 are the Tier A target line. PostgreSQL 14 remains Transitional during the
2026 qualification window.

## Unit qualification

```text
419 passed
44 deselected
coverage 86.15%
required coverage 85.0%
```

## Other gates

```text
Ruff format       PASS
Ruff check        PASS
Mypy strict       PASS
Package build     PASS
Twine check       PASS
Wheel install     PASS
CLI smoke         PASS
```

## Known policy item

The repository currently has no `LICENSE` file or declared package license.

This is not silently resolved by LOT-20 because choosing MIT, Apache, proprietary or another
license is a legal/product-owner decision. LOT-21 / the 1.0 publication gate must record the
chosen policy and synchronize package metadata accordingly.

## Promotion

No new feature work is required to close LOT-20.

The repository may now enter:

```text
LOT-21
Qualification / Documentation
        ↓
1.0 release-candidate gate
        ↓
1.0.0
```
