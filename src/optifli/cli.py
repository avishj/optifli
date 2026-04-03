# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI entry point."""

import logging
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.table import Table

from optifli import __version__
from optifli.config import settings
from optifli.exit_codes import ExitCode
from optifli.logging import setup_logging
from optifli.models.itinerary import Itinerary
from optifli.profile import ProfileError, load_profile

logger = logging.getLogger(__name__)

app = App(
    name="optifli",
    help="optifli CLI.",
    version=__version__,
    version_flags=["--version", "-V"],
)
app.register_install_completion_command()
console = Console(stderr=True)
_out = Console()


def _print_itinerary(itinerary: Itinerary) -> None:
    """Print a resolved itinerary summary as a Rich table."""
    table = Table(title="Itinerary Summary")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row(
        "Origin",
        f"{itinerary.origin.name} ({', '.join(itinerary.origin.airports)})",
    )

    for i, dest in enumerate(itinerary.destinations, 1):
        city = dest.city
        table.add_row(
            f"Destination {i}",
            f"{city.name} ({', '.join(city.airports)}) - {dest.stay}",
        )

    table.add_row(
        "Return",
        (f"{itinerary.return_city.name} ({', '.join(itinerary.return_city.airports)})"),
    )
    table.add_row("Direction", itinerary.direction.value)
    table.add_row("Route mode", itinerary.route_mode.value)
    table.add_row("Legs", str(len(itinerary.legs)))

    _out.print(table)


@app.command
def optimize(
    *,
    profile: Annotated[
        Path | None,
        Parameter("--profile", help="Path to a JSON profile file."),
    ] = None,
) -> ExitCode:
    """Search for optimal flights from a profile.

    Parameters
    ----------
    profile:
        Path to a JSON itinerary profile.
    """
    if profile is None:
        console.print("[red]Error:[/red] --profile is required")
        return ExitCode.USAGE

    try:
        itinerary = load_profile(profile)
    except ProfileError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return ExitCode.USAGE

    logger.debug("loaded itinerary with %d destinations", len(itinerary.destinations))
    _print_itinerary(itinerary)
    return ExitCode.OK


@app.meta.default
def main(
    *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    verbose: Annotated[
        bool,
        Parameter("--verbose", help="Enable verbose output."),
    ] = settings.verbose,
) -> ExitCode:
    """Run the optifli CLI."""
    settings.verbose = verbose
    setup_logging(verbose=verbose, log_format=settings.log_format)
    return app(tokens)


def entrypoint() -> None:
    """Package entrypoint for console_scripts."""
    app.meta()
