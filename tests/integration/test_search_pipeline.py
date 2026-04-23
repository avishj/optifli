# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests: candidate generation through search with a fake provider."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from optifli.engine import generate_candidates
from optifli.profile import load_profile
from optifli.search import (
    FallbackBehavior,
    FliAdapter,
    LegOption,
    SearchPolicy,
    SearchResponse,
    SegmentDetail,
    search_candidate,
)
from optifli.search.models import SearchOutcome

pytestmark = pytest.mark.integration


def _option() -> LegOption:
    return LegOption(
        segments=(
            SegmentDetail(
                airline="XX",
                flight_number="XX100",
                departure_airport="DEL",
                arrival_airport="HAN",
                departure_time=datetime(2026, 7, 16, 10, 0),
                arrival_time=datetime(2026, 7, 16, 16, 0),
                duration_minutes=360,
            ),
        ),
        price=150.0,
        currency="USD",
        total_duration_minutes=360,
        stops=0,
    )


_HIT = SearchResponse(options=(_option(),), failure=None)
_MISS = SearchResponse(options=(), failure=None)


def _always_hit_adapter(call_count: int) -> FliAdapter:
    mock_client = MagicMock()
    adapter = FliAdapter(client=mock_client)
    adapter.search = MagicMock(side_effect=lambda *args, **kwargs: _HIT)  # ty: ignore[invalid-assignment]
    return adapter


def _always_miss_adapter(call_count: int) -> FliAdapter:
    mock_client = MagicMock()
    adapter = FliAdapter(client=mock_client)
    adapter.search = MagicMock(side_effect=lambda *args, **kwargs: _MISS)  # ty: ignore[invalid-assignment]
    return adapter


class TestSearchPipeline:
    """End-to-end: generate candidates from a profile, search with fake provider."""

    @pytest.fixture
    def forward_candidate(self, profiles_dir):
        it = load_profile(profiles_dir / "minimal.json")
        candidates = generate_candidates(it)
        assert len(candidates) == 1
        return candidates[0]

    def test_all_legs_searched(self, forward_candidate):
        leg_count = len(forward_candidate.legs)
        # Generous adapter: enough hits for all slices across all legs.
        adapter = _always_hit_adapter(call_count=leg_count * 4)

        all_opts, result = search_candidate(forward_candidate, adapter)

        assert result.completed is True
        assert len(result.legs) == leg_count
        for opts in all_opts:
            assert len(opts) >= 1

    def test_deterministic_across_runs(self, forward_candidate):
        adapter1 = _always_hit_adapter(call_count=50)
        adapter2 = _always_hit_adapter(call_count=50)

        _, r1 = search_candidate(forward_candidate, adapter1)
        _, r2 = search_candidate(forward_candidate, adapter2)

        assert len(r1.legs) == len(r2.legs)
        for l1, l2 in zip(r1.legs, r2.legs, strict=True):
            assert l1.trace.attempted_queries == l2.trace.attempted_queries
            assert l1.trace.final_status == l2.trace.final_status

    def test_no_results_deterministic(self, forward_candidate):
        adapter = _always_miss_adapter(call_count=50)

        _, result = search_candidate(forward_candidate, adapter)

        assert result.completed is True
        for leg_result in result.legs:
            assert leg_result.trace.final_status is SearchOutcome.NO_RESULTS_BASE_WINDOW

    def test_budget_preserves_partial(self, forward_candidate):
        adapter = _always_hit_adapter(call_count=50)

        _all_opts, result = search_candidate(
            forward_candidate,
            adapter,
            policy=SearchPolicy(max_requests=1),
        )

        assert result.completed is False
        assert result.request_budget_exhausted is True
        assert len(result.legs) >= 1
        assert len(result.legs) < len(forward_candidate.legs)


class TestSearchPipelineBenchmark:
    """Benchmark profile: DEL -> 4 dests -> DEL, direction BOTH."""

    @pytest.fixture
    def candidates(self, profiles_dir):
        it = load_profile(profiles_dir / "benchmark.json")
        return generate_candidates(it)

    def test_both_directions_searched(self, candidates):
        for candidate in candidates:
            adapter = _always_hit_adapter(call_count=100)
            _all_opts, result = search_candidate(candidate, adapter)

            assert result.completed is True
            assert len(result.legs) == len(candidate.legs)

    def test_fallback_engages_on_miss(self, candidates):
        candidate = candidates[0]
        # Enough misses to exhaust nonstop, then hits on fallback.
        adapter = _always_miss_adapter(call_count=100)

        _, result = search_candidate(
            candidate,
            adapter,
            policy=SearchPolicy(fallback=FallbackBehavior.ONE_STOP),
        )

        assert result.completed is True
        for leg_result in result.legs:
            assert leg_result.trace.fallback_used is True
            assert (
                leg_result.trace.final_status is SearchOutcome.NO_RESULTS_AFTER_FALLBACK
            )
