<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-013: Direction Choice Experience

## Type

User-facing

## Story

As a traveler, I want to compare forward and reverse trip directions side by side so I can choose the direction that best fits price and convenience.

## Business Value

Direction choice is a major lever for total trip quality and cost.

## Acceptance Criteria

1. Users can request forward-only, reverse-only, or both directions in one run.
2. When both directions are requested, output groups recommendations by direction and clearly labels each group.
3. Each direction group shows comparable summary fields (price, duration, stops, and score) so users can make a direct choice.
4. Once users pick a preferred direction, follow-up optimization respects that choice.

## Dependencies

1. docs/user-stories/US-002-reverse-duration-remap.md
2. docs/user-stories/US-011-cli-reporting.md
