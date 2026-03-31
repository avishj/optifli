# US-006: Build Ticket Construction Candidates

## Story
As a budget traveler, I want Optifli to compare one-way, multi-city, and round-trip constructions so I can book the cheapest feasible combination.

## Business Value
Different fare constructions often produce materially different totals.

## Acceptance Criteria
1. The combination engine generates all-one-way candidate plans for every valid route candidate.
2. The combination engine generates valid multi-city booking candidates when leg continuity rules are satisfied.
3. The combination engine builds round-trip candidates only when outbound and inbound legs are opposite-direction travel between the same city groups and satisfy traveler constraints.
4. Round-trip candidates are included only when FLI returns a valid round-trip fare quote for the paired request.
5. Duplicate plans are removed in deduplication tests using canonical plan hashes.
6. Each candidate plan stores total fare, per-leg fare allocation, and construction type for downstream ranking.

## Dependencies
1. Route/date candidates.
2. Leg-level flight result sets.
