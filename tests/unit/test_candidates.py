# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for route candidate generation."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from optifli.engine.candidates import RouteCandidate
from optifli.models.itinerary import DirectionMode

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
