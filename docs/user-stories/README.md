<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Optifli User Stories

## User-Facing Stories
1. US-001: Itinerary and constraints.
2. US-002: Reverse duration remap.
3. US-003: City airport groups.
4. US-008: Auto optimization mode.
5. US-009: Interactive leg lock mode.
6. US-011: CLI reporting.
7. US-013: Direction choice experience.
8. US-014: Bundle risk guidance.
9. US-015: Airport suggestion confirmation.

## Engine Behavior Stories
1. US-004: Route and date candidates.
2. US-005: Flight search policy.
3. US-006: Booking construction.
4. US-007: Scoring and swaps.

## Operational Stories
1. US-010: Rate-limit resilience.
2. US-012: Performance, rate-limit-aware execution and artifacts.

## Story Boundaries

### What Is a User Story
1. Describes user-visible behavior or outcomes.
2. States user value in plain language.
3. Defines acceptance criteria that product, design, and engineering can all verify.

### What Is an Engineering Spec
1. Defines implementation contracts and system internals.
2. Owns low-level details such as schema fields, retry bounds, signal handling, and logging payload structure.
3. Supports user stories but should not replace them.

### Split Rule
1. If a single document mixes user outcomes and low-level system contracts, keep user outcomes in a user story and move system contracts to an engineering spec.

Each story is defined as a modular implementation unit with clear interfaces, dependencies, and acceptance criteria.

## Templates
1. docs/user-stories/TEMPLATE-user-story.md
2. docs/engineering-specs/TEMPLATE-engineering-spec.md
