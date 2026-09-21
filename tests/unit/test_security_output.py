"""Unit tests for security output."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.security import RoleDescription, RoleInfo, RoleMembership
from pydbadminkit.output.human import render_role_description, render_role_list
from pydbadminkit.output.serialization import render_json, render_yaml

pytestmark = pytest.mark.unit


def _description() -> RoleDescription:
    return RoleDescription(
        role=RoleInfo(
            name="app",
            can_login=True,
            valid_until=datetime(2030, 1, 1, tzinfo=UTC),
        ),
        member_of=(
            RoleMembership(
                role="reader",
                member="app",
                grantor="postgres",
            ),
        ),
        members=(
            RoleMembership(
                role="app",
                member="worker",
                grantor="postgres",
                admin_option=True,
            ),
        ),
    )


def test_role_human_renderers() -> None:
    description = _description()

    listing = render_role_list((description.role,))
    detail = render_role_description(description)

    assert "app\tyes\tno\tno\tno\tno\tno\tno" in listing
    assert "Valid until: 2030-01-01T00:00:00+00:00" in detail
    assert "MEMBER OF" in detail
    assert "reader\tpostgres\tno" in detail
    assert "worker\tpostgres\tyes" in detail


def test_role_machine_output_serializes_datetime() -> None:
    import json

    import yaml

    json_value = json.loads(render_json(_description()))
    yaml_value = yaml.safe_load(render_yaml(_description()))

    assert json_value["role"]["valid_until"] == "2030-01-01T00:00:00+00:00"
    assert yaml_value["member_of"][0]["role"] == "reader"
