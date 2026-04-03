# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for itinerary models."""

import pytest
from pydantic import ValidationError

from optifli.models.itinerary import Destination

pytestmark = pytest.mark.unit


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
