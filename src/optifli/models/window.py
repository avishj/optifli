# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Departure window and arrival cutoff models."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, model_validator


def _require_tz_aware(dt: datetime, field: str) -> None:
    """Raise if *dt* is a naive datetime."""
    if dt.tzinfo is None:
        msg = (
            f"'{field}' must be timezone-aware "
            "(e.g. '2026-07-16T19:00:00+05:30' or '2026-07-16T19:00:00Z')"
        )
        raise ValueError(msg)


class DepartureWindow(BaseModel, frozen=True):
    """A TZ-aware time window for departures.

    Both ``start`` and ``end`` must carry timezone info, and
    ``start`` must be strictly before ``end``.
    """

    start: datetime
    end: datetime

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        _require_tz_aware(self.start, "start")
        _require_tz_aware(self.end, "end")
        if self.start >= self.end:
            msg = "'start' must be before 'end'"
            raise ValueError(msg)
        return self
