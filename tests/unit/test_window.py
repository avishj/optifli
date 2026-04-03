# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for DepartureWindow and ArrivalCutoff models."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from optifli.models.window import ArrivalCutoff, DepartureWindow

pytestmark = pytest.mark.unit


class TestDepartureWindowValid:
    def test_utc_offset(self):
        w = DepartureWindow(
            start=datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
            end=datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
        )
        assert w.start < w.end

    def test_iana_timezone(self):
        tz = ZoneInfo("Asia/Kolkata")
        w = DepartureWindow(
            start=datetime(2026, 7, 16, 19, 0, tzinfo=tz),
            end=datetime(2026, 7, 17, 11, 0, tzinfo=tz),
        )
        assert w.start.tzinfo is not None
        assert w.end.tzinfo is not None

    def test_cross_day_window(self):
        tz = ZoneInfo("America/New_York")
        w = DepartureWindow(
            start=datetime(2026, 7, 16, 23, 0, tzinfo=tz),
            end=datetime(2026, 7, 17, 3, 0, tzinfo=tz),
        )
        assert w.start < w.end

    def test_from_iso_strings(self):
        w = DepartureWindow.model_validate(
            {
                "start": "2026-07-16T19:00:00+05:30",
                "end": "2026-07-17T11:00:00+05:30",
            }
        )
        assert w.start.tzinfo is not None


class TestDepartureWindowInvalid:
    def test_naive_start(self):
        with pytest.raises(ValidationError, match="timezone-aware"):
            DepartureWindow(
                start=datetime(2026, 7, 16, 19, 0),
                end=datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
            )

    def test_naive_end(self):
        with pytest.raises(ValidationError, match="timezone-aware"):
            DepartureWindow(
                start=datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
                end=datetime(2026, 7, 17, 11, 0),
            )

    def test_end_equals_start(self):
        dt = datetime(2026, 7, 16, 19, 0, tzinfo=UTC)
        with pytest.raises(ValidationError, match="before"):
            DepartureWindow(start=dt, end=dt)

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="before"):
            DepartureWindow(
                start=datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
                end=datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
            )

    def test_missing_start(self):
        with pytest.raises(ValidationError):
            DepartureWindow(
                end=datetime(2026, 7, 17, 11, 0, tzinfo=UTC),
            )

    def test_missing_end(self):
        with pytest.raises(ValidationError):
            DepartureWindow(
                start=datetime(2026, 7, 16, 19, 0, tzinfo=UTC),
            )


class TestArrivalCutoffValid:
    def test_utc(self):
        c = ArrivalCutoff(deadline=datetime(2026, 7, 17, 14, 0, tzinfo=UTC))
        assert c.deadline.tzinfo is not None

    def test_iana_timezone(self):
        tz = ZoneInfo("Asia/Kolkata")
        c = ArrivalCutoff(deadline=datetime(2026, 7, 17, 14, 0, tzinfo=tz))
        assert c.deadline.tzinfo is not None

    def test_from_iso_string(self):
        c = ArrivalCutoff.model_validate({"deadline": "2026-07-17T14:00:00+05:30"})
        assert c.deadline.tzinfo is not None


class TestArrivalCutoffInvalid:
    def test_naive_datetime(self):
        with pytest.raises(ValidationError, match="timezone-aware"):
            ArrivalCutoff(deadline=datetime(2026, 7, 17, 14, 0))

    def test_missing_deadline(self):
        with pytest.raises(ValidationError):
            ArrivalCutoff()
