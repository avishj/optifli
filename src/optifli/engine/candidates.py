# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Route candidate generation."""

import logging
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, model_validator

from optifli.engine.direction import expand_directions
from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.itinerary import (
    Destination,
    DirectionMode,
    Itinerary,
    Leg,
    RouteMode,
)
from optifli.models.window import DepartureWindow
from optifli.timezones import lookup_airport_timezone

logger = logging.getLogger(__name__)

_DEFAULT_TRAVEL_ESTIMATE = timedelta(hours=6)
_DEFAULT_WINDOW_WIDTH = timedelta(hours=24)


class RouteCandidate(BaseModel, frozen=True):
    """A generated route candidate for a single concrete direction.

    Attributes:
        direction: Always FORWARD or REVERSE (never BOTH).
        origin: Starting city group.
        destinations: Ordered destinations for this direction.
        return_city: City to return to at the end.
        legs: Computed legs with departure windows.
    """

    model_config = ConfigDict(extra="forbid")

    direction: DirectionMode
    origin: CityGroup
    destinations: list[Destination]
    return_city: CityGroup
    legs: list[Leg]

    @model_validator(mode="after")
    def _validate_direction_not_both(self) -> Self:
        if self.direction is DirectionMode.BOTH:
            msg = "'direction' must be FORWARD or REVERSE, not BOTH"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_legs_non_empty(self) -> Self:
        if not self.legs:
            msg = "'legs' must be non-empty"
            raise ValueError(msg)
        return self


def build_leg_sequence(
    origin: CityGroup,
    destinations: list[Destination],
    return_city: CityGroup,
) -> list[tuple[CityGroup, CityGroup]]:
    """Generate ordered (origin, destination) city-group pairs for a fixed-order route.

    For destinations ``[A, B, C]`` with origin *O* and return *R* the result is
    ``[(O, A), (A, B), (B, C), (C, R)]``.

    Args:
        origin: Starting city group.
        destinations: Ordered destinations to visit.
        return_city: City to return to at the end.

    Returns:
        A list of ``(from, to)`` city-group pairs.
    """
    stops: list[CityGroup] = [
        origin,
        *(dest.city for dest in destinations),
        return_city,
    ]
    return list(pairwise(stops))


def compute_first_window(
    departure_date: date,
    origin_timezone: ZoneInfo,
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> DepartureWindow:
    """Compute the departure window for the first leg from a calendar date.

    Args:
        departure_date: Trip start date.
        origin_timezone: IANA timezone for the origin city group.
        window_width: Width of the departure window.

    Returns:
        A TZ-aware ``DepartureWindow`` starting at origin-local midnight,
        converted to UTC.
    """
    start_local = datetime(
        departure_date.year,
        departure_date.month,
        departure_date.day,
        tzinfo=origin_timezone,
    )
    start = start_local.astimezone(UTC)
    return DepartureWindow(start=start, end=start + window_width)


def propagate_window(
    previous_window: DepartureWindow,
    stay: Duration,
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> DepartureWindow:
    """Compute the departure window for a subsequent leg.

    Next window start = ``previous_window.start + travel_estimate + stay``.

    Args:
        previous_window: The departure window of the preceding leg.
        stay: How long to stay at the preceding destination.
        travel_estimate: Estimated travel time for the preceding leg.
        window_width: Width of the new departure window.

    Returns:
        A TZ-aware ``DepartureWindow`` for the next leg.
    """
    start = previous_window.start + travel_estimate + stay.timedelta
    return DepartureWindow(start=start, end=start + window_width)


def propagate_all_windows(
    first_window: DepartureWindow,
    stays: list[Duration],
    leg_count: int,
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> list[DepartureWindow]:
    """Propagate departure windows for all legs from a trip start date.

    The first window is provided directly; each subsequent window
    is derived from the previous one plus a stay duration and travel estimate.

    ``stays`` has one entry per destination (N destinations produce N+1 legs).
    The final leg (return) has no preceding stay.

    Args:
        first_window: Departure window for the first leg.
        stays: Stay duration at each destination.
        leg_count: Total number of legs to generate windows for.
        travel_estimate: Estimated travel time per leg.
        window_width: Width of each departure window.

    Returns:
        A list of exactly *leg_count* ``DepartureWindow`` objects.
    """
    windows: list[DepartureWindow] = [
        first_window,
    ]
    for i in range(1, leg_count):
        stay = stays[i - 1]
        windows.append(
            propagate_window(windows[-1], stay, travel_estimate, window_width),
        )
    return windows


def _resolve_city_group_timezone(city_group: CityGroup) -> ZoneInfo:
    """Resolve the single timezone for a city group.

    The ``Itinerary`` model guarantees that date-only propagation is only
    used when the origin city group has one unambiguous timezone.
    """
    timezone_names = {
        lookup_airport_timezone(airport_code) for airport_code in city_group.airports
    }
    return ZoneInfo(next(iter(timezone_names)))


def validate_leg_consistency(
    legs: list[Leg],
    destinations: list[Destination],
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
) -> list[str]:
    """Check user-provided legs for scheduling consistency.

    Returns a list of warning strings (not errors — user windows take
    precedence).  An empty list means no warnings.

    Warnings are emitted only when the next departure window is impossible
    even under the most optimistic interpretation of the prior leg window:
    previous departure at window start, then estimated travel time and stay.

    Args:
        legs: User-provided legs with explicit departure windows.
        destinations: The ordered destinations (used for stay durations).
        travel_estimate: Estimated travel time per leg.

    Returns:
        A list of warning strings (empty if consistent).
    """
    warnings: list[str] = []
    for i in range(len(legs) - 1):
        if i < len(destinations):
            required = travel_estimate + destinations[i].stay.timedelta
        else:
            required = travel_estimate
        earliest_next_departure = legs[i].departure_window.start + required
        if legs[i + 1].departure_window.end < earliest_next_departure:
            warnings.append(
                f"Leg {i + 2} departure window ends before the earliest "
                f"estimated feasible departure ({earliest_next_departure})",
            )
    return warnings


def _format_city_group(city_group: CityGroup) -> str:
    return "/".join(city_group.airports)


def _same_city_group(left: CityGroup, right: CityGroup) -> bool:
    return set(left.airports) == set(right.airports)


def validate_explicit_leg_route_shape(
    legs: list[Leg],
    expected_pairs: list[tuple[CityGroup, CityGroup]],
) -> None:
    """Require explicit legs to cover the whole concrete route in order."""
    if len(legs) != len(expected_pairs):
        msg = (
            "Explicit legs must cover the full concrete route: "
            f"expected {len(expected_pairs)} leg(s), got {len(legs)}"
        )
        raise ValueError(msg)

    for index, (leg, (expected_origin, expected_destination)) in enumerate(
        zip(legs, expected_pairs, strict=True),
        start=1,
    ):
        if not _same_city_group(leg.origin, expected_origin) or not _same_city_group(
            leg.destination, expected_destination
        ):
            msg = (
                f"Explicit leg {index} must match the concrete route segment "
                f"{_format_city_group(expected_origin)} -> "
                f"{_format_city_group(expected_destination)}; got "
                f"{_format_city_group(leg.origin)} -> "
                f"{_format_city_group(leg.destination)}"
            )
            raise ValueError(msg)


def generate_candidates(
    itinerary: Itinerary,
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> list[RouteCandidate]:
    """Generate route candidates from an itinerary.

    Wires direction expansion, leg sequence building, and date propagation
    into ``RouteCandidate`` output.  When the itinerary carries explicit legs
    they are used directly; otherwise windows are propagated from
    ``departure_date``.

    Args:
        itinerary: The itinerary to generate candidates for.
        travel_estimate: Estimated travel time per leg.
        window_width: Width of each departure window.

    Returns:
        A list of ``RouteCandidate`` objects (one per concrete direction).
    """
    if itinerary.route_mode is RouteMode.REORDER:
        msg = (
            "'route_mode=reorder' is not yet supported. Use 'fixed' or omit route_mode."
        )
        raise ValueError(msg)
    expanded = expand_directions(itinerary)
    candidates: list[RouteCandidate] = []

    for direction, destinations in expanded:
        pairs = build_leg_sequence(
            itinerary.origin,
            destinations,
            itinerary.return_city,
        )
        if itinerary.legs:
            validate_explicit_leg_route_shape(itinerary.legs, pairs)
            legs = list(itinerary.legs)
            warnings = validate_leg_consistency(
                legs,
                destinations,
                travel_estimate,
            )
            for warning in warnings:
                logger.warning(warning)
        else:
            if itinerary.departure_date is None:
                msg = "'departure_date' is required when no explicit legs are provided"
                raise ValueError(msg)
            origin_timezone = _resolve_city_group_timezone(itinerary.origin)
            first_window = compute_first_window(
                itinerary.departure_date,
                origin_timezone,
                window_width,
            )
            stays = [d.stay for d in destinations]
            windows = propagate_all_windows(
                first_window,
                stays,
                leg_count=len(pairs),
                travel_estimate=travel_estimate,
                window_width=window_width,
            )
            legs = [
                Leg(
                    origin=orig,
                    destination=dest,
                    departure_window=window,
                )
                for (orig, dest), window in zip(pairs, windows, strict=True)
            ]

        candidates.append(
            RouteCandidate(
                direction=direction,
                origin=itinerary.origin,
                destinations=destinations,
                return_city=itinerary.return_city,
                legs=legs,
            ),
        )
        logger.debug(
            "Candidate %s: %d leg(s), windows %s → %s",
            direction.value,
            len(legs),
            legs[0].departure_window.start.isoformat(),
            legs[-1].departure_window.end.isoformat(),
        )

    directions_used = ", ".join(c.direction.value for c in candidates)
    logger.info(
        "Generated %d candidate(s) for direction(s): %s",
        len(candidates),
        directions_used,
    )

    return candidates
