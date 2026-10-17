#!/usr/bin/env bash
# Push every lore file's current body and summary into the live save.
#
#   GM=<engine dir> scripts/sync-lore.sh [--check] [campaign-id]
#
# A live campaign cannot be re-imported -- importing a package next to a live
# save forks it -- so each entry is pushed with update-lore, matched on the
# frontmatter id. If the file's id is not in the graph, the script looks in
# scripts/lore-id-map.tsv (file-id <TAB> graph-id). If it is in neither it
# FAILS LOUDLY and creates nothing: a silently created duplicate is an
# orphaned entry, and the whole project exists to prevent that.
#
# --check changes nothing: it reads each entry back out of the graph and
# reports every one whose content or summary differs from its file.
#
# --add-new is the one opt-in way to create: a file whose id is in neither
# place is added with add-lore (which cannot take a chosen id), and the
# generated graph id is appended to lore-id-map.tsv so it is matched next time.
# Run it once per genuinely new file, never as a habit.
set -euo pipefail
: "${GM:?set GM to the engine directory}"
MODE=sync
if [ "${1:-}" = "--check" ]; then MODE=check; shift; fi
if [ "${1:-}" = "--add-new" ]; then MODE=addnew; shift; fi
CAMPAIGN="${1:-myth-campaign-first-through-s1}"
cd "$(dirname "$0")/.."
export GM MODE CAMPAIGN
exec uv run -q --project "$GM" python - <<'PY'
import glob, json, os, re, subprocess, sys
GM, MODE, CAMPAIGN = os.environ["GM"], os.environ["MODE"], os.environ["CAMPAIGN"]
CLI = ["uv", "run", "-q", "--project", GM, "python", f"{GM}/mythras_gm.py"]

def run(*a):
    p = subprocess.run(CLI + list(a), capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: d = {"success": False, "error": (p.stdout + p.stderr).strip()}
    return d

amap = {}
if os.path.exists("scripts/lore-id-map.tsv"):
    for l in open("scripts/lore-id-map.tsv"):
        l = l.rstrip("\n")
        if l and not l.startswith("#"):
            a, b = l.split("\t"); amap[a] = b

ok = bad = 0
for f in sorted(glob.glob("lore/*/*.md")):
    t = open(f).read()
    m = re.match(r"^---\n(.*?)\n---\n?", t, re.S)
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if _: fm[k.strip()] = v.strip()
    fid = json.loads(fm["id"]); summary = json.loads(fm["summary"])
    body = t[m.end():].strip()
    gid = amap.get(fid, fid)
    g = run("get-lore", "--id", gid)
    if not g.get("success") and MODE == "addnew":
        a = run("add-lore", "--campaign", CAMPAIGN, "--title", json.loads(fm["title"]),
                "--category", json.loads(fm["category"]), "--summary", summary,
                "--narrative", body, "--visibility", json.loads(fm["visibility"]))
        if a.get("success"):
            with open("scripts/lore-id-map.tsv", "a") as mf: mf.write(f"{fid}\t{a['id']}\n")
            print(f"added  {a['id']}  {f}"); ok += 1
        else: print(f"FAIL  {fid}  {f}: add-lore: {a.get('error')}"); bad += 1
        continue
    if not g.get("success"):
        print(f"FAIL  {fid}  {f}: no such entry in the graph (unknown id; nothing created)"); bad += 1; continue
    cur = g["lore"]
    same = (cur.get("content") or "").strip() == body and (cur.get("description") or "") == summary
    if MODE == "check":
        print(("ok    " if same else "DIFFERS ") + f"{gid}  {f}")
        bad += 0 if same else 1; ok += same; continue
    if same:
        print(f"same   {gid}  {f}"); ok += 1; continue
    r = run("update-lore", "--id", gid, "--narrative", body, "--summary", summary)
    if r.get("success"): print(f"synced {gid}  {f}"); ok += 1
    else: print(f"FAIL  {gid}  {f}: {r.get('error')}"); bad += 1
print(f"{MODE}: {ok} ok, {bad} not")
sys.exit(1 if bad else 0)
PY
