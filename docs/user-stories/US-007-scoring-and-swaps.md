# US-007: Score, Rank, and Surface Leg Swaps

## Type
Engine behavior

## Story
As a decision-maker, I want transparent ranking and swap suggestions so I can trade off price, duration, and convenience intelligently.

## Business Value
Explainable ranking increases trust and booking confidence.

## Acceptance Criteria
1. Default ranking uses weighted scoring across total price, total duration, number of stops, and departure convenience.
2. Preset scoring profiles are available with Balanced as default.
3. Every returned plan includes component scores and the final weighted score.
4. The engine generates leg-level swap opportunities that are strictly better in at least one ranking dimension and non-worse in all other ranking dimensions, without violating hard constraints; each swap includes impact summary fields (fare delta, duration delta, stop delta, and bundle-compatibility delta), and explicitly warns when reduced bundle compatibility may increase total trip price.
5. Ranking output is deterministic for identical input and cached API responses, verified by determinism tests.
6. Top-N limits for global plans and leg alternatives are configurable via CLI and profile.

## Dependencies
1. Candidate plan objects from US-006.
2. Constraint validator.
3. Artifact schema versioning and replay compatibility rules are defined in US-012.

## Linked Engineering Specs
1. docs/engineering-specs/ES-002-scoring-contract.md
2. docs/TBD.md

