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
short and usually avoidable, and they will always be told how dangerous
something is before they choose it; and Passions are the good bit.

Do this **before** they choose a character. Knowing that Passions matter changes
which one they pick, and a player who has been told *you do not need to learn
any rules* relaxes.

Do not read them the rulebook. There is no rulebook to read.

## 2. Read `TABLE-ADDENDUM.md` before the first roll

Three rules specific to this campaign, and all three change how you run it:

- **Danger is real, and it is always named before it is taken.** **People die in
  this campaign** — NPCs, and the player's character — and the Mythras rules are
  unmodified. What protects a child's first character is information, not
  immunity: *a character may die only from a risk the player could see when they
  chose it.* So name the danger out loud, in the fiction, **before** they commit;
  never spring a lethal surprise; answer *can this kill me* with a straight yes
  or no; and say once, early and out of character, that they have **Luck Points**
  and can spend them. A death gets its weight — let it land, and do not soften it
  afterwards into a coma.
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

## 6. The opener is light, and nobody is told there is a crisis

Two rules, and they are the two that decide whether this campaign is any good.

### Rule one: the first day is social, and it is not throat-clearing

A morning in the ready room — a kettle argument, somebody's fetch being
impossible, Calloway pleased to see them — then one short crossing that works,
then a game of sling in the gallery void. Nothing is wrong. Nobody is in danger.

The player learns the job by doing it while it works, and learns the setting by
living in it for an hour, and meets five people.

**Those five people are load-bearing.** Every relationship made on the quiet day
is structural later: the kid who keeps the board, the deck engineer who controls
which shutters open, the fathom nobody talks to, the nineteen-year-old who is
better than you, the twenty-one-year-old who is nearly finished. Do not rush
this to get to the plot. This *is* the plot, arriving early and in disguise.

### Rule two: do not hand over the emergency

The crisis — `how-many` — is **already running
in the world** on a clock before the player touches it, and **they find it.**

Read `lore/entry-points/how-many.md` section 1 and
`lore/gm-guide/running-a-staged-crisis.md` before you run any of it. The short
version:

- Stage the beats on the clock with `add-beat --when`, and `tick` the world
  whether or not the party is present.
- Put every piece of evidence in **public** — a number on a board in the hall, an
  unopened file in a records office, a frightened shift worker in a queue.
  Nothing hidden, nothing gated behind a roll.
- Several ways in, keyed to what the character is actually good at. Reading,
  anchor hardware, people, bodies, moving, or simply **asking the Old Man**, who
  hands over every fact he has the moment somebody puts a question to him.
- **Then do not point at it.** No nudges, no significant pauses, no NPC raising
  an eyebrow at a door number. Answer what they look at.

### Ground them early. It is the best move available to you.

If the player's first crossing goes badly — and the first one often does — take
them off the rota for a day or three. Not as a punishment: it is what any
director who has lost people does without being asked.

A first-through with a day to fill and a station to walk around is the single
most reliable way into this scenario, and everything they find that way is
something they chose to look at.

### And the clock stops the table stalling

Refusing to offer is not the same as nothing happening. `how-many` section 1
carries the escalation ladder: the transit time rises every watch, the queue
shuts, Ladder's supply run fails, and at the bottom of the timer **it comes to
them** — Calloway puts them on it in the ready room with the number and the
stakes in one breath.

So the hand-over scene still exists. It is the fallback, not the default. And if
the player got there first, they walk into that room already knowing more than
Calloway does, which is a much better scene than the one where she tells them.

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
rule id. Everybody also carries Life Support, because that is the weave
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
  --equipment '["Weave", ...]' \
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
