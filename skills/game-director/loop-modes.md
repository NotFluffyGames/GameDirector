# Loop modes

How the director gets a fresh session per task, by what the harness offers.

## Subagents (default)

The director dispatches each task to a subagent and waits for its reply. The director's context grows by one short reply per task. Use this whenever the harness can start subagents.

**Parallel builds** (optional, for long build milestones): when the tracker shows several unblocked tickets for different features in the current milestone, dispatch up to 3 `game-build` subagents at once, each in its own git worktree and branch. Merge their branches one at a time, running `gamestate.py check` after each merge. Only the director runs `tick` and `advance`, so `state.json` changes only on the integration branch. Resolve conflicts by keeping both sides: in `features.json` each side's `passes`/`evidence` and new items, in `progress.md` and tracker files both appended blocks. Run sequentially when the harness has no worktrees or the frontier has one ticket.

## External loop

When the harness has no subagents, or the run is too long for one director session, an outer shell loop starts a new agent process per task. Nobody is there to answer questions, so this mode runs autonomous. Each process runs `/game-director --step` (one dispatch plus checks) and exits; the loop stops when status says `stop:`.

[scripts/loop.sh](scripts/loop.sh) does this. Set `AGENT_CMD` to your agent's non-interactive command, which receives the prompt as its last argument. With Claude Code, for example:

```bash
AGENT_CMD='claude -p' ./loop.sh 200
```

An unattended loop needs the agent's permissions pre-approved for this repo's build, test and git commands. Grant those specific commands in the agent's settings rather than disabling permission checks wholesale.

## Resuming

Every mode resumes the same way: all state is on disk, so running `/game-director` again picks up from `gamestate.py status`. After clearing the human queue or raising a limit, run it again.
