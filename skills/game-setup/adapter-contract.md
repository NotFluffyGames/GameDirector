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
| `sim` | runs the simulation core headless: `--seed N --ticks T [--knobs FILE] [--events PATH]` (a tick is a frame or a turn) | final state hash and metrics as JSON on stdout; the event log at PATH | yes; `--events` optional |
| `replay` | plays a recorded input file through the game: `FILE [--seed N] [--events PATH]` | final state hash and metrics JSON; the event log | yes; `--events` optional |
| `bot` | runs a bot policy for N matches or runs: `--policy P --runs N --seed S [--knobs FILE] [--events DIR]` | metrics JSON per run plus a summary; an event log per run | yes; `--events` optional |
| `capture` | renders a screenshot (and optionally video) at a seed and tick: `--seed N --tick T --out PATH`; a named state: `--state NAME --out PATH`; a frame strip: `--strip INPUT --frames N --every K --out PATH` | image file(s) | if the platform can render off-screen; `--state` and `--strip` optional |
| `dump` | lists what the player reads and sets: `strings`, `ui` or `settings`, `--out PATH` | JSON | optional |
| `loudness` | measures the mixed output in a named state: `--state NAME --seconds S` | integrated loudness (LUFS) and true peak (dBTP) as JSON | optional |
| `package` | produces a distributable build per target platform: `--platform P` | artifact path(s) | yes, by the polish phase |

Same seed, same input, same knobs → same state hash. That determinism is what makes `sim`, `replay` and `bot` evidence instead of anecdotes.

## What the roles read

The roles review the running game from these outputs; game-review makes them once per review from one build. Each is optional: where the engine can't give one, it is `n/a` with its reason (see When the engine resists).

- **Named states**: `capture --state NAME` renders one of the capture states game-plan records in `docs/game/engine-notes.md` (a beauty view, a typical play moment, peak effects load, each main menu, the HUD over the brightest and darkest areas), each defined there as a seed, a tick or replay prefix, and a camera. The same build and state render the same frame.
- **Frame strips**: `capture --strip INPUT --frames N --every K` plays the scripted input file INPUT and saves N frames, one every K frames from its first input, into PATH as numbered images or as one contact sheet; `measure.py sheet` (the game-review skill's `scripts/measure.py`) stitches numbered frames into a sheet.
- **The event log**: `sim`, `replay` and `bot` with `--events` write JSON lines, one event each, `frame` counted from the start of the run. Where the core runs headless, log the feedback the core asks of the shell.

  ```
  {"frame": 0, "kind": "launch", "ms": 0}
  {"frame": 96, "kind": "control", "ms": 1600}
  {"frame": 398, "kind": "input", "action": "dash", "accepted": false, "why": "outside the buffer window"}
  {"frame": 412, "kind": "input", "action": "dash", "accepted": true}
  {"frame": 412, "kind": "action", "action": "dash", "input": 412, "response": 414, "channels": ["visual", "sound", "camera"]}
  {"frame": 414, "kind": "sound", "event": "dash", "sample": "dash_whoosh_03", "voices": 6}
  ```

  - `input`, per input that arrives: the `action` it maps to, and `accepted` `true` or `false`; a dropped one also says `why` (outside a buffer or forgiveness window, locked out by another action, ...).
  - `action`, per player action (named as the feel sheets name them): the frame its input arrived (`input`), the frame its first response shows (`response`), and the feedback `channels` it fired: `visual` effect, `sound` event, `camera`, `haptic`.
  - `sound`, per sound event: the gameplay `event` it serves, the `sample` id played, and the `voices` playing at that moment.
  - `launch` and `control`, from a run that starts at launch (a `replay` recorded from the title screen): the launch and the first accepted input, with wall-clock `ms`, giving launch-to-control time.

  The same seed and input write the same log, `ms` aside.
- **Dumps**: `dump strings` lists every player-facing string with its id and where it shows (screen, and place: button, title, tooltip, subtitle); `dump ui` lists, per screen, its size and each text box with its id, position and size in pixels, and its text size; `dump settings` lists what the settings menu offers, each option with its values.
- **Loudness**: `loudness` renders S seconds of the mix in a named state offline and measures it (ffmpeg's `ebur128` filter, for one).

## Smoke test

Run each command on the current project in this session and record the result in the Verified column (date and a one-line result).

**Test fixtures.** Adapter mode runs at plan's walking skeleton, before the game has a title screen, a settings menu or a sound. An optional output the engine supports is smoke-tested on a **test fixture** the skeleton adds for the purpose: a test state or scene, outside the shipped game, holding one scripted action that fires a visual effect and a test tone, one input it drops, one text box, and one settings entry. Such an output is never `n/a` for want of content: `n/a` means the engine can't give it.

A command is verified when:

- `bootstrap`, `build`, `test`: exit 0.
- `run`: the game starts and stays up for 10 seconds, then exits cleanly when stopped (check with a timeout and the process exit or log). With no display, start it under a virtual display; failing that, verify it starts with the engine's headless or no-window flag and record that the windowed launch is untested.
- `sim`: two runs with the same seed print the same hash; a different seed prints a different one.
- `replay`: replaying a file recorded from a `sim` or `bot` run reproduces its hash.
- `bot`: prints metrics JSON for at least 2 runs.
- `capture`: writes a non-empty image; look at it.
- `capture --state`: writes a non-empty image for each state `engine-notes.md` names, or for the fixture's state before game-plan names any; look at one.
- `capture --strip`: a strip of a core action, or of the fixture's action, writes N frames or a sheet showing them; look at it: the action plays across the frames.
- the event log: a `replay` of a core action, or of the fixture's action, with `--events` logs an `input` line per input, an `action` line with `input`, `response` and at least one channel, and a `sound` line for the sound it plays; an input the game drops (the fixture's, before the game has its own) logs `accepted: false` with its `why`; two `sim` runs with the same seed write the same log; a run from launch logs `launch` and `control`.
- `dump`: each kind writes valid JSON holding the game's strings, text boxes and settings, or at least the fixture's text box and settings entry before the game has its own.
- `loudness`: prints LUFS and true peak for a state with sound: the fixture's test tone before the game has its own.
- `package`: produces an artifact for at least the dev platform that launches.

When every required command is verified and every optional one is verified (on the fixture while the game has nothing of its own to show) or `n/a` because the engine can't give it, with the reason, set `adapter_verified: true` in `docs/game/state.json`.

## When the engine resists

- **No headless mode**: keep the simulation core in plain code that builds and runs outside the engine; `sim`, `replay` and `bot` drive that. The engine only hosts the presentation shell.
- **No way to run game logic headless at all** (neither outside nor inside the engine): mark `sim`, `replay` and `bot` `n/a`. game-plan then measures proxies with instrumented `test` runs where it can and turns the rest into `human` items; the verdict leans on the playtest kit. Say so in the engine ADR: it is the weakest setup this workflow supports.
- **No off-screen rendering** (`capture`): try a virtual display (for example a headless X server on Linux) or the engine's own render-to-texture. If neither works, mark `capture` `n/a` with the reason; visual checks then become `human` verify items.
- **An optional output the engine can't give** (`--state`, `--strip`, `--events` or one of its event kinds, a `dump` kind, `loudness`): mark it `n/a` with the reason in the Verified column. One the engine supports but the game can't show yet is no `n/a`: it is verified on the test fixture (Smoke test). A review's `inputs/index.md` then lists it as `<input>: n/a: <reason>`, the role checks that need it are `not-assessed` with that reason, and game-plan writes acceptance that needs it as `human` verify items. A hand-made or remembered substitute never stands in for it.
- **Physics or logic owned by the engine** (the core can't leave it): run the engine itself headless with a fixed timestep and record input; `sim`, `replay` and `bot` become scripted engine runs. Accept weaker determinism and say so in the engine ADR; compare metrics within a tolerance instead of exact hashes.
- **Target platform needs hardware or a store toolchain the agent lacks** (consoles, mobile signing): `package` covers what this machine can build; the rest goes to the human queue with a wizard.
- **Windows machine**: write wrappers in a language both shells run (Python, or the engine's own scripting), not bash.

Facts about how the chosen engine does each of these come from its official docs, gathered with the `research` skill into `docs/game/engine-notes.md`.
