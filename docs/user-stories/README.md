# Optifli User Stories 

1. US-001: Itinerary and constraints.
2. US-002: Reverse duration remap.
3. US-003: City airport groups.
4. US-004: Route and date candidates.
5. US-005: Flight search policy.
6. US-006: Booking construction.
7. US-007: Scoring and swaps.
8. US-008: Auto optimization mode.
9. US-009: Interactive leg lock mode.
10. US-010: Rate-limit resilience.
11. US-011: CLI reporting.
12. US-012: Performance, rate-limit-aware execution and artifacts.

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
