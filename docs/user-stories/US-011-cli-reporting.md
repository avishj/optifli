<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-011: CLI Reporting and Explainability

## Type
User-facing

## Story
As a traveler, I want a clear CLI report with ranking rationale so I can confidently choose a booking plan.

## Business Value
Readable outputs improve decision speed and reduce confusion.

## Acceptance Criteria
1. Report output includes ranked global plans, leg-level alternatives, constraint summary sections, grouped direction views (forward/reverse when requested), search policy traces, and construction type indicators (standalone one-way vs multi-city/round-trip bundle).
2. Each global plan includes total fare, total duration, stop count, and ranking explanation.
3. Report displays warning banners for unknown classifications, incomplete coverage, and swaps that reduce bundle compatibility (with potential total-price increase warning).
4. Report formatting follows a stable default summary mode, with an optional verbose mode for deeper diagnostics.
5. Snapshot tests cover representative report scenarios for stable rendering.

## Dependencies
1. Scoring pipeline output schema.
2. CLI formatter and template layer.

## Linked Engineering Specs
1. docs/engineering-specs/ES-003-reporting-contract.md
