"""Shared helpers for the content gates.

parse_frontmatter deliberately mirrors campaign_io._parse_md in the engine: it
JSON-decodes each value and falls back to the raw string. Validating anything
else would validate a document the importer never sees.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LAUNCH_YEARS_AGO = 975
YEARS_PER_LIGHT_YEAR = 20


def parse_frontmatter(text):
    """Return (meta, body) from a frontmatter markdown document."""
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            try:
                meta[k.strip()] = json.loads(v.strip())
            except (json.JSONDecodeError, ValueError):
                meta[k.strip()] = v.strip()
    return meta, body.strip()


def lore_files(category=None):
    pattern = f"{category}/*.md" if category else "*/*.md"
    return sorted((ROOT / "lore").glob(pattern))


def systems():
    return json.loads((ROOT / "data" / "systems.json").read_text())


def edges():
    return json.loads((ROOT / "data" / "edges.json").read_text())


def door_opened_years_ago(distance_ly):
    """Years before the present that a Sol-launched seedship's door opened.

    Negative means the ship is still in flight.
    """
    return LAUNCH_YEARS_AGO - round(distance_ly * YEARS_PER_LIGHT_YEAR)


def _xyz(s):
    ra = math.radians(s["ra_deg"])
    dec = math.radians(s["dec_deg"])
    d = s["distance_ly"]
    return (
        d * math.cos(dec) * math.cos(ra),
        d * math.cos(dec) * math.sin(ra),
        d * math.sin(dec),
    )


def separation_ly(a, b):
    """True 3-D separation between two systems, in light years."""
    return math.dist(_xyz(a), _xyz(b))


CONTENT_DIRS = ("lore", "guide", "beats", "agendas", "facts", "factions",
                "characters", "locations", "setting")

# Banned-vocabulary gates start scoped to the directories their own task
# rewrites, and Task 11 widens them to CONTENT_DIRS. A gate that fails on
# files its task does not own blocks that task on another task's work.
FIRST_PASS_DIRS = ("lore", "factions")


def content_files(dirs=CONTENT_DIRS):
    """Prose files under the named directories."""
    out = []
    for d in dirs:
        root = ROOT / d
        if root.is_dir():
            out.extend(sorted(root.rglob("*.md")))
    return out


def all_content_files():
    """Every prose file a rewrite could touch."""
    out = []
    for d in CONTENT_DIRS:
        root = ROOT / d
        if root.is_dir():
            out.extend(sorted(root.rglob("*.md")))
    return out


def lore_ids():
    """The frontmatter id of every lore file, which is the join key to the
    live TypeDB save. Losing one orphans that entry."""
    ids = set()
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        if "id" in meta:
            ids.add(meta["id"])
    return ids
