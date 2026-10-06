# First Through — campaign design

**Date:** 2026-10-05
**Status: SUPERSEDED** by `2026-10-06-first-through-v2-design.md`.
Kept as the design record of the first pass. Its premise (doors fail, nobody
dies, powers are kit, fetches are a companion animal, the Tally is quietly
sinister) was replaced wholesale in play-testing; see v2 section 11 for the
audit of what changed and why.

**Original status:** Design approved in conversation; awaiting written-spec review
**Target repo:** `fourth-wall-gaming/first-through-campaign` (installs as plugin `first-through`)
**Engine:** mythras-gm, system `mythras` (Mythras Imperative — *not* Classic Fantasy)
**Campaign id:** `myth-campaign-first-through-s1`

---

## 1. Goal and audience

A **published campaign plugin** that any 10-15 year old can install and play
solo, with Claude as Gamesmaster. Its primary job is to be **a good first
roleplaying game** — the science-fiction setting is the hook and the texture,
not a lesson.

Inspiration is Douglas Hill's *Last Legionary* books: a young, trained
operative sent out alone into trouble, a handler who briefs them, a companion
who talks back, and missions that resolve in a sitting. We inherit the shape,
never the proper nouns (see §3).

Success means a kid who has never played an RPG can install it, be playing
inside five minutes, finish a first mission in one sitting, and come back.

## 2. Non-goals

- **No engine changes.** `mythras_engine.py` and the rules layer are untouched.
  Everything here is campaign content plus table guidance.
- **No new novelization styles**, no dashboard, no schema changes.
- **Not a physics curriculum.** The science must be true, but the campaign
  never stops to teach it.
- **Not a group campaign.** Designed for one player. It should not *break* with
  two or three, but solo is the target.

## 3. Content rules (hard constraints)

These are binding on every lore entry, location, NPC and scenario we write.

1. **The astronomy is real and current.** Every system, spectral type, planet,
   distance and physical oddity is a real, cited fact. We invent only what
   *people built there*. If a player looks up Teegarden's Star, everything the
   game told them checks out. Sources go in each lore entry's frontmatter.
   **Invented life is the one exception, and it is constrained — see §12.**
2. **No Douglas Hill intellectual property.** No Keill Randor, Glr, Moros,
   Veynaa, Overseers, Deathwing, or the Warlord. We inherit structure only.
3. **Incapacitation, not death — in both directions.** The player's character
   is knocked out, captured, or dragged clear rather than killed; and the player
   is never put in a position where killing is the expected solution. This is a
   tone decision as much as a safety one, and it drives the technology: stunners,
   restraints, pressure-breaching, sabotage. Mythras rules are **unchanged** —
   the convention lives in the campaign's table guidance so Claude applies it
   every time.
4. **No rules lecture.** The engine already assumes the player needn't know the
   rules, and the mechanics wall (`TABLE.md §3`) shows every roll in its own
   marked block. A newcomer absorbs percentages by watching. We add nothing to
   read before play.

## 4. The setting: the Causeway

Nine hundred and seventy-five years ago an earlier, richer human expansion —
the **First Reach** — launched robotic seedships at roughly 0.05c, each
carrying one half of an anchor pair. Where a ship arrived and woke, a door
opened. **That is the only way between stars.**

Transit through a paired anchor is instantaneous. Everything else obeys the
speed of light, *including radio*. Three consequences carry the whole setting:

- **The galaxy is a graph, not a volume.** A star two hundred light years off
  can be one step away while its nearest neighbour is unreachable. Edges exist
  only where somebody carried an anchor.
- **Nothing outruns a person.** News travels at the speed of a courier walking
  through a door. Information is the currency, and carrying it is a job.
- **Step through and you are unreachable.** Your handler briefs you on this
  side and cannot follow, cannot call, cannot help. You and whoever is with you
  are the entire response. This is the core tension of every mission.

It is a graph rather than spokes because **an anchor is a pair of independent
devices.** Every far half rode the one great launch from Sol -- which is why
`975 - 20d` holds for every system without exception -- but the First Reach did
not keep every *mate* at home. It distributed mates among its early nodes, so
where a door leads is a matter of where its other half was placed, and a link
comes into service on the date its later half lands.

The result is that Sol holds seven doors and Sirius holds nine. The old country
kept the original direct routes and the long shots to a frontier where there is
still nothing; the junction ended up at Sirius because Sirius is physically the
most central node in the neighbourhood, and eight of the Nine's edges are simply
its own nearest neighbours.

### The arithmetic

**Transit time = distance in light years × 20.** One light year per twenty
years — arithmetic a twelve-year-old does in their head, and the single most
load-bearing number in the setting.

- Launch was **975 years ago**, so the frontier is a sphere **48.75 ly** out.
- It expands at **one light year every twenty years.**
- **Gate age correlates with distance.** Near stars are the old country:
  settled, bureaucratic, mined out. Far ones are raw.

### The two crises

**The old doors are failing.** Anchors were never built to run for ten
centuries. When one dies the world behind it is not destroyed, just
*unreachable*, with everyone still on it. They are failing faster than age
explains, and nobody will say why.

**One door is about to open, on schedule, and everyone knows it.** The campaign
spine. See §10, and §11 for who does not want it to open.

### The Threshold

The service that handles both: the first step through a new anchor, and the call
when an old one goes wrong. Its field operatives are **first-throughs**. Home
station is **the Nine**, at Sirius — the junction where nine edges meet, which
is the fastest way to teach a player that this galaxy is a graph: a place
defined by how many doors it has. Sirius has no planets, so the Nine is all
station, hung in the glare of an A1V star with a white dwarf for a second sun.

## 5. The star map

The shipping map. `Opened` = 975 − (ly × 20), in years before the present.

**Figures below are the design-time values; `data/systems.json` is authoritative.**
Distances are computed from SIMBAD parallaxes as `3261.5638 / plx_mas` and the
door dates from `975 - round(ly * 20)`, so the table is regenerated from the
data rather than maintained by hand. Where a Wikipedia figure and SIMBAD
disagreed the larger discrepancies were Sirius (8.71 vs **8.60**), Gliese 65
(8.77 vs **8.87**) and Alpha Centauri (4.25 vs **4.39**); SIMBAD wins.


| System | ly | Opened | What is really there |
|---|---|---|---|
| **Sol** | 0 | launch site | The oldest launch site. The old country, sidelined. |
| **Alpha Centauri** | 4.39 | 887 yr | Triple. Proxima b in the habitable zone of a vicious flare star; Proxima d; a Saturn-mass candidate at α Cen A. The first door ever opened; old money. |
| **Barnard's Star** | 5.96 | 856 yr | Nearest single star — and four scorched sub-Earth pebbles, no habitable zone at all. A famous disappointment, now heavy industry. Largest proper motion of any star: it visibly moves. |
| **Luhman 16** | 6.5 | 845 yr | Two brown dwarfs and *no star*. Mapped storm bands, real weather. A sunless world. |
| **WISE 0855−0714** | 7.43 | 826 yr | Coldest known object outside the solar system, ~270 K, a few Jupiter masses, water-ice clouds. A dark drifter. |
| **Wolf 359** | 7.86 | 818 yr | Violent flare star, candidate planet. |
| **Lalande 21185** | 8.3 | 809 yr | Two planets, one a cold gas giant on an eight-year orbit. |
| **Sirius** | 8.6 | 803 yr | A1V glare plus the hottest white dwarf nearby. No planets, so it is all station. **Home: the Nine.** |
| **Gliese 65 (BL/UV Ceti)** | 8.87 | 798 yr | The archetypal flare stars, twinned. The sky here kills you on a schedule. |
| **Epsilon Eridani** | 10.5 | 765 yr | Young K2V with two asteroid belts and a Kuiper analogue, plus a Jupiter-mass planet. A shooting gallery. |
| **Gliese 887** | 10.72 | 761 yr | **GJ 887 d** — habitable-zone super-Earth, confirmed March 2026, around an unusually *quiet* red dwarf. Four planets total. The best real living world near home. |
| **Ross 128** | 11.01 | 755 yr | Quiet red dwarf, one temperate planet. |
| **61 Cygni** | 11.4 | 747 yr | The first star whose distance humans ever measured. Where the Threshold trains. |
| **Procyon** | 11.46 | 746 yr | F5 subgiant plus white dwarf. The largest object within 20 ly. |
| **Gl 725 (Struve 2398)** | 11.49 | 745 yr | **Gl 725 B c** — habitable-zone super-Earth, confirmed August 2026, the second-closest known. Binary red dwarfs. |
| **Epsilon Indi** | 11.87 | 738 yr | K5 primary, a confirmed cold Jupiter, and *two brown dwarfs*. |
| **Tau Ceti** | 11.91 | 737 yr | Sun-like — and a debris disk ten times ours. A good star in a shooting gallery. |
| **YZ Ceti** | 12.12 | 733 yr | Radio aurorae from star–planet interaction: the first planetary magnetic field ever measured. A system that *sings*. |
| **Teegarden's Star** | 12.5 | 725 yr | Very quiet M7 with two Earth-mass planets, both possibly habitable. |
| **van Maanen's Star** | 14.07 | 694 yr | Nearest solitary white dwarf, atmosphere polluted with iron, calcium and magnesium — it is **eating its own shattered planets**. A graveyard. |
| **Gliese 876** | 15.24 | 670 yr | Four planets in a Laplace resonance chain. A clockwork system. |
| **40 Eridani** | 16.34 | 648 yr | Triple: a K dwarf, a white dwarf, and a red flare star. |
| **TRAPPIST-1** | 40.66 | 162 yr | Seven tidally-locked planets, three in the habitable zone. The frontier jewel, opened within institutional memory. |
| **HD 69830** | 41.03 | 154 yr | Three Neptunes and a thick warm asteroid belt. A door that opened into rubble. |
| **55 Cancri** | 41.05 | 154 yr | Five planets including a lava super-Earth, plus a red dwarf companion. |
| **HD 40307** | 42.18 | 131 yr | Six super-Earths, one temperate. |
| **GJ 1214** | 47.75 | 20 yr | The famous hazy water-world sub-Neptune. The most recent door, and a cautionary precedent. |
| **LHS 1140** | 48.8 | **opens in ~1 year** | **The spine of the campaign.** The best known rocky habitable-zone planet outside the solar system; a JWST water-world candidate. Its arrival has been computed for centuries. |

**The edges are a separate deliverable.** The table above is the node set; the
network's shape is the edge list, and it is load-bearing in two ways. Sirius must
carry **exactly nine** edges or the Nine is misnamed. And because second-generation
ships launched from early nodes, an edge may only exist where its origin node's
door opened *before* the ship could have reached the far end — the arithmetic in
§4 constrains the graph, so the edge list has to be checked against it, not drawn
freehand.

Expansion room, already arithmetically placed: Ross 154, Ross 248,
Groombridge 34, EZ Aquarii, DX Cancri, Luyten's Star, Kapteyn's Star,
Wolf 1061, Gliese 1002, 82 Eridani, Gliese 581, Gliese 3378, 61 Virginis,
Wolf 1069, HD 85512.

## 6. The player, the handler, the companion

**You are a first-through**, fifteen, the youngest the Threshold has taken in
years.

**Character creation is four pre-gens, not a build.** Mythras chargen would sink
a first session, and the skill spread *is* the character here. Four
first-throughs, each a genuinely different way through a problem:

| Pre-gen | Shape | Leans on |
|---|---|---|
| **the Runner** | climbs, jumps, moves, takes hits | Athletics, Endurance, Combat Style, Brawn |
| **the Tinker** | opens, fixes, sabotages, understands anchors | Mechanisms, Engineering, Lore (anchors), Locale |
| **the Talker** | reads people, lies, de-escalates, gets invited in | Insight, Influence, Deceit, Willpower |
| **the Fieldhand** | bodies, biology, vacuum medicine, tracking | First Aid, Healing, Lore (biology), Perception, Track |

**Every scenario must be solvable by all four.** The non-lethal rule already
forces this; the pre-gen table makes it checkable.

Each ships with Passions written in, because `NEW-TO-MYTHRAS.md` is right that
Passions are the fastest route from stat block to person.

**Calloway** runs the desk at the Nine: a former first-through whose body will
not take transit any more, now sending a fifteen-year-old where they cannot
follow. That constraint *is* the relationship.

**Tolk comes with you.** Cat-sized, six-limbed, from an anchor world called
Bell. Genuinely speaks — learned language, nothing telepathic — opinionated,
and wholly indifferent to the Threshold's chain of command.

Tolk is also the **onboarding mechanism**, and this is the design's load-bearing
trick. `TABLE.md §5` forbids option menus and forbids narrating the PC's
interior — correctly, but a first-time player facing an open prompt will wait
for a list. Tolk is an NPC physically present in every scene, so under `TABLE.md` §5 and
§6 Tolk may notice things aloud and ask *"well? what are we doing?"* That
scaffolds a stuck beginner **without** a menu and without Claude writing the
player's mind. The nudge comes from a character, not from the screen.

Late-arc: Tolk's species was **built**, by whoever built the anchors.

## 7. Powers: kit and conditioning

Mythras Imperative's **Superpowers** framework is the right chassis and needs
no modification, because it already has a branch for exactly this:

> core powers = POW + (CON for altered physiology | **INT for tech/training**)

So "powers" in First Through are **trained conditioning and worn kit**, keyed to
INT, with nothing invented and no engine change.

**The economy, as the player experiences it.** Power Points = POW, recovering
one per minute of rest. In fiction that is two things at once: the **charge** in
a first-through's kit, and the **breath** behind their conditioning. A typical
fifteen-year-old PC (POW ~11, INT ~13) lands on the 21-30 row of the build
table: **three core powers**, plus a Boost for taking a Limit.

**Permitted core powers** — each one defensible as technology or training:

| Power | What it is here |
|---|---|
| **Life Support** | The pressure-skin. Immunity to two environments: vacuum, cold, hard radiation, a toxic atmosphere. The single most setting-appropriate power in the book. |
| **Inherent Armor** | The suit proper — CON/3 at every location. |
| **Savant** | **The Threshold's training**, mechanically. Three skills sharing a characteristic, each one grade easier. Trained at 61 Cygni, which is already on the map. |
| **Heightened Sense** | The sensor package: infrared, echo-sense, pressure-gradient. |
| **Enhanced Reactions** | Neural tuning and drilled reflex. |
| **Durability** | Conditioning — the body the Threshold built. |
| **Enhanced Strength / Speed** | Exo-assist in the suit's limbs. |
| **Combat Expert** | The action track's power. Drilled, not gifted. |
| **Lucky** | Luck is not a physics claim. Permitted as-is. |

**Excluded, and the exclusion is good fiction:** Flight, Vaporous Form,
Animation, Elemental Control, Energy Blast — and above all **Teleport**.
Personal teleportation is precisely the thing nobody in this setting can do.
That is *why* the Causeway matters, why the anchors are irreplaceable, and why
a door is worth a war. Excluding one power from the list is the load-bearing
sentence of the whole setting.

**Limits map onto the fiction for free,** and one of them is a gift:

- **External Power Source** — your powers are in your kit, and the rules
  already say a handheld source is vulnerable to **Disarm Weapon** and **Take
  Weapon**. A kid trades a real mechanical bonus for the risk of being stripped
  of their gear mid-mission, which is the best adventure hook in the framework.
- **Activation Cost** — the charge has to be spent to spin the suit up.
- **Vulnerability / Physical Limitation** — available, used sparingly.

Each pre-gen in §6 ships with its powers, Limits and Boost already chosen, so
the player picks a character rather than building one.

## 8. Onboarding without menus

What a first-timer actually needs is not dice, it is permission: the knowledge
that they can say anything and the world will answer. Four devices, all in
campaign content, none requiring engine change:

1. **Tolk asks the question** instead of the GM offering a list (§6).
2. **Dense physical affordances in the first two scenes.** Early rooms are
   written so that concrete things to touch, open, climb and talk to are *in
   the prose*, satisfying "put the detail in the room and let them go and get
   it" rather than prompting.
3. **A sixty-second briefing**, adapted from `NEW-TO-MYTHRAS.md` for science
   fiction and for a younger reader: skills are percentages, fights are short
   and frightening and you can avoid them, Passions are the good bit.
4. **One guaranteed early success** before the first real risk, so the first
   roll a player ever sees in the mechanics block is one that worked.

## 9. Two entry points

Shipped side by side, chosen at `/first-through:start`. Same system, same
pre-gens, same non-lethal rule — opposite appetites. Precedent: Purewater
ships four entry points in `lore/entry-points/`.

### A. "The Quiet Door" — low violence
**Gliese 887** (10.7 ly). The anchor serving the farming settlement on
**GJ 887 d** has gone intermittent. Four thousand people are on the far side of
a door that is dying. The mission is diagnosis, persuasion and repair against a
clock; there is exactly one avoidable confrontation, and avoiding it is the
better play. Teaches: stepping through, being unreachable, Tolk, skill checks
across all four pre-gens, and stakes measured in people rather than bodies.

### B. "Flare" — high action
**Gliese 65** (8.8 ly), the archetypal twin flare stars. A station crew has
barricaded the anchor and is refusing passage, and the stars are about to do
what they do. A flare is inbound on a known clock, the shelter is behind the
barricade, and the only door out is the one they are sitting on. Teaches the
same things plus the Mythras combat engine properly: initiative, action points,
parry-versus-evade, hit locations, and **special effects as the player's choice**
(`TABLE.md §7`) — which is where the fun actually is for a kid who came to
fight. Everything resolves in knockouts, restraints and stun: nobody dies, and
the clock, not a body count, is the threat.

Both are one-sitting missions and both end back at the Nine with a debrief that
sets up Act 2.

## 10. The five-act arc

1. **The job.** Either entry point. Establish the Nine, Calloway, Tolk, and
   that stepping through means being alone.
2. **The doors are failing.** The pattern is not random. Evidence runs to
   **van Maanen's Star** — a real white dwarf visibly consuming the wreckage of
   its own planets, which is better imagery than anything invented, and true.
   Discovery: the Threshold has known for forty years and has been managing the
   news — and the paperwork carries a countersignature nobody will explain
   (§11).
3. **The frontier.** TRAPPIST-1 and the newest doors. Somebody is running
   **pattern transfer** — scan, destroy, rebuild from local matter — as
   contraband. It still needs an anchor, because the classical channel it
   depends on has to cross one; what it bypasses is the **checkpoint**, since
   what steps through the door is data rather than a person on a manifest. It
   is illegal for good reasons, and the reasons are the scenario. A thread also
   opens on what Tolk is.
4. **The countdown.** LHS 1140's door opens in months. Every faction on the
   Causeway converges on the one anchor everybody has waited nine hundred and
   seventy-five years for.
5. **Through.** What is on the other side — and **the door nobody launched**,
   which is where the Quorum keeps the body he started with.
   One edge in the network has no seedship, no launch record, and no
   explanation, which means somebody built anchors before the First Reach. Its
   mouths are relativistically offset, so crossing it moves you in time; that
   is the late-arc secret, confined to this one edge so continuity stays
   holdable.

The deepest layer stays loose on purpose: anchors are failing partly from plain
entropy (true, and sad), and the people who could repair them were not human.

## 11. The Quorum

The campaign needs one antagonist who looms, in the way Douglas Hill's Warlord
looms: unseen for most of the run, felt through lieutenants, and wanting
everything. He is built as the logical consequence of this setting's physics
rather than imported into it.

### Who he is

A first-through named **Sarn** — the best the Threshold ever trained — solved
the problem that defeats everyone here: you cannot be in two places, and nothing
you send outruns a courier. He solved it with **pattern transfer**: scan,
destroy, rebuild. He has been copying himself through the doors for sixty years,
and he is now **the Quorum** — a title, not a name, because a quorum is the
smallest number of you needed to decide.

**His lieutenants are him.** Any tallyman captain, any station director, any
courteous grey man across a table may be Sarn, and the player has no reliable
way to tell. This deploys the antagonist into any scene at no cost, which is
what Hill gets from the Deathwing and we get for free.

### What he wants, and why it looks like entropy

A network must be small enough for one mind to stay **synchronised** across it,
and the Causeway is far too large. So he is pruning it. Every anchor he kills
makes the survivors more valuable, but that is a side effect: the goal is a
galaxy that fits inside him.

**He is shrinking the human galaxy to the size of one mind.** Worlds go dark by
isolation. Nobody is murdered. It reads as age on the Threshold's charts, which
is exactly why §4's second crisis looked like entropy and §10's Act 2 reveal
lands.

### Lightspeed does the character work

Because news travels only at courier speed, **his copies fall out of sync.**
Some of him know about the player; some do not. Some have been out of contact
for years and are quietly becoming different people. Two of them want
incompatible things and have begun to work against each other. The Quorum can
no longer reach quorum.

This is not a metaphor bolted on. It is §4's own rule — nothing outruns a person
— applied to a man, and it is the seam the player eventually prises open.

### The reveal ladder

| Act | What the player gets |
|---|---|
| 1 | A name on a manifest. No face. |
| 2 | A tallyman captain who knows things he should not, and a countersignature on the cover-up's paperwork: *the Quorum*. |
| 3 | They meet him. An ordinary, tired, courteous man in his sixties, who offers them a job. Hill's inversion: physically unimpressive, wholly in command. |
| 4 | How many of him there are — and that two of him are at war. |
| 5 | Behind the door nobody launched, the original body. And the real reveal: **the original died decades ago.** There is no Sarn. There is only the network. |

### Why this ends the campaign correctly

There is nothing to kill. So the non-lethal rule in §3.3 stops being a safety
constraint and becomes the **thesis**: the player wins by **opening** a door,
not closing one. LHS 1140 comes online on schedule, the Causeway grows past the
size the Quorum can hold himself together across, and he comes apart into a
hundred arguing strangers.

**The player beats him with geometry.** For a ten-to-fifteen-year-old that is a
better ending than a duel, and it is the one this setting was built to deliver.

### How the other adversaries realign under him

The tiers in §12 are not a flat list; they are his organisation, which tightens
them rather than adding a sixth:

- **The Tally** is his instrument — he founded the tollkeepers.
- **The Second Hand** is his franchise, and the reason pattern transfer is
  contraband is that he does not want competitors.
- **Ferren** takes orders without knowing whose voice is giving them.
- **Director Hale's** forty-year silence was **bought**.

### What v1 must seed

Acts 1-2 ship (§16), so v1 carries only the bottom of the ladder: the name on a
manifest, the countersigned paperwork, and one tallyman captain who knows too
much. No face, no copies, no explanation. Everything above that is documented in
`lore/gm-secret/` so the arc is on record and the release is still finishable.

## 12. Adversaries: his organisation

The arc supplies crises; a first RPG needs **faces to beat**. Five tiers, built
so that none of them requires killing and the action track still has bodies to
fight.

### The Tally — the standing opposition
An anchor is fixed, finite infrastructure, so whoever holds the station holds
the door. The real power on the Causeway is therefore not a navy but a
**tollkeeper**: the Tally counts what goes through, charges for it, and thereby
governs. Its enforcers are **tallymen** — pressure armour, shock batons, and a
manifest.

This gives the non-lethal rule an antagonist-side motive instead of a house
rule: **the Tally wants everybody alive, because a body is not a line on the
manifest.** Prisoners, restraints and impounded kit are what winning against
the player looks like. They are the opposition at LHS 1140, and they are what
the action track fights.

### Ferren — the rival
Another first-through, nineteen, genuinely better, and always already there when
the player arrives. Gets the postings the player wanted. Working for the Tally
without yet admitting it. Present from Act 1, never killed, beatable — and for
a ten-to-fifteen-year-old a rival is far more motivating than a villain.

### Director Hale — the institution
The Threshold's directorate has known for forty years that the anchors are
failing and has managed the news to prevent panic. Hale is not evil; Hale is
culpable. The Act 2 antagonist is a **decision**, with a face attached, and the
player's weapon against it is disclosure rather than violence.

### The Second Hand — the smugglers
Pattern-transfer contraband (Act 3): scan, destroy, rebuild. They move people
who are not allowed through doors, and they keep copies. Unsettling rather than
gory, and the horror is conceptual, which is the right register for the age
band.

### The system itself
For the low-violence track the adversary is not a person, and the real
astronomy does the work: the flare clock at Gliese 65, debris at Epsilon
Eridani and Tau Ceti, vacuum, pressure, and an anchor that is dying on its own.
A kid should finish "The Quiet Door" having been genuinely frightened by
physics.

Held offstage until Act 5: whoever built anchors before the First Reach. Not a
monster — an absence.

### Creatures, and a correction to §3.1

The action track needs xenofauna, and Tolk is already invented life, so §3.1 as
first written was too strict. The corrected rule:

> **Astronomy is real and fixed. Life is invented but constrained.** We may
> place life only on bodies whose surfaces are genuinely unobserved, only
> consistent with that system's actual temperature, insolation, tidal locking
> and chemistry, and always flagged `invented: life` in the lore entry's
> frontmatter.

So a tidally-locked TRAPPIST-1 world may have terminator-band life, and
Barnard's four scorched pebbles may not. This is the rule a working
exobiologist would want, and it keeps the promise that anything a player looks
up will check out.

## 13. Mechanics decisions

- **System `mythras`**, rules unchanged, no engine or schema work.
- **Superpowers framework, INT (tech/training) branch**, with a permitted-power
  whitelist and Teleport excluded by design (§7).
- **The antagonist is unkillable by construction** (§11), so the non-lethal rule
  and the arc's resolution are the same decision.
- **Non-lethal convention** in campaign table guidance (§3.3), applied by
  Claude every time, both directions.
- **Pre-gens as `templates/`**, created through the normal
  `create-character` path so sheets are engine-legal.
- **Luck Points** are the visible safety valve and the campaign says so.
- **Living world:** agendas with clocks and scheduled beats per the engine's
  `tick` model. Target scale, benchmarked against Purewater v2 (16 agendas,
  40 beats, 42 characters): **~12 agendas, ~24 beats, ~20 characters** for v1 —
  smaller, because solo play visits fewer places.
- **The facts graph** carries what the player has learned about why the doors
  are failing, so Act 2's reveal is computed from knowledge rather than
  remembered.

## 14. Repo shape and deliverables

Standard mythras-gm campaign export tree plus plugin wiring, modelled on
`purewater-campaign-v2`:

```
.claude-plugin/plugin.json      name: first-through, depends on mythras-gm
campaign.yaml                   manifest, id myth-campaign-first-through-s1
README.md                       what it is, how to install, what's real
CLAUDE.md                       GM orientation for this campaign
TABLE-ADDENDUM.md               the non-lethal rule + onboarding devices
commands/start.md               /first-through:start — pick entry point + pre-gen
hooks/hooks.json                SessionStart preflight
scripts/{engine.sh,session-start.sh}
lore/player-briefing/           the sixty-second briefing, the Causeway, the map
lore/character-creation/        the four pre-gens explained in player language
lore/cosmology/                 how anchors work; the arithmetic
lore/geography/                 one entry per shipping system, with real sources
lore/history/                   the First Reach, the Threshold, GJ 1214
lore/technology/                stunners, pressure gear, anchor hardware, and
                                the kit that carries a first-through's powers
lore/organizations/             the Threshold and the factions
lore/entry-points/              "The Quiet Door" and "Flare"
lore/gm-guide/ lore/gm-secret/  the arc, the reveals, the door nobody launched
characters/{pcs,npcs,creatures}/
                                incl. Ferren, Hale, tallymen, and the bestiary
templates/                      four pre-gens, powers and Limits pre-chosen
locations/ factions/ encounters/
agendas/ beats/ facts/ knowledge.json
journal/events.json
tests/                          import round-trip + astronomy fact check
```

**Two tests worth having:** a round-trip import/export check (standard for these
repos), and a **fact-check test** that every astronomical claim in `lore/` cites
a source in frontmatter — the hard content rule in §3.1 is only real if
something enforces it.

## 15. Success criteria

1. A newcomer installs the plugin and is in a scene within five minutes, having
   read nothing.
2. Either entry point completes in one sitting.
3. All four pre-gens can complete both entry points without killing anyone.
4. Every astronomical statement in `lore/` is true as of October 2026 and cited;
   every invented organism is flagged and consistent with its real system.
5. The engine is untouched: no changes to `mythras_engine.py`, the rules layer,
   or the schema. The repo's own Python is confined to `tests/`, as in
   `purewater-campaign-v2`.

## 16. Open questions

- Repo and campaign name: **"First Through"** is a working title, chosen because
  it names the job and the action. Easy to change before publication.
- **Decided:** Calloway uses they/them unless the author says otherwise.
- **Decided:** v1 ships **Acts 1-2** — both entry points, playable to the
  van Maanen's Star reveal. Acts 3-5 ship as `lore/gm-secret/` outline only, so
  the arc is documented and the release is finishable. This is what the
  implementation plan should be scoped to.
