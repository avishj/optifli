# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for IATACode validator."""

import pytest
from pydantic import BaseModel, ValidationError

from optifli.models.airport import IATACode

pytestmark = pytest.mark.unit


class _IATAModel(BaseModel):
    code: IATACode


class TestValidCodes:
    def test_uppercase(self):
        m = _IATAModel(code="DEL")
        assert m.code == "DEL"

    def test_lowercase_normalised(self):
        m = _IATAModel(code="del")
        assert m.code == "DEL"

    def test_mixed_case(self):
        m = _IATAModel(code="jFk")
        assert m.code == "JFK"

    def test_another_valid_code(self):
        m = _IATAModel(code="JFK")
        assert m.code == "JFK"


class TestInvalidCodes:
    def test_too_short(self):
        with pytest.raises(ValidationError, match="not a valid IATA code"):
            _IATAModel(code="de")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="not a valid IATA code"):
            _IATAModel(code="DELH")

    def test_digits_in_code(self):
        with pytest.raises(ValidationError, match="not a valid IATA code"):
            _IATAModel(code="12A")

    def test_empty_string(self):
        with pytest.raises(ValidationError, match="empty"):
            _IATAModel(code="")

    def test_not_in_fli_enum(self):
        with pytest.raises(ValidationError, match="not a recognized IATA airport"):
            _IATAModel(code="ZZZ")
