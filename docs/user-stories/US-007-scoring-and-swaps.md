# US-007: Score, Rank, and Surface Leg Swaps

## Story
As a decision-maker, I want transparent ranking and swap suggestions so I can trade off price, duration, and convenience intelligently.

## Business Value
Explainable ranking increases trust and booking confidence.

## Acceptance Criteria
1. Default ranking uses weighted scoring across total price, total duration, number of stops, and departure convenience.
2. Preset scoring profiles are available: Cheapest, Balanced (default), Fastest, and Fewer Stops.
3. Every returned plan includes component scores and the final weighted score.
4. The engine generates leg-level swap opportunities that improve at least one ranking dimension without violating hard constraints.
5. Ranking output is deterministic for identical input and cached API responses, verified by determinism tests.
6. Top-N limits for global plans and leg alternatives are configurable via CLI and profile.

## Dependencies
1. Candidate plan objects from US-006.
2. Constraint validator.
