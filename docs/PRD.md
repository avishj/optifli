<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# PRD: Optifli Flight Optimization Engine

## What We Are Building

Optifli is a CLI-first optimization engine for multi-city trips. It uses the FLI Python library to query Google Flights data, then compares different ways to route and ticket the same vacation.

The engine should help a traveler answer questions like:

1. Should I do this route forward or reverse?
2. Should I keep the order or reorder cities?
3. Should I book as all one-way tickets, a multi-city ticket, round-trip combos, or a mix?
4. Which leg swaps improve price or convenience without breaking my trip constraints?

## Why This Matters

For a trip with several cities, there are too many combinations to compare manually. People usually miss good options because they only check one route order or one booking style.

Optifli should do that heavy lifting and return clear, practical options.

## Quick Example

This is the kind of itinerary Optifli is designed for:

1. Route (IATA): DEL -> HAN -> DAD -> PQC -> SIN -> DEL.
2. Route (city names): Delhi -> Hanoi -> Da Nang -> Phu Quoc -> Singapore -> Delhi.
3. Stay durations (including half-day): HAN=2d, DAD=1.5d, PQC=3d, SIN=0.5d.
4. Half-day interpretation: SIN=0.5d means the next leg can depart no earlier than 12 hours after arrival in SIN.
5. Example departure window for one leg: DEL -> HAN can depart between 2026-07-16 19:00 Indian standard time and 2026-07-17 11:00 Indian standard time.
6. Reverse mode means the same city durations still apply to the same cities, even though leg order flips.
7. The engine compares one-way, multi-city, round-trip, and mixed constructions.

## Key Terms

1. Itinerary: ordered list of cities including start and return city.
2. Leg: one flight segment between two cities in a candidate route.
3. City group: the set of allowed airports for a city.
4. Base window: the exact departure window the user requested for a leg.
5. Expanded window: additional search range around the base window, used only when enabled and needed.
6. Fallback: backup search path used only if the primary search path returns no results.
7. Construction: how tickets are combined (one-way, multi-city, round-trip, or mixed).
8. Global plan: one complete end-to-end candidate for the whole trip.
9. Leg alternative: a replaceable option for a specific leg within a global plan.
10. Leg swap: replacing one leg alternative with another within a global plan while preserving hard constraints.
11. Coverage gap: part of the search space not fully explored due to limits (for example rate limits or request budget).
12. Round-trip compatibility rule: the minimum conditions needed to treat two opposite-direction legs as one round-trip candidate.

## Goals

1. Generate valid optimization results for itineraries with an origin, up to 10 destination cities, and a final return city.
2. Support both full automatic optimization and interactive leg-by-leg locking.
3. Respect real trip constraints: stay durations, date/time windows, airport preferences, and stop preferences.
4. Return explainable rankings with both full-trip recommendations and per-leg alternatives.
5. Handle API ambiguity gracefully and label outcomes clearly (no silent failures).

## Scope

### In Scope

1. FLI library integration only.
2. One-way, multi-city, and round-trip fare construction analysis.
3. Forward, reverse, and both-direction comparisons.
4. Fixed-order and reorder-enabled route exploration.
5. User-defined city airport groups with include/exclude controls (no curated airport list).
6. Stop policy: prefer non-stop, optionally fallback to one-stop.
7. Departure windows with optional arrival cutoff.
8. Optional window expansion in 1-hour rounds when base window has no results (round 2 reaches +/-2 hours).
9. CLI-first output with machine-readable run artifacts.

### Out of Scope

1. Hotel, visa, baggage, insurance, or non-flight planning.
2. Booking and payment execution.
3. MCP server integration.
4. Default support for two-stop fallback.

## Product Requirements

### 1) Inputs and Constraints

1. The CLI accepts an itinerary with origin, 1-10 destination cities, and final return city.
2. The CLI accepts stay durations per destination.
3. Stay duration supports fractional values, including half-day and smaller units.
4. Stay duration can be entered as fractional days or hours.
5. The system must treat stay duration as elapsed time from arrival, not as fixed calendar buckets (see Section 2 for timezone and daylight-saving handling).
6. There must be no hard noon/midnight boundary assumption.
7. The CLI accepts per-leg departure windows with start and end datetime.
8. Cross-day windows are valid and searched fully.
9. Optional per-leg arrival cutoff is supported.
10. Invalid input returns actionable messages with field, reason, and fix hint.
11. All date/time inputs must include timezone context (explicit offset or named timezone).
12. If timezone context is missing, the CLI returns a clear validation error.

### 2) Time Logic and Duration Handling

1. Forward mode and reverse mode both preserve city-level stay intent.
2. In reverse mode, duration stays attached to the destination city, not the original leg position.
3. Per-city override is supported in reverse mode.
4. Date propagation uses exact elapsed durations, including fractional durations.
5. Example: 2.5 days means 60 hours from arrival, not "2 days plus next morning".
6. Cross-time-zone legs are calculated using absolute timestamps so elapsed stay time remains correct.
7. Duration handling must not drift on timezone or daylight-saving transitions.

### 3) Airport Handling

1. Users can define airport sets per city.
2. Users can include or exclude airports from each city group.
3. The system does not maintain or enforce a curated airport list; user-selected airports are the source of truth.
4. The CLI validates airport code format as uppercase IATA three-letter codes and rejects duplicates with clear errors.
5. Leg searches only use airports allowed by the city group definition.
6. The system can surface nearby airport suggestions ranked by distance, but suggested airports are never auto-added and require explicit user confirmation.
7. Nearby-airport suggestions use a local airport dataset consumed by the CLI.
8. Suggestion ranking uses dataset fields for latitude/longitude, IATA code, and city grouping, and must still respect city group definition and CLI validation rules.
9. Dataset refresh is optional and user-invoked from the CLI; if not refreshed, the CLI uses the latest locally available dataset.
10. If the dataset is unavailable, nearby-airport suggestions are disabled for that run and the CLI reports suggestions as temporarily unavailable without blocking user-provided airport input.

### 4) Route and Candidate Generation

1. Support direction modes: forward, reverse, both.
2. Support route modes: fixed order, reorder-enabled.
3. In reorder-enabled mode, keep first departure city and final return city fixed; permute intermediate cities.
4. Build feasible leg windows from itinerary constraints and duration rules.
5. Apply pruning limits so search does not explode for large itineraries.

### 5) Flight Search Policy

1. Use FLI Python library as the flight data source.
2. Attempt non-stop first by default.
3. If non-stop returns no valid results and fallback is enabled, retry with one-stop as a backup path.
4. Search the entire base departure window before expanding.
5. If no results in base window and expansion is enabled, expand both window ends by 1 hour per round up to a configured cap.
6. Support optional arrival cutoff filtering when requested.

### 6) Booking Construction

1. Generate all-one-way candidate plans.
2. Generate valid multi-city booking candidates.
3. Build round-trip candidates only when outbound and inbound legs are opposite-direction travel between the same city groups and satisfy traveler constraints (passenger mix, cabin or fare restrictions, airport-group compatibility, and configured time windows).
4. Include a round-trip candidate only if FLI returns a valid round-trip fare quote for that paired request.
5. Allow mixed constructions across a single trip.
6. De-duplicate equivalent plans.

### 7) Ranking and Alternatives

1. Default ranking uses a weighted score profile across total price, total duration, stops, and departure convenience.
2. Preset scoring profiles are available with explicit defaults: Cheapest (Price 100%, Duration 0%, Stops 0%, Convenience 0%), Balanced default (Price 40%, Duration 30%, Stops 20%, Convenience 10%), Fastest (Price 0%, Duration 100%, Stops 0%, Convenience 0%), and Fewer Stops (Price 0%, Duration 0%, Stops 100%, Convenience 0%).
3. Every recommendation includes transparent component scores and final weighted score.
4. Return both top full-trip plans and leg-level swap opportunities.
5. Let users configure top-N counts for full-trip and leg-level outputs.
6. Every leg alternative includes swap impact summary: fare delta, duration delta, stop delta, and bundle-compatibility impact, with explicit warning when reduced bundle compatibility may increase total trip price.

### 8) Execution Modes and Output

1. Full automatic mode: optimize the whole trip at once.
2. Interactive mode: let user lock a leg, then recompute remaining legs.
3. CLI output includes grouped direction views (forward/reverse when requested), ranked full-trip plans, leg-level alternatives, constraints used, search policy trace, and status classification for partial/failed lookups.
4. Save machine-readable artifacts in JSON with a common envelope (`runId`, `timestamp`, `schemaVersion`) for reproducibility and replay.
5. For each option, output shows whether it is standalone one-way or tied to a multi-city/round-trip bundle.
6. If a swap breaks or weakens bundle compatibility, output must warn that total trip price can increase versus bundled pricing.

### 9) Reliability and Runtime Behavior

1. Classify unresolved lookups as no-inventory, rate-limited, or unknown.
2. Retry transient failures with exponential backoff and jitter.
3. Throttle requests to reduce API rate-limit risk.
4. Return a structured result for every run, even when partially complete.
5. Do not assume fixed completion times; runtime depends on external API limits and search complexity.
6. Show live progress during long runs, including completed legs, retries, and throttling/backoff events, with summary refresh every 5 seconds and immediate updates on critical events.
7. When limits are hit, return best available partial results with clear coverage gaps.
8. Support configurable request budgets with defaults and bounds: `maxRequests` (default 500, range 50-5000), `maxRetries` (default 5, range 0-10), and `maxExpansionRounds` (default 2, range 0-10).

## Success Criteria

1. The engine reliably returns either ranked plans or clearly classified partial output.
2. Ranking is deterministic for identical inputs and cached responses.
3. No failures are returned without status classification.
4. Users can understand why a plan ranked higher than another without digging into raw logs.

## Decision Log

1. Airport curation: no curated airport list. Users define airport sets per city, and Optifli uses those sets.
2. Round-trip compatibility: pair opposite-direction legs between the same city groups, apply traveler constraints, and include only when FLI returns a valid round-trip fare quote.
3. Scoring: weighted scoring is the default mode with explicit preset weights (Cheapest 100/0/0/0, Balanced 40/30/20/10, Fastest 0/100/0/0, Fewer Stops 0/0/100/0 for Price/Duration/Stops/Convenience).

## Linked Documentation

### User-Facing Stories

1. docs/user-stories/US-001-itinerary-and-constraints.md
2. docs/user-stories/US-002-reverse-duration-remap.md
3. docs/user-stories/US-003-city-airport-groups.md
4. docs/user-stories/US-008-auto-optimization-mode.md
5. docs/user-stories/US-009-interactive-leg-lock-mode.md
6. docs/user-stories/US-011-cli-reporting.md
7. docs/user-stories/US-013-direction-choice-experience.md
8. docs/user-stories/US-014-bundle-risk-guidance.md
9. docs/user-stories/US-015-airport-suggestion-confirmation.md

### Engine Behavior Stories

1. docs/user-stories/US-004-route-and-date-candidates.md
2. docs/user-stories/US-005-flight-search-policy.md
3. docs/user-stories/US-006-booking-construction.md
4. docs/user-stories/US-007-scoring-and-swaps.md

### Operational Stories

1. docs/user-stories/US-010-rate-limit-resilience.md
2. docs/user-stories/US-012-performance-and-artifacts.md

### Engineering Specs

1. docs/engineering-specs/ES-001-search-policy-contract.md
2. docs/engineering-specs/ES-002-scoring-contract.md
3. docs/engineering-specs/ES-003-reporting-contract.md
4. docs/engineering-specs/ES-004-rate-limit-resilience.md
5. docs/engineering-specs/ES-005-runtime-artifacts.md

### Deferred Items

1. docs/TBD.md
