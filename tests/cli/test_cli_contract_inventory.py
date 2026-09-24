"""Drift guard for the LOT-20 CLI contract inventory."""

import pytest
from typer.main import get_command

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.unit, pytest.mark.cli]

EXPECTED_COMMAND_PATHS = {
    "access grant",
    "access list",
    "access revoke",
    "backup create",
    "backup restore",
    "backup validate",
    "blocking list",
    "capability get",
    "capability list",
    "connection test",
    "database describe",
    "database list",
    "effective-access list",
    "health check",
    "index describe",
    "index list",
    "lock list",
    "ownership list",
    "postgres analyze",
    "postgres progress reindex",
    "postgres progress vacuum",
    "postgres reindex",
    "postgres vacuum",
    "query cancel",
    "query list",
    "role alter",
    "role create",
    "role describe",
    "role drop",
    "role list",
    "role membership-add",
    "role membership-remove",
    "schema describe",
    "schema list",
    "server info",
    "session list",
    "session terminate",
    "table describe",
    "table list",
    "transaction list",
    "view describe",
    "view list",
    "wait list",
}

EXPECTED_ROOT_OPTIONS = {
    ("--config",),
    ("--connection", "-c"),
    ("--dry-run",),
    ("--install-completion",),
    ("--non-interactive",),
    ("--output", "-o"),
    ("--show-completion",),
    ("--version",),
    ("--yes", "-y"),
}


def _leaf_command_paths(group: object, prefix: tuple[str, ...] = ()) -> set[str]:
    paths: set[str] = set()
    commands = getattr(group, "commands", {})
    for name, command in commands.items():
        current = (*prefix, name)
        if getattr(command, "commands", None) is not None:
            paths.update(_leaf_command_paths(command, current))
        else:
            paths.add(" ".join(current))
    return paths


def test_cli_command_paths_match_inventory() -> None:
    command = get_command(app)

    assert _leaf_command_paths(command) == EXPECTED_COMMAND_PATHS


def test_cli_root_options_match_inventory() -> None:
    command = get_command(app)
    explicit_options = {
        tuple(option.opts) for option in command.params if getattr(option, "opts", None)
    }

    assert explicit_options == EXPECTED_ROOT_OPTIONS
