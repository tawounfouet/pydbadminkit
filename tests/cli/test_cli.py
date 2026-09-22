"""CLI bootstrap tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.unit, pytest.mark.cli]

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "database administration toolkit" in result.stdout


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "pydbadminkit 0.5.0a2"


def test_connection_test_requires_selected_profile() -> None:
    result = runner.invoke(app, ["connection", "test"])
    assert result.exit_code == 2
    assert "Select a profile with --connection" in result.output


def test_connection_test_reports_missing_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--config",
            str(tmp_path / "missing.toml"),
            "connection",
            "test",
        ],
    )
    assert result.exit_code == 2
    assert "Configuration file" in result.output


def test_capability_json_output_is_machine_only() -> None:
    import json

    result = runner.invoke(app, ["--output", "json", "capability", "get", "server.info"])

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["name"] == "server.info"
    assert parsed["availability"] == "available"
    assert "Name:" not in result.stdout


def test_capability_yaml_output_is_machine_only() -> None:
    import yaml

    result = runner.invoke(app, ["--output", "yaml", "capability", "get", "server.info"])

    assert result.exit_code == 0
    parsed = yaml.safe_load(result.stdout)
    assert parsed["name"] == "server.info"
    assert parsed["availability"] == "available"
