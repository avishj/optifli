# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Itinerary domain models."""

from pydantic import BaseModel

from optifli.models.airport import CityGroup
from optifli.models.duration import Duration


class Destination(BaseModel, frozen=True):
    """A destination city with its stay duration.

    Attributes:
        city: The city group to visit.
        stay: How long to stay at this destination.
    """

    city: CityGroup
    stay: Duration
