"""Unit tests for CLI mutation approval resolution."""

import pytest
import typer

from pydbadminkit.cli.app import app
from pydbadminkit.cli.context import CLIContext
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.common import EnvironmentName, RiskLevel
from pydbadminkit.domain.safety import ConfirmationLevel, OperationPlan

pytestmark = [pytest.mark.unit, pytest.mark.security]


def _context(**kwargs: object) -> typer.Context:
    root = CLIContext(**kwargs)
    return typer.Context(typer.main.get_command(app), obj=root)


def _plan(
    confirmation: ConfirmationLevel,
    *,
    target: str = "app",
) -> OperationPlan:
    return OperationPlan(
        operation="security.role.create",
        target=target,
        environment=EnvironmentName.TESTING,
        risk=RiskLevel.MEDIUM,
        confirmation=confirmation,
        effects=("Create role.",),
        correlation_id="corr-1",
    )


def test_dry_run_never_prompts() -> None:
    options = mutation_options(
        _context(dry_run=True),
        _plan(ConfirmationLevel.TYPE_TARGET),
    )

    assert options.dry_run is True
    assert options.confirmed_target is None


def test_yes_approves_explicit_but_not_typed_target() -> None:
    explicit = mutation_options(
        _context(assume_yes=True),
        _plan(ConfirmationLevel.EXPLICIT),
    )
    typed = mutation_options(
        _context(assume_yes=True, non_interactive=True),
        _plan(ConfirmationLevel.TYPE_TARGET),
    )

    assert explicit.approved is True
    assert typed.approved is False
    assert typed.confirmed_target is None


def test_non_interactive_preserves_supplied_typed_target() -> None:
    options = mutation_options(
        _context(non_interactive=True),
        _plan(ConfirmationLevel.TYPE_TARGET),
        confirmed_target="app",
    )

    assert options.confirmed_target == "app"


def test_interactive_simple_confirmation_uses_typer_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)

    options = mutation_options(
        _context(),
        _plan(ConfirmationLevel.SIMPLE),
    )

    assert options.approved is True


def test_interactive_typed_confirmation_uses_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(typer, "prompt", lambda *args, **kwargs: "critical-role")

    options = mutation_options(
        _context(),
        _plan(ConfirmationLevel.TYPE_TARGET, target="critical-role"),
    )

    assert options.confirmed_target == "critical-role"


def test_none_confirmation_is_auto_approved() -> None:
    options = mutation_options(
        _context(),
        _plan(ConfirmationLevel.NONE),
    )

    assert options.approved is True
