# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for search-related settings fields."""

import pytest
from pydantic import ValidationError

from optifli.config import Settings
from optifli.search import FallbackBehavior, StopMode

pytestmark = pytest.mark.unit


def _settings(**overrides: str) -> Settings:
    """Build a ``Settings`` with env-file disabled and env overrides applied."""
    return Settings(_env_file=None, **overrides)


# --- defaults ----------------------------------------------------------------


class TestSearchSettingsDefaults:
    def test_max_retries_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_MAX_RETRIES", raising=False)
        assert _settings().max_retries == 5

    def test_max_expansion_rounds_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_MAX_EXPANSION_ROUNDS", raising=False)
        assert _settings().max_expansion_rounds == 2

    def test_expand_on_fallback_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_EXPAND_ON_FALLBACK", raising=False)
        assert _settings().expand_on_fallback is False

    def test_max_requests_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_MAX_REQUESTS", raising=False)
        assert _settings().max_requests == 500

    def test_default_stop_mode_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_DEFAULT_STOP_MODE", raising=False)
        assert _settings().default_stop_mode is StopMode.NON_STOP

    def test_fallback_behavior_default(self, monkeypatch):
        monkeypatch.delenv("OPTIFLI_FALLBACK_BEHAVIOR", raising=False)
        assert _settings().fallback_behavior is FallbackBehavior.ONE_STOP


# --- env overrides -----------------------------------------------------------


class TestSearchSettingsEnvOverrides:
    def test_max_retries_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_RETRIES", "8")
        assert _settings().max_retries == 8

    def test_max_expansion_rounds_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_EXPANSION_ROUNDS", "5")
        assert _settings().max_expansion_rounds == 5

    def test_expand_on_fallback_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_EXPAND_ON_FALLBACK", "true")
        assert _settings().expand_on_fallback is True

    def test_max_requests_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_REQUESTS", "1000")
        assert _settings().max_requests == 1000

    def test_default_stop_mode_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_DEFAULT_STOP_MODE", "one-stop")
        assert _settings().default_stop_mode is StopMode.ONE_STOP

    def test_fallback_behavior_from_env(self, monkeypatch):
        monkeypatch.setenv("OPTIFLI_FALLBACK_BEHAVIOR", "disabled")
        assert _settings().fallback_behavior is FallbackBehavior.DISABLED


# --- boundary validation -----------------------------------------------------


class TestSearchSettingsBounds:
    @pytest.mark.parametrize("value", ["-1", "11"])
    def test_max_retries_out_of_range(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_RETRIES", value)
        with pytest.raises(ValidationError):
            _settings()

    @pytest.mark.parametrize("value", ["-1", "11"])
    def test_max_expansion_rounds_out_of_range(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_EXPANSION_ROUNDS", value)
        with pytest.raises(ValidationError):
            _settings()

    @pytest.mark.parametrize("value", ["49", "5001"])
    def test_max_requests_out_of_range(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_REQUESTS", value)
        with pytest.raises(ValidationError):
            _settings()

    @pytest.mark.parametrize("value", ["0", "10"])
    def test_max_retries_boundary_accepted(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_RETRIES", value)
        assert _settings().max_retries == int(value)

    @pytest.mark.parametrize("value", ["0", "10"])
    def test_max_expansion_rounds_boundary_accepted(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_EXPANSION_ROUNDS", value)
        assert _settings().max_expansion_rounds == int(value)

    @pytest.mark.parametrize("value", ["50", "5000"])
    def test_max_requests_boundary_accepted(self, value, monkeypatch):
        monkeypatch.setenv("OPTIFLI_MAX_REQUESTS", value)
        assert _settings().max_requests == int(value)
