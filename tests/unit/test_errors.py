# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for error formatting."""

import pytest
from pydantic import ValidationError

from optifli.errors import InputError, format_errors, from_pydantic
from optifli.models.itinerary import Itinerary

pytestmark = pytest.mark.unit


class TestInputError:
    def test_fields(self):
        err = InputError(field="origin", reason="required", hint="add an origin")
        assert err.field == "origin"
        assert err.reason == "required"
        assert err.hint == "add an origin"

    def test_default_hint_empty(self):
        err = InputError(field="stay", reason="invalid")
        assert err.hint == ""

    def test_frozen(self):
        err = InputError(field="x", reason="y")
        with pytest.raises(AttributeError):
            err.field = "z"


class TestFormatErrors:
    def test_single_error(self):
        result = format_errors(
            [
                InputError(
                    field="origin", reason="is required", hint="provide a value"
                ),
            ]
        )
        assert "origin" in result
        assert "is required" in result
        assert "provide a value" in result

    def test_multiple_errors(self):
        result = format_errors(
            [
                InputError(field="stay", reason="invalid format"),
                InputError(field="airports", reason="empty list"),
            ]
        )
        assert "stay" in result
        assert "airports" in result
        lines = [ln for ln in result.splitlines() if ln.strip()]
        assert len(lines) == 2

    def test_no_hint_omitted(self):
        result = format_errors(
            [
                InputError(field="x", reason="bad"),
            ]
        )
        assert "x" in result
        assert "bad" in result
        assert "()" not in result


class TestFromPydantic:
    def test_converts_validation_error(self):
        try:
            Itinerary(
                origin={"name": "Delhi", "airports": ["DEL"]},
                destinations=[],
                return_city={"name": "Delhi", "airports": ["DEL"]},
            )
        except ValidationError as exc:
            errors = from_pydantic(exc)

        assert len(errors) >= 1
        assert any("at least one" in e.reason for e in errors)

    def test_nested_error_includes_path(self):
        try:
            Itinerary(
                origin={"name": "Delhi", "airports": ["DEL"]},
                destinations=[
                    {"city": {"name": "Bad", "airports": ["ZZZ"]}, "stay": "2d"},
                ],
                return_city={"name": "Delhi", "airports": ["DEL"]},
            )
        except ValidationError as exc:
            errors = from_pydantic(exc)

        assert len(errors) >= 1
        assert any("destinations" in e.field for e in errors)
