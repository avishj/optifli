# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for the optimize command input handling."""

import json
from pathlib import Path

import pytest

from optifli.exit_codes import ExitCode

pytestmark = pytest.mark.integration

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "profiles"


class TestOptimizeValidProfile:
    def test_minimal_profile(self, invoke):
        result = invoke("optimize", "--profile", str(_FIXTURES / "minimal.json"))
        assert result.exit_code == ExitCode.OK
        assert "Delhi" in result.output
        assert "Hanoi" in result.output

    def test_full_profile(self, invoke):
        result = invoke("optimize", "--profile", str(_FIXTURES / "full.json"))
        assert result.exit_code == ExitCode.OK
        assert "Da Nang" in result.output
        assert "both" in result.output


class TestOptimizeInvalidProfile:
    def test_missing_profile(self, invoke):
        result = invoke("optimize", "--profile", "/nonexistent/profile.json")
        assert result.exit_code == ExitCode.USAGE

    def test_invalid_json(self, invoke, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{broken", encoding="utf-8")
        result = invoke("optimize", "--profile", str(bad))
        assert result.exit_code == ExitCode.USAGE

    def test_validation_errors(self, invoke, tmp_path):
        data = {
            "origin": {"name": "X", "include": ["ZZZ"]},
            "destinations": [
                {"city": {"name": "Y", "include": ["HAN"]}, "stay": "2d"},
            ],
            "return_city": {"name": "Y", "include": ["HAN"]},
        }
        p = tmp_path / "bad_airport.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = invoke("optimize", "--profile", str(p))
        assert result.exit_code == ExitCode.USAGE


class TestOptimizeNoProfile:
    def test_no_profile_flag(self, invoke):
        result = invoke("optimize")
        assert result.exit_code == ExitCode.USAGE
