# US-005: Execute Flight Search Policy

## Story
As a traveler, I want search to honor my time windows and stop preferences so the options are both cheap and practical.

## Business Value
Correct policy handling prevents invalid recommendations and missed opportunities.

## Acceptance Criteria
1. Each leg search scans the full departure window provided by the user, including cross-day windows.
2. Optional arrival cutoff constraints are applied only when configured, and behavior is covered by cutoff policy tests.
3. Non-stop is attempted first, and one-stop fallback runs only if non-stop returns zero results and fallback is enabled.
4. If base window has zero results, expansion runs in configurable +/-1 or +/-2 hour increments until max expansion limit.
5. Search logs include policy trace fields (base window hit, fallback used, expansion count), and these are present in integration test outputs.

## Dependencies
1. FLI adapter and leg query builder.
2. Policy configuration loader.
