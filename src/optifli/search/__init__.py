# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Search-domain models and execution helpers."""

from optifli.search.models import (
    ApiFailureClassification,
    CandidateSearchResult,
    FallbackBehavior,
    LegSearchResult,
    LegSearchTrace,
    SearchOutcome,
    StopMode,
)
from optifli.search.windows import (
    LocalQuerySlice,
    build_local_query_slices,
    group_airports_by_timezone,
    split_window_by_local_date,
)

__all__: list[str] = [
    "ApiFailureClassification",
    "CandidateSearchResult",
    "FallbackBehavior",
    "LegSearchResult",
    "LegSearchTrace",
    "LocalQuerySlice",
    "SearchOutcome",
    "StopMode",
    "build_local_query_slices",
    "group_airports_by_timezone",
    "split_window_by_local_date",
]
