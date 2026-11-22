#!/usr/bin/env bash
# Run unattended game-* sessions back to back: one fresh agent process per step, until
# the next step needs a person, or the run stops.
# Usage: AGENT_CMD='<agent non-interactive command>' loop.sh [max-sessions]
# Run from the game repo's root, after ideation and brainstorm have been done with a person.
set -euo pipefail

if [[ -z "${AGENT_CMD:-}" ]]; then
  echo "set AGENT_CMD to the agent's non-interactive command, e.g. AGENT_CMD='claude -p'" >&2
  exit 2
fi
STATE_TOOL="docs/game/gamestate.py"
if [[ ! -f "$STATE_TOOL" ]]; then
  echo "no game state here: start with /game-next <idea> in a session with a person" >&2
  exit 2
fi
MAX="${1:-50}"

for ((i = 1; i <= MAX; i++)); do
  next="$(python3 "$STATE_TOOL" status --no-user | sed -n 's/^next: //p')"
  if [[ "$next" == stop:* ]]; then
    echo "loop: $next"
    exit 0
  fi
  echo "loop $i/$MAX: $next"
  $AGENT_CMD "/game-next --unattended"
done

echo "loop: reached $MAX sessions; run again to continue"
