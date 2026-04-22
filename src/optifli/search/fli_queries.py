# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Translate local query slices into FLI search filter objects."""

from math import ceil, floor

from fli.models.airport import Airport
from fli.models.google_flights.base import (
    FlightSegment,
    MaxStops,
    PassengerInfo,
    TimeRestrictions,
)
from fli.models.google_flights.flights import FlightSearchFilters

from optifli.search.models import StopMode
from optifli.search.windows import LocalQuerySlice

_MAX_DEPARTURE_HOUR = 24

_STOP_MODE_MAP: dict[StopMode, MaxStops] = {
    StopMode.NON_STOP: MaxStops.NON_STOP,
    StopMode.ONE_STOP: MaxStops.ONE_STOP_OR_FEWER,
}


def _encode_airport(code: str) -> list[Airport | int]:
    """Encode an IATA code into FLI's ``[Airport, 0]`` wire format."""
    return [Airport[code], 0]


def _build_time_restrictions(query_slice: LocalQuerySlice) -> TimeRestrictions | None:
    """Convert local departure bounds to FLI hour-of-day restrictions.

    Returns ``None`` when the slice covers a full day (no restriction needed).
    """
    start = query_slice.departure_start_local
    end = query_slice.departure_end_local

    earliest_hour = start.hour + start.minute / 60
    end_hour = end.hour + end.minute / 60

    # Full-day slice (00:00 → next midnight) needs no restriction.
    is_full_day = earliest_hour == 0 and end_hour == 0 and end.date() > start.date()
    if is_full_day:
        return None

    earliest = floor(earliest_hour)
    # Ceil and clamp to 24; end==midnight of next day means "up to 24".
    latest = ceil(end_hour) if end_hour > 0 else _MAX_DEPARTURE_HOUR

    if earliest == 0 and latest >= _MAX_DEPARTURE_HOUR:
        return None

    return TimeRestrictions(
        earliest_departure=earliest if earliest > 0 else None,
        latest_departure=latest if latest < _MAX_DEPARTURE_HOUR else None,
    )


def _build_flight_segment(
    query_slice: LocalQuerySlice,
    time_restrictions: TimeRestrictions | None,
) -> FlightSegment:
    """Build a single ``FlightSegment`` from a local query slice."""
    return FlightSegment(
        departure_airport=[
            _encode_airport(code) for code in query_slice.origin_airports
        ],
        arrival_airport=[
            _encode_airport(code) for code in query_slice.destination_airports
        ],
        travel_date=query_slice.travel_date.isoformat(),
        time_restrictions=time_restrictions,
    )


def build_search_filters(
    query_slice: LocalQuerySlice,
    stop_mode: StopMode,
) -> FlightSearchFilters:
    """Build a complete ``FlightSearchFilters`` for one query slice.

    The result is always a one-way, single-segment search with economy
    seating and one adult — matching per-leg search granularity.
    """
    time_restrictions = _build_time_restrictions(query_slice)
    segment = _build_flight_segment(query_slice, time_restrictions)
    return FlightSearchFilters(
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[segment],
        stops=_STOP_MODE_MAP[stop_mode],
    )
