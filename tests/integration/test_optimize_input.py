# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for the optimize command input handling."""

import json

import pytest

from optifli.exit_codes import ExitCode

pytestmark = pytest.mark.integration


class TestOptimizeValidProfile:
    def test_minimal_profile(self, invoke, profiles_dir):
        result = invoke("optimize", "--profile", str(profiles_dir / "minimal.json"))
        assert result.exit_code == ExitCode.OK
        assert "Delhi" in result.output
        assert "Hanoi" in result.output

    def test_full_profile(self, invoke, profiles_dir):
        result = invoke("optimize", "--profile", str(profiles_dir / "full.json"))
        assert result.exit_code == ExitCode.OK

        assert "Delhi" in result.output
        assert "Hanoi" in result.output
        assert "Da Nang" in result.output
        assert "2d" in result.output
        assert "1.5d" in result.output
        assert "both" in result.output
        assert "fixed" in result.output
        assert "Legs" in result.output
        assert "1" in result.output  # single leg from profile

        # Direction "both" triggers the comparison table
        assert "Direction Comparison" in result.output
        comparison = result.output.split("Direction Comparison", maxsplit=1)[1]
        assert "Forward" in comparison
        assert "Reverse" in comparison


class TestOptimizeInvalidProfile:
    def test_missing_profile(self, invoke):
        result = invoke("optimize", "--profile", "/nonexistent/profile.json")
        assert result.exit_code == ExitCode.USAGE
        assert "Error:" in result.errors
        assert "Profile not found" in result.errors

    def test_invalid_json(self, invoke, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{broken", encoding="utf-8")
        result = invoke("optimize", "--profile", str(bad))
        assert result.exit_code == ExitCode.USAGE
        assert "Error:" in result.errors
        assert "Invalid JSON" in result.errors

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
        assert "Error:" in result.errors
        assert "validation failed" in result.errors
        assert "ZZZ" in result.errors


def _patch_prompts(monkeypatch, prompt_answers, confirm_answers):
    """Patch the wizard I/O boundary so the full pipeline runs without a TTY."""
    prompt_iter = iter(prompt_answers)
    confirm_iter = iter(confirm_answers)

    def fake_prompt_ask(prompt, **_kwargs):
        try:
            return next(prompt_iter)
        except StopIteration:
            msg = f"no more prompt answers ({prompt!r})"
            raise AssertionError(msg) from None

    def fake_confirm_ask(_prompt, **_kwargs):
        try:
            return next(confirm_iter)
        except StopIteration:
            msg = f"no more confirm answers ({_prompt!r})"
            raise AssertionError(msg) from None

    monkeypatch.setattr("optifli.wizard.Prompt.ask", fake_prompt_ask)
    monkeypatch.setattr("optifli.wizard.Confirm.ask", fake_confirm_ask)


class TestOptimizeWizard:
    def test_single_destination_renders_itinerary(self, invoke, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=["del", "han", "2d", "del", "forward", "fixed"],
            confirm_answers=[False, False],
        )

        result = invoke("optimize")

        assert result.exit_code == ExitCode.OK
        assert "DEL" in result.output
        assert "HAN" in result.output
        assert "2d" in result.output
        assert "forward" in result.output
        assert "fixed" in result.output

    def test_multi_destination_renders_all_cities(self, invoke, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "dad",
                "1.5d",
                "del",
                "forward",
                "fixed",
            ],
            confirm_answers=[True, False, False],
        )

        result = invoke("optimize")

        assert result.exit_code == ExitCode.OK
        assert "HAN" in result.output
        assert "DAD" in result.output
        assert "2d" in result.output
        assert "1.5d" in result.output

    def test_with_departure_windows_renders_leg_count(self, invoke, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "del",
                "2026-07-16T19:00:00+05:30",
                "2026-07-16T23:00:00+05:30",
                "2026-07-18T09:00:00+05:30",
                "2026-07-18T18:00:00+05:30",
                "forward",
                "fixed",
            ],
            confirm_answers=[False, True, False, False],
        )

        result = invoke("optimize")

        assert result.exit_code == ExitCode.OK
        assert "2" in result.output

    def test_reverse_direction_renders_reverse_map(self, invoke, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "dad",
                "1.5d",
                "del",
                "reverse",
                "fixed",
            ],
            confirm_answers=[True, False, False],
        )

        result = invoke("optimize")

        assert result.exit_code == ExitCode.OK
        assert "Reverse Duration Map" in result.output
        section = result.output.split("Reverse Duration Map", maxsplit=1)[1]
        assert "DAD" in section
        assert "HAN" in section
        assert section.find("DAD") < section.find("HAN")

    def test_both_direction_renders_comparison(self, invoke, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "dad",
                "1.5d",
                "del",
                "both",
                "fixed",
            ],
            confirm_answers=[True, False, False],
        )

        result = invoke("optimize")

        assert result.exit_code == ExitCode.OK
        assert "Direction Comparison" in result.output
        assert "Forward" in result.output
        assert "Reverse" in result.output
