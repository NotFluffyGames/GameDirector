# Unattended sessions

Steps that need no person (planning, building features, verdicts, polish, GDD syncs) can run back to back without anyone starting each session. [scripts/loop.sh](scripts/loop.sh) starts one fresh agent process per step, each running `/game-next --unattended`, and stops when the next step needs a person (`with-user:` ideation or brainstorm topics) or the run stops.

Set `AGENT_CMD` to your agent's non-interactive command, which receives the prompt as its last argument. With Claude Code, for example:

```bash
AGENT_CMD='claude -p' ./loop.sh 50
```

An unattended loop needs the agent's permissions pre-approved for this repo's build, test and git commands. Grant those specific commands in the agent's settings rather than disabling permission checks wholesale.

Ideation and brainstorm topics always wait for a person: when the loop stops with `waiting for a person`, start a session yourself and run `/game-next`. Builds that don't depend on the open topic carry on unattended until nothing else is left.
