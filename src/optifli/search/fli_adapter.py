# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Adapter between FLI search results and Optifli-native models."""

import logging
from dataclasses import dataclass
from datetime import datetime

from fli.models.google_flights.base import FlightLeg, FlightResult
from fli.models.google_flights.flights import FlightSearchFilters

from optifli.search.fli_client import FliClient
from optifli.search.models import ApiFailureClassification

logger = logging.getLogger(__name__)

_RATE_LIMIT_FRAGMENTS = ("rate limit", "429", "too many requests")


@dataclass(frozen=True, slots=True)
class SegmentDetail:
    """One physical flight segment within a leg option."""

    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int


@dataclass(frozen=True, slots=True)
class LegOption:
    """A normalized flight option for one itinerary leg."""

    segments: tuple[SegmentDetail, ...]
    price: float
    currency: str | None
    total_duration_minutes: int
    stops: int


def normalize_leg(leg: FlightLeg) -> SegmentDetail:
    """Convert a single FLI ``FlightLeg`` into a ``SegmentDetail``."""
    return SegmentDetail(
        airline=leg.airline.name,
        flight_number=leg.flight_number,
        departure_airport=leg.departure_airport.name,
        arrival_airport=leg.arrival_airport.name,
        departure_time=leg.departure_datetime,
        arrival_time=leg.arrival_datetime,
        duration_minutes=leg.duration,
    )


def normalize_result(result: FlightResult) -> LegOption:
    """Convert a FLI ``FlightResult`` into an Optifli ``LegOption``."""
    return LegOption(
        segments=tuple(normalize_leg(leg) for leg in result.legs),
        price=result.price,
        currency=result.currency,
        total_duration_minutes=result.duration,
        stops=result.stops,
    )


def classify_error(exc: Exception) -> ApiFailureClassification:
    """Map a provider exception to an API failure classification."""
    message = str(exc).lower()
    if any(fragment in message for fragment in _RATE_LIMIT_FRAGMENTS):
        return ApiFailureClassification.RATE_LIMITED
    if "no results" in message or "no inventory" in message or "empty" in message:
        return ApiFailureClassification.NO_INVENTORY
    return ApiFailureClassification.UNKNOWN


@dataclass(frozen=True, slots=True)
class SearchResponse:
    """Outcome of a single adapter search call."""

    options: tuple[LegOption, ...]
    failure: ApiFailureClassification | None


class FliAdapter:
    """Wraps ``FliClient`` to produce normalized Optifli search results."""

    def __init__(self, client: FliClient | None = None) -> None:
        """Initialise with an optional ``FliClient`` (default creates one)."""
        self._client = client or FliClient()

    def search(self, filters: FlightSearchFilters) -> SearchResponse:
        """Execute a search and return normalized results or a failure."""
        try:
            raw = self._client.search(filters)
        except Exception as exc:  # noqa: BLE001 — FLI raises bare Exception
            classification = classify_error(exc)
            logger.warning("FLI search failed (%s): %s", classification, exc)
            return SearchResponse(options=(), failure=classification)

        if not raw:
            return SearchResponse(options=(), failure=None)

        options = tuple(normalize_result(r) for r in raw)
        logger.debug("FLI adapter returned %d option(s)", len(options))
        return SearchResponse(options=options, failure=None)
