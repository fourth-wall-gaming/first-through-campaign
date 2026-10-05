# First Through

**A Mythras Imperative campaign for [mythras-gm](https://github.com/fourth-wall-gaming/mythras-gm)
— a first roleplaying game for 10-15 year olds, set in the real stellar
neighbourhood. Nobody dies.**

Nine hundred and seventy-five years ago an earlier, richer human expansion
launched robotic seedships at a twentieth of lightspeed, each carrying one half
of an anchor pair. Where a ship arrived and woke, a door opened. **That is the
only way between stars.** Transit through a paired anchor is instantaneous;
everything else obeys the speed of light, including radio.

So the inhabited galaxy is a **graph, not a volume**. A star two hundred light
years off can be one step away while its nearest neighbour is unreachable.
Nothing outruns a person, so news travels at the speed of a courier walking
through a door. And the moment you step through, **nobody can reach you** —
your handler briefs you on this side and cannot follow, cannot call, cannot
help.

You are a **first-through**: fifteen, the youngest the Threshold has taken in
years. The old doors are failing faster than age explains. And the one
everybody has waited nine centuries for opens next year.

## Install

```
/plugin marketplace add fourth-wall-gaming/mythras-gm
/plugin install first-through@fourth-wall-gaming
/first-through:start
```

The engine arrives with it. You do not need to read anything first — the start
command briefs a new player in about a minute and then you are playing.

## Two ways in

Pick one at `/first-through:start`. Both are one sitting, both end in the same
place, and both can be finished by any of the four characters.

- **The Quiet Door** — A farming settlement's only door has started stuttering,
  and there are four thousand people on the far side of it. Investigation,
  machinery and persuasion; there is one confrontation and you can avoid it
  entirely.
- **Flare** — A refinery crew have barricaded their own corridor, their shelter
  is on the far side of it, and the two stars above them are about to do what
  flare stars do. A real fight on a real clock, with the special effect always
  yours to choose.

## Four first-throughs

**The Runner** gets there. **The Tinker** opens things. **The Talker** gets
invited in. **The Fieldhand** knows what is alive. No building, no arithmetic —
pick one and read the three things your character cares about.

## Nobody dies

A character at death's door is knocked out, captured or dragged clear, never
killed — and the rule runs in both directions, so you are never put in a
position where killing is the expected solution. The Mythras rules are
completely unchanged; this is a convention in the fiction, and the setting
supplies the reasons: a hull is thin, a station is a closed volume, a corpse is
paperwork nine light years long, and the tollkeepers want you alive because a
body is not a line on a manifest.

Losing means you are on the floor and tied, with your kit in a locker. That is
a real defeat. It is just not a dead child's first character.

## The astronomy is real

Every system, star type, planet, distance and oddity in this campaign is a real
and current fact, cited in the lore. We invent only what people built there.

`data/systems.json` is the authority: distances computed from SIMBAD parallaxes,
and every door date derived from the setting's one load-bearing sum — **transit
time is distance in light years times twenty.** If the prose and the data
disagree, the data wins and the prose is a bug. There is a test for it.

The map is Alpha Centauri and Barnard's four scorched pebbles; the brown dwarfs
of Luhman 16 with weather and no sun at all; the water-ice clouds of
WISE 0855; the twin flare stars of Gliese 65; the habitable-zone super-Earths
confirmed at GJ 887 in March 2026 and at Gl 725 in August 2026; the radio
aurorae of YZ Ceti, which gave us the first measurement of a planet's magnetic
field; and van Maanen's Star — the nearest solitary white dwarf, visibly eating
the wreckage of its own planets.

Nine doors meet at Sirius, and eight of them are simply Sirius's nearest
neighbours. Sol holds seven. That is how the old country became the old country.

The frontier is a sphere 48.75 light years out, moving one light year every
twenty years, and it is about to reach **LHS 1140** — genuinely the best rocky
habitable-zone planet anybody has found. Its ship has been flying for nine
hundred and seventy-six years. Do the subtraction.

Invented life is the one exception, and it is constrained: only on genuinely
unobserved surfaces, only consistent with the real system's temperature,
insolation and tidal locking, and always flagged in the lore.

## Scope

**v1 is Acts 1-2** — both entry points, playable through to the van Maanen's
Star reveal. Acts 3-5 are documented in `lore/gm-secret/` as outline.

## For GMs

Start with `CLAUDE.md`, then `TABLE-ADDENDUM.md`, then `lore/gm-guide/`.

```bash
uv run --with pytest pytest tests/ -q
```

## Licence

MIT for the content. Game mechanics are based on the *Mythras Imperative* SRD
and used under the ORC License.

> This product is based on *Mythras Imperative*, Written by Pete Nash and
> Lawrence Whitaker, and published by The Design Mechanism, Copyright 2023.
> *Mythras* and *Mythras Imperative* are Reserved Material of The Design
> Mechanism.

The setting (the Causeway, the Threshold, the Tally, and this repository's
characters and story) is Reserved Material of its authors under the ORC
framework, and simultaneously released under MIT — use it freely with
attribution.
