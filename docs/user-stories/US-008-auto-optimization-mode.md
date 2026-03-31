# US-008: Full-Trip Automatic Optimization Mode

## Story
As a traveler who wants speed, I want a one-command full optimization run so I can get best recommendations without manual leg decisions.

## Business Value
Default automation enables quick, repeatable planning.

## Acceptance Criteria
1. One CLI command runs complete optimization for selected mode (forward, reverse, or both) without interactive prompts.
2. The mode outputs ranked global plans and leg-level alternatives in a single report.
3. If some legs fail classification, the mode still returns partial ranked output with explicit warnings.
4. Pilot users can complete one run without assistance in usability sessions.
5. Automated mode supports profile-based defaults for stop policy, expansion policy, and top-N counts.

## Dependencies
1. Candidate generation, search, combination, and scoring pipeline.
2. CLI report formatter.
