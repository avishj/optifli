# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Leg-level search policy: base window, expansion, and fallback."""

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from optifli.models.itinerary import Leg
from optifli.models.window import DepartureWindow
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

_EXPANSION_STEP = timedelta(hours=1)


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


def _expand_window(
    window: DepartureWindow,
    rounds: int,
) -> DepartureWindow:
    """Symmetrically widen a departure window by *rounds* expansion steps."""
    delta = _EXPANSION_STEP * rounds
    return DepartureWindow(
        start=window.start - delta,
        end=window.end + delta,
    )


def _build_expanded_leg(leg: Leg, rounds: int) -> Leg:
    """Return a copy of *leg* with a symmetrically expanded window."""
    return Leg(
        origin=leg.origin,
        destination=leg.destination,
        departure_window=_expand_window(leg.departure_window, rounds),
        arrival_cutoff=leg.arrival_cutoff,
    )


def search_leg(
    leg: Leg,
    adapter: FliAdapter,
    *,
    max_expansion_rounds: int = 0,
) -> tuple[list[LegOption], LegSearchTrace]:
    """Execute non-stop search with optional expansion for a single leg.

    Returns the collected options and a trace of the execution.
    """
    acc = _SearchAccumulator()
    base_hit = False
    expansion_rounds_used = 0
    searched_window = leg.departure_window

    # --- base window ---
    slices = build_local_query_slices(leg)
    _run_slices(slices, StopMode.NON_STOP, adapter, acc)

    if acc.has_results:
        base_hit = True
    else:
        # --- expansion rounds ---
        for round_num in range(1, max_expansion_rounds + 1):
            expanded_leg = _build_expanded_leg(leg, round_num)
            searched_window = expanded_leg.departure_window
            expansion_rounds_used = round_num

            slices = build_local_query_slices(expanded_leg)
            _run_slices(slices, StopMode.NON_STOP, adapter, acc)

            if acc.has_results:
                break

    status = _resolve_nonstop_outcome(
        has_results=acc.has_results,
        expanded=expansion_rounds_used > 0,
    )

    trace = LegSearchTrace(
        attempted_queries=acc.attempted,
        successful_queries=acc.successful,
        failed_queries=acc.failed,
        base_window_hit=base_hit,
        expansion_rounds=expansion_rounds_used,
        final_status=status,
        window_start=searched_window.start,
        window_end=searched_window.end,
    )

    logger.debug(
        "Leg %s->%s search: %s (%d option(s), %d expansion round(s))",
        "/".join(leg.origin.airports),
        "/".join(leg.destination.airports),
        status.value,
        len(acc.options),
        expansion_rounds_used,
    )

    return acc.options, trace


def _resolve_nonstop_outcome(
    *,
    has_results: bool,
    expanded: bool,
) -> SearchOutcome:
    """Determine the search outcome after non-stop phases."""
    if has_results:
        return SearchOutcome.RESULTS_FOUND
    if expanded:
        return SearchOutcome.NO_RESULTS_AFTER_EXPANSION
    return SearchOutcome.NO_RESULTS_BASE_WINDOW
