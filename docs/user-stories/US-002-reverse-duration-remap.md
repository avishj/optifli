# US-002: Reverse Direction with Duration Remap

## Story
As a traveler comparing forward vs reverse journeys, I want stay durations to stay attached to destination cities so reverse plans remain realistic.

## Business Value
Reverse-route comparisons are invalid if durations are mirrored by leg position instead of city meaning.

## Acceptance Criteria
1. Given forward mode durations per city, reverse mode reuses the same city durations (including fractional values) in deterministic mapping tests.
2. Users can override reverse durations per city, and overrides take precedence in override tests.
3. Date propagation for reverse mode produces valid, non-overlapping leg windows in schedule consistency tests.
4. Reverse-mode duration handling uses elapsed-time offsets and does not snap to fixed calendar boundaries.
5. CLI output explicitly shows the resolved duration map used for reverse runs.
6. Regression tests cover at least 20 mixed forward/reverse itineraries with expected resolved dates.

## Dependencies
1. City-duration data model from US-001.
2. Route direction engine.
