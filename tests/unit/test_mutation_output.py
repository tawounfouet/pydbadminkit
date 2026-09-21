"""Unit tests for mutation plan/result output."""

import json

import pytest

from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationResult,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.safety import ConfirmationLevel, OperationPlan
from pydbadminkit.output.human import render_operation_plan, render_operation_result
from pydbadminkit.output.serialization import render_json

pytestmark = [pytest.mark.unit, pytest.mark.security]


def test_operation_plan_human_and_json_output() -> None:
    plan = OperationPlan(
        operation="security.role.drop",
        target="app",
        environment=EnvironmentName.PRODUCTION,
        risk=RiskLevel.CRITICAL,
        confirmation=ConfirmationLevel.TYPE_TARGET,
        effects=("Drop role 'app'.",),
        warnings=("Production target.",),
        correlation_id="corr-1",
    )

    human = render_operation_plan(plan)
    machine = json.loads(render_json(plan))

    assert "Risk: critical" in human
    assert "Confirmation: type_target" in human
    assert "Drop role 'app'." in human
    assert machine["risk"] == "critical"
    assert machine["environment"] == "production"
    assert machine["confirmation"] == "type_target"


def test_operation_result_human_and_json_output() -> None:
    result = OperationResult(
        operation="security.role.create",
        status=OperationStatus.SUCCEEDED,
        changed=True,
        message="Created.",
        metadata={"target": "app", "risk": "medium"},
    )

    human = render_operation_result(result)
    machine = json.loads(render_json(result))

    assert "Status: succeeded" in human
    assert "Changed: yes" in human
    assert "target: app" in human
    assert machine["status"] == "succeeded"
    assert machine["metadata"]["risk"] == "medium"
