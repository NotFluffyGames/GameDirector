---
name: game-polish
description: After the full verdict ships, turn polish into definition-of-done features, one pass per role (feel, art, audio, narrative, ux) plus balance, performance and a launchable packaged build; each is reviewed by its role and by the creative director against the identity invariants, and taste calls are settled by a person's A/B picks. Runs after the full verdict in the game-* workflow.
disable-model-invocation: true
---

# Game Polish

Plans the `polish` milestone: the work that makes a game that is already fun on bots feel good in a person's hands and run as a real build, without sanding off what makes it recognisable. game-build then builds it one feature at a time like any other, each reviewed by `game-review polish <id>`, and the final verdict judges the result. Read `docs/agents/game.md` first and follow its session rules.

## 1. Gather

Read the roles' pages (`feel`, `art-bible`, `audio`, `tone-and-world`, `screens`, `onboarding`; ids in `docs/game/wiki.json`), `docs/game/vision.json` (`invariants`, `north_stars`, `roles_off`), the ADRs for platforms, performance budget and asset sources, `docs/game/assets.md`, the full verdict ADR and its review (`docs/game/reviews/verdict-full/`: the notes it decided `feature` are features already), the features already in milestone `polish`, and [polish-checklist.md](polish-checklist.md).

**Done when** you know the target platforms, which assets are still placeholders, which checklist lines apply to this game, and which of them a polish feature already covers.

## 2. Write the polish features

Work through the checklist one section at a time; when this task resumes in a new session, start at the first section with no features yet. Turn every applicable line into features in `docs/game/features.json` (milestone `polish`), each with a pillar, tier, the wiki `pages` it implements, acceptance and verify method, then ticket them as game-plan's step 5 describes. Specifically:

- one feel feature per core action on the `feel` page;
- one final-asset feature per group of placeholder assets in assets.md, citing the art bible, or the `audio` page for sounds;
- one performance feature and one packaged-build feature per target platform this machine can build for. Platforms it can't build for (consoles, signed mobile builds) are listed in the progress entry for the final report, not queued.

Each feature also gets:

- **`roles`**: its section's role, any other role whose aspect it changes ("Which roles are in charge" in `docs/agents/game.md`), and `creative`, which reviews every polish feature against the identity invariants. The design section and the playable build put no owner on their features: `design` judges its section at the final verdict, and no role owns the build.
- **Acceptance** with its roles' measured checks, one per line with the page's number in it, as game-plan's step 4 writes them: a measured failure of it blocks a polish feature like any other.
- **A/B picks** when its acceptance is a taste call (a grade, a feel retune, a mix): verify `human`, the acceptance naming what the person picks, and `how` naming the two to four before-and-after pairs to show, with the measured checks beside them. game-build makes the compare kit and queues its `compare` entry; the picks go into `docs/game/keep.json` and the role's memory, and the feature passes on them ([kits.md](../game-build/kits.md), "Compare kit").

A switched-off role's section doesn't apply (`roles_off`). Lines that don't apply get one sentence each in the progress entry saying why.

**Done when** every applicable checklist line maps to a feature with a ticket, every polish feature has its section's role (where it has one) and `creative` in `roles`, every taste call is verify `human` with its pairs named, and `gamestate.py check --since <base>` passes.

## 3. Re-estimate and close

Raise `limits.budget_sessions` to at least sessions used plus the slice's rate per ticket (status shows the sessions the slice took) times the new tickets, counting a ticket for A/B picks twice, plus 5 for the final verdict. Commit, progress entry, `gamestate.py complete`.

**Done when** `complete` succeeds.
