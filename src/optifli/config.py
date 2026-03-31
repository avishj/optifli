# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Application configuration."""

import sys
from enum import StrEnum

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from optifli.exit_codes import ExitCode


class LogFormat(StrEnum):
    """Supported log output formats."""

    PRETTY = "pretty"
    JSON = "json"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="OPTIFLI_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    verbose: bool = False
    log_format: LogFormat = LogFormat.PRETTY


try:
    settings = Settings()
except ValidationError as exc:
    body = Text()
    for error in exc.errors():
        loc = " → ".join(str(part) for part in error["loc"])
        body.append(f"  • {loc}", style="bold red")
        body.append(f"  {error['msg']}\n", style="dim")
    Console(stderr=True).print(
        Panel(
            body,
            title="⚙ Configuration Error",
            subtitle="check your .env file or OPTIFLI_* variables",
            border_style="red",
            expand=False,
        ),
    )
    sys.exit(ExitCode.CONFIG)
