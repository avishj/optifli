<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# ES-004: Rate-Limit Resilience Contract

## Purpose

Defines retry, classification, and failure-observability behavior supporting US-010.

## Supports

1. docs/user-stories/US-010-rate-limit-resilience.md

## Contract

1. Transient failures trigger exponential backoff with jitter.
2. Retry bound uses `maxRetries` default 5 with configurable range 0-10.
3. Final failure classification uses `no-inventory`, `rate-limited`, or `unknown`.
4. Retry logs include retry count, backoff timing, and final status.
5. Runs return partial outputs when at least one leg has valid candidates.

## Validation

1. Resilience tests verify retry policy behavior.
2. Classification tests verify final status mapping.
3. Integration tests verify partial-output behavior.
