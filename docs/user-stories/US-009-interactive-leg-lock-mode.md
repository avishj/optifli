# US-009: Interactive Leg-by-Leg Lock Mode

## Story
As a hands-on traveler, I want to lock one leg at a time so I can guide optimization while preserving downstream feasibility.

## Business Value
Interactive control improves confidence when users care about specific flights.

## Acceptance Criteria
1. The interactive mode shows candidate options for the current leg and accepts a lock selection.
2. After a lock, the engine recomputes remaining legs using locked constraints, verified in recomputation tests.
3. Locked legs remain immutable unless user explicitly unlocks.
4. Mode tracks and displays current lock state, the ordered list of pending leg indices, and the count of remaining decisions (one decision step equals one leg lock or unlock action).
5. A full interactive run can be resumed from persisted state after interruption.

## Dependencies
1. Scoring and per-leg alternative generation.
2. Session state persistence.
