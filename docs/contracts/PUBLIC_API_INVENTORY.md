# LOT-20 / T20-001 — Public Python API Inventory

## Status

```text
Ticket: T20-001
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Purpose: inventory before the 1.0 public API freeze
```

This document records the intentionally importable Python surface at the start of LOT-20.
It is an inventory baseline, not permission to expose adapter or infrastructure internals.

## Public package root

```python
from pydbadminkit import __version__
```

The package root deliberately remains small. Public domain, application and port contracts
are imported from their explicit subpackages.

## Domain API

### `pydbadminkit.domain.common`

```text
CapabilityAvailability
CapabilityStatus
DatabaseEngine
DatabaseObjectRef
DatabaseObjectType
DatabaseVersion
EnvironmentName
OperationResult
OperationStatus
QualifiedName
RiskLevel
parse_qualified_name
```

### `pydbadminkit.domain.connection`

```text
ConnectionProfile
ConnectionProfileName
ConnectionTestResult
ResolvedConnectionConfig
SSLConfig
SSLMode
SecretReference
SecretValue
TimeoutConfig
```

### `pydbadminkit.domain.catalog`

```text
ColumnInfo
ConstraintInfo
ConstraintType
DatabaseInfo
IndexDescription
IndexInfo
SchemaInfo
ServerInfo
TableDescription
TableInfo
TableKind
ViewDescription
ViewInfo
ViewKind
```

### `pydbadminkit.domain.security`

```text
AccessSource
AccessType
AlterRoleCommand
CreateRoleCommand
DirectAccess
EffectiveAccess
MembershipCommand
OwnershipInfo
RelationAccessCommand
RoleDescription
RoleInfo
RoleMembership
```

### `pydbadminkit.domain.runtime`

```text
BackendSignalResult
BlockingRelation
CancelQueryCommand
LockInfo
QueryInfo
SessionInfo
SessionState
TerminateSessionCommand
TransactionInfo
WaitInfo
```

### `pydbadminkit.domain.operations`

```text
AnalyzeCommand
Backup
BackupArtifactInfo
BackupFormat
BackupMetadata
BackupPaths
BackupToolResult
BackupValidation
CreateBackupCommand
ExternalTool
MaintenanceOperation
MaintenanceOperationType
MaintenanceProgress
ProcessResult
ReindexCommand
ReindexTargetType
RestoreBackupCommand
RestoreOperation
RestoreValidation
VacuumCommand
```

### `pydbadminkit.domain.monitoring`

```text
CORE_METRIC_DESCRIPTORS
CORE_METRIC_REGISTRY
DEFAULT_EXPORT_LABELS
FORBIDDEN_EXPORT_LABELS
INTERNAL_METRIC_PREFIX
PROMETHEUS_METRIC_PREFIX
ConnectionStatistics
DatabaseSizeMetric
HealthCheckCategory
HealthCheckEvidence
HealthCheckResult
HealthReport
HealthStatus
IndexStatistics
Metric
MetricCardinalityPolicy
MetricDescriptor
MetricType
MonitoringSnapshot
TableSizeMetric
TableStatistics
Threshold
internal_metric_name
prometheus_metric_name
validate_metric_name
```

## Application API

```text
pydbadminkit.application.capability
  CapabilityService

pydbadminkit.application.catalog
  CatalogService

pydbadminkit.application.connection
  ConnectionConfigResolver
  ConnectionService

pydbadminkit.application.operations
  BackupService
  BackupValidationService
  MaintenanceService
  RestoreService

pydbadminkit.application.runtime
  RuntimeMutationService
  RuntimeService

pydbadminkit.application.security
  SecurityMutationService
  SecurityService

pydbadminkit.application.server
  ServerService

pydbadminkit.application.monitoring
  HealthCheckConfig
  HealthCheckRunner
  HealthService
  MetricExportService
  MonitoringService
  MonitoringSnapshotService
```

## Ports / extension contracts

`pydbadminkit.ports` exposes:

```text
AuditPort
BackupFileStorePort
BackupPort
CapabilityPort
CatalogPort
ConfigRepositoryPort
ConnectionTesterPort
MaintenancePort
MetricExporterPort
MonitoringPort
ProcessRunnerPort
RestoreDatabasePort
RestorePort
RuntimeMutationPort
RuntimePort
SecretProviderPort
SecurityMutationPort
SecurityPort
ServerPort
ToolResolverPort
```

These protocols form the adapter boundary. Their signatures require separate compatibility
review before 1.0.

## Error API

`pydbadminkit.errors` exposes the complete typed error hierarchy:

```text
AuditUnavailableError
AuthenticationError
AuthorizationError
BackupError
BackupValidationError
CapabilityNotAvailableError
ChecksumMismatchError
ConfigurationError
ConfirmationRequiredError
DatabaseConnectionError
DatabaseConnectionTimeoutError
DatabaseOperationError
ExternalToolError
FileCollisionError
InternalError
MaintenanceError
OperationTimeoutError
PolicyDeniedError
ProfileNotFoundError
PyDBAdminError
ResourceAlreadyExistsError
ResourceNotFoundError
RestoreError
RestoreValidationError
SafetyPolicyError
SecretResolutionError
ToolExecutionError
ToolNotFoundError
ToolVersionMismatchError
UnsafePathError
ValidationError
```

Error codes themselves are reviewed separately by T20-004.

## Bootstrap convenience API

The following non-underscore functions in `pydbadminkit.bootstrap` are the current
composition-root convenience surface:

```text
resolve_connection
build_connection_service
build_server_service
build_catalog_service
build_backup_service
build_backup_validation_service
build_restore_service
build_maintenance_service
build_health_service
build_monitoring_snapshot_service
build_monitoring_service
build_runtime_service
build_runtime_mutation_service
build_security_service
build_security_mutation_service
build_capability_service
```

## Explicitly non-public

The inventory does **not** make these implementation packages stable API:

```text
pydbadminkit.adapters.*
pydbadminkit.infrastructure.*
pydbadminkit.cli.*
module members not exported through a package __all__
underscore-prefixed bootstrap helpers
PostgreSQL SQL/query modules
PostgreSQL mapper modules
```

Applications may technically import those modules, but 1.0 compatibility guarantees should
not be inferred from that possibility.

## Drift guard

`tests/unit/test_public_api_inventory.py` records the `__all__` sets for the public
package surfaces above. A change to one of those sets must therefore be deliberate and
reviewed as an API-contract change.

## Findings for follow-up

T20-001 identifies the following review points for subsequent hardening tickets:

1. the root package exports only `__version__`; decide whether 1.0 should preserve that
   intentionally narrow root;
2. port signatures need compatibility review alongside the public services that consume
   them;
3. bootstrap functions are de facto user-facing convenience APIs and need an explicit 1.0
   stability decision;
4. constants in `domain.monitoring` are currently exported and therefore need an explicit
   keep/internalize decision before the API freeze;
5. errors are publicly exported, while their machine codes are handled separately by
   T20-004.

## Next ticket

```text
T20-002 — CLI contract inventory
```
