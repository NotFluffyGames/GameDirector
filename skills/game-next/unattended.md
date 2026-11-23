# Unattended sessions

Steps that need no person (the landscape scan and the study of references in the `scan` and `research` phases, planning, building features, verdicts, polish, GDD syncs) can run back to back without anyone starting each session. [scripts/loop.sh](scripts/loop.sh) starts one fresh agent process per step, each running `/game-next --unattended`, and stops when the next step needs a person (`with-user:` setup, ideation or brainstorm topics), when the run stops, or when a session reports a stop (a line starting `stop:` in its output, such as `stop: ClickUp docs unreachable`). Before the first session it compares the game's version with the plugin's, as game-next does, and stops when they differ: run it from where the plugin installed it, since it reads the plugin's `gamestate.py` beside it.

Set `AGENT_CMD` to your agent's non-interactive command, which receives the prompt as its last argument, and run the script from the game repo's root. With Claude Code, for example:

```bash
AGENT_CMD='claude -p' <plugin folder>/skills/game-next/scripts/loop.sh 50
```

An unattended loop needs the agent's permissions pre-approved for this repo's build, test and git commands. Grant those specific commands in the agent's settings rather than disabling permission checks wholesale.

Ideation and brainstorm topics always wait for a person: when the loop stops with `waiting for a person`, start a session yourself and run `/game-next`. Builds that don't depend on the open topic carry on unattended until nothing else is left.

The person's short moments stop the loop too, each with its own stop line saying what to do:

- **Research homework**: while an item in `docs/game/research/homework.json` is open, brainstorm waits (`stop: waiting for research homework`). Answer or skip each open item (on the homework page, on its ticket, or in a session with a person), then run `/game-next` yourself: its homework step folds the answers in before brainstorm.
- **Calibration**: once the visual target passes, the slice verdict waits for the calibration labels (`stop: waiting for calibration`). Label the kit the stop names into `docs/game/calibration/labels.json`, commit, and run the loop again. Builds go on meanwhile; only the slice verdict waits.
- **The slice playtest** (`stop: waiting for the slice playtest`): play the build with the kit and write the answers file.
- **A/B picks**: once nothing else in polish is left to build, the final verdict waits for the picks (`stop: waiting for A/B picks`). Write one pick per pair into the file the stop names, leave the queue entry, commit, and run the loop again: a build session applies them.
