# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""JSON profile loading and validation."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from optifli.errors import InputError, format_errors, from_pydantic
from optifli.models.itinerary import Itinerary


class ProfileError(Exception):
    """Raised when a profile cannot be loaded or validated."""

    def __init__(self, message: str, errors: list[InputError] | None = None) -> None:
        """Initialise with a message and optional structured errors.

        Args:
            message: Human-readable summary.
            errors: Optional list of structured input errors.
        """
        super().__init__(message)
        self.errors = errors or []


def _remap_city(data: dict[str, Any]) -> dict[str, Any]:
    """Remap ``include`` key to ``airports`` for CityGroup compatibility."""
    if "include" in data and "airports" not in data:
        data = {**data, "airports": data.pop("include")}
    return data


def _remap_profile(data: dict[str, Any]) -> dict[str, Any]:
    """Remap profile JSON keys to match model field names."""
    if "origin" in data and isinstance(data["origin"], dict):
        data["origin"] = _remap_city(data["origin"])

    if "return_city" in data and isinstance(data["return_city"], dict):
        data["return_city"] = _remap_city(data["return_city"])

    for dest in data.get("destinations", []):
        if isinstance(dest, dict) and isinstance(dest.get("city"), dict):
            dest["city"] = _remap_city(dest["city"])

    for leg in data.get("legs", []):
        if not isinstance(leg, dict):
            continue
        if isinstance(leg.get("origin"), dict):
            leg["origin"] = _remap_city(leg["origin"])
        if isinstance(leg.get("destination"), dict):
            leg["destination"] = _remap_city(leg["destination"])

    return data


def load_profile(path: Path) -> Itinerary:
    """Load a JSON profile file into a validated ``Itinerary``.

    Args:
        path: Path to the JSON profile file.

    Returns:
        A validated Itinerary model.

    Raises:
        ProfileError: If the file is missing, unparsable, or invalid.
    """
    if not path.exists():
        msg = f"Profile not found: {path}"
        raise ProfileError(msg)

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Cannot read profile: {exc}"
        raise ProfileError(msg) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in profile: {exc.msg} (line {exc.lineno})"
        raise ProfileError(msg) from exc

    if not isinstance(data, dict):
        msg = "Profile must be a JSON object, not a list or scalar"
        raise ProfileError(msg)

    data = _remap_profile(data)

    try:
        return Itinerary.model_validate(data)
    except ValidationError as exc:
        input_errors = from_pydantic(exc)
        msg = f"Profile validation failed:\n{format_errors(input_errors)}"
        raise ProfileError(msg, errors=input_errors) from exc
