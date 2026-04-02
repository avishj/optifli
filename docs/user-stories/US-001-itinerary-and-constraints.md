<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-001: Capture Itinerary and Constraints

## Type
User-facing

## Story
As a vacation planner, I want to provide my city sequence, stay durations, and date/time constraints so that Optifli can generate valid optimization candidates.

## Business Value
Without structured input and constraint validation, optimization results are unreliable.

## Acceptance Criteria
1. The CLI accepts itinerary inputs with 1 origin city, 1-10 destination cities, and 1 final return city via flags or profile file.
2. The CLI accepts per-destination stay durations in these formats: `<number>d` (fractional days allowed, for example `2d`, `1.5d`, `0.5d`) and `<number>h` (fractional hours allowed, for example `12h`, `30h`, `2.5h`); compound formats like `1d12h` are rejected in this version.
3. The CLI accepts per-leg departure windows as start/end datetime, including cross-day windows.
4. Stay durations are applied as elapsed time from arrival, with no hard noon or midnight boundary assumptions (for example: 0.5d means 12 hours from the arrival timestamp).
5. Invalid inputs return actionable errors (field, reason, fix hint), and this behavior is covered by validation tests.
6. Schema validation unit tests provide strong coverage for input parsing and validation modules.
7. Date/time parsing requires timezone context using either UTC offset format (`+/-HH:MM`, for example `+05:30`) or IANA timezone names (for example `Asia/Kolkata`), with clear validation errors for missing or invalid timezone values.

## Dependencies
1. CLI argument parser and config loader.
2. Domain model for itinerary, leg windows, and durations.
