# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""End-to-end tests invoking the CLI as a subprocess."""

import subprocess

import pytest

pytestmark = pytest.mark.e2e


def _run(*args: str, input_data: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["optifli", *args],
        input=input_data,
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


def test_wizard_happy_path_forward():
    inputs = (
        "DEL\n"  # Origin
        "HAN\n"  # Destination 1
        "3d\n"  # Stay at Destination 1
        "n\n"  # Add another destination? (No)
        "SGN\n"  # Return city
        "forward\n"  # Direction mode
        "n\n"  # Add departure windows? (No)
        "2026-07-16\n"  # Departure date
    )

    result = _run("optimize", input_data=inputs)
    assert result.returncode == 0
    assert "Itinerary Summary" in result.stdout
    assert "DEL (DEL)" in result.stdout
    assert "HAN (HAN)" in result.stdout
    assert "SGN (SGN)" in result.stdout
    assert "forward" in result.stdout


def test_wizard_happy_path_both():
    inputs = (
        "JFK\n"  # Origin
        "LHR\n"  # Destination 1
        "2d\n"  # Stay at Destination 1
        "y\n"  # Add another destination? (Yes)
        "CDG\n"  # Destination 2
        "3d\n"  # Stay at Destination 2
        "n\n"  # Add another destination? (No)
        "FRA\n"  # Return city
        "both\n"  # Direction mode
        "2026-08-01\n"  # Departure date
    )

    result = _run("optimize", input_data=inputs)
    assert result.returncode == 0
    assert "Itinerary Summary" in result.stdout
    assert "Direction Comparison" in result.stdout
    assert "JFK (JFK)" in result.stdout
    assert "both" in result.stdout
