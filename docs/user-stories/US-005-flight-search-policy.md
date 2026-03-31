# US-005: Execute Flight Search Policy

## Story
As a traveler, I want search to honor my time windows and stop preferences so the options are both cheap and practical.

## Business Value
Correct policy handling prevents invalid recommendations and missed opportunities.

## Acceptance Criteria
1. Each leg search scans the full departure window provided by the user, including cross-day windows.
2. Optional arrival cutoff constraints are applied only when configured, and behavior is covered by cutoff policy tests.
3. Search order is explicit: run non-stop search on the base window first; if zero results and expansion is enabled, expand symmetrically (+/-1h or +/-2h per round) and re-run non-stop until expansion limits are reached; run one-stop fallback only if non-stop still returns zero and fallback is enabled.
4. If one-stop fallback also returns zero, the run returns an empty result set with final status `NO_RESULTS_AFTER_FALLBACK`; one-stop expansion is attempted only when `expandOnFallback=true`.
5. Search logs include structured policy trace fields with stable semantics: `baseWindowHit` (boolean), `fallbackUsed` (boolean), `expansionRounds` (integer), `finalStatus` (enum), `fallbackExhausted` (boolean), and `windowStart/windowEnd` (ISO-8601 timestamps).

## Dependencies
1. FLI adapter and leg query builder.
2. Policy configuration loader.
