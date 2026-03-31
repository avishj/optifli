# ES-005: Runtime and Artifact Contract

## Purpose
Defines runtime progress, cancellation, and artifact contract details supporting US-012.

## Supports
1. docs/user-stories/US-012-performance-and-artifacts.md

## Contract
1. Runtime does not promise fixed completion time.
2. Progress display includes completed legs, requests, retries, and throttle/backoff events.
3. Summary progress refreshes every 5 seconds by default and updates immediately on critical events.
4. Artifacts are JSON with envelope fields `runId`, `timestamp`, and `schemaVersion`.
5. Artifact payloads include normalized input, selected policies, candidate summaries, and final classification.
6. Replay validates schema compatibility and supports backward-compatible schemas or documented migration paths.
7. Cancellation via SIGINT or SIGTERM preserves partial artifacts and flushes pending logs.
8. Runtime budget defaults and bounds are `maxRequests` default 500 range 50-5000, `maxRetries` default 5 range 0-10, and `maxExpansionRounds` default 2 range 0-10.

## Validation
1. Runtime tests verify progress and cancellation behavior.
2. Artifact tests verify schema fields and replay compatibility checks.