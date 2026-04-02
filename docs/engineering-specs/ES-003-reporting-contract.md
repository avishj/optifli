<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# ES-003: Reporting Contract

## Purpose
Defines report field-level schema and verbosity behavior for US-011.

## Supports
1. docs/user-stories/US-011-cli-reporting.md

## Contract
1. Summary mode (default) fields per leg include `attemptedQueries`, `successfulQueries`, `failedQueries`, `fallbackUsed`, `expansionRounds`, and `finalStatus`.
2. Verbose mode includes summary fields plus per-query window boundaries and timestamps.
3. Report rows include construction type indicator (`standalone-one-way` or `bundle`).
4. Report rows include bundle-risk warning text when bundle compatibility is reduced.

## Validation
1. Snapshot tests cover summary-mode and verbose-mode variants.
2. Snapshot tests cover warning and non-warning swap scenarios.
