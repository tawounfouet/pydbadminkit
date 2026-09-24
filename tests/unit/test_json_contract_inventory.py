"""Drift guard for the LOT-20 JSON contract inventory."""

import json

import pytest

from pydbadminkit.domain.catalog import DatabaseInfo
from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    OperationResult,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.connection import ConnectionTestResult
from pydbadminkit.output.serialization import render_json, to_machine_value

pytestmark = pytest.mark.unit


def test_connection_result_json_contract() -> None:
    result = ConnectionTestResult(
        engine=DatabaseEngine.POSTGRESQL,
        version=DatabaseVersion(18),
        current_database="analytics",
        current_user="app",
        latency_ms=12.5,
    )

    assert to_machine_value(result) == {
        "engine": "postgresql",
        "version": {
            "major": 18,
            "minor": None,
            "patch": None,
            "raw": None,
        },
        "current_database": "analytics",
        "current_user": "app",
        "latency_ms": 12.5,
    }


def test_list_payload_and_explicit_null_contract() -> None:
    databases = (
        DatabaseInfo(
            name="analytics",
            owner="app",
            encoding="UTF8",
            collation=None,
            allow_connections=True,
            connection_limit=-1,
            size_bytes=1024,
        ),
    )

    assert to_machine_value(databases) == [
        {
            "name": "analytics",
            "owner": "app",
            "encoding": "UTF8",
            "collation": None,
            "allow_connections": True,
            "connection_limit": -1,
            "size_bytes": 1024,
        }
    ]
    assert to_machine_value(()) == []


def test_operation_result_json_contract_and_risk_label() -> None:
    result = OperationResult(
        operation="example",
        status=OperationStatus.SUCCEEDED,
        changed=True,
        message="completed",
        metadata={"risk": RiskLevel.LOW},
    )

    assert to_machine_value(result) == {
        "operation": "example",
        "status": "succeeded",
        "changed": True,
        "message": "completed",
        "metadata": {"risk": "low"},
    }


def test_render_json_preserves_contract_order() -> None:
    result = OperationResult(
        operation="example",
        status=OperationStatus.SUCCEEDED,
        changed=True,
        message="completed",
        metadata=None,
    )

    rendered = render_json(result)
    parsed = json.loads(rendered)

    assert list(parsed) == ["operation", "status", "changed", "message", "metadata"]
    assert '"operation": "example"' in rendered
    assert '"metadata": null' in rendered
