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

## 6. The opener

There is one, and it is `lore/entry-points/how-many.md`. Read it and its guide,
`lore/gm-guide/running-how-many.md`, before you narrate anything.

Pitch it to the player in two sentences and no more:

> *A door at the Nine has started stuttering, which means it is going to move.
> There are sixty-one people on the far side of it and nineteen of them are
> children, and you are the only person on this station who can bring anybody
> back.*

Then stop talking and let them pick a character.

## 7. Offer the four pre-gens

One line each, from `lore/character-creation/choosing-a-first-through.md`:

- **The Runner** — gets there. Climbs, carries, and has never been the slowest
  person in a room.
- **The Tinker** — opens things. Can tell a dying anchor from a sulking one.
- **The Talker** — gets invited in. Reads people fast and is usually right.
- **The Fieldhand** — knows what is alive. Raised behind a single door and has
  watched people decide not to pack.

Say plainly: **all four can finish either mission, and none of them has to hurt
anybody.** They are not picking a difficulty setting.

**They already exist in the save.** The four pre-gens import as real PCs, with
their Passions and their kit and their powers, so there is nothing to build and
nothing to roll. The player is choosing a person, not generating one.

Do **not** run `create-character` and do **not** run `spawn`. There is no
`--template` flag on `create-character`, and `spawn` makes an NPC and throws
away Passions and powers -- which are the two things these characters are made
of.

Find their ids:

```bash
gm list-characters --campaign <id> --type pc
```

Then put the chosen one where the scene is, and post the other three elsewhere:

```bash
gm move-character --id <chosen-pc-id> --location myth-loc-71ceb7852898      # the ready room
gm move-character --id <other-1> --location myth-loc-2c575cc45375            # the Yards, 61 Cygni
gm move-character --id <other-2> --location myth-loc-2c575cc45375
gm move-character --id <other-3> --location myth-loc-2c575cc45375
```

The three they did not pick are **not deleted**. They are the rest of the
intake, on other postings, and the world engine stages beats from recorded
presence -- so moving them to the Yards is what keeps them out of the player's
scenes while leaving them available to turn up at the Nine between missions. Say
that to the player. It makes the choice feel less like a door closing, and it is
true.

Let them rename their character if they want to. Then read them their three
Passions and ask whether they would change one -- that single question does more
for a first session than anything else in this file.

```bash
gm update-campaign --campaign <id> --session-number 1
gm log-event --campaign <id> --type session-start --summary "<entry point>, <character>"
```

## 8. Set the scene, then narrate

```bash
gm set-scene --campaign <id> --scene "<where they are, what is in front of them>"
```

**Not before.** The ready room at the Nine, Calloway standing up because they do
not sit down for this one, and Tolk on the table with opinions.

Then run the kit check as the guaranteed early success — a Very Easy call on
something they are already good at — so the first mechanics block they ever see
is one that worked.
