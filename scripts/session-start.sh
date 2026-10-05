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

# Do NOT call init-db here. It is not concurrency-safe -- run two together and
# whichever loses the race exits 1 with a TypeDB commit conflict -- and the
# engine's own SessionStart hook already calls it at this exact moment. When both
# hooks called it, one of them always lost, and the loser told the player their
# save file did not exist. Both halves of that were observed in a real session.
#
# So the engine owns bringing the database up, and this hook only waits for it to
# become readable. init-db appears once, as a last resort, for the case where the
# engine's hook did not run at all -- by which point nothing is racing us.
DB_READY=""
for _ in 1 2 3 4 5 6; do
  if gm list-campaigns >/dev/null 2>&1; then DB_READY="yes"; break; fi
  sleep 2
done

if [ -z "${DB_READY}" ]; then
  gm init-db >/dev/null 2>&1 || true
  PROBE=$(gm list-campaigns 2>&1) && DB_READY="yes"
fi

if [ -z "${DB_READY}" ]; then
  REMEDY=$(printf '%s' "${PROBE:-}" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print(d.get("remedy") or d.get("error") or "")
' 2>/dev/null || true)
  [ -z "$REMEDY" ] && REMEDY="${PROBE:-the database did not become readable}"
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
  # NB: no backslashes and no single quotes inside this snippet. It is wrapped
  # in a single-quoted shell string, and the version inherited from purewater
  # used \" escapes inside an f-string expression -- which is a SyntaxError, so
  # it silently fell through to "?|?" every time, took the in-progress branch,
  # and told the player NOT to run the start command. Found by running it.
  STATE=$(gm get-campaign --campaign "$SEED_ID" 2>/dev/null | python3 -c '
import json,sys
try:
    c = json.load(sys.stdin).get("campaign") or {}
except Exception:
    print("?|?"); raise SystemExit
date = c.get("myth-game-date") or "?"
session = c.get("myth-session-number")
print("%s|%s" % (date, session))
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
