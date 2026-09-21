"""Shared CLI helpers for mutation results."""

import typer

from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.common import OperationResult
from pydbadminkit.domain.safety import OperationPlan
from pydbadminkit.output.human import render_operation_plan, render_operation_result


def emit_mutation_outcome(
    ctx: typer.Context,
    outcome: OperationPlan | OperationResult,
) -> None:
    """Emit a dry-run plan or completed mutation result."""

    if isinstance(outcome, OperationPlan):
        emit_output(ctx, outcome, render_operation_plan(outcome))
        return
    emit_output(ctx, outcome, render_operation_result(outcome))
