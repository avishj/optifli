<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# TBD (Future Work)

## Deferred for Later

1. Departure convenience formula details are deferred for now.
2. Future update should define exact convenience components, scoring formula, and tuning knobs (for example preferred time windows, red-eye penalties, and connection comfort penalties).
3. Current behavior remains weighted scoring with the default profile values already defined in PRD and US-007.
4. Bundled airport database: a filtered dataset (e.g., OurAirports CSV) with IATA code, name, lat/lon, and city for all worldwide airports. This would enable offline airport name lookups, validation against real codes, and distance-based nearby-airport suggestions (US-003, US-015). Currently, airport validation uses format-only checks (`[A-Z]{3}`) plus FLI's Airport enum.
5. Add Interactive Recheck post Interactive input.
6. Wizard: support multi-airport city groups (e.g., `DEL BOM`) and descriptive city names instead of repeating the IATA code as the name.
