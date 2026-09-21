"""Capability CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_capability_service
from pydbadminkit.cli.output import emit_output
from pydbadminkit.output.human import render_capability_info, render_capability_list

capability_app = typer.Typer(
    name="capability",
    no_args_is_help=True,
    help="Inspect capabilities implemented by the current adapter.",
)


@capability_app.command("list")
def list_capabilities(ctx: typer.Context) -> None:
    """List known PostgreSQL capabilities."""

    capabilities = build_capability_service().list()
    emit_output(ctx, capabilities, render_capability_list(capabilities))


@capability_app.command("get")
def get_capability(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Capability identifier.")],
) -> None:
    """Describe one capability."""

    capability = build_capability_service().get(name)
    emit_output(ctx, capability, render_capability_info(capability))
