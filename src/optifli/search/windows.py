# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Helpers for splitting leg departure windows into provider-local query slices."""

from datetime import date, datetime, time, timedelta
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, model_validator

from optifli.models.airport import CityGroup, IATACode
from optifli.models.itinerary import Leg
from optifli.timezones import lookup_airport_timezone


def _midnight(day: date, timezone: ZoneInfo) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone)


class LocalQuerySlice(BaseModel, frozen=True):
    """A single provider-local date slice for one leg search."""

    model_config = ConfigDict(extra="forbid")

    origin_airports: list[IATACode]
    destination_airports: list[IATACode]
    origin_timezone: str
    travel_date: date
    departure_start_local: datetime
    departure_end_local: datetime

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        if not self.origin_airports:
            msg = "'origin_airports' must contain at least one airport"
            raise ValueError(msg)
        if not self.destination_airports:
            msg = "'destination_airports' must contain at least one airport"
            raise ValueError(msg)
        start = self.departure_start_local
        end = self.departure_end_local
        if start.tzinfo is None or start.utcoffset() is None:
            msg = "'departure_start_local' must be timezone-aware"
            raise ValueError(msg)
        if end.tzinfo is None or end.utcoffset() is None:
            msg = "'departure_end_local' must be timezone-aware"
            raise ValueError(msg)
        if start >= end:
            msg = "'departure_start_local' must be before 'departure_end_local'"
            raise ValueError(msg)
        if start.date() != self.travel_date or end.date() not in {
            self.travel_date,
            self.travel_date + timedelta(days=1),
        }:
            msg = "Local slice bounds must align to the declared travel_date"
            raise ValueError(msg)
        if end.date() != self.travel_date and end.time() != time.min:
            msg = "Cross-day local slices must end exactly at next local midnight"
            raise ValueError(msg)
        return self


def group_airports_by_timezone(city_group: CityGroup) -> dict[str, list[IATACode]]:
    """Group airports in a city group by IANA timezone name."""
    groups: dict[str, list[IATACode]] = {}
    for airport_code in city_group.airports:
        timezone_name = lookup_airport_timezone(airport_code)
        groups.setdefault(timezone_name, []).append(airport_code)
    return dict(sorted(groups.items()))


def split_window_by_local_date(
    leg: Leg,
    *,
    origin_airports: list[IATACode],
    origin_timezone: str,
) -> list[LocalQuerySlice]:
    """Split a leg's UTC window into one or more origin-local date slices."""
    timezone = ZoneInfo(origin_timezone)
    local_start = leg.departure_window.start.astimezone(timezone)
    local_end = leg.departure_window.end.astimezone(timezone)

    slices: list[LocalQuerySlice] = []
    cursor = local_start
    while cursor < local_end:
        next_midnight = _midnight(cursor.date() + timedelta(days=1), timezone)
        slice_end = min(next_midnight, local_end)
        slices.append(
            LocalQuerySlice(
                origin_airports=origin_airports,
                destination_airports=leg.destination.airports,
                origin_timezone=origin_timezone,
                travel_date=cursor.date(),
                departure_start_local=cursor,
                departure_end_local=slice_end,
            ),
        )
        cursor = slice_end
    return slices


def build_local_query_slices(leg: Leg) -> list[LocalQuerySlice]:
    """Build deterministic provider-local slices for one itinerary leg."""
    slices: list[LocalQuerySlice] = []
    for timezone_name, airports in group_airports_by_timezone(leg.origin).items():
        slices.extend(
            split_window_by_local_date(
                leg,
                origin_airports=airports,
                origin_timezone=timezone_name,
            ),
        )
    return slices
