"""Simple stable human-readable renderers for the initial CLI."""

from pydbadminkit.domain.catalog import DatabaseInfo, ServerInfo


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


def _connections_value(value: bool | None) -> str:
    if value is None:
        return "-"
    return "yes" if value else "no"


def _optional_int(value: int | None) -> str:
    if value is None:
        return "-"
    return str(value)
