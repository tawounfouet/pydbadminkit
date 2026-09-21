"""CLI output routing."""

import typer

from pydbadminkit.cli.common import require_cli_context
from pydbadminkit.output.format import OutputFormat
from pydbadminkit.output.serialization import render_json, render_yaml


def emit_output(
    ctx: typer.Context,
    value: object,
    human_rendered: str,
) -> None:
    """Emit exactly one representation to stdout."""

    root_context = require_cli_context(ctx)

    if root_context.output_format is OutputFormat.JSON:
        typer.echo(render_json(value))
        return

    if root_context.output_format is OutputFormat.YAML:
        typer.echo(render_yaml(value))
        return

    typer.echo(human_rendered)
