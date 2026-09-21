"""Restricted-permission JSONL audit sink."""

import json
import os
from pathlib import Path

from platformdirs import user_state_path

from pydbadminkit.domain.audit import AuditEvent
from pydbadminkit.errors import AuditUnavailableError


def default_audit_path() -> Path:
    """Return the default local audit path, allowing a test/ops override."""

    override = os.getenv("PYDBADMIN_AUDIT_PATH")
    if override:
        return Path(override).expanduser()
    return Path(user_state_path("pydbadminkit")) / "audit.jsonl"


class JsonlAuditSink:
    """Append audit events to a local JSONL file with restrictive permissions."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, event: AuditEvent) -> None:
        payload = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "actor": event.actor,
            "profile": event.profile,
            "environment": event.environment.value,
            "database": event.database,
            "operation": event.operation,
            "target": event.target,
            "risk": event.risk.label,
            "status": event.status.value,
            "correlation_id": event.correlation_id,
            "message": event.message,
        }

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(
                self._path,
                os.O_APPEND | os.O_CREAT | os.O_WRONLY,
                0o600,
            )
            with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False))
                stream.write("\n")
        except OSError as error:
            raise AuditUnavailableError(
                f"Audit event could not be persisted to '{self._path}'."
            ) from error
