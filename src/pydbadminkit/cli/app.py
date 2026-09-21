"""Root Typer application."""

from typing import Annotated

import typer

from pydbadminkit.version import __version__

app = typer.Typer(
    name="pydbadmin",
    no_args_is_help=True,
    help="CLI-first, Python-first database administration toolkit.",
)


def _version_callback(value: bool) -> bool:
    if value:
        typer.echo(f"pydbadminkit {__version__}")
        raise typer.Exit()
    return value


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed PyDBAdminKit version and exit.",
        ),
    ] = False,
) -> None:
    """PyDBAdminKit command-line interface."""
