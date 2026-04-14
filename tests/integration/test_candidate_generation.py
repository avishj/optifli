# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for route candidate generation with the PRD benchmark itinerary."""

from datetime import UTC

import pytest

from optifli.engine import generate_candidates
from optifli.models.itinerary import DirectionMode
from optifli.profile import ProfileError, load_profile

pytestmark = pytest.mark.integration


class TestBenchmarkItinerary:
    """DEL → HAN(2d) → DAD(1.5d) → PQC(3d) → SIN(0.5d) → DEL, direction BOTH."""

    @pytest.fixture
    def candidates(self, profiles_dir):
        it = load_profile(profiles_dir / "benchmark.json")
        return generate_candidates(it)

    def test_produces_two_candidates(self, candidates):
        assert len(candidates) == 2
        directions = {c.direction for c in candidates}
        assert directions == {DirectionMode.FORWARD, DirectionMode.REVERSE}

    def test_no_invalid_leg_chronology(self, candidates):
        for rc in candidates:
            for i in range(len(rc.legs) - 1):
                curr = rc.legs[i].departure_window.start
                nxt = rc.legs[i + 1].departure_window.start
                assert curr < nxt

    def test_all_windows_tz_aware_utc(self, candidates):
        for rc in candidates:
            for leg in rc.legs:
                assert leg.departure_window.start.tzinfo is not None
                assert leg.departure_window.end.tzinfo == UTC
                assert leg.departure_window.start.tzinfo == UTC

    def test_elapsed_time_math(self, candidates):
        fwd = next(c for c in candidates if c.direction is DirectionMode.FORWARD)
        assert len(fwd.legs) == 5
        # Each window start should be previous start + 6h travel + stay
        stays_hours = [48, 36, 72, 12]  # 2d, 1.5d, 3d, 0.5d
        for i in range(1, len(fwd.legs)):
            prev_start = fwd.legs[i - 1].departure_window.start
            curr_start = fwd.legs[i].departure_window.start
            expected_offset_hours = 6 + stays_hours[i - 1]
            actual_offset = curr_start - prev_start
            assert actual_offset.total_seconds() == expected_offset_hours * 3600

    def test_determinism(self, profiles_dir):
        it = load_profile(profiles_dir / "benchmark.json")
        a = generate_candidates(it)
        b = generate_candidates(it)
        for ca, cb in zip(a, b, strict=True):
            assert ca.direction == cb.direction
            for la, lb in zip(ca.legs, cb.legs, strict=True):
                assert la.departure_window == lb.departure_window


class TestExplicitLegContracts:
    def test_forward_explicit_profile_passes(self, profiles_dir):
        it = load_profile(profiles_dir / "full.json")

        candidates = generate_candidates(it)

        assert len(candidates) == 1
        assert candidates[0].direction is DirectionMode.FORWARD
        assert [leg.origin.airports[0] for leg in candidates[0].legs] == [
            "DEL",
            "HAN",
            "DAD",
        ]

    def test_reverse_explicit_profile_passes(self, profiles_dir):
        it = load_profile(profiles_dir / "reverse_full_explicit.json")

        candidates = generate_candidates(it)

        assert len(candidates) == 1
        assert candidates[0].direction is DirectionMode.REVERSE
        assert [leg.origin.airports[0] for leg in candidates[0].legs] == [
            "DEL",
            "DAD",
            "HAN",
        ]

    def test_both_direction_with_explicit_legs_fails_clearly(self, profiles_dir):
        with pytest.raises(ProfileError, match="direction=both"):
            load_profile(profiles_dir / "both_full_explicit.json")

    def test_partial_explicit_chain_fails_clearly(self, profiles_dir):
        it = load_profile(profiles_dir / "forward_partial_explicit.json")

        with pytest.raises(ValueError, match="full concrete route"):
            generate_candidates(it)

    def test_wrong_explicit_city_order_fails_clearly(self, profiles_dir):
        it = load_profile(profiles_dir / "forward_wrong_order_explicit.json")

        with pytest.raises(ValueError, match="concrete route segment"):
            generate_candidates(it)
