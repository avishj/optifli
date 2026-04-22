# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Leg-level search policy: base window, expansion, and fallback."""

import logging
from dataclasses import dataclass, field

from optifli.models.itinerary import Leg
from optifli.search.fli_adapter import FliAdapter, LegOption, SearchResponse
from optifli.search.fli_queries import build_search_filters
from optifli.search.models import (
    ApiFailureClassification,
    LegSearchTrace,
    SearchOutcome,
    StopMode,
)
from optifli.search.windows import LocalQuerySlice, build_local_query_slices

logger = logging.getLogger(__name__)


@dataclass
class _SearchAccumulator:
    """Mutable counters for one leg search policy run."""

    attempted: int = 0
    successful: int = 0
    failed: int = 0
    options: list[LegOption] = field(default_factory=list)
    last_failure: ApiFailureClassification | None = None

    @property
    def has_results(self) -> bool:
        return len(self.options) > 0

    def record(self, response: SearchResponse) -> None:
        """Record one adapter response."""
        self.attempted += 1
        if response.failure is not None:
            self.failed += 1
            self.last_failure = response.failure
        else:
            self.successful += 1
            self.options.extend(response.options)


def _run_slices(
    slices: list[LocalQuerySlice],
    stop_mode: StopMode,
    adapter: FliAdapter,
    acc: _SearchAccumulator,
) -> None:
    """Search all slices for a given stop mode, updating *acc* in place."""
    for query_slice in slices:
        filters = build_search_filters(query_slice, stop_mode)
        response = adapter.search(filters)
        acc.record(response)


def search_leg(
    leg: Leg,
    adapter: FliAdapter,
) -> tuple[list[LegOption], LegSearchTrace]:
    """Execute base-window non-stop search for a single leg.

    Returns the collected options and a trace of the execution.
    """
    slices = build_local_query_slices(leg)
    acc = _SearchAccumulator()

    _run_slices(slices, StopMode.NON_STOP, adapter, acc)

    if acc.has_results:
        status = SearchOutcome.RESULTS_FOUND
    else:
        status = SearchOutcome.NO_RESULTS_BASE_WINDOW

    trace = LegSearchTrace(
        attempted_queries=acc.attempted,
        successful_queries=acc.successful,
        failed_queries=acc.failed,
        base_window_hit=acc.has_results,
        final_status=status,
        window_start=leg.departure_window.start,
        window_end=leg.departure_window.end,
    )

    logger.debug(
        "Leg %s→%s base search: %s (%d option(s))",
        "/".join(leg.origin.airports),
        "/".join(leg.destination.airports),
        status.value,
        len(acc.options),
    )

    return acc.options, trace
