# LOT-21 / T21-008 — README Final Review

## Decision

```text
Ticket: T21-008
Result: PASS for 1.0 RC preparation
```

The root README now provides, before the detailed feature catalogue:

- supported Python range;
- PostgreSQL Tier A / Transitional status;
- source-checkout installation;
- minimal secret-referenced TOML profile;
- first connection/catalog commands;
- read-only-first guidance;
- explicit 1.0 qualification status;
- clear statement that the installed version remains 0.6.0 until RC promotion.

The existing detailed sections continue to document Monitoring, Object Explorer, Security,
Runtime, Backup/Restore/Maintenance, local PostgreSQL setup, Python API/notebooks,
architecture and the roadmap.

The release version shown in the README must be updated by T21-014 and T21-015 during the
actual RC/stable promotions rather than being pre-announced here.
