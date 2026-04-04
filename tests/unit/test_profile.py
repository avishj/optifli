# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for JSON profile loading."""

import json
from pathlib import Path

import pytest

from optifli.models.itinerary import DirectionMode, RouteMode
from optifli.profile import ProfileError, load_profile

pytestmark = pytest.mark.unit

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "profiles"


class TestLoadProfileValid:
    def test_minimal(self):
        it = load_profile(_FIXTURES / "minimal.json")
        assert it.origin.name == "Delhi"
        assert it.origin.airports == ["DEL"]
        assert len(it.destinations) == 1
        assert it.destinations[0].city.name == "Hanoi"
        assert it.destinations[0].stay.total_days == 2.0
        assert it.return_city.airports == ["DEL"]
        assert it.direction is DirectionMode.FORWARD
        assert it.route_mode is RouteMode.FIXED
        assert it.legs == []

    def test_full(self):
        it = load_profile(_FIXTURES / "full.json")
        assert len(it.destinations) == 2
        assert it.destinations[1].city.name == "Da Nang"
        assert it.destinations[1].stay.total_days == 1.5
        assert it.direction is DirectionMode.BOTH
        assert it.route_mode is RouteMode.FIXED
        assert len(it.legs) == 1
        assert it.legs[0].origin.airports == ["DEL"]
        assert it.legs[0].destination.airports == ["HAN"]

    def test_uppercase_enums(self):
        it = load_profile(_FIXTURES / "uppercase_enums.json")
        assert it.direction is DirectionMode.BOTH
        assert it.route_mode is RouteMode.REORDER


class TestLoadProfileFileErrors:
    def test_file_not_found(self):
        with pytest.raises(ProfileError, match="not found"):
            load_profile(Path("/nonexistent/profile.json"))

    def test_malformed_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ProfileError, match="Invalid JSON"):
            load_profile(bad)

    def test_json_array_rejected(self, tmp_path):
        arr = tmp_path / "array.json"
        arr.write_text('[{"origin": {}}]', encoding="utf-8")
        with pytest.raises(ProfileError, match="JSON object"):
            load_profile(arr)


class TestLoadProfileValidationErrors:
    def test_missing_origin(self, tmp_path):
        p = tmp_path / "no_origin.json"
        data = {
            "destinations": [
                {"city": {"name": "X", "include": ["HAN"]}, "stay": "2d"},
            ],
            "return_city": {"name": "X", "include": ["HAN"]},
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ProfileError, match="validation failed"):
            load_profile(p)

    def test_bad_airport(self, tmp_path):
        p = tmp_path / "bad_airport.json"
        data = {
            "origin": {"name": "X", "include": ["ZZZ"]},
            "destinations": [
                {"city": {"name": "Y", "include": ["HAN"]}, "stay": "2d"},
            ],
            "return_city": {"name": "Y", "include": ["HAN"]},
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ProfileError, match="validation failed") as exc_info:
            load_profile(p)
        assert len(exc_info.value.errors) >= 1

    def test_bad_duration(self, tmp_path):
        p = tmp_path / "bad_dur.json"
        data = {
            "origin": {"name": "X", "include": ["DEL"]},
            "destinations": [
                {"city": {"name": "Y", "include": ["HAN"]}, "stay": "1d12h"},
            ],
            "return_city": {"name": "X", "include": ["DEL"]},
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ProfileError, match="validation failed"):
            load_profile(p)

    def test_too_many_destinations(self, tmp_path):
        dests = [
            {"city": {"name": f"C{i}", "include": ["HAN"]}, "stay": "1d"}
            for i in range(11)
        ]
        p = tmp_path / "too_many.json"
        data = {
            "origin": {"name": "X", "include": ["DEL"]},
            "destinations": dests,
            "return_city": {"name": "X", "include": ["DEL"]},
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ProfileError, match="validation failed"):
            load_profile(p)

    def test_naive_datetime_in_leg(self, tmp_path):
        data = {
            "origin": {"name": "Delhi", "include": ["DEL"]},
            "destinations": [
                {"city": {"name": "Hanoi", "include": ["HAN"]}, "stay": "2d"},
            ],
            "return_city": {"name": "Delhi", "include": ["DEL"]},
            "legs": [
                {
                    "origin": {"name": "Delhi", "include": ["DEL"]},
                    "destination": {"name": "Hanoi", "include": ["HAN"]},
                    "departure_window": {
                        "start": "2026-07-16T19:00:00",
                        "end": "2026-07-17T11:00:00",
                    },
                },
            ],
        }
        p = tmp_path / "naive.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ProfileError, match="validation failed"):
            load_profile(p)
