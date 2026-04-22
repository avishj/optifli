# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Search-domain models and execution helpers."""

from optifli.search.fli_adapter import (
    FliAdapter,
    LegOption,
    SearchResponse,
    SegmentDetail,
    classify_error,
    normalize_leg,
    normalize_result,
)
from optifli.search.fli_client import FliClient
from optifli.search.fli_queries import build_search_filters
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
    "FliAdapter",
    "FliClient",
    "LegOption",
    "LegSearchResult",
    "LegSearchTrace",
    "LocalQuerySlice",
    "SearchOutcome",
    "SearchResponse",
    "SegmentDetail",
    "StopMode",
    "build_local_query_slices",
    "build_search_filters",
    "classify_error",
    "group_airports_by_timezone",
    "normalize_leg",
    "normalize_result",
    "split_window_by_local_date",
]
