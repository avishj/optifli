# US-003: Manage City Airport Groups

## Story
As a traveler, I want to define which airports belong to each city in my itinerary so search remains relevant and avoids unsuitable airports.

## Business Value
Airport quality and inclusion materially affect price and feasibility.

## Acceptance Criteria
1. Users can set a city code and maintain include/exclude airport lists per city group in CLI config.
2. The system does not auto-curate or auto-insert airports; user-provided airport sets are authoritative.
3. CLI validates airport code format and duplicate entries with clear error messages.
4. Each leg query uses only airports allowed by the city group rules, and this is validated by integration tests.
5. Edits to city airport groups in profile files are reflected in the next run with no restart required.

## Dependencies
1. Airport code validator.
2. Leg query builder.
