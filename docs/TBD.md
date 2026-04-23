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
7. Reorder mode (`route_mode=reorder`): deferred because smart pruning requires realistic travel-time estimates between all destination pairs. Without them, the permutation space grows factorially with no way to discard infeasible orderings early. B3's `probe_travel_times()` can feed real FLI-based estimates to make this viable. Design considerations: permutation cap (e.g., max 6–8 destinations for reorder), heuristic pre-filters (geographic clustering, known hub connections), and caching of probe results across candidates.
8. Explicit-leg feasibility remains estimate-based. B2 only checks whether the next departure window is impossible under a rough travel-time + stay heuristic; true feasibility needs real arrival and search data from later stages in B3.
9. Configurable retry/rate-limit for the FLI search client. Currently delegates to FLI's built-in defaults (3 retries with exponential backoff, 10 req/s rate limit). Future work: own retry count, backoff, jitter, and rate-limit settings in Optifli's `Settings`, applied via a custom HTTP client injected into `SearchFlights`.
10. Explicit currency support for price outputs. The current FLI API provider returns prices natively as floats without currency metadata, assuming defaults based on the executing environment (e.g. USD). Future updates to the CLI should allow explicit currency specification if supported upstream.
11. Post-filter search results against the original departure window. The FLI API only accepts whole-hour time restrictions, so `_build_time_restrictions` floors/ceils partial-hour bounds (e.g. 06:30–22:45 becomes 06:00–23:00) and drops restrictions entirely for near-full-day windows. This means flights departing outside the user's actual `DepartureWindow` can leak through. A post-filter step in the adapter or policy layer should discard options whose departure time falls outside the original window bounds.
