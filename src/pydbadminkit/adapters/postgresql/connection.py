"""PostgreSQL connection factory and connection-test adapter."""

from time import perf_counter
from typing import Any

import psycopg
from psycopg import Connection

from pydbadminkit.adapters.postgresql.errors import translate_connection_error
from pydbadminkit.adapters.postgresql.version import parse_server_version_num
from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.connection.resolved import ResolvedConnectionConfig
from pydbadminkit.domain.connection.result import ConnectionTestResult
from pydbadminkit.errors import CapabilityNotAvailableError, InternalError
from pydbadminkit.errors.context import ErrorContext
from pydbadminkit.version import __version__

PsycopgConnection = Connection[tuple[Any, ...]]


class PostgreSQLConnectionFactory:
    """Create short-lived Psycopg connections from resolved configuration."""

    def connect(self, config: ResolvedConnectionConfig) -> PsycopgConnection:
        if config.engine is not DatabaseEngine.POSTGRESQL:
            raise CapabilityNotAvailableError(
                f"Engine '{config.engine.value}' is not supported by the PostgreSQL adapter."
            )

        context = ErrorContext(
            operation="connection.open",
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(config.name),
            environment=config.environment,
        )

        parameters: dict[str, str | int] = {
            "host": config.host,
            "port": config.port,
            "dbname": config.database,
            "user": config.username,
            "sslmode": config.ssl.mode.value,
            "connect_timeout": config.timeouts.connect_seconds,
            "application_name": f"pydbadminkit/{__version__}/cli",
        }

        if config.password is not None:
            parameters["password"] = config.password.reveal()
        if config.ssl.root_cert is not None:
            parameters["sslrootcert"] = config.ssl.root_cert
        if config.ssl.cert is not None:
            parameters["sslcert"] = config.ssl.cert
        if config.ssl.key is not None:
            parameters["sslkey"] = config.ssl.key

        conninfo = psycopg.conninfo.make_conninfo(**parameters)

        try:
            return psycopg.connect(conninfo, autocommit=True)
        except psycopg.Error as error:
            raise translate_connection_error(error, context=context) from error


class PostgreSQLConnectionTester:
    """Validate a PostgreSQL connection and return safe server diagnostics."""

    def __init__(self, factory: PostgreSQLConnectionFactory) -> None:
        self._factory = factory

    def test(self, config: ResolvedConnectionConfig) -> ConnectionTestResult:
        started = perf_counter()

        with self._factory.connect(config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        current_setting('server_version_num')::int,
                        current_database(),
                        current_user
                    """
                )
                row = cursor.fetchone()

        latency_ms = (perf_counter() - started) * 1000

        if row is None or len(row) != 3:
            raise InternalError("PostgreSQL connection test returned an unexpected result.")

        version_info = parse_server_version_num(int(row[0]))
        return ConnectionTestResult(
            engine=DatabaseEngine.POSTGRESQL,
            version=version_info.version,
            current_database=str(row[1]),
            current_user=str(row[2]),
            latency_ms=latency_ms,
        )
