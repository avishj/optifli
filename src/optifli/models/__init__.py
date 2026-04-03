# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Domain models for optifli."""

from optifli.models.airport import CityGroup, IATACode
from optifli.models.duration import Duration
from optifli.models.itinerary import (
    Destination,
    DirectionMode,
    Itinerary,
    Leg,
    RouteMode,
)
from optifli.models.remap import apply_overrides, remap_for_reverse

__all__ = [
    "CityGroup",
    "Destination",
    "DirectionMode",
    "Duration",
    "IATACode",
    "Itinerary",
    "Leg",
    "RouteMode",
    "apply_overrides",
    "remap_for_reverse",
]
