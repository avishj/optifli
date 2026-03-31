# ES-001: Search Policy Contract

## Purpose
Defines deterministic search-order and trace-field behavior for US-005.

## Supports
1. docs/user-stories/US-005-flight-search-policy.md

## Contract
1. Search order step 1: run non-stop search on base window.
2. Search order step 2: if zero non-stop results and expansion is enabled, expand symmetrically (+/-1h or +/-2h per round) and re-run non-stop until expansion limits are reached.
3. Search order step 3: if non-stop still returns zero and fallback is enabled, run one-stop fallback.
4. Fallback exhaustion behavior: if fallback also returns zero, classify as `NO_RESULTS_AFTER_FALLBACK`.
5. One-stop expansion is attempted only when `expandOnFallback=true`.
6. Policy trace schema includes `baseWindowHit` boolean, `fallbackUsed` boolean, `expansionRounds` integer, `finalStatus` enum, `fallbackExhausted` boolean, and `windowStart/windowEnd` ISO-8601 timestamps.

## Validation
1. Integration tests verify search order for base-only, expansion, and fallback paths.
2. Integration tests verify no-results classification and trace-field presence.