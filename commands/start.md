---
description: Begin First Through — brief a new player, import the scenario, pick an entry point and a character, and open the first scene.
---

# Start First Through

The zero-state path. Use this when the campaign has never been played on this
machine. **If a game is already in progress, stop and use `/mythras-gm:play`
instead** — step 4 checks, and it matters, because a start command that resets
somebody's campaign is worse than no start command at all.

Resolve the engine first; everything below needs it:

```bash
. "${CLAUDE_PLUGIN_ROOT}/scripts/engine.sh"   # sets GM_ROOT, GM_SKILL, GM_CLI, gm()
[ -z "$GM_ROOT" ] && echo "mythras-gm is not installed: /plugin install mythras-gm@fourth-wall-gaming"
```

## 1. Is this their first roleplaying game? Brief them first

**Ask. Do not assume.** If they have played before, say so in a line and move on.

If they have not, read `lore/player-briefing/first-through-the-sixty-second-briefing.md`
and give it **in your own words**, in about a minute. Three things and then stop:
their skills are numbers out of a hundred and they roll under them; fights are
short and avoidable and nobody dies; and Passions are the good bit.

Do this **before** they choose a character. Knowing that Passions matter changes
which one they pick, and a player who has been told *you do not need to learn
any rules* relaxes.

Do not read them the rulebook. There is no rulebook to read.

## 2. Read `TABLE-ADDENDUM.md` before the first roll

Three rules specific to this campaign, and all three change how you run it:

- **Incapacitation, never death, in both directions.** Mythras unchanged; the
  fiction resolves fatal wounds as knockouts, capture and being dragged clear.
  This is the one that protects a child's first character from one bad exchange.
- **When the player goes quiet, Tolk speaks** — never a menu.
- **The player always chooses the special effect.**

## 3. The engine and the database

```bash
gm init-db                                   # idempotent; stop and report if it fails
```

If this fails, say so plainly, do not narrate, do not roll, and do not tell the
player anything was saved. Offer `/mythras-gm:setup`.

## 4. Check the state of the save

```bash
gm get-campaign --campaign myth-campaign-first-through-s1
```

- **Not found** → carry on to step 5 and import.
- **Found with `myth-session-number` of 0** → already imported, never started.
  **Skip step 5.**
- **Found with a session number above 0** → a game is in progress. **Stop.**
  Tell the player what clock it is at and hand them `/mythras-gm:play`.
  **Do not import**, do not re-seed, and do not offer to start over unless they
  ask in so many words.

## 5. Import

```bash
gm import-campaign --path "${CLAUDE_PLUGIN_ROOT}" --new-ids
```

Note the campaign id it returns; everything after this uses it.

## 6. The opener is light, and the hard thing comes on day two

**Do not open on the emergency.** The first session is a morning in a ready room:
a kettle argument, somebody's fetch being impossible, Calloway pleased to see
them, one short crossing that works. The player learns the job by doing it while
nothing is wrong, and learns the setting by living in it for an hour.

The hard one is `how-many` (`lore/entry-points/how-many.md`) and it arrives on
**d1**, after the light beats have landed: a door at the Nine starts stuttering,
sixty-one people are behind it, nineteen of them children, and adults cannot be
carried. Pitch it then, in two sentences, and not before:

> *A door at the Nine has started stuttering, which means it is going to move.
> There are sixty-one people on the far side of it and nineteen of them are
> children, and you are the only person on this station who can bring anybody
> back.*

Act I's beats are already staged in the save in that order. Run `gm list-beats`
and follow them; do not reach for `how-many` early because the table has gone
quiet.

## 7. Build a character — three stages, out loud

**There are no pre-gens. Every character is built at the table, every time.**
Defining your own person is most of the point of a first roleplaying game, and a
handed-over sheet skips it. Do not run `spawn` (it makes an NPC and discards
Passions and powers) and there is no `--template` flag on `create-character`.

Work through it **one stage at a time**, letting them choose at each step and
saying the running totals out loud. It takes twenty minutes and it is the best
twenty minutes of the session.

**Who they are first, numbers second.** Name, age (fifteen is the default and the
reason they are allowed through a door at all), where they grew up, and what
their fetch is — `lore/character-creation/your-fetch.md`. The fetch is a person,
not equipment; let them name it and let it have an opinion before any dice.

**Stage 1 — Culture: 100 points.** Six cultures in
`lore/character-creation/cultures.md`: the Garden, Station-born, Holding-born,
Shelter-born, Works-born, Belt-born. Spend **100** across that culture's Standard
skills and up to three of its Professional skills.

**Stage 2 — Career: 100 points.** Six careers in
`lore/character-creation/careers.md`: Courier, Pathfinder, Doorwright, Lifeline,
Envoy, Scout-runner. Every career includes **Crossing** — that is the job. Spend
another **100** across that career's Standard skills and up to three of its own
Professional skills. A Professional skill belongs to the culture or career that
lists it; do not let one be taken from a list the character does not have.

**Stage 3 — Bonus: 150 points.** Free spend across anything already on the sheet.

**The cap is 15 points per skill per stage.** Not 15 total — 15 in each of the
three rounds, so the most any skill can reach is its base plus 45. Add them up
piece by piece in front of the player and say each number as it lands. Aim for
**somewhat specialised, not narrow**: three or four things they are good at, a
spread of things they can attempt, and nothing at 90.

**Knack and powers.** One knack, from the table in
`lore/character-creation/the-knacks.md`, which maps it to its Mythras power and
rule id. Everybody also carries Life Support, because that is the membrane suit
and not the child, with the Limit *External Power Source*. Core powers are POW +
INT; the knacks entry states the table. Leave the third slot **open** — a second
knack can surface in play, and knowing that is a gift.

**Three Passions.** Written by the player, in their words, about people and
places that exist in this setting. Then ask whether they would change one. That
single question does more for a first session than anything else in this file.

Then create them, with everything in one call:

```bash
gm create-character --campaign <id> --name "<their name>" --type pc \
  --species humanoid \
  --stats '{"STR":..,"CON":..,"SIZ":..,"DEX":..,"INT":..,"POW":..,"CHA":..}' \
  --skills '{...}' --passions '{...}' \
  --equipment '["Membrane suit", ...]' \
  --description "<age, culture, career, knack, fetch>"
```

**`create-character` takes no `--powers`.** The knack and the suit's Life Support
go on in a second call, or the sheet comes out with no powers at all:

```bash
gm update-character --id <pc-id> --powers '[{"name":"...","rule":"magic/power-...","limits":[...]}]'
```

**`--species humanoid` is not optional.** It defaults to `avian`, and a character
created without it gets wings, a Flight skill and a flying movement rate. This
has already happened once to a played character.

Then set Luck and the suit's charge full, and put them where the scene is:

```bash
gm update-character --id <pc-id> --fatigue Fresh --luck <luck_points>
gm move-character --id <pc-id> --location myth-loc-71ceb7852898   # the ready room
gm update-campaign --campaign <id> --session-number 1 --played <pc-id>
gm log-event --campaign <id> --type session-start --summary "<entry point>, <character>"
```

**`--played` matters.** Beat staging counts only the PCs somebody is actually
playing; without it every beat in the world reads as onscreen.

The fetch is a character too. Create it as an NPC with its own Passions before
the first scene, or the journal has no one to link when it does something.

## 8. Set the scene, then narrate

```bash
gm set-scene --campaign <id> --scene "<where they are, what is in front of them>"
```

**Not before.** The ready room at the Nine, Calloway standing up because they do
not sit down for this one, and Tolk on the table with opinions.

Then run the kit check as the guaranteed early success — a Very Easy call on
something they are already good at — so the first mechanics block they ever see
is one that worked.
