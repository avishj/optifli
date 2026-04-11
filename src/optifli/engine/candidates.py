# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Route candidate generation."""

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.itinerary import Destination, DirectionMode, Leg
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
