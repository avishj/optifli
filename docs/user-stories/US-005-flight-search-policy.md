<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-005: Execute Flight Search Policy

## Type

Engine behavior

## Story

As a traveler, I want search to honor my time windows and stop preferences so the options are both cheap and practical.

## Business Value

Correct policy handling prevents invalid recommendations and missed opportunities.

## Acceptance Criteria

1. Each leg search scans the full departure window provided by the user, including cross-day windows.
2. Optional arrival cutoff constraints are applied only when configured.
3. Search prefers non-stop options first and falls back to one-stop options when non-stop options are unavailable and fallback is enabled.
4. If no valid options are found after configured search steps, the run returns a clear no-results classification.
5. Output clearly indicates whether fallback and window expansion were used.

## Dependencies

1. FLI adapter and leg query builder.
2. Policy configuration loader.

## Linked Engineering Specs

1. docs/engineering-specs/ES-001-search-policy-contract.md
