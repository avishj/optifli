# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for Duration model."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from optifli.models.duration import Duration

pytestmark = pytest.mark.unit


class TestValidParsing:
    def test_days_integer(self):
        d = Duration(raw="2d")
        assert d.total_days == 2.0
        assert d.total_hours == 48.0

    def test_days_fractional(self):
        d = Duration(raw="1.5d")
        assert d.total_days == 1.5
        assert d.total_hours == 36.0

    def test_half_day(self):
        d = Duration(raw="0.5d")
        assert d.total_hours == 12.0

    def test_hours_integer(self):
        d = Duration(raw="12h")
        assert d.total_hours == 12.0

    def test_hours_large(self):
        d = Duration(raw="30h")
        assert d.total_hours == 30.0
        assert d.total_days == pytest.approx(30 / 24)

    def test_hours_fractional(self):
        d = Duration(raw="2.5h")
        assert d.total_hours == 2.5
        assert d.timedelta == timedelta(hours=2, minutes=30)

    def test_uppercase_unit(self):
        d = Duration(raw="3D")
        assert d.total_days == 3.0

    def test_uppercase_hours(self):
        d = Duration(raw="6H")
        assert d.total_hours == 6.0


class TestFromString:
    def test_string_shorthand(self):
        d = Duration.model_validate("2d")
        assert d.total_days == 2.0

    def test_string_hours(self):
        d = Duration.model_validate("12h")
        assert d.total_hours == 12.0


class TestRejection:
    def test_compound_format(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Duration.model_validate("1d12h")

    def test_zero_duration(self):
        with pytest.raises(ValidationError, match="positive"):
            Duration.model_validate("0d")

    def test_zero_hours(self):
        with pytest.raises(ValidationError, match="positive"):
            Duration.model_validate("0h")

    def test_negative_not_matched(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Duration.model_validate("-1d")

    def test_empty_string(self):
        with pytest.raises(ValidationError, match="empty"):
            Duration.model_validate("")

    def test_whitespace_only(self):
        with pytest.raises(ValidationError, match="empty"):
            Duration.model_validate("   ")

    def test_no_unit(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Duration.model_validate("12")

    def test_invalid_unit(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Duration.model_validate("2m")

    def test_text(self):
        with pytest.raises(ValidationError, match="Invalid duration format"):
            Duration.model_validate("two days")


class TestRoundTrip:
    def test_serialize_deserialize(self):
        original = Duration.model_validate("1.5d")
        data = original.model_dump()
        restored = Duration.model_validate(data)
        assert restored.total_hours == original.total_hours

    def test_json_round_trip(self):
        original = Duration.model_validate("2.5h")
        json_str = original.model_dump_json()
        restored = Duration.model_validate_json(json_str)
        assert restored.total_hours == original.total_hours


class TestProperties:
    def test_timedelta_property(self):
        d = Duration.model_validate("1d")
        assert d.timedelta == timedelta(days=1)

    def test_str(self):
        d = Duration.model_validate("2d")
        assert str(d) == "2d"

    def test_repr(self):
        d = Duration.model_validate("12h")
        assert repr(d) == "Duration('12h')"
