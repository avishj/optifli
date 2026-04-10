# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Reverse-mode duration remap logic."""

from optifli.models.duration import Duration
from optifli.models.itinerary import Destination, Itinerary


def remap_for_reverse(itinerary: Itinerary) -> list[Destination]:
    """Reverse destination order, keeping durations attached to their cities.

    Args:
        itinerary: The itinerary whose destinations to reverse.

    Returns:
        Destinations in reversed order with original city-duration pairings.
    """
    return list(reversed(itinerary.destinations))


def apply_overrides(
    destinations: list[Destination],
    overrides: dict[str, Duration],
) -> list[Destination]:
    """Apply per-city duration overrides to a destination list.

    Args:
        destinations: The base destination list.
        overrides: Mapping of city name to replacement duration.

    Returns:
        New destination list with overridden durations where applicable.

    Raises:
        ValueError: If an override key doesn't match any destination city.
    """
    city_names = {d.city.name for d in destinations}
    unknown = set(overrides.keys()) - city_names
    if unknown:
        sorted_unknown = ", ".join(sorted(unknown))
        msg = f"Override cities not found in destinations: {sorted_unknown}"
        raise ValueError(msg)

    return [
        Destination(city=d.city, stay=overrides[d.city.name])
        if d.city.name in overrides
        else d
        for d in destinations
    ]
