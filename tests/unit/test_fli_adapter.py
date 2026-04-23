# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the FLI adapter and result normalizer."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fli.models.airline import Airline
from fli.models.airport import Airport
from fli.models.google_flights.base import FlightLeg, FlightResult

from optifli.search.fli_adapter import (
    FliAdapter,
    classify_error,
    normalize_leg,
    normalize_result,
)
from optifli.search.models import ApiFailureClassification

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

_LEG_DEFAULTS: dict = {
    "airline": Airline.AI,
    "flight_number": "AI302",
    "departure_airport": Airport.DEL,
    "arrival_airport": Airport.HAN,
    "departure_datetime": datetime(2026, 7, 16, 10, 30),
    "arrival_datetime": datetime(2026, 7, 16, 16, 45),
    "duration": 375,
}


def _fli_leg(**overrides: object) -> FlightLeg:
    """Build a ``FlightLeg`` with sensible defaults."""
    return FlightLeg(**{**_LEG_DEFAULTS, **overrides})


_RESULT_DEFAULTS: dict = {
    "price": 245.0,
    "duration": 375,
    "stops": 0,
}


def _fli_result(
    legs: list[FlightLeg] | None = None, **overrides: object
) -> FlightResult:
    """Build a ``FlightResult`` with sensible defaults."""
    return FlightResult(
        **{**_RESULT_DEFAULTS, "legs": legs or [_fli_leg()], **overrides}
    )


# ---------------------------------------------------------------------------
# normalize_leg
# ---------------------------------------------------------------------------


class TestNormalizeLeg:
    def test_maps_airline_name(self):
        seg = normalize_leg(_fli_leg())
        assert seg.airline == "AI"

    def test_maps_airports_as_strings(self):
        seg = normalize_leg(_fli_leg())
        assert seg.departure_airport == "DEL"
        assert seg.arrival_airport == "HAN"

    def test_preserves_times(self):
        leg = _fli_leg()
        seg = normalize_leg(leg)
        assert seg.departure_time == leg.departure_datetime
        assert seg.arrival_time == leg.arrival_datetime

    def test_preserves_duration(self):
        seg = normalize_leg(_fli_leg(duration=420))
        assert seg.duration_minutes == 420

    def test_preserves_flight_number(self):
        seg = normalize_leg(_fli_leg(flight_number="6E801"))
        assert seg.flight_number == "6E801"


# ---------------------------------------------------------------------------
# normalize_result
# ---------------------------------------------------------------------------


class TestNormalizeResult:
    def test_single_leg_option(self):
        opt = normalize_result(_fli_result())
        assert len(opt.segments) == 1
        assert opt.stops == 0

    def test_multi_leg_option(self):
        legs = [
            _fli_leg(arrival_airport=Airport.BKK),
            _fli_leg(departure_airport=Airport.BKK),
        ]
        opt = normalize_result(_fli_result(legs=legs, stops=1))
        assert len(opt.segments) == 2
        assert opt.stops == 1

    def test_preserves_price(self):
        opt = normalize_result(_fli_result(price=312.5))
        assert opt.price == 312.5

    def test_total_duration(self):
        opt = normalize_result(_fli_result(duration=600))
        assert opt.total_duration_minutes == 600


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------


class TestClassifyError:
    def test_rate_limited_429(self):
        assert (
            classify_error(Exception("HTTP 429"))
            is ApiFailureClassification.RATE_LIMITED
        )

    def test_rate_limited_text(self):
        exc = Exception("Search failed: rate limit exceeded")
        assert classify_error(exc) is ApiFailureClassification.RATE_LIMITED

    def test_rate_limited_too_many(self):
        exc = Exception("too many requests")
        assert classify_error(exc) is ApiFailureClassification.RATE_LIMITED

    def test_no_inventory(self):
        exc = Exception("no results found")
        assert classify_error(exc) is ApiFailureClassification.NO_INVENTORY

    def test_no_inventory_no_flights(self):
        assert (
            classify_error(Exception("no flights"))
            is ApiFailureClassification.NO_INVENTORY
        )

    def test_unknown_fallback(self):
        exc = Exception("connection reset by peer")
        assert classify_error(exc) is ApiFailureClassification.UNKNOWN


# ---------------------------------------------------------------------------
# FliAdapter.search
# ---------------------------------------------------------------------------


class TestFliAdapterSearch:
    def _adapter(self, mock_client: MagicMock) -> FliAdapter:
        return FliAdapter(client=mock_client)

    def test_successful_results_normalize(self):
        client = MagicMock()
        client.search.return_value = [_fli_result(), _fli_result()]
        resp = self._adapter(client).search(MagicMock())
        assert len(resp.options) == 2
        assert resp.failure is None

    def test_empty_results_no_failure(self):
        client = MagicMock()
        client.search.return_value = []
        resp = self._adapter(client).search(MagicMock())
        assert resp.options == ()
        assert resp.failure is None

    def test_provider_error_classifies(self):
        client = MagicMock()
        client.search.side_effect = Exception("Search failed: HTTP 429")
        resp = self._adapter(client).search(MagicMock())
        assert resp.options == ()
        assert resp.failure is ApiFailureClassification.RATE_LIMITED

    def test_unknown_error_classifies(self):
        client = MagicMock()
        client.search.side_effect = Exception("socket timeout")
        resp = self._adapter(client).search(MagicMock())
        assert resp.failure is ApiFailureClassification.UNKNOWN
