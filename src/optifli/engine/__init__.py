# SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Route candidate generation and optimization engine."""

from optifli.engine.candidates import (
    RouteCandidate,
    generate_candidates,
    validate_leg_consistency,
)
from optifli.engine.direction import expand_directions

__all__: list[str] = [
    "RouteCandidate",
    "expand_directions",
    "generate_candidates",
    "validate_leg_consistency",
]
