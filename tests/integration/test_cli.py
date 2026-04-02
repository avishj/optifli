# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI integration tests."""

import pytest

from optifli import __version__
from optifli.exit_codes import ExitCode

pytestmark = pytest.mark.integration


def test_version(invoke):
    result = invoke("--version")
    assert result.exit_code == ExitCode.OK
    assert __version__ in result.output


def test_hello(invoke):
    result = invoke("hello", "World")
    assert result.exit_code == ExitCode.OK
    assert "World" in result.output


def test_no_args(invoke):
    result = invoke()
    assert result.exit_code == ExitCode.OK
    assert "Usage" in result.output
