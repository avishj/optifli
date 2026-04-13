# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Airport timezone lookup."""

from functools import cache

import airportsdata


class TimezoneLookupError(RuntimeError):
    """Raised when an airport timezone cannot be resolved."""


@cache
def _airport_timezones() -> dict[str, str]:
    return {
        code: airport["tz"]
        for code, airport in airportsdata.load("IATA").items()
        if airport.get("tz")
    }


def lookup_airport_timezone(airport_code: str) -> str:
    """Return the IANA timezone name for an IATA airport code."""
    code = airport_code.strip().upper()
    try:
        return _airport_timezones()[code]
    except KeyError:
        msg = f"Could not resolve timezone for airport code '{code}'"
        raise TimezoneLookupError(msg) from None
