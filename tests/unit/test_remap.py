# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for reverse-mode duration remap logic."""

import pytest

from optifli.models.duration import Duration
from optifli.models.itinerary import Destination, Itinerary
from optifli.models.remap import apply_overrides, remap_for_reverse

pytestmark = pytest.mark.unit

_DELHI = {"name": "Delhi", "airports": ["DEL"]}
_HANOI = {"name": "Hanoi", "airports": ["HAN"]}
_DANANG = {"name": "Da Nang", "airports": ["DAD"]}


def _dest(city, stay="2d"):
    return {"city": city, "stay": stay}


def _make_itinerary(destinations):
    return Itinerary(
        origin=_DELHI,
        destinations=destinations,
        return_city=_DELHI,
    )


class TestRemapForReverse:
    def test_three_cities_reversed(self):
        it = _make_itinerary(
            [
                _dest(_DELHI, "1d"),
                _dest(_HANOI, "2d"),
                _dest(_DANANG, "3d"),
            ]
        )
        result = remap_for_reverse(it)

        assert len(result) == 3
        assert result[0].city.name == "Da Nang"
        assert result[0].stay.total_days == 3.0
        assert result[1].city.name == "Hanoi"
        assert result[1].stay.total_days == 2.0
        assert result[2].city.name == "Delhi"
        assert result[2].stay.total_days == 1.0

    def test_single_destination_unchanged(self):
        it = _make_itinerary([_dest(_HANOI, "5d")])
        result = remap_for_reverse(it)

        assert len(result) == 1
        assert result[0].city.name == "Hanoi"
        assert result[0].stay.total_days == 5.0

    def test_determinism(self):
        it = _make_itinerary(
            [
                _dest(_DELHI, "1d"),
                _dest(_HANOI, "2d"),
                _dest(_DANANG, "3d"),
            ]
        )
        assert remap_for_reverse(it) == remap_for_reverse(it)


class TestApplyOverrides:
    def test_override_one_city(self):
        destinations = [
            Destination(city=_DELHI, stay="1d"),
            Destination(city=_HANOI, stay="2d"),
            Destination(city=_DANANG, stay="3d"),
        ]
        result = apply_overrides(destinations, {"Hanoi": Duration(raw="5d")})

        assert result[0].stay.total_days == 1.0
        assert result[1].stay.total_days == 5.0
        assert result[2].stay.total_days == 3.0

    def test_override_multiple_cities(self):
        destinations = [
            Destination(city=_DELHI, stay="1d"),
            Destination(city=_HANOI, stay="2d"),
        ]
        result = apply_overrides(
            destinations,
            {"Delhi": Duration(raw="10h"), "Hanoi": Duration(raw="4d")},
        )

        assert result[0].stay.total_hours == 10.0
        assert result[1].stay.total_days == 4.0

    def test_empty_overrides_unchanged(self):
        destinations = [
            Destination(city=_HANOI, stay="2d"),
        ]
        result = apply_overrides(destinations, {})

        assert result == destinations

    def test_unknown_city_raises(self):
        destinations = [
            Destination(city=_HANOI, stay="2d"),
        ]
        with pytest.raises(ValueError, match="not found in destinations"):
            apply_overrides(destinations, {"Nowhere": Duration(raw="1d")})

    def test_determinism(self):
        destinations = [
            Destination(city=_DELHI, stay="1d"),
            Destination(city=_HANOI, stay="2d"),
        ]
        overrides = {"Hanoi": Duration(raw="5d")}
        assert apply_overrides(destinations, overrides) == apply_overrides(
            destinations, overrides
        )
