# LOT-20 / T20-004 — Error-Code Freeze

## Status

```text
Ticket: T20-004
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Contract: frozen for the route to 1.0
```

PyDBAdminKit exposes machine-readable error identifiers through:

```python
from pydbadminkit.errors import ErrorCode
```

The enum value is the wire value. Names and values are intentionally identical uppercase
snake-case strings.

## Frozen codes

```text
CONFIGURATION_ERROR
PROFILE_NOT_FOUND
SECRET_RESOLUTION_ERROR
CONNECTION_ERROR
CONNECTION_TIMEOUT
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
DATABASE_OPERATION_ERROR
RESOURCE_NOT_FOUND
RESOURCE_ALREADY_EXISTS
CAPABILITY_UNAVAILABLE
VALIDATION_ERROR
SAFETY_POLICY_ERROR
POLICY_DENIED
CONFIRMATION_REQUIRED
AUDIT_UNAVAILABLE
BACKUP_ERROR
BACKUP_VALIDATION_ERROR
RESTORE_ERROR
RESTORE_VALIDATION_ERROR
MAINTENANCE_ERROR
CHECKSUM_MISMATCH
FILE_COLLISION
UNSAFE_PATH
EXTERNAL_TOOL_ERROR
TOOL_NOT_FOUND
TOOL_VERSION_MISMATCH
TOOL_EXECUTION_ERROR
OPERATION_TIMEOUT
INTERNAL_ERROR
```

## Compatibility rules

From this freeze onward:

- an existing code must not be removed before a major-version compatibility break;
- an existing wire value must not be renamed or repurposed;
- exception classes may become more specific, but must use a documented `ErrorCode`;
- new codes are additive and require documentation plus a contract-test update;
- human-readable error messages are not substitutes for machine codes;
- consumers should branch on `ErrorCode`, not parse exception messages.

## Hierarchy behavior

`PyDBAdminError` is the root operational exception and defaults to `INTERNAL_ERROR`.
Specific public subclasses override `code` where a more precise machine classification
exists.

The error-code contract is separate from the CLI process exit-code contract. Multiple
error codes may intentionally map to the same process exit code.

## Automated drift guard

`tests/unit/test_error_code_contract.py` freezes the complete ordered value set and verifies
that every value is stable uppercase snake case.

T20-001 also verifies that `ErrorCode` remains exported from `pydbadminkit.errors`.

## Next ticket

```text
T20-005 — exit-code freeze
```
