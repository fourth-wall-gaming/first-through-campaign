#!/usr/bin/env bash
#
# First Through preflight. Reports the state of the save; never changes it.
#
# Deliberately does NOT import the campaign. Importing writes several hundred
# rows and is a real act with a real cost, so it belongs to a command the user
# ran (/first-through:start), not to a hook that fires every time they open a
# terminal. All this does is find out where things stand and say so, because on
# SessionStart hook stdout reaches the model.
#
# Like the engine's preflight, it never exits non-zero: having this plugin
# enabled must not block a session in an unrelated directory.

set -uo pipefail
unset VIRTUAL_ENV

SEED_ID="myth-campaign-first-through-s1"

# `set -u` is on, so a bare ${CLAUDE_PLUGIN_ROOT} does not degrade to empty --
# it aborts this script with "unbound variable" and exit 1, which is precisely
# the one thing the header above promises never happens. The variable is set
# when Claude Code runs the hook, and unset whenever anyone runs this file by
# hand to see what it says. Fall back to the directory this script lives in.
FT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=/dev/null
. "${FT}/scripts/engine.sh"

if [ -z "${GM_ROOT}" ]; then
  cat <<MSG
first-through: the mythras-gm engine is not installed, so this campaign cannot run.

  /plugin install mythras-gm@fourth-wall-gaming

First Through declares that dependency, so it should have arrived automatically --
if it did not, install it by hand, or set MYTHRAS_GM_ROOT to a checkout. Until
then: do not GM this campaign off the files in this package. They are a source
export, not a save file, and nothing you change in them reaches the game.
MSG
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "first-through: uv is not installed, so the engine CLI cannot run. Install it (https://docs.astral.sh/uv/) and start a new session."
  exit 0
fi

# The engine's own hook normally has the database up already. Calling init-db
# here too is cheap, idempotent, and removes any dependence on hook ordering.
if ! INIT=$(gm init-db 2>&1); then
  REMEDY=$(printf '%s' "$INIT" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("remedy") or d.get("error") or "")' 2>/dev/null || true)
  [ -z "$REMEDY" ] && REMEDY="$INIT"
  cat <<MSG
first-through: PREFLIGHT FAILED -- the game database is not usable, so there is
no save file and no dice tower.

  ${REMEDY}

Do not narrate, do not roll, and do not tell the user anything was saved. Offer
to run /mythras-gm:setup.
MSG
  exit 0
fi

if gm get-campaign --campaign "$SEED_ID" >/dev/null 2>&1; then
  STATE=$(gm get-campaign --campaign "$SEED_ID" 2>/dev/null | python3 -c '
import json,sys
try:
    c = json.load(sys.stdin).get("campaign") or {}
except Exception:
    print("?|?"); raise SystemExit
print(f"{c.get(\"myth-game-date\") or \"?\"}|{c.get(\"myth-session-number\")}")
' 2>/dev/null || echo "?|?")
  CLOCK="${STATE%%|*}"; SESSION="${STATE##*|}"
  if [ "${SESSION:-0}" = "0" ]; then
    echo "first-through: the campaign is imported and has not been started (clock ${CLOCK}). Run /first-through:start to pick an entry point and a character, and read TABLE-ADDENDUM.md before the first roll. MYTH_CAMPAIGN=${SEED_ID}"
  else
    echo "first-through: a game is in progress -- ${SEED_ID}, clock ${CLOCK}, session ${SESSION}. Resume it with /mythras-gm:play. Do NOT run /first-through:start; it is for a campaign that has not begun."
  fi
  exit 0
fi

echo "first-through: the campaign is installed but has not been imported into the database yet. Run /first-through:start -- it will import ${SEED_ID} from ${FT} and walk the player through choosing an entry point and a character. Do not GM from the files in this package; they are a source export, not the save."
exit 0
