# US-001: Capture Itinerary and Constraints

## Story
As a vacation planner, I want to provide my city sequence, stay durations, and date/time constraints so that Optifli can generate valid optimization candidates.

## Business Value
Without structured input and constraint validation, optimization results are unreliable.

## Acceptance Criteria
1. The CLI accepts itinerary inputs with 1 origin city, 1-10 destination cities, and 1 final return city via flags or profile file.
2. The CLI accepts per-destination stay durations as fractional days or hours (for example: HAN=2d, DAD=1.5d, PQC=2.5d, SIN=0.5d; or 12h, 30h) and validates required values in <=1 second for a 10-destination payload on a standard developer workstation.
3. The CLI accepts per-leg departure windows as start/end datetime, including cross-day windows.
4. Stay durations are applied as elapsed time from arrival, with no hard noon or midnight boundary assumptions (for example: 0.5d means 12 hours from the arrival timestamp).
5. Invalid inputs return actionable errors (field, reason, fix hint), and this behavior is covered by validation tests.
6. Schema validation unit tests provide strong coverage for input parsing and validation modules.
7. Date/time parsing requires timezone context (offset or named timezone), with clear validation errors for missing timezone.

## Dependencies
1. CLI argument parser and config loader.
2. Domain model for itinerary, leg windows, and durations.
