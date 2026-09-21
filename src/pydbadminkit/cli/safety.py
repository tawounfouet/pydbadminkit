"""CLI-only mutation confirmation handling."""

import typer

from pydbadminkit.cli.common import require_cli_context
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan


def mutation_options(
    ctx: typer.Context,
    plan: OperationPlan,
    *,
    confirmed_target: str | None = None,
) -> MutationOptions:
    """Resolve CLI approval without moving prompts into application services."""

    root_context = require_cli_context(ctx)

    if root_context.dry_run:
        return MutationOptions(dry_run=True)

    if plan.confirmation is ConfirmationLevel.TYPE_TARGET:
        if confirmed_target is None and not root_context.non_interactive:
            confirmed_target = typer.prompt(
                f"Type target exactly to confirm [{plan.target}]",
                default="",
                show_default=False,
            )
        return MutationOptions(confirmed_target=confirmed_target)

    if plan.confirmation is ConfirmationLevel.NONE:
        return MutationOptions(approved=True)

    if root_context.assume_yes:
        return MutationOptions(approved=True)

    if root_context.non_interactive:
        return MutationOptions(approved=False)

    typer.echo(f"Operation: {plan.operation}", err=True)
    typer.echo(f"Target: {plan.target}", err=True)
    typer.echo(f"Risk: {plan.risk.label}", err=True)
    for warning in plan.warnings:
        typer.echo(f"Warning: {warning}", err=True)

    approved = typer.confirm("Proceed with this mutation?", default=False)
    return MutationOptions(approved=approved)
