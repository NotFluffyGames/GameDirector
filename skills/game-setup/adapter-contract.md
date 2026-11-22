# Adapter contract

The commands every game-* session uses to build, run and prove the game, whatever the engine, language or platform. game-setup fills the Commands table in `docs/agents/game.md` with one shell command per row, run from the repo root, non-interactive, exiting non-zero on failure.

The **dev platform** is whatever the agent's machine can build and run: a desktop build, the target's emulator or simulator, or a browser build. For a mobile- or console-only game, pick the closest of these in the engine ADR; `package` still targets the real platforms.

Write commands as thin wrappers (a `scripts/` or `tools/` file, a make target, a package script) when the raw engine invocation is long. The wrapper is then the single place engine knowledge lives.

## Commands

| Name | Does | Output | Required |
| --- | --- | --- | --- |
| `bootstrap` | installs toolchain and dependencies on a fresh machine | exit code | yes |
| `build` | compiles or imports the project for the dev platform | exit code; build log | yes |
| `test` | runs the whole automated test suite; accepts a filter for a single test or file | test report | yes |
| `run` | launches the game for a person to play | a running game | yes |
| `sim` | runs the simulation core headless: `--seed N --ticks T [--knobs FILE]` (a tick is a frame or a turn) | final state hash and metrics as JSON on stdout | yes |
| `replay` | plays a recorded input file through the game: `FILE [--seed N]` | final state hash and metrics JSON | yes |
| `bot` | runs a bot policy for N matches or runs: `--policy P --runs N --seed S [--knobs FILE]` | metrics JSON per run plus a summary | yes |
| `capture` | renders a screenshot (and optionally video) at a seed and tick: `--seed N --tick T --out PATH` | image file(s) | if the platform can render off-screen |
| `package` | produces a distributable build per target platform: `--platform P` | artifact path(s) | yes, by the polish phase |

Same seed, same input, same knobs → same state hash. That determinism is what makes `sim`, `replay` and `bot` evidence instead of anecdotes.

## Smoke test

Run each command on the current project in this session and record the result in the Verified column (date and a one-line result). A command is verified when:

- `bootstrap`, `build`, `test`: exit 0.
- `run`: the game starts and stays up for 10 seconds, then exits cleanly when stopped (check with a timeout and the process exit or log). With no display, start it under a virtual display; failing that, verify it starts with the engine's headless or no-window flag and record that the windowed launch is untested.
- `sim`: two runs with the same seed print the same hash; a different seed prints a different one.
- `replay`: replaying a file recorded from a `sim` or `bot` run reproduces its hash.
- `bot`: prints metrics JSON for at least 2 runs.
- `capture`: writes a non-empty image; look at it.
- `package`: produces an artifact for at least the dev platform that launches.

When every required command is verified, set `adapter_verified: true` in `docs/game/state.json`.

## When the engine resists

- **No headless mode**: keep the simulation core in plain code that builds and runs outside the engine; `sim`, `replay` and `bot` drive that. The engine only hosts the presentation shell.
- **No way to run game logic headless at all** (neither outside nor inside the engine): mark `sim`, `replay` and `bot` `n/a`. game-plan then measures proxies with instrumented `test` runs where it can and turns the rest into `human` items; the verdict leans on the playtest kit. Say so in the engine ADR: it is the weakest setup this workflow supports.
- **No off-screen rendering** (`capture`): try a virtual display (for example a headless X server on Linux) or the engine's own render-to-texture. If neither works, mark `capture` `n/a` with the reason; visual checks then become `human` verify items.
- **Physics or logic owned by the engine** (the core can't leave it): run the engine itself headless with a fixed timestep and record input; `sim`, `replay` and `bot` become scripted engine runs. Accept weaker determinism and say so in the engine ADR; compare metrics within a tolerance instead of exact hashes.
- **Target platform needs hardware or a store toolchain the agent lacks** (consoles, mobile signing): `package` covers what this machine can build; the rest goes to the human queue with a wizard.
- **Windows machine**: write wrappers in a language both shells run (Python, or the engine's own scripting), not bash.

Facts about how the chosen engine does each of these come from its official docs, gathered with the `research` skill into `docs/game/engine-notes.md`.
