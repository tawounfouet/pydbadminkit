"""Simple stable human-readable renderers for the initial CLI."""

from pydbadminkit.domain.catalog import (
    DatabaseInfo,
    SchemaInfo,
    ServerInfo,
    TableDescription,
    TableInfo,
)
from pydbadminkit.domain.common import CapabilityStatus


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
