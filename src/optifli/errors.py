# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consistent, actionable error formatting for CLI display."""

from dataclasses import dataclass

from pydantic import ValidationError
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text


@dataclass(frozen=True)
class InputError:
    """A single user-facing input validation error.

    Attributes:
        field: The field or path that failed validation.
        reason: What went wrong.
        hint: Actionable suggestion for fixing it.
    """

    field: str
    reason: str
    hint: str = ""


class FormattedErrors:
    """Rich-renderable collection of input errors."""

    def __init__(self, errors: list[InputError]) -> None:
        """Wrap a list of input errors for Rich rendering."""
        self.errors = errors

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        """Yield Rich renderables for each error."""
        for error in self.errors:
            line = Text()
            line.append(f"  {error.field}", style="bold red")
            line.append(f": {error.reason}")
            if error.hint:
                line.append(f" ({error.hint})", style="dim")
            yield line


def format_errors(errors: list[InputError]) -> str:
    """Render input errors to a plain string.

    Args:
        errors: Validation errors to format.

    Returns:
        Multi-line string with one error per line.
    """
    console = Console(no_color=True, width=120)
    with console.capture() as capture:
        console.print(FormattedErrors(errors))
    return capture.get().rstrip()


def from_pydantic(exc: ValidationError) -> list[InputError]:
    """Convert a Pydantic ``ValidationError`` into ``InputError`` items.

    Args:
        exc: The Pydantic validation error.

    Returns:
        List of user-friendly input errors.
    """
    results: list[InputError] = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err["loc"]) or "input"
        reason = err["msg"]
        results.append(InputError(field=loc, reason=reason))
    return results
