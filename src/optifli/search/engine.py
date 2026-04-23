# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Candidate-level search: iterate the leg policy across a route candidate."""

import logging

from optifli.engine.candidates import RouteCandidate
from optifli.search.fli_adapter import FliAdapter, LegOption
from optifli.search.models import (
    CandidateSearchResult,
    LegSearchResult,
    SearchPolicy,
)
from optifli.search.policy import search_leg

logger = logging.getLogger(__name__)


def search_candidate(
    candidate: RouteCandidate,
    adapter: FliAdapter,
    policy: SearchPolicy | None = None,
) -> tuple[list[list[LegOption]], CandidateSearchResult]:
    """Search every leg in a route candidate.

    Returns per-leg option lists and a ``CandidateSearchResult`` with traces.
    Stops early when *max_requests* is exhausted, preserving partial results.
    """
    if policy is None:
        policy = SearchPolicy()

    all_options: list[list[LegOption]] = []
    leg_results: list[LegSearchResult] = []
    requests_used = 0
    budget_exhausted = False

    for leg in candidate.legs:
        if policy.max_requests is not None and requests_used >= policy.max_requests:
            budget_exhausted = True
            logger.warning(
                "Request budget exhausted (%d/%d) - skipping remaining legs",
                requests_used,
                policy.max_requests,
            )
            break

        options, trace, failure = search_leg(
            leg,
            adapter,
            policy,
            used_requests=requests_used,
        )
        requests_used += trace.attempted_queries
        all_options.append(options)
        leg_results.append(
            LegSearchResult(leg=leg, trace=trace, api_failure=failure),
        )

    completed = len(leg_results) == len(candidate.legs) and not budget_exhausted
    result = CandidateSearchResult(
        candidate=candidate,
        legs=leg_results,
        completed=completed,
        request_budget_exhausted=budget_exhausted,
    )

    logger.debug(
        "Candidate %s: %d/%d leg(s) searched, completed=%s",
        candidate.direction.value,
        len(leg_results),
        len(candidate.legs),
        completed,
    )

    return all_options, result
