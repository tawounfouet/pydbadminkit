# PyDBAdminKit 1.0 — Python API Fundamentals

## Objective

Use PyDBAdminKit as a Python library without depending on implementation internals.

This guide explains the stable 1.0 Python surface:

```text
pydbadminkit.bootstrap
pydbadminkit.domain.*
pydbadminkit.application.*
pydbadminkit.ports
pydbadminkit.errors
```

and the modules that are intentionally **outside** the 1.0 compatibility boundary:

```text
pydbadminkit.adapters.*
pydbadminkit.infrastructure.*
pydbadminkit.cli.*
underscore-prefixed bootstrap helpers
PostgreSQL SQL/query internals
PostgreSQL mapper internals
non-exported module members
```

For the normative API inventory, see
[`PYTHON_API_REFERENCE.md`](../reference/PYTHON_API_REFERENCE.md).

## Prerequisites

Before continuing, you should understand:

- connection profiles;
- secret references;
- the CLI concepts from the previous guides;
- basic Python imports and virtual environments.

A typical application starts with:

```python
from pathlib import Path
```

and then imports public PyDBAdminKit builders or domain types.

## The package root is deliberately small

The root package exposes:

```python
from pydbadminkit import __version__
```

Example:

```python
from pydbadminkit import __version__

print(__version__)
```

The root package intentionally does **not** re-export every service, domain type and adapter.

This keeps the public namespace explicit.

Use explicit imports such as:

```python
from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.domain.catalog import DatabaseInfo
from pydbadminkit.errors import PyDBAdminError
```

rather than expecting a large flat root API.

## Recommended starting point: bootstrap

For most consumers, the simplest 1.0 entry point is:

```text
pydbadminkit.bootstrap
```

The bootstrap module is the public composition root.

It wires together:

```text
configuration
    ↓
secret resolution
    ↓
application service
    ↓
PostgreSQL adapter
    ↓
infrastructure
```

without requiring application code to import those lower-level implementation packages directly.

## Stable bootstrap builders

The stable 1.0 convenience builders are:

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

These non-underscore functions are part of the 1.0 public convenience API.

## Resolve a connection profile

Use:

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

resolved = resolve_connection(
    "local",
    Path("config.toml"),
)

print(resolved.name)
print(resolved.host)
print(resolved.database)
print(resolved.username)
print(resolved.environment)
print(resolved.read_only)
```

The returned object is:

```text
ResolvedConnectionConfig
```

If a password was resolved, it is stored as `SecretValue`.

Printing it remains redacted:

```python
print(resolved.password)
```

Expected representation:

```text
<redacted>
```

## Connection service

Build the public connection service with:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_connection_service

service = build_connection_service(Path("config.toml"))

result = service.test("local")

print(result.engine)
print(result.version)
print(result.current_database)
print(result.current_user)
print(result.latency_ms)
```

The method:

```text
ConnectionService.test(profile_name)
```

resolves the profile and tests connectivity.

## Server service

Build a server inspection service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_server_service

server = build_server_service(
    "local",
    Path("config.toml"),
)

info = server.get_info()

print(info.engine)
print(info.version)
print(info.current_database)
print(info.current_user)
```

This is the Python equivalent of:

```bash
pydbadmin -c local server info
```

## Catalog service

The catalog service is a good first API for experimentation.

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service(
    "local",
    Path("config.toml"),
)

databases = catalog.list_databases()

for database in databases:
    print(database.name)
```

The service returns public domain models rather than dictionaries assembled by the CLI.

That means you work with typed objects such as:

```text
DatabaseInfo
SchemaInfo
TableInfo
TableDescription
ViewInfo
ViewDescription
IndexInfo
IndexDescription
```

## Runtime inspection

Use:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_runtime_service

runtime = build_runtime_service(
    "prod",
    Path("config.toml"),
)

sessions = runtime.list_sessions()

for session in sessions:
    print(session.pid, session.username, session.state)
```

Available read-only runtime methods include:

```text
list_sessions
list_queries
list_transactions
list_waits
list_locks
list_blocking
```

Example with filters:

```python
sessions = runtime.list_sessions(
    database="app",
    username="app_user",
    include_self=False,
)
```

The service returns tuples of typed public domain models.

## Security inspection

Build a read-only security service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_service

security = build_security_service(
    "prod",
    Path("config.toml"),
)

roles = security.list_roles(
    include_system=False,
    login_only=True,
)

for role in roles:
    print(role.name, role.can_login)
```

The service also exposes:

```text
describe_role
list_role_memberships
list_direct_access
list_effective_access
list_ownership
```

Example:

```python
effective = security.list_effective_access(
    "app_user",
    schema="public",
)

for entry in effective:
    print(entry.object.name, entry.access_type, entry.sources)
```

## Capability discovery

Capability discovery does not require a selected connection profile.

```python
from pydbadminkit.bootstrap import build_capability_service

capabilities = build_capability_service()

for capability in capabilities.list():
    print(capability.name, capability.availability)
```

Fetch one capability:

```python
capability = build_capability_service().get("runtime.cancel-query")

print(capability.name)
print(capability.available)
print(capability.reason)
```

Use capability discovery instead of hard-coding assumptions where possible.

## Health service

Build the default point-in-time health suite:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_health_service

health = build_health_service(
    "prod",
    Path("config.toml"),
)

report = health.check()

print(report.overall_status)
print(report.captured_at)

for check in report.checks:
    print(check.name, check.status, check.message)
```

The public health facade method is:

```text
HealthService.check()
```

## Monitoring service

Build monitoring access with:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_monitoring_service

monitoring = build_monitoring_service(
    "prod",
    Path("config.toml"),
)
```

The monitoring APIs expose point-in-time PostgreSQL operational metrics through public monitoring
domain models.

For a composed monitoring plus health snapshot, use:

```python
from pydbadminkit.bootstrap import build_monitoring_snapshot_service

snapshot_service = build_monitoring_snapshot_service(
    "prod",
    Path("config.toml"),
)
```

Detailed monitoring usage is covered in guides 21–23.

## Backup validation without a connection

Backup validation has a dedicated builder that does not require a profile:

```python
from pydbadminkit.bootstrap import build_backup_validation_service

validator = build_backup_validation_service()
```

This is intentionally separate from builders that require database connectivity.

Operational examples are covered in the backup guide.

## Read-only versus mutation services

PyDBAdminKit separates several inspection and mutation services.

Examples:

```text
RuntimeService
RuntimeMutationService

SecurityService
SecurityMutationService
```

The read-only services expose inspection methods.

Mutation services participate in:

```text
operation planning
safety policy
confirmation semantics
dry-run
audit
execution
```

Do not treat a mutation service as a direct adapter around arbitrary SQL.

## Mutation builders

Mutation-oriented builders include:

```text
build_runtime_mutation_service
build_security_mutation_service
build_restore_service
build_maintenance_service
build_backup_service
```

These builders wire the configured profile together with:

- PostgreSQL adapters;
- safety-relevant connection metadata;
- audit infrastructure where applicable;
- native PostgreSQL tools where required.

Detailed mutation examples are intentionally deferred to the relevant operational guides so that
the complete safety contract can be shown alongside the API.

## Domain objects

The public domain packages are the typed vocabulary of PyDBAdminKit.

Main areas:

```text
pydbadminkit.domain.common
pydbadminkit.domain.connection
pydbadminkit.domain.catalog
pydbadminkit.domain.security
pydbadminkit.domain.runtime
pydbadminkit.domain.operations
pydbadminkit.domain.monitoring
```

Use these types when:

- consuming service results;
- constructing public commands;
- validating values;
- typing your own integration code.

## Common domain

Representative public common types include:

```text
DatabaseEngine
EnvironmentName
DatabaseVersion
DatabaseObjectRef
DatabaseObjectType
QualifiedName
OperationName
OperationResult
OperationStatus
RiskLevel
CapabilityStatus
```

Example:

```python
from pydbadminkit.domain.common import EnvironmentName

if resolved.environment is EnvironmentName.PRODUCTION:
    print("production target")
```

## Connection domain

Representative types:

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

These types separate persisted connection intent from runtime-resolved credentials.

## Catalog domain

Representative types:

```text
DatabaseInfo
SchemaInfo
TableInfo
TableDescription
ViewInfo
ViewDescription
IndexInfo
IndexDescription
ColumnInfo
ConstraintInfo
```

These are the return types used by the object explorer services.

## Security domain

Representative public command and result types include:

```text
CreateRoleCommand
AlterRoleCommand
MembershipCommand
RelationAccessCommand
RoleInfo
RoleDescription
RoleMembership
DirectAccess
EffectiveAccess
OwnershipInfo
AccessType
AccessSource
```

These typed command objects are used by mutation services rather than passing unstructured
dictionaries through the application boundary.

## Runtime domain

Representative types:

```text
SessionInfo
QueryInfo
TransactionInfo
WaitInfo
LockInfo
BlockingRelation
SessionState
CancelQueryCommand
TerminateSessionCommand
BackendSignalResult
```

## Operations domain

Representative types:

```text
CreateBackupCommand
RestoreBackupCommand
VacuumCommand
AnalyzeCommand
ReindexCommand
Backup
BackupValidation
RestoreOperation
MaintenanceOperation
MaintenanceProgress
```

These are used by backup, restore and maintenance services.

## Monitoring domain

Representative public monitoring types include:

```text
HealthReport
HealthCheckResult
HealthStatus
Threshold
MonitoringSnapshot
Metric
MetricDescriptor
ConnectionStatistics
DatabaseSizeMetric
TableStatistics
IndexStatistics
```

The monitoring package also exports several naming/registry constants as stable 1.0 API.

## Application services

The application layer is the main behavior boundary.

Stable service classes include:

```text
CapabilityService
CatalogService
ConnectionConfigResolver
ConnectionService
BackupService
BackupValidationService
MaintenanceService
RestoreService
RuntimeService
RuntimeMutationService
SecurityService
SecurityMutationService
ServerService
HealthCheckConfig
HealthCheckRunner
HealthService
MetricExportService
MonitoringService
MonitoringSnapshotService
```

These services depend on public ports and domain contracts rather than directly on PostgreSQL SQL
modules.

## Ports are public extension contracts

PyDBAdminKit 1.0 exposes its ports as public protocols.

Examples:

```text
CatalogPort
ConfigRepositoryPort
ConnectionTesterPort
RuntimePort
RuntimeMutationPort
SecurityPort
SecurityMutationPort
MonitoringPort
SecretProviderPort
AuditPort
BackupPort
RestorePort
MaintenancePort
MetricExporterPort
ProcessRunnerPort
ToolResolverPort
```

Ports describe what the application layer needs from adapters or infrastructure.

This makes it possible to provide alternate implementations in advanced integrations.

## Why ports matter

Instead of application code depending on a concrete PostgreSQL adapter:

```text
application service
    ↓
Port protocol
    ↓
adapter implementation
```

This preserves the architectural boundary.

For example:

```text
CatalogService
    ↓
CatalogPort
    ↓
PostgreSQLCatalogAdapter
```

Consumers that only need the standard PostgreSQL implementation should normally use the bootstrap
builders and not instantiate adapters manually.

## Custom extension example

Suppose you want to test a service with your own fake port.

Conceptually:

```python
from pydbadminkit.application.catalog import CatalogService
from pydbadminkit.domain.catalog import DatabaseInfo

class FakeCatalogPort:
    def list_databases(self):
        return (
            DatabaseInfo(name="analytics"),
            DatabaseInfo(name="postgres"),
        )

    # Implement the remaining CatalogPort methods required by your use case.

service = CatalogService(FakeCatalogPort())
```

For production custom adapters, implement the complete relevant port contract and preserve the
public semantics.

## Typed errors

The public error root is:

```python
from pydbadminkit.errors import PyDBAdminError
```

Typical integration pattern:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.errors import PyDBAdminError

try:
    catalog = build_catalog_service("prod", Path("config.toml"))
    databases = catalog.list_databases()
except PyDBAdminError as exc:
    print(exc.code)
    raise
```

For finer behavior, catch specific typed errors.

## Specific error example

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection
from pydbadminkit.errors import ProfileNotFoundError, SecretResolutionError

try:
    config = resolve_connection("prod", Path("config.toml"))
except ProfileNotFoundError:
    print("profile does not exist")
except SecretResolutionError:
    print("secret could not be resolved")
```

Do not parse human-readable exception messages to classify failures.

Use the typed hierarchy and `ErrorCode`.

## ErrorCode

Import:

```python
from pydbadminkit.errors import ErrorCode
```

The enum values are stable machine identifiers.

Example:

```python
from pydbadminkit.errors import PyDBAdminError

try:
    ...
except PyDBAdminError as exc:
    print(exc.code.value)
```

Machine consumers should branch on the stable code rather than free-form message text.

## Public versus internal imports

Good:

```python
from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.domain.catalog import DatabaseInfo
from pydbadminkit.application.catalog import CatalogService
from pydbadminkit.ports import CatalogPort
from pydbadminkit.errors import PyDBAdminError
```

Avoid building application code around:

```python
from pydbadminkit.adapters.postgresql import PostgreSQLCatalogAdapter
from pydbadminkit.infrastructure.config import TomlConnectionProfileRepository
from pydbadminkit.cli.context import CLIContext
```

Those imports may work technically, but they are outside the 1.0 compatibility guarantee.

## Why internal imports are risky

Implementation packages may change due to:

- PostgreSQL adapter refactoring;
- infrastructure replacement;
- SQL organization changes;
- mapper reorganization;
- CLI implementation changes;
- composition-root changes.

A technically importable module is not automatically a public API.

The public boundary is defined by the documented exports and 1.0 inventory.

## Underscore bootstrap helpers are internal

For example:

```text
_build_connection_resolver
```

exists inside `pydbadminkit.bootstrap`, but its underscore prefix explicitly keeps it outside
the public 1.0 convenience API.

Use:

```python
resolve_connection(...)
```

or:

```python
build_connection_service(...)
```

instead.

## Public API and machine output are different concerns

The Python API returns typed models.

The CLI machine interface serializes those models.

For example:

```python
databases = catalog.list_databases()
```

returns Python objects.

Whereas:

```bash
pydbadmin -c local --output json database list
```

returns JSON serialization of those public models.

Do not force Python applications to parse CLI JSON when they can call the Python API directly.

## Python application pattern

A clean application structure can be:

```text
your_app/
├── config.py
├── database_admin.py
└── main.py
```

`database_admin.py`:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service, build_health_service

def inspect_database(profile: str, config_path: Path) -> None:
    catalog = build_catalog_service(profile, config_path)
    health = build_health_service(profile, config_path)

    databases = catalog.list_databases()
    report = health.check()

    for database in databases:
        print(database.name)

    print(report.overall_status)
```

The application remains dependent on the public composition root and public models.

## Notebook pattern

For experimentation:

```python
from pathlib import Path

from pydbadminkit.bootstrap import (
    build_catalog_service,
    build_runtime_service,
    build_server_service,
)

CONFIG = Path("config.toml")
PROFILE = "local"

server = build_server_service(PROFILE, CONFIG)
catalog = build_catalog_service(PROFILE, CONFIG)
runtime = build_runtime_service(PROFILE, CONFIG)

server.get_info()
catalog.list_databases()
runtime.list_sessions()
```

This is preferable to manually wiring PostgreSQL adapters inside notebook cells.

## Service lifetime

Bootstrap builders construct service instances around the selected profile.

For simple scripts and notebooks, creating the service when needed is appropriate.

For larger applications, keep composition centralized rather than calling bootstrap functions from
every low-level function.

For example:

```python
class DatabaseAdmin:
    def __init__(self, catalog, runtime):
        self.catalog = catalog
        self.runtime = runtime
```

and create those dependencies once in your application composition layer.

## Configuration path

Most profile-based builders accept:

```text
profile_name
config_path
```

Example:

```python
catalog = build_catalog_service(
    "prod",
    Path("/etc/pydbadminkit/config.toml"),
)
```

If `config_path` is omitted, the default platform-specific PyDBAdminKit config path is used.

Production applications usually benefit from making the path explicit.

## Secrets in Python

The resolved configuration may contain:

```text
SecretValue
```

Do not:

```python
print(resolved.password.reveal())
```

or store that raw value in logs, notebook output or custom DTOs.

The explicit raw-secret boundary exists for execution infrastructure.

## Read-only inspection first

For unfamiliar or production environments, start with read-only services:

```text
build_server_service
build_catalog_service
build_runtime_service
build_security_service
build_health_service
build_monitoring_service
```

Use mutation builders only when the workflow intentionally performs guarded changes.

## Dry-run in Python

The CLI provides a convenient `--dry-run` switch.

In Python, mutation services use public safety-domain inputs and operation-plan semantics rather
than CLI flags.

Detailed examples are covered in the mutation/safety guides.

Do not bypass service planning by calling internal adapters directly merely to avoid the public
safety model.

## Compatibility expectations

For the 1.0 public Python API, compatibility-sensitive changes include:

- removing an exported public symbol;
- renaming an exported public symbol;
- incompatible constructor/signature changes;
- port signature breaks;
- semantic changes to stable enums;
- semantic changes to typed errors;
- changing stable bootstrap builder contracts.

Such changes require the project migration/deprecation policy rather than silent replacement.

## Public API drift guard

The repository maintains:

```text
tests/unit/test_public_api_inventory.py
```

to freeze the exported `__all__` sets for the public package surfaces.

This is executable evidence that the public API boundary is deliberate.

## Worked example

```python
from pathlib import Path

from pydbadminkit.bootstrap import (
    build_catalog_service,
    build_health_service,
    build_runtime_service,
    build_security_service,
    build_server_service,
)
from pydbadminkit.errors import PyDBAdminError

CONFIG = Path("config.toml")
PROFILE = "local"

try:
    server = build_server_service(PROFILE, CONFIG)
    catalog = build_catalog_service(PROFILE, CONFIG)
    runtime = build_runtime_service(PROFILE, CONFIG)
    security = build_security_service(PROFILE, CONFIG)
    health = build_health_service(PROFILE, CONFIG)

    server_info = server.get_info()
    databases = catalog.list_databases()
    sessions = runtime.list_sessions()
    roles = security.list_roles(login_only=True)
    health_report = health.check()

    print("Server:", server_info.version)
    print("Databases:", [database.name for database in databases])
    print("Sessions:", len(sessions))
    print("Login roles:", [role.name for role in roles])
    print("Health:", health_report.overall_status)

except PyDBAdminError as exc:
    print("PyDBAdminKit error:", exc.code.value)
    raise
```

This example remains entirely inside the public 1.0 API boundary.

## Troubleshooting

### Import works but is undocumented

A Python module being importable does not mean it is stable.

Check the public API reference before depending on it.

### Adapter import appears convenient

Prefer the matching bootstrap builder or public port.

For example, prefer:

```python
build_catalog_service(...)
```

over constructing `PostgreSQLCatalogAdapter` directly.

### Method name from an old example fails

Use the current public reference and inspect the service class.

Examples verified for 1.0 include:

```text
ConnectionService.test
ServerService.get_info
CatalogService.list_databases
RuntimeService.list_sessions
SecurityService.list_roles
CapabilityService.list
CapabilityService.get
HealthService.check
```

### Secret prints as redacted

Expected behavior.

Do not bypass redaction for routine debugging.

### PyDBAdminError is too broad

Catch a specific public subclass when your workflow needs different recovery behavior.

### You need a custom provider or adapter

Implement the relevant public port and compose the service deliberately.

Do not depend on undocumented internal implementation types unless you accept the absence of 1.0
compatibility guarantees.

## Best practices

Prefer:

```text
bootstrap builders for standard PostgreSQL usage
public domain models
public application services
public ports for extensions
typed public errors
explicit config paths
centralized dependency composition
read-only services for inspection
```

Avoid:

```text
imports from adapters.*
imports from infrastructure.*
imports from cli.*
underscore bootstrap helpers
PostgreSQL SQL modules
PostgreSQL mapper modules
parsing CLI JSON from Python when a direct API exists
raw SecretValue.reveal() in logs
direct adapter mutation bypassing safety services
```

## Key takeaways

- The package root intentionally exports only `__version__`.
- `pydbadminkit.bootstrap` is the recommended composition root.
- Non-underscore bootstrap builders are stable 1.0 convenience APIs.
- Services return typed public domain objects.
- Application services are stable behavioral boundaries.
- Ports are public extension contracts.
- Typed errors and `ErrorCode` are public machine-relevant API.
- `adapters.*`, `infrastructure.*` and `cli.*` are implementation details.
- Technically importable does not mean publicly stable.
- Python integrations should call the Python API directly instead of shelling out to the CLI when
  both options are available.
- Mutation services should be used through the public planning/safety model rather than bypassed
  through adapters.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md)
- [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md)
- [CLI Fundamentals](06_CLI_FUNDAMENTALS.md)
- [Table, JSON and YAML Output](07_OUTPUT_FORMATS_JSON_YAML_TABLE.md)
- [Database Exploration](09_DATABASE_EXPLORATION.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Python Automation Patterns](29_PYTHON_AUTOMATION_PATTERNS.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)
- [Public API inventory](../contracts/PUBLIC_API_INVENTORY.md)
- [Migration and deprecation policy](../reference/MIGRATION_AND_DEPRECATION_POLICY.md)

## Next

Continue with [Database Exploration](09_DATABASE_EXPLORATION.md).
