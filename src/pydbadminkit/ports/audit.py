"""Audit persistence port."""

from typing import Protocol

from pydbadminkit.domain.audit import AuditEvent


class AuditPort(Protocol):
    """Persist security-relevant audit events."""

    def write(self, event: AuditEvent) -> None:
        """Persist one audit event or raise if persistence is unavailable."""
        ...
