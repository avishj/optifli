# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for direction expansion."""

from pathlib import Path

import pytest

from optifli.engine.direction import expand_directions
from optifli.models.itinerary import DirectionMode
from optifli.profile import load_profile

pytestmark = pytest.mark.unit


class TestExpandDirectionsForward:
    def test_single_entry_returned(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "minimal.json")
        result = expand_directions(it)
        assert len(result) == 1
        assert result[0][0] is DirectionMode.FORWARD

    def test_destinations_unchanged(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_forward.json")
        result = expand_directions(it)
        cities = [d.city.airports[0] for d in result[0][1]]
        assert cities == ["HAN", "DAD", "SIN"]

    def test_order_preserved(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "two_dest_varied_stays.json")
        result = expand_directions(it)
        stays = [d.stay.total_days for d in result[0][1]]
        assert stays == [1.0, 3.0]


class TestExpandDirectionsReverse:
    def test_reversed_order(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_reverse.json")
        result = expand_directions(it)
        assert len(result) == 1
        assert result[0][0] is DirectionMode.REVERSE
        cities = [d.city.airports[0] for d in result[0][1]]
        assert cities == ["SIN", "DAD", "HAN"]

    def test_durations_stay_with_cities(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_reverse.json")
        result = expand_directions(it)
        pairs = [(d.city.airports[0], d.stay.total_days) for d in result[0][1]]
        assert pairs == [("SIN", 3.0), ("DAD", 2.0), ("HAN", 1.0)]

    def test_single_destination_same_as_forward(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "single_dest_reverse.json")
        result = expand_directions(it)
        assert result[0][1][0].city.airports == ["HAN"]


class TestExpandDirectionsBoth:
    def test_two_entries(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "both.json")
        result = expand_directions(it)
        assert len(result) == 2

    def test_contains_forward_and_reverse(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "both.json")
        result = expand_directions(it)
        directions = {r[0] for r in result}
        assert directions == {DirectionMode.FORWARD, DirectionMode.REVERSE}

    def test_forward_has_original_order(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "both.json")
        result = expand_directions(it)
        fwd = next(r for r in result if r[0] is DirectionMode.FORWARD)
        cities = [d.city.airports[0] for d in fwd[1]]
        assert cities == ["HAN", "DAD"]

    def test_reverse_has_reversed_order(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "both.json")
        result = expand_directions(it)
        rev = next(r for r in result if r[0] is DirectionMode.REVERSE)
        cities = [d.city.airports[0] for d in rev[1]]
        assert cities == ["DAD", "HAN"]
