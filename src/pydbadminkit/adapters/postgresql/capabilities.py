"""PostgreSQL capability discovery."""

from pydbadminkit.domain.common import CapabilityAvailability, CapabilityStatus


class PostgreSQLCapabilityAdapter:
    """Expose capabilities implemented by the current PostgreSQL adapter."""

    _IMPLEMENTED = frozenset(
        {
            "connection.test",
            "server.info",
            "catalog.database.list",
            "catalog.database.describe",
        }
    )

    _PLANNED = frozenset(
        {
            "catalog.schema.list",
            "catalog.table.list",
            "catalog.table.describe",
            "runtime.session.list",
            "runtime.query.list",
            "runtime.lock.list",
        }
    )

    def get_capability(self, name: str) -> CapabilityStatus:
        if name in self._IMPLEMENTED:
            return CapabilityStatus(
                name=name,
                availability=CapabilityAvailability.AVAILABLE,
            )
        if name in self._PLANNED:
            return CapabilityStatus(
                name=name,
                availability=CapabilityAvailability.DISABLED_BY_POLICY,
                reason="Capability is defined but not implemented in this release.",
            )
        return CapabilityStatus(
            name=name,
            availability=CapabilityAvailability.UNKNOWN,
            reason="Unknown capability.",
        )

    def list_capabilities(self) -> tuple[CapabilityStatus, ...]:
        names = sorted(self._IMPLEMENTED | self._PLANNED)
        return tuple(self.get_capability(name) for name in names)
