# ES-001: Search Policy Contract

## Purpose
Defines deterministic search-order and trace-field behavior for US-005.

## Supports
1. docs/user-stories/US-005-flight-search-policy.md

## Contract
1. Search order step 1: run non-stop search on base window.
2. Search order step 2: if zero non-stop results and expansion is enabled, expand symmetrically by +/-1 hour per round and re-run non-stop until expansion limits are reached. This means round 2 naturally reaches +/-2 hours.
3. Search order step 3: if non-stop still returns zero and fallback is enabled, run one-stop fallback (backup search path).
4. Fallback exhaustion behavior: if fallback also returns zero, set search-outcome `finalStatus` to `NO_RESULTS_AFTER_FALLBACK`.
5. One-stop expansion is attempted only when `expandOnFallback=true`.
6. Policy trace schema includes `baseWindowHit` boolean, `fallbackUsed` boolean, `expansionRounds` integer, `finalStatus` enum (see Final status values), `fallbackExhausted` boolean, `windowStart` ISO-8601 timestamp, and `windowEnd` ISO-8601 timestamp.
7. API failure classifications (`no-inventory`, `rate-limited`, `unknown`) are tracked separately where applicable and are never values of `finalStatus`.

## Final status values
1. `RESULTS_FOUND`: at least one itinerary is found (with or without expansion or fallback).
2. `NO_RESULTS_BASE_WINDOW`: no results are found in the base window, and expansion/fallback are not attempted or not enabled.
3. `NO_RESULTS_AFTER_EXPANSION`: no results are found after exhausting all configured non-stop expansion rounds, and fallback is not attempted or not enabled.
4. `NO_RESULTS_AFTER_FALLBACK`: no results are found after exhausting fallback.

## Validation
1. Integration tests verify search order for base-only, expansion, and fallback paths with fixed +/-1 hour expansion per round.
2. Integration tests verify `finalStatus` allowed values and separation from API failure classifications.
3. Integration tests verify trace-field presence, including separate `windowStart` and `windowEnd` fields.
