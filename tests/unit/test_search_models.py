# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for search enums."""

import pytest

from optifli.search import (
    ApiFailureClassification,
    FallbackBehavior,
    SearchOutcome,
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
