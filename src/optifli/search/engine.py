# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Candidate-level search: iterate the leg policy across a route candidate."""

import logging

from optifli.engine.candidates import RouteCandidate
from optifli.search.fli_adapter import FliAdapter, LegOption
from optifli.search.models import (
    CandidateSearchResult,
    FallbackBehavior,
    LegSearchResult,
)
from optifli.search.policy import search_leg

logger = logging.getLogger(__name__)


def search_candidate(
    candidate: RouteCandidate,
    adapter: FliAdapter,
    *,
    max_expansion_rounds: int = 0,
    fallback: FallbackBehavior = FallbackBehavior.DISABLED,
    expand_on_fallback: bool = False,
) -> tuple[list[list[LegOption]], CandidateSearchResult]:
    """Search every leg in a route candidate.

    Returns per-leg option lists and a ``CandidateSearchResult`` with traces.
    """
    all_options: list[list[LegOption]] = []
    leg_results: list[LegSearchResult] = []

    for leg in candidate.legs:
        options, trace, failure = search_leg(
            leg,
            adapter,
            max_expansion_rounds=max_expansion_rounds,
            fallback=fallback,
            expand_on_fallback=expand_on_fallback,
        )
        all_options.append(options)
        leg_results.append(
            LegSearchResult(leg=leg, trace=trace, api_failure=failure),
        )

    result = CandidateSearchResult(
        candidate=candidate,
        legs=leg_results,
    )

    logger.debug(
        "Candidate %s: %d/%d leg(s) with results",
        candidate.direction.value,
        sum(1 for opts in all_options if opts),
        len(candidate.legs),
    )

    return all_options, result
