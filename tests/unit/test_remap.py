# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for reverse-mode duration remap logic."""

from pathlib import Path

import pytest

from optifli.models.duration import Duration
from optifli.models.remap import apply_overrides, remap_for_reverse
from optifli.profile import load_profile

pytestmark = pytest.mark.unit


class TestRemapForReverse:
    def test_three_cities_reversed(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_numbered_stays.json")
        result = remap_for_reverse(it)

        assert len(result) == 3
        assert result[0].city.name == "Singapore"
        assert result[0].stay.total_days == 3.0
        assert result[1].city.name == "Da Nang"
        assert result[1].stay.total_days == 2.0
        assert result[2].city.name == "Hanoi"
        assert result[2].stay.total_days == 1.0

    def test_single_destination_unchanged(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "minimal.json")
        result = remap_for_reverse(it)

        assert len(result) == 1
        assert result[0].city.name == "Hanoi"
        assert result[0].stay.total_days == 2.0

    def test_determinism(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_numbered_stays.json")
        assert remap_for_reverse(it) == remap_for_reverse(it)


class TestApplyOverrides:
    def test_override_one_city(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_numbered_stays.json")
        result = apply_overrides(list(it.destinations), {"Da Nang": Duration(raw="5d")})

        assert result[0].stay.total_days == 1.0
        assert result[1].stay.total_days == 5.0
        assert result[2].stay.total_days == 3.0

    def test_override_multiple_cities(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_numbered_stays.json")
        result = apply_overrides(
            list(it.destinations[:2]),
            {"Hanoi": Duration(raw="10h"), "Da Nang": Duration(raw="4d")},
        )

        assert result[0].stay.total_hours == 10.0
        assert result[1].stay.total_days == 4.0

    def test_empty_overrides_unchanged(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "minimal.json")
        destinations = list(it.destinations)
        result = apply_overrides(destinations, {})

        assert result == destinations

    def test_unknown_city_raises(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "minimal.json")
        with pytest.raises(ValueError, match="not found in destinations"):
            apply_overrides(list(it.destinations), {"Nowhere": Duration(raw="1d")})

    def test_determinism(self, profiles_dir: Path):
        it = load_profile(profiles_dir / "three_dest_numbered_stays.json")
        destinations = list(it.destinations[:2])
        overrides = {"Da Nang": Duration(raw="5d")}
        assert apply_overrides(destinations, overrides) == apply_overrides(
            destinations, overrides
        )
