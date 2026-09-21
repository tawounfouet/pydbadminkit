"""Capability CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_capability_service
from pydbadminkit.output.human import render_capability_info, render_capability_list

capability_app = typer.Typer(
    name="capability",
    no_args_is_help=True,
    help="Inspect capabilities implemented by the current adapter.",
)


@capability_app.command("list")
def list_capabilities() -> None:
    """List known PostgreSQL capabilities."""

    typer.echo(render_capability_list(build_capability_service().list()))


@capability_app.command("get")
def get_capability(
    name: Annotated[str, typer.Argument(help="Capability identifier.")],
) -> None:
    """Describe one capability."""

    typer.echo(render_capability_info(build_capability_service().get(name)))
