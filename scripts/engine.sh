#!/usr/bin/env bash
#
# Find the mythras-gm engine. Sourced by First Through's hook and cited by its
# commands; sets GM_ROOT, GM_SKILL and GM_CLI, or returns 1.
#
# Copied VERBATIM from purewater-campaign-v2 apart from this comment. Do not
# rewrite it: the header below records two bugs already paid for in a real
# session, and both of them look like tidying.
#
# This exists because of a hard limit in the plugin system: ${CLAUDE_PLUGIN_ROOT}
# resolves to THIS plugin's directory and there is no variable for a sibling's.
# A campaign plugin therefore cannot name the engine it depends on, even though
# the dependency guarantees it is installed. So we look, in order of how much we
# trust the answer.
#
# Two rules learned the hard way, both of which this file once broke:
#
#   1. EVERY environment variable here is expanded with `:-`. This file is
#      sourced by a hook that runs `set -u`, so a bare ${CLAUDE_PLUGIN_ROOT}
#      does not fall back to empty -- it aborts the caller. That is exactly
#      what happened: the probe meant to be a last-resort convenience killed
#      the search, and the campaign reported the engine as missing when it was
#      installed and working.
#
#   2. The install-tree probe must not hard-code one layout. Claude Code keeps
#      plugins in at least three shapes, and the probe below was written for
#      only one of them -- so it silently matched nothing on a real install.

_engine_find() {
  local gm_rel="skills/mythras-gm/mythras_gm.py"

  # 1. Told explicitly. The documented escape hatch, and what CI uses.
  if [ -n "${MYTHRAS_GM_ROOT:-}" ] && [ -f "${MYTHRAS_GM_ROOT}/${gm_rel}" ]; then
    printf '%s' "${MYTHRAS_GM_ROOT}"; return 0
  fi

  # 2. The breadcrumb the engine's own init-db drops. Deterministic and
  #    version-agnostic -- but a plugin upgrade can leave it stale, so check.
  local pointer="${HOME:-}/.claude/mythras-gm/engine-root"
  if [ -n "${HOME:-}" ] && [ -f "$pointer" ]; then
    local p; p=$(head -1 "$pointer" 2>/dev/null)
    if [ -n "$p" ] && [ -f "${p}/${gm_rel}" ]; then
      printf '%s' "$p"; return 0
    fi
  fi

  local plugins="${HOME:-}/.claude/plugins"

  # 3. The installed-plugins record, when it names us. This is the only probe
  #    that asks Claude Code where it put the plugin rather than guessing, so
  #    it outranks any search. It does not cover every install mechanism --
  #    the synced tree is absent from it entirely -- hence step 4.
  if [ -f "${plugins}/installed_plugins.json" ] && command -v python3 >/dev/null 2>&1; then
    local recorded
    recorded=$(python3 -c '
import json,os,sys
try: d=json.load(open(sys.argv[1]))
except Exception: raise SystemExit
best=None
for key,entries in (d.get("plugins") or {}).items():
    if key.split("@")[0] != "mythras-gm": continue
    for e in entries or []:
        ip=e.get("installPath")
        if ip and os.path.isfile(os.path.join(ip,"skills","mythras-gm","mythras_gm.py")):
            k=e.get("lastUpdated") or e.get("installedAt") or ""
            if best is None or k>best[0]: best=(k,ip)
if best: print(best[1])
' "${plugins}/installed_plugins.json" 2>/dev/null)
    if [ -n "$recorded" ]; then printf '%s' "$recorded"; return 0; fi
  fi

  # 4. Search the trees Claude Code actually uses, most-trusted first:
  #
  #      cache/<marketplace>/<plugin>/<version>/skills/mythras-gm/...
  #      synced/<bucket>/<plugin>/skills/mythras-gm/...
  #      marketplaces/<marketplace>/skills/mythras-gm/...   (source: "./")
  #
  #    Note there is NO version segment in the last two. The previous pattern
  #    required one ('*/mythras-gm/*/skills/...') and only ever looked in
  #    cache/, which is why it found nothing here. Match on the skills path
  #    instead -- that suffix is the same in all three -- and take the highest
  #    version within whichever tree answers first.
  local root hit
  for root in cache synced marketplaces; do
    [ -d "${plugins}/${root}" ] || continue
    hit=$(find "${plugins}/${root}" -maxdepth 7 -path "*/${gm_rel}" 2>/dev/null \
          | sort -V | tail -1)
    if [ -n "$hit" ]; then
      printf '%s' "${hit%/${gm_rel}}"; return 0
    fi
  done

  # 5. Local development: --plugin-dir siblings, or a checkout next door.
  local cand
  local -a cands=()
  [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && cands+=("${CLAUDE_PLUGIN_ROOT}/../mythras-gm")
  cands+=("${CLAUDE_PROJECT_DIR:-.}/../mythras-gm" "${HOME:-.}/mythras-gm")
  for cand in "${cands[@]}"; do
    if [ -f "${cand}/${gm_rel}" ]; then
      ( cd "$cand" && pwd ); return 0
    fi
  done

  return 1
}

if GM_ROOT=$(_engine_find); then
  GM_SKILL="${GM_ROOT}/skills/mythras-gm"
  GM_CLI="${GM_SKILL}/mythras_gm.py"
  export GM_ROOT GM_SKILL GM_CLI
  gm() { uv run -q --project "$GM_SKILL" python "$GM_CLI" "$@"; }
else
  GM_ROOT=""; export GM_ROOT
fi
