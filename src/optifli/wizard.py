# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Interactive itinerary collection for the CLI."""

from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm, Prompt

from optifli.errors import InputError, format_errors, from_pydantic
from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.itinerary import Destination, DirectionMode, Itinerary, RouteMode

_MAX_DESTINATIONS = 10
_error_console = Console(stderr=True)


def _print_error(field: str, reason: str, hint: str = "") -> None:
    """Render a single actionable input error to stderr."""
    rendered = format_errors([InputError(field=field, reason=reason, hint=hint)])
    _error_console.print(rendered)


def _prompt_city(prompt_text: str) -> CityGroup:
    """Prompt until a single-airport city group validates."""
    while True:
        code = Prompt.ask(prompt_text)
        name = code.strip().upper()
        try:
            return CityGroup.model_validate({"name": name, "airports": [code]})
        except ValidationError as exc:
            reason = from_pydantic(exc)[0].reason
            _print_error(
                field=prompt_text,
                reason=reason,
                hint="Enter a 3-letter IATA airport code like DEL or HAN",
            )


def _prompt_duration(prompt_text: str) -> Duration:
    """Prompt until a stay duration validates."""
    while True:
        value = Prompt.ask(prompt_text)
        try:
            return Duration.model_validate(value)
        except ValidationError as exc:
            reason = from_pydantic(exc)[0].reason
            _print_error(
                field=prompt_text,
                reason=reason,
                hint="Use values like 2d, 1.5d, or 12h",
            )


def _prompt_direction_mode() -> DirectionMode:
    """Prompt until a valid direction mode is selected."""
    choices = [mode.value for mode in DirectionMode]
    while True:
        value = Prompt.ask(
            "Direction mode",
            choices=choices,
            default=DirectionMode.FORWARD.value,
        )
        value = value.strip().lower()
        try:
            return DirectionMode(value)
        except ValueError:
            _print_error(
                field="Direction mode",
                reason=f"'{value}' is not a valid direction mode",
                hint="Choose forward, reverse, or both",
            )


def _prompt_route_mode() -> RouteMode:
    """Prompt until a valid route mode is selected."""
    choices = [mode.value for mode in RouteMode]
    while True:
        value = Prompt.ask(
            "Route mode",
            choices=choices,
            default=RouteMode.FIXED.value,
        )
        value = value.strip().lower()
        try:
            return RouteMode(value)
        except ValueError:
            _print_error(
                field="Route mode",
                reason=f"'{value}' is not a valid route mode",
                hint="Choose fixed or reorder",
            )


def _prompt_destination(index: int) -> Destination:
    """Prompt for one destination and stay duration."""
    city = _prompt_city(f"Destination {index} airport code")
    stay = _prompt_duration(f"Destination {index} stay duration")
    return Destination(city=city, stay=stay)


def collect_itinerary() -> Itinerary:
    """Collect a basic itinerary interactively.

    The wizard currently models each prompted airport as a single-airport city group.
    """
    origin = _prompt_city("Origin airport code")
    destinations = [_prompt_destination(1)]

    while len(destinations) < _MAX_DESTINATIONS and Confirm.ask(
        "Add another destination?",
        default=False,
    ):
        destinations.append(_prompt_destination(len(destinations) + 1))

    return_city = _prompt_city("Return airport code")
    direction = _prompt_direction_mode()
    route_mode = _prompt_route_mode()

    return Itinerary(
        origin=origin,
        destinations=destinations,
        return_city=return_city,
        direction=direction,
        route_mode=route_mode,
    )
