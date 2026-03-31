# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI entry point."""

import logging
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.markup import escape

from optifli import __version__
from optifli.config import settings
from optifli.exit_codes import ExitCode
from optifli.logging import setup_logging

logger = logging.getLogger(__name__)

app = App(
    name="optifli",
    help="optifli CLI.",
    version=__version__,
    version_flags=["--version", "-V"],
)
app.register_install_completion_command()
console = Console()


@app.command
def hello(name: str) -> ExitCode:
    """Greet someone.

    Parameters
    ----------
    name:
        Name to greet.
    """
    logger.debug("greeting name=%s", name)
    console.print(f"Hello, [bold]{escape(name)}[/bold]!")
    return ExitCode.OK


@app.meta.default
def main(
    *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    verbose: Annotated[
        bool,
        Parameter("--verbose", help="Enable verbose output."),
    ] = settings.verbose,
) -> None:
    """Run the optifli CLI."""
    settings.verbose = verbose
    setup_logging(verbose=verbose, log_format=settings.log_format)
    app(tokens)


def entrypoint() -> None:
    """Package entrypoint for console_scripts."""
    app.meta()
