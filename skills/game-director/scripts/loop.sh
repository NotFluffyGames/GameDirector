#!/usr/bin/env bash
# Run the game-director one step per fresh agent process until it says stop.
# Usage: AGENT_CMD='<agent non-interactive command>' [IDEA='<game idea>'] loop.sh [max-iterations]
# Run from the game repo's root. IDEA is passed only to the first, setup run, which saves it
# to docs/game/seed.md. This mode runs autonomous: no one is there to answer questions.
set -euo pipefail

if [[ -z "${AGENT_CMD:-}" ]]; then
  echo "set AGENT_CMD to the agent's non-interactive command, e.g. AGENT_CMD='claude -p'" >&2
  exit 2
fi
MAX="${1:-100}"
STATE_TOOL="docs/game/gamestate.py"

for ((i = 1; i <= MAX; i++)); do
  args="--step"
  if [[ -f "$STATE_TOOL" ]]; then
    next="$(python3 "$STATE_TOOL" status | sed -n 's/^next: //p')"
    if [[ "$next" == stop:* ]]; then
      echo "loop: $next"
      exit 0
    fi
    echo "loop $i/$MAX: $next"
  else
    echo "loop $i/$MAX: setup"
    args="--step ${IDEA:-}"
  fi
  $AGENT_CMD "/game-director $args"
done

echo "loop: reached $MAX iterations; run again to continue"
