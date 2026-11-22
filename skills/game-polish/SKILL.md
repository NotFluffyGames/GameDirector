---
name: game-polish
description: After the full verdict ships, turn polish into definition-of-done features - game feel, final art and audio, balance, performance, accessibility, onboarding, settings and saves, and a launchable packaged build. Phase 5 of the game-* workflow.
disable-model-invocation: true
---

# Game Polish

Plans the `polish` milestone: the work that makes a game that is already fun on bots feel good in a person's hands and run as a real build. game-build then builds it one feature at a time like any other, and the final verdict judges the result. Read `docs/agents/game.md` first and follow its session rules.

## 1. Gather

Read `design.md` (Feel, Screens and onboarding, Tone, art and world), the ADRs for platforms, performance budget and asset sources, `docs/game/assets.md`, the full verdict ADR (its notes on feel and visuals), and [polish-checklist.md](polish-checklist.md).

**Done when** you know the target platforms, which assets are still placeholders, and which checklist lines apply to this game.

## 2. Write the polish features

Work through the checklist one section at a time; when this task resumes in a new session, start at the first section with no features yet. Turn every applicable line into features in `docs/game/features.json` (milestone `polish`), each with a pillar, tier, acceptance and verify method, then ticket them as game-plan's step 4 describes. Specifically:

- one feel feature per core action in design.md's Feel section;
- one final-asset feature per group of placeholder assets in assets.md, citing the style guide;
- one performance feature and one packaged-build feature per target platform this machine can build for. Platforms it can't build for (consoles, signed mobile builds) are listed in the progress entry for the final report, not queued.

Lines that don't apply get one sentence each in the progress entry saying why.

**Done when** every applicable checklist line maps to a feature with a ticket, and `gamestate.py check --since <base>` passes.

## 3. Re-estimate and close

Raise `limits.budget_sessions` to at least sessions used plus 1.5 × the new tickets plus 5 for the final verdict. Commit, progress entry, `gamestate.py complete`.
