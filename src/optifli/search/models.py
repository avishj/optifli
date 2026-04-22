# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Provider-agnostic search enums and result models."""

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    computed_field,
    model_validator,
)
from pydantic.alias_generators import to_camel

from optifli.engine.candidates import RouteCandidate
from optifli.models.itinerary import Leg


def _require_tz_aware(dt: datetime, field: str) -> None:
    """Raise if *dt* is a naive datetime."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        msg = f"'{field}' must be timezone-aware"
        raise ValueError(msg)


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


class SearchPolicy(BaseModel, frozen=True):
    """Encapsulates all search constraints and budgets."""

    model_config = ConfigDict(extra="forbid")

    max_expansion_rounds: NonNegativeInt = 0
    fallback: FallbackBehavior = FallbackBehavior.DISABLED
    expand_on_fallback: bool = False
    max_requests: int | None = None


class LegSearchTrace(BaseModel, frozen=True):
    """Trace fields for one leg search policy execution."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        alias_generator=to_camel,
    )

    attempted_queries: NonNegativeInt = 0
    successful_queries: NonNegativeInt = 0
    failed_queries: NonNegativeInt = 0
    base_window_hit: bool = False
    fallback_used: bool = False
    fallback_exhausted: bool = False
    expansion_rounds: NonNegativeInt = 0
    final_status: SearchOutcome
    window_start: datetime
    window_end: datetime

    @model_validator(mode="after")
    def _validate_counts(self) -> Self:
        if self.successful_queries + self.failed_queries != self.attempted_queries:
            msg = (
                f"'successful_queries' ({self.successful_queries}) + "
                f"'failed_queries' ({self.failed_queries}) must equal "
                f"'attempted_queries' ({self.attempted_queries})"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_outcome_flags(self) -> Self:
        if self.base_window_hit:
            if self.final_status is not SearchOutcome.RESULTS_FOUND:
                msg = "'base_window_hit' requires final_status=RESULTS_FOUND"
                raise ValueError(msg)
            if self.expansion_rounds > 0:
                msg = "'base_window_hit' requires 'expansion_rounds'=0"
                raise ValueError(msg)
        if self.fallback_exhausted:
            if not self.fallback_used:
                msg = "'fallback_exhausted' requires 'fallback_used'=True"
                raise ValueError(msg)
            if self.final_status is not SearchOutcome.NO_RESULTS_AFTER_FALLBACK:
                msg = (
                    "'fallback_exhausted' requires "
                    "final_status=NO_RESULTS_AFTER_FALLBACK"
                )
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        _require_tz_aware(self.window_start, "window_start")
        _require_tz_aware(self.window_end, "window_end")
        if self.window_start >= self.window_end:
            msg = "'window_start' must be before 'window_end'"
            raise ValueError(msg)
        return self


class LegSearchResult(BaseModel, frozen=True):
    """Search result metadata for one concrete itinerary leg."""

    model_config = ConfigDict(extra="forbid")

    leg: Leg
    trace: LegSearchTrace
    api_failure: ApiFailureClassification | None = None
    completed: bool = True

    @computed_field
    @property
    def partial(self) -> bool:
        """Whether the leg search returned partial progress only."""
        return not self.completed


class CandidateSearchResult(BaseModel, frozen=True):
    """Search result metadata for a whole route candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate: RouteCandidate
    legs: list[LegSearchResult]
    completed: bool = True
    request_budget_exhausted: bool = False

    @computed_field
    @property
    def partial(self) -> bool:
        """Whether the candidate search returned partial progress only."""
        return not self.completed

    @model_validator(mode="after")
    def _validate_completion_state(self) -> Self:
        if self.request_budget_exhausted and self.completed:
            msg = "'request_budget_exhausted' requires 'completed'=False"
            raise ValueError(msg)
        expected_legs = self.candidate.legs
        if not self.legs:
            msg = "'legs' must contain at least one leg search result"
            raise ValueError(msg)
        if len(self.legs) > len(expected_legs):
            msg = "'legs' cannot exceed candidate leg count"
            raise ValueError(msg)
        if self.completed and len(self.legs) != len(expected_legs):
            msg = "'completed' results must include every candidate leg"
            raise ValueError(msg)
        for index, leg_result in enumerate(self.legs):
            if leg_result.leg != expected_legs[index]:
                msg = (
                    f"Leg search result {index + 1} must match candidate leg "
                    f"{index + 1}"
                )
                raise ValueError(msg)
        return self
