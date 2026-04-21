# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI entry point."""

import logging
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from optifli import __version__
from optifli.config import settings
from optifli.exit_codes import ExitCode
from optifli.logging import setup_logging
from optifli.models import remap_for_reverse
from optifli.models.itinerary import Destination, DirectionMode, Itinerary
from optifli.profile import ProfileError, load_profile
from optifli.wizard import collect_itinerary

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


def _format_destination(destination: Destination) -> str:
    """Format one destination for CLI display."""
    city = destination.city
    return f"{city.name} ({', '.join(city.airports)}) - {destination.stay}"


def _print_reverse_map(itinerary: Itinerary) -> None:
    """Print the resolved reverse destination-duration map."""
    table = Table(title="Reverse Duration Map")
    table.add_column("Step", style="bold")
    table.add_column("Destination")

    for index, destination in enumerate(remap_for_reverse(itinerary), start=1):
        table.add_row(str(index), _format_destination(destination))

    _out.print(table)


def _print_direction_comparison(itinerary: Itinerary) -> None:
    """Print forward and reverse duration maps side by side."""
    table = Table(title="Direction Comparison")
    table.add_column("Step", style="bold")
    table.add_column("Forward")
    table.add_column("Reverse")

    forward = itinerary.destinations
    reverse = remap_for_reverse(itinerary)
    for index, (forward_destination, reverse_destination) in enumerate(
        zip(forward, reverse, strict=True),
        start=1,
    ):
        table.add_row(
            str(index),
            _format_destination(forward_destination),
            _format_destination(reverse_destination),
        )

    _out.print(table)


def _print_direction_resolution(itinerary: Itinerary) -> None:
    """Print resolved duration maps for reverse-aware directions."""
    if itinerary.direction is DirectionMode.REVERSE:
        _print_reverse_map(itinerary)
    elif itinerary.direction is DirectionMode.BOTH:
        _print_direction_comparison(itinerary)


@app.command
def optimize(
    *,
    profile: Annotated[
        Path | None,
        Parameter("--profile", help="Path to a JSON profile file."),
    ] = None,
) -> ExitCode:
    """Collect or load itinerary input for optimization.

    Parameters
    ----------
    profile:
        Optional path to a JSON itinerary profile.
    """
    if profile is None:
        itinerary = collect_itinerary()
    else:
        try:
            itinerary = load_profile(profile)
        except ProfileError as exc:
            console.print(f"[red]Error:[/red] {escape(str(exc))}")
            return ExitCode.USAGE

    logger.debug("loaded itinerary with %d destinations", len(itinerary.destinations))
    _print_itinerary(itinerary)
    _print_direction_resolution(itinerary)
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
