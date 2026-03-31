# US-012: Performance, Rate-Limit-Aware Execution, and Run Artifacts

## Type
Operational spec

## Story
As a maintainer, I want runs to stay useful even under API limits so optimization remains observable, debuggable, and actionable.

## Business Value
Rate-limit-aware execution and reproducibility are required for dependable rollout.

## Acceptance Criteria
1. The system does not promise fixed completion time; it reports live progress based on current request throughput.
2. During execution, CLI shows progress metrics including completed legs, requests sent, retries, and throttling or backoff events, refreshed every 5 seconds by default and immediately on critical state changes.
3. Every run emits machine-readable artifacts in JSON with a common envelope (`runId`, `timestamp`, `schemaVersion`) and payloads for normalized input, selected policies, candidate summaries, and final classification.
4. Artifacts follow a versioned schema contract; replay validates schema compatibility before execution and supports backward-compatible schemas or documented migration paths.
5. Long-run cancellation via SIGINT or SIGTERM exits gracefully, preserves partial artifacts, and flushes pending logs.
6. If request budget is exhausted or rate limits persist, the run returns partial results with unresolved segments clearly labeled.
7. Request budget controls are configurable with defaults and bounds: `maxRequests` (default 500, range 50-5000), `maxRetries` (default 5, range 0-10), and `maxExpansionRounds` (default 2, range 0-10).

## Dependencies
1. Rate-limit simulation harness.
2. Artifact persistence and replay utility.
