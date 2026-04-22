# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the leg search policy."""

from datetime import UTC, datetime, timedelta
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
from optifli.search.models import (
    ApiFailureClassification,
    FallbackBehavior,
    SearchOutcome,
)
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
    adapter.search = MagicMock(side_effect=list(responses))  # type: ignore[method-assign]  # ty: ignore[invalid-assignment]
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


# ---------------------------------------------------------------------------
# Expansion rounds
# ---------------------------------------------------------------------------

_EMPTY = SearchResponse(options=(), failure=None)


class TestSearchLegExpansion:
    """Expansion tests.

    DEL (+05:30) slice counts for the default 06:00-18:00 UTC window:
    - base (06-18 UTC -> 11:30-23:30 +05:30): 1 slice
    - round 1 (05-19 UTC -> 10:30-00:30+1 +05:30): 2 slices
    - round 2 (04-20 UTC -> 09:30-01:30+1 +05:30): 2 slices
    """

    def test_round1_widens_by_1h(self):
        # Base: 1 miss. Round 1: 2 slices, hit on first.
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(_EMPTY, resp_hit, _EMPTY)

        options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=2,
        )

        assert trace.expansion_rounds == 1
        assert trace.final_status is SearchOutcome.RESULTS_FOUND
        assert trace.base_window_hit is False
        assert len(options) >= 1
        assert trace.window_start == _BASE_START - timedelta(hours=1)
        assert trace.window_end == _BASE_END + timedelta(hours=1)

    def test_round2_widens_by_2h(self):
        # Base: 1 miss. Round 1: 2 misses. Round 2: hit on first of 2.
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(
            _EMPTY,
            _EMPTY,
            _EMPTY,
            resp_hit,
            _EMPTY,
        )

        _options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=2,
        )

        assert trace.expansion_rounds == 2
        assert trace.final_status is SearchOutcome.RESULTS_FOUND
        assert trace.window_start == _BASE_START - timedelta(hours=2)
        assert trace.window_end == _BASE_END + timedelta(hours=2)

    def test_stops_at_configured_cap(self):
        # Base: 1 miss. Round 1: 2 misses. Cap=1 so no round 2.
        adapter = _adapter_returning(_EMPTY, _EMPTY, _EMPTY)

        options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=1,
        )

        assert trace.expansion_rounds == 1
        assert trace.final_status is SearchOutcome.NO_RESULTS_AFTER_EXPANSION
        assert len(options) == 0

    def test_zero_cap_skips_expansion(self):
        adapter = _adapter_returning(_EMPTY)

        _options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=0,
        )

        assert trace.expansion_rounds == 0
        assert trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW

    def test_trace_counts_across_rounds(self):
        # Base: 1 miss. Round 1: 1 fail + 1 hit (2 slices).
        fail_resp = SearchResponse(
            options=(),
            failure=ApiFailureClassification.RATE_LIMITED,
        )
        hit_resp = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(_EMPTY, fail_resp, hit_resp)

        _options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=2,
        )

        assert trace.attempted_queries == 3
        assert trace.successful_queries == 2
        assert trace.failed_queries == 1


# ---------------------------------------------------------------------------
# One-stop fallback
# ---------------------------------------------------------------------------

_FALLBACK = FallbackBehavior.ONE_STOP


class TestSearchLegFallback:
    """Fallback tests.

    DEL (+05:30) slice counts for the default 06:00-18:00 UTC window:
    - nonstop base: 1 slice
    - fallback base (same window, one-stop): 1 slice
    - fallback expansion round 1 (05-19 UTC): 2 slices
    """

    def test_hit_returns_results_with_fallback_used(self):
        # Nonstop miss (1), fallback hit (1).
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(_EMPTY, resp_hit)

        options, trace = search_leg(_leg(), adapter, fallback=_FALLBACK)

        assert len(options) == 1
        assert trace.final_status is SearchOutcome.RESULTS_FOUND
        assert trace.fallback_used is True
        assert trace.fallback_exhausted is False

    def test_exhaustion_returns_no_results_after_fallback(self):
        # Nonstop miss (1), fallback miss (1).
        adapter = _adapter_returning(_EMPTY, _EMPTY)

        options, trace = search_leg(_leg(), adapter, fallback=_FALLBACK)

        assert len(options) == 0
        assert trace.final_status is SearchOutcome.NO_RESULTS_AFTER_FALLBACK
        assert trace.fallback_used is True
        assert trace.fallback_exhausted is True

    def test_disabled_skips_fallback(self):
        adapter = _adapter_returning(_EMPTY)

        _options, trace = search_leg(
            _leg(),
            adapter,
            fallback=FallbackBehavior.DISABLED,
        )

        assert trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW
        assert trace.fallback_used is False

    def test_nonstop_hit_skips_fallback(self):
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(resp_hit)

        _options, trace = search_leg(_leg(), adapter, fallback=_FALLBACK)

        assert trace.final_status is SearchOutcome.RESULTS_FOUND
        assert trace.fallback_used is False
        assert adapter.search.call_count == 1  # ty: ignore[unresolved-attribute]

    def test_expansion_then_fallback(self):
        # Nonstop base miss (1), expansion round 1 miss (2),
        # fallback on expanded window (2 slices), hit on first.
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(_EMPTY, _EMPTY, _EMPTY, resp_hit, _EMPTY)

        options, trace = search_leg(
            _leg(),
            adapter,
            max_expansion_rounds=1,
            fallback=_FALLBACK,
        )

        assert len(options) == 1
        assert trace.expansion_rounds == 1
        assert trace.fallback_used is True
        assert trace.fallback_exhausted is False
        assert trace.final_status is SearchOutcome.RESULTS_FOUND

    def test_expand_on_fallback(self):
        # max_expansion_rounds=1 applies to both phases.
        # Nonstop base miss (1), nonstop exp r1 miss (2),
        # fallback base on expanded window miss (2),
        # fallback exp r1 hit on first of 2.
        resp_hit = SearchResponse(options=(_option(),), failure=None)
        adapter = _adapter_returning(
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
            resp_hit,
            _EMPTY,
        )

        options, trace = search_leg(
            _leg(),
            adapter,
            fallback=_FALLBACK,
            expand_on_fallback=True,
            max_expansion_rounds=1,
        )

        assert len(options) == 1
        assert trace.fallback_used is True
        assert trace.final_status is SearchOutcome.RESULTS_FOUND

    def test_expand_on_fallback_exhaustion(self):
        # Nonstop base miss (1), nonstop exp r1 miss (2),
        # fallback base on expanded window miss (2),
        # fallback exp r1 miss (2).
        adapter = _adapter_returning(
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
            _EMPTY,
        )

        _options, trace = search_leg(
            _leg(),
            adapter,
            fallback=_FALLBACK,
            expand_on_fallback=True,
            max_expansion_rounds=1,
        )

        assert trace.fallback_used is True
        assert trace.fallback_exhausted is True
        assert trace.final_status is SearchOutcome.NO_RESULTS_AFTER_FALLBACK

    def test_trace_counts_span_all_phases(self):
        # Nonstop miss (1), fallback fail (1).
        fail_resp = SearchResponse(
            options=(),
            failure=ApiFailureClassification.UNKNOWN,
        )
        adapter = _adapter_returning(_EMPTY, fail_resp)

        _options, trace = search_leg(_leg(), adapter, fallback=_FALLBACK)

        assert trace.attempted_queries == 2
        assert trace.successful_queries == 1
        assert trace.failed_queries == 1
