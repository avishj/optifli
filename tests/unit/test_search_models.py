# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for search enums."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from optifli.search import (
    ApiFailureClassification,
    FallbackBehavior,
    LegSearchTrace,
    SearchOutcome,
    SearchPolicy,
    StopMode,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("enum_type", "expected_values"),
    [
        (
            StopMode,
            {
                "NON_STOP": "non-stop",
                "ONE_STOP": "one-stop",
            },
        ),
        (
            FallbackBehavior,
            {
                "DISABLED": "disabled",
                "ONE_STOP": "one-stop",
            },
        ),
        (
            SearchOutcome,
            {
                "RESULTS_FOUND": "RESULTS_FOUND",
                "NO_RESULTS_BASE_WINDOW": "NO_RESULTS_BASE_WINDOW",
                "NO_RESULTS_AFTER_EXPANSION": "NO_RESULTS_AFTER_EXPANSION",
                "NO_RESULTS_AFTER_FALLBACK": "NO_RESULTS_AFTER_FALLBACK",
            },
        ),
        (
            ApiFailureClassification,
            {
                "NO_INVENTORY": "no-inventory",
                "RATE_LIMITED": "rate-limited",
                "UNKNOWN": "unknown",
            },
        ),
    ],
)
def test_enum_values(enum_type, expected_values):
    assert {member.name: member.value for member in enum_type} == expected_values


@pytest.mark.parametrize(
    ("enum_type", "raw_value"),
    [
        (StopMode, "non-stop"),
        (FallbackBehavior, "one-stop"),
        (SearchOutcome, "NO_RESULTS_AFTER_EXPANSION"),
        (ApiFailureClassification, "rate-limited"),
    ],
)
def test_enum_round_trip(enum_type, raw_value):
    member = enum_type(raw_value)
    assert member.value == raw_value
    assert enum_type(member.value) is member


class TestSearchPolicy:
    def test_default_values(self):
        policy = SearchPolicy()
        assert policy.max_expansion_rounds == 0
        assert policy.fallback is FallbackBehavior.DISABLED
        assert policy.expand_on_fallback is False
        assert policy.max_requests is None

    def test_valid_custom_values(self):
        policy = SearchPolicy(
            max_expansion_rounds=2,
            fallback=FallbackBehavior.ONE_STOP,
            expand_on_fallback=True,
            max_requests=100,
        )
        assert policy.max_expansion_rounds == 2
        assert policy.max_requests == 100

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            SearchPolicy(unknown="field")


class TestLegSearchTrace:
    def test_alias_generator_to_camel(self):
        trace = LegSearchTrace(
            attempted_queries=1,
            successful_queries=1,
            failed_queries=0,
            base_window_hit=True,
            final_status=SearchOutcome.RESULTS_FOUND,
            window_start=datetime(2026, 7, 16, 10, 0, tzinfo=UTC),
            window_end=datetime(2026, 7, 16, 18, 0, tzinfo=UTC),
        )
        data = trace.model_dump(by_alias=True)
        assert "attemptedQueries" in data
        assert "baseWindowHit" in data
        assert "finalStatus" in data

    def test_exact_count_validation(self):
        dt = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
        with pytest.raises(ValidationError, match="must equal 'attempted_queries'"):
            LegSearchTrace(
                attempted_queries=2,
                successful_queries=1,
                failed_queries=0,  # 1+0 != 2
                final_status=SearchOutcome.RESULTS_FOUND,
                window_start=dt,
                window_end=dt.replace(hour=18),
            )
