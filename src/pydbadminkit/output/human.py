"""Simple stable human-readable renderers for the initial CLI."""

from pydbadminkit.domain.catalog import (
    DatabaseInfo,
    IndexDescription,
    IndexInfo,
    SchemaInfo,
    ServerInfo,
    TableDescription,
    TableInfo,
    ViewDescription,
    ViewInfo,
)
from pydbadminkit.domain.common import CapabilityStatus, OperationResult
from pydbadminkit.domain.connection import ConnectionTestResult
from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, TransactionInfo
from pydbadminkit.domain.safety import OperationPlan
from pydbadminkit.domain.security import (
    DirectAccess,
    EffectiveAccess,
    OwnershipInfo,
    RoleDescription,
    RoleInfo,
)


def render_operation_plan(plan: OperationPlan) -> str:
    """Render a mutation plan."""

    lines = [
        f"Operation: {plan.operation}",
        f"Target: {plan.target}",
        f"Environment: {plan.environment.value}",
        f"Risk: {plan.risk.label}",
        f"Confirmation: {plan.confirmation.value}",
        f"Correlation ID: {plan.correlation_id}",
        "",
        "EFFECTS",
    ]
    lines.extend(f"- {effect}" for effect in plan.effects)
    if plan.warnings:
        lines.extend(("", "WARNINGS"))
        lines.extend(f"- {warning}" for warning in plan.warnings)
    return "\n".join(lines)


def render_operation_result(result: OperationResult) -> str:
    """Render a mutation result."""

    lines = [
        f"Operation: {result.operation}",
        f"Status: {result.status.value}",
        f"Changed: {'yes' if result.changed else 'no' if result.changed is False else '-'}",
        f"Message: {result.message or '-'}",
    ]
    if result.metadata:
        lines.extend(("", "METADATA"))
        lines.extend(f"{key}: {value}" for key, value in result.metadata.items())
    return "\n".join(lines)


def render_connection_test(result: ConnectionTestResult) -> str:
    """Render a successful connection test."""

    return "\n".join(
        (
            "Connection OK",
            f"Engine: {result.engine.value}",
            f"Version: {result.version}",
            f"Database: {result.current_database}",
            f"User: {result.current_user}",
            f"Latency: {result.latency_ms:.2f} ms",
        )
    )


def render_server_info(info: ServerInfo) -> str:
    """Render server information as label/value lines."""

    lines = [
        f"Engine: {info.engine.value}",
        f"Version: {info.version}",
        f"Database: {info.current_database or '-'}",
        f"User: {info.current_user or '-'}",
    ]
    return "\n".join(lines)


def render_database_list(databases: tuple[DatabaseInfo, ...]) -> str:
    """Render database summaries as a deterministic tab-separated table."""

    lines = ["NAME\tOWNER\tENCODING\tCONNECTIONS\tSIZE_BYTES"]
    for database in databases:
        lines.append(
            "\t".join(
                (
                    database.name,
                    database.owner or "-",
                    database.encoding or "-",
                    _connections_value(database.allow_connections),
                    _optional_int(database.size_bytes),
                )
            )
        )
    return "\n".join(lines)


def render_database_info(database: DatabaseInfo) -> str:
    """Render one database as label/value lines."""

    lines = [
        f"Name: {database.name}",
        f"Owner: {database.owner or '-'}",
        f"Encoding: {database.encoding or '-'}",
        f"Collation: {database.collation or '-'}",
        f"Allow connections: {_connections_value(database.allow_connections)}",
        f"Connection limit: {_optional_int(database.connection_limit)}",
        f"Size bytes: {_optional_int(database.size_bytes)}",
    ]
    return "\n".join(lines)


def render_schema_list(schemas: tuple[SchemaInfo, ...]) -> str:
    """Render schema summaries."""

    lines = ["NAME\tOWNER\tSYSTEM"]
    for schema in schemas:
        lines.append(
            "\t".join(
                (
                    schema.name,
                    schema.owner or "-",
                    "yes" if schema.is_system else "no",
                )
            )
        )
    return "\n".join(lines)


def render_schema_info(schema: SchemaInfo) -> str:
    """Render one schema."""

    return "\n".join(
        (
            f"Name: {schema.name}",
            f"Owner: {schema.owner or '-'}",
            f"System: {'yes' if schema.is_system else 'no'}",
        )
    )


def render_table_list(tables: tuple[TableInfo, ...]) -> str:
    """Render table summaries."""

    lines = ["NAME\tOWNER\tKIND\tEST_ROWS\tSIZE_BYTES"]
    for table in tables:
        lines.append(
            "\t".join(
                (
                    str(table.name),
                    table.owner or "-",
                    table.kind.value,
                    _optional_int(table.estimated_rows),
                    _optional_int(table.size_bytes),
                )
            )
        )
    return "\n".join(lines)


def render_table_description(description: TableDescription) -> str:
    """Render table metadata, columns and constraints."""

    table = description.table
    lines = [
        f"Name: {table.name}",
        f"Owner: {table.owner or '-'}",
        f"Kind: {table.kind.value}",
        f"Estimated rows: {_optional_int(table.estimated_rows)}",
        f"Size bytes: {_optional_int(table.size_bytes)}",
        "",
        "COLUMNS",
        "POSITION\tNAME\tTYPE\tNULLABLE\tDEFAULT\tIDENTITY\tGENERATED",
    ]
    for column in description.columns:
        lines.append(
            "\t".join(
                (
                    str(column.position),
                    column.name,
                    column.data_type,
                    "yes" if column.nullable else "no",
                    column.default or "-",
                    "yes" if column.identity else "no",
                    "yes" if column.generated else "no",
                )
            )
        )

    lines.extend(("", "CONSTRAINTS", "NAME\tTYPE\tCOLUMNS\tDEFINITION"))
    for constraint in description.constraints:
        lines.append(
            "\t".join(
                (
                    constraint.name,
                    constraint.constraint_type.value,
                    ",".join(constraint.columns) or "-",
                    constraint.definition or "-",
                )
            )
        )
    return "\n".join(lines)


def render_view_list(views: tuple[ViewInfo, ...]) -> str:
    """Render view summaries."""

    lines = ["NAME\tOWNER\tKIND"]
    for view in views:
        lines.append(
            "\t".join(
                (
                    str(view.name),
                    view.owner or "-",
                    view.kind.value,
                )
            )
        )
    return "\n".join(lines)


def render_view_description(description: ViewDescription) -> str:
    """Render view metadata, columns and definition."""

    view = description.view
    lines = [
        f"Name: {view.name}",
        f"Owner: {view.owner or '-'}",
        f"Kind: {view.kind.value}",
        "",
        "COLUMNS",
        "POSITION\tNAME\tTYPE\tNULLABLE",
    ]
    for column in description.columns:
        lines.append(
            "\t".join(
                (
                    str(column.position),
                    column.name,
                    column.data_type,
                    "yes" if column.nullable else "no",
                )
            )
        )
    lines.extend(("", "DEFINITION", description.definition or "-"))
    return "\n".join(lines)


def render_index_list(indexes: tuple[IndexInfo, ...]) -> str:
    """Render index summaries."""

    lines = ["NAME\tTABLE\tMETHOD\tUNIQUE\tPRIMARY\tVALID\tREADY\tSIZE_BYTES"]
    for index in indexes:
        lines.append(
            "\t".join(
                (
                    str(index.name),
                    str(index.table),
                    index.method,
                    "yes" if index.unique else "no",
                    "yes" if index.primary else "no",
                    "yes" if index.valid else "no",
                    "yes" if index.ready else "no",
                    _optional_int(index.size_bytes),
                )
            )
        )
    return "\n".join(lines)


def render_index_description(description: IndexDescription) -> str:
    """Render one index in detail."""

    index = description.index
    return "\n".join(
        (
            f"Name: {index.name}",
            f"Table: {index.table}",
            f"Owner: {index.owner or '-'}",
            f"Method: {index.method}",
            f"Unique: {'yes' if index.unique else 'no'}",
            f"Primary: {'yes' if index.primary else 'no'}",
            f"Valid: {'yes' if index.valid else 'no'}",
            f"Ready: {'yes' if index.ready else 'no'}",
            f"Size bytes: {_optional_int(index.size_bytes)}",
            f"Predicate: {description.predicate or '-'}",
            "",
            "DEFINITION",
            description.definition,
        )
    )


def render_effective_access_list(entries: tuple[EffectiveAccess, ...]) -> str:
    """Render effective access entries with their sources."""

    lines = ["PRINCIPAL\tOBJECT\tTYPE\tACCESS\tSOURCES"]
    for entry in entries:
        lines.append(
            "\t".join(
                (
                    entry.principal,
                    str(entry.object.name),
                    entry.object.object_type.value,
                    entry.access_type.value,
                    ",".join(source.value for source in entry.sources),
                )
            )
        )
    return "\n".join(lines)


def render_ownership_list(entries: tuple[OwnershipInfo, ...]) -> str:
    """Render ownership relationships."""

    lines = ["OWNER\tOBJECT\tTYPE"]
    for entry in entries:
        lines.append(
            "\t".join(
                (
                    entry.owner,
                    str(entry.object.name),
                    entry.object.object_type.value,
                )
            )
        )
    return "\n".join(lines)


def render_access_list(entries: tuple[DirectAccess, ...]) -> str:
    """Render explicit relation access entries."""

    lines = ["PRINCIPAL\tOBJECT\tTYPE\tACCESS\tISSUER\tDELEGABLE"]
    for entry in entries:
        lines.append(
            "\t".join(
                (
                    entry.principal,
                    str(entry.object.name),
                    entry.object.object_type.value,
                    entry.access_type.value,
                    entry.issuer or "-",
                    "yes" if entry.delegable else "no",
                )
            )
        )
    return "\n".join(lines)


def render_role_list(roles: tuple[RoleInfo, ...]) -> str:
    """Render role summaries."""

    lines = ["NAME\tLOGIN\tSUPERUSER\tCREATEDB\tCREATEROLE\tREPLICATION\tBYPASSRLS\tSYSTEM"]
    for role in roles:
        lines.append(
            "\t".join(
                (
                    role.name,
                    "yes" if role.can_login else "no",
                    "yes" if role.is_superuser else "no",
                    "yes" if role.can_create_db else "no",
                    "yes" if role.can_create_role else "no",
                    "yes" if role.can_replicate else "no",
                    "yes" if role.bypass_rls else "no",
                    "yes" if role.is_system else "no",
                )
            )
        )
    return "\n".join(lines)


def render_role_description(description: RoleDescription) -> str:
    """Render one role and its membership relationships."""

    role = description.role
    lines = [
        f"Name: {role.name}",
        f"Login: {'yes' if role.can_login else 'no'}",
        f"Superuser: {'yes' if role.is_superuser else 'no'}",
        f"Create DB: {'yes' if role.can_create_db else 'no'}",
        f"Create role: {'yes' if role.can_create_role else 'no'}",
        f"Replication: {'yes' if role.can_replicate else 'no'}",
        f"Inherit: {'yes' if role.inherit else 'no'}",
        f"Bypass RLS: {'yes' if role.bypass_rls else 'no'}",
        f"Connection limit: {_optional_int(role.connection_limit)}",
        f"Valid until: {role.valid_until.isoformat() if role.valid_until else '-'}",
        "",
        "MEMBER OF",
        "ROLE\tGRANTOR\tADMIN",
    ]
    for membership in description.member_of:
        lines.append(
            "\t".join(
                (
                    membership.role,
                    membership.grantor or "-",
                    "yes" if membership.admin_option else "no",
                )
            )
        )

    lines.extend(("", "MEMBERS", "MEMBER\tGRANTOR\tADMIN"))
    for membership in description.members:
        lines.append(
            "\t".join(
                (
                    membership.member,
                    membership.grantor or "-",
                    "yes" if membership.admin_option else "no",
                )
            )
        )
    return "\n".join(lines)


def render_capability_list(capabilities: tuple[CapabilityStatus, ...]) -> str:
    """Render capabilities in deterministic tab-separated form."""

    lines = ["NAME\tSTATUS\tREASON"]
    for capability in capabilities:
        lines.append(
            "\t".join(
                (
                    capability.name,
                    capability.availability.value,
                    capability.reason or "-",
                )
            )
        )
    return "\n".join(lines)


def render_capability_info(capability: CapabilityStatus) -> str:
    """Render one capability."""

    return "\n".join(
        (
            f"Name: {capability.name}",
            f"Status: {capability.availability.value}",
            f"Available: {'yes' if capability.available else 'no'}",
            f"Reason: {capability.reason or '-'}",
        )
    )


def _connections_value(value: bool | None) -> str:
    if value is None:
        return "-"
    return "yes" if value else "no"


def _optional_int(value: int | None) -> str:
    if value is None:
        return "-"
    return str(value)


def render_session_list(sessions: tuple[SessionInfo, ...]) -> str:
    """Render live database sessions."""

    lines = [
        (
            "PID\tDATABASE\tUSER\tAPPLICATION\tCLIENT\tSTATE\tWAIT"
            "\tBACKEND_TYPE\tBACKEND_STARTED"
        )
    ]
    for session in sessions:
        wait = _wait_value(session.wait_event_type, session.wait_event)
        lines.append(
            "\t".join(
                (
                    str(session.pid),
                    session.database or "-",
                    session.username or "-",
                    session.application_name or "-",
                    session.client_address or "-",
                    session.state.value if session.state else "-",
                    wait,
                    session.backend_type or "-",
                    session.backend_started_at.isoformat()
                    if session.backend_started_at
                    else "-",
                )
            )
        )
    return "\n".join(lines)


def render_query_list(queries: tuple[QueryInfo, ...]) -> str:
    """Render currently active queries."""

    lines = ["PID\tDATABASE\tUSER\tQUERY_ID\tSTATE\tELAPSED_MS\tWAIT\tQUERY"]
    for query in queries:
        lines.append(
            "\t".join(
                (
                    str(query.pid),
                    query.database or "-",
                    query.username or "-",
                    _optional_int(query.query_id),
                    query.state.value if query.state else "-",
                    _optional_float(query.elapsed_ms),
                    _wait_value(query.wait_event_type, query.wait_event),
                    _query_preview(query.query_text),
                )
            )
        )
    return "\n".join(lines)


def render_transaction_list(transactions: tuple[TransactionInfo, ...]) -> str:
    """Render open transactions."""

    lines = [
        (
            "PID\tDATABASE\tUSER\tSTATE\tELAPSED_MS\tXID\tXMIN"
            "\tSTARTED_AT\tQUERY"
        )
    ]
    for transaction in transactions:
        lines.append(
            "\t".join(
                (
                    str(transaction.pid),
                    transaction.database or "-",
                    transaction.username or "-",
                    transaction.state.value if transaction.state else "-",
                    _optional_float(transaction.elapsed_ms),
                    transaction.backend_xid or "-",
                    transaction.backend_xmin or "-",
                    transaction.transaction_started_at.isoformat(),
                    _query_preview(transaction.query_text),
                )
            )
        )
    return "\n".join(lines)


def _wait_value(wait_event_type: str | None, wait_event: str | None) -> str:
    if wait_event_type is None and wait_event is None:
        return "-"
    if wait_event_type is None:
        return wait_event or "-"
    if wait_event is None:
        return wait_event_type
    return f"{wait_event_type}:{wait_event}"


def _optional_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _query_preview(value: str | None, limit: int = 160) -> str:
    if value is None:
        return "-"
    single_line = " ".join(value.split())
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 1] + "…"
