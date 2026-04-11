# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Route candidate generation."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from optifli.models.airport import CityGroup
from optifli.models.itinerary import Destination, DirectionMode, Leg


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
