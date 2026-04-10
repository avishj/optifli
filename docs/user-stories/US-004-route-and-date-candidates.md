<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-004: Generate Route and Date Candidates

## Type

Engine behavior

## Story

As an optimizer, I want to generate valid route and schedule candidates so that search can compare realistic options.

## Business Value

Candidate quality controls both runtime and recommendation quality.

## Acceptance Criteria

1. Route generation supports fixed-order and reorder-enabled modes.
2. Reorder-enabled mode keeps origin and final return city fixed while permuting intermediate destinations.
3. Date propagation generates earliest/latest departure windows per leg from stay durations (including fractional durations) and user constraints in consistency tests.
4. Candidate window generation preserves elapsed-time offsets and does not snap to fixed noon/midnight boundaries.
5. The generator enforces configurable permutation caps and logs when pruning occurs.
6. Benchmark itineraries complete candidate generation without invalid leg chronology.
7. Cross-time-zone candidate propagation is validated with UTC as the canonical internal timeline, while departure and arrival display times are rendered in their respective airport local timezones with no timestamp drift across conversions.

## Dependencies

1. Input and duration model.
2. Direction and remap logic.
