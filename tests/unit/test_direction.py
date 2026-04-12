# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for direction expansion."""

from datetime import date

import pytest

from optifli.engine.direction import expand_directions
from optifli.models.itinerary import DirectionMode, Itinerary

pytestmark = pytest.mark.unit

_DELHI = {"name": "Delhi", "airports": ["DEL"]}
_HANOI = {"name": "Hanoi", "airports": ["HAN"]}
_DANANG = {"name": "Da Nang", "airports": ["DAD"]}
_SINGAPORE = {"name": "Singapore", "airports": ["SIN"]}


def _dest(city, stay="2d"):
    return {"city": city, "stay": stay}


def _make_itinerary(destinations, direction=DirectionMode.FORWARD):
    return Itinerary(
        origin=_DELHI,
        destinations=destinations,
        return_city=_DELHI,
        departure_date=date(2026, 7, 16),
        direction=direction,
    )


class TestExpandDirectionsForward:
    def test_single_entry_returned(self):
        it = _make_itinerary([_dest(_HANOI)])
        result = expand_directions(it)
        assert len(result) == 1
        assert result[0][0] is DirectionMode.FORWARD

    def test_destinations_unchanged(self):
        it = _make_itinerary([_dest(_HANOI), _dest(_DANANG), _dest(_SINGAPORE)])
        result = expand_directions(it)
        cities = [d.city.airports[0] for d in result[0][1]]
        assert cities == ["HAN", "DAD", "SIN"]

    def test_order_preserved(self):
        it = _make_itinerary([_dest(_SINGAPORE, "1d"), _dest(_HANOI, "3d")])
        result = expand_directions(it)
        stays = [d.stay.total_days for d in result[0][1]]
        assert stays == [1.0, 3.0]


class TestExpandDirectionsReverse:
    def test_reversed_order(self):
        it = _make_itinerary(
            [_dest(_HANOI), _dest(_DANANG), _dest(_SINGAPORE)],
            direction=DirectionMode.REVERSE,
        )
        result = expand_directions(it)
        assert len(result) == 1
        assert result[0][0] is DirectionMode.REVERSE
        cities = [d.city.airports[0] for d in result[0][1]]
        assert cities == ["SIN", "DAD", "HAN"]

    def test_durations_stay_with_cities(self):
        it = _make_itinerary(
            [_dest(_HANOI, "1d"), _dest(_DANANG, "2d"), _dest(_SINGAPORE, "3d")],
            direction=DirectionMode.REVERSE,
        )
        result = expand_directions(it)
        pairs = [(d.city.airports[0], d.stay.total_days) for d in result[0][1]]
        assert pairs == [("SIN", 3.0), ("DAD", 2.0), ("HAN", 1.0)]

    def test_single_destination_same_as_forward(self):
        it = _make_itinerary([_dest(_HANOI)], direction=DirectionMode.REVERSE)
        result = expand_directions(it)
        assert result[0][1][0].city.airports == ["HAN"]
