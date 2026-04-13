# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for route candidate generation."""

import logging
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from optifli.engine.candidates import (
    RouteCandidate,
    build_leg_sequence,
    compute_first_window,
    generate_candidates,
    propagate_all_windows,
    propagate_window,
    validate_leg_consistency,
)
from optifli.models.duration import Duration
from optifli.models.itinerary import DirectionMode, Itinerary, Leg
from optifli.profile import load_profile

pytestmark = pytest.mark.unit

_DELHI = {"name": "Delhi", "airports": ["DEL"]}
_HANOI = {"name": "Hanoi", "airports": ["HAN"]}
_DEST_HANOI = {"city": _HANOI, "stay": "2d"}
_KOLKATA = ZoneInfo("Asia/Kolkata")


def _make_leg():
    return {
        "origin": _DELHI,
        "destination": _HANOI,
        "departure_window": {
            "start": datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
            "end": datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
        },
    }


def _make_candidate(**overrides):
    defaults = {
        "direction": DirectionMode.FORWARD,
        "origin": _DELHI,
        "destinations": [_DEST_HANOI],
        "return_city": _DELHI,
        "legs": [_make_leg()],
    }
    return RouteCandidate.model_validate({**defaults, **overrides})


class TestRouteCandidateValid:
    def test_forward(self):
        rc = _make_candidate(direction=DirectionMode.FORWARD)
        assert rc.direction is DirectionMode.FORWARD
        assert rc.origin.airports == ["DEL"]
        assert len(rc.legs) == 1

    def test_reverse(self):
        rc = _make_candidate(direction=DirectionMode.REVERSE)
        assert rc.direction is DirectionMode.REVERSE


class TestRouteCandidateValidation:
    def test_reject_direction_both(self):
        with pytest.raises(ValidationError, match="not BOTH"):
            _make_candidate(direction=DirectionMode.BOTH)

    def test_reject_empty_legs(self):
        with pytest.raises(ValidationError, match="non-empty"):
            _make_candidate(legs=[])


class TestBuildLegSequence:
    def test_single_destination(self, profiles_dir):
        it = load_profile(profiles_dir / "minimal.json")
        pairs = build_leg_sequence(it.origin, list(it.destinations), it.return_city)
        assert len(pairs) == 2
        assert pairs[0][0].airports == ["DEL"]
        assert pairs[0][1].airports == ["HAN"]
        assert pairs[1][0].airports == ["HAN"]
        assert pairs[1][1].airports == ["DEL"]

    def test_three_destinations(self, profiles_dir):
        it = load_profile(profiles_dir / "three_dest_forward.json")
        pairs = build_leg_sequence(it.origin, list(it.destinations), it.return_city)
        assert len(pairs) == 4
        assert [p[0].airports[0] for p in pairs] == ["DEL", "HAN", "DAD", "SIN"]
        assert [p[1].airports[0] for p in pairs] == ["HAN", "DAD", "SIN", "DEL"]

    def test_origin_equals_return(self, profiles_dir):
        it = load_profile(profiles_dir / "minimal.json")
        pairs = build_leg_sequence(it.origin, list(it.destinations), it.return_city)
        assert pairs[0][0].airports == pairs[-1][1].airports

    def test_origin_differs_from_return(self, profiles_dir):
        it = load_profile(profiles_dir / "diff_return_city.json")
        pairs = build_leg_sequence(it.origin, list(it.destinations), it.return_city)
        assert pairs[0][0].airports == ["DEL"]
        assert pairs[-1][1].airports == ["SIN"]


class TestComputeFirstWindow:
    def test_default_24h_window(self):
        w = compute_first_window(date(2026, 7, 16), _KOLKATA)
        assert w.start == datetime(2026, 7, 15, 18, 30, tzinfo=UTC)
        assert w.end == datetime(2026, 7, 16, 18, 30, tzinfo=UTC)

    def test_custom_width(self):
        w = compute_first_window(
            date(2026, 7, 16),
            _KOLKATA,
            window_width=timedelta(hours=12),
        )
        assert w.start == datetime(2026, 7, 15, 18, 30, tzinfo=UTC)
        assert w.end == datetime(2026, 7, 16, 6, 30, tzinfo=UTC)

    def test_returns_valid_departure_window(self):
        w = compute_first_window(date(2026, 7, 16), _KOLKATA)
        assert w.start.tzinfo is not None
        assert w.end.tzinfo is not None
        assert w.start < w.end


class TestPropagateWindow:
    def _first(self):
        return compute_first_window(date(2026, 7, 16), _KOLKATA)

    def test_basic_2d_stay(self):
        first = self._first()
        stay = Duration.model_validate("2d")
        w = propagate_window(first, stay)
        expected_start = first.start + timedelta(hours=54)
        assert w.start == expected_start
        assert w.end == expected_start + timedelta(hours=24)

    def test_fractional_stay(self):
        first = self._first()
        stay = Duration.model_validate("0.5d")
        w = propagate_window(first, stay)
        expected_start = first.start + timedelta(hours=18)
        assert w.start == expected_start

    def test_custom_travel_estimate(self):
        first = self._first()
        stay = Duration.model_validate("2d")
        w = propagate_window(first, stay, travel_estimate=timedelta(hours=12))
        expected_start = first.start + timedelta(hours=60)
        assert w.start == expected_start

    def test_custom_window_width(self):
        first = self._first()
        stay = Duration.model_validate("2d")
        w = propagate_window(first, stay, window_width=timedelta(hours=12))
        assert w.end - w.start == timedelta(hours=12)


class TestPropagateAllWindows:
    def test_single_destination_two_legs(self):
        stays = [Duration.model_validate("2d")]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=2,
        )
        assert len(windows) == 2
        assert windows[0].start == datetime(2026, 7, 15, 18, 30, tzinfo=UTC)
        expected = windows[0].start + timedelta(hours=54)
        assert windows[1].start == expected

    def test_three_destinations_four_legs(self):
        stays = [
            Duration.model_validate("2d"),
            Duration.model_validate("1.5d"),
            Duration.model_validate("3d"),
        ]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=4,
        )
        assert len(windows) == 4
        for w in windows:
            assert w.start < w.end

    def test_fractional_durations(self):
        stays = [Duration.model_validate("0.5d"), Duration.model_validate("12h")]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=3,
        )
        assert len(windows) == 3
        assert windows[1].start == windows[0].start + timedelta(hours=18)
        assert windows[2].start == windows[0].start + timedelta(hours=36)

    def test_determinism(self):
        stays = [Duration.model_validate("2d"), Duration.model_validate("1d")]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        a = propagate_all_windows(
            first,
            stays,
            leg_count=3,
        )
        b = propagate_all_windows(
            first,
            stays,
            leg_count=3,
        )
        assert a == b


class TestCrossTimezoneCorrectness:
    """Verify UTC-canonical propagation doesn't drift across timezone conversions."""

    def test_round_trip_asia_kolkata(self):
        stays = [Duration.model_validate("2d")]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=2,
        )
        kolkata = ZoneInfo("Asia/Kolkata")
        for w in windows:
            local_start = w.start.astimezone(kolkata)
            back_to_utc = local_start.astimezone(UTC)
            assert back_to_utc == w.start

    def test_dst_transition_no_drift(self):
        # 2026-03-08 is US spring-forward day (EST→EDT at 02:00)
        stays = [Duration.model_validate("1d")]
        first = compute_first_window(date(2026, 3, 8), ZoneInfo("US/Eastern"))
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=2,
        )
        eastern = ZoneInfo("US/Eastern")
        for w in windows:
            local_start = w.start.astimezone(eastern)
            back_to_utc = local_start.astimezone(UTC)
            assert back_to_utc == w.start

    def test_all_windows_tz_aware(self):
        stays = [Duration.model_validate("2d"), Duration.model_validate("1d")]
        first = compute_first_window(date(2026, 7, 16), _KOLKATA)
        windows = propagate_all_windows(
            first,
            stays,
            leg_count=3,
        )
        for w in windows:
            assert w.start.tzinfo is not None
            assert w.end.tzinfo is not None


def _make_typed_leg(
    origin_code: str,
    dest_code: str,
    start: datetime,
    end: datetime,
) -> Leg:
    return Leg.model_validate(
        {
            "origin": {"name": origin_code, "airports": [origin_code]},
            "destination": {"name": dest_code, "airports": [dest_code]},
            "departure_window": {"start": start, "end": end},
        }
    )


class TestValidateLegConsistency:
    def test_consistent_legs_no_warnings(self, profiles_dir):
        legs = [
            _make_typed_leg(
                "DEL",
                "HAN",
                datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 6, 0, tzinfo=UTC),
            ),
            _make_typed_leg(
                "HAN",
                "DEL",
                datetime(2026, 7, 20, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 20, 6, 0, tzinfo=UTC),
            ),
        ]
        it = load_profile(profiles_dir / "minimal.json")
        assert validate_leg_consistency(legs, list(it.destinations)) == []

    def test_tight_schedule_warning(self, profiles_dir):
        legs = [
            _make_typed_leg(
                "DEL",
                "HAN",
                datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 6, 0, tzinfo=UTC),
            ),
            _make_typed_leg(
                "HAN",
                "DEL",
                datetime(2026, 7, 17, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 17, 6, 0, tzinfo=UTC),
            ),
        ]
        it = load_profile(profiles_dir / "minimal.json")
        warnings = validate_leg_consistency(legs, list(it.destinations))
        assert len(warnings) == 1
        assert "shorter than stay + travel estimate" in warnings[0]

    def test_overlapping_legs_warning(self, profiles_dir):
        legs = [
            _make_typed_leg(
                "DEL",
                "HAN",
                datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 12, 0, tzinfo=UTC),
            ),
            _make_typed_leg(
                "HAN",
                "DEL",
                datetime(2026, 7, 16, 6, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 18, 0, tzinfo=UTC),
            ),
        ]
        it = load_profile(profiles_dir / "minimal.json")
        warnings = validate_leg_consistency(legs, list(it.destinations))
        assert len(warnings) == 1
        assert "overlapping" in warnings[0]

    def test_single_leg_no_warnings(self, profiles_dir):
        legs = [
            _make_typed_leg(
                "DEL",
                "HAN",
                datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 6, 0, tzinfo=UTC),
            ),
        ]
        it = load_profile(profiles_dir / "minimal.json")
        assert validate_leg_consistency(legs, list(it.destinations)) == []


class TestGenerateCandidates:
    def test_forward_no_legs(self, profiles_dir):
        it = load_profile(profiles_dir / "minimal.json")
        candidates = generate_candidates(it)
        assert len(candidates) == 1
        rc = candidates[0]
        assert rc.direction is DirectionMode.FORWARD
        assert len(rc.legs) == 2
        assert rc.legs[0].departure_window.start == datetime(
            2026,
            7,
            15,
            18,
            30,
            tzinfo=UTC,
        )
        assert rc.legs[0].origin.airports == ["DEL"]
        assert rc.legs[0].destination.airports == ["HAN"]
        assert rc.legs[1].origin.airports == ["HAN"]
        assert rc.legs[1].destination.airports == ["DEL"]

    def test_reverse_no_legs(self, profiles_dir):
        it = load_profile(profiles_dir / "reverse.json")
        candidates = generate_candidates(it)
        assert len(candidates) == 1
        rc = candidates[0]
        assert rc.direction is DirectionMode.REVERSE
        cities = [leg.destination.airports[0] for leg in rc.legs]
        assert cities[0] == "DAD"
        assert cities[1] == "HAN"

    def test_both_no_legs(self, profiles_dir):
        it = load_profile(profiles_dir / "both.json")
        candidates = generate_candidates(it)
        assert len(candidates) == 2
        directions = {c.direction for c in candidates}
        assert directions == {DirectionMode.FORWARD, DirectionMode.REVERSE}

    def test_forward_explicit_legs(self, profiles_dir):
        it = load_profile(profiles_dir / "full.json")
        candidates = generate_candidates(it)
        assert len(candidates) == 2
        for rc in candidates:
            assert rc.legs[0].departure_window.start is not None

    def test_propagated_windows_are_tz_aware(self, profiles_dir):
        it = load_profile(profiles_dir / "minimal.json")
        candidates = generate_candidates(it)
        for leg in candidates[0].legs:
            assert leg.departure_window.start.tzinfo is not None
            assert leg.departure_window.end.tzinfo is not None


class TestCandidateLogging:
    def test_info_log_candidate_count(self, profiles_dir, caplog):
        it = load_profile(profiles_dir / "minimal.json")
        with caplog.at_level(logging.INFO, logger="optifli.engine.candidates"):
            generate_candidates(it)
        assert any("Generated 1 candidate(s)" in m for m in caplog.messages)

    def test_debug_log_leg_details(self, profiles_dir, caplog):
        it = load_profile(profiles_dir / "minimal.json")
        with caplog.at_level(logging.DEBUG, logger="optifli.engine.candidates"):
            generate_candidates(it)
        assert any("2 leg(s)" in m for m in caplog.messages)

    def test_warning_log_tight_legs(self, caplog):
        legs = [
            _make_typed_leg(
                "DEL",
                "HAN",
                datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 16, 6, 0, tzinfo=UTC),
            ),
            _make_typed_leg(
                "HAN",
                "DEL",
                datetime(2026, 7, 17, 0, 0, tzinfo=UTC),
                datetime(2026, 7, 17, 6, 0, tzinfo=UTC),
            ),
        ]
        it = Itinerary.model_validate(
            {
                "origin": _DELHI,
                "destinations": [_DEST_HANOI],
                "return_city": _DELHI,
                "legs": legs,
            }
        )
        with caplog.at_level(logging.WARNING, logger="optifli.engine.candidates"):
            generate_candidates(it)
        assert any("shorter than stay + travel estimate" in m for m in caplog.messages)
