# US-011: CLI Reporting and Explainability

## Story
As a traveler, I want a clear CLI report with ranking rationale so I can confidently choose a booking plan.

## Business Value
Readable outputs improve decision speed and reduce confusion.

## Acceptance Criteria
1. Report output includes ranked global plans, leg-level alternatives, and constraint summary sections.
2. Each global plan includes total fare, total duration, stop count, and ranking explanation.
3. Report displays warning banners for unknown classifications or incomplete coverage.
4. Report formatting follows the project's standard CLI presentation style consistently across runs.
5. Snapshot tests cover at least 20 report scenarios for stable rendering.

## Dependencies
1. Scoring pipeline output schema.
2. CLI formatter and template layer.
