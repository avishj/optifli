# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thin wrapper around FLI's search client.

Provides a stable interface for Optifli to call FLI search without
leaking provider internals. Configurable retry/rate-limit behavior
is TBD — for now this delegates to FLI's built-in client defaults.
"""

import logging

from fli.models.google_flights.base import FlightResult
from fli.models.google_flights.flights import FlightSearchFilters
from fli.search.flights import SearchFlights

logger = logging.getLogger(__name__)


class FliClient:
    """Optifli's interface to the FLI search provider."""

    def __init__(self) -> None:
        """Initialise with FLI's default search client."""
        self._search = SearchFlights()

    def search(
        self,
        filters: FlightSearchFilters,
    ) -> list[FlightResult]:
        """Execute a one-way flight search and return results.

        Returns an empty list when the provider finds no inventory.
        """
        logger.debug(
            "FLI search: %s → %s on %s",
            filters.flight_segments[0].departure_airport,
            filters.flight_segments[0].arrival_airport,
            filters.flight_segments[0].travel_date,
        )
        raw = self._search.search(filters)
        if raw is None:
            return []
        # One-way searches return list[FlightResult] directly.
        return [r for r in raw if isinstance(r, FlightResult)]
