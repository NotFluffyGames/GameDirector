# Unattended sessions

Steps that need no person (planning, building features, verdicts, polish, GDD syncs) can run back to back without anyone starting each session. [scripts/loop.sh](scripts/loop.sh) starts one fresh agent process per step, each running `/game-next --unattended`, and stops when the next step needs a person (`with-user:` setup, ideation or brainstorm topics), when the run stops, or when a session reports a stop (a line starting `stop:` in its output, such as `stop: ClickUp docs unreachable`). Before the first session it compares the game's version with the plugin's, as game-next does, and stops when they differ: run it from where the plugin installed it, since it reads the plugin's `gamestate.py` beside it.

Set `AGENT_CMD` to your agent's non-interactive command, which receives the prompt as its last argument, and run the script from the game repo's root. With Claude Code, for example:

```bash
AGENT_CMD='claude -p' <plugin folder>/skills/game-next/scripts/loop.sh 50
```

An unattended loop needs the agent's permissions pre-approved for this repo's build, test and git commands. Grant those specific commands in the agent's settings rather than disabling permission checks wholesale.

Ideation and brainstorm topics always wait for a person: when the loop stops with `waiting for a person`, start a session yourself and run `/game-next`. Builds that don't depend on the open topic carry on unattended until nothing else is left.
