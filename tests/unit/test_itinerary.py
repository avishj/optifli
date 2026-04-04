# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for itinerary models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from optifli.models.itinerary import (
    Destination,
    DirectionMode,
    Itinerary,
    Leg,
    RouteMode,
)

pytestmark = pytest.mark.unit


class TestDirectionMode:
    def test_values(self):
        assert DirectionMode.FORWARD == "forward"
        assert DirectionMode.REVERSE == "reverse"
        assert DirectionMode.BOTH == "both"

    def test_string_identity(self):
        assert DirectionMode.FORWARD == "forward"
        assert isinstance(DirectionMode.FORWARD, str)

    def test_case_insensitive_lookup(self):
        assert DirectionMode("forward") is DirectionMode.FORWARD
        assert DirectionMode("FORWARD".lower()) is DirectionMode.FORWARD

    def test_invalid_value(self):
        with pytest.raises(ValueError, match="not a valid"):
            DirectionMode("diagonal")


class TestDirectionModeDirectConstruction:
    def test_uppercase_raises(self):
        with pytest.raises(ValueError, match="not a valid"):
            DirectionMode("FORWARD")

    def test_mixed_case_raises(self):
        with pytest.raises(ValueError, match="not a valid"):
            DirectionMode("Both")


class TestRouteModeDirectConstruction:
    def test_uppercase_raises(self):
        with pytest.raises(ValueError, match="not a valid"):
            RouteMode("FIXED")

    def test_mixed_case_raises(self):
        with pytest.raises(ValueError, match="not a valid"):
            RouteMode("Reorder")


class TestDirectionModeInItinerary:
    def test_uppercase_direction_in_model(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DELHI,
            direction="FORWARD",
        )
        assert it.direction is DirectionMode.FORWARD

    def test_mixed_case_direction_in_model(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DELHI,
            direction="Both",
        )
        assert it.direction is DirectionMode.BOTH


class TestRouteMode:
    def test_values(self):
        assert RouteMode.FIXED == "fixed"
        assert RouteMode.REORDER == "reorder"

    def test_string_identity(self):
        assert RouteMode.FIXED == "fixed"
        assert isinstance(RouteMode.FIXED, str)

    def test_case_insensitive_lookup(self):
        assert RouteMode("fixed") is RouteMode.FIXED
        assert RouteMode("FIXED".lower()) is RouteMode.FIXED

    def test_invalid_value(self):
        with pytest.raises(ValueError, match="not a valid"):
            RouteMode("shuffle")


class TestRouteModeInItinerary:
    def test_uppercase_route_mode_in_model(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DELHI,
            route_mode="REORDER",
        )
        assert it.route_mode is RouteMode.REORDER


class TestDestinationValid:
    def test_basic_construction(self):
        d = Destination(
            city={"name": "Hanoi", "airports": ["HAN"]},
            stay="2d",
        )
        assert d.city.name == "Hanoi"
        assert d.city.airports == ["HAN"]
        assert d.stay.total_days == 2.0

    def test_multi_airport_city(self):
        d = Destination(
            city={"name": "London", "airports": ["LHR", "LGW"]},
            stay="1.5d",
        )
        assert len(d.city.airports) == 2
        assert d.stay.total_hours == 36.0

    def test_hours_stay(self):
        d = Destination(
            city={"name": "Delhi", "airports": ["DEL"]},
            stay="12h",
        )
        assert d.stay.total_hours == 12.0


class TestDestinationNestedValidation:
    def test_bad_duration_bubbles_up(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Destination(
                city={"name": "Hanoi", "airports": ["HAN"]},
                stay="1d12h",
            )

    def test_bad_airport_bubbles_up(self):
        with pytest.raises(ValidationError, match="not a recognized IATA"):
            Destination(
                city={"name": "Nowhere", "airports": ["ZZZ"]},
                stay="2d",
            )

    def test_empty_airports_bubbles_up(self):
        with pytest.raises(ValidationError, match="at least one airport"):
            Destination(
                city={"name": "Empty", "airports": []},
                stay="2d",
            )

    def test_zero_duration_bubbles_up(self):
        with pytest.raises(ValidationError, match="positive"):
            Destination(
                city={"name": "Hanoi", "airports": ["HAN"]},
                stay="0d",
            )


class TestLegValid:
    def test_basic_leg(self):
        leg = Leg(
            origin={"name": "Delhi", "airports": ["DEL"]},
            destination={"name": "Hanoi", "airports": ["HAN"]},
            departure_window={
                "start": datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
                "end": datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
            },
        )
        assert leg.origin.airports == ["DEL"]
        assert leg.destination.airports == ["HAN"]
        assert leg.arrival_cutoff is None

    def test_leg_with_arrival_cutoff(self):
        leg = Leg(
            origin={"name": "Delhi", "airports": ["DEL"]},
            destination={"name": "Hanoi", "airports": ["HAN"]},
            departure_window={
                "start": datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
                "end": datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
            },
            arrival_cutoff={
                "deadline": datetime(2026, 7, 17, 23, 0, tzinfo=UTC),
            },
        )
        assert leg.arrival_cutoff is not None
        assert leg.arrival_cutoff.deadline.year == 2026

    def test_leg_multi_airport_groups(self):
        leg = Leg(
            origin={"name": "London", "airports": ["LHR", "LGW"]},
            destination={"name": "Tokyo", "airports": ["NRT", "HND"]},
            departure_window={
                "start": datetime(2026, 8, 1, 6, 0, tzinfo=UTC),
                "end": datetime(2026, 8, 1, 14, 0, tzinfo=UTC),
            },
        )
        assert len(leg.origin.airports) == 2
        assert len(leg.destination.airports) == 2


class TestLegNestedValidation:
    def test_bad_airport_bubbles_up(self):
        with pytest.raises(ValidationError, match="not a recognized IATA"):
            Leg(
                origin={"name": "Nowhere", "airports": ["ZZZ"]},
                destination={"name": "Hanoi", "airports": ["HAN"]},
                departure_window={
                    "start": datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
                    "end": datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
                },
            )

    def test_naive_datetime_bubbles_up(self):
        with pytest.raises(ValidationError, match="timezone-aware"):
            Leg(
                origin={"name": "Delhi", "airports": ["DEL"]},
                destination={"name": "Hanoi", "airports": ["HAN"]},
                departure_window={
                    "start": datetime(2026, 7, 16, 19, 0),
                    "end": datetime(2026, 7, 17, 11, 0),
                },
            )

    def test_window_end_before_start_bubbles_up(self):
        with pytest.raises(ValidationError, match="before"):
            Leg(
                origin={"name": "Delhi", "airports": ["DEL"]},
                destination={"name": "Hanoi", "airports": ["HAN"]},
                departure_window={
                    "start": datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
                    "end": datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
                },
            )


_DELHI = {"name": "Delhi", "airports": ["DEL"]}
_HANOI = {"name": "Hanoi", "airports": ["HAN"]}
_DANANG = {"name": "Da Nang", "airports": ["DAD"]}


def _dest(city: dict, stay: str = "2d"):
    return {"city": city, "stay": stay}


class TestItineraryValid:
    def test_single_destination(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DELHI,
        )
        assert len(it.destinations) == 1
        assert it.direction is DirectionMode.FORWARD
        assert it.route_mode is RouteMode.FIXED
        assert it.legs == []

    def test_multiple_destinations(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI), _dest(_DANANG, "1.5d")],
            return_city=_DELHI,
        )
        assert len(it.destinations) == 2

    def test_ten_destinations(self):
        dests = [_dest(_HANOI, f"{i + 1}d") for i in range(10)]
        it = Itinerary(
            origin=_DELHI,
            destinations=dests,
            return_city=_DELHI,
        )
        assert len(it.destinations) == 10

    def test_origin_differs_from_return(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DANANG,
        )
        assert it.origin.name == "Delhi"
        assert it.return_city.name == "Da Nang"

    def test_explicit_direction_and_route(self):
        it = Itinerary(
            origin=_DELHI,
            destinations=[_dest(_HANOI)],
            return_city=_DELHI,
            direction="both",
            route_mode="reorder",
        )
        assert it.direction is DirectionMode.BOTH
        assert it.route_mode is RouteMode.REORDER


class TestItineraryInvalid:
    def test_zero_destinations_rejected(self):
        with pytest.raises(ValidationError, match="at least one"):
            Itinerary(
                origin=_DELHI,
                destinations=[],
                return_city=_DELHI,
            )

    def test_eleven_destinations_rejected(self):
        dests = [_dest(_HANOI, f"{i + 1}d") for i in range(11)]
        with pytest.raises(ValidationError, match="at most 10"):
            Itinerary(
                origin=_DELHI,
                destinations=dests,
                return_city=_DELHI,
            )
