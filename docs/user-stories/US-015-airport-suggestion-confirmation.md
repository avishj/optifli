<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-015: Airport Suggestion Confirmation

## Type
User-facing

## Story
As a traveler, I want nearby airport suggestions for my selected city so I can broaden search coverage without losing control of my chosen airport set.

## Business Value
Users discover better options while preserving explicit control over included airports.

## Acceptance Criteria
1. Nearby airport suggestions are presented as optional recommendations ranked by distance.
2. Suggested airports are never auto-added.
3. Users must explicitly confirm each suggested airport before it becomes active in the city group.
4. Users can accept, reject, or ignore suggestions without breaking the current run.

## Dependencies
1. docs/user-stories/US-003-city-airport-groups.md
