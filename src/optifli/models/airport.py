# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""IATA airport code validation and city group model."""

import re
from typing import Annotated, Self

from fli.models import Airport
from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator

_IATA_RE = re.compile(r"^[A-Z]{3}$")


def _validate_iata(value: str) -> str:
    """Validate and normalise an IATA airport code."""
    if not isinstance(value, str) or not value.strip():
        msg = "IATA code cannot be empty"
        raise ValueError(msg)
    code = value.strip().upper()
    if not _IATA_RE.match(code):
        msg = (
            f"'{value}' is not a valid IATA code. "
            "Expected exactly 3 letters (e.g. 'DEL', 'JFK')"
        )
        raise ValueError(msg)
    try:
        Airport[code]
    except KeyError:
        msg = f"{code} is not a recognized IATA airport code"
        raise ValueError(msg) from None
    return code


IATACode = Annotated[str, BeforeValidator(_validate_iata)]
"""A 3-letter IATA airport code validated against the FLI airport database."""


class CityGroup(BaseModel, frozen=True):
    """A named group of airports representing a city or region.

    Attributes:
        name: User-facing label (e.g. ``"Delhi"``).
        airports: Airports to search (at least one required).
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    airports: list[IATACode]

    @model_validator(mode="after")
    def _validate_fields(self) -> Self:
        if not self.name.strip():
            msg = "'name' must not be empty"
            raise ValueError(msg)

        if not self.airports:
            msg = "'airports' must contain at least one airport code"
            raise ValueError(msg)

        if len(set(self.airports)) != len(self.airports):
            msg = "'airports' contains duplicate airport codes"
            raise ValueError(msg)

        return self
