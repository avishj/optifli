# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""IATA airport code validation."""

import re
from typing import Annotated

from fli.models import Airport
from pydantic import BeforeValidator

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
