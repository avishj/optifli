# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Duration value object for stay lengths."""

import re
from datetime import timedelta

from pydantic import BaseModel, model_validator

_DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*([dDhH])$")


class Duration(BaseModel, frozen=True):
    """A positive duration expressed as days or hours.

    Accepted string formats: ``"2d"``, ``"1.5d"``, ``"12h"``, ``"2.5h"``.
    Compound formats like ``"1d12h"`` are rejected.
    """

    _timedelta: timedelta

    raw: str
    """The original string representation."""

    @model_validator(mode="before")
    @classmethod
    def _parse(cls, data: object) -> dict[str, object]:
        """Parse a duration string into a validated dict."""
        if isinstance(data, str):
            data = {"raw": data}
        if not isinstance(data, dict):
            msg = "Expected a duration string like '2d' or '12h'"
            raise TypeError(msg)
        raw = data.get("raw", "")
        if not isinstance(raw, str) or not raw.strip():
            msg = "Duration cannot be empty"
            raise ValueError(msg)
        raw = raw.strip()
        match = _DURATION_RE.match(raw)
        if not match:
            msg = (
                f"Invalid duration format: '{raw}'. "
                "Use a single unit like '2d', '1.5d', '12h', or '2.5h'"
            )
            raise ValueError(msg)
        value = float(match.group(1))
        if value <= 0:
            msg = "Duration must be positive"
            raise ValueError(msg)
        data["raw"] = raw
        return data

    def model_post_init(self, _context: object) -> None:
        """Compute the internal timedelta after validation."""
        match = _DURATION_RE.match(self.raw)
        assert match  # guaranteed by _parse  # noqa: S101
        value = float(match.group(1))
        unit = match.group(2).lower()
        td = timedelta(days=value) if unit == "d" else timedelta(hours=value)
        object.__setattr__(self, "_timedelta", td)

    @property
    def timedelta(self) -> timedelta:
        """Return the underlying ``timedelta``."""
        return self._timedelta

    @property
    def total_hours(self) -> float:
        """Total duration in hours."""
        return self._timedelta.total_seconds() / 3600

    @property
    def total_days(self) -> float:
        """Total duration in days."""
        return self._timedelta.total_seconds() / 86400

    def __str__(self) -> str:
        """Return the original duration string."""
        return self.raw

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"Duration('{self.raw}')"
