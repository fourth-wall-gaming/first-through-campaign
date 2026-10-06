# First Through — GM orientation

A Mythras Imperative campaign for the **mythras-gm** engine, built as a first
roleplaying game for 10-15 year olds playing solo, and set in the real stellar
neighbourhood.

## Read these, in this order

1. The engine's **`TABLE.md`** — how to run the table at all. Non-negotiable.
2. **`TABLE-ADDENDUM.md`** — the three rules specific to this campaign:
   incapacitation never death in both directions, Tolk as the onboarding
   mechanism, and the player always choosing the special effect.
3. **`lore/gm-guide/`** — playing Tolk, running each entry point, special
   effects.
4. **`lore/gm-secret/`** — the Quorum, Acts 3-5, and what Tolk is. Know all of
   it; spend almost none of it.

## These files are a source export, not the save

Nothing you edit here reaches a game in progress. The save lives in TypeDB.
`/first-through:start` imports this tree once; after that the engine is the
authority on state and these files are history.

## data/ is the authority on every astronomical claim

Every system, distance, spectral type and planet in this campaign is real and
cited. `data/systems.json` holds the figures, computed from SIMBAD parallaxes,
and `data/edges.json` holds the network.

**If prose and data disagree, the data wins and the prose is a bug.** There is a
test for it. The arithmetic — transit time is distance in light years times
twenty, the launch was 975 years ago — is the setting's load-bearing number and
every door date in the repository is derived from it.

The one exception is **life**, which is invented but constrained: only on
genuinely unobserved surfaces, only consistent with the real system's
temperature, insolation and tidal locking, and always flagged `invented: "life"`
in frontmatter.

## Scope

**v1 is Acts 1-2.** Two one-sitting entry points, playable through to the van
Maanen's Star reveal. The Quorum appears only as a name on two forms — no face,
no copies, no explanation. Acts 3-5 are documented in `lore/gm-secret/` as
outline, with no agendas, beats or facts behind them.

## Checks

```bash
uv run --with pytest pytest tests/ -q
```

`maps/causeway_chart.py` regenerates `maps/the-causeway.svg` from `data/`. Every
star is placed from its SIMBAD position, every door is a real edge, so the chart
cannot drift from the worldbook. Re-run it after any change to `data/`.

The suite is the content rules made enforceable: cited astronomy, the seedship
arithmetic, the Causeway's causality, the power whitelist, seed invariants, and
the three ways the plugin could ship broken.
