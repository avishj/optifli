# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Provider-agnostic search enums."""

from enum import StrEnum


class StopMode(StrEnum):
    """Stop constraints that Optifli can apply to a leg search."""

    NON_STOP = "non-stop"
    ONE_STOP = "one-stop"


class FallbackBehavior(StrEnum):
    """Fallback behavior after non-stop search exhaustion."""

    DISABLED = "disabled"
    ONE_STOP = "one-stop"


class SearchOutcome(StrEnum):
    """Final outcome values defined by ES-001."""

    RESULTS_FOUND = "RESULTS_FOUND"
    NO_RESULTS_BASE_WINDOW = "NO_RESULTS_BASE_WINDOW"
    NO_RESULTS_AFTER_EXPANSION = "NO_RESULTS_AFTER_EXPANSION"
    NO_RESULTS_AFTER_FALLBACK = "NO_RESULTS_AFTER_FALLBACK"


class ApiFailureClassification(StrEnum):
    """Final provider-failure classifications defined by ES-004."""

    NO_INVENTORY = "no-inventory"
    RATE_LIMITED = "rate-limited"
    UNKNOWN = "unknown"
