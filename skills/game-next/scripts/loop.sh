#!/usr/bin/env bash
# Run unattended game-* sessions back to back: one fresh agent process per step, until
# the next step needs a person, or the run stops.
# Usage: AGENT_CMD='<agent non-interactive command>' loop.sh [max-sessions]
# Run from the game repo's root, after setup. It runs the scan unattended, and stops at
# every with-user step (ideation, homework, brainstorm topics) and at every stop for a
# person's moment (calibration, the slice playtest and A/B picks).
# Run it where the plugin installed it: it compares the game's version with the plugin's.
set -euo pipefail

if [[ -z "${AGENT_CMD:-}" ]]; then
  echo "set AGENT_CMD to the agent's non-interactive command, e.g. AGENT_CMD='claude -p'" >&2
  exit 2
fi
STATE_TOOL="docs/game/gamestate.py"
if [[ ! -f "$STATE_TOOL" || ! -f "docs/game/state.json" ]]; then
  echo "no game state here: start with /game-next <idea> in a session with a person" >&2
  exit 2
fi
PLUGIN_TOOL="$(dirname "$0")/../../game-setup/scripts/gamestate.py"
if [[ ! -f "$PLUGIN_TOOL" ]]; then
  echo "run loop.sh from the plugin's skills/game-next/scripts/: it needs the plugin's game-setup/scripts/gamestate.py" >&2
  exit 2
fi
MAX="${1:-50}"

# The same version guard as the game-next skill's step 1: an older or newer game needs a person first.
version_stop() {
  python3 - "$PLUGIN_TOOL" <<'PY'
import json, re, sys
tool = open(sys.argv[1], encoding="utf-8").read()
current = int(re.search(r"^CURRENT_VERSION = (\d+)$", tool, re.M).group(1))
state = json.load(open("docs/game/state.json", encoding="utf-8"))
found, phase = state.get("version", 1), state.get("phase")
if not isinstance(found, int) or isinstance(found, bool):
    print(f"stop: docs/game/state.json version {found!r} is not a whole number")
elif found < current and phase == "setup":
    print(f"stop: this game is at version {found} and the plugin at {current}: "
          "run /game-next in a session with a person to do game-setup upgrade")
elif found < current:
    print(f"stop: this game is at version {found} and the plugin at {current}: "
          "upgrading a game mid-run is not supported; finish it with the plugin release it was made with")
elif found > current:
    print(f"stop: this game is at version {found}, newer than the plugin ({current}): update the plugin")
PY
}
stop_line="$(version_stop)"
if [[ -n "$stop_line" ]]; then
  echo "loop: $stop_line"
  exit 0
fi

report="$(mktemp)"
trap 'rm -f "$report"' EXIT

for ((i = 1; i <= MAX; i++)); do
  next="$(python3 "$STATE_TOOL" status --no-user | sed -n 's/^next: //p')"
  if [[ "$next" == stop:* ]]; then
    echo "loop: $next"
    exit 0
  fi
  echo "loop $i/$MAX: $next"
  $AGENT_CMD "/game-next --unattended" | tee "$report"
  # A stop the session reports (game-next prints it on a line of its own) ends the loop too.
  stop_line="$(grep -m 1 '^stop:' "$report" || true)"
  if [[ -n "$stop_line" ]]; then
    echo "loop: $stop_line"
    exit 0
  fi
done

echo "loop: reached $MAX sessions; run again to continue"
