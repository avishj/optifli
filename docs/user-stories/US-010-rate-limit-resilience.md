# US-010: Rate-Limit Resilience and Outcome Classification

## Type
Operational spec

## Story
As an operator, I want robust retries and explicit status classification so I can distinguish inventory gaps from API constraints.

## Business Value
Accurate failure classification drives user trust and better retries.

## Acceptance Criteria
1. Transient API issues are handled automatically without forcing users to restart runs.
2. Failed lookups are clearly classified as inventory gaps, rate-limit issues, or unknown states.
3. The system returns partial results whenever useful options exist, instead of hard-failing the whole run.
4. Users can see clear retry and failure outcomes in run output.

## Dependencies
1. FLI adapter with typed error handling.
2. Structured logger.

## Linked Engineering Specs
1. docs/engineering-specs/ES-004-rate-limit-resilience.md

