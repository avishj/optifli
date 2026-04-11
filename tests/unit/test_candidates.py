# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for route candidate generation."""

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from optifli.engine.candidates import (
    RouteCandidate,
    build_leg_sequence,
    compute_first_window,
)
from optifli.models.airport import CityGroup
from optifli.models.itinerary import Destination, DirectionMode

pytestmark = pytest.mark.unit

_DELHI = {"name": "Delhi", "airports": ["DEL"]}
_HANOI = {"name": "Hanoi", "airports": ["HAN"]}
_DEST_HANOI = {"city": _HANOI, "stay": "2d"}


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


def _city(name: str, code: str) -> CityGroup:
    return CityGroup.model_validate({"name": name, "airports": [code]})


def _dest(name: str, code: str, stay: str = "2d") -> Destination:
    return Destination(city=_city(name, code), stay=stay)


class TestBuildLegSequence:
    def test_single_destination(self):
        origin = _city("Delhi", "DEL")
        dests = [_dest("Hanoi", "HAN")]
        ret = _city("Delhi", "DEL")
        pairs = build_leg_sequence(origin, dests, ret)
        assert len(pairs) == 2
        assert pairs[0][0].airports == ["DEL"]
        assert pairs[0][1].airports == ["HAN"]
        assert pairs[1][0].airports == ["HAN"]
        assert pairs[1][1].airports == ["DEL"]

    def test_three_destinations(self):
        origin = _city("Delhi", "DEL")
        dests = [
            _dest("Hanoi", "HAN"),
            _dest("Da Nang", "DAD"),
            _dest("Singapore", "SIN"),
        ]
        ret = _city("Delhi", "DEL")
        pairs = build_leg_sequence(origin, dests, ret)
        assert len(pairs) == 4
        assert [p[0].airports[0] for p in pairs] == ["DEL", "HAN", "DAD", "SIN"]
        assert [p[1].airports[0] for p in pairs] == ["HAN", "DAD", "SIN", "DEL"]

    def test_origin_equals_return(self):
        origin = _city("Delhi", "DEL")
        dests = [_dest("Hanoi", "HAN")]
        pairs = build_leg_sequence(origin, dests, origin)
        assert pairs[0][0].airports == pairs[-1][1].airports

    def test_origin_differs_from_return(self):
        origin = _city("Delhi", "DEL")
        dests = [_dest("Hanoi", "HAN")]
        ret = _city("Singapore", "SIN")
        pairs = build_leg_sequence(origin, dests, ret)
        assert pairs[0][0].airports == ["DEL"]
        assert pairs[-1][1].airports == ["SIN"]


class TestComputeFirstWindow:
    def test_default_24h_window(self):
        w = compute_first_window(date(2026, 7, 16))
        assert w.start == datetime(2026, 7, 16, 0, 0, tzinfo=UTC)
        assert w.end == datetime(2026, 7, 17, 0, 0, tzinfo=UTC)

    def test_custom_width(self):
        w = compute_first_window(date(2026, 7, 16), window_width=timedelta(hours=12))
        assert w.start == datetime(2026, 7, 16, 0, 0, tzinfo=UTC)
        assert w.end == datetime(2026, 7, 16, 12, 0, tzinfo=UTC)

    def test_returns_valid_departure_window(self):
        w = compute_first_window(date(2026, 7, 16))
        assert w.start.tzinfo is not None
        assert w.end.tzinfo is not None
        assert w.start < w.end
