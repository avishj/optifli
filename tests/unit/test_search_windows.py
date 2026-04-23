# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for departure-window slicing and timezone grouping."""

from datetime import datetime, time, timedelta
from itertools import pairwise
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from optifli.models.airport import CityGroup
from optifli.models.itinerary import Leg
from optifli.models.window import DepartureWindow
from optifli.search.windows import (
    LocalQuerySlice,
    build_local_query_slices,
    group_airports_by_timezone,
    split_window_by_local_date,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

TZ_KOLKATA = ZoneInfo("Asia/Kolkata")
TZ_TOKYO = ZoneInfo("Asia/Tokyo")
TZ_UTC = ZoneInfo("UTC")


def _city(name: str, *codes: str) -> CityGroup:
    return CityGroup(name=name, airports=list(codes))


def _window(start: datetime, end: datetime) -> DepartureWindow:
    return DepartureWindow(start=start, end=end)


def _leg(
    origin: CityGroup,
    destination: CityGroup,
    start: datetime,
    end: datetime,
) -> Leg:
    return Leg(
        origin=origin,
        destination=destination,
        departure_window=_window(start, end),
    )


# ---------------------------------------------------------------------------
# LocalQuerySlice validation
# ---------------------------------------------------------------------------


class TestLocalQuerySliceValidation:
    def test_valid_same_day_slice(self):
        dt = datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA)
        s = LocalQuerySlice(
            origin_airports=["DEL"],
            destination_airports=["HAN"],
            origin_timezone="Asia/Kolkata",
            travel_date=dt.date(),
            departure_start_local=dt,
            departure_end_local=dt.replace(hour=23, minute=59, second=59),
        )
        assert s.travel_date == dt.date()

    def test_rejects_empty_origin_airports(self):
        dt = datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA)
        with pytest.raises(ValidationError, match="origin_airports"):
            LocalQuerySlice(
                origin_airports=[],
                destination_airports=["HAN"],
                origin_timezone="Asia/Kolkata",
                travel_date=dt.date(),
                departure_start_local=dt,
                departure_end_local=dt.replace(hour=14),
            )

    def test_rejects_empty_destination_airports(self):
        dt = datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA)
        with pytest.raises(ValidationError, match="destination_airports"):
            LocalQuerySlice(
                origin_airports=["DEL"],
                destination_airports=[],
                origin_timezone="Asia/Kolkata",
                travel_date=dt.date(),
                departure_start_local=dt,
                departure_end_local=dt.replace(hour=14),
            )

    def test_rejects_naive_start(self):
        aware = datetime(2026, 7, 16, 14, 0, tzinfo=TZ_KOLKATA)
        with pytest.raises(ValidationError, match="timezone-aware"):
            LocalQuerySlice(
                origin_airports=["DEL"],
                destination_airports=["HAN"],
                origin_timezone="Asia/Kolkata",
                travel_date=aware.date(),
                departure_start_local=aware.replace(tzinfo=None),
                departure_end_local=aware,
            )

    def test_rejects_start_not_before_end(self):
        dt = datetime(2026, 7, 16, 14, 0, tzinfo=TZ_KOLKATA)
        with pytest.raises(ValidationError, match="before"):
            LocalQuerySlice(
                origin_airports=["DEL"],
                destination_airports=["HAN"],
                origin_timezone="Asia/Kolkata",
                travel_date=dt.date(),
                departure_start_local=dt,
                departure_end_local=dt,
            )

    def test_cross_day_must_end_at_midnight(self):
        start = datetime(2026, 7, 16, 22, 0, tzinfo=TZ_KOLKATA)
        bad_end = datetime(2026, 7, 17, 2, 0, tzinfo=TZ_KOLKATA)
        with pytest.raises(ValidationError, match="midnight"):
            LocalQuerySlice(
                origin_airports=["DEL"],
                destination_airports=["HAN"],
                origin_timezone="Asia/Kolkata",
                travel_date=start.date(),
                departure_start_local=start,
                departure_end_local=bad_end,
            )

    def test_cross_day_ending_at_midnight_accepted(self):
        start = datetime(2026, 7, 16, 22, 0, tzinfo=TZ_KOLKATA)
        midnight = datetime.combine(
            start.date() + timedelta(days=1), time.min, tzinfo=TZ_KOLKATA
        )
        s = LocalQuerySlice(
            origin_airports=["DEL"],
            destination_airports=["HAN"],
            origin_timezone="Asia/Kolkata",
            travel_date=start.date(),
            departure_start_local=start,
            departure_end_local=midnight,
        )
        assert s.departure_end_local == midnight


# ---------------------------------------------------------------------------
# group_airports_by_timezone
# ---------------------------------------------------------------------------


class TestGroupAirportsByTimezone:
    def test_single_timezone(self):
        city = _city("Delhi", "DEL")
        groups = group_airports_by_timezone(city)
        assert groups == {"Asia/Kolkata": ["DEL"]}

    def test_multiple_airports_same_timezone(self):
        city = _city("Tokyo", "NRT", "HND")
        groups = group_airports_by_timezone(city)
        assert groups == {"Asia/Tokyo": ["NRT", "HND"]}

    def test_airports_across_timezones(self):
        city = _city("Multi", "DEL", "NRT")
        groups = group_airports_by_timezone(city)
        assert set(groups.keys()) == {"Asia/Kolkata", "Asia/Tokyo"}
        assert groups["Asia/Kolkata"] == ["DEL"]
        assert groups["Asia/Tokyo"] == ["NRT"]

    def test_result_is_sorted_by_timezone(self):
        city = _city("Multi", "NRT", "DEL")
        groups = group_airports_by_timezone(city)
        assert list(groups.keys()) == sorted(groups.keys())


# ---------------------------------------------------------------------------
# split_window_by_local_date
# ---------------------------------------------------------------------------


class TestSplitWindowByLocalDate:
    def test_single_day_produces_one_slice(self):
        origin = _city("Delhi", "DEL")
        dest = _city("Hanoi", "HAN")
        start = datetime(2026, 7, 16, 10, 0, tzinfo=TZ_KOLKATA)
        end = datetime(2026, 7, 16, 18, 0, tzinfo=TZ_KOLKATA)
        leg = _leg(origin, dest, start, end)

        slices = split_window_by_local_date(
            leg, origin_airports=["DEL"], origin_timezone="Asia/Kolkata"
        )

        assert len(slices) == 1
        assert slices[0].travel_date == start.date()
        assert slices[0].departure_start_local == start
        assert slices[0].departure_end_local == end

    def test_cross_day_produces_two_slices(self):
        origin = _city("Delhi", "DEL")
        dest = _city("Hanoi", "HAN")
        start = datetime(2026, 7, 16, 22, 0, tzinfo=TZ_KOLKATA)
        end = datetime(2026, 7, 17, 4, 0, tzinfo=TZ_KOLKATA)
        leg = _leg(origin, dest, start, end)

        slices = split_window_by_local_date(
            leg, origin_airports=["DEL"], origin_timezone="Asia/Kolkata"
        )

        assert len(slices) == 2
        # first slice: 22:00 → midnight
        assert slices[0].travel_date == start.date()
        assert slices[0].departure_start_local == start
        assert slices[0].departure_end_local.timetz() == time.min
        # second slice: midnight → 04:00
        assert slices[1].travel_date == end.date()
        assert slices[1].departure_end_local == end

    def test_utc_window_converted_to_local(self):
        origin = _city("Delhi", "DEL")
        dest = _city("Hanoi", "HAN")
        # 18:00 UTC = 23:30 Kolkata, 20:00 UTC = 01:30 Kolkata next day
        start_utc = datetime(2026, 7, 16, 18, 0, tzinfo=TZ_UTC)
        end_utc = datetime(2026, 7, 16, 20, 0, tzinfo=TZ_UTC)
        leg = _leg(origin, dest, start_utc, end_utc)

        slices = split_window_by_local_date(
            leg, origin_airports=["DEL"], origin_timezone="Asia/Kolkata"
        )

        # Kolkata is UTC+5:30, so the window spans 23:30 to 01:30 → two dates
        assert len(slices) == 2
        local_start = slices[0].departure_start_local
        assert local_start.hour == 23
        assert local_start.minute == 30

    def test_slices_preserve_airports(self):
        origin = _city("Tokyo", "NRT", "HND")
        dest = _city("Delhi", "DEL")
        start = datetime(2026, 7, 16, 10, 0, tzinfo=TZ_TOKYO)
        end = datetime(2026, 7, 16, 18, 0, tzinfo=TZ_TOKYO)
        leg = _leg(origin, dest, start, end)

        slices = split_window_by_local_date(
            leg, origin_airports=["NRT", "HND"], origin_timezone="Asia/Tokyo"
        )

        assert slices[0].origin_airports == ["NRT", "HND"]
        assert slices[0].destination_airports == ["DEL"]

    def test_slices_are_contiguous(self):
        origin = _city("Delhi", "DEL")
        dest = _city("Hanoi", "HAN")
        start = datetime(2026, 7, 16, 20, 0, tzinfo=TZ_KOLKATA)
        end = datetime(2026, 7, 17, 6, 0, tzinfo=TZ_KOLKATA)
        leg = _leg(origin, dest, start, end)

        slices = split_window_by_local_date(
            leg, origin_airports=["DEL"], origin_timezone="Asia/Kolkata"
        )

        for prev_slice, next_slice in pairwise(slices):
            assert prev_slice.departure_end_local == next_slice.departure_start_local


# ---------------------------------------------------------------------------
# build_local_query_slices  (integration of grouping + splitting)
# ---------------------------------------------------------------------------


class TestBuildLocalQuerySlices:
    def test_single_tz_single_day(self):
        origin = _city("Delhi", "DEL")
        dest = _city("Hanoi", "HAN")
        start = datetime(2026, 7, 16, 8, 0, tzinfo=TZ_KOLKATA)
        end = datetime(2026, 7, 16, 20, 0, tzinfo=TZ_KOLKATA)
        leg = _leg(origin, dest, start, end)

        slices = build_local_query_slices(leg)

        assert len(slices) == 1
        assert slices[0].origin_timezone == "Asia/Kolkata"

    def test_multi_tz_origin_produces_separate_groups(self):
        origin = _city("Mixed", "DEL", "NRT")
        dest = _city("Singapore", "SIN")
        # Window that fits in a single day in both Kolkata and Tokyo
        start_utc = datetime(2026, 7, 16, 4, 0, tzinfo=TZ_UTC)
        end_utc = datetime(2026, 7, 16, 8, 0, tzinfo=TZ_UTC)
        leg = _leg(origin, dest, start_utc, end_utc)

        slices = build_local_query_slices(leg)

        timezones = {s.origin_timezone for s in slices}
        assert "Asia/Kolkata" in timezones
        assert "Asia/Tokyo" in timezones

    def test_deterministic_ordering(self):
        origin = _city("Mixed", "NRT", "DEL")
        dest = _city("Singapore", "SIN")
        start_utc = datetime(2026, 7, 16, 4, 0, tzinfo=TZ_UTC)
        end_utc = datetime(2026, 7, 16, 8, 0, tzinfo=TZ_UTC)
        leg = _leg(origin, dest, start_utc, end_utc)

        first = build_local_query_slices(leg)
        second = build_local_query_slices(leg)

        assert first == second
