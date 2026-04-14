# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""End-to-end tests invoking the CLI as a subprocess."""

import subprocess

import pytest

pytestmark = pytest.mark.e2e


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["optifli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_version_flag():
    result = _run("--version")
    assert result.returncode == 0
    assert result.stdout.strip()


def test_optimize_profile(profiles_dir):
    result = _run("optimize", "--profile", str(profiles_dir / "minimal.json"))
    assert result.returncode == 0
    assert "Delhi" in result.stdout
    assert "Hanoi" in result.stdout


def test_optimize_full_profile(profiles_dir):
    result = _run("optimize", "--profile", str(profiles_dir / "full.json"))
    assert result.returncode == 0
    assert "Delhi" in result.stdout
    assert "Hanoi" in result.stdout
    assert "Da Nang" in result.stdout
    assert "forward" in result.stdout


def test_no_args_shows_help():
    result = _run()
    assert result.returncode == 0
    assert "Usage" in result.stdout or "optifli" in result.stdout


def test_optimize_missing_profile():
    result = _run("optimize", "--profile", "nonexistent.json")
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_verbose_flag(profiles_dir):
    result = _run(
        "--verbose", "optimize", "--profile", str(profiles_dir / "minimal.json")
    )
    assert result.returncode == 0
    assert "Delhi" in result.stdout


def test_optimize_reverse_profile(profiles_dir):
    result = _run("optimize", "--profile", str(profiles_dir / "reverse.json"))
    assert result.returncode == 0
    assert "Reverse" in result.stdout
    assert "Da Nang" in result.stdout
    assert "Hanoi" in result.stdout


def test_optimize_invalid_data_profile(profiles_dir):
    result = _run("optimize", "--profile", str(profiles_dir / "invalid_data.json"))
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_optimize_malformed_profile(profiles_dir):
    result = _run("optimize", "--profile", str(profiles_dir / "malformed.json"))
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_invalid_env_config():
    result = subprocess.run(
        ["optifli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "OPTIFLI_LOG_FORMAT": "garbage"},
    )
    assert result.returncode != 0
    assert "configuration" in result.stderr.lower()


def test_invalid_command():
    result = _run("nonexistent")
    assert result.returncode != 0
