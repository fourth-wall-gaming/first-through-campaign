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

## The two books

The campaign ships as a website with a book on each side of the screen, built
from the campaign files by `guide/build.py` and published to GitHub Pages:

- **The Players' Guide** — everything a first-through already knows, with no
  spoilers in it.
- **The Games Master's Guide** — the physics, the cast, Act One beat by beat,
  how to run it for a young player, and full statistics. Contains the ending.
- **What Actually Happens** — a page for a parent, with a novel transcribed
  from a real four-day run of the game attached to it.

```bash
uv run --with pyyaml --with pillow python guide/build.py   # writes _site/
```

Chapters are hand-written markdown in `guide/gm/` and `guide/players/`.
Anything with a number in it comes out of the campaign files through a
directive on a line of its own -- `<!-- roster -->`, `<!-- timeline -->`,
`<!-- agendas -->`, `<!-- areas -->`, `<!-- statblocks: major -->`,
`<!-- lore: lore/....md -->` -- so the books cannot drift from the game.

## Install

```
/plugin marketplace add fourth-wall-gaming/mythras-gm
/plugin install first-through@fourth-wall-gaming
/first-through:start
```

The engine arrives with it. You do not need to read anything first — the start
command briefs a new player in about a minute and then you are playing.

## How it opens

The first session is light. A morning in the ready room at the Nine: a kettle
argument, somebody's fetch being impossible, Calloway pleased to see you, and
one short crossing that works. You learn the job by doing it while nothing is
wrong.

Then, on day two, **How Many** — a door at the Nine starts stuttering, sixty-one
people are behind it, nineteen of them are children, and adults cannot be
carried. One sitting, winnable, and it will cost.

## You build your own first-through

There are no ready-made characters. The start command walks a new player through
the whole thing out loud in about twenty minutes: where you grew up, what you
trained as, what your knack is, who your fetch is, and the three things you care
about enough to fight for. Six cultures, six careers, and a spend of 100 / 100 /
150 points across three stages.

Defining your own person is most of the point of a first roleplaying game.

## Danger is real

People die in this campaign, including yours. The Mythras rules are unmodified
and nothing is softened behind the screen.

What the campaign promises instead is **information**: a character can only die
from a risk that was named, in the fiction, before the player chose it. No
unannounced trap, no ambush from a direction you had no way to check, and an
honest answer every time you ask whether something can kill you.

The tollkeepers carry shock batons and restraint loops and no blades, because a
body is not a line on a manifest. That makes the professionals the safest people
you will meet, and the frightened civilians and the physics the dangerous ones.

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
