# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the candidate search engine."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from optifli.engine.candidates import RouteCandidate
from optifli.models.airport import CityGroup
from optifli.models.itinerary import Destination, DirectionMode, Leg
from optifli.models.window import DepartureWindow
from optifli.search.engine import search_candidate
from optifli.search.fli_adapter import (
    FliAdapter,
    LegOption,
    SearchResponse,
    SegmentDetail,
)
from optifli.search.models import (
    ApiFailureClassification,
    FallbackBehavior,
    SearchOutcome,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

_BASE_START = datetime(2026, 7, 16, 6, 0, tzinfo=UTC)
_BASE_END = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
_SECOND_START = datetime(2026, 7, 19, 6, 0, tzinfo=UTC)
_SECOND_END = datetime(2026, 7, 19, 18, 0, tzinfo=UTC)

_DEL = CityGroup(name="Delhi", airports=["DEL"])
_HAN = CityGroup(name="Hanoi", airports=["HAN"])
_BKK = CityGroup(name="Bangkok", airports=["BKK"])

_EMPTY = SearchResponse(options=(), failure=None)


def _leg(
    origin: CityGroup = _DEL,
    destination: CityGroup = _HAN,
    start: datetime = _BASE_START,
    end: datetime = _BASE_END,
) -> Leg:
    return Leg(
        origin=origin,
        destination=destination,
        departure_window=DepartureWindow(start=start, end=end),
    )


def _option(
    dep_airport: str = "DEL",
    arr_airport: str = "HAN",
    price: float = 200.0,
) -> LegOption:
    return LegOption(
        segments=(
            SegmentDetail(
                airline="AI",
                flight_number="AI302",
                departure_airport=dep_airport,
                arrival_airport=arr_airport,
                departure_time=datetime(2026, 7, 16, 10, 30),
                arrival_time=datetime(2026, 7, 16, 16, 45),
                duration_minutes=375,
            ),
        ),
        price=price,
        currency="USD",
        total_duration_minutes=375,
        stops=0,
    )


def _candidate(*legs: Leg) -> RouteCandidate:
    leg_list = list(legs) if legs else [_leg()]
    return RouteCandidate(
        direction=DirectionMode.FORWARD,
        origin=leg_list[0].origin,
        destinations=[
            Destination(city=leg.destination, stay="2d") for leg in leg_list[:-1]
        ]
        + [Destination(city=leg_list[-1].destination, stay="2d")],
        return_city=leg_list[0].origin,
        legs=leg_list,
    )


def _adapter_returning(*responses: SearchResponse) -> FliAdapter:
    mock_client = MagicMock()
    adapter = FliAdapter(client=mock_client)
    adapter.search = MagicMock(side_effect=list(responses))  # type: ignore[method-assign]  # ty: ignore[invalid-assignment]
    return adapter


# ---------------------------------------------------------------------------
# Single-leg candidate
# ---------------------------------------------------------------------------


class TestSingleLeg:
    def test_hit_returns_options_and_result(self):
        resp = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(resp)

        all_opts, result = search_candidate(_candidate(), adapter)

        assert len(all_opts) == 1
        assert len(all_opts[0]) == 1
        assert result.completed is True
        assert len(result.legs) == 1
        assert result.legs[0].trace.final_status is SearchOutcome.RESULTS_FOUND

    def test_miss_returns_empty_options(self):
        adapter = _adapter_returning(_EMPTY)

        all_opts, result = search_candidate(_candidate(), adapter)

        assert len(all_opts) == 1
        assert len(all_opts[0]) == 0
        assert result.completed is True
        assert result.legs[0].trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW

    def test_api_failure_propagated(self):
        fail = SearchResponse(
            options=(),
            failure=ApiFailureClassification.RATE_LIMITED,
        )
        adapter = _adapter_returning(fail)

        _all_opts, result = search_candidate(_candidate(), adapter)

        assert result.legs[0].api_failure is ApiFailureClassification.RATE_LIMITED
        assert result.legs[0].trace.failed_queries == 1


# ---------------------------------------------------------------------------
# Multi-leg candidate
# ---------------------------------------------------------------------------


class TestMultiLeg:
    def _two_leg_candidate(self) -> RouteCandidate:
        leg1 = _leg(origin=_DEL, destination=_HAN)
        leg2 = _leg(
            origin=_HAN,
            destination=_BKK,
            start=_SECOND_START,
            end=_SECOND_END,
        )
        return _candidate(leg1, leg2)

    def test_both_legs_searched(self):
        resp1 = SearchResponse(options=(_option("DEL", "HAN"),), failure=None)
        resp2 = SearchResponse(options=(_option("HAN", "BKK"),), failure=None)
        # Leg 1 (DEL): 1 slice. Leg 2 (HAN +07:00): 2 slices.
        adapter = _adapter_returning(resp1, resp2, _EMPTY)

        all_opts, result = search_candidate(self._two_leg_candidate(), adapter)

        assert len(all_opts) == 2
        assert len(all_opts[0]) == 1
        assert len(all_opts[1]) == 1
        assert result.completed is True
        assert len(result.legs) == 2

    def test_traces_preserved_per_leg(self):
        resp1 = SearchResponse(options=(_option("DEL", "HAN"),), failure=None)
        # Leg 1 (DEL): 1 slice hit. Leg 2 (HAN +07:00): 2 slices miss.
        adapter = _adapter_returning(resp1, _EMPTY, _EMPTY)

        _all_opts, result = search_candidate(self._two_leg_candidate(), adapter)

        assert result.legs[0].trace.final_status is SearchOutcome.RESULTS_FOUND
        assert result.legs[1].trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW

    def test_leg_results_match_candidate_legs(self):
        # Leg 1 (DEL +05:30): 1 slice. Leg 2 (HAN +07:00): 2 slices.
        adapter = _adapter_returning(_EMPTY, _EMPTY, _EMPTY)
        candidate = self._two_leg_candidate()

        _all_opts, result = search_candidate(candidate, adapter)

        for i, leg_result in enumerate(result.legs):
            assert leg_result.leg == candidate.legs[i]

    def test_policy_params_forwarded(self):
        hit = SearchResponse(options=(_option(),), failure=None)
        # Leg 1 (DEL +05:30):
        #   base nonstop: 1 miss
        #   exp r1 nonstop (10:30-01:00+1 -> 2 slices): 2 misses
        #   fallback one-stop on expanded window (2 slices): hit on 1st
        # Leg 2 (HAN +07:00):
        #   base nonstop (13:00-01:00+1 -> 2 slices): hit on 1st
        adapter = _adapter_returning(
            _EMPTY,
            _EMPTY,
            _EMPTY,
            hit,
            _EMPTY,
            hit,
            _EMPTY,
        )

        _all_opts, result = search_candidate(
            self._two_leg_candidate(),
            adapter,
            max_expansion_rounds=1,
            fallback=FallbackBehavior.ONE_STOP,
        )

        assert result.legs[0].trace.fallback_used is True
        assert result.legs[1].trace.fallback_used is False
