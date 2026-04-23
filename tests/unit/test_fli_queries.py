# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for FLI query object construction."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from fli.models.airport import Airport
from fli.models.google_flights.base import MaxStops, TripType

from optifli.search.fli_queries import (
    _build_time_restrictions,
    _encode_airport,
    build_search_filters,
)
from optifli.search.models import StopMode
from optifli.search.windows import LocalQuerySlice

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared constants and factories
# ---------------------------------------------------------------------------

TZ_KOLKATA = ZoneInfo("Asia/Kolkata")
TZ_TOKYO = ZoneInfo("Asia/Tokyo")


_SLICE_DEFAULTS: dict = {
    "origin_airports": ["DEL"],
    "destination_airports": ["HAN"],
    "origin_timezone": "Asia/Kolkata",
    "travel_date": date(2026, 7, 16),
    "departure_start_local": datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA),
    "departure_end_local": datetime(2026, 7, 16, 18, 0, tzinfo=TZ_KOLKATA),
}


def _slice(**overrides: object) -> LocalQuerySlice:
    """Build a ``LocalQuerySlice`` with sensible defaults."""
    return LocalQuerySlice(**{**_SLICE_DEFAULTS, **overrides})


# ---------------------------------------------------------------------------
# _encode_airport
# ---------------------------------------------------------------------------


class TestEncodeAirport:
    def test_returns_airport_enum_with_zero(self):
        result = _encode_airport("DEL")
        assert result == [Airport.DEL, 0]

    def test_different_airport(self):
        result = _encode_airport("JFK")
        assert result == [Airport.JFK, 0]


# ---------------------------------------------------------------------------
# _build_time_restrictions
# ---------------------------------------------------------------------------


class TestBuildTimeRestrictions:
    def test_mid_day_window(self):
        s = _slice(
            departure_start_local=datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime(2026, 7, 16, 18, 0, tzinfo=TZ_KOLKATA),
        )
        tr = _build_time_restrictions(s)
        assert tr is not None
        assert tr.earliest_departure == 10
        assert tr.latest_departure == 18

    def test_full_day_returns_none(self):
        day = date(2026, 7, 16)
        s = _slice(
            departure_start_local=datetime.combine(day, time.min, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime.combine(
                day + timedelta(days=1), time.min, tzinfo=TZ_KOLKATA
            ),
        )
        assert _build_time_restrictions(s) is None

    def test_start_at_midnight_only_sets_latest(self):
        s = _slice(
            departure_start_local=datetime(2026, 7, 16, 0, 0, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime(2026, 7, 16, 14, 0, tzinfo=TZ_KOLKATA),
        )
        tr = _build_time_restrictions(s)
        assert tr is not None
        assert tr.earliest_departure is None
        assert tr.latest_departure == 14

    def test_end_at_midnight_only_sets_earliest(self):
        day = date(2026, 7, 16)
        s = _slice(
            travel_date=day,
            departure_start_local=datetime(2026, 7, 16, 20, 0, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime.combine(
                day + timedelta(days=1), time.min, tzinfo=TZ_KOLKATA
            ),
        )
        tr = _build_time_restrictions(s)
        assert tr is not None
        assert tr.earliest_departure == 20
        assert tr.latest_departure is None

    def test_fractional_start_floors(self):
        s = _slice(
            departure_start_local=datetime(2026, 7, 16, 10, 30, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime(2026, 7, 16, 18, 0, tzinfo=TZ_KOLKATA),
        )
        tr = _build_time_restrictions(s)
        assert tr is not None
        assert tr.earliest_departure == 10

    def test_fractional_end_ceils(self):
        s = _slice(
            departure_start_local=datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime(2026, 7, 16, 17, 15, tzinfo=TZ_KOLKATA),
        )
        tr = _build_time_restrictions(s)
        assert tr is not None
        assert tr.latest_departure == 18


# ---------------------------------------------------------------------------
# build_search_filters
# ---------------------------------------------------------------------------


class TestBuildSearchFilters:
    def test_one_way_trip_type(self):
        filters = build_search_filters(_slice(), StopMode.NON_STOP)
        assert filters.trip_type is TripType.ONE_WAY

    def test_single_segment(self):
        filters = build_search_filters(_slice(), StopMode.NON_STOP)
        assert len(filters.flight_segments) == 1

    def test_non_stop_maps_correctly(self):
        filters = build_search_filters(_slice(), StopMode.NON_STOP)
        assert filters.stops is MaxStops.NON_STOP

    def test_one_stop_maps_correctly(self):
        filters = build_search_filters(_slice(), StopMode.ONE_STOP)
        assert filters.stops is MaxStops.ONE_STOP_OR_FEWER

    def test_travel_date_matches_slice(self):
        s = _slice()
        filters = build_search_filters(s, StopMode.NON_STOP)
        segment = filters.flight_segments[0]
        assert segment.travel_date == s.travel_date.isoformat()

    def test_departure_airports_encoded(self):
        s = _slice(origin_airports=["DEL", "BOM"])
        filters = build_search_filters(s, StopMode.NON_STOP)
        segment = filters.flight_segments[0]
        assert segment.departure_airport == [
            [Airport.DEL, 0],
            [Airport.BOM, 0],
        ]

    def test_arrival_airports_encoded(self):
        s = _slice(destination_airports=["NRT", "HND"])
        filters = build_search_filters(s, StopMode.NON_STOP)
        segment = filters.flight_segments[0]
        assert segment.arrival_airport == [
            [Airport.NRT, 0],
            [Airport.HND, 0],
        ]

    def test_time_restrictions_propagated(self):
        s = _slice(
            departure_start_local=datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime(2026, 7, 16, 18, 0, tzinfo=TZ_KOLKATA),
        )
        filters = build_search_filters(s, StopMode.NON_STOP)
        tr = filters.flight_segments[0].time_restrictions
        assert tr is not None
        assert tr.earliest_departure == 10
        assert tr.latest_departure == 18

    def test_full_day_has_no_time_restrictions(self):
        day = date(2026, 7, 16)
        s = _slice(
            departure_start_local=datetime.combine(day, time.min, tzinfo=TZ_KOLKATA),
            departure_end_local=datetime.combine(
                day + timedelta(days=1), time.min, tzinfo=TZ_KOLKATA
            ),
        )
        filters = build_search_filters(s, StopMode.NON_STOP)
        assert filters.flight_segments[0].time_restrictions is None

    def test_default_passenger_info(self):
        filters = build_search_filters(_slice(), StopMode.NON_STOP)
        assert filters.passenger_info.adults == 1
        assert filters.passenger_info.children == 0
