<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-012: Performance, Rate-Limit-Aware Execution, and Run Artifacts

## Type
Operational spec

## Story
As a maintainer, I want runs to stay useful even under API limits so optimization remains observable, debuggable, and actionable.

## Business Value
Rate-limit-aware execution and reproducibility are required for dependable rollout.

## Acceptance Criteria
1. Long-running execution shows live progress and remains useful under API limits.
2. Runs always emit machine-readable artifacts that support debugging and replay.
3. Cancellation preserves usable partial output and artifacts.
4. Runtime budget controls are configurable for different quota and speed trade-offs.

## Dependencies
1. Rate-limit simulation harness.
2. Artifact persistence and replay utility.

## Linked Engineering Specs
1. docs/engineering-specs/ES-005-runtime-artifacts.md
