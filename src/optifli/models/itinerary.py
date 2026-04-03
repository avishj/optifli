# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Itinerary domain models."""

from pydantic import BaseModel

from optifli.models.airport import CityGroup
from optifli.models.duration import Duration
from optifli.models.window import ArrivalCutoff, DepartureWindow


class Destination(BaseModel, frozen=True):
    """A destination city with its stay duration.

    Attributes:
        city: The city group to visit.
        stay: How long to stay at this destination.
    """

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

    origin: CityGroup
    destination: CityGroup
    departure_window: DepartureWindow
    arrival_cutoff: ArrivalCutoff | None = None
