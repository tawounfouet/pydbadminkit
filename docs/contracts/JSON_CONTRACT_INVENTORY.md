# LOT-20 / T20-003 — JSON Contract Inventory

## Status

```text
Ticket: T20-003
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Purpose: inventory the machine-readable JSON surface before the 1.0 freeze
```

PyDBAdminKit does not maintain a second JSON-only DTO hierarchy. Machine output is produced
from public immutable domain/application models by `pydbadminkit.output.serialization`.

This document inventories that contract and establishes the baseline for the later 1.0
machine-interface freeze.

## Serialization rules

`to_machine_value()` applies the following stable rules:

```text
None                 → null
bool/int/float/str   → same primitive
datetime/date        → ISO-8601 string
StrEnum              → enum value
RiskLevel            → lowercase label
dataclass            → object using dataclass field declaration order
tuple/list           → JSON array
Mapping[str, ...]    → JSON object
```

Mappings with non-string keys and unsupported Python values are rejected instead of being
silently stringified.

`render_json()` uses:

```text
UTF-8/unescaped Unicode
2-space indentation
field order preserved
no key sorting
```

## CLI payload families

| CLI surface | JSON payload |
| --- | --- |
| `connection test` | `ConnectionTestResult` object |
| `server info` | `ServerInfo` object |
| catalog `list` commands | array of catalog read models |
| catalog `describe` commands | one catalog description/read model |
| `role list` | array of `RoleInfo` |
| `role describe` | `RoleDescription` |
| `access list` | array of `DirectAccess` |
| `effective-access list` | array of `EffectiveAccess` |
| `ownership list` | array of `OwnershipInfo` |
| runtime `list` commands | arrays of runtime read models |
| `capability list` | array of `CapabilityStatus` |
| `capability get` | one `CapabilityStatus` |
| `health check` | `HealthReport` |
| `backup create` | `Backup` when executed; operation plan in dry-run |
| `backup validate` | `BackupValidation` |
| `backup restore` | `RestoreOperation` when executed; operation plan in dry-run |
| guarded mutation commands | operation result/plan payload emitted by the mutation pipeline |
| maintenance progress | arrays of `MaintenanceProgress` |

## Representative frozen shapes

### Connection test

```json
{
  "engine": "postgresql",
  "version": {
    "major": 18,
    "minor": null,
    "patch": null,
    "raw": null
  },
  "current_database": "analytics",
  "current_user": "app",
  "latency_ms": 12.5
}
```

### Database list item

```json
{
  "name": "analytics",
  "owner": "app",
  "encoding": "UTF8",
  "collation": null,
  "allow_connections": true,
  "connection_limit": -1,
  "size_bytes": 1024
}
```

A list command wraps items like this in a JSON array. Empty results are `[]`, not
`null`.

### Generic operation result

```json
{
  "operation": "example",
  "status": "succeeded",
  "changed": true,
  "message": "completed",
  "metadata": {
    "risk": "low"
  }
}
```

### Health report

The stable health report contract is already frozen by the 0.6 qualification:

```text
overall_status
checks
captured_at
```

Each check keeps:

```text
name
status
message
details
captured_at
evidence
```

## Nullability and omission

Current serialization is structural: dataclass fields are **not omitted** merely because
their value is `None`. They are serialized as `null`.

This is important for 1.0 compatibility. Changing from explicit `null` to omitted keys
would be a machine-contract change.

## Field ordering

JSON object fields preserve dataclass declaration order. Although consumers should normally
parse by key rather than position, deterministic order is intentionally retained for:

- reproducible CLI output;
- snapshot testing;
- diffs;
- operational logs and artifacts.

## Secrets and sensitive data

Machine serialization does not itself perform redaction. Secret safety must therefore be
guaranteed by the public DTOs and error/mutation boundaries before values reach the
serializer.

The dedicated redaction review remains T20-012. Query/runtime models may intentionally
contain query text for runtime inspection; this is operational data, not credential data,
and requires separate security review rather than silent serializer mutation.

## Compatibility policy for hardening

Before 1.0, the following are machine-contract changes requiring explicit review:

- removing or renaming a JSON field;
- changing a field type or enum wire value;
- changing `null` into field omission or vice versa;
- changing a list payload into an object payload;
- changing date/time encoding;
- changing `RiskLevel` labels;
- changing deterministic field order;
- adding secrets or credential material to a serialized public model.

Additive fields must also be reviewed because strict downstream consumers may reject them.

## Automated drift guard

`tests/unit/test_json_contract_inventory.py` freezes representative contracts for:

- scalar and enum conversion;
- connection result field order and nested version shape;
- list payload behavior;
- explicit nulls;
- generic operation-result shape;
- JSON rendering order.

The dedicated health contract remains covered by
`tests/unit/test_monitoring_release_contract.py`.

## Next ticket

```text
T20-004 — error-code freeze
```
