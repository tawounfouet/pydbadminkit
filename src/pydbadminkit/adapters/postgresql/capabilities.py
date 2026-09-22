"""PostgreSQL capability discovery."""

from pydbadminkit.domain.common import CapabilityAvailability, CapabilityStatus
from pydbadminkit.ports.tools import ToolResolverPort


class PostgreSQLCapabilityAdapter:
    """Expose capabilities implemented by the current PostgreSQL adapter."""

    _IMPLEMENTED = frozenset(
        {
            "connection.test",
            "server.info",
            "catalog.database.list",
            "catalog.database.describe",
            "catalog.schema.list",
            "catalog.schema.describe",
            "catalog.table.list",
            "catalog.table.describe",
            "catalog.view.list",
            "catalog.view.describe",
            "catalog.index.list",
            "catalog.index.describe",
            "security.role.list",
            "security.role.describe",
            "security.membership.list",
            "security.access.direct.list",
            "security.access.effective.list",
            "security.ownership.list",
            "security.role.create",
            "security.role.alter",
            "security.role.drop",
            "security.membership.add",
            "security.membership.remove",
            "security.access.grant",
            "security.access.revoke",
            "runtime.session.list",
            "runtime.query.list",
            "runtime.transaction.list",
            "runtime.wait.list",
            "runtime.lock.list",
            "runtime.blocking.list",
            "runtime.query.cancel",
            "runtime.session.terminate",
            "backup.create",
            "backup.validate",
        }
    )

    _PLANNED = frozenset(
        {
            "backup.restore",
            "maintenance.vacuum",
            "maintenance.analyze",
            "maintenance.reindex",
        }
    )

    def __init__(self, tool_resolver: ToolResolverPort | None = None) -> None:
        self._tool_resolver = tool_resolver

    def get_capability(self, name: str) -> CapabilityStatus:
        if name == "backup.create" and self._tool_resolver is not None:
            tool = self._tool_resolver.resolve("pg_dump")
            if not tool.available:
                return CapabilityStatus(
                    name=name,
                    availability=CapabilityAvailability.UNAVAILABLE_TOOL,
                    reason="Required tool 'pg_dump' was not found.",
                )

        if name in self._IMPLEMENTED:
            return CapabilityStatus(
                name=name,
                availability=CapabilityAvailability.AVAILABLE,
            )
        if name in self._PLANNED:
            return CapabilityStatus(
                name=name,
                availability=CapabilityAvailability.UNKNOWN,
                reason="Capability is defined in the roadmap but not implemented yet.",
            )
        return CapabilityStatus(
            name=name,
            availability=CapabilityAvailability.UNKNOWN,
            reason="Unknown capability.",
        )

    def list_capabilities(self) -> tuple[CapabilityStatus, ...]:
        names = sorted(self._IMPLEMENTED | self._PLANNED)
        return tuple(self.get_capability(name) for name in names)
