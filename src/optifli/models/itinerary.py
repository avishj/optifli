# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Itinerary domain models."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator

from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.window import ArrivalCutoff, DepartureWindow
from optifli.timezones import lookup_airport_timezone


class DirectionMode(StrEnum):
    """Which direction(s) to search the itinerary.

    Attributes:
        FORWARD: Search in the given destination order.
        REVERSE: Search in reversed destination order.
        BOTH: Search both forward and reverse orders.
    """

    FORWARD = "forward"
    REVERSE = "reverse"
    BOTH = "both"


class RouteMode(StrEnum):
    """Whether destination order is fixed or may be reordered.

    Attributes:
        FIXED: Keep destinations in the given order.
        REORDER: Allow the optimizer to reorder destinations.
    """

    FIXED = "fixed"
    REORDER = "reorder"


class Destination(BaseModel, frozen=True):
    """A destination city with its stay duration.

    Attributes:
        city: The city group to visit.
        stay: How long to stay at this destination.
    """

    model_config = ConfigDict(extra="forbid")

    city: CityGroup
    stay: Duration


class Leg(BaseModel, frozen=True):
    """One flight segment between two city groups.

    Attributes:
        origin: Departure city group.
        destination: Arrival city group.
        departure_window: When the flight should depart.
        arrival_cutoff: Optional upper-bound arrival time.
    """

    model_config = ConfigDict(extra="forbid")

    origin: CityGroup
    destination: CityGroup
    departure_window: DepartureWindow
    arrival_cutoff: ArrivalCutoff | None = None

    @model_validator(mode="after")
    def _validate_different_cities(self) -> Self:
        if self.origin.airports == self.destination.airports:
            msg = "Leg origin and destination must differ"
            raise ValueError(msg)
        return self


MAX_DESTINATIONS = 10


class Itinerary(BaseModel, frozen=True):
    """The full itinerary container.

    Attributes:
        origin: Starting city group.
        destinations: Cities to visit (1-10).
        return_city: City to return to at the end.
        direction: Search direction mode.
        route_mode: Whether destination order is fixed or reorderable.
        legs: Explicit per-leg departure windows (optional).
        departure_date: Trip start date (required when no explicit legs).
    """

    model_config = ConfigDict(extra="forbid")

    origin: CityGroup
    destinations: list[Destination]
    return_city: CityGroup
    direction: Annotated[DirectionMode, BeforeValidator(str.lower)] = (
        DirectionMode.FORWARD
    )
    route_mode: Annotated[RouteMode, BeforeValidator(str.lower)] = RouteMode.FIXED
    legs: list[Leg] = []
    departure_date: date | None = None

    @model_validator(mode="after")
    def _validate_destinations(self) -> Self:
        count = len(self.destinations)
        if count < 1:
            msg = "'destinations' must contain at least one destination"
            raise ValueError(msg)
        if count > MAX_DESTINATIONS:
            msg = (
                f"'destinations' must contain at most "
                f"{MAX_DESTINATIONS} destinations, got {count}"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_departure_date_required(self) -> Self:
        if not self.legs and self.departure_date is None:
            msg = "'departure_date' is required when no explicit legs are provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_reorder_no_legs(self) -> Self:
        if self.route_mode is RouteMode.REORDER and self.legs:
            msg = "'route_mode' cannot be 'reorder' when explicit legs are provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_origin_single_timezone(self) -> Self:
        if self.departure_date is None or self.legs:
            return self
        timezone_names = {
            lookup_airport_timezone(code) for code in self.origin.airports
        }
        if len(timezone_names) != 1:
            joined = ", ".join(sorted(timezone_names))
            msg = (
                f"Cannot use 'departure_date' with origin city group "
                f"'{self.origin.name}' because its airports span multiple "
                f"timezones ({joined}). Provide explicit legs instead."
            )
            raise ValueError(msg)
        return self
