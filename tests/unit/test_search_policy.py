# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the leg search policy."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from optifli.models.airport import CityGroup
from optifli.models.itinerary import Leg
from optifli.models.window import DepartureWindow
from optifli.search.fli_adapter import (
    FliAdapter,
    LegOption,
    SearchResponse,
    SegmentDetail,
)
from optifli.search.models import ApiFailureClassification, SearchOutcome
from optifli.search.policy import search_leg

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

# 06:00-18:00 UTC (single local date slice for DEL at +05:30)
_BASE_START = datetime(2026, 7, 16, 6, 0, tzinfo=UTC)
_BASE_END = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)


def _leg(
    origin_airports: list[str] | None = None,
    dest_airports: list[str] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> Leg:
    return Leg(
        origin=CityGroup(
            name="Origin",
            airports=origin_airports or ["DEL"],
        ),
        destination=CityGroup(
            name="Dest",
            airports=dest_airports or ["HAN"],
        ),
        departure_window=DepartureWindow(
            start=start or _BASE_START,
            end=end or _BASE_END,
        ),
    )


def _option(price: float = 200.0) -> LegOption:
    return LegOption(
        segments=(
            SegmentDetail(
                airline="AI",
                flight_number="AI302",
                departure_airport="DEL",
                arrival_airport="HAN",
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


def _adapter_returning(
    *responses: SearchResponse,
) -> FliAdapter:
    mock_client = MagicMock()
    adapter = FliAdapter(client=mock_client)
    adapter.search = MagicMock(side_effect=list(responses))  # type: ignore[method-assign]
    return adapter


# ---------------------------------------------------------------------------
# Base-window search
# ---------------------------------------------------------------------------


class TestSearchLegBaseWindow:
    def test_hit_returns_results_found(self):
        resp = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(resp)

        options, trace = search_leg(_leg(), adapter)

        assert len(options) == 1
        assert trace.final_status is SearchOutcome.RESULTS_FOUND
        assert trace.base_window_hit is True

    def test_miss_returns_no_results_base(self):
        resp = SearchResponse(options=(), failure=None)
        adapter = _adapter_returning(resp)

        options, trace = search_leg(_leg(), adapter)

        assert len(options) == 0
        assert trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW
        assert trace.base_window_hit is False

    def test_api_failure_counted(self):
        resp = SearchResponse(
            options=(),
            failure=ApiFailureClassification.RATE_LIMITED,
        )
        adapter = _adapter_returning(resp)

        _options, trace = search_leg(_leg(), adapter)

        assert trace.failed_queries == 1
        assert trace.successful_queries == 0
        assert trace.attempted_queries == 1

    def test_multiple_slices_aggregate(self):
        resp1 = SearchResponse(options=(_option(100),), failure=None)
        resp2 = SearchResponse(options=(_option(200),), failure=None)
        adapter = _adapter_returning(resp1, resp2)

        # LHR (UTC+1 in Jul) cross-day window → 2 slices → 2 calls
        options, trace = search_leg(
            _leg(
                origin_airports=["LHR"],
                dest_airports=["JFK"],
                start=datetime(2026, 7, 16, 22, 0, tzinfo=UTC),
                end=datetime(2026, 7, 17, 4, 0, tzinfo=UTC),
            ),
            adapter,
        )

        assert len(options) == 2
        assert trace.attempted_queries == 2
        assert trace.successful_queries == 2

    def test_window_bounds_in_trace(self):
        start = datetime(2026, 7, 16, 5, 0, tzinfo=UTC)
        end = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
        resp = SearchResponse(options=(), failure=None)
        adapter = _adapter_returning(resp)

        _options, trace = search_leg(_leg(start=start, end=end), adapter)

        assert trace.window_start == start
        assert trace.window_end == end

    def test_no_fallback_or_expansion_flags(self):
        resp = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(resp)

        _options, trace = search_leg(_leg(), adapter)

        assert trace.fallback_used is False
        assert trace.fallback_exhausted is False
        assert trace.expansion_rounds == 0
