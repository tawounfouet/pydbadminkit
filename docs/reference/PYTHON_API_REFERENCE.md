# PyDBAdminKit Python API Reference

## Stability boundary

PyDBAdminKit keeps the package root deliberately small:

```python
from pydbadminkit import __version__
```

The stable 1.0 Python API is imported from explicit domain, application, ports, errors and
bootstrap modules. PostgreSQL adapters, SQL query modules, mappers, CLI internals and
infrastructure modules are implementation details.

## Composition root

For most application code, start with `pydbadminkit.bootstrap`.

Stable convenience builders:

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

Example:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service("local", Path("config.toml"))
databases = catalog.list_databases()
```

These non-underscore builders are treated as public 1.0 convenience API.

## Common domain

`pydbadminkit.domain.common`:

```text
CapabilityAvailability
CapabilityStatus
DatabaseEngine
DatabaseObjectRef
DatabaseObjectType
DatabaseVersion
EnvironmentName
OperationName
OperationResult
OperationStatus
QualifiedName
RiskLevel
parse_qualified_name
```

## Connection domain

`pydbadminkit.domain.connection`:

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

Persist `SecretReference`, not resolved secret material. `SecretValue` is an execution-
boundary type and renders redacted in string/machine contexts.

## Catalog domain

`pydbadminkit.domain.catalog`:

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

## Security domain

`pydbadminkit.domain.security`:

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

## Runtime domain

`pydbadminkit.domain.runtime`:

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

## Operations domain

`pydbadminkit.domain.operations`:

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

## Monitoring domain

`pydbadminkit.domain.monitoring`:

```text
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
```

The following exported monitoring registry/naming symbols are also retained as public for
the 1.0 line:

```text
CORE_METRIC_DESCRIPTORS
CORE_METRIC_REGISTRY
DEFAULT_EXPORT_LABELS
FORBIDDEN_EXPORT_LABELS
INTERNAL_METRIC_PREFIX
PROMETHEUS_METRIC_PREFIX
internal_metric_name
prometheus_metric_name
validate_metric_name
```

This explicitly resolves the LOT-20 question about whether those exports should be
internalized: they remain public for 1.0.

## Application services

Stable service classes:

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
  RuntimeService
  RuntimeMutationService

pydbadminkit.application.security
  SecurityService
  SecurityMutationService

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

Application services depend on ports/domain contracts rather than PostgreSQL implementation
classes.

## Extension ports

`pydbadminkit.ports` exposes the stable adapter boundary:

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

For 1.0 these protocols are treated as public extension contracts. Signature-breaking
changes therefore require the migration/deprecation policy rather than silent replacement.

## Errors

`pydbadminkit.errors` exposes `PyDBAdminError`, `ErrorCode` and the typed error
hierarchy.

Public errors:

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

Machine error codes are frozen separately in `docs/contracts/ERROR_CODE_CONTRACT.md`.

## Non-public implementation surface

No 1.0 compatibility guarantee is attached to:

```text
pydbadminkit.adapters.*
pydbadminkit.infrastructure.*
pydbadminkit.cli.*
underscore-prefixed bootstrap helpers
PostgreSQL SQL/query modules
PostgreSQL mapper modules
non-exported module members
```

Importing these modules is possible in Python but does not promote them into the public
contract.

## 1.0 API decisions

The pre-1.0 inventory questions are resolved as follows:

```text
package root             keep intentionally narrow
bootstrap builders       public/stable
ports                    public extension contracts
monitoring constants     public/stable
typed errors/ErrorCode   public/stable
adapters/infrastructure  internal
```

The exported `__all__` sets are protected by
`tests/unit/test_public_api_inventory.py`.

## Compatibility

Removal/rename of an exported symbol, incompatible constructor/signature change, port
signature break or semantic change to a stable public enum/error code is a compatibility
event and follows the 1.0 migration/deprecation policy.
