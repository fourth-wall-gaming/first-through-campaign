# Session 1 — paused mid-Act I

**Beat:** Act I, beat 2, *"A short one, and it goes right."* It did not go right.
**Status:** paused. Resume at bunk nineteen, Nine Station, three days before the Procyon collection.

## The character

**Lint** — called Lin — 15. `myth-char-3ca32bf47646`
Culture: the Garden (the Remainder). Career: Pathfinder. Knack: **the Quick**.
Fetch: **BlingBling**, a glint.

Skills from the full three-stage build (Culture 100 / Career 100 / Bonus 150):
Perception 57 · Athletics 56 · Evade 54 · Crossing 51 · Vacuum 45 · First Aid 44 · Combat Style 43 · Swim 40

**Condition at the pause:** Winded. Luck **2 / 3**. Fresh clouding on both forearms,
permanent. Membrane fed. Off the rota for three days by Calloway's order.

## What happened

A routine posting: cross to Procyon, collect the reader **Mina Haral**, 81, bring her home.

- Crossing out, solo — success.
- The carry — failed at Hard (76 against 44, augmented by a Passion).
- Lint chose to **push** rather than put Mina down. The push failed at Formidable (96).
- She spent a Luck Point and re-rolled 48 — still a failure, but a much better one.
- She let go in time. Both fell on the Procyon side. Mina broke a wrist and lived.

Mina forgave her, then told her she was turned back at a hall at twenty-two and has
**paid children to carry her forty-one times since**. She asked Lint to come back for
her in three days. Lint went down the corridor to apologise, which Mina said no one
else ever had.

Afterwards Lint asked BlingBling what *she* wanted, and they spent an hour in the
unfiltered light gallery on Procyon's third level — eleven glints talking in colour,
BlingBling magnificent in the best light in human space.

Then home alone, clean crossing, and the debrief. Calloway did not care about the
failed carry. She cared entirely about the push:

> "Every single one was lost because they were having a bad day and decided they
> could have it both ways."
>
> "Stopping is the skill. Not the carry. You've got it about a second slower than
> you need it."

## Open threads

- **Mina Haral**, Procyon infirmary, to be collected in three days. Lint promised.
- Calloway now knows about the forty-one paid crossings. Her passion *Nobody uses my kids* is 80.
- Mina intends to tell Calloway it was her own fault and her own figures. It wasn't.
- BlingBling had the best light in human space and then came back to sit in the
  dead grey of bunk nineteen. That's the friendship; it should pay off later.
- Lint swore in front of Mina Haral. Calloway expects this to follow her for forty years.

## Engine note

`update-campaign` is broken upstream — `cmd_update_campaign` reads `args.staging_notes`
at `mythras_gm.py:492` but the parser never defines it, so every invocation crashes.
The arc clock was therefore not advanced through the CLI. Fix is three lines
(`--arc-file`, `--played`, `--staging-notes` on the subparser) and has not been authorised.
