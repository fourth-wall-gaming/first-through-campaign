# First Through v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a published mythras-gm campaign plugin — two one-sitting entry points and the Act 1-2 arc — that a 10-15 year old can install and play solo with Claude as GM.

**Architecture:** A pure content repo. No engine code, no schema changes. The star map lives in `data/*.json` as machine-checkable truth and in `lore/geography/*.md` as prose the GM reads; a pytest suite enforces the spec's hard content rules (cited astronomy, flagged invented life, the seedship arithmetic, the Causeway's causality) so they are gates rather than aspirations. Powers use the engine's existing `powers` field pointing at stock `magic/power-*` rule ids. Plugin wiring is modelled on `purewater-campaign-v2`, whose `scripts/engine.sh` is copied near-verbatim because it encodes bugs already paid for.

**Tech Stack:** Markdown with JSON-encoded YAML frontmatter, JSON data files, Bash hook scripts, pytest (`uv run --with pytest`). TypeDB 3.x via the mythras-gm CLI for the round-trip check only.

**Spec:** `docs/superpowers/specs/2026-10-05-first-through-design.md`

## Global Constraints

Copied verbatim from the spec. Every task's requirements implicitly include these.

- **Campaign id:** `myth-campaign-first-through-s1`. Plugin name `first-through`.
- **System:** `mythras` (Mythras Imperative), **not** `classic-fantasy`.
- **No engine changes.** No edits to `mythras_engine.py`, the rules layer, `spell_registry.json`, or the schema. This repo's only Python is under `tests/`.
- **Launch was 975 years ago. Transit time = distance in light years × 20.** Frontier at 48.75 ly.
- **Astronomy is real and fixed.** Every system, spectral type, planet, distance and oddity is real and current as of October 2026, with a source URL in frontmatter. Never write a figure from memory — fetch it.
- **Life is invented but constrained.** Only on genuinely unobserved surfaces, only consistent with that system's real temperature, insolation, tidal locking and chemistry, and always flagged `invented: "life"` with `system:` naming its host.
- **Incapacitation, not death — in both directions.** The PC is knocked out, captured or dragged clear, never killed; and the player is never put where killing is the expected solution. Mythras rules unchanged; the convention lives in `TABLE-ADDENDUM.md`.
- **No Douglas Hill intellectual property.** No Keill Randor, Glr, Moros, Veynaa, Overseers, Deathwing, or the Warlord.
- **Teleport is excluded from the permitted powers list** by design. Flight, Vaporous Form, Animation, Elemental Control and Energy Blast are also excluded.
- **No rules lecture.** Nothing to read before play.
- **Seed invariants:** `session_number: 0`, every beat `status: "pending"`, `journal/events.json` holds exactly one `gm-note`, and `current_scene` names no character.
- **v1 scope:** Acts 1-2 only. Acts 3-5 exist as `lore/gm-secret/` outline. The Quorum appears in v1 only as a name on a manifest and a countersignature — no face, no copies, no explanation.

## Review Focus

Five failure modes the spec implies that no feature task's own tests would otherwise exercise, most likely to bite a real user first. Each line's test is assigned to the task that owns the code.

1. **The engine is not installed, or the database is down, and the session-start hook takes the whole session down with it.** A player opening a terminal in an unrelated directory must still get a working session; the hook must report and exit 0, never non-zero, and never with an unbound-variable abort. → test in Task 13.
2. **A game is already in progress and `/first-through:start` resets it.** A start command that wipes somebody's campaign is worse than no start command. → test in Task 13.
3. **A pre-gen's power names a rule id that does not resolve in the rules graph, so powers come back empty on the sheet and the player silently has none.** → test in Task 7.
4. **`import-campaign --new-ids` remaps every id, orphaning cross-references.** `data/*.json` keys on system slugs and lore bodies use `[[Name]]` links, both of which must survive remapping; anything keyed on a literal `myth-` id inside prose will not. → test in Task 14.
5. **A resolve-attack drops the PC to zero and Claude narrates a death**, ending a child's first character on one roll. The non-lethal convention must be stated where the GM will actually read it and cited from the start command. → test in Task 13.

---

## File Structure

```
data/systems.json            29 real systems: distance, coords, type, source URLs
data/edges.json              the Causeway graph; Sirius carries exactly nine
campaign.yaml                manifest, seed state
README.md CLAUDE.md TABLE-ADDENDUM.md
.claude-plugin/plugin.json
commands/start.md            /first-through:start
hooks/hooks.json
scripts/engine.sh            copied from purewater-campaign-v2
scripts/session-start.sh     preflight; reports, never blocks
lore/player-briefing/        the sixty-second briefing
lore/cosmology/              anchors, the arithmetic, being unreachable
lore/geography/              prose per v1 system + the-causeway-map.md
lore/history/                the First Reach, the Threshold, GJ 1214
lore/technology/             kit, stunners, anchor hardware
lore/organizations/          the Threshold, the Tally
lore/character-creation/     the four pre-gens in player language
lore/entry-points/          "The Quiet Door", "Flare"
lore/gm-guide/ gm-secret/    Act 1-2 running notes; Acts 3-5 outline
templates/                   four pre-gens
characters/{pcs,npcs,creatures}/
locations/ factions/ encounters/
agendas/ beats/ facts/ knowledge.json journal/events.json
tests/content_rules.py       shared helpers; mirrors campaign_io._parse_md
tests/test_content_rules.py  the hard-rule gates
tests/test_seed.py           seed invariants
tests/test_powers.py         pre-gen legality
tests/test_plugin.py         hook/command safety
tests/test_roundtrip.py      import/export, skipped without a database
```

---

### Task 1: Validators and the manifest

The content gates come first so every later task has something to fail against.

**Files:**
- Create: `tests/content_rules.py`, `tests/test_content_rules.py`, `campaign.yaml`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/content_rules.py` exporting `ROOT: Path`, `LAUNCH_YEARS_AGO: int = 975`, `YEARS_PER_LIGHT_YEAR: int = 20`, `parse_frontmatter(text: str) -> tuple[dict, str]`, `lore_files(category: str | None = None) -> list[Path]`, `systems() -> dict[str, dict]`, `edges() -> list[dict]`, `door_opened_years_ago(distance_ly: float) -> int`, `separation_ly(a: dict, b: dict) -> float`. Every later task's tests import from here.

- [ ] **Step 1: Write the failing test**

`tests/test_content_rules.py`:

```python
"""The spec's hard content rules, as gates rather than aspirations."""
import json

import pytest

from content_rules import (
    LAUNCH_YEARS_AGO,
    ROOT,
    door_opened_years_ago,
    parse_frontmatter,
)


def test_frontmatter_parser_matches_the_importer():
    """campaign_io._parse_md JSON-decodes each value and falls back to the raw
    string. A parser that disagreed would validate something the engine never
    sees."""
    meta, body = parse_frontmatter(
        '---\n'
        'id: "myth-lore-0001"\n'
        'sources: ["https://example.org/a"]\n'
        'bare: not json\n'
        '---\n'
        'Body text.\n'
    )
    assert meta["id"] == "myth-lore-0001"
    assert meta["sources"] == ["https://example.org/a"]
    assert meta["bare"] == "not json"
    assert body == "Body text."


def test_the_arithmetic_is_the_spec_arithmetic():
    assert LAUNCH_YEARS_AGO == 975
    assert door_opened_years_ago(4.25) == 890   # Alpha Centauri
    assert door_opened_years_ago(8.71) == 801   # Sirius
    assert door_opened_years_ago(40.66) == 162  # TRAPPIST-1
    assert door_opened_years_ago(48.8) == -1    # LHS 1140: still inbound


def test_the_manifest_is_an_unplayed_seed():
    text = (ROOT / "campaign.yaml").read_text()
    assert 'id: "myth-campaign-first-through-s1"' in text
    assert "session_number: 0" in text
    assert 'format: "mythras-gm-campaign"' in text


def test_the_opening_scene_names_no_character_and_stops_the_gm():
    text = (ROOT / "campaign.yaml").read_text()
    scene = text.split('current_scene: "', 1)[1].split('"\n', 1)[0]
    for name in ("Calloway", "Tolk", "Ferren", "Hale", "Sarn"):
        assert name not in scene, f"the seed's opening scene names {name}"
    assert "/first-through:start" in scene
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd ~/first-through-campaign
uv run --with pytest pytest tests/ -q
```

Expected: FAIL — `ModuleNotFoundError: No module named 'content_rules'`.

- [ ] **Step 3: Write the helper module**

`tests/content_rules.py`:

```python
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
```

- [ ] **Step 4: Add pytest config so `content_rules` imports**

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["tests"]
testpaths = ["tests"]
```

- [ ] **Step 5: Write the manifest**

`campaign.yaml`. `time_index` is 0 because the clock starts at the player's first shift; `current_scene` must stop the GM dead.

```yaml
format: "mythras-gm-campaign"
format_version: "1.1"
id: "myth-campaign-first-through-s1"
name: "First Through"
description: "A Mythras Imperative campaign for a first-time roleplayer, set in the real stellar neighbourhood. Nine hundred and seventy-five years ago robotic seedships carried anchor pairs out at a twentieth of lightspeed; where one arrived, a door opened, and that is the only way between stars. Transit is instant, everything else obeys the speed of light, and the moment you step through nobody can reach you. You are a first-through: fifteen, newest the Threshold has taken in years. The old doors are failing faster than age explains, and the one everybody has waited nine centuries for opens in a year."
game_date: "s-1/first shift -- the day before the player's first posting"
current_scene: "NOTHING HAS BEGUN AND NO CHARACTER HAS BEEN CHOSEN. Run /first-through:start. Offer the two entry points in lore/entry-points/ -- 'The Quiet Door' (investigation and repair, one avoidable fight) and 'Flare' (a boarding action on a flare-star clock) -- and one of the four pre-gens in templates/. Do not narrate a scene until an entry point and a character are picked and set-scene has been called."
time_index: 0
session_number: 0
created_at: "2026-10-05T12:00:00"
exported_at: "2026-10-05T12:00:00"
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add tests/ pyproject.toml campaign.yaml
git commit -m "test: content-rule validators, and the seed manifest they gate"
```

---

### Task 2: The star map as data

**Files:**
- Create: `data/systems.json`
- Modify: `tests/test_content_rules.py` (append)
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `content_rules.systems`, `door_opened_years_ago`, `separation_ly`.
- Produces: `data/systems.json` — an object keyed by **slug** (e.g. `"gliese-887"`), each value `{"name": str, "distance_ly": float, "ra_deg": float, "dec_deg": float, "spectral": str, "components": [str], "planets": [str], "note": str, "opened_years_ago": int, "sources": [str]}`. Slugs are the join key used by `data/edges.json`, `locations/`, and every lore entry's `system:` field. **Never a `myth-` id**, because `--new-ids` remaps those (Review Focus 4).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_content_rules.py`:

```python
from content_rules import separation_ly, systems

V1_SYSTEMS = {
    "sol", "alpha-centauri", "barnards-star", "sirius", "gliese-65",
    "gliese-887", "gl-725", "61-cygni", "van-maanens-star",
    "trappist-1", "gj-1214", "lhs-1140",
}


def test_every_system_carries_a_real_source():
    for slug, s in systems().items():
        assert s.get("sources"), f"{slug} cites no source"
        for url in s["sources"]:
            assert url.startswith("https://"), f"{slug}: {url} is not a URL"


def test_door_dates_match_the_seedship_arithmetic():
    """The arithmetic in spec section 4 is the setting's load-bearing number.
    If a door date drifts from it the map stops being self-consistent."""
    for slug, s in systems().items():
        if slug == "sol":
            continue
        expected = door_opened_years_ago(s["distance_ly"])
        assert s["opened_years_ago"] == expected, (
            f"{slug}: distance {s['distance_ly']} ly implies {expected}, "
            f"file says {s['opened_years_ago']}"
        )


def test_lhs_1140_has_not_opened_yet():
    """It is the campaign spine precisely because it is still inbound."""
    assert systems()["lhs-1140"]["opened_years_ago"] < 0


def test_the_v1_systems_are_all_present():
    missing = V1_SYSTEMS - set(systems())
    assert not missing, f"v1 needs these systems: {sorted(missing)}"


def test_coordinates_reproduce_a_known_separation():
    """Sirius and Procyon are about 5.2 ly apart. If the coordinate convention
    is wrong (radians for degrees, or dec/ra swapped) this is the test that
    notices, and every edge length in Task 3 depends on it."""
    s = systems()
    gap = separation_ly(s["sirius"], s["procyon"])
    assert 4.5 < gap < 6.0, f"Sirius-Procyon came out {gap:.2f} ly"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: FAIL — `FileNotFoundError: data/systems.json`.

- [ ] **Step 3: Fetch the real numbers — do not write them from memory**

The Global Constraints forbid writing an astronomical figure from memory. For each
of the 29 systems in spec §5 plus `procyon`, fetch distance, RA, Dec and spectral
type, and record the URL you used.

```bash
# SIMBAD gives all four fields in one line per object.
curl -sG 'https://simbad.u-strasbg.fr/simbad/sim-script' \
  --data-urlencode 'script=format object form1 "%IDLIST(1)|%COO(d;A)|%COO(d;D)|%PLX(V)|%SP(S)"
output console=off script=off
query id Sirius
query id Procyon
query id "Gliese 887"
query id "Gliese 65"
query id "van Maanen 2"
query id "61 Cygni"
query id "Barnard star"
query id TRAPPIST-1
query id "LHS 1140"
query id "GJ 1214"
query id "Struve 2398"
query id "Alpha Centauri"'
```

Parallax in milliarcseconds converts to light years as `3261.564 / plx_mas`.
Cross-check each distance against the Wikipedia list of nearest stars, and put
**both** URLs in `sources`. Where the two disagree by more than 0.1 ly, prefer
SIMBAD and say so in `note`.

- [ ] **Step 4: Write the data file**

`data/systems.json`, keyed by slug. Worked specimen — every entry follows this
shape exactly, with figures from Step 3 rather than from this plan:

```json
{
  "sol": {
    "name": "Sol",
    "distance_ly": 0.0,
    "ra_deg": 0.0,
    "dec_deg": 0.0,
    "spectral": "G2V",
    "components": ["Sol"],
    "planets": ["eight"],
    "note": "The oldest launch site. The old country, sidelined.",
    "opened_years_ago": null,
    "sources": ["https://en.wikipedia.org/wiki/Sun"]
  },
  "gliese-887": {
    "name": "Gliese 887",
    "distance_ly": 10.72,
    "ra_deg": 346.4667,
    "dec_deg": -35.8533,
    "spectral": "M0.5V",
    "components": ["Gliese 887"],
    "planets": ["GJ 887 b", "GJ 887 c", "GJ 887 d", "GJ 887 e"],
    "note": "GJ 887 d is a habitable-zone super-Earth confirmed March 2026, around an unusually quiet red dwarf. The best real living world near home.",
    "opened_years_ago": 761,
    "sources": [
      "https://phys.org/news/2026-03-nearby-red-dwarf-star-hosts.html",
      "https://en.wikipedia.org/wiki/Gliese_887"
    ]
  }
}
```

`sol` is the one entry with `opened_years_ago: null` — it is the launch site, not
a destination, and the arithmetic test skips it.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: 9 passed. If `test_door_dates_match_the_seedship_arithmetic` fails,
the *data* is wrong, not the test — recompute `975 - round(distance_ly * 20)`.

- [ ] **Step 6: Commit**

```bash
git add data/systems.json tests/test_content_rules.py
git commit -m "feat: the star map as cited data, with the arithmetic enforced"
```

---

### Task 3: The Causeway graph

**Files:**
- Create: `data/edges.json`
- Modify: `tests/test_content_rules.py` (append)
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `content_rules.edges`, `systems`, `separation_ly`, `LAUNCH_YEARS_AGO`, `YEARS_PER_LIGHT_YEAR`.
- Produces: `data/edges.json` — a list of `{"a": slug, "b": slug, "opened_years_ago": int, "built_from": slug, "note": str}`. `built_from` must equal `a` or `b` and names the node whose yard launched the ship.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_content_rules.py`:

```python
from content_rules import YEARS_PER_LIGHT_YEAR, edges


def test_sirius_carries_exactly_nine_edges():
    """The Nine is named for its edge count. If this drifts the station is
    misnamed and the spec's first teaching image is wrong."""
    count = sum(1 for e in edges() if "sirius" in (e["a"], e["b"]))
    assert count == 9, f"Sirius carries {count} edges, not nine"


def test_every_edge_endpoint_is_a_known_system():
    known = set(systems())
    for e in edges():
        assert e["a"] in known, f"unknown endpoint {e['a']}"
        assert e["b"] in known, f"unknown endpoint {e['b']}"
        assert e["built_from"] in (e["a"], e["b"]), (
            f"{e['a']}-{e['b']}: built_from {e['built_from']} is not an endpoint"
        )


def test_no_edge_was_built_before_its_own_yard_existed():
    """A second-generation ship cannot leave a node before that node's door
    opened, and cannot arrive before it has flown. The arithmetic constrains
    the graph; the graph is not drawn freehand."""
    s = systems()
    for e in edges():
        origin = s[e["built_from"]]
        launched = (
            LAUNCH_YEARS_AGO if e["built_from"] == "sol"
            else origin["opened_years_ago"]
        )
        flight = separation_ly(s[e["a"]], s[e["b"]]) * YEARS_PER_LIGHT_YEAR
        earliest_arrival = launched - flight
        assert e["opened_years_ago"] <= launched, (
            f"{e['a']}-{e['b']} opened before {e['built_from']} had a door"
        )
        assert e["opened_years_ago"] <= earliest_arrival + 1, (
            f"{e['a']}-{e['b']} opened {e['opened_years_ago']} yr ago but the "
            f"ship could not arrive before {earliest_arrival:.0f} yr ago"
        )
        assert e["opened_years_ago"] > 0, f"{e['a']}-{e['b']} has not opened"


def test_the_graph_is_connected_from_sol():
    adj = {}
    for e in edges():
        adj.setdefault(e["a"], set()).add(e["b"])
        adj.setdefault(e["b"], set()).add(e["a"])
    seen, stack = {"sol"}, ["sol"]
    while stack:
        for n in adj.get(stack.pop(), ()):
            if n not in seen:
                seen.add(n)
                stack.append(n)
    unreachable = {k for k, v in systems().items() if v["opened_years_ago"]} - seen
    unreachable = {u for u in unreachable if u in adj}
    assert not unreachable, f"no route from Sol to {sorted(unreachable)}"


def test_lhs_1140_has_no_edge_yet():
    assert not [e for e in edges() if "lhs-1140" in (e["a"], e["b"])]
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `FileNotFoundError: data/edges.json`.

- [ ] **Step 3: Write the graph**

Build it so Sirius has exactly nine edges and every edge satisfies Step 1's
causality test. Work outward from Sol: Sol's own edges use
`built_from: "sol"` and `opened_years_ago` equal to the far system's
`opened_years_ago` from Task 2. Second-generation edges launch from an already-open
node, so their `opened_years_ago` is `origin.opened_years_ago − 20 × separation`,
rounded down, and must still be positive.

Specimen, two edges — one first-generation, one second:

```json
[
  {
    "a": "sol",
    "b": "sirius",
    "opened_years_ago": 801,
    "built_from": "sol",
    "note": "First generation, straight out of the launch yards."
  },
  {
    "a": "sirius",
    "b": "procyon",
    "opened_years_ago": 696,
    "built_from": "sirius",
    "note": "Launched from the Sirius yards once its own door was eighty years open; 5.2 ly at a twentieth of lightspeed."
  }
]
```

Nine is a constraint to *design to*, not to discover: pick Sirius's nine
neighbours from systems whose arithmetic permits the link, and record why each
exists in `note`.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add data/edges.json tests/test_content_rules.py
git commit -m "feat: the Causeway graph, with causality and the Nine enforced"
```

---

### Task 4: Lore — the briefing and the cosmology

The first words a player ever reads, and the physics they rest on.

**Files:**
- Create: `lore/player-briefing/first-through-the-sixty-second-briefing.md`, `lore/player-briefing/the-causeway-in-one-page.md`, `lore/cosmology/how-an-anchor-works.md`, `lore/cosmology/the-arithmetic-of-the-reach.md`, `lore/cosmology/why-nobody-can-reach-you.md`
- Modify: `tests/test_content_rules.py` (append)
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `content_rules.lore_files`, `parse_frontmatter`, `systems`.
- Produces: the lore frontmatter contract every later lore task follows:

```
id          "myth-lore-<12 hex>"      unique across the repo
title       str
category    str                       must equal the parent directory name
visibility  "player" | "gm"           gm-guide and gm-secret are always "gm"
summary     str                       one sentence
system      slug                      REQUIRED in geography and for invented life
sources     [url]                     REQUIRED in geography and cosmology
invented    "life"                    ONLY when the entry places an organism
created_at  "2026-10-05T12:00:00"
```

- [ ] **Step 1: Write the failing test**

Append to `tests/test_content_rules.py`:

```python
import re

from content_rules import lore_files

HEX12 = re.compile(r"^myth-lore-[0-9a-f]{12}$")
CITED_CATEGORIES = {"geography", "cosmology"}


def test_every_lore_entry_has_a_well_formed_unique_id():
    seen = {}
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        assert HEX12.match(str(meta.get("id", ""))), f"{p.name}: bad id"
        assert meta["id"] not in seen, f"{p.name} reuses the id of {seen.get(meta['id'])}"
        seen[meta["id"]] = p.name


def test_category_matches_the_directory():
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("category") == p.parent.name, (
            f"{p.name}: category {meta.get('category')!r} in {p.parent.name}/"
        )


def test_gm_only_directories_are_never_player_visible():
    """A player-visible gm-secret entry hands a child the ending."""
    for p in lore_files():
        if p.parent.name in {"gm-guide", "gm-secret"}:
            meta, _ = parse_frontmatter(p.read_text())
            assert meta.get("visibility") == "gm", f"{p.name} is not gm-only"


def test_astronomical_categories_cite_their_sources():
    for p in lore_files():
        if p.parent.name not in CITED_CATEGORIES:
            continue
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("sources"), f"{p.name} makes astronomical claims uncited"


def test_the_briefing_teaches_percentages_without_a_rules_lecture():
    """Spec section 8: nothing to read before play, and the mechanics wall does
    the teaching. The briefing must not grow into a rulebook."""
    p = ROOT / "lore/player-briefing/first-through-the-sixty-second-briefing.md"
    meta, body = parse_frontmatter(p.read_text())
    assert meta["visibility"] == "player"
    assert len(body.split()) < 400, "a sixty-second briefing is under 400 words"
    assert "Passion" in body, "Passions are the good bit; say so"
    for banned in ("d20", "Action Point", "difficulty grade"):
        assert banned not in body, f"the briefing lectures about {banned}"


def test_the_arithmetic_entry_states_the_load_bearing_number():
    p = ROOT / "lore/cosmology/the-arithmetic-of-the-reach.md"
    _, body = parse_frontmatter(p.read_text())
    assert "975" in body and "twenty" in body.lower()
    assert "48.7" in body or "48.8" in body, "the frontier distance must appear"
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `FileNotFoundError` on the briefing.

- [ ] **Step 3: Write the five entries**

Generate each `id` with `python3 -c "import uuid;print('myth-lore-'+uuid.uuid4().hex[:12])"`.

Worked specimen — `lore/cosmology/the-arithmetic-of-the-reach.md`:

```markdown
---
id: "myth-lore-3f81a0c4d2e7"
title: "The Arithmetic of the Reach"
category: "cosmology"
visibility: "player"
summary: "One light year per twenty years: the sum that explains why the frontier is where it is, and why it moves so slowly."
sources: ["https://en.wikipedia.org/wiki/List_of_nearest_stars_and_brown_dwarfs"]
created_at: "2026-10-05T12:00:00"
---

The seedships went out at a twentieth of the speed of light. That is a stupid,
grinding, patient speed, and it gives you the only sum anybody on the Causeway
needs:

**One light year takes twenty years.**

Sirius is eight and three-quarter light years from Sol, so the ship that carried
its anchor flew for a hundred and seventy-four years. It launched nine hundred
and seventy-five years ago. Subtract, and you have the age of the door you walk
through every morning: eight hundred and one years old.

Do it the other way and you get the frontier. Nine hundred and seventy-five
years of flying, at a light year every twenty, is **forty-eight and three-quarter
light years**. That is the edge of everything. Not because anybody decided — the
ships are simply still out there, and that is as far as they have got.

Which means the frontier moves at **one light year every twenty years**, and
nothing anyone does will hurry it. A first-through who serves forty years will
see it advance by two light years. You can hold the whole map in your head and
still not reach the end of it in a life.
```

The other four, each a single idea:

- **`first-through-the-sixty-second-briefing.md`** (`visibility: "player"`, under 400 words). Adapted from the engine's `NEW-TO-MYTHRAS.md` for science fiction and a younger reader: you do not need the rules, skills are percentages you roll under, fights are short and frightening and usually avoidable, Passions are the good bit. No `d20`, no "Action Point", no "difficulty grade" — the test checks.
- **`the-causeway-in-one-page.md`** (`player`). The graph, not the volume. One door, one step, and nothing faster than a courier.
- **`how-an-anchor-works.md`** (`player`, cited). A paired device, one half carried out the slow way; transit instant between the pair and nowhere else; an anchor whose far side dies is a door onto nothing.
- **`why-nobody-can-reach-you.md`** (`player`, cited). Radio obeys lightspeed, so the far side of a door is out of contact by definition. Your handler briefs you and then you are gone. This is the entry a GM points at when a player asks "can I call for help?"

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: 20 passed.

- [ ] **Step 5: Commit**

```bash
git add lore/player-briefing lore/cosmology tests/test_content_rules.py
git commit -m "feat(lore): the sixty-second briefing and the cosmology under it"
```

---

### Task 5: Lore — geography for the v1 systems

**Files:**
- Create: `lore/geography/the-causeway-map.md`, plus one entry per v1 system: `sirius-the-nine.md`, `gliese-887.md`, `gliese-65-the-flare-twins.md`, `van-maanens-star.md`, `61-cygni.md`, `lhs-1140.md`, `barnards-star.md`, `trappist-1.md`, `gj-1214.md`
- Modify: `tests/test_content_rules.py` (append)
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: the Task 4 frontmatter contract; `data/systems.json` slugs.
- Produces: `lore/geography/*.md` each carrying `system:` equal to a slug in `data/systems.json`.

- [ ] **Step 1: Write the failing test**

```python
def test_geography_entries_name_a_system_in_the_data():
    known = set(systems())
    found = set()
    for p in lore_files("geography"):
        meta, _ = parse_frontmatter(p.read_text())
        if p.name == "the-causeway-map.md":
            continue
        slug = meta.get("system")
        assert slug in known, f"{p.name}: system {slug!r} is not in data/systems.json"
        found.add(slug)
    assert V1_SYSTEMS - {"sol", "alpha-centauri", "gl-725"} <= found, (
        f"v1 systems with no prose: {sorted(V1_SYSTEMS - found)}"
    )


def test_geography_prose_agrees_with_the_data_on_distance():
    """Prose and data drifting apart is how a campaign starts lying to a kid
    who looked it up."""
    for p in lore_files("geography"):
        meta, body = parse_frontmatter(p.read_text())
        slug = meta.get("system")
        if not slug:
            continue
        ly = systems()[slug]["distance_ly"]
        assert f"{ly:.1f}" in body or f"{ly:.2f}" in body or str(round(ly)) in body, (
            f"{p.name} never states its own distance ({ly} ly)"
        )
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — the v1 systems have no prose.

- [ ] **Step 3: Write the entries**

Every entry: `category: "geography"`, `visibility: "player"`, a `system:` slug, and
`sources` carrying the same URLs as the data file. The body states the real
distance, the real star, the real planets — then exactly one invented thing:
what people built there.

Worked specimen — `lore/geography/van-maanens-star.md`:

```markdown
---
id: "myth-lore-9c4b27e1aa50"
title: "van Maanen's Star"
category: "geography"
visibility: "player"
system: "van-maanens-star"
summary: "The nearest solitary white dwarf, 14.1 light years out, slowly eating the wreckage of its own planets. Nothing lives here and the Threshold keeps an office anyway."
sources: ["https://en.wikipedia.org/wiki/Van_Maanen_2", "https://science.nasa.gov/universe/exoplanets/overlooked-treasure-the-first-evidence-of-exoplanets/"]
created_at: "2026-10-05T12:00:00"
---

Fourteen light years out, and the door is six hundred and ninety-four years old.

van Maanen's Star is the nearest white dwarf standing on its own — a dead sun
the size of a world, still hot, with nothing orbiting it that anyone has found.
It is also a crime scene. Run a spectrum and the star's own light tells you
there is iron in its atmosphere, and calcium, and magnesium, which have no
business being there. Metals sink in a white dwarf. Anything you can still see
arrived recently.

It had planets. It pulled them in and tore them apart, and it is still
swallowing the pieces.

**What people built here:** one station, bolted to a rock, with an office the
Threshold keeps staffed by two people who did not ask to be here. There is no
cargo and no colony. The reason the office exists is that the anchor logs are
kept here, and the reason they are kept *here* is that nobody visits.
```

The remaining eight, each one real fact plus one built thing:

| File | The real thing | The built thing |
|---|---|---|
| `sirius-the-nine.md` | A1V glare and the hottest nearby white dwarf; no planets | **The Nine** — Threshold home station, nine doors |
| `gliese-887.md` | Quiet M0.5V, four planets, GJ 887 d habitable-zone super-Earth (March 2026) | The farm settlement behind a dying anchor — entry point A |
| `gliese-65-the-flare-twins.md` | BL Ceti and UV Ceti, the archetypal flare stars | A refinery whose shelter is behind the barricade — entry point B |
| `61-cygni.md` | First star whose distance was ever measured; K5V + K7V | Where the Threshold trains first-throughs |
| `lhs-1140.md` | Best known rocky habitable-zone planet; JWST water-world candidate | Nothing. There is nothing there yet. That is the point. |
| `barnards-star.md` | Nearest single star; four scorched sub-Earths; largest proper motion | Heavy industry on a famous disappointment |
| `trappist-1.md` | Seven tidally-locked planets, three in the habitable zone | The frontier jewel, opened 162 years ago |
| `gj-1214.md` | The hazy water-world sub-Neptune | The most recent door, 25 years old, and a cautionary tale |
| `the-causeway-map.md` | — | Reads `data/edges.json` back as prose; states that Sirius carries nine |

- [ ] **Step 4: Run the tests to verify they pass**

Expected: 22 passed.

- [ ] **Step 5: Commit**

```bash
git add lore/geography tests/test_content_rules.py
git commit -m "feat(lore): geography for the v1 systems, prose checked against the data"
```

---

### Task 6: Lore — the Threshold, the Tally, the kit, the history

**Files:**
- Create: `lore/organizations/the-threshold.md`, `lore/organizations/the-tally.md`, `lore/technology/a-first-throughs-kit.md`, `lore/technology/stunners-and-restraints.md`, `lore/technology/anchor-hardware.md`, `lore/history/the-first-reach.md`, `lore/history/the-founding-of-the-threshold.md`
- Modify: `tests/test_content_rules.py` (append)

**Interfaces:**
- Consumes: the Task 4 frontmatter contract.
- Produces: the in-fiction vocabulary every later task uses verbatim — **first-through**, **the Nine**, **anchor**, **step through**, **the Threshold**, **the Tally**, **tallyman**, **charge** (Power Points in fiction).

- [ ] **Step 1: Write the failing test**

```python
NON_LETHAL_WEAPON_WORDS = ("stunner", "shock baton", "restraint", "net", "gel")


def test_the_tally_wants_prisoners_not_corpses():
    """Spec section 12: the antagonist's own motive supplies the non-lethal rule.
    If this entry ever loses that, the convention becomes a house rule again."""
    p = ROOT / "lore/organizations/the-tally.md"
    _, body = parse_frontmatter(p.read_text())
    assert "manifest" in body.lower()
    assert any(w in body.lower() for w in NON_LETHAL_WEAPON_WORDS)


def test_the_kit_entry_explains_charge_without_naming_power_points():
    """The mechanics wall: prose never contains rules vocabulary."""
    p = ROOT / "lore/technology/a-first-throughs-kit.md"
    _, body = parse_frontmatter(p.read_text())
    assert "charge" in body.lower()
    for banned in ("Power Point", "POW", "Boost", "Limit"):
        assert banned not in body, f"the kit entry leaks the rules word {banned!r}"
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `FileNotFoundError` on `the-tally.md`.

- [ ] **Step 3: Write the seven entries**

- **`the-threshold.md`** (`player`). What a first-through is and does: the first step through a new anchor, and the call when an old one goes wrong. Trains at 61 Cygni. Home at the Nine. Includes the one sentence that frames every mission — *once you step through, you are the whole response.*
- **`the-tally.md`** (`player`). Whoever holds the station holds the door, so the Causeway is governed by a tollkeeper rather than a navy. Tallymen, pressure armour, shock batons, manifests. **They want everyone alive, because a body is not a line on a manifest.** No mention of the Quorum.
- **`a-first-throughs-kit.md`** (`player`). The pressure-skin, the suit, the sensor package, and the **charge** that runs them — which is also the operative's own conditioning and breath. Says plainly that the kit can be taken off you. Never uses a rules word.
- **`stunners-and-restraints.md`** (`player`). Why nobody on the Causeway carries a killing weapon as a first choice: a hull is thin, a station is a closed volume, and a corpse is paperwork. The in-fiction root of the non-lethal rule.
- **`anchor-hardware.md`** (`player`, cited). What an anchor physically is, what failing looks like, and what a first-through can and cannot repair.
- **`the-first-reach.md`** (`player`, cited). The expansion that launched the ships 975 years ago and then stopped. Deliberately thin on *why* it stopped — that is Act 5.
- **`the-founding-of-the-threshold.md`** (`player`). Why a service exists to walk through doors first, and the accident that created it.

- [ ] **Step 4: Run the tests to verify they pass**

Expected: 24 passed.

- [ ] **Step 5: Commit**

```bash
git add lore/organizations lore/technology lore/history tests/test_content_rules.py
git commit -m "feat(lore): the Threshold, the Tally, the kit and the First Reach"
```

---

### Task 7: The four pre-gens

Owns **Review Focus 3** — a power naming an unresolvable rule id.

**Files:**
- Create: `templates/the-runner.json`, `templates/the-tinker.json`, `templates/the-talker.json`, `templates/the-fieldhand.json`, `lore/character-creation/choosing-a-first-through.md`
- Create: `tests/test_powers.py`
- Test: `tests/test_powers.py`

**Interfaces:**
- Consumes: `content_rules.ROOT`.
- Produces: four template JSON files in the engine's template shape — `{"id": "myth-tmpl-<12 hex>", "name", "description", "narrative", "characteristics", "attributes", "skills", "combat_styles", "passions", "powers", "equipment", "extras"}`. `powers` is a list of `{"name", "rule", "boosts": [], "limits": []}` exactly as `characters/pcs/magda.json` does in `purewater-campaign-v2`.

- [ ] **Step 1: Write the failing test**

`tests/test_powers.py`:

```python
"""The pre-gens must be engine-legal and must obey the spec's power whitelist."""
import json
import re
import subprocess

import pytest

from content_rules import ROOT

TEMPLATES = sorted((ROOT / "templates").glob("*.json"))

PERMITTED = {
    "Life Support", "Inherent Armor", "Savant", "Heightened Sense",
    "Enhanced Reactions", "Durability", "Enhanced Strength",
    "Enhanced Speed", "Combat Expert", "Lucky",
}
FORBIDDEN = {
    "Teleport", "Flight", "Vaporous Form", "Animation",
    "Elemental Control", "Energy Blast",
}


def test_there_are_four_pregens():
    assert len(TEMPLATES) == 4, [p.name for p in TEMPLATES]


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.stem)
def test_template_is_engine_shaped(path):
    t = json.loads(path.read_text())
    assert re.match(r"^myth-tmpl-[0-9a-f]{12}$", t["id"])
    for key in ("name", "description", "characteristics", "attributes",
                "skills", "passions", "powers"):
        assert key in t, f"{path.name} has no {key}"
    for stat in ("STR", "CON", "SIZ", "DEX", "INT", "POW", "CHA"):
        assert isinstance(t["characteristics"][stat], int)
    assert t["passions"], "a pre-gen with no Passions is a stat block"


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.stem)
def test_powers_are_whitelisted_and_teleport_is_absent(path):
    """Spec section 7: personal teleportation being impossible is why the
    Causeway matters. A pre-gen that could teleport would unmake the setting."""
    for p in json.loads(path.read_text())["powers"]:
        assert p["name"] in PERMITTED, f"{path.name}: {p['name']} is not permitted"
        assert p["name"] not in FORBIDDEN


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.stem)
def test_power_count_matches_the_build_table(path):
    """core powers = POW + INT on the tech/training branch, per the table:
    <=12 -> 1, 13-20 -> 2, 21-30 -> 3, 31-40 -> 4, 40+ -> 5; and each Limit
    taken beyond the first buys a core power, the first buys a Boost."""
    t = json.loads(path.read_text())
    pool = t["characteristics"]["POW"] + t["characteristics"]["INT"]
    allowed = 1 if pool <= 12 else 2 if pool <= 20 else 3 if pool <= 30 else 4 if pool <= 40 else 5
    limits = {l for p in t["powers"] for l in p["limits"]}
    if len(limits) >= 2:
        allowed += 1
    assert len(t["powers"]) <= allowed, (
        f"{path.name}: POW+INT={pool} allows {allowed} core powers, "
        f"file has {len(t['powers'])}"
    )


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.stem)
def test_every_power_rule_id_resolves_in_the_rules_graph(path):
    """Review Focus 3. A typo here does not raise -- it yields a sheet with no
    powers at all, which a player would discover mid-mission."""
    engine = subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    for p in json.loads(path.read_text())["powers"]:
        out = subprocess.run(
            ["uv", "run", "-q", "--project", engine, "python",
             f"{engine}/mythras_gm.py", "get-rule", "--id", p["rule"]],
            capture_output=True, text=True,
        )
        assert json.loads(out.stdout).get("success"), (
            f"{path.name}: power {p['name']} cites rule {p['rule']}, "
            "which does not resolve"
        )
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run --with pytest pytest tests/test_powers.py -q
```

Expected: FAIL — `test_there_are_four_pregens` reports `[]`.

- [ ] **Step 3: Write the four templates**

Characteristics for a trained fifteen-year-old: roll-equivalent but assigned, POW
10-12 and INT 12-14, so POW+INT lands on the 21-30 row and each gets **three core
powers**. Every one takes `External Power Source` as a Limit — the suit can be
taken off you — which is one Limit, buying a Boost.

Rule ids, verified present at `rules/magic/power-*.md` and therefore available to
a `mythras` campaign:

| Power | Rule id |
|---|---|
| Life Support | `magic/power-life-support` |
| Inherent Armor | `magic/power-inherent-armor` |
| Savant | `magic/power-savant` |
| Heightened Sense | `magic/power-heightened-sense` |
| Enhanced Reactions | `magic/power-enhanced-reactions` |
| Durability | `magic/power-durability` |
| Combat Expert | `magic/power-combat-expert` |
| Enhanced Strength | `magic/power-enhanced-strength` |

Worked specimen — `templates/the-tinker.json` (the other three follow the same
shape with their own skill emphasis from spec §6):

```json
{
  "id": "myth-tmpl-71ca03e9b4d8",
  "name": "The Tinker",
  "description": "A first-through who opens things. Fifteen, two years in the Threshold's yards at 61 Cygni before anyone let them near a door, and the only one in their intake who can tell a failing anchor from a sulking one.",
  "narrative": "You were taken on because you fixed a pressure door nobody had asked you to\ntouch, and then explained what had been wrong with it. The Threshold has a word\nfor people who do that and the word is useful.\n\nYour suit is older than you are and you have improved it in four ways that are\nnot strictly permitted.",
  "characteristics": {
    "STR": 10, "CON": 12, "SIZ": 10, "DEX": 14, "INT": 14, "POW": 11, "CHA": 10
  },
  "attributes": {
    "action_points": 3,
    "damage_modifier": "+0",
    "experience_modifier": 1,
    "healing_rate": 2,
    "initiative_bonus": 14,
    "luck_points": 3,
    "magic_points": 11,
    "movement": "6"
  },
  "skills": {
    "Athletics": 45, "Brawn": 25, "Endurance": 54, "Evade": 58,
    "Willpower": 52, "Conceal": 40, "Deceit": 30, "First Aid": 42,
    "Influence": 35, "Insight": 44, "Locale": 40, "Native Tongue": 54,
    "Perception": 58, "Sleight": 48, "Stealth": 45, "Unarmed": 40,
    "Mechanisms": 72, "Engineering": 66, "Lore (Anchors)": 68,
    "Craft (Pressure Fitting)": 60, "Science (Physics)": 50
  },
  "combat_styles": {"Threshold Drill (stunner, baton, unarmed)": 45},
  "passions": {
    "It was working when I left it": 65,
    "Loyalty (Calloway)": 55,
    "Nothing is sealed to me": 50
  },
  "powers": [
    {
      "name": "Life Support",
      "rule": "magic/power-life-support",
      "boosts": ["Hard vacuum and hard radiation, both (2 PP)"],
      "limits": ["External Power Source -- the suit, and it can be taken"]
    },
    {
      "name": "Savant",
      "rule": "magic/power-savant",
      "boosts": [],
      "limits": ["External Power Source -- the toolroll, and it can be taken"]
    },
    {
      "name": "Heightened Sense",
      "rule": "magic/power-heightened-sense",
      "boosts": [],
      "limits": ["External Power Source -- the sensor hood, and it can be taken"]
    }
  ],
  "equipment": [
    "Threshold pressure suit, patched (AP 2 all locations)",
    "Stunner, two charges spare",
    "Toolroll",
    "Sensor hood",
    "Restraint loops, four"
  ],
  "extras": {
    "age": 15,
    "pronouns": "they/them",
    "game_system": "mythras",
    "character_type": "first-through",
    "power_branch": "tech/training (INT)",
    "trained_at": "61-cygni",
    "charge": "Power Points = POW 11; recovers 1 per minute of rest"
  }
}
```

- [ ] **Step 4: Write `lore/character-creation/choosing-a-first-through.md`**

`visibility: "player"`. The four in a player's language — *climbs, fixes, talks,
knows bodies* — one paragraph each, no numbers, and the single most important
sentence: **all four can finish either mission, and none of them has to hurt
anybody.**

- [ ] **Step 5: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: all passed; the rule-resolution test skips if no engine is installed.

- [ ] **Step 6: Commit**

```bash
git add templates/ lore/character-creation/ tests/test_powers.py
git commit -m "feat: four pre-gens, powers whitelisted and rule ids verified"
```

---

### Task 8: The cast

**Files:**
- Create: `characters/npcs/calloway.json`, `characters/npcs/tolk.json`, `characters/npcs/ferren.json`, `characters/npcs/director-hale.json`, `characters/npcs/tallyman-captain-brace.json`, `characters/npcs/sep-anwar.json`, `characters/npcs/meriel-koll.json`
- Create: `characters/creatures/tallyman.json`, `characters/creatures/bell-sixlimb.json`
- Create: `lore/gm-guide/playing-tolk.md`
- Modify: `tests/test_content_rules.py` (append)

**Interfaces:**
- Consumes: the template shape from Task 7.
- Produces: character JSON in the engine's character shape — the Task 7 keys plus `"type": "npc"`, `"status": "active"`, and `actor_notes`. `extras.pronouns` is set on every named character; unstated means `they/them`.

- [ ] **Step 1: Write the failing test**

```python
import json as _json

NAMED_CAST = {
    "calloway", "tolk", "ferren", "director-hale",
    "tallyman-captain-brace", "sep-anwar", "meriel-koll",
}


def test_the_named_cast_is_present():
    have = {p.stem for p in (ROOT / "characters" / "npcs").glob("*.json")}
    assert NAMED_CAST <= have, f"missing: {sorted(NAMED_CAST - have)}"


def test_every_character_declares_pronouns():
    """Guessing a character's pronouns from their name misgenders them in a way
    the neutral default never does."""
    for p in (ROOT / "characters").rglob("*.json"):
        c = _json.loads(p.read_text())
        assert (c.get("extras") or {}).get("pronouns"), f"{p.name} declares none"


def test_no_hill_proper_nouns_anywhere_in_the_repo():
    """Global Constraints: we inherit the shape, never the names."""
    banned = ("Keill", "Randor", "Glr", "Moros", "Veynaa",
              "Overseer", "Deathwing", "Galactic Warlord")
    for p in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.json")):
        if ".git" in p.parts or "docs" in p.parts:
            continue
        text = p.read_text()
        for word in banned:
            assert word not in text, f"{p.relative_to(ROOT)} contains {word!r}"


def test_v1_never_shows_the_quorum_his_face():
    """Spec section 11: v1 ships only the bottom rung of the reveal ladder."""
    for p in (ROOT / "characters").rglob("*.json"):
        c = _json.loads(p.read_text())
        assert c["name"] != "Sarn", "Sarn has no sheet in v1"
    player_visible = [
        p for p in lore_files()
        if parse_frontmatter(p.read_text())[0].get("visibility") == "player"
    ]
    for p in player_visible:
        body = p.read_text()
        assert "pattern transfer" not in body.lower(), f"{p.name} leaks Act 3"
        assert "copies of himself" not in body.lower()
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `missing: ['calloway', 'director-hale', ...]`.

- [ ] **Step 3: Write the cast**

- **Calloway** — runs the desk at the Nine. Former first-through; transit has stopped being survivable for them. `pronouns: "they/them"`. High Insight, Influence, Lore (Anchors); no combat emphasis. `actor_notes`: *warm, brisk, and never pretends the job is safe. They will tell a fifteen-year-old the truth and then send them anyway, and they hate it.*
- **Tolk** — cat-sized, six-limbed, from Bell. `type: "npc"`, real skills (Perception, Stealth, Athletics high; Native Tongue present because Tolk **learned** to speak). `extras.invented_life: true`, `extras.home_system: "gliese-887"` or whichever anchor world Bell is placed at in `data/systems.json` — and that placement must satisfy the Task 5 constraint that invented life sits on an unobserved surface consistent with its real system.
- **Ferren** — nineteen, another first-through, better than the player and visibly so. Combat Style and Athletics above the pre-gens. `actor_notes`: *already there when you arrive, pleasant about it, and takes orders from a voice he has never questioned.*
- **Director Hale** — the Threshold's directorate. No combat. `actor_notes`: *not evil; culpable. Has known for forty years and has reasons that sound good right up to the moment you say them aloud.*
- **Tallyman Captain Brace** — the v1 face of the Tally, and the one who knows things he should not. Carries a shock baton and restraints, **never a lethal weapon**.
- **Sep Anwar** and **Meriel Koll** — the two Threshold staff at van Maanen's Star, where the anchor logs are kept.
- **`creatures/tallyman.json`** — the generic mook. Pressure armour (AP 4), shock baton, restraint loops. Spawned by name in both entry points.
- **`creatures/bell-sixlimb.json`** — Tolk's species as a creature entry, for the GM who needs a second one.
- **`lore/gm-guide/playing-tolk.md`** (`visibility: "gm"`) — the onboarding mechanism written down: Tolk is physically present in every scene, so Tolk may notice things aloud and ask *"well? what are we doing?"*. That scaffolds a stuck beginner without an option menu and without writing the player's interior. Cites `TABLE.md` §5 and §6. States plainly: **when the player goes quiet, Tolk speaks — the GM does not offer a list.**

- [ ] **Step 4: Run the tests to verify they pass**

Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add characters/ lore/gm-guide/playing-tolk.md tests/test_content_rules.py
git commit -m "feat: the cast, and Tolk written down as the onboarding mechanism"
```

---

### Task 9: Locations and factions

**Files:**
- Create: `locations/the-nine.md`, `locations/the-nine-ready-room.md`, `locations/gj-887-d-landing.md`, `locations/the-farm-at-coldwater.md`, `locations/gliese-65-refinery.md`, `locations/the-barricade.md`, `locations/van-maanens-office.md`, `locations/61-cygni-yards.md`
- Create: `factions/the-threshold.md`, `factions/the-tally.md`, `factions/the-coldwater-holding.md`
- Modify: `tests/test_content_rules.py` (append)

**Interfaces:**
- Consumes: `data/systems.json` slugs.
- Produces: location markdown with frontmatter `{id: "myth-loc-<12 hex>", name, type, summary, system: slug, created_at}`; faction markdown with `{id: "myth-fac-<12 hex>", name, summary, created_at}`.

- [ ] **Step 1: Write the failing test**

```python
def test_locations_sit_in_a_known_system():
    known = set(systems())
    paths = sorted((ROOT / "locations").glob("*.md"))
    assert paths, "no locations"
    for p in paths:
        meta, _ = parse_frontmatter(p.read_text())
        assert re.match(r"^myth-loc-[0-9a-f]{12}$", str(meta.get("id", "")))
        assert meta.get("system") in known, f"{p.name}: system {meta.get('system')!r}"


def test_both_entry_points_have_somewhere_to_happen():
    systems_used = {
        parse_frontmatter(p.read_text())[0].get("system")
        for p in (ROOT / "locations").glob("*.md")
    }
    assert "gliese-887" in systems_used, "entry point A has no location"
    assert "gliese-65" in systems_used, "entry point B has no location"
    assert "sirius" in systems_used, "the Nine has no location"
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — "no locations".

- [ ] **Step 3: Write them**

Each location body follows `TABLE.md`'s rule that a GM runs `brief --id
<location>` before narrating a place: concrete, sensory, and **dense with
physical affordances** — things to touch, open, climb and talk to — because spec
§8 makes that the second onboarding device. Two or three named, reachable
details per room, minimum.

Worked specimen — `locations/the-barricade.md`:

```markdown
---
id: "myth-loc-4ab19c70e2f1"
name: "The Barricade"
type: "chokepoint"
summary: "Six metres of corridor between the Gliese 65 refinery's living deck and its anchor, stacked shoulder-high with cargo crates, ore drums and one welded bunk frame. The only way out of the system is on the far side of it."
system: "gliese-65"
created_at: "2026-10-05T12:00:00"
---

The corridor runs six metres and then stops being a corridor. Someone has
emptied the loading bay into it: ore drums on their sides, cargo crates stacked
to shoulder height and cross-braced, and a bunk frame welded across the top of
the heap at an angle, so the whole thing leans toward you like it is listening.

Three things are true about it and all three are reachable. The stack is
**cross-braced with cargo strap**, which a knife goes through. There is a
**maintenance crawl** behind the left-hand panel, forty centimetres square,
which an adult cannot use and a fifteen-year-old can. And the **drums are
full** — whoever built this was in a hurry and stacked mass they cannot shift
quickly, so the barricade cannot be opened fast from either side, including by
the people behind it.

Above, the deck lighting runs on the refinery's own bus. It browns out every
ninety seconds or so, and it has been doing that since the star started getting
restless.
```

The three factions carry a one-paragraph summary and their standing toward the
player: the Threshold employs you, the Tally outranks you everywhere it counts,
and the Coldwater Holding behind the GJ 887 d anchor are four thousand farmers
who have no idea how close they are to being unreachable.

- [ ] **Step 4: Run the tests to verify they pass**

Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add locations/ factions/ tests/test_content_rules.py
git commit -m "feat: locations dense with affordances, and the three factions"
```

---

### Task 10: Entry point A — "The Quiet Door"

**Files:**
- Create: `lore/entry-points/the-quiet-door.md`, `encounters/coldwater-anchor-fault.json`, `lore/gm-guide/running-the-quiet-door.md`
- Modify: `tests/test_content_rules.py` (append)

**Interfaces:**
- Consumes: `templates/*.json` names; `locations/gj-887-d-landing.md`, `locations/the-farm-at-coldwater.md`; `characters/npcs/calloway.json`, `tolk.json`.
- Produces: `lore/entry-points/the-quiet-door.md` with frontmatter key `entry_point: "the-quiet-door"`, read by `commands/start.md`.

- [ ] **Step 1: Write the failing test**

```python
ENTRY_POINTS = {"the-quiet-door", "flare"}


def test_both_entry_points_exist_and_declare_themselves():
    found = {}
    for p in lore_files("entry-points"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("entry_point"), f"{p.name} declares no entry_point key"
        found[meta["entry_point"]] = p
    assert set(found) == ENTRY_POINTS, f"found {sorted(found)}"


def test_each_entry_point_names_all_four_pregens_as_viable():
    """Spec section 6: every scenario must be solvable by all four. An entry
    point that only lists two has quietly cut half the pre-gens."""
    names = {_json.loads(p.read_text())["name"]
             for p in (ROOT / "templates").glob("*.json")}
    for p in lore_files("entry-points"):
        body = p.read_text()
        for n in names:
            assert n in body, f"{p.name} never says how {n} solves it"


def test_the_quiet_door_keeps_its_one_fight_optional():
    p = ROOT / "lore/entry-points/the-quiet-door.md"
    _, body = parse_frontmatter(p.read_text())
    assert "avoid" in body.lower(), "the avoidable fight must be marked avoidable"
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `found []`.

- [ ] **Step 3: Write the scenario**

`lore/entry-games/` is not a directory — the file is
`lore/entry-points/the-quiet-door.md`, `visibility: "gm"`, with a short
player-facing hook quoted inside it for Claude to read aloud.

The shape, one sitting:

1. **The Nine, ready room.** Calloway briefs. The anchor serving the Coldwater Holding at GJ 887 d has gone intermittent: it passed a scheduled test four days ago and failed two since. Four thousand people are on the far side. **The guaranteed early success** (spec §8, device 4) lives here: a kit check the player cannot fail, so the first mechanics block they ever see is one that worked.
2. **Step through.** The moment of the setting: the door closes behind them and nothing can reach them. Tolk says something unhelpful.
3. **The Landing.** Diagnosis. The fault is real and physical, and the Tinker reads it fastest — but the Runner can get to the housing on the mast, the Fieldhand can tell that the maintenance crew have been working double shifts and lying about it, and the Talker can get the truth out of the foreman in one conversation.
4. **The complication.** The Holding's people have been *keeping the anchor warm* with a jury-rig that is making the failure worse, because being cut off would end them and they cannot bear to stop. Nobody here is a villain.
5. **The avoidable fight.** The foreman will physically stop the player from shutting the jury-rig down. Marked **avoidable** in the text, with the three non-violent outs written out explicitly — and if it happens, it ends in a knockout and a restraint loop, never worse.
6. **The repair, and the cost.** The door can be saved for now. Fixing it properly needs a part that is not here, and getting it is somebody's decision above the player's pay grade.
7. **Debrief at the Nine.** Calloway signs it off. On the paperwork is a countersignature neither of them can explain — *the Quorum*. That is the whole of Act 1's reveal: **a word, and no face.**

`lore/gm-guide/running-the-quiet-door.md` (`gm`) carries the four-pre-gen
solution matrix as a table, the three non-violent outs, and the one line the GM
must not skip: **if the player asks to call for help, the answer is that there is
nobody to call, and that is not a punishment.**

`encounters/coldwater-anchor-fault.json` holds the optional confrontation in the
engine's encounter shape, with the foreman and, if it escalates, two Holding
hands — all three carrying tools and fists, **no lethal weapons**.

- [ ] **Step 4: Run the tests to verify they pass**

Expected: all passed except `test_both_entry_points_exist_and_declare_themselves`,
which still wants `flare` — that is Task 11. Mark it `xfail` only if the executor
is running tasks strictly in order; otherwise finish Task 11 before gating.

- [ ] **Step 5: Commit**

```bash
git add lore/entry-points/the-quiet-door.md lore/gm-guide/running-the-quiet-door.md encounters/
git commit -m "feat: entry point A, 'The Quiet Door' -- diagnosis, and one avoidable fight"
```

---

### Task 11: Entry point B — "Flare"

**Files:**
- Create: `lore/entry-points/flare.md`, `encounters/the-barricade.json`, `lore/gm-guide/running-flare.md`, `lore/gm-guide/special-effects-are-the-players.md`
- Modify: `tests/test_content_rules.py` (append)

**Interfaces:**
- Consumes: `locations/gliese-65-refinery.md`, `locations/the-barricade.md`, `characters/creatures/tallyman.json`.
- Produces: `lore/entry-points/flare.md` with `entry_point: "flare"`.

- [ ] **Step 1: Write the failing test**

```python
def test_flare_runs_on_a_clock_and_still_kills_nobody():
    p = ROOT / "lore/entry-points/flare.md"
    _, body = parse_frontmatter(p.read_text())
    low = body.lower()
    assert "clock" in low or "minutes" in low, "the flare must be on a timer"
    for word in ("kill", "killed", "corpse", "dead"):
        assert f" {word} " not in low, (
            f"the action track must resolve in knockouts; found {word!r}"
        )


def test_the_action_track_hands_special_effects_to_the_player():
    """TABLE.md section 7, and the whole reason a kid who came to fight stays."""
    p = ROOT / "lore/gm-guide/special-effects-are-the-players.md"
    _, body = parse_frontmatter(p.read_text())
    assert "never choose" in body.lower() or "the player chooses" in body.lower()


def test_every_combatant_in_an_encounter_carries_a_non_lethal_weapon():
    """Review Focus 5, enforced in data rather than trusted to the GM."""
    for p in (ROOT / "encounters").glob("*.json"):
        enc = _json.loads(p.read_text())
        for c in enc.get("combatants", []):
            gear = " ".join(c.get("equipment", [])).lower()
            assert any(w in gear for w in
                       ("stunner", "baton", "restraint", "unarmed", "tool", "net")), (
                f"{p.name}: {c.get('name')} carries nothing non-lethal"
            )
            for lethal in ("rifle", "sidearm", "blade", "knife", "pistol"):
                assert lethal not in gear, (
                    f"{p.name}: {c.get('name')} carries a {lethal}"
                )
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — `FileNotFoundError: lore/entry-points/flare.md`.

- [ ] **Step 3: Write the scenario**

The combat-forward sitting, same length and same ending shape as Task 10.

1. **The Nine.** Calloway briefs under pressure: the Gliese 65 refinery has stopped answering, and BL Ceti and UV Ceti are **flare stars** — the real reason this is urgent is in `lore/geography/gliese-65-the-flare-twins.md`, and it is true.
2. **Step through into the brownout.** Deck lighting failing every ninety seconds. The refinery crew have barricaded the corridor between the living deck and the anchor.
3. **The clock, stated out loud.** The flare arrives in a known number of minutes. Write the actual count in the GM guide and have Claude mark its passage in fiction — the lights, the hull, the radio hiss — never as a number in prose.
4. **Why they barricaded it.** The shelter is on the anchor side. A tallyman detachment impounded the refinery's transit rights that morning and the crew decided that if they could not leave they would at least hold the door. They are frightened, not hostile, and **Captain Brace's tallymen are still in there with them.**
5. **The fight, and it is a real one.** This is where the Mythras engine earns its keep: initiative, action points, parry versus evade, hit locations, and **special effects as the player's choice** every single time they win an exchange. Three waves at most, escalating, each with a way through that is not fighting if the player finds it.
6. **Everybody lives.** Tallymen want prisoners because a body is not a line on a manifest (Task 6). Stunners, batons, restraint loops. The barricade's cross-strap and maintenance crawl from Task 9 are the two non-violent solutions, and the Tinker and the Runner each own one.
7. **Debrief.** Same countersignature on the same paperwork: *the Quorum*. Brace knew the impound order was coming before it was issued, and says so once, and should not have.

`lore/gm-guide/special-effects-are-the-players.md` (`gm`) is short and absolute:
when the player wins an exchange, **the GM never chooses the special effect** —
they name what is available and the player picks. Cites `TABLE.md` §7. This is
the single biggest difference between a fight that a twelve-year-old enjoys and
one they endure.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: all passed, including
`test_both_entry_points_exist_and_declare_themselves`.

- [ ] **Step 5: Commit**

```bash
git add lore/entry-points/flare.md lore/gm-guide/ encounters/
git commit -m "feat: entry point B, 'Flare' -- the combat engine on a flare-star clock"
```

---

### Task 12: The living world — agendas, beats, facts, journal

**Files:**
- Create: 12 files under `agendas/`, 24 under `beats/`, 9 under `facts/`, plus `knowledge.json` and `journal/events.json`
- Create: `lore/gm-secret/the-quorum.md`, `lore/gm-secret/acts-three-to-five.md`, `lore/gm-secret/what-tolk-is.md`
- Modify: `tests/test_seed.py` (create)

**Interfaces:**
- Consumes: character and location ids from Tasks 8-9 (agendas reference `holder`/`targets` by `myth-char-` id; beats reference `agenda` and `place`).
- Produces: `facts/*.md` with `status: "not-yet-true"` or `"established"`, which Act 2's reveal is computed from rather than remembered.

- [ ] **Step 1: Write the failing test**

`tests/test_seed.py`:

```python
"""Seed invariants. A seed that has been played is not a seed."""
import glob
import json
from pathlib import Path

from content_rules import ROOT, parse_frontmatter

SEED_ID = "myth-campaign-first-through-s1"


def test_every_beat_is_pending():
    paths = glob.glob(str(ROOT / "beats" / "*.md"))
    assert len(paths) >= 20, f"only {len(paths)} beats"
    for b in paths:
        meta, _ = parse_frontmatter(Path(b).read_text())
        assert meta.get("status") == "pending", f"{Path(b).name} is not pending"


def test_the_journal_holds_one_seed_note():
    events = json.loads((ROOT / "journal" / "events.json").read_text())
    assert len(events) == 1, f"a seed carries one note, not {len(events)}"
    assert events[0]["type"] == "gm-note"


def test_agendas_reference_real_characters():
    ids = {json.loads(p.read_text())["id"]
           for p in (ROOT / "characters").rglob("*.json")}
    for p in (ROOT / "agendas").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["holder"] in ids, f"{p.name}: holder {meta['holder']} unknown"
        for t in meta.get("targets") or []:
            assert t in ids, f"{p.name}: target {t} unknown"


def test_beats_reference_real_agendas_and_places():
    agendas = {parse_frontmatter(p.read_text())[0]["id"]
               for p in (ROOT / "agendas").glob("*.md")}
    places = {parse_frontmatter(p.read_text())[0]["id"]
              for p in (ROOT / "locations").glob("*.md")}
    for p in (ROOT / "beats").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["agenda"] in agendas, f"{p.name}: agenda {meta['agenda']}"
        assert meta["place"] in places, f"{p.name}: place {meta['place']}"


def test_the_act_two_reveal_is_a_fact_not_a_memory():
    """Spec section 13: the facts graph carries what the player has learned, so
    the reveal is computed rather than improvised."""
    titles = [parse_frontmatter(p.read_text())[0]["title"].lower()
              for p in (ROOT / "facts").glob("*.md")]
    assert any("forty years" in t or "has known" in t for t in titles), (
        "no fact records the Threshold's forty-year silence"
    )
    for p in (ROOT / "facts").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["status"] in ("not-yet-true", "established")
        assert meta["truth"] in ("true", "false")
```

- [ ] **Step 2: Run it to verify it fails**

Expected: FAIL — "only 0 beats".

- [ ] **Step 3: Write the twelve agendas**

Each with a clock (`clock_size` 4-8, `clock_filled: 0`), a `holder`, and a
`status` of `active` or `dormant`. Target scale from spec §13, smaller than
Purewater because solo play visits fewer places.

Suggested set: Calloway *keep the intake alive*; Hale *keep the failure rate out
of the public record*; Brace *collect on the impound orders before anyone asks
who signed them*; Ferren *be the one they send to LHS 1140*; the Coldwater
Holding *keep the door warm whatever it costs*; the Tally *bring every anchor
under toll before the new door opens*; Tolk *find out what Bell was*; plus five
more that give the near systems something to be doing.

Dormant agendas gate on knowledge, which the engine activates during `tick` when
the holder learns the trigger fact — so write the trigger as a fact id, not as
prose.

- [ ] **Step 4: Write the twenty-four beats**

Each `status: "pending"`, a `when` on the campaign clock, a `trigger`, an
`onscreen_if` describing the presence that stages it, an `agenda`, and a `place`.
At least six must fire in each entry point's system so that a player who takes
either route still meets a living world.

- [ ] **Step 5: Write the nine facts and `knowledge.json`**

The spine: *the anchors are failing faster than age explains* (`established`,
true); *the Threshold has known for forty years* (`established`, true, known
only to Hale and two others); *the Coldwater jury-rig is making it worse*
(`established`, true, known to the Holding's engineer and nobody else); *the
Quorum countersigned the impound orders* (`established`, true, known to Brace);
and the one believed falsehood — *the failures are ordinary ageing*
(`established`, **false**, believed by almost everyone, which is exactly the
first-class object the engine was built to hold).

`knowledge.json` is `{"knows": [...]}` with one entry per
character/fact pair carrying `certainty`, `source` and `since: 0`.

- [ ] **Step 6: Write the three gm-secret entries**

All `visibility: "gm"`.

- **`the-quorum.md`** — the whole of spec §11, so a GM running v1 knows what the countersignature means even though the player cannot learn it yet.
- **`acts-three-to-five.md`** — the outline, explicitly labelled *not implemented in v1*.
- **`what-tolk-is.md`** — Tolk's species was built. **Records as an open authoring decision** whether this is the same revelation as the door nobody launched, or a second one; v1 does not need to resolve it and must not accidentally foreclose it.

- [ ] **Step 7: Write `journal/events.json`**

Exactly one `gm-note` describing the seed state and naming no character.

- [ ] **Step 8: Run the tests to verify they pass**

Expected: all passed.

- [ ] **Step 9: Commit**

```bash
git add agendas/ beats/ facts/ knowledge.json journal/ lore/gm-secret/ tests/test_seed.py
git commit -m "feat: the living world -- 12 agendas, 24 beats, and a believed falsehood"
```

---

### Task 13: Plugin wiring

Owns **Review Focus 1, 2 and 5** — the three ways this ships broken for a real
player on day one.

**Files:**
- Create: `.claude-plugin/plugin.json`, `hooks/hooks.json`, `scripts/engine.sh`, `scripts/session-start.sh`, `commands/start.md`, `TABLE-ADDENDUM.md`, `CLAUDE.md`
- Create: `tests/test_plugin.py`
- Test: `tests/test_plugin.py`

**Interfaces:**
- Consumes: `lore/entry-points/*.md` `entry_point` keys; `templates/*.json` names.
- Produces: `scripts/engine.sh` exporting `GM_ROOT`, `GM_SKILL`, `GM_CLI` and a `gm()` shell function, sourced by the hook and by `commands/start.md`.

- [ ] **Step 1: Write the failing test**

`tests/test_plugin.py`:

```python
"""The three ways a campaign plugin ships broken, each one a bug that has
actually happened in a sibling repository."""
import json
import os
import subprocess

from content_rules import ROOT

SEED_ID = "myth-campaign-first-through-s1"


def test_the_hook_never_takes_the_session_down():
    """Review Focus 1. purewater's engine.sh header records why: the hook runs
    under `set -u`, so one bare ${CLAUDE_PLUGIN_ROOT} aborts the caller and the
    campaign reports the engine missing when it is installed and working.

    Run it with no engine, no plugin root and no HOME pointer, which is the
    worst case, and require exit 0."""
    env = dict(os.environ)
    for k in ("CLAUDE_PLUGIN_ROOT", "MYTHRAS_GM_ROOT", "VIRTUAL_ENV"):
        env.pop(k, None)
    env["HOME"] = "/nonexistent-home-for-this-test"
    r = subprocess.run(
        ["bash", str(ROOT / "scripts" / "session-start.sh")],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert r.returncode == 0, (
        f"the hook exited {r.returncode}; it must always exit 0\n"
        f"stderr: {r.stderr}"
    )
    assert r.stdout.strip(), "the hook said nothing; its stdout reaches the model"
    assert "unbound variable" not in r.stderr


def test_every_environment_variable_in_engine_sh_has_a_default():
    """The `set -u` trap, checked statically so it cannot regress."""
    text = (ROOT / "scripts" / "engine.sh").read_text()
    import re
    for m in re.finditer(r"\$\{([A-Z_][A-Z0-9_]*)([^}]*)\}", text):
        name, rest = m.group(1), m.group(2)
        if name in ("GM_ROOT", "GM_SKILL", "GM_CLI", "BASH_SOURCE"):
            continue
        assert rest.startswith(":-") or rest.startswith("%") or rest.startswith("#"), (
            f"${{{name}{rest}}} has no :- default"
        )


def test_the_start_command_refuses_to_clobber_a_game_in_progress():
    """Review Focus 2. A start command that resets somebody's campaign is worse
    than no start command at all."""
    text = (ROOT / "commands" / "start.md").read_text()
    assert "get-campaign" in text, "it must look before it imports"
    assert "/mythras-gm:play" in text, "it must hand a live game to the play command"
    low = text.lower()
    assert "do not import" in low or "stop" in low


def test_the_start_command_states_the_non_lethal_rule():
    """Review Focus 5. If the GM has not read it before the first roll, a
    child's first character can die on one bad exchange."""
    text = (ROOT / "commands" / "start.md").read_text()
    assert "TABLE-ADDENDUM.md" in text


def test_the_addendum_states_the_rule_in_both_directions():
    text = (ROOT / "TABLE-ADDENDUM.md").read_text()
    low = text.lower()
    assert "never killed" in low or "not killed" in low
    assert "knocked out" in low or "unconscious" in low
    assert "both directions" in low, (
        "the rule applies to what the PC does as well as what is done to them"
    )


def test_the_start_command_offers_both_entry_points_and_all_four_pregens():
    text = (ROOT / "commands" / "start.md").read_text()
    for slug in ("the-quiet-door", "flare"):
        assert slug in text, f"start does not offer {slug}"
    for p in (ROOT / "templates").glob("*.json"):
        assert json.loads(p.read_text())["name"] in text


def test_the_plugin_manifest_declares_the_engine_dependency():
    m = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "first-through"
    assert "mythras-gm" in m["dependencies"]
    assert m["hooks"] == "./hooks/hooks.json"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run --with pytest pytest tests/test_plugin.py -q
```

Expected: FAIL — `FileNotFoundError: scripts/session-start.sh`.

- [ ] **Step 3: Copy `scripts/engine.sh` verbatim from the sibling repo**

```bash
cp ~/purewater-campaign-v2/scripts/engine.sh scripts/engine.sh
chmod +x scripts/engine.sh
```

Do **not** rewrite it. Its header documents two bugs already paid for: every
variable expands with `:-` because the hook runs under `set -u`, and the
install-tree probe matches on the skills path rather than one hard-coded plugin
layout. Change nothing but the comment that names the campaign.

- [ ] **Step 4: Write `scripts/session-start.sh`**

Model on `~/purewater-campaign-v2/scripts/session-start.sh`, which already has
the right shape. Four things it must do and one it must never:

- `set -uo pipefail`, `unset VIRTUAL_ENV`, and `PW="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"` — the fallback is what makes the file runnable by hand, and by the test above.
- Report *engine missing*, *uv missing*, *database unusable*, *imported but unstarted*, *in progress*, and *not yet imported* — each as one clear line on stdout, because on `SessionStart` stdout reaches the model.
- **Never import.** Importing writes hundreds of rows and belongs to a command the user ran.
- **Always `exit 0`.** Having this plugin enabled must not block a session in an unrelated directory.
- When the database is unusable, say so and tell the model **not to narrate, not to roll, and not to claim anything was saved.**

- [ ] **Step 5: Write `hooks/hooks.json`**

```json
{
  "description": "Report the state of the First Through save at session start. Never imports, never blocks.",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/session-start.sh\"",
            "timeout": 120000,
            "statusMessage": "Checking the First Through save file",
            "async": false
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "first-through",
  "displayName": "First Through",
  "description": "A Mythras Imperative campaign for mythras-gm, built as a first roleplaying game for 10-15 year olds and set in the real stellar neighbourhood. Nine hundred and seventy-five years ago seedships carried anchor pairs out at a twentieth of lightspeed; where one arrived, a door opened, and that is the only way between stars. Two one-sitting entry points -- one investigation, one boarding action -- four pre-generated first-throughs, and a living world of 12 agendas and 24 beats. Nobody dies.",
  "version": "0.1.0",
  "author": {"name": "Fourth Wall Gaming", "url": "https://github.com/fourth-wall-gaming"},
  "repository": "https://github.com/fourth-wall-gaming/first-through-campaign",
  "homepage": "https://github.com/fourth-wall-gaming/first-through-campaign",
  "license": "MIT",
  "keywords": ["rpg", "mythras", "campaign", "gamemaster", "tabletop", "science-fiction", "kids"],
  "dependencies": ["mythras-gm"],
  "hooks": "./hooks/hooks.json"
}
```

- [ ] **Step 7: Write `TABLE-ADDENDUM.md`**

The non-lethal convention, stated where the GM will read it. It must say, in
substance and in these words where the test checks them: a first-through at
death's door is **knocked out**, captured, or dragged clear and is **never
killed**; the rule runs in **both directions**, so the player is never put where
killing is the expected solution; Mythras rules are unchanged, and this is a
narration convention applied at the moment a wound would be fatal. Add the
in-fiction reasons from Task 6 — a hull is thin, a station is a closed volume, a
corpse is paperwork, and the Tally wants prisoners because a body is not a line
on a manifest — so the GM is applying the setting rather than overriding dice.

Also carries the two onboarding devices that are table conduct rather than
content: **when the player goes quiet, Tolk speaks and the GM does not offer a
list**, and **the player always chooses the special effect**.

- [ ] **Step 8: Write `commands/start.md`**

Model on `~/purewater-campaign-v2/commands/start.md` (147 lines). Order matters:

1. Source `scripts/engine.sh`; if `GM_ROOT` is empty, say how to install the engine and stop.
2. **Is the player new to roleplaying?** Ask, do not assume. If yes, read `lore/player-briefing/first-through-the-sixty-second-briefing.md` and give it **in your own words** in about a minute. Before character choice, because knowing Passions matter changes what a player picks.
3. **Read `TABLE-ADDENDUM.md` before the first roll.** Named explicitly; the test checks for it.
4. `gm init-db`, then `gm get-campaign --campaign myth-campaign-first-through-s1` — **not found** → import; **session 0** → skip import; **session > 0** → **stop**, report the clock, hand them `/mythras-gm:play`, do not import and do not offer to start over unless they ask in so many words.
5. Offer the two entry points by name, in the player's language, two sentences each — *"a door that is dying, and four thousand people behind it"* versus *"a barricade, a crew who will not move, and a star about to do something"*.
6. Offer the four pre-gens, one line each, and say plainly that every one of them can finish either mission.
7. `set-scene`, then narrate. Not before.

- [ ] **Step 9: Write `CLAUDE.md`**

Short. What this repo is, that the files are a **source export and not the save**, that the engine's `TABLE.md` governs conduct and `TABLE-ADDENDUM.md` adds the non-lethal rule, and that `data/systems.json` is the authority on every astronomical claim — if prose and data disagree, the data wins and the prose is a bug.

- [ ] **Step 10: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: all passed.

- [ ] **Step 11: Commit**

```bash
git add .claude-plugin/ hooks/ scripts/ commands/ TABLE-ADDENDUM.md CLAUDE.md tests/test_plugin.py
git commit -m "feat: plugin wiring, and the three ways this would have shipped broken"
```

---

### Task 14: Round trip, and the README

Owns **Review Focus 4** — `--new-ids` orphaning cross-references.

**Files:**
- Create: `tests/test_roundtrip.py`
- Modify: `README.md`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: everything. This is the gate that says the repo is a loadable campaign rather than a pile of markdown.

- [ ] **Step 1: Write the failing test**

`tests/test_roundtrip.py`:

```python
"""The repo must import into TypeDB and export back out without losing a thing,
and it must survive id remapping."""
import json
import re
import subprocess

import pytest

from content_rules import ROOT, lore_files, parse_frontmatter

SEED_ID = "myth-campaign-first-through-s1"


def _gm(*args):
    engine = subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    r = subprocess.run(
        ["uv", "run", "-q", "--project", engine, "python",
         f"{engine}/mythras_gm.py", *args],
        capture_output=True, text=True, cwd=ROOT,
    )
    return r


def test_no_prose_hardcodes_a_myth_id():
    """Review Focus 4. --new-ids remaps every id, so a myth- id written into a
    sentence becomes a dangling reference the moment anybody installs this."""
    pattern = re.compile(r"myth-(char|loc|fac|lore|agenda|beat|fact|tmpl)-[0-9a-f]{12}")
    for p in lore_files():
        _, body = parse_frontmatter(p.read_text())
        found = pattern.findall(body)
        assert not found, f"{p.relative_to(ROOT)} hardcodes a myth- id in prose"


def test_cross_references_use_wiki_links_or_slugs():
    """The two forms that survive remapping: [[Name]] links, resolved by name,
    and data/*.json slugs, which are not ids at all."""
    linked = 0
    for p in lore_files():
        _, body = parse_frontmatter(p.read_text())
        linked += len(re.findall(r"\[\[[^\]]+\]\]", body))
    assert linked > 10, f"only {linked} wiki links; the worldbook is not connected"


def test_the_database_is_reachable_before_we_claim_anything():
    r = _gm("doctor")
    if r.returncode != 0:
        pytest.skip(f"database not usable: {r.stdout[:200]}")


def test_import_then_export_round_trips_losslessly(tmp_path):
    r = _gm("import-campaign", "--path", str(ROOT), "--new-ids")
    if r.returncode != 0:
        pytest.skip(f"import failed: {r.stdout[:400]}")
    new_id = json.loads(r.stdout)["campaign"]
    try:
        out = tmp_path / "exported"
        e = _gm("export-campaign", "--campaign", new_id, "--output", str(out))
        assert e.returncode == 0, e.stdout

        for sub, glob in (("lore", "*/*.md"), ("agendas", "*.md"),
                          ("beats", "*.md"), ("facts", "*.md"),
                          ("locations", "*.md"), ("factions", "*.md")):
            before = len(list((ROOT / sub).glob(glob)))
            after = len(list((out / sub).glob(glob)))
            assert after == before, f"{sub}: {before} in, {after} out"

        chars_in = len(list((ROOT / "characters").rglob("*.json")))
        chars_out = len(list((out / "characters").rglob("*.json")))
        assert chars_out == chars_in, f"characters: {chars_in} in, {chars_out} out"
    finally:
        _gm("delete-campaign", "--campaign", new_id, "--yes")
```

- [ ] **Step 2: Run it to verify it fails or skips honestly**

```bash
uv run --with pytest pytest tests/test_roundtrip.py -v
```

Expected: `test_no_prose_hardcodes_a_myth_id` and
`test_cross_references_use_wiki_links_or_slugs` FAIL if any task wrote a raw id
into prose or left the worldbook unlinked. The database tests **skip** when no
engine or no TypeDB is present, and that skip is correct — it must never look
like a pass.

- [ ] **Step 3: Fix what it found**

Replace any `myth-` id in prose with a `[[Name]]` link. Add wiki links until the
worldbook is genuinely connected: every geography entry should link its station,
every entry point should link its locations and cast.

- [ ] **Step 4: Run the full suite with a live database**

```bash
uv run --with pytest pytest tests/ -q
```

Expected: everything passes, including the round trip.

- [ ] **Step 5: Finish the README**

Replace the Status section with: install instructions
(`/plugin install first-through@fourth-wall-gaming`, then
`/first-through:start`), the two entry points described in a sentence each, the
four pre-gens named, the promise that **nobody dies**, and a short *"the
astronomy is real"* section pointing at `data/systems.json` as the cited source
of every figure. Keep the ORC notice.

- [ ] **Step 6: Commit and push**

```bash
git add tests/test_roundtrip.py README.md
git commit -m "test: the round trip, and the id-remapping trap it guards"
git push origin main
```

---

## Self-Review

Run against the spec, 2026-10-05.

**Spec coverage.** §1-2 → Task 1 manifest and the plan's Global Constraints.
§3 content rules → Tasks 1, 2, 4, 5, 8 tests. §4 the Causeway → Tasks 2, 3, 4.
§5 the star map and the edge-list deliverable → Tasks 2, 3, 5. §6 pre-gens,
Calloway, Tolk → Tasks 7, 8. §7 powers → Task 7. §8 onboarding (all four
devices) → Task 4 briefing, Task 9 affordances, Task 8 Tolk, Task 10 guaranteed
early success. §9 two entry points → Tasks 10, 11. §10 the arc, Acts 1-2 →
Tasks 10, 11, 12. §11 the Quorum, bottom rung only → Task 12 gm-secret, tested
in Task 8. §12 adversaries and the creature rule → Tasks 6, 8. §13 mechanics
and living-world scale → Tasks 7, 12. §14 repo shape → Tasks 1-13. §15 success
criteria → Tasks 13 (five-minute start), 10-11 (one sitting), 7 and 10-11 (all
four pre-gens, nobody killed), 2 and 5 (cited astronomy), Global Constraints
(engine untouched). §16 decisions → Task 12 records the Tolk question as open.

**Placeholder scan.** No TBDs. Every test step carries runnable code; every
content step carries a full worked specimen plus an exact file list. The two
steps that legitimately defer are Task 2 Step 3 (fetch real coordinates — the
*method* is given, and writing figures from memory is forbidden by the
constraints) and Task 3 Step 3 (design nine Sirius edges to satisfy a stated
predicate).

**Type consistency.** `parse_frontmatter`, `lore_files`, `systems`, `edges`,
`door_opened_years_ago`, `separation_ly`, `ROOT`, `LAUNCH_YEARS_AGO`,
`YEARS_PER_LIGHT_YEAR` are defined once in Task 1 and used with those exact
names in Tasks 2-14. Slug keys — not `myth-` ids — are the join between
`data/*.json`, `lore/geography/*.md` and `locations/*.md`, consistently, and
Task 14 enforces it. The `powers` entry shape `{name, rule, boosts, limits}`
matches `purewater-campaign-v2/characters/pcs/magda.json` exactly.

**Review Focus coverage.** 1 and 2 and 5 → `tests/test_plugin.py` (Task 13).
3 → `tests/test_powers.py` (Task 7). 4 → `tests/test_roundtrip.py` (Task 14).
All five have tests in the task that owns the code.

One gap found and fixed inline: §5's edge-list deliverable had no owning task in
the first draft of this plan. It is now Task 3, with the causality predicate
machine-checked.
