# US-012: Rate-Limit-Aware Execution and Run Artifacts

## Story
As a maintainer, I want runs to stay useful even under API limits so optimization remains observable, debuggable, and actionable.

## Business Value
Rate-limit-aware execution and reproducibility are required for dependable rollout.

## Acceptance Criteria
1. The system does not promise fixed completion time; it reports live progress based on current request throughput.
2. During execution, CLI shows progress metrics including completed legs, requests sent, retries, and throttling/backoff events.
3. Every run emits machine-readable artifacts including normalized input, selected policies, candidate summaries, and final classification.
4. Artifacts can replay deterministic ranking in replay test cases using cached payloads.
5. Long-run cancellation exits gracefully and preserves partial artifacts.
6. If request budget is exhausted or rate limits persist, the run returns partial results with unresolved segments clearly labeled.
7. Request budget controls are configurable (max requests, max retries, max expansion rounds).

## Dependencies
1. Rate-limit simulation harness.
2. Artifact persistence and replay utility.
