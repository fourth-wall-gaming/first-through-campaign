# First Through v3 Setting Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Propagate the v3 design across every content file in the repository and into the live TypeDB save, so that the game that gets narrated is the game that was designed.

**Architecture:** This is a content rewrite driven by executable gates. `tests/content_rules.py` already parses frontmatter exactly as the engine's importer does, and `tests/test_content_rules.py` already runs hard content rules as pytest gates. Every task here adds a gate first, watches it fail and name the offending files, rewrites those files, and watches it pass. Scale and system facts move into `data/systems.json` as structured data so prose can be checked against them rather than drifting from them. The final task propagates into the live campaign with `update-lore`, because the save is mid-session-6 and a re-import would fork it.

**Tech Stack:** Python 3, pytest, `uv`, markdown with JSON-valued frontmatter, TypeDB via the `mythras-gm` CLI.

**Spec:** `docs/superpowers/specs/2026-10-17-first-through-v3-design.md`

## Global Constraints

- **The register is space opera.** Star Wars and Douglas Hill. Velocity, wonder, a home worth belonging to, villains worth hating, a child who is the most important person in the room. Where astronomy competes with the adventure, the adventure wins.
- **Every astronomical figure is real and fetched, never recalled.** `data/systems.json` carries `sources` per system; anything new gets one. Invented life is the only exception and must be flagged as invented.
- **Transit arithmetic is fixed:** `LAUNCH_YEARS_AGO = 975`, `YEARS_PER_LIGHT_YEAR = 20`. Do not change these; `test_the_arithmetic_is_the_spec_arithmetic` gates them.
- **No nakedness, anywhere, ever.** Audience constraint, not flavour. A 10–15 year old plays this alone with an AI GM.
- **Nothing manufactured crosses a door.** The weave and grown kit cross; freight never does; there is no interstellar trade.
- **No signal crosses a door.** Information moves at courier speed, in living cells, carried by children.
- **Fetches are people.** Never bred, never stock, never written to by a human with a machine.
- **Lethality stands.** `TABLE-ADDENDUM.md` §1 is correct as written and is not to be softened. The duty survives: no death from a risk the player could not see when they chose it.
- **Every file keeps its frontmatter `id`.** The ids are the join keys to the live save. Changing one orphans an entry.
- **Commit after every task.** Work stays on `feat/v3-setting-redesign`.

## Review Focus

Five things the spec implies that no single task's gate will catch, most likely to bite first:

1. **An `id` gets dropped or edited during a rewrite**, silently orphaning that entry from the live save — covered by a gate in Task 1 that pins the full id set before any rewriting starts.
2. **Banned vocabulary reappears in a file rewritten by a later task**, because the gate that banned it ran earlier — every gate in this plan runs over the whole tree on every invocation, never over one file, so later tasks re-run earlier gates.
3. **`data/systems.json` and the prose disagree about a population or a door count** once both exist — Task 1 adds `test_no_geography_page_contradicts_its_data_row`, which pulls every "N people" figure out of each `lore/geography/*.md` and fails if one is absent from that system's data row. It is deliberately narrow: it catches the contradiction that broke credibility (van Maanen's with two staff) and does not try to parse prose in general.
4. **A beat or agenda still turns on an object that no longer exists** (a ledger, a report, a signed form), so the scene cannot be run as written — Task 11 sweeps `beats/`, `agendas/` and `facts/` with the same banned-vocabulary gate as `lore/`.
5. **The live save keeps serving v1 text after the files are correct**, which is the exact failure that produced session 5 — Task 12 verifies by reading entries back **out of the graph**, not out of the files, and the task is not complete until that read-back passes.

---

### Task 1: Pin the ids, and put scale in the data

**Files:**
- Modify: `data/systems.json`
- Modify: `tests/content_rules.py`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `content_rules.lore_ids()` returning `set[str]`; `content_rules.all_content_files()` returning `list[Path]`; every row in `data/systems.json` gains integer `population` and integer `doors`.

- [ ] **Step 1: Write the failing gates**

Add to `tests/content_rules.py`:

```python
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
```

Add to `tests/test_content_rules.py`:

```python
from content_rules import all_content_files, edges, lore_ids, systems

# Captured 2026-10-17, before the v3 rewrite began. These ids are the join
# keys to myth-campaign-first-through-s1, which is live at session 6. A
# rewrite may change every word of a file and may not change its id.
FROZEN_LORE_IDS = None  # replaced in Step 2 with the real set

# Ids deliberately removed by a later task, each with the task that did it.
REMOVED_LORE_IDS = set()  # Task 6 adds the-cold-arm.md's id here


def test_no_lore_id_is_lost_or_changed():
    """Subset semantics, not equality: later tasks legitimately create new
    lore files. What must never happen is a frozen id going missing or being
    edited, because the ids are the join keys to a live save."""
    expected = set(FROZEN_LORE_IDS) - REMOVED_LORE_IDS
    missing = expected - lore_ids()
    assert not missing, f"lore ids lost or changed: {sorted(missing)}"


def test_every_system_has_a_population_and_a_door_count():
    for key, s in systems().items():
        assert isinstance(s.get("population"), int), f"{key} has no population"
        assert isinstance(s.get("doors"), int), f"{key} has no door count"


def test_the_scale_is_thirty_billion():
    total = sum(s["population"] for s in systems().values())
    assert 25_000_000_000 <= total <= 35_000_000_000, total


def test_sol_holds_most_of_humanity_and_sirius_holds_almost_none():
    s = systems()
    assert s["sol"]["population"] > 9_000_000_000
    assert s["sirius"]["population"] == 40_000
    assert s["sirius"]["doors"] == 9
    assert s["sol"]["doors"] == 7


def test_no_geography_page_contradicts_its_data_row():
    """van Maanen's with two staff is the line that broke this setting's
    credibility. Deliberately narrow: every "N people" figure on a geography
    page must appear in that system's data row. It is not a prose parser."""
    import re as _re
    s = systems()
    num = _re.compile(r"\b([\d,]{2,})\s+people\b", _re.I)
    bad = []
    for p in lore_files("geography"):
        meta, body = parse_frontmatter(p.read_text())
        key = meta.get("system")
        if key not in s:
            continue
        allowed = {s[key]["population"]}
        for found in num.findall(body):
            if int(found.replace(",", "")) not in allowed:
                bad.append(f"{p.name}: {found} people, data says "
                           f"{s[key]['population']}")
    assert not bad, "\n".join(bad)


def test_doors_are_derived_from_the_edge_data():
    """data/edges.json is the authority on the network and existing tests
    already gate it. A door count written by hand in a second place is the
    exact drift this project exists to fix."""
    import collections
    deg = collections.Counter()
    for e in edges():
        deg[e["a"]] += 1
        deg[e["b"]] += 1
    for key, s in systems().items():
        assert s["doors"] == deg[key], f"{key}: {s['doors']} != {deg[key]}"
    assert sum(deg.values()) == 54, sum(deg.values())
    assert deg["lhs-1140"] == 0


```

- [ ] **Step 2: Run them to verify they fail, then freeze the real ids**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: `test_no_lore_id_is_lost_or_changed` FAILS on `None`; the four scale tests FAIL with "has no population".

Then capture the real set and paste it in place of `None`:

```bash
uv run python -c "
import sys; sys.path.insert(0, 'tests')
from content_rules import lore_ids
import json; print(json.dumps(sorted(lore_ids()), indent=4))
"
```

- [ ] **Step 3: Add population and doors to every system**

Edit `data/systems.json` so every one of the 29 rows carries integer `population` and `doors`. Use these, which satisfy the gates above and the spec's §1 table:

Populations, hand-written because nothing else holds them (plain JSON integers — `11000000000`, not `11000000000` with separators):

`sol` 11000000000 · `alpha-centauri` 4000000000 · `tau-ceti` 3000000000 · `61-cygni` 2000000000 · `procyon` 1200000000 · `epsilon-eridani` 1000000000 · `40-eridani` 900000000 · `epsilon-indi` 800000000 · `lalande-21185` 700000000 · `ross-128` 600000000 · `55-cancri` 500000000 · `gliese-876` 450000000 · `hd-40307` 400000000 · `hd-69830` 350000000 · `yz-ceti` 300000000 · `teegardens-star` 250000000 · `gliese-887` 4000 · `kapteyns-star` 11000 · `gl-725` 200000000 · `barnards-star` 180000000 · `wolf-359` 150000000 · `luhman-16` 90000 · `wise-0855` 40000 · `gj-1214` 120000000 · `trappist-1` 60000000 · `gliese-65` 61 · `van-maanens-star` 3000 · `sirius` 40000 · `lhs-1140` 0

**`doors` is NOT hand-written.** Compute it for each system as that system's degree in `data/edges.json`, which is the authority and which existing tests already gate.

Note `gliese-65` is Ladder at 61 people and `van-maanens-star` rises from 2 staff to a 3,000-person records station per spec §5.5; both are deliberate.

- [ ] **Step 4: Run the gates to verify they pass**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add data/systems.json tests/content_rules.py tests/test_content_rules.py
git commit -m "test(content): freeze the lore ids and put the scale in the data

The ids are the join keys to a live save; a rewrite may change every word
of a file and may not change its id. And thirty billion people belongs in
systems.json where a gate can check the prose against it, not scattered
through sixty markdown files where the last rewrite lost track of it."
```

---

### Task 2: What crosses — the grown weave, and no nakedness

**Files:**
- Modify: `lore/the-crossing/what-crosses-easily.md`
- Modify: `lore/technology/a-first-throughs-kit.md`
- Modify: `lore/technology/the-weave.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `content_rules.all_content_files()` from Task 1.
- Produces: nothing later tasks import.

- [ ] **Step 1: Write the failing gate**

```python
import re

NAKEDNESS = re.compile(
    r"\b(naked|nakedness|undress(?:es|ed|ing)?|disrobe\w*|dressing[- ]room)\b",
    re.I)


def test_nobody_ever_arrives_naked():
    """Audience constraint, not flavour: this is a game a 10-15 year old plays
    alone with an AI GM, and a mandatory undress-cross-dress beat on every
    transit is not acceptable regardless of how elegant the physics is."""
    bad = []
    for p in all_content_files():
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if NAKEDNESS.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_weave_crosses_and_freight_does_not():
    text = (ROOT / "lore/the-crossing/what-crosses-easily.md").read_text().lower()
    assert "weave" in text
    assert "freight does not cross" in text
    assert "grown" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "naked or weave_crosses" -v`
Expected: FAIL, listing the lines in `what-crosses-easily.md` that describe undressing and arriving with nothing.

- [ ] **Step 3: Rewrite the three files**

`lore/the-crossing/what-crosses-easily.md` — keep the id, the category and the structure. Replace the "You arrive with nothing" section entirely. What it must now say: a door takes a living thing apart and lays it down again; **you cross in your weave**, which is alive and grown, which is why a Threshold flash grows into it, and which for most people is the only possession that has ever followed anybody between stars; a **pressure-skin** and the plated suit and the sensor hood are grown from the same stock, are Threshold property, and are issued and returned — "the Nine's suit, stays at the Nine" means issued and returned, not immobile; **freight does not cross**, so there are no crates, no bar stock, no bulk of any kind, no interstellar trade at all, and every system is supplied from inside itself. Delete every dressing room. Rewrite the `summary:` frontmatter to match.

`lore/technology/a-first-throughs-kit.md` — the pressure-skin, suit and hood are grown, not built. Keep the charge budget and the "it can be taken off you" section, which both still work.

`lore/technology/the-weave.md` — it is alive, it is grown, the flash grows into it, it is yours, and it is the one thing that crosses.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all, including Task 1's id gate.

- [ ] **Step 5: Commit**

```bash
git add lore/the-crossing/what-crosses-easily.md lore/technology/a-first-throughs-kit.md lore/technology/the-weave.md tests/test_content_rules.py
git commit -m "fix(crossing): you cross in your weave, and nobody arrives naked

A courier who arrives with nothing dies on an unsurveyed far side, which is
the case the old rule never had an answer for. And a mandatory undress beat
on every transit is not something to put in front of a thirteen-year-old
playing alone, however tidy the physics was.

The kit is grown rather than built, which keeps every structural reason the
rule existed for: no freight, no trade, no shippable army."
```

---

### Task 3: Kill the paper

**Files:**
- Modify: `lore/technology/the-standing.md`
- Modify: `lore/organizations/the-threshold.md`
- Modify: `factions/the-threshold.md`
- Create: `lore/technology/lading-and-attestation.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `all_content_files()`.
- Produces: the vocabulary other tasks must use — `lading`, `attestation`, `budding`, `drift`, `reconciliation`.

- [ ] **Step 1: Write the failing gate**

```python
PAPER = re.compile(
    r"\b(ledger|ledgers|logbook|log ?book|tome|tomes|clerk|clerks|clerical"
    r"|filing cabinet|paperwork|bureaucrat\w*|rubber[- ]stamp\w*"
    r"|carbon copy|in triplicate|typed|typewrit\w*)\b", re.I)

# Inside a system there is no reason to write anything down. Between stars
# the channel is living cells. Paper is a v1 artefact in both places.
PAPER_ALLOWED = {
    "docs",                      # specs and plans may discuss what was deleted
    "lore/history",              # the Sorting and the First Reach are historical
}


def _exempt(p):
    rel = str(p.relative_to(ROOT))
    return any(rel.startswith(a) for a in PAPER_ALLOWED)


def test_there_is_no_paper_left_in_the_causeway():
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if _exempt(p):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if PAPER.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_new_vocabulary_is_defined_somewhere():
    text = (ROOT / "lore/technology/lading-and-attestation.md").read_text().lower()
    for word in ("lading", "attestation", "budding", "drift", "reconciliation"):
        assert word in text, word
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "paper or vocabulary" -v`
Expected: FAIL, listing every surviving ledger and clerk, and FAIL on the missing file.

- [ ] **Step 3: Write the new vocabulary file and rewrite the offenders**

Create `lore/technology/lading-and-attestation.md` with fresh frontmatter — a new `myth-lore-` id (12 hex characters, matching the existing convention), `category: "technology"`, `visibility: "player"`. It defines, with a paragraph each:

**Lading** — what a courier is carrying. *"What's your lading?"* replaces every manifest in the setting. **Attestation** — what replaces a signature: you say it, a mind witnesses it, and it is permanent and public within that hull, so nothing can be recorded unofficially, ever, which makes an off-book order harder rather than easier. **Budding** — how a living archive is copied so it can be carried. **Drift** — the divergence between two systems' copies of the same archive; *"the drift on the anchor corpus is nine months."* **A reconciliation** — the job of merging an arriving lading into a local archive: a profession, and a political one, because two archives disagree and somebody decides.

`lore/technology/the-standing.md` — keep the id and the name. It is no longer a board on a wall. It is a **living archive** holding the testimony of every far side anybody has stood on. Keep the existing rule, which gets better: a mind may not write on the Standing, because a mind has no testimony; only a body that went can enter one. Add: unlike a board, a Standing can be **budded and carried**, so every system holds a divergent copy and they disagree.

`lore/organizations/the-threshold.md` and `factions/the-threshold.md` — strip the underfunded-charity framing. The Threshold is small because the doors cap it, and it is the most strategically valuable institution in human space and far too small to defend itself.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add lore/ factions/ tests/test_content_rules.py
git commit -m "feat(information): lading, attestation, budding, drift

Inside a system there is no reason to write anything down, and between
stars the channel is living cells. Paper was a v1 artefact in both places
and it is what made the setting feel like a parish council.

The Standing stops being a board and becomes a living archive, which keeps
the rule that a mind may not write on it -- a mind has no testimony -- and
adds the thing a board could never do: it can be budded and carried, so
every system holds a copy and they disagree."
```

---

### Task 4: Fetches are people, and the councils

**Files:**
- Modify: `lore/character-creation/your-fetch.md`
- Modify: `lore/gm-guide/playing-fetches.md`
- Create: `lore/organizations/the-councils.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `all_content_files()`.
- Produces: the councils as a referenceable institution for Task 5.

- [ ] **Step 1: Write the failing gate**

```python
# "bred", "stock" and "kept" applied to fetches is the v1 framing. Under v3
# that framing is an atrocity the setting itself repudiated.
FETCH_AS_LIVESTOCK = re.compile(
    r"\b(bred for|breeding|kept as stock|a book is an animal"
    r"|written to by strangers|handed over at the far end)\b", re.I)


def test_fetches_are_never_described_as_livestock():
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        text = p.read_text()
        for n, line in enumerate(text.splitlines(), 1):
            if FETCH_AS_LIVESTOCK.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_book_trade_is_recorded_as_having_ended():
    text = (ROOT / "lore/organizations/the-councils.md").read_text().lower()
    assert "council" in text
    assert "ended" in text
    assert "within living memory" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "livestock or book_trade" -v`
Expected: FAIL on `what-crosses-easily.md` and `your-fetch.md`, and on the missing councils file.

- [ ] **Step 3: Write the councils and rewrite the fetch files**

Create `lore/organizations/the-councils.md`, new `myth-lore-` id, `category: "organizations"`, `visibility: "player"`:

A fetch observes, records, recalls and shares, and does all of it under their own control; great recall is a faculty of theirs, not a service performed on them. Read-in and read-out are managed by the fetch's own senses and communications, interfacing directly with a system's minds. **No human writes to a fetch with a machine.** Humans request, receive and use. Fetches share with one another at their own discretion.

**The mutual hostage:** a fetch cannot cross a door without a first-through, and a human cannot hold a payload without a fetch. Five peoples who cannot move between stars without human children; thirty billion humans who cannot know anything about each other without the fetches; the whole thing held together by bonded pairs of a fifteen-year-old and a friend.

**The history:** the old book trade — unbonded fetch-animals kept as media, warm and fed, written to by strangers — **was slavery, and it ended within living memory.** Humanity used these people as media for centuries without understanding they were people, until it became impossible to pretend. The councils formed, the trade ended, and the information economy passed into non-human hands. Some humans are still sour about it.

**One cross-species council**, seated at the Nine, part of the Tally, composed of fetch and human delegates. It **can convene**, because it is made of the only things in the galaxy that travel — which is precisely why legitimate authority ended up with it. It is not all-powerful: frequently ignored, slow, under-resourced, and still the only legitimate body there is.

`lore/character-creation/your-fetch.md` — delete the "a book does not speak… kept as stock" passage entirely and replace it with the ended trade. Keep the bonding material, the quiet, and the fixed biology of the five species, all of which still work.

`lore/gm-guide/playing-fetches.md` — keep §1 (physiology fixed, culture a default) and §2 (every folly is a negotiation) unchanged; they are correct. Add that a fetch has a people and a council with an interest in what the player is doing, and that a fetch chooses what to share.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add lore/ tests/test_content_rules.py
git commit -m "feat(fetches): they are people, they have a council, and they own the channel

The old framing had them bred as stock and written to by strangers, which
under this design is an atrocity -- so make it one. The book trade was
slavery and it ended within living memory, the councils formed, and the
information economy of human space passed into non-human hands.

That is the setting's moral spine, every faction has a position on it, and
it makes the bond between a first-through and a fetch the most important
relationship in the game instead of a piece of equipment."
```

---

### Task 5: The Tally, masonic

**Files:**
- Modify: `lore/organizations/the-tally.md`
- Modify: `factions/the-tally.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: the councils from Task 4.
- Produces: nothing later tasks import.

- [ ] **Step 1: Write the failing gate**

```python
def test_the_tally_counts_no_crates_and_has_no_clerks():
    for rel in ("lore/organizations/the-tally.md", "factions/the-tally.md"):
        text = (ROOT / rel).read_text().lower()
        assert "lading" in text, rel
        assert "masonic" in text or "rites" in text, rel
        assert "counting house" not in text, rel
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k tally -v`
Expected: FAIL on both files.

- [ ] **Step 3: Rewrite both Tally files**

Not a counting house, no clerks, never counts a crate because there are no crates. It controls **lading** — what information is allowed to cross — exists in every system, and answers to nobody human.

Two halves in permanent tension. **The masonic order of minds:** human-made minds, one per system, bound by rites and charters older than most governments they operate under, efficiency their only value. They have never met and never can, so they have been drifting apart for centuries and even the Tally does not reliably know what the Tally currently thinks. Alien in the shadows, and not entirely bad. **The cross-species council** (Task 4), which can convene, and is why the Tally holds legitimate authority at all.

Keep the shock batons and restraint loops and the no-blades doctrine, and keep `TABLE-ADDENDUM.md`'s framing of it: an institutional preference, never a guarantee of anybody's safety.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add lore/organizations/the-tally.md factions/the-tally.md tests/test_content_rules.py
git commit -m "feat(tally): masonic, mind-run, and counting no crates

Clerks with books made no sense at this tech level and were most of what
made the setting feel grey. The Tally controls lading rather than freight,
answers to an order of minds who have never met and have been drifting
apart for centuries, and contains the one council in human space that can
actually convene."
```

---

### Task 6: Delete the cold arm, promote the Listen

**Files:**
- Delete: `lore/cosmology/the-cold-arm.md`
- Modify: `lore/cosmology/the-hesitation.md`
- Modify: `lore/character-creation/the-knacks.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: `all_content_files()`, `lore_ids()`.
- Produces: nothing later tasks import.

- [ ] **Step 1: Write the failing gate**

```python
COLD_ARM = re.compile(r"cold[- ]arm|the cold arm", re.I)


def test_the_cold_arm_is_gone():
    """A passive affliction with nothing to do in it. What survives is the
    field an unsettled mouth has, which is the thing the Listen reads."""
    assert not (ROOT / "lore/cosmology/the-cold-arm.md").exists()
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if COLD_ARM.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_listen_reads_an_unsettled_door():
    text = (ROOT / "lore/character-creation/the-knacks.md").read_text().lower()
    assert "the listen" in text
    assert "unsettled" in text
    assert "the hold" in text
```

Note: `test_no_lore_id_is_lost_or_changed` will now fail, correctly, because an id is being removed on purpose. Remove `the-cold-arm.md`'s id from `FROZEN_LORE_IDS` in the same step, with a comment saying why.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "cold_arm or listen" -v`
Expected: FAIL — the file exists, and references survive in `the-hesitation.md` and the guide.

- [ ] **Step 3: Delete and rewrite**

```bash
git rm lore/cosmology/the-cold-arm.md
```

`lore/cosmology/the-hesitation.md` — keep the mechanism, which is correct and good: transit is zero, what takes time is the door agreeing to open, a mouth that cannot settle will not establish a throat on demand, and the thing to measure is how long you stand in a lit housing before it will have you. Replace every cold-arm reference with the field itself: an unsettled mouth has a real gradient, and **that is what the Listen reads.** No accumulating injury, nobody landlocked by it.

`lore/character-creation/the-knacks.md` — promote the Listen from one knack among seven to the campaign's central ability: it is the only early-warning system humanity has and the only instrument that can sense the inside of a mouth, because nothing dead crosses and there has never been an instrument in a housing. Keep the Hold unavailable at creation and state plainly that a door being grashed is a door being made to move, so the Hold is the counter-weapon and it exists only in children.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add -A lore/ tests/test_content_rules.py
git commit -m "feat(knacks): the cold arm is deleted and the Listen is the campaign

The cold arm was a passive affliction with nothing to do in it -- a
medical mystery where the player has no move -- and it was the dull
version of an ability this setting already had a far better active
version of.

What survives is the field. An unsettled mouth has a real gradient and
the Listen reads it: conscious, deliberate, done on purpose. It is the
only warning anybody gets that a door is about to move, and the Hold is
the counter-weapon, and both exist only in children."
```

---

### Task 7: Grashing becomes an open problem

**Files:**
- Modify: `lore/cosmology/straying.md`
- Create: `lore/cosmology/the-open-problem.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the open problem as a referenceable entry for Task 8.

- [ ] **Step 1: Write the failing gate**

```python
def test_nobody_can_grash_a_door_on_purpose():
    text = (ROOT / "lore/cosmology/the-open-problem.md").read_text().lower()
    assert "nobody" in text
    for phrase in ("the mathematics", "mass", "instrument"):
        assert phrase in text, phrase
    assert "child" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k open_problem -v`
Expected: FAIL, file missing.

- [ ] **Step 3: Write it**

Create `lore/cosmology/the-open-problem.md`, new `myth-lore-` id, `category: "cosmology"`, `visibility: "player"`. Grashing is not a procedure anybody can execute; it is a question nobody can state properly, and the race to answer it is the plot. Three obstacles: **the mathematics does not exist** — nobody can predict where a mouth will go, only that it went; **the mass budget is planetary** — no station and no government can move what it would take; and **you cannot measure the inside of a mouth**, because nothing dead crosses and there has never been an instrument in a housing, so **the only probe that can go inside a door is a child.**

Then the thesis, stated plainly: the one problem humanity must solve is the one problem it is physically incapable of collaborating on, because no mind has ever met another mind and data moves at courier speed. A fifteen-year-old is the only thing that can carry a collaboration between minds that cannot meet.

`lore/cosmology/straying.md` — unchanged mechanically; it is correct. Add a closing pointer to the open problem, and make sure nothing in it implies the process can be driven deliberately.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add lore/cosmology/ tests/test_content_rules.py
git commit -m "feat(cosmology): grashing is an open problem and nobody has it

A weapon anybody can fire is background atrocity. A question nobody can
state is a race, and a race has sides, scientists, and a reason for the
player to matter -- because the only probe that can go inside a mouth is
a child, which puts the corps at the centre of the science."
```

---

### Task 8: The Quorum revised, and the Late

**Files:**
- Modify: `lore/gm-secret/the-quorum.md`
- Modify: `lore/gm-secret/acts-three-to-five.md`
- Create: `lore/gm-secret/the-late.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: the open problem from Task 7.
- Produces: the Late as a faction for Task 9.

- [ ] **Step 1: Write the failing gate**

```python
def test_the_quorum_suppresses_rather_than_grashes():
    text = (ROOT / "lore/gm-secret/the-quorum.md").read_text().lower()
    assert "suppress" in text
    assert "overwrit" in text
    assert "children cannot be overwritten" in text
    # the file currently cites a rule that does not exist in TABLE-ADDENDUM
    assert "non-lethal rule" not in text


def test_the_late_exist_and_nobody_in_them_knows():
    text = (ROOT / "lore/gm-secret/the-late.md").read_text().lower()
    assert "the late" in text
    assert "flash" in text        # identified by the cut-out flash
    assert "none of them know" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "quorum or the_late" -v`
Expected: FAIL on both.

- [ ] **Step 3: Rewrite the Quorum and write the Late**

`lore/gm-secret/the-quorum.md` — keep Sarn, the title, the lieutenants-are-him structure, the out-of-sync seam and the ending. Three changes. **He does not have the weapon:** pruning is the ambition and *suppression* is the method, which is what the shipped Act 1 and Act 2 evidence has always actually shown — a countersignature on two forms, and the same countersignature on the paperwork that enforced the silence. **Overwriting:** a pattern is written over a living adult and that person is gone; it takes hours, a room, and a subject alive and still throughout. **Children cannot be overwritten**, because a child's body is still building itself and mends around the pattern — so the only people safe from him are the only people who can carry him, a child who works it out is hunted rather than taken, and every copy is landlocked for ever because an adult cannot cross. Add the tells: he has his own memories and not the body's, so he fails on intimacy; the accent is wrong; the body rejects it slowly, so copies have a shelf life and he must keep taking people. Add the trail: his traffic is ladings, the Tally controls lading, and the shape of his network is already in Tally records with nobody reading them that way. **Delete the sentence citing "the non-lethal rule in `TABLE-ADDENDUM.md`"** — no such rule exists — and replace it with what it actually means: the Quorum is defeated by opening a door rather than by killing anybody, which is a plot shape and not a table rule.

Create `lore/gm-secret/the-late.md`, new `myth-lore-` id, `category: "gm-secret"`, `visibility: "gm"`. First-throughs aged seventeen to twenty-two, weeks or months from being landlocked, recruited with the one thing nobody else can offer: *there is something afterwards.* They are the only agents the Quorum has who can move. Identified by an absence — the Threshold flash grows into the weave and the Late cut theirs out — and they carry no lading. Grown kit: living blades and grown armour. Knacks: the Quick and the Set as standard, the Read in lieutenants, rumours of the Hold. Tactics: they arrive one at a time, never hold ground, hit and go back through the door, and nobody can pursue a child through a door except another child. Field commander **Ines Caul**, twenty-two, past it, still crossing, and it is killing her; she was Calloway's. Played at full lethality.

And §9.7: **none of them know that promotion is annihilation.** From inside it looks like the thing they were promised — the best are called up and never seen again, and the only people who could say otherwise are gone. So the player can find out first, telling a Late the truth is a weapon that works where violence does not, and it lands hardest on Rill.

`lore/gm-secret/acts-three-to-five.md` — update to match: the race for the science rather than an ongoing atrocity, and the Second Hand has a face that is not him.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add lore/gm-secret/ tests/test_content_rules.py
git commit -m "feat(quorum): he suppresses the science, and the Late do his walking

The shipped evidence never showed him killing a door. It showed a
countersignature on the paperwork that killed a study -- so pruning is the
ambition and suppression is the method, and the race for the science is
the arc.

He cannot overwrite a child, so he cannot become a courier, so he has to
recruit them. The Late are what he recruits: seventeen to twenty-two,
weeks from being landlocked, bought with the only thing anybody has ever
offered them for afterwards. None of them know that promotion is being
eaten, which makes the truth a weapon that works where violence does not."
```

---

### Task 9: Sollen, the Yards resistance, and the theocracy

**Files:**
- Create: `characters/marek-sollen.md`
- Create: `characters/sabra-ode.md`
- Create: `characters/tobin-ashe.md`
- Create: `characters/ines-caul.md`
- Create: `factions/the-late.md`
- Create: `factions/sollens-faction.md`
- Create: `lore/geography/the-theocracy.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: the Late from Task 8.
- Produces: character ids referenced by Task 12's live-save work.

- [ ] **Step 1: Write the failing gate**

Read an existing character file first — `characters/` already has the session-5 cast — and copy its frontmatter shape exactly.

```python
def test_the_antagonists_exist_with_actor_notes():
    import pathlib
    needed = {
        "characters/marek-sollen.md": ("WANTS", "PRESSURE", "KEY"),
        "characters/sabra-ode.md": ("WANTS", "PRESSURE", "KEY"),
        "characters/tobin-ashe.md": ("WANTS", "PRESSURE", "KEY"),
        "characters/ines-caul.md": ("WANTS", "PRESSURE", "KEY"),
    }
    for rel, fields in needed.items():
        p = ROOT / rel
        assert p.exists(), rel
        text = p.read_text()
        for f in fields:
            assert f in text, f"{rel} has no {f}"


def test_no_card_contains_a_rules_word():
    """TABLE.md: nothing on a card may contain a skill name, a number, or a
    rules word."""
    banned = re.compile(r"\b(d100|skill|roll|hit points|action points)\b", re.I)
    for p in sorted((ROOT / "characters").glob("*.md")):
        _, body = parse_frontmatter(p.read_text())
        for n, line in enumerate(body.splitlines(), 1):
            assert not banned.search(line), f"{p.name}:{n}: {line.strip()}"
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "antagonists or rules_word" -v`
Expected: FAIL, four files missing.

- [ ] **Step 3: Write the cards and the factions**

`characters/marek-sollen.md` — the card is written in full in spec §9.2; copy it. **LOOKS** sixties, big through the chest, plainly and expensively dressed, a voice that fills a hall without a system, never touches anybody and never needs to. **CORE** children are children, the galaxy has been handed to them by negligent adults, and he is the only man with the spine to say so. **NATURE** hearty, genuinely funny on a platform, remembers your name and your mother's name and uses both; likes being liked, likes being obeyed more. **WOUND** he was never taken — tested, not chosen, then aged out of eligibility. **WANTS** the corps under his hand, legally, with an attestation on it, and to be thanked. **PRESSURE** gets loud and personal; addresses a fifteen-year-old as though they were seven, in public, and cannot stop himself. **KEY** *"Somebody has to be the grown-up."*

`characters/sabra-ode.md` — seventeen, best of her generation, nearly out of career, leads the Yards resistance. It must be a child structurally: she can reach other systems and every adult around her physically cannot.

`characters/tobin-ashe.md` — instructor at the Yards who covers for her; the man who gave Lint the van Maanen's door and asked nothing back.

`characters/ines-caul.md` — twenty-two, field commander of the Late, past it and still crossing, and she was Calloway's.

`factions/sollens-faction.md` — political, not military: votes, committees, strikes, smuggled children, and a school quietly refusing. His argument is popular and partly correct, which is what makes him dangerous rather than merely hateful.

`factions/the-late.md` — the faction entry pointing at `lore/gm-secret/the-late.md`.

`lore/geography/the-theocracy.md` — a system with ground and millions of people, cut off about three centuries ago, returned within living memory because a grashed mouth can stray back out of rock. **Its god is its system mind.** It has a congregation, three hundred years of grievance, and nobody knows what it has. And it is the precedent: the last time a door came back out of the rock, *that* came through it. **The star is Teegarden's Star**, which is already in `data/systems.json` with its sources: a very old, very dim red dwarf about twelve light years out with two temperate roughly Earth-mass planets, which is a world that can hold millions and a sky that barely moves. It holds **one door**, so a single grash cut it off completely — which is why it was gone for three centuries and why nobody could reach it. Task 1 already gives it 250,000,000 and 1.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add characters/ factions/ lore/geography/the-theocracy.md tests/test_content_rules.py
git commit -m "feat(antagonists): Sollen, the Yards resistance, and the theocracy

Five sessions with nobody to hate. Sollen is a totalitarian populist and
an old-fashioned schoolmaster bully whose argument is popular and partly
correct, which is the worst kind. The Yards resist him, led by a
seventeen-year-old, because she can reach other systems and every adult
around her physically cannot.

And a theocracy whose god is its own system mind, back out of the rock
after three centuries -- which is the precedent that makes Kapteyn's
frightening."
```

---

### Task 10: Fix the stale cross-reference in the addendum

**Files:**
- Modify: `TABLE-ADDENDUM.md`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Write the failing gate**

```python
def test_the_addendum_still_says_danger_is_real():
    """This file was twice described in design notes as carrying a non-lethal
    rule. It does not and never did, and it must not acquire one."""
    text = (ROOT / "TABLE-ADDENDUM.md").read_text()
    assert "Danger is real" in text
    assert "The player's character can die" in text
    assert "a risk the player could see when they chose it" in text


def test_nothing_in_the_repo_claims_a_non_lethal_rule():
    bad = []
    for p in all_content_files() + [ROOT / "TABLE-ADDENDUM.md"]:
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if re.search(r"non-?lethal rule", line, re.I):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -k "addendum or non_lethal" -v`
Expected: the first PASSES already; the second FAILS on `lore/gm-secret/the-quorum.md` if Task 8 has not run, and otherwise passes. Run it anyway — it is the regression gate.

- [ ] **Step 3: Add the Late to the addendum**

`TABLE-ADDENDUM.md` §1 is correct and is not to be softened. Add one short paragraph under it: the Late are played at full lethality, and the duty applies to them exactly as to everything else — name the danger in the fiction before it is live, never a lethal surprise, and a death gets its weight.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: PASS, all.

- [ ] **Step 5: Commit**

```bash
git add TABLE-ADDENDUM.md tests/test_content_rules.py
git commit -m "docs(table): there was never a non-lethal rule, and now there is a gate

Two design drafts asserted that this file carried one. It says the
opposite, in a section headed 'Danger is real'. The gate stops the claim
coming back, and the Late are written in at full lethality under the duty
that already governs everything else: no death from a risk the player
could not see when they chose it."
```

---

### Task 11: Sweep everything else

**Files:**
- Modify: whichever files the gates name, across `guide/`, `beats/`, `agendas/`, `facts/`, `locations/`, `setting/`, and the remaining `lore/`
- Test: `tests/test_content_rules.py`

**Interfaces:**
- Consumes: every gate written in Tasks 1–10.
- Produces: a tree that passes all of them.

- [ ] **Step 1: Write the failing gate**

```python
V1_TONE = re.compile(
    r"\b(counting house|politically powerless|underfunded charity"
    r"|chalk|slate|brown paper|lamp log|rota sheet|requisition log"
    r"|torn out|pinned to the wall)\b", re.I)


def test_no_v1_tone_survives():
    bad = []
    for p in all_content_files():
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if V1_TONE.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_tech_level_is_stated_somewhere_positively():
    """Spec section 2. Sweeping low-tech references out is not the same as
    saying what the tech level now is, and the thing that made this setting
    feel wrong was an absence rather than a presence."""
    text = (ROOT / "lore/player-briefing/the-causeway-in-one-page.md").read_text().lower()
    assert "no signal" in text
    for phrase in ("inside a system", "mind"):
        assert phrase in text, phrase


def test_no_system_is_described_as_nearly_empty():
    """van Maanen's with two staff was the line that broke the setting's
    credibility. Populations live in data/systems.json and the prose must
    not contradict them."""
    bad = []
    tiny = re.compile(r"\b(two (?:people|staff)|a staff of two"
                      r"|nobody (?:lives|visits) (?:here|there))\b", re.I)
    for p in all_content_files():
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if tiny.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_content_rules.py -v`
Expected: FAIL, with a list of every remaining offender across the tree. That list is the task.

- [ ] **Step 3: Widen every scoped gate, then work the list**

First, change `content_files(FIRST_PASS_DIRS)` to `all_content_files()` in
`test_there_is_no_paper_left_in_the_causeway`,
`test_fetches_are_never_described_as_livestock` and
`test_the_cold_arm_is_gone`, and re-run. Those three gates were scoped to
`lore/` and `factions/` by the pre-flight ruling so that earlier tasks were
not blocked by files they did not own; this is where they go tree-wide and
the rest of the tree gets fixed.

Then work the list.

Fix each named file. Three rules while sweeping: keep the frontmatter `id` untouched; where a scene turns on a physical object that no longer exists, replace the object rather than deleting the scene — a report becomes a finding in the corpus, a pinned sheet becomes something a fetch holds, a signed form becomes an attestation; `earth.md` specifically needs its "quietly managed downward for nine hundred years" framing replaced per spec §1, because it is the single greyest page in the repository; and `lore/player-briefing/the-causeway-in-one-page.md` must state the tech level positively per spec §2 — a full high-tech civilisation inside every system, with no signal of any kind across a door — because that page is the first thing a new player reads and it currently implies the opposite.

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest tests/ -v`
Expected: PASS, all — including `test_guide.py`, `test_plugin.py`, `test_portability.py`, `test_powers.py`, `test_roundtrip.py` and `test_seed.py`, which must not have been broken by any of this.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix(tone): sweep the last of v1 out of the tree

The gates name the files; this is the list worked. Every scene that turned
on a piece of paper now turns on the thing that replaced it, because
deleting the object and leaving the scene is how a beat becomes unrunnable."
```

---

### Task 12: Propagate into the live save and verify from the graph

**Files:**
- Modify: the live campaign `myth-campaign-first-through-s1` via the `mythras-gm` CLI
- Create: `scripts/sync-lore.sh`

**Interfaces:**
- Consumes: every rewritten lore file.
- Produces: a graph whose entries match the files.

**This is the task whose absence caused session 5.** The v2 rewrite converted half the files and never re-imported, so the GM narrated out of v1 text for months. Do not mark it complete on the strength of the files being right.

- [ ] **Step 1: Write the sync script**

The live campaign cannot be re-imported — importing a package next to a live save forks it — so each changed entry is pushed with `update-lore`, matched on the frontmatter `id`.

```bash
#!/usr/bin/env bash
# Push every lore file's current body and summary into the live save.
# Matches on the frontmatter id, so a file whose id changed will fail loudly
# rather than silently creating a duplicate.
set -euo pipefail
: "${GM:?set GM to the engine directory}"
CAMPAIGN="${1:-myth-campaign-first-through-s1}"
for f in lore/*/*.md; do
  id=$(python3 -c "
import sys,json,re
t=open(sys.argv[1]).read()
m=re.match(r'^---\n(.*?)\n---\n?', t, re.S)
print(json.loads(dict(
  (k.strip(), v.strip()) for k,_,v in
  (l.partition(':') for l in m.group(1).splitlines() if ':' in l)
)['id']))" "$f")
  body=$(python3 -c "
import sys,re
t=open(sys.argv[1]).read()
print(re.sub(r'^---\n.*?\n---\n?', '', t, flags=re.S).strip())" "$f")
  uv run -q --project "$GM" python "$GM/mythras_gm.py" update-lore \
      --id "$id" --narrative "$body" >/dev/null
  echo "synced $id  $f"
done
```

- [ ] **Step 2: Run it against the live campaign**

```bash
export GM="$HOME/.claude/plugins/synced/"*"/mythras-gm/skills/mythras-gm"
chmod +x scripts/sync-lore.sh && ./scripts/sync-lore.sh
```
Expected: one `synced` line per lore file, no errors. Any `No lore 'myth-lore-…'` means an id was changed during the rewrite — find it and fix the file, do not create a new entry.

- [ ] **Step 3: Verify by reading back out of the graph, not the files**

```bash
for id in myth-lore-a47dd64a96ab myth-lore-8770c99bc8be myth-lore-5f0e076b4984; do
  uv run -q --project "$GM" python "$GM/mythras_gm.py" get-lore --id "$id" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['lore']['content'][:400])"
done
```
Expected: `what-crosses-easily` describes the weave and mentions no dressing room; `earth` is not "quietly managed downward"; `the-tally` mentions lading and no counting house. **If any of these still reads as v1, the sync did not take and this task is not done.**

- [ ] **Step 4: Log the retcons into the live journal**

Retract the two mid-session notes that recorded the superseded what-crosses ruling, and log one `gm-note --visibility meta` pointing at the spec and listing the six reconciliations from spec §11: kit crossed and Calloway's lines were attested aloud; the cold arm is a field, not an affliction; Orsk's book was the hall's own record; Sep's reports are a finding in the corpus; BlingBling witnessed Kapteyn's and chooses what to share; and the Listen surfaces in Lint in session 6.

Also update `world_constraints` via `update-campaign --staging-notes` so it matches spec §4 and §5 rather than the mid-session text.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync-lore.sh
git commit -m "feat(sync): push lore into the live save, and verify from the graph

The v2 rewrite converted half the files and never re-imported, so the GM
narrated out of v1 text for months and the player spent a session in a
setting the repo had already replaced. A live campaign cannot be
re-imported without forking it, so this pushes per entry on the
frontmatter id.

The verification step reads back out of the graph rather than the files,
because the files being right is exactly what was true the whole time."
```

---

## Done when

`uv run pytest tests/ -v` passes, `./scripts/sync-lore.sh` runs clean, and three entries read back out of TypeDB in v3 voice. Then the gazetteer gets its own spec: twenty-seven systems on the eight axes in spec §13, with `data/systems.json` already holding the astronomy.
