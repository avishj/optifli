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
    FallbackBehavior,
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


@dataclass
class _NonstopResult:
    """Outcome of the nonstop search phase (base + expansion)."""

    base_hit: bool
    expansion_rounds: int
    searched_window: DepartureWindow


def _run_nonstop_phase(
    leg: Leg,
    adapter: FliAdapter,
    acc: _SearchAccumulator,
    *,
    max_expansion_rounds: int,
) -> _NonstopResult:
    """Execute base window search and optional expansion rounds."""
    searched_window = leg.departure_window
    expansion_rounds_used = 0

    slices = build_local_query_slices(leg)
    _run_slices(slices, StopMode.NON_STOP, adapter, acc)

    if not acc.has_results:
        for round_num in range(1, max_expansion_rounds + 1):
            expanded_leg = _build_expanded_leg(leg, round_num)
            searched_window = expanded_leg.departure_window
            expansion_rounds_used = round_num

            slices = build_local_query_slices(expanded_leg)
            _run_slices(slices, StopMode.NON_STOP, adapter, acc)

            if acc.has_results:
                break

    return _NonstopResult(
        base_hit=acc.has_results and expansion_rounds_used == 0,
        expansion_rounds=expansion_rounds_used,
        searched_window=searched_window,
    )


def _run_fallback_phase(  # noqa: PLR0913
    leg: Leg,
    adapter: FliAdapter,
    acc: _SearchAccumulator,
    *,
    searched_window: DepartureWindow,
    expand: bool,
    max_expansion_rounds: int,
) -> DepartureWindow:
    """Execute one-stop fallback search, returning the final searched window."""
    fallback_leg = Leg(
        origin=leg.origin,
        destination=leg.destination,
        departure_window=searched_window,
        arrival_cutoff=leg.arrival_cutoff,
    )

    slices = build_local_query_slices(fallback_leg)
    _run_slices(slices, StopMode.ONE_STOP, adapter, acc)

    if acc.has_results or not expand:
        return searched_window

    for round_num in range(1, max_expansion_rounds + 1):
        expanded_leg = _build_expanded_leg(leg, round_num)
        searched_window = expanded_leg.departure_window

        slices = build_local_query_slices(expanded_leg)
        _run_slices(slices, StopMode.ONE_STOP, adapter, acc)

        if acc.has_results:
            break

    return searched_window


def search_leg(
    leg: Leg,
    adapter: FliAdapter,
    *,
    max_expansion_rounds: int = 0,
    fallback: FallbackBehavior = FallbackBehavior.DISABLED,
    expand_on_fallback: bool = False,
) -> tuple[list[LegOption], LegSearchTrace]:
    """Execute search policy for a single leg.

    Returns the collected options and a trace of the execution.
    """
    acc = _SearchAccumulator()

    nonstop = _run_nonstop_phase(
        leg,
        adapter,
        acc,
        max_expansion_rounds=max_expansion_rounds,
    )
    searched_window = nonstop.searched_window
    fallback_used = False
    fallback_exhausted = False

    if not acc.has_results and fallback is FallbackBehavior.ONE_STOP:
        fallback_used = True
        searched_window = _run_fallback_phase(
            leg,
            adapter,
            acc,
            searched_window=nonstop.searched_window,
            expand=expand_on_fallback,
            max_expansion_rounds=max_expansion_rounds,
        )
        fallback_exhausted = not acc.has_results

    status = _resolve_outcome(
        has_results=acc.has_results,
        expanded=nonstop.expansion_rounds > 0,
        fallback_used=fallback_used,
    )

    trace = LegSearchTrace(
        attempted_queries=acc.attempted,
        successful_queries=acc.successful,
        failed_queries=acc.failed,
        base_window_hit=nonstop.base_hit,
        expansion_rounds=nonstop.expansion_rounds,
        fallback_used=fallback_used,
        fallback_exhausted=fallback_exhausted,
        final_status=status,
        window_start=searched_window.start,
        window_end=searched_window.end,
    )

    logger.debug(
        "Leg %s->%s search: %s (%d option(s), %d expansion round(s), fallback=%s)",
        "/".join(leg.origin.airports),
        "/".join(leg.destination.airports),
        status.value,
        len(acc.options),
        nonstop.expansion_rounds,
        fallback_used,
    )

    return acc.options, trace


def _resolve_outcome(
    *,
    has_results: bool,
    expanded: bool,
    fallback_used: bool,
) -> SearchOutcome:
    """Determine the final search outcome."""
    if has_results:
        return SearchOutcome.RESULTS_FOUND
    if fallback_used:
        return SearchOutcome.NO_RESULTS_AFTER_FALLBACK
    if expanded:
        return SearchOutcome.NO_RESULTS_AFTER_EXPANSION
    return SearchOutcome.NO_RESULTS_BASE_WINDOW
