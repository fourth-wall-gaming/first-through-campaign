---
name: first-through
description: The First Through campaign for mythras-gm — a first roleplaying game for 10-15 year olds, set in the real stellar neighbourhood, where doors between stars were carried out at a twentieth of lightspeed and only the young can cross. Use when the user wants to play, start or continue First Through, or asks about the Threshold, the Nine, crossings, fetches, anchors or the failing doors.
---

# First Through

A campaign package for the **mythras-gm** engine. This skill is not a second GM
manual — the engine owns how to run a table (`TABLE.md`) and this owns the four
things the engine structurally cannot know.

## 1. Where this campaign's files are

`$FT` is this package's root. The preflight prints it as
`FIRST_THROUGH_ROOT=<path>` at session start; failing that it is the directory
two levels above this `SKILL.md`. A plugin-root environment variable is not it —
your host sets one for hook commands only, never in your shell.

```bash
. "${FT}/scripts/engine.sh"    # sets GM_ROOT, GM_SKILL, GM_CLI and a gm() shell function
```

| what | where |
|---|---|
| the arc, act by act | `${FT}/setting/story.md` |
| **the three rules that change how you run it** | `${FT}/TABLE-ADDENDUM.md` |
| the one-minute player briefing | `${FT}/lore/player-briefing/` |
| the entry points | `${FT}/lore/entry-points/` |
| building a character at the table | `${FT}/lore/character-creation/` |
| running the crisis on a clock | `${FT}/lore/gm-guide/running-a-staged-crisis.md` |
| beat texts | `${FT}/beats/` |

## 2. The campaign id

`myth-campaign-first-through-s1`. A first run needs the **`first-through-start`**
skill (`/first-through:start` in Claude Code), which imports it. If
`get-campaign` on that id returns a session number above 0, a game is in
progress: resume it with the **`mythras-play`** skill and do not import anything.

## 3. Read the addendum before the first roll

`${FT}/TABLE-ADDENDUM.md` carries three rules specific to this campaign, and all
three change how you run it. The first is the one that matters most, because the
player may be ten years old:

**Danger is real, and it is always named before it is taken.** People die in
this campaign — the player's character included — and the Mythras rules are
unmodified. What protects a child's first character is information, not
immunity: *a character may die only from a risk the player could see when they
chose it.* Name the danger out loud before they commit, never spring a lethal
surprise, answer *can this kill me* with a straight yes or no, and make sure they
know they have Luck Points. A death gets its weight; do not soften it afterwards
into a coma.

The other two: **when the player goes quiet, Tolk speaks** — never a menu — and
**the player always chooses the special effect.**

## 4. This campaign's own conventions

- **There are no pre-generated characters.** Every character is built at the
  table, three stages out loud: Culture 100 points, Career 100, Bonus 150, with a
  cap of 15 per skill per stage. Defining your own person is most of the point of
  a first roleplaying game. The `first-through-start` skill carries the whole
  procedure.
- **Keep `--species humanoid` on `create-character`.** It is the engine's
  default now, so this is belt and braces rather than a trap — but it used to
  default to `avian`, because the engine was written for a sky realm, and a
  played character got wings, a Flight skill and a flying movement rate before
  anyone noticed.
- **A fetch is a person, not equipment.** Create it as an NPC with its own
  Passions, or the journal has nobody to link when it acts.
- **The opener is light and nobody is told there is a crisis.** The first day is
  social and that *is* the plot arriving early in disguise. The crisis runs on a
  clock in the world and the player finds it; do not hand it over.

## Entry points

| skill | slash command (Claude Code) | when |
|---|---|---|
| `first-through-start` | `/first-through:start` | first run: brief, import, build a character, open the scene |
| `mythras-play` | `/mythras-gm:play` | every session after that |
| `mythras-setup` | `/mythras-gm:setup` | once per machine, if the database is not up |

Name the **skill** when you tell a player what to do next. The slash commands
exist only in Claude Code; in Codex there is nothing to type.
