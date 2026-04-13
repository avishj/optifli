# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the interactive itinerary wizard."""

from datetime import date

import pytest

from optifli.models.itinerary import DirectionMode, RouteMode
from optifli.wizard import collect_itinerary

pytestmark = pytest.mark.unit


def _patch_prompts(monkeypatch, prompt_answers, confirm_answers):
    prompt_iter = iter(prompt_answers)
    confirm_iter = iter(confirm_answers)
    prompt_calls = []

    def fake_prompt_ask(prompt, **_kwargs):
        prompt_calls.append(prompt)
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
    return prompt_calls


class TestCollectItineraryValid:
    def test_collects_single_destination_without_windows(self, monkeypatch):
        prompt_calls = _patch_prompts(
            monkeypatch,
            prompt_answers=["del", "han", "2d", "del", "both", "2026-07-16"],
            confirm_answers=[False, False],
        )

        itinerary = collect_itinerary()

        assert itinerary.origin.name == "DEL"
        assert itinerary.origin.airports == ["DEL"]
        assert len(itinerary.destinations) == 1
        assert itinerary.destinations[0].city.airports == ["HAN"]
        assert itinerary.destinations[0].stay.total_days == 2.0
        assert itinerary.return_city.airports == ["DEL"]
        assert itinerary.legs == []
        assert itinerary.direction is DirectionMode.BOTH
        assert itinerary.route_mode is RouteMode.FIXED
        assert itinerary.departure_date == date(2026, 7, 16)
        assert prompt_calls == [
            "Origin airport code",
            "Destination 1 airport code",
            "Destination 1 stay duration",
            "Return airport code",
            "Direction mode",
            "Trip start date (YYYY-MM-DD)",
        ]

    def test_collects_departure_windows(self, monkeypatch):
        prompt_calls = _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "del",
                "2026-07-16T19:00:00+05:30",
                "2026-07-16T23:00:00+05:30",
                "2026-07-17T08:00:00+05:30",
                "2026-07-18T09:00:00+05:30",
                "2026-07-18T18:00:00+05:30",
                "forward",
            ],
            confirm_answers=[False, True, True, False],
        )

        itinerary = collect_itinerary()

        assert len(itinerary.legs) == 2
        assert itinerary.legs[0].origin.airports == ["DEL"]
        assert itinerary.legs[0].destination.airports == ["HAN"]
        assert itinerary.legs[0].arrival_cutoff is not None
        assert (
            itinerary.legs[0]
            .arrival_cutoff.deadline.isoformat()
            .startswith("2026-07-17T08:00:00+05:30")
        )
        assert itinerary.legs[1].origin.airports == ["HAN"]
        assert itinerary.legs[1].destination.airports == ["DEL"]
        assert itinerary.legs[1].arrival_cutoff is None
        assert itinerary.departure_date is None
        assert prompt_calls.count("Leg 1 departure start (DEL -> HAN)") == 1
        assert prompt_calls.count("Leg 2 departure start (HAN -> DEL)") == 1
        assert "Trip start date (YYYY-MM-DD)" not in prompt_calls


class TestWizardRouteMode:
    def test_wizard_always_uses_fixed(self, monkeypatch):
        _patch_prompts(
            monkeypatch,
            prompt_answers=["del", "han", "2d", "del", "forward", "2026-07-16"],
            confirm_answers=[False, False],
        )

        itinerary = collect_itinerary()

        assert itinerary.route_mode is RouteMode.FIXED


class TestCollectItineraryAbort:
    def test_ctrl_c_exits_cleanly(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "optifli.wizard.Prompt.ask",
            lambda *a, **kw: (_ for _ in ()).throw(KeyboardInterrupt),
        )
        with pytest.raises(SystemExit) as exc:
            collect_itinerary()
        assert exc.value.code == 130
        assert "Aborted" in capsys.readouterr().err

    def test_eof_exits_cleanly(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "optifli.wizard.Prompt.ask",
            lambda *a, **kw: (_ for _ in ()).throw(EOFError),
        )
        with pytest.raises(SystemExit) as exc:
            collect_itinerary()
        assert exc.value.code == 130
        assert "Aborted" in capsys.readouterr().err


class TestCollectItineraryValidation:
    def test_reprompts_after_invalid_input(self, monkeypatch, capsys):
        prompt_calls = _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "de",
                "del",
                "han",
                "1d12h",
                "2d",
                "12a",
                "del",
                "forward",
                "2026-07-16",
            ],
            confirm_answers=[False, False],
        )

        itinerary = collect_itinerary()
        captured = capsys.readouterr()

        assert itinerary.origin.airports == ["DEL"]
        assert itinerary.return_city.airports == ["DEL"]
        assert itinerary.direction is DirectionMode.FORWARD
        assert itinerary.route_mode is RouteMode.FIXED
        assert prompt_calls.count("Origin airport code") == 2
        assert prompt_calls.count("Destination 1 stay duration") == 2
        assert prompt_calls.count("Return airport code") == 2
        assert "not a valid IATA code" in captured.err
        assert "Invalid duration format" in captured.err

    def test_reprompts_after_invalid_datetime(self, monkeypatch, capsys):
        prompt_calls = _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "del",
                "2026-07-16T19:00:00",
                "2026-07-16T23:00:00",
                "2026-07-16T19:00:00+05:30",
                "2026-07-16T23:00:00+05:30",
                "2026-07-18T09:00:00+05:30",
                "2026-07-18T18:00:00+05:30",
                "forward",
            ],
            confirm_answers=[False, True, False, False],
        )

        itinerary = collect_itinerary()
        captured = capsys.readouterr()

        assert len(itinerary.legs) == 2
        assert prompt_calls.count("Leg 1 departure start (DEL -> HAN)") == 2
        assert prompt_calls.count("Leg 1 departure end (DEL -> HAN)") == 2
        assert "timezone-aware" in captured.err
        assert "Use timezone-aware ISO datetimes" in captured.err

    def test_reprompts_after_invalid_date(self, monkeypatch, capsys):
        prompt_calls = _patch_prompts(
            monkeypatch,
            prompt_answers=[
                "del",
                "han",
                "2d",
                "del",
                "forward",
                "not-a-date",
                "2026-07-16",
            ],
            confirm_answers=[False, False],
        )

        itinerary = collect_itinerary()
        captured = capsys.readouterr()

        assert itinerary.departure_date == date(2026, 7, 16)
        assert prompt_calls.count("Trip start date (YYYY-MM-DD)") == 2
        assert "Invalid date format" in captured.err
