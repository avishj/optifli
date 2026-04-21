# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Search-domain models and execution helpers."""

from optifli.search.models import (
    ApiFailureClassification,
    FallbackBehavior,
    SearchOutcome,
    StopMode,
)

__all__: list[str] = [
    "ApiFailureClassification",
    "FallbackBehavior",
    "SearchOutcome",
    "StopMode",
]
