# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Route candidate generation."""

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from optifli.engine.direction import expand_directions
from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.itinerary import Destination, DirectionMode, Itinerary, Leg
from optifli.models.window import DepartureWindow

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
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> DepartureWindow:
    """Compute the departure window for the first leg from a calendar date.

    Args:
        departure_date: Trip start date.
        window_width: Width of the departure window.

    Returns:
        A TZ-aware ``DepartureWindow`` starting at midnight UTC.
    """
    start = datetime(
        departure_date.year,
        departure_date.month,
        departure_date.day,
        tzinfo=UTC,
    )
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
    departure_date: date,
    stays: list[Duration],
    leg_count: int,
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
    window_width: timedelta = _DEFAULT_WINDOW_WIDTH,
) -> list[DepartureWindow]:
    """Propagate departure windows for all legs from a trip start date.

    The first window is computed from *departure_date*; each subsequent window
    is derived from the previous one plus a stay duration and travel estimate.

    ``stays`` has one entry per destination (N destinations produce N+1 legs).
    The final leg (return) has no preceding stay.

    Args:
        departure_date: Trip start date.
        stays: Stay duration at each destination.
        leg_count: Total number of legs to generate windows for.
        travel_estimate: Estimated travel time per leg.
        window_width: Width of each departure window.

    Returns:
        A list of exactly *leg_count* ``DepartureWindow`` objects.
    """
    windows: list[DepartureWindow] = [
        compute_first_window(departure_date, window_width),
    ]
    for i in range(1, leg_count):
        stay = stays[i - 1]
        windows.append(
            propagate_window(windows[-1], stay, travel_estimate, window_width),
        )
    return windows


def validate_leg_consistency(
    legs: list[Leg],
    destinations: list[Destination],
    travel_estimate: timedelta = _DEFAULT_TRAVEL_ESTIMATE,
) -> list[str]:
    """Check user-provided legs for scheduling consistency.

    Returns a list of warning strings (not errors — user windows take
    precedence).  An empty list means no warnings.

    Warnings are emitted when the gap between one leg's end and the next
    leg's start is shorter than the expected stay + travel time, or when
    legs overlap.

    Args:
        legs: User-provided legs with explicit departure windows.
        destinations: The ordered destinations (used for stay durations).
        travel_estimate: Estimated travel time per leg.

    Returns:
        A list of warning strings (empty if consistent).
    """
    warnings: list[str] = []
    for i in range(len(legs) - 1):
        gap = legs[i + 1].departure_window.start - legs[i].departure_window.end
        if i < len(destinations):
            required = travel_estimate + destinations[i].stay.timedelta
        else:
            required = travel_estimate
        if gap < timedelta(0):
            warnings.append(
                f"Leg {i + 1} and leg {i + 2} have overlapping departure windows",
            )
        elif gap < required:
            warnings.append(
                f"Gap between leg {i + 1} and leg {i + 2} "
                f"({gap}) is shorter than stay + travel estimate ({required})",
            )
    return warnings


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
    expanded = expand_directions(itinerary)
    candidates: list[RouteCandidate] = []

    for direction, destinations in expanded:
        if itinerary.legs:
            legs = list(itinerary.legs)
        else:
            pairs = build_leg_sequence(
                itinerary.origin,
                destinations,
                itinerary.return_city,
            )
            stays = [d.stay for d in destinations]
            windows = propagate_all_windows(
                itinerary.departure_date,  # type: ignore[arg-type]
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

    return candidates
