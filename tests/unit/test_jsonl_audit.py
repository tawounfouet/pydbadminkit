"""Unit tests for the local JSONL audit sink."""

import json
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import EnvironmentName, OperationStatus, RiskLevel
from pydbadminkit.infrastructure.audit import JsonlAuditSink

pytestmark = [pytest.mark.unit, pytest.mark.security]


def test_jsonl_audit_sink_writes_secret_safe_event(tmp_path: Path) -> None:
    path = tmp_path / "audit" / "events.jsonl"
    sink = JsonlAuditSink(path)
    sink.write(
        AuditEvent(
            event_id="event-1",
            event_type=AuditEventType.SUCCEEDED,
            timestamp=datetime(2026, 9, 21, tzinfo=UTC),
            actor="postgres",
            profile="local",
            environment=EnvironmentName.TESTING,
            database="pydbadmin_test",
            operation="security.role.create",
            target="app",
            risk=RiskLevel.MEDIUM,
            status=OperationStatus.SUCCEEDED,
            correlation_id="corr-1",
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["operation"] == "security.role.create"
    assert payload["risk"] == "medium"
    assert payload["correlation_id"] == "corr-1"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
