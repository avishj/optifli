# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for reverse-aware CLI output."""

import json

import pytest

from optifli.exit_codes import ExitCode

pytestmark = pytest.mark.integration


def _write_profile(path, direction):
    data = {
        "origin": {"name": "Delhi", "include": ["DEL"]},
        "destinations": [
            {"city": {"name": "Hanoi", "include": ["HAN"]}, "stay": "2d"},
            {"city": {"name": "Da Nang", "include": ["DAD"]}, "stay": "1.5d"},
        ],
        "return_city": {"name": "Delhi", "include": ["DEL"]},
        "direction": direction,
        "route_mode": "fixed",
    }
    path.write_text(json.dumps(data), encoding="utf-8")


class TestReverseCliDisplay:
    def test_reverse_shows_reversed_duration_map(self, invoke, tmp_path):
        profile = tmp_path / "reverse.json"
        _write_profile(profile, "reverse")

        result = invoke("optimize", "--profile", str(profile))

        assert result.exit_code == ExitCode.OK
        assert "Reverse Duration Map" in result.output
        section = result.output.split("Reverse Duration Map", maxsplit=1)[1]
        assert section.find("Da Nang (DAD) - 1.5d") < section.find("Hanoi (HAN) - 2d")

    def test_both_shows_direction_comparison(self, invoke, tmp_path):
        profile = tmp_path / "both.json"
        _write_profile(profile, "both")

        result = invoke("optimize", "--profile", str(profile))

        assert result.exit_code == ExitCode.OK
        assert "Direction Comparison" in result.output
        section = result.output.split("Direction Comparison", maxsplit=1)[1]
        assert "Forward" in section
        assert "Reverse" in section
        assert "Hanoi (HAN) - 2d" in section
        assert "Da Nang (DAD) - 1.5d" in section
