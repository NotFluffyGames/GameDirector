# Tech decisions

## Choosing the engine

An engine or framework already in the repo wins, unless its ADR records why it can't meet the criteria below. Otherwise score the candidates that can target every platform in the pitch:

1. **Agent-operable**: builds, tests and exports from the command line, non-interactively. This is the deciding criterion: an engine the agent can't drive headless can't produce evidence.
2. **Text-first project files**: scenes, prefabs and settings in diffable text, so tickets, reviews and merges work.
3. **Headless and off-screen**: runs logic without a window; renders to an image without a display.
4. **Fit to the game**: 2D or 3D, physics, networking and UI needs from the design.
5. **Docs the agent can reach**: official, current and public, so `research` can ground engine-notes.md.
6. **License and cost** compatible with how the game will be shared.

For small 2D or turn-based games, a code-first framework or plain web stack often beats a full editor-centric engine on criteria 1–3. Record the scores and the runner-up in the ADR.

## The simulation core / presentation shell seam

Split the game so its rules are testable without the engine:

| Simulation core | Presentation shell |
| --- | --- |
| game state, rules, AI, economy, progression | rendering, animation, particles, camera |
| fixed tick; time passed in, never read from a clock | audio playback |
| seeded RNG owned by the core | input devices, mapped to input **actions** fed to the core |
| state serializable to a hash | UI widgets, reading core state |
| tuning knobs loaded from data files | scene and asset loading |
| emits events and metrics | reacts to core events with feedback |

The shell calls the core each tick with that tick's input actions and renders the resulting state; the core never calls the shell. Tests, `sim`, `replay` and `bot` all drive the core directly, which is what makes them fast and deterministic.

Deepen the core's interface with the `codebase-design` skill: a few entry points (`step(state, actions) → state, events`, `serialize`, `load_knobs`) over a large implementation.

When the engine must own the rules (its physics or animation drives gameplay), keep the seam at input actions and a state snapshot instead, and follow the adapter contract's "engine owns the logic" fallback.

## Determinism checklist

- One seeded RNG source, passed in; no ambient randomness.
- No wall-clock time, frame-rate-dependent logic or unordered-collection iteration in the core.
- Floating-point results that feed state either avoided (fixed point, integers) or accepted with a tolerance recorded in the ADR.
- Replays store the seed, knob file hash, build version and the input actions per tick.

## Netcode

When the game has networked multiplayer, choose the model in its ADR before any gameplay code: lockstep or rollback (needs the deterministic core above), or server-authoritative with client prediction. The choice decides the core's shape, which is why it can't wait.
