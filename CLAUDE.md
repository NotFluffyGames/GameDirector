# GameDirector

Agent skills that take a raw game idea to a fun, playable, rich, working and tested game. See `README.md`.

- Skills live in `skills/<name>/`, one folder each, listed in `.claude-plugin/plugin.json`.
- Write and edit skills following the `writing-for-agents` skill: steps end on completion criteria, reference sits behind pointers, leading words over restated triads.
- The game is made over many sessions, one step per session: `game-next` asks the state tool for the step and runs the phase skill in that session. There is no orchestrator conversation.
- Shared reference for game repos lives in `skills/game-setup/game.md`, which game-setup copies into each game as `docs/agents/game.md`. The phase skills point there instead of repeating it.
- `skills/game-setup/scripts/gamestate.py` is the state machine. Change it test-first: `python3 -m unittest discover tests`. Keep its schema in step with `game.md`.
