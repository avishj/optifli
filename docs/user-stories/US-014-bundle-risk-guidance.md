<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-014: Bundle Risk Guidance

## Type
User-facing

## Story
As a traveler, I want clear warnings when a leg swap weakens bundle compatibility so I understand that total trip price may increase.

## Business Value
Users avoid misleading leg-level savings that can increase end-to-end booking cost.

## Acceptance Criteria
1. When a swap reduces bundle compatibility, output clearly flags the risk.
2. Risk messaging explains that a lower leg fare can still increase overall trip price.
3. Users can still choose the swap, but guidance is shown before confirmation.
4. Reports preserve both swap-level deltas and bundle-risk warning state.

## Dependencies
1. docs/user-stories/US-007-scoring-and-swaps.md
2. docs/user-stories/US-011-cli-reporting.md
