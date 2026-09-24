"""Unit tests for the python -m pydbadminkit entrypoint."""

import importlib
import runpy
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.unit


def test_module_entrypoint_calls_cli_app(monkeypatch: pytest.MonkeyPatch) -> None:
    cli_app_module = importlib.import_module("pydbadminkit.cli.app")
    app = Mock()
    monkeypatch.setattr(cli_app_module, "app", app)

    runpy.run_module("pydbadminkit.__main__", run_name="__main__")

    app.assert_called_once_with()


def test_module_entrypoint_does_not_call_cli_app_when_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli_app_module = importlib.import_module("pydbadminkit.cli.app")
    app = Mock()
    monkeypatch.setattr(cli_app_module, "app", app)

    runpy.run_module("pydbadminkit.__main__", run_name="pydbadminkit.__main_test__")

    app.assert_not_called()
