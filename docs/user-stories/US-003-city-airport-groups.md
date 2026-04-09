<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# US-003: Manage City Airport Groups

## Type

User-facing

## Story

As a traveler, I want to define which airports belong to each city in my itinerary so search remains relevant and avoids unsuitable airports.

## Business Value

Airport quality and inclusion materially affect price and feasibility.

## Acceptance Criteria

1. Users can set a city code and maintain include/exclude airport lists per city group in CLI config.
2. The system does not auto-curate or auto-insert airports; user-provided airport sets are authoritative.
3. CLI validates airport code format as uppercase IATA three-letter codes (`[A-Z]{3}`) and rejects duplicates with clear error messages.
4. Each leg query uses only airports allowed by the city group rules, and this is validated by integration tests.
5. Edits to city airport groups in profile files are reflected in the next run with no restart required.
6. The system surfaces nearby airport suggestions ranked by distance from the selected city center, but suggestions are never auto-inserted and require explicit user confirmation.

## Dependencies

1. Airport code validator.
2. Leg query builder.
3. Airport geodata source for distance-based suggestions.
