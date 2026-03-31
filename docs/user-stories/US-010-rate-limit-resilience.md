# US-010: Rate-Limit Resilience and Outcome Classification

## Story
As an operator, I want robust retries and explicit status classification so I can distinguish inventory gaps from API constraints.

## Business Value
Accurate failure classification drives user trust and better retries.

## Acceptance Criteria
1. Transient failures trigger exponential backoff with jitter and bounded retries (`maxRetries` default 5, configurable range 0-10).
2. Unresolved outcomes are classified as no-inventory, rate-limited, or unknown for every failed leg.
3. Classification quality is validated on mocked resilience test fixtures.
4. The system logs retry count, backoff timings, and final status for every failed lookup.
5. Partial outputs are returned instead of hard-failing when at least one leg has valid candidates.

## Dependencies
1. FLI adapter with typed error handling.
2. Structured logger.
