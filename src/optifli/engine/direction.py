# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Direction expansion for itinerary routing."""

from optifli.models.itinerary import Destination, DirectionMode, Itinerary


def expand_directions(
    itinerary: Itinerary,
) -> list[tuple[DirectionMode, list[Destination]]]:
    """Expand an itinerary's direction mode into concrete destination orderings.

    For ``FORWARD``, returns the destinations as-is.
    For ``REVERSE``, returns the destinations in reversed order.
    For ``BOTH``, returns two entries — forward first, then reverse.

    Args:
        itinerary: The itinerary to expand.

    Returns:
        A list of ``(direction, destinations)`` pairs.
    """
    if itinerary.direction is DirectionMode.FORWARD:
        return [(DirectionMode.FORWARD, list(itinerary.destinations))]

    msg = f"Direction mode {itinerary.direction!r} not yet supported"
    raise NotImplementedError(msg)
