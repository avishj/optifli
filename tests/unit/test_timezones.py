# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for airport timezone lookup."""

import pytest

from optifli.timezones import TimezoneLookupError, lookup_airport_timezone

pytestmark = pytest.mark.unit


class TestLookupAirportTimezone:
    def test_resolves_delhi(self):
        assert lookup_airport_timezone("DEL") == "Asia/Kolkata"

    def test_resolves_new_york(self):
        assert lookup_airport_timezone("JFK") == "America/New_York"

    def test_rejects_unknown_airport(self):
        with pytest.raises(TimezoneLookupError, match="ZZZ"):
            lookup_airport_timezone("ZZZ")
