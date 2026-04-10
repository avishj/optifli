<!--
SPDX-FileCopyrightText: 2026 Avish Jha <avish.j@pm.me>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# ES-002: Scoring Contract

## Purpose

Defines score profile weights, swap acceptance rules, and output field semantics for US-007.

## Supports

1. docs/user-stories/US-007-scoring-and-swaps.md

## Contract

1. Score dimensions are Price, Duration, Stops, and DepartureConvenience.
2. Preset profile weights (Price/Duration/Stops/Convenience) for Cheapest are 100/0/0/0.
3. Preset profile weights (Price/Duration/Stops/Convenience) for Balanced default are 40/30/20/10.
4. Preset profile weights (Price/Duration/Stops/Convenience) for Fastest are 0/100/0/0.
5. Preset profile weights (Price/Duration/Stops/Convenience) for FewerStops are 0/0/100/0.
6. Swap acceptance rule is Pareto-like: strictly better in at least one dimension and non-worse in all other dimensions.
7. Swap impact fields are `fareDelta`, `durationDelta`, `stopDelta`, and `bundleCompatibilityImpact`.
8. `bundleCompatibilityImpact` is a categorical value with allowed values `UNCHANGED`, `REDUCED`, or `BROKEN`.
9. Reduced bundle compatibility rule: if `bundleCompatibilityImpact` is `REDUCED` or `BROKEN`, emit a user-visible warning that total trip price may increase versus bundled pricing.

## Deferred Details

1. Exact departure-convenience formula is deferred in docs/TBD.md.
2. Exact internals for deriving `bundleCompatibilityImpact` from bundle scoring signals are deferred until bundle scoring internals are finalized, but the categorical contract in steps 8-9 is required and testable.

## Validation

1. Profile weight tests verify exact weighted-score outputs for fixed fixtures.
2. Swap acceptance tests verify strict-improve and non-worse behavior.
3. Warning tests verify warning behavior for `bundleCompatibilityImpact` values `REDUCED` and `BROKEN`, and no warning for `UNCHANGED`.
