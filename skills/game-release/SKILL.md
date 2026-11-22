---
name: game-release
description: After a ship verdict, turn polish and release work into definition-of-done features - game feel, balance, performance, accessibility, final assets, packaging, store materials - with wizards for the steps only a person can do. Phase 5 of the game-* workflow.
disable-model-invocation: true
---

# Game Release

Plans the last two milestones, `polish` and `release`; game-build then builds them one feature at a time like any other. Read `docs/agents/game.md` first and follow its session rules.

## 1. Gather

Read `design.md`, the ADRs for platforms, performance budget and asset sources, `docs/game/assets.md`, the full verdict ADR (its notes on feel and visuals feed polish), and [release-checklist.md](release-checklist.md).

**Done when** you know the target platforms, which assets are still placeholders, and which checklist lines apply to this game.

## 2. Write the polish and release features

Turn every applicable checklist line into features in `docs/game/features.json` (milestone `polish` or `release`), each with a pillar, tier, acceptance and verify method, then ticket them as game-plan's step 4 describes. Specifically:

- one final-asset feature per group of placeholder assets in assets.md, citing the design's style guide;
- one performance feature per target platform, measured against the budget ADR;
- a wizard feature for the human-only release steps: the `wizard` skill writes it under `scripts/release/`, verified by `bash -n`; a human queue entry points to it.

Lines that don't apply get one sentence each in the progress entry saying why.

**Done when** every applicable checklist line maps to a feature with a ticket, and `gamestate.py check` passes.

## 3. Close

Commit, progress entry. The director drives game-build through the new features; when they pass, the run ends with a release candidate and the human queue.
